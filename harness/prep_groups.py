"""Build the answerer inputs from the dataset, retrieved contexts, and docs/.

Produces:
  - corpus_inject.txt          : all 6 docs tagged <document doc_id="..."> (INJECT context)
  - inject_group_{FA,LP,SP}.md : question lists per practice area (INJECT reads the corpus)
  - nav_group_{FA,LP,SP}.md    : per question, the retrieved <provisions> extract (NAVEMBED input)

Run after save_minilm_ctx.py::

    python3 prep_groups.py
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = [
    "FA_fluor_amendment",
    "FA_generac_amendment",
    "LP_thomas_green",
    "LP_carlyle",
    "SP_first_avenue",
    "SP_meta_giphy",
]

questions = json.load(open(f"{HERE}/../data/benchmark_qa.json"))
nav_contexts = json.load(open(f"{HERE}/nav_contexts_minilm.json"))

# INJECT corpus: every document, verbatim, tagged.
documents = [
    f'<document doc_id="{doc}">\n'
    + open(f"{HERE}/docs/{doc}.txt").read()
    + "\n</document>"
    for doc in DOCS
]
open(f"{HERE}/corpus_inject.txt", "w").write("\n\n".join(documents))

# Group questions by practice area (the SP group also carries the 2 controls).
groups = {"FA": [], "LP": [], "SP": []}
for question in questions:
    if question["id"].startswith("FA"):
        group = "FA"
    elif question["id"].startswith("LP"):
        group = "LP"
    else:
        group = "SP"
    groups[group].append(question)

for group, items in groups.items():
    inject_md, nav_md = [], []
    for question in items:
        inject_md.append(f"### {question['id']}\n{question['text']}\n")
        context = nav_contexts.get(question["id"], {}).get(
            "context", "(no context retrieved)"
        )
        nav_md.append(
            f"### {question['id']}\n{question['text']}\n\n"
            f"<provisions>\n{context}\n</provisions>\n"
        )
    open(f"{HERE}/inject_group_{group}.md", "w").write("\n".join(inject_md))
    open(f"{HERE}/nav_group_{group}.md", "w").write("\n".join(nav_md))
    print(
        f"{group}: {len(items)} questions -> inject_group_{group}.md, nav_group_{group}.md"
    )

print("wrote corpus_inject.txt + group files")
