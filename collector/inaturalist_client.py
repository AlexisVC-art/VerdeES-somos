import requests
from typing import List, Dict, Optional


class iNaturalistClient:
    """
    Cliente simple para obtener observaciones y fotos de iNaturalist
    """

    BASE_URL = "https://api.inaturalist.org/v1"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "FLORA_ELSALVADOR/1.0 (proyecto escolar El Salvador)"
        })

    def search_observations(
        self,
        taxon_name: str = None,
        place_id: int = 7506,          # El Salvador
        quality_grade: str = "research",
        limit: int = 30,
        has_photos: bool = True
    ) -> List[Dict]:
        """
        Busca observaciones en El Salvador.
        place_id 7506 = El Salvador
        """
        url = f"{self.BASE_URL}/observations"
        params = {
            "place_id": place_id,
            "quality_grade": quality_grade,
            "per_page": limit,
            "order": "desc",
            "order_by": "created_at",
        }
        if taxon_name:
            params["taxon_name"] = taxon_name
        if has_photos:
            params["photos"] = "true"

        response = self.session.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])

    def get_photos_for_species(self, scientific_name: str, limit: int = 10) -> List[Dict]:
        """
        Obtiene fotos de una especie en El Salvador
        """
        observations = self.search_observations(
            taxon_name=scientific_name,
            limit=limit
        )

        photos = []
        for obs in observations:
            for photo in obs.get("photos", []):
                photos.append({
                    "url": photo.get("url", "").replace("square", "medium"),
                    "original_url": photo.get("original_url"),
                    "attribution": photo.get("attribution"),
                    "observation_id": obs.get("id"),
                    "taxon_name": obs.get("taxon", {}).get("name"),
                })
        return photos


# Prueba rápida
if __name__ == "__main__":
    client = iNaturalistClient()

    print("Buscando observaciones de plantas en El Salvador...")
    obs = client.search_observations(limit=5)

    print(f"\nSe encontraron {len(obs)} observaciones:\n")
    for i, o in enumerate(obs, 1):
        taxon = o.get("taxon", {})
        name = taxon.get("name", "Sin nombre")
        common = taxon.get("preferred_common_name", "")
        print(f"{i}. {name} ({common})")
        if o.get("photos"):
            print(f"   Foto: {o['photos'][0].get('url', '').replace('square', 'medium')}")
        print()