import time
from pathlib import Path

import requests

from database.connection import SessionLocal, init_db
from database.models import Plant, Image

# 7563 = El Salvador en iNaturalist
PLACE_ID = 7563
FOTOS_POR_PLANTA = 180
CARPETA = Path(__file__).resolve().parent.parent / "dataset" / "fotos"


def nombre_corto(cientifico: str) -> str:
    partes = cientifico.replace("×", " ").split()
    if len(partes) >= 2:
        return f"{partes[0]} {partes[1]}"
    return cientifico


def buscar_fotos(session: requests.Session, nombre: str) -> list[dict]:
    url = "https://api.inaturalist.org/v1/observations"
    base = {
        "taxon_name": nombre,
        "photos": "true",
        "quality_grade": "research",
        "per_page": 70,
        "order_by": "votes",
    }
    for extra in ({"place_id": PLACE_ID}, {}):
        respuesta = session.get(url, params={**base, **extra}, timeout=25)
        respuesta.raise_for_status()
        fotos = []
        for obs in respuesta.json().get("results", []):
            for photo in obs.get("photos") or []:
                cruda = photo.get("url") or ""
                if not cruda:
                    continue
                fotos.append(
                    {
                        "url": cruda.replace("square", "medium"),
                        "original": photo.get("original_url") or cruda.replace("square", "original"),
                        "obs_id": str(obs.get("id") or ""),
                    }
                )
                if len(fotos) >= FOTOS_POR_PLANTA:
                    return fotos
        if fotos:
            return fotos
        time.sleep(0.4)
    return []


def descargar(session: requests.Session, url: str, destino: Path) -> bool:
    try:
        respuesta = session.get(url, timeout=30)
        respuesta.raise_for_status()
        destino.write_bytes(respuesta.content)
        return True
    except requests.RequestException:
        return False


def main():
    init_db()
    CARPETA.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    http = requests.Session()
    http.headers["User-Agent"] = "FLORA_ELSALVADOR/1.0 (proyecto escolar, El Salvador)"

    plantas = db.query(Plant).order_by(Plant.id).all()
    print(f"Plantas en la base: {len(plantas)}")

    try:
        for planta in plantas:
            ya = (
                db.query(Image)
                .filter(Image.plant_id == planta.id, Image.source == "inaturalist")
                .count()
            )
            if ya >= FOTOS_POR_PLANTA:
                print(f"ya tiene fotos: {planta.scientific_name}")
                continue

            nombre = nombre_corto(planta.scientific_name)
            print(f"buscando: {nombre}")
            fotos = buscar_fotos(http, nombre)
            nuevas = 0
            for i, foto in enumerate(fotos, start=ya + 1):
                if db.query(Image).filter(Image.url == foto["url"]).first():
                    continue
                archivo = CARPETA / f"planta_{planta.id}_{i}.jpg"
                if not descargar(http, foto["original"], archivo):
                    continue
                db.add(
                    Image(
                        plant_id=planta.id,
                        file_path=str(archivo),
                        url=foto["url"],
                        source="inaturalist",
                        source_id=foto["obs_id"],
                        is_for_training=True,
                        is_verified=False,
                    )
                )
                nuevas += 1
            db.commit()
            print(f"  guardadas: {nuevas}")
            time.sleep(0.6)

        total = db.query(Image).count()
        print(f"Listo. Fotos en la tabla images: {total}")
        print(f"Archivos en: {CARPETA}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()