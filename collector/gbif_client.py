import requests


class GBIFClient:
    BASE_URL = "https://api.gbif.org/v1"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "FLORA_ELSALVADOR/1.0 (proyecto escolar)"

    def search_plants_el_salvador(self, query="Plantae", limit=50):
        params = {
            "country": "SV",
            "kingdomKey": 6,
            "limit": limit,
            "hasCoordinate": "true",
        }
        if query and query != "Plantae":
            params["q"] = query
        respuesta = self.session.get(
            f"{self.BASE_URL}/occurrence/search", params=params, timeout=25
        )
        respuesta.raise_for_status()
        return respuesta.json().get("results", [])

    def ficha_especie(self, nombre):
        coincidencia = self.session.get(
            f"{self.BASE_URL}/species/match",
            params={"name": nombre, "kingdom": "Plantae"},
            timeout=20,
        )
        coincidencia.raise_for_status()
        dato = coincidencia.json()
        clave = dato.get("usageKey")
        if not clave:
            return None

        nombres = self.session.get(
            f"{self.BASE_URL}/species/{clave}/vernacularNames",
            params={"limit": 50},
            timeout=20,
        )
        nombres.raise_for_status()
        comun = None
        for item in nombres.json().get("results", []):
            if item.get("language") in ("spa", "es", "esp") and item.get("vernacularName"):
                comun = item["vernacularName"]
                break

        descripciones = self.session.get(
            f"{self.BASE_URL}/species/{clave}/descriptions",
            params={"limit": 40},
            timeout=20,
        )
        descripciones.raise_for_status()
        lineas = []
        riesgo = None
        for item in descripciones.json().get("results", []):
            tipo = (item.get("type") or "").strip()
            texto = (item.get("description") or "").strip()
            if not texto or texto.upper() == "FALSO":
                continue
            if "riesgo" in tipo.lower():
                riesgo = texto
            if tipo and len(texto) < 400:
                lineas.append(f"{tipo}: {texto}")

        return {
            "gbif_taxon_key": clave,
            "scientific_name": dato.get("canonicalName") or nombre,
            "common_name_es": comun,
            "family": dato.get("family"),
            "genus": dato.get("genus"),
            "description": "\n".join(lineas[:8]) or None,
            "ecological_impact": riesgo,
        }