import json
from pathlib import Path

import numpy as np

from database.connection import SessionLocal, init_db
from database.models import Image as FotoPlanta
from ml.huella import vectores

CARPETA = Path(__file__).resolve().parent
INDICE = CARPETA / "indice.json"
VECTORES = CARPETA / "vectores.npy"
EXTENSIONES = {".jpg", ".jpeg", ".png", ".webp"}


def entrenar():
    init_db()
    db = SessionLocal()
    meta_previa = {}
    if INDICE.exists():
        for fila in json.loads(INDICE.read_text(encoding="utf-8")).get("fotos", []):
            meta_previa[fila["archivo"]] = fila

    viejos = None
    if VECTORES.exists() and meta_previa:
        viejos = np.load(VECTORES)

    rutas_nuevas = []
    fichas = []
    try:
        fotos = db.query(FotoPlanta).filter(FotoPlanta.file_path.isnot(None)).all()
        orden_viejo = {fila["archivo"]: i for i, fila in enumerate(
            json.loads(INDICE.read_text(encoding="utf-8")).get("fotos", [])
        )} if INDICE.exists() else {}
        for foto in fotos:
            ruta = Path(foto.file_path)
            if not ruta.exists() or ruta.suffix.lower() not in EXTENSIONES:
                continue
            clave = str(ruta)
            mtime = ruta.stat().st_mtime_ns
            previa = meta_previa.get(clave)
            if previa and previa.get("mtime") == mtime and viejos is not None:
                fichas.append((previa, viejos[orden_viejo[clave]]))
            else:
                rutas_nuevas.append((foto, ruta, mtime))
    finally:
        db.close()

    if rutas_nuevas:
        nuevos = vectores([ruta for _, ruta, _ in rutas_nuevas])
    else:
        nuevos = np.zeros((0, 576), dtype=np.float32)

    fotos_json = []
    bloques = []
    cursor = 0
    for previa, vector in fichas:
        fotos_json.append(previa)
        bloques.append(vector)
    for (foto, ruta, mtime), vector in zip(rutas_nuevas, nuevos):
        fotos_json.append(
            {
                "plant_id": foto.plant_id,
                "image_id": foto.id,
                "archivo": str(ruta),
                "mtime": mtime,
            }
        )
        bloques.append(vector)
        cursor += 1

    if not bloques:
        print("No hay fotos utilizables.")
        return

    np.save(VECTORES, np.stack(bloques).astype(np.float32))
    INDICE.write_text(json.dumps({"version": 3, "fotos": fotos_json}), encoding="utf-8")
    print(f"Fotos en el indice: {len(fotos_json)}. Nuevas esta vez: {len(rutas_nuevas)}.")
    print(f"Vectores: {VECTORES}")


if __name__ == "__main__":
    entrenar()