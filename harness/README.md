# Evaluation harness

A **fully public, API-optional** way to run the paper's evaluation protocol
end-to-end on the released 20-question set.

## What this is and what it is not

This kit reproduces the paper's **evaluation protocol**, not its proprietary
production pipeline:

- **Included:** the released dataset (`../data/`), the paper's prompts
  (`../prompts/`), the paired forward/reverse judging protocol with the
  both-directions-must-agree rule, token-footprint accounting, and an
  independent anchor-accuracy cross-check, plus **one fully public
  INJECT-vs-NAVEMBED baseline** so the protocol is runnable without any proprietary
  infrastructure.
- **Not included:** Syntheia's structure-aware chunking and the enriched
  `*.index.json` files that the paper's headline NAVEMBED / NAVINDEX runs use
  (author decision). The baseline retriever here is a public
  sentence-transformer over fixed-size chunks, so the exact headline numbers of
  the proprietary pipeline are **not** expected to be reproduced bit-for-bit;
  this is a transparent public reference point.

The recorded baseline result is in [`results/RESULTS.json`](results/RESULTS.json).

## The baseline retriever

Fixed-size 512-token chunks (64 overlap) over the six-document corpus,
`all-MiniLM-L6-v2` cosine similarity, top-10, no rerank. `harness_rerank.py`
adds an optional retrieve-40 → BGE-rerank-10 arm (slow on CPU, not required).

## Pipeline

Python does deterministic work only (chunking, local embedding, retrieval,
scoring, aggregation). The **answering** and **judging** steps call an LLM;
supply your own (Anthropic API, or Claude Code subagents as stand-ins; the
answerer role matches `claude-sonnet-4-6`, the judge `claude-opus-4-7`). The
exact prompts are in [`../prompts/`](../prompts).

```bash
cd harness
pip install -r requirements.txt          # sentence-transformers, tiktoken, numpy, scikit-learn

# 1. Data (deterministic)
python3 fetch_docs.py                     # download the 6 SEC filings -> docs/*.txt  (skip if present)
#    questions + reference answers + doc mapping are read directly from ../data/benchmark_qa.json

# 2. Retrieval baseline (deterministic)
python3 harness.py sentence-transformers/all-MiniLM-L6-v2 512 64 10   # anchor recall@10
python3 save_minilm_ctx.py                # per-question top-10 extract -> nav_contexts_minilm.json
python3 prep_groups.py                    # corpus_inject.txt + {inject,nav}_group_{FA,LP,SP}.md

# 3. ANSWER (LLM): 6 answerer runs (3 INJECT + 3 NAVEMBED) -> ans/{inject,nav}_{FA,LP,SP}.json
#    INJECT reads corpus_inject.txt; NAVEMBED reads only each question's <provisions> block.
#    Use the prompts in ../prompts/{inject_answer_system,navigate_answer_system}.md
python3 score.py                          # anchor-accuracy + build judge_{fwd,rev}.md, judge_input.json

# 4. JUDGE (LLM): forward + reverse -> judge_{fwd,rev}_out.json
#    Use ../prompts/judge_groundtruth_system.md (reference-anchored).
python3 aggregate.py                      # both-directions-agree rule -> results/RESULTS.json
```

`fetch_docs.py`, the `docs/` texts, retrieval outputs, answerer/judge I/O, and
`corpus_inject.txt` are all regenerated locally and are **not** committed; the
repo ships code, the dataset, and the recorded `RESULTS.json` only.

## Protocol notes

- **Paired verdict.** Each question is answered by both arms and judged twice
  (forward and reverse, positions swapped). A win counts **only when both
  directions agree**; any disagreement or hedge is a tie. This controls the
  position bias documented for LLM judges.
- **Anchor-accuracy** is an independent, model-free cross-check: does the answer
  contain the verified gold fact? It is reported alongside the judge verdicts,
  not merged into them.
- **Out-of-scope controls.** Two questions are unanswerable by construction; a
  correct arm declines with the exact silence string.
