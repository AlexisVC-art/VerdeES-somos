from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image as PILImage
from sqlalchemy.orm import Session, joinedload

from database.connection import get_db, init_db
from database.models import Image, Plant, PlantStatus

BASE = Path(__file__).resolve().parent.parent
FOTOS = BASE / "dataset" / "fotos"
STATIC = Path(__file__).resolve().parent / "static"
FOTOS.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="FLORA El Salvador")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/fotos", StaticFiles(directory=str(FOTOS)), name="fotos")
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


def estado(valor) -> str:
    if isinstance(valor, PlantStatus):
        return valor.value
    return str(valor or "desconocido")


def fuentes(planta: Plant) -> list[str]:
    urls = []
    for img in planta.images:
        if img.file_path and Path(img.file_path).exists():
            urls.append("/fotos/" + Path(img.file_path).name)
        elif img.url:
            urls.append(img.url)
    return urls


def ficha(planta: Plant) -> dict:
    return {
        "id": planta.id,
        "scientific_name": planta.scientific_name,
        "common_name_es": planta.common_name_es,
        "status": estado(planta.status),
        "family": planta.family,
        "description": planta.description,
        "ecological_impact": planta.ecological_impact,
        "control_methods": planta.control_methods,
        "fotos": fuentes(planta),
    }


def huella(path: Path) -> tuple:
    imagen = PILImage.open(path).convert("L").resize((16, 16))
    pixeles = list(imagen.getdata())
    promedio = sum(pixeles) / len(pixeles)
    return tuple(1 if p > promedio else 0 for p in pixeles)


def distancia(a: tuple, b: tuple) -> int:
    return sum(x != y for x, y in zip(a, b))


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def inicio():
    return FileResponse(STATIC / "index.html")


@app.get("/api/plantas")
def listar(q: str = "", status: str = "", db: Session = Depends(get_db)):
    consulta = db.query(Plant).options(joinedload(Plant.images))
    if q.strip():
        like = f"%{q.strip()}%"
        consulta = consulta.filter(
            Plant.scientific_name.ilike(like) | Plant.common_name_es.ilike(like)
        )
    if status:
        try:
            consulta = consulta.filter(Plant.status == PlantStatus(status))
        except ValueError:
            raise HTTPException(400, "Estado invalido")
    plantas = consulta.order_by(Plant.scientific_name).all()
    return [ficha(p) for p in plantas]


@app.get("/api/plantas/{plant_id}")
def una(plant_id: int, db: Session = Depends(get_db)):
    planta = (
        db.query(Plant)
        .options(joinedload(Plant.images))
        .filter(Plant.id == plant_id)
        .first()
    )
    if not planta:
        raise HTTPException(404, "Planta no encontrada")
    return ficha(planta)


@app.post("/api/identificar")
async def identificar(foto: UploadFile = File(...), db: Session = Depends(get_db)):
    temporal = FOTOS / "_consulta.jpg"
    temporal.write_bytes(await foto.read())
    try:
        consulta = huella(temporal)
    except Exception:
        temporal.unlink(missing_ok=True)
        raise HTTPException(400, "Ese archivo no es una imagen valida")

    imagenes = db.query(Image).filter(Image.file_path.isnot(None)).all()
    mejores: dict[int, int] = {}
    for img in imagenes:
        ruta = Path(img.file_path)
        if not ruta.exists():
            continue
        try:
            marca = huella(ruta)
        except Exception:
            continue
        dist = distancia(consulta, marca)
        anterior = mejores.get(img.plant_id)
        if anterior is None or dist < anterior:
            mejores[img.plant_id] = dist

    temporal.unlink(missing_ok=True)
    if not mejores:
        raise HTTPException(404, "No hay fotos locales en la base para comparar")

    orden = sorted(mejores.items(), key=lambda par: par[1])[:3]
    salida = []
    for plant_id, dist in orden:
        planta = (
            db.query(Plant)
            .options(joinedload(Plant.images))
            .filter(Plant.id == plant_id)
            .first()
        )
        if not planta:
            continue
        parecido = max(0, round(100 * (1 - dist / 256)))
        salida.append({"parecido": parecido, "planta": ficha(planta)})
    return {"resultados": salida}