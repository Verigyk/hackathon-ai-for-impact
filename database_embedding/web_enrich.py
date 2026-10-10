"""Web search (Jina s.jina.ai) for school-relevant POIs that have no description.

Usage: set JINA_API_KEY, then: python web_enrich.py [--max N]
Results are cached in data/web_cache.json (keyed by URI) so the script can be resumed.
Each search costs ~10k Jina tokens, so only the most relevant POIs are searched.
"""
import argparse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

SRC = "data/datatourisme-reg-occ.csv"
CACHE = "data/web_cache.json"

# Categories useful for a school trip, by priority (first = most useful).
PRIORITY = [
    "Museum", "InterpretationCentre", "ArcheologicalSite", "CaveSinkholeOrAven", "MegalithDolmenMenhir",
    "Castle", "FortifiedCastle", "CastleAndPrestigeMansion", "Abbey", "Cathedral", "Cloister",
    "DefenceSite", "RemembranceSite", "MilitaryCemetery", "TechnicalHeritage", "IndustrialSite", "Mill", "Mine",
    "Aqueduct", "Bridge", "RomanPath", "Ruins", "Fort", "Bastide", "Palace", "Monastery", "Convent",
    "ZooAnimalPark", "VivariumAquarium", "TeachingFarm", "EducationalTrail", "NaturalHeritage", "NaturalCuriosity",
    "Gorge", "Waterfall", "Cirque", "Canyon", "Lake", "Forest", "ParkAndGarden", "PointOfView",
    "ThemePark", "AdventurePark", "Library", "Theater", "Opera", "Cinema", "ArtGalleryOrExhibitionGallery",
    "CulturalSite", "RemarkableBuilding", "CityHeritage", "ReligiousSite", "Church", "Chapel",
    "Visit", "WalkingTour", "Tour", "CulturalActivityProvider", "LeisureSportActivityProvider", "ActivityProvider",
    "SportsAndLeisurePlace",
]
RANK = {c: i for i, c in enumerate(PRIORITY)}


def cats(v):
    return {x.split("#")[-1] for x in str(v).split("|") if "datatourisme" in x}


def commune(v):
    return str(v).split("#")[-1] if pd.notna(v) else ""


def search(session, q):
    for _ in range(10):
        try:
            r = session.get("https://s.jina.ai/", params={"q": q, "gl": "FR", "hl": "fr"}, timeout=60)
        except requests.RequestException:
            time.sleep(15)
            continue
        if r.status_code == 200:
            return [{"title": d.get("title"), "description": d.get("description"), "url": d.get("url")}
                    for d in r.json().get("data", [])[:5]]
        if r.status_code in (429,) or r.status_code >= 500:
            time.sleep(int(r.headers.get("Retry-After", 60)))
            continue
        if r.status_code == 402:  # quota exhausted
            raise SystemExit("Quota Jina épuisé")
        return []
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=900)
    args = ap.parse_args()

    df = pd.read_csv(SRC)
    nd = df[df.Description.isna()].copy()
    nd["rank"] = nd.Categories_de_POI.map(lambda v: min((RANK[c] for c in cats(v) if c in RANK), default=None))
    nd = nd[nd["rank"].notna()].drop_duplicates("Nom_du_POI").sort_values("rank").head(args.max)

    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    todo = [r for r in nd.itertuples() if r.URI_ID_du_POI not in cache]
    print(f"{len(nd)} lieux ciblés, {len(todo)} à chercher")

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {os.environ['JINA_API_KEY']}",
                            "Accept": "application/json", "X-Respond-With": "no-content"})

    def work(r):
        return r.URI_ID_du_POI, search(session, f"{r.Nom_du_POI} {commune(r.Code_postal_et_commune)}")

    with ThreadPoolExecutor(4) as pool:
        for k, (uri, res) in enumerate(pool.map(work, todo), 1):
            cache[uri] = res
            if k % 20 == 0 or k == len(todo):
                json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
                print(f"{k}/{len(todo)}", flush=True)


if __name__ == "__main__":
    main()
