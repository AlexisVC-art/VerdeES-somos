import json
from pathlib import Path

import numpy as np
from sqlalchemy.orm import Session, joinedload

from database.models import Plant
from ml.entrenar import INDICE, VECTORES
from ml.huella import parecido, vector

def identificar_ruta(ruta_consulta: Path, db: Session, tope: int = 3) -> list[dict]:
    if not VECTORES.exists():
        raise FileNotFoundError("Falta el indice. Ejecuta: python -m ml.entrenar")
    consulta = vector(ruta_consulta)
    matriz = np.load(VECTORES)
    notas = parecido(consulta, matriz)
    meta = json.loads(INDICE.read_text(encoding="utf-8"))["fotos"]

    mejor_por_planta: dict[int, float] = {}
    for nota, fila in zip(notas, meta):
        planta_id = fila["plant_id"]
        if nota > mejor_por_planta.get(planta_id, -1):
            mejor_por_planta[planta_id] = float(nota)

    orden = sorted(mejor_por_planta.items(), key=lambda par: par[1], reverse=True)[:tope]
    salida = []
    for plant_id, nota in orden:
        if nota < 0.35:
            continue
        planta = (
            db.query(Plant)
            .options(joinedload(Plant.images))
            .filter(Plant.id == plant_id)
            .first()
        )
        if planta:
            salida.append({"parecido": int(round(nota * 100)), "planta": planta})
    return salida