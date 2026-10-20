from database.connection import SessionLocal, init_db
from database.models import Plant, PlantStatus

# Lista prioritaria de invasivas (nombre científico limpio)
INVASIVAS = {
    "Spathodea campanulata": "Llama del bosque",
    "Erythrina poeppigiana": "Pito extranjero",
    "Eichhornia crassipes": "Jacinto de agua",
    "Salvinia molesta": "Salvina gigante",
    "Pistia stratiotes": "Lechuga de agua",
    "Syzygium jambos": "Manzana rosa",
    "Melinis minutiflora": "Pasto melaza",
    "Megathyrsus maximus": "Pasto guinea",
    "Sansevieria cylindrica": "Lengua de suegra",
    "Sansevieria trifasciata": "Lengua de suegra",
    "Tradescantia spathacea": "Moses-in-the-cradle",
    "Hypoestes phyllostachya": "Planta de puntos",
    "Oeceoclades maculata": "Orquídea africana",
    "Ricinus communis": "Higuerillo",
    "Ficus microcarpa": "Ficus",
    "Aloe vera": "Sábila",
    "Duranta erecta": "Duranta",
    "Catharanthus roseus": "Vinca",
    "Epipremnum aureum": "Potus",
    "Caesalpinia pulcherrima": "Clavellina",
}

# Algunas nativas importantes
NATIVAS = {
    "Tabebuia rosea": "Maquilishuat",
    "Yucca guatemalensis": "Izote",
    "Myroxylon balsamum": "Bálsamo",
    "Brosimum alicastrum": "Ojushte",
    "Chamaedorea tepejilote": "Pacaya",
}


def classify_and_add():
    init_db()
    db = SessionLocal()

    try:
        # 1. Clasificar las que ya existen
        plants = db.query(Plant).all()
        print(f"Plantas actuales en BD: {len(plants)}")

        for plant in plants:
            name = plant.scientific_name.split()[0] + " " + (plant.scientific_name.split()[1] if len(plant.scientific_name.split()) > 1 else "")
            # Limpieza simple
            clean = plant.scientific_name.split("(")[0].strip()

            if any(inv in clean for inv in INVASIVAS.keys()) or clean in INVASIVAS:
                plant.status = PlantStatus.INVASIVA
                if not plant.common_name_es:
                    for k, v in INVASIVAS.items():
                        if k in clean or clean in k:
                            plant.common_name_es = v
                            break
                print(f"  → Invasiva: {plant.scientific_name}")

            elif any(nat in clean for nat in NATIVAS.keys()) or clean in NATIVAS:
                plant.status = PlantStatus.NATIVA
                if not plant.common_name_es:
                    for k, v in NATIVAS.items():
                        if k in clean or clean in k:
                            plant.common_name_es = v
                            break
                print(f"  → Nativa: {plant.scientific_name}")

        # 2. Agregar las prioritarias que faltan
        for sci_name, common in INVASIVAS.items():
            exists = db.query(Plant).filter(Plant.scientific_name.like(f"%{sci_name}%")).first()
            if not exists:
                plant = Plant(
                    scientific_name=sci_name,
                    common_name_es=common,
                    status=PlantStatus.INVASIVA,
                    is_priority=True
                )
                db.add(plant)
                print(f"  + Agregada invasiva: {sci_name}")

        for sci_name, common in NATIVAS.items():
            exists = db.query(Plant).filter(Plant.scientific_name.like(f"%{sci_name}%")).first()
            if not exists:
                plant = Plant(
                    scientific_name=sci_name,
                    common_name_es=common,
                    status=PlantStatus.NATIVA,
                    is_priority=True
                )
                db.add(plant)
                print(f"  + Agregada nativa: {sci_name}")

        db.commit()
        print("\nClasificación terminada.")

        # Resumen
        nativas = db.query(Plant).filter(Plant.status == PlantStatus.NATIVA).count()
        invasivas = db.query(Plant).filter(Plant.status == PlantStatus.INVASIVA).count()
        desconocidas = db.query(Plant).filter(Plant.status == PlantStatus.DESCONOCIDO).count()
        print(f"Nativas: {nativas} | Invasivas: {invasivas} | Desconocidas: {desconocidas}")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    classify_and_add()