"""Optional retrieve-then-rerank arm: MiniLM top-40 -> BGE cross-encoder top-10.

Mirrors the paper's semantic+rerank pipeline shape. Slow on CPU and not required
for the baseline result. Writes ``nav_contexts.json``.
"""

import json
import sys

import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer

from harness import ANCHORS, HERE, anchors_in, build_chunks

questions = json.load(open(f"{HERE}/../data/benchmark_qa.json"))
chunks = build_chunks(512, 64)
chunk_texts = [c["text"] for c in chunks]

print(f"{len(chunks)} chunks; first-stage embed (MiniLM)...", file=sys.stderr)
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
chunk_emb = embedder.encode(
    chunk_texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False
)
query_emb = embedder.encode(
    [q["text"] for q in questions], normalize_embeddings=True, show_progress_bar=False
)
similarity = query_emb @ chunk_emb.T

print("loading cross-encoder bge-reranker-v2-m3 (cached)...", file=sys.stderr)
reranker = CrossEncoder("BAAI/bge-reranker-v2-m3", max_length=512)

contexts = {}
hit_all = hit_any = scored = 0
for qi, question in enumerate(questions):
    candidates = list(np.argsort(-similarity[qi])[:40])
    pairs = [[question["text"], chunks[j]["text"]] for j in candidates]
    rerank_scores = reranker.predict(pairs, batch_size=32, show_progress_bar=False)
    top = [candidates[j] for j in np.argsort(-np.array(rerank_scores))][:10]
    retrieved = [chunks[j] for j in top]
    context = "\n\n---\n\n".join(f"[{c['doc']}]\n{c['text']}" for c in retrieved)
    patterns = ANCHORS.get(question["id"], [])
    if patterns:
        scored += 1
        found = anchors_in(context, patterns)
        all_found = len(found) == len(patterns)
        any_found = len(found) > 0
        hit_all += all_found
        hit_any += any_found
        if all_found:
            status = "ALL"
        elif any_found:
            status = "PARTIAL"
        else:
            status = "MISS"
    else:
        status = "OOS"
    retrieved_docs = [c["doc"] for c in retrieved]
    contexts[question["id"]] = {
        "doc": question["doc"],
        "context": context,
        "retrieved_docs": retrieved_docs,
        "status": status,
        "ctx_tokens": len(context) // 4,
    }
    print(f"  {status:7s} {question['id']:55s} docs={sorted(set(retrieved_docs))}")

print(
    f"\nRERANK ANCHOR RECALL@10 (18 answerable): "
    f"all={hit_all}/{scored}  any={hit_any}/{scored}"
)
avg_tokens = np.mean([v["ctx_tokens"] for v in contexts.values()])
print(f"avg retrieved context ~{avg_tokens:.0f} tokens/question (vs INJECT ~163K)")
json.dump(contexts, open(f"{HERE}/nav_contexts.json", "w"), indent=2)
print("saved nav_contexts.json", file=sys.stderr)
