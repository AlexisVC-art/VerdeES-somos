import time

from database.connection import SessionLocal, init_db
from database.models import Plant, PlantStatus
from collector.gbif_client import GBIFClient

# Peligro y recomendacion que GBIF casi nunca trae completos.
LOCAL = {
    "Spathodea campanulata": {
        "status": PlantStatus.INVASIVA,
        "common": "Llama del bosque",
        "impacto": "Peligro alto. Sus plantulas cubren claros y desplazan arboles nativos. En parques de El Salvador llega a dominar el dosel.",
        "control": "No plantar mas. Arrancar plantulas. Al cortar un adulto, tratar el tocon para que no rebrote.",
    },
    "Erythrina poeppigiana": {
        "status": PlantStatus.INVASIVA,
        "common": "Pito extranjero",
        "impacto": "Peligro alto en cafetales y bordes de bosque. Ocupa sitios abiertos y compite con arboles nativos.",
        "control": "Evitar nuevas siembras junto a bosque. Cortar rebrotes y no mover semilla a otra finca.",
    },
    "Eichhornia crassipes": {
        "status": PlantStatus.INVASIVA,
        "common": "Jacinto de agua",
        "impacto": "Peligro alto en lagunas y canales. Tapa el agua, baja el oxigeno y estorba la pesca y el riego.",
        "control": "Sacar las matas antes de que cubran todo. No tirar trozos a otro cuerpo de agua: vuelven a crecer.",
    },
    "Pistia stratiotes": {
        "status": PlantStatus.INVASIVA,
        "common": "Lechuga de agua",
        "impacto": "Cubre estanques igual que el jacinto. Quita luz a las plantas y animales del agua.",
        "control": "Retirar a mano. No trasladarla a otra laguna.",
    },
    "Salvinia molesta": {
        "status": PlantStatus.INVASIVA,
        "common": "Salvina gigante",
        "impacto": "Helecho flotante. Un fragmento forma un tapete y ahoga el cuerpo de agua.",
        "control": "Sacar el tapete completo, sin dejar pedazos.",
    },
    "Syzygium jambos": {
        "status": PlantStatus.INVASIVA,
        "common": "Manzana rosa",
        "impacto": "Bajo su copa casi no crece otra planta. Forma manchas densas.",
        "control": "Sacar plantulas. No dejar frutos cerca de bosque o cafetal abandonado.",
    },
    "Ricinus communis": {
        "status": PlantStatus.INVASIVA,
        "common": "Higuerillo",
        "impacto": "Peligro para personas y animales: las semillas son muy toxicas. Ademas coloniza terrenos removidos.",
        "control": "Arrancar con guantes antes de que fructifique. No dejar semillas en el suelo.",
    },
    "Sansevieria trifasciata": {
        "status": PlantStatus.INVASIVA,
        "common": "Lengua de suegra",
        "impacto": "Un recorte de hoja enraiza y forma manchas fuera del jardin.",
        "control": "Sacar el rizoma completo. No tirar recortes al monte.",
    },
    "Hypoestes phyllostachya": {
        "status": PlantStatus.INVASIVA,
        "common": "Planta de puntos",
        "impacto": "Muy agresiva a la sombra, sobre todo en cafetales.",
        "control": "Arrancar antes de que suelte semilla. No usarla como cobertura.",
    },
    "Oeceoclades maculata": {
        "status": PlantStatus.INVASIVA,
        "common": "Orquidea africana",
        "impacto": "Se extiende por suelos de cafetal y bosque bajo. Es de las invasoras terrestres mas citadas en el pais.",
        "control": "Arrancar el bulbo antes de que fructifique.",
    },
    "Melinis minutiflora": {
        "status": PlantStatus.INVASIVA,
        "common": "Pasto melaza",
        "impacto": "Cubre laderas, desplaza hierbas nativas y aumenta el fuego.",
        "control": "Cortar varias veces para que no semille.",
    },
    "Megathyrsus maximus": {
        "status": PlantStatus.INVASIVA,
        "common": "Pasto guinea",
        "impacto": "Ocupa orillas de camino y terrenos abiertos.",
        "control": "Cortar antes de la floracion.",
    },
    "Ficus microcarpa": {
        "status": PlantStatus.INVASIVA,
        "common": "Laurel de la India",
        "impacto": "Raices agresivas. Se naturaliza y compite en areas verdes.",
        "control": "No plantar junto a bosque ni banqueta. Controlar plantulas.",
    },
    "Tabebuia rosea": {
        "status": PlantStatus.NATIVA,
        "common": "Maquilishuat",
        "impacto": "Arbol nacional. No es un peligro: da sombra y flor para la fauna.",
        "control": "Conviene sembrarlo en lugar de arboles invasores.",
    },
    "Yucca guatemalensis": {
        "status": PlantStatus.NATIVA,
        "common": "Izote",
        "impacto": "Flor nacional. La flor es comestible y la planta marca linderos.",
        "control": "No aplica un control. Se conserva y se cultiva.",
    },
    "Chamaedorea tepejilote": {
        "status": PlantStatus.NATIVA,
        "common": "Pacaya",
        "impacto": "Palma nativa de sombra. La pacaya se come.",
        "control": "Cosechar la inflorescencia sin matar la mata.",
    },
}


def nombre_base(cientifico: str) -> str:
    partes = cientifico.replace("×", " ").split()
    if len(partes) >= 2:
        return f"{partes[0]} {partes[1]}"
    return cientifico


def construir():
    init_db()
    db = SessionLocal()
    gbif = GBIFClient()
    plantas = db.query(Plant).order_by(Plant.id).all()
    print(f"Plantas a completar: {len(plantas)}")

    try:
        for planta in plantas:
            clave = nombre_base(planta.scientific_name)
            local = LOCAL.get(clave)
            ficha = None
            try:
                ficha = gbif.ficha_especie(clave)
            except Exception as error:
                print(f"  GBIF fallo en {clave}: {error}")

            if ficha:
                planta.gbif_taxon_key = planta.gbif_taxon_key or ficha["gbif_taxon_key"]
                planta.family = planta.family or ficha["family"]
                planta.genus = planta.genus or ficha["genus"]
                if not planta.common_name_es and ficha["common_name_es"]:
                    planta.common_name_es = ficha["common_name_es"]
                if not planta.description and ficha["description"]:
                    planta.description = ficha["description"]
                if not planta.ecological_impact and ficha["ecological_impact"]:
                    planta.ecological_impact = "Riesgo segun GBIF: " + ficha["ecological_impact"]

            if local:
                planta.status = local["status"]
                planta.common_name_es = planta.common_name_es or local["common"]
                planta.ecological_impact = local["impacto"]
                planta.control_methods = local["control"]
                planta.is_priority = True
                if not planta.description:
                    planta.description = local["impacto"]

            print(f"  {clave} | {planta.status} | comun={planta.common_name_es}")
            time.sleep(0.3)

        db.commit()
        con_texto = db.query(Plant).filter(Plant.description.isnot(None)).count()
        con_control = db.query(Plant).filter(Plant.control_methods.isnot(None)).count()
        print(f"Listo. Con descripcion: {con_texto}. Con recomendacion: {con_control}.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    construir()