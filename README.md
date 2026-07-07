# Inject or Navigate?

**Token-Efficient Retrieval for LLM Analysis of Transactional Legal Documents**

[Mahmoud Hany](https://www.linkedin.com/in/mahmoud-hany-fathalla-6b1690219/), [Mourad ElSheraey](https://www.linkedin.com/in/mourad-elsheraey/), [Mahmoud Said](https://www.linkedin.com/in/mahsaid/), [Peter Naoum](https://www.linkedin.com/in/peternaoum/), *Syntheia Pty Ltd*

📄 **Paper:** arXiv link coming soon; until then see [`paper/inject_or_navigate.pdf`](paper/inject_or_navigate.pdf).

> This repository is the companion dataset + evaluation harness for the paper.

---

## Abstract

Answering questions over a set of transactional legal documents is most simply
done by *injecting* the whole corpus into the LLM's context window on every
query. That baseline maximises retrieval recall, but its token footprint scales
with the corpus rather than the question, and long-context degradation scales
with it. We report what it took to replace full-corpus injection in a
legal-document analysis system, comparing it against two structured retrieval
modes over our proprietary structure-aware chunking: embedding retrieval
(NAVEMBED) and LLM navigation over a compact structured index (NAVINDEX). On a
20-question benchmark with verified ground-truth answers, a
position-bias-controlled, reference-anchored pairwise judge scored semantic
retrieval with reranking tied with injection on 16 of 18 document-bound
questions (injection preferred on 2) while attending to 17.3× fewer input
tokens (a general-text-embedding (GTE) configuration reaches 29.9× at a lower
tie rate); both modes were judged tied on the 2 out-of-scope controls. NAVINDEX
was judged tied on all 18 at a 1.61× smaller total token footprint, a ~56×
smaller answering context, and 25% lower dollar cost. We derive a closed-form
caching-crossover rule: cached injection is cheaper in dollars only while the
corpus stays below roughly ten times the retrieval payload. Scope and
uncertainty are quantified in Section 8.

## What's in this repo

| Path | Contents |
|---|---|
| [`data/`](data) | The scored benchmark: 20 questions with verified reference answers and document mapping (`benchmark_qa.json`), per-document [`sources.md`](data/sources.md), and the 52-question DocNavBench development set (`docnavbench_questions.json`) |
| [`prompts/`](prompts) | The five system prompts used by the pipeline, verbatim from the paper appendix |
| [`harness/`](harness) | A public, API-optional kit that runs the paper's **evaluation protocol** end-to-end with one public INJECT-vs-NAVEMBED baseline |
| [`paper/`](paper) | The compiled paper PDF (placeholder until the arXiv link is live) |

## Dataset

### Scored benchmark: [`data/benchmark_qa.json`](data/benchmark_qa.json)

**20 questions** over **6 public transactional documents** across three practice
areas: facility agreements (`FA`), limited partnership agreements (`LP`), and
share/asset purchase agreements + disclosure schedules (`SP`). **18** are
document-bound (three per document) with verified reference answers; **2** are
out-of-scope controls whose answers are absent from every document by
construction, testing correct declination rather than retrieval.

Each record:

```json
{
  "id": "FA_fluor_facility_amendment_1.pdf_Q1",
  "doc": "FA_fluor_amendment",
  "text": "What is the total facility size of the revolving loan agreement that was amended, and who serves as the administrative agent for this facility?",
  "answer": "$1,800,000,000; BNP Paribas serves as the Administrative Agent."
}
```

| Field | Description |
|---|---|
| `id` | Question identifier: source-file stem + `_Q<n>`; controls are `out_of_scope_Q1` / `out_of_scope_Q2` |
| `doc` | Short document key (also used in the harness and [`data/sources.md`](data/sources.md)); `OOS` for the controls |
| `text` | The question |
| `answer` | The verified reference answer |

Documents are **public filings** (SEC EDGAR); no document text is redistributed
here; [`harness/fetch_docs.py`](harness/fetch_docs.py) fetches them from source
(see [`data/sources.md`](data/sources.md)).

### DocNavBench: [`data/docnavbench_questions.json`](data/docnavbench_questions.json)

**52 questions** (FA 13, LP 17, SP 22) used during development, a different
artifact from the scored benchmark: lawyer-authored, issue-driven, and
document-agnostic (a question may legitimately resolve to "not in the
agreement"), with **no ground-truth answers**, scored by pairwise preference
only. Fields: `id`, `text`, `difficulty` (`high` / `medium`).

**Designed to stress embedding retrieval.** Many DocNavBench questions are
deliberately *compound*: one part is easy to locate (say, the governing law),
while another asks for a specific provision that is very likely absent, so the
correct answer is partly "not in the agreement." That shape is hard for vector
embedding retrieval, which tends to surface passages that merely look topically
similar to the whole question. It is a core motivation for the set: to probe
whether an LLM reasoning over a structured index can outperform conventional
embedding retrieval on questions where the right answer is a partial decline.
For example (`SP-19`):

> Which law governs the agreement, and does the agreement contain any provision
> acknowledging that obligations arising under a regulatory remedies order take
> precedence over the contractual terms in the event of a conflict?

The governing-law clause is trivially retrieved; a provision subordinating the
contract to a regulatory remedies order almost never exists, so a correct
response states the governing law and declines the second part. A full
DocNavBench evaluation of this hypothesis is future work.

**Initial experiments were run on this set**, and the scored evaluation used the
disjoint 20-question set above, so the two do not overlap.

## Scope

The harness reproduces the paper's **evaluation protocol** with a fully public
baseline retriever. Syntheia's structure-aware chunking and the enriched
`*.index.json` files behind the paper's headline NAVEMBED / NAVINDEX runs are
**not** included, so this is a transparent public reference point rather than a
bit-for-bit reproduction of the proprietary pipeline. See
[`harness/README.md`](harness/README.md).

## Acknowledgments

We are grateful to [Horace Wu](https://www.linkedin.com/in/horace-wu/), who
authored the 52-question DocNavBench open-search set and verified the scored
benchmark's reference answers against the source documents, and to
[Mahmoud Abdallah](https://www.linkedin.com/in/mahmoud-abdallah-59929b142/) for
his work on the document-index API and surrounding features.

## License

© Syntheia Pty Ltd, dual-licensed:

- **Dataset, prompts, docs, and the paper** ([`data/`](data), [`prompts/`](prompts), [`paper/`](paper)): [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE). Use freely with attribution.
- **Code** ([`harness/`](harness)): [MIT](harness/LICENSE).

The underlying documents referenced in [`data/sources.md`](data/sources.md) are
public filings owned by their respective filers and are subject to their own
terms; this license covers the content of this repository, not the source
filings.
