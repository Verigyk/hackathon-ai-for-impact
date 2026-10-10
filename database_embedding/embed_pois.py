"""Embed POI titles + descriptions with a static multilingual model (very fast on CPU).

Usage: python embed_pois.py [--limit N]
Output: data/poi_embeddings.csv (URI_ID_du_POI, Nom_du_POI, texte_embedde, embedding as JSON list)
        data/poi_embeddings.npy (float32 matrix, same row order) for fast loading.

Static embeddings (no transformer): ~5000 texts/s on a laptop CPU, the full file in seconds.
At query time, embed the teacher's request with the same model (no prefix) and use cosine similarity.
Dimensions are Matryoshka: you can keep only the first 256/128 and re-normalize if needed.
"""
import argparse
import json
import time

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

MODEL = "sentence-transformers/static-similarity-mrl-multilingual-v1"
SRC = "data/datatourisme-reg-occ.csv"
OUT_CSV = "data/poi_embeddings.csv"
OUT_NPY = "data/poi_embeddings.npy"


def build_text(row):
    title = str(row["Nom_du_POI"]).strip() if pd.notna(row["Nom_du_POI"]) else ""
    desc = str(row["Description"]).strip() if pd.notna(row["Description"]) else ""
    return f"{title}. {desc}" if desc else title


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    df = pd.read_csv(SRC)
    if args.limit:
        df = df.head(args.limit)
    texts = df.apply(build_text, axis=1).tolist()

    model = SentenceTransformer(MODEL, device="cpu")

    t0 = time.time()
    emb = model.encode(
        texts, batch_size=256, normalize_embeddings=True,
        show_progress_bar=True, convert_to_numpy=True,
    ).astype(np.float32)
    print(f"{len(texts)} textes en {time.time() - t0:.1f}s")

    out = pd.DataFrame({
        "URI_ID_du_POI": df["URI_ID_du_POI"],
        "Nom_du_POI": df["Nom_du_POI"],
        "texte_embedde": texts,
        "embedding": [json.dumps([round(float(x), 6) for x in v]) for v in emb],
    })
    out.to_csv(OUT_CSV, index=False, encoding="utf-8")
    np.save(OUT_NPY, emb)
    print(f"Ecrit {OUT_CSV} et {OUT_NPY} ({emb.shape})")


if __name__ == "__main__":
    main()
