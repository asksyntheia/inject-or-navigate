"""Persist each question's top-10 MiniLM-retrieved extract to nav_contexts_minilm.json.

This is the NAVEMBED context that the answering step reads. Run after the documents
have been fetched::

    python3 save_minilm_ctx.py
"""

import json

import numpy as np
from sentence_transformers import SentenceTransformer

from harness import HERE, build_chunks

questions = json.load(open(f"{HERE}/../data/benchmark_qa.json"))
chunks = build_chunks(512, 64)
chunk_texts = [c["text"] for c in chunks]

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
chunk_emb = model.encode(
    chunk_texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False
)
query_emb = model.encode(
    [q["text"] for q in questions], normalize_embeddings=True, show_progress_bar=False
)
similarity = query_emb @ chunk_emb.T

contexts = {}
for qi, question in enumerate(questions):
    ranked = np.argsort(-similarity[qi])[:10]
    retrieved = [chunks[j] for j in ranked]
    context = "\n\n---\n\n".join(f"[{c['doc']}]\n{c['text']}" for c in retrieved)
    contexts[question["id"]] = {
        "doc": question["doc"],
        "context": context,
        "retrieved_docs": [c["doc"] for c in retrieved],
        "ctx_tokens": len(context) // 4,
    }

json.dump(contexts, open(f"{HERE}/nav_contexts_minilm.json", "w"), indent=2)
average = np.mean([v["ctx_tokens"] for v in contexts.values()])
print(f"saved nav_contexts_minilm.json; avg ctx tokens={average:.0f}")
