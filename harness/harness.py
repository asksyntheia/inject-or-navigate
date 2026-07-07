"""Baseline retrieval: fixed-size chunking + sentence-transformer cosine top-k.

Chunks the six-document corpus into fixed-size token windows, embeds them with
the given sentence-transformer model, retrieves the top-k chunks per question by
cosine similarity, and reports anchor recall (whether the retrieved context
contains the distinctive gold fact for each answerable question).

Usage::

    python3 harness.py [model] [chunk_size] [overlap] [top_k]
    python3 harness.py sentence-transformers/all-MiniLM-L6-v2 512 64 10

Writes ``retrieval_<model>_<size>_<topk>.json``. ``build_chunks``, ``ANCHORS``,
and ``anchors_in`` are imported by the other retrieval scripts.
"""

import json
import os
import re
import sys

import numpy as np
import tiktoken

HERE = os.path.dirname(os.path.abspath(__file__))
ENCODER = tiktoken.get_encoding("cl100k_base")

DOCS = [
    "FA_fluor_amendment",
    "FA_generac_amendment",
    "LP_thomas_green",
    "LP_carlyle",
    "SP_first_avenue",
    "SP_meta_giphy",
]


def chunk_doc(text, size, overlap):
    """Split text into overlapping fixed-size token windows."""
    tokens = ENCODER.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        chunks.append(ENCODER.decode(tokens[start : start + size]))
        if start + size >= len(tokens):
            break
        start += size - overlap
    return chunks


def build_chunks(size, overlap):
    """Chunk every document into ``{doc, idx, text}`` records."""
    records = []
    for doc in DOCS:
        text = open(f"{HERE}/docs/{doc}.txt").read()
        for idx, chunk in enumerate(chunk_doc(text, size, overlap)):
            records.append({"doc": doc, "idx": idx, "text": chunk})
    return records


# Distinctive gold anchors per question: the most-identifying string(s) for the
# answer's location. A question is "recalled" when its anchors appear in the
# retrieved context. Out-of-scope controls have no anchors.
ANCHORS = {
    "FA_fluor_facility_amendment_1.pdf_Q1": [r"1,800,000,000", r"BNP\s+Paribas"],
    "FA_fluor_facility_amendment_1.pdf_Q2": [r"25,000,000"],
    "FA_fluor_facility_amendment_1.pdf_Q3": [r"10,000,000,000"],
    "FA_generac_2024_amendment.pdf_Q1": [r"\$500\s*million", r"\$30\s*million"],
    "FA_generac_2024_amendment.pdf_Q2": [r"July\s+3,?\s+2031"],
    "FA_generac_2024_amendment.pdf_Q3": [r"credit\s+spread\s+adjustment"],
    "LP_thomas_green_fund_lpa.pdf_Q1": [r"\$500\s*million", r"\$10\s*million"],
    "LP_thomas_green_fund_lpa.pdf_Q2": [r"Energy\s*Star"],
    "LP_thomas_green_fund_lpa.pdf_Q3": [r"seventy-five\s+percent", r"twenty\s+percent"],
    "LP_carlyle_pe_partners_lpa.pdf_Q1": [r"12\.5%"],
    "LP_carlyle_pe_partners_lpa.pdf_Q2": [r"Early\s+Redemption\s+Deduction"],
    "LP_carlyle_pe_partners_lpa.pdf_Q3": [r"Leverage\s+Target"],
    "SP_first_avenue_networks_disclosure_schedule.pdf_Q1": [r"14,313,868"],
    "SP_first_avenue_networks_disclosure_schedule.pdf_Q2": [r"Neil\s+Subin"],
    "SP_first_avenue_networks_disclosure_schedule.pdf_Q3": [r"3\.8\s*million"],
    "SP_meta_shutterstock_giphy_spa.pdf_Q1": [r"128,000,000"],
    "SP_meta_shutterstock_giphy_spa.pdf_Q2": [r"Transferred\s+Employees"],
    "SP_meta_shutterstock_giphy_spa.pdf_Q3": [r"75,000,000"],
    "out_of_scope_Q1": [],
    "out_of_scope_Q2": [],
}


def anchors_in(text, patterns):
    """Return the anchor patterns that appear in ``text`` (case-insensitive)."""
    return [p for p in patterns if re.search(p, text, re.I)]


def main(model_name, size, overlap, top_k):
    from sentence_transformers import SentenceTransformer

    questions = json.load(open(f"{HERE}/../data/benchmark_qa.json"))
    chunks = build_chunks(size, overlap)
    chunk_texts = [c["text"] for c in chunks]
    print(
        f"model={model_name} chunk={size}/{overlap} -> {len(chunks)} chunks; embedding...",
        file=sys.stderr,
    )
    model = SentenceTransformer(model_name)
    is_bge = "bge" in model_name.lower()
    chunk_emb = model.encode(
        chunk_texts, batch_size=64, normalize_embeddings=True, show_progress_bar=False
    )
    # BGE models expect a retrieval-instruction prefix on the query side.
    query_texts = [
        (
            ("Represent this sentence for searching relevant passages: " + q["text"])
            if is_bge
            else q["text"]
        )
        for q in questions
    ]
    query_emb = model.encode(
        query_texts, normalize_embeddings=True, show_progress_bar=False
    )
    similarity = query_emb @ chunk_emb.T

    results = []
    hit_all = hit_any = scored = 0
    for qi, question in enumerate(questions):
        ranked = np.argsort(-similarity[qi])[:top_k]
        retrieved = [chunks[j] for j in ranked]
        context = "\n".join(c["text"] for c in retrieved)
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
        right_doc = (
            question["doc"] in retrieved_docs if question["doc"] != "OOS" else None
        )
        results.append(
            {
                "id": question["id"],
                "doc": question["doc"],
                "retrieved_docs": retrieved_docs,
                "status": status,
                "top_chunk_idx": [(c["doc"], c["idx"]) for c in retrieved[:3]],
            }
        )
        print(f"  {status:7s} {question['id']:55s} right_doc_in_topk={right_doc}")

    print(
        f"\nANCHOR RECALL@{top_k} (18 answerable): "
        f"all-anchors={hit_all}/{scored}  any-anchor={hit_any}/{scored}"
    )
    out_path = f"{HERE}/retrieval_{os.path.basename(model_name)}_{size}_{top_k}.json"
    json.dump(results, open(out_path, "w"), indent=2)


if __name__ == "__main__":
    main(
        sys.argv[1] if len(sys.argv) > 1 else "sentence-transformers/all-MiniLM-L6-v2",
        int(sys.argv[2]) if len(sys.argv) > 2 else 512,
        int(sys.argv[3]) if len(sys.argv) > 3 else 64,
        int(sys.argv[4]) if len(sys.argv) > 4 else 10,
    )
