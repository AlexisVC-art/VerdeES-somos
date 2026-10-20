from database.connection import SessionLocal, init_db
from database.models import Plant, Occurrence, PlantStatus
from collector.gbif_client import GBIFClient
from datetime import datetime


def save_plants_from_gbif(limit=20):
    print("Conectando a GBIF y guardando plantas...")

    # Asegurar que las tablas existan
    init_db()

    client = GBIFClient()
    db = SessionLocal()

    try:
        # Traer ocurrencias de plantas en El Salvador
        occurrences = client.search_plants_el_salvador(limit=limit)
        print(f"Se obtuvieron {len(occurrences)} registros de GBIF")

        saved_plants = 0
        saved_occurrences = 0

        for occ in occurrences:
            scientific_name = occ.get("scientificName")
            if not scientific_name:
                continue

            # Limpiar el nombre (quitar autor)
            clean_name = scientific_name.split(" (")[0].strip()

            # Buscar si ya existe la planta
            plant = db.query(Plant).filter(Plant.scientific_name == clean_name).first()

            if not plant:
                # Crear nueva planta
                plant = Plant(
                    scientific_name=clean_name,
                    status=PlantStatus.DESCONOCIDO,  # Luego lo clasificamos
                    gbif_taxon_key=occ.get("taxonKey"),
                    family=occ.get("family"),
                    genus=occ.get("genus"),
                )
                db.add(plant)
                db.flush()  # Para obtener el id
                saved_plants += 1
                print(f"  + Nueva planta: {clean_name}")

            # Guardar la ocurrencia
            source_id = str(occ.get("key", ""))
            exists = db.query(Occurrence).filter(
                Occurrence.source == "gbif",
                Occurrence.source_id == source_id
            ).first()

            if not exists:
                occurrence = Occurrence(
                    plant_id=plant.id,
                    source="gbif",
                    source_id=source_id,
                    latitude=occ.get("decimalLatitude"),
                    longitude=occ.get("decimalLongitude"),
                    locality=occ.get("locality"),
                    is_verified=True,
                    observed_at=None,
                )
                db.add(occurrence)
                saved_occurrences += 1

        db.commit()
        print(f"\nResumen:")
        print(f"  Plantas nuevas: {saved_plants}")
        print(f"  Ocurrencias nuevas: {saved_occurrences}")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    save_plants_from_gbif(limit=30)