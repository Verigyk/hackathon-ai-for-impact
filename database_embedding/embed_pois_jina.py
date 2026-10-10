"""Embed POI titles + descriptions with the Jina AI embeddings API.

Usage: set JINA_API_KEY in the environment, then: python embed_pois_jina.py [--limit N]
Output: data/poi_embeddings_jina.csv (URI_ID_du_POI, Nom_du_POI, texte_embedde, embedding as JSON list)
        data/poi_embeddings_jina.npy (float32 matrix, same row order).

At query time, embed the teacher's request with the same model and task="retrieval.query".
On rate limit (429) or transient errors, waits for the per-minute quota to reset, then retries.
Progress is checkpointed so a re-run resumes where it stopped.
"""
import argparse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import requests

API_URL = "https://api.jina.ai/v1/embeddings"
MODEL = "jina-embeddings-v3"
DIM = 1024
BATCH = 128
WORKERS = 4  # parallel requests; 429s are retried after the quota resets
SRC = "data/datatourisme-reg-occ.csv"
OUT_CSV = "data/poi_embeddings_jina.csv"
OUT_NPY = "data/poi_embeddings_jina.npy"
CKPT = "data/poi_embeddings_jina.partial.npy"


def build_text(row):
    title = str(row["Nom_du_POI"]).strip() if pd.notna(row["Nom_du_POI"]) else ""
    desc = str(row["Description"]).strip() if pd.notna(row["Description"]) else ""
    return f"{title}. {desc}" if desc else title


def embed_batch(session, texts, max_retries=20):
    payload = {"model": MODEL, "task": "retrieval.passage", "dimensions": DIM,
               "normalized": True, "input": texts}
    for attempt in range(max_retries):
        try:
            r = session.post(API_URL, json=payload, timeout=120)
        except requests.RequestException as e:
            wait = 20
            print(f"  erreur réseau ({e}), nouvel essai dans {wait}s")
            time.sleep(wait)
            continue
        if r.status_code == 200:
            data = sorted(r.json()["data"], key=lambda d: d["index"])
            return [d["embedding"] for d in data]
        if r.status_code == 429 or r.status_code >= 500:
            wait = int(r.headers.get("Retry-After", 60))
            print(f"  HTTP {r.status_code}, attente {wait}s (quota par minute)")
            time.sleep(wait)
            continue
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    raise RuntimeError("Trop d'échecs consécutifs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    key = os.environ.get("JINA_API_KEY")
    if not key:
        raise SystemExit("Définis la variable d'environnement JINA_API_KEY")

    df = pd.read_csv(SRC)
    if args.limit:
        df = df.head(args.limit)
    texts = df.apply(build_text, axis=1).tolist()
    n = len(texts)

    emb = np.zeros((n, DIM), dtype=np.float32)
    start = 0
    if os.path.exists(CKPT):
        saved = np.load(CKPT)
        if saved.shape == emb.shape:
            emb = saved
            empty = np.flatnonzero(~emb.any(axis=1))
            start = int(empty[0]) if len(empty) else n
            print(f"Reprise à la ligne {start}")

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {key}", "Content-Type": "application/json"})

    t0 = time.time()
    pool = ThreadPoolExecutor(WORKERS)
    step = BATCH * WORKERS
    for g in range(start, n, step):
        starts = range(g, min(g + step, n), BATCH)
        results = pool.map(lambda i: embed_batch(session, texts[i:i + BATCH]), starts)
        for i, vecs in zip(starts, results):
            emb[i:i + BATCH] = vecs
        np.save(CKPT, emb)
        done = min(g + step, n)
        rate = (done - start) / (time.time() - t0)
        print(f"{done}/{n}  ({rate:.0f} textes/s, reste ~{(n - done) / rate / 60:.1f} min)")

    out = pd.DataFrame({
        "URI_ID_du_POI": df["URI_ID_du_POI"],
        "Nom_du_POI": df["Nom_du_POI"],
        "texte_embedde": texts,
        "embedding": [json.dumps([round(float(x), 6) for x in v]) for v in emb],
    })
    out.to_csv(OUT_CSV, index=False, encoding="utf-8")
    np.save(OUT_NPY, emb)
    os.remove(CKPT)
    print(f"Écrit {OUT_CSV} et {OUT_NPY} {emb.shape} en {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
