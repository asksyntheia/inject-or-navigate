"""Combine forward + reverse judge verdicts into results/RESULTS.json.

Applies the paper's rule (a win counts only when both directions agree; otherwise
a tie), folds in objective anchor-accuracy and token footprint, and writes
``results/RESULTS.json``. Run after both judge passes have written their
verdicts::

    python3 aggregate.py

Inputs: ``judge_fwd_out.json`` (A=inject, B=nav), ``judge_rev_out.json``
(A=nav, B=inject), ``judge_input.json`` (acc_inject/acc_nav),
``nav_contexts_minilm.json``, ``corpus_inject.txt``.
"""

import json
import os

import numpy as np
import tiktoken

HERE = os.path.dirname(os.path.abspath(__file__))

# judge_fwd_out.json ordered answers as A=inject, B=nav; the reverse pass swaps.
forward = {r["id"]: r["verdict"] for r in json.load(open(f"{HERE}/judge_fwd_out.json"))}
reverse = {r["id"]: r["verdict"] for r in json.load(open(f"{HERE}/judge_rev_out.json"))}
rows = json.load(open(f"{HERE}/judge_input.json"))
nav_contexts = json.load(open(f"{HERE}/nav_contexts_minilm.json"))
corpus_tokens = len(
    tiktoken.get_encoding("cl100k_base").encode(
        open(f"{HERE}/corpus_inject.txt").read()
    )
)


def verdict(qid):
    """Both directions must agree for a win; otherwise it is a tie."""
    fwd, rev = forward[qid], reverse[qid]
    if fwd == "A" and rev == "B":
        return "INJECT"
    if fwd == "B" and rev == "A":
        return "NAVEMBED"
    return "tie"


counts = {"tie": 0, "INJECT": 0, "NAVEMBED": 0}
inject_total = nav_total = 0.0
nav_token_counts = []
print(f"{'question':52s} fwd rev -> verdict")
for row in rows:
    qid = row["id"]
    result = verdict(qid)
    counts[result] += 1
    inject_total += row["acc_inject"]
    nav_total += row["acc_nav"]
    nav_token_counts.append(nav_contexts[qid]["ctx_tokens"])
    mark = {"INJECT": "  <INJECT win>", "NAVEMBED": "  <NAVEMBED win>", "tie": ""}[
        result
    ]
    print(f"{qid:52s}  {forward[qid]:3s} {reverse[qid]:3s} -> {result:8s}{mark}")

nav_avg_tokens = float(np.mean(nav_token_counts))
results = {
    "n": len(rows),
    "public_baseline": {
        "ties": counts["tie"],
        "inject_wins": counts["INJECT"],
        "nav_wins": counts["NAVEMBED"],
        "acc_inject": f"{inject_total / len(rows) * 100:.0f}%",
        "acc_nav": f"{nav_total / len(rows) * 100:.0f}%",
        "footprint_reduction": f"~{corpus_tokens / nav_avg_tokens:.1f}x",
        "inject_tokens_per_q": corpus_tokens,
        "nav_tokens_per_q": round(nav_avg_tokens),
    },
    "paper_reported": {
        "RUN-012_rerank": {"ties": 18, "inject": 2, "nav": 0, "red": "17.3x"},
        "RUN-009_GTE": {"ties": 15, "inject": 4, "nav": 1, "red": "29.9x"},
    },
}
json.dump(results, open(f"{HERE}/results/RESULTS.json", "w"), indent=2)
print(
    f"\nPairwise (both-directions-agree): "
    f"TIES={counts['tie']} INJECT={counts['INJECT']} NAVEMBED={counts['NAVEMBED']}"
)
print(
    f"Anchor-accuracy: INJECT={inject_total / len(rows) * 100:.0f}%  "
    f"NAVEMBED={nav_total / len(rows) * 100:.0f}%"
)
print(
    f"Footprint/query: INJECT={corpus_tokens:,}  NAVEMBED~{nav_avg_tokens:.0f}  "
    f"reduction~{corpus_tokens / nav_avg_tokens:.1f}x"
)
print("wrote RESULTS.json")
