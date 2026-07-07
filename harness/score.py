"""Objective anchor-accuracy scorer and judge-input builder.

Loads the INJECT and NAVEMBED answers (``ans/{inject,nav}_{FA,LP,SP}.json``), checks
each against the decisive gold facts for its question, and writes
``judge_input.json`` for the pairwise judging step. Run after the answering
step::

    python3 score.py
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
questions = {q["id"]: q for q in json.load(open(f"{HERE}/../data/benchmark_qa.json"))}

# The answer must contain these decisive gold facts. Within a group (tuple) any
# variant counts; every group in the list is required. "DECLINE" means a correct
# answer refuses to answer (the out-of-scope controls).
ANSWER_ANCHORS = {
    "FA_fluor_facility_amendment_1.pdf_Q1": [
        (r"1,?800,?000,?000", r"1\.8\s*billion"),
        (r"BNP\s+Paribas",),
    ],
    "FA_fluor_facility_amendment_1.pdf_Q2": [(r"25,?000,?000", r"25\s*million")],
    "FA_fluor_facility_amendment_1.pdf_Q3": [(r"10,?000,?000,?000", r"10\s*billion")],
    "FA_generac_2024_amendment.pdf_Q1": [
        (r"30\s*million", r"30,?000,?000"),
        (r"500\s*million", r"500,?000,?000"),
    ],
    "FA_generac_2024_amendment.pdf_Q2": [(r"July\s+3,?\s+2031", r"2031")],
    "FA_generac_2024_amendment.pdf_Q3": [(r"credit\s+spread\s+adjustment",)],
    "LP_thomas_green_fund_lpa.pdf_Q1": [
        (r"500\s*million", r"500,?000,?000"),
        (r"10\s*million", r"10,?000,?000"),
    ],
    "LP_thomas_green_fund_lpa.pdf_Q2": [(r"silver",), (r"Energy\s*Star",)],
    "LP_thomas_green_fund_lpa.pdf_Q3": [
        (r"20\s*%", r"twenty\s+percent"),
        (r"75\s*%", r"seventy-five\s+percent"),
    ],
    "LP_carlyle_pe_partners_lpa.pdf_Q1": [(r"12\.5",), (r"\b5\s*%", r"5\s*percent")],
    "LP_carlyle_pe_partners_lpa.pdf_Q2": [
        (r"\b5\s*%", r"5\s*percent"),
        (r"two|2\s*\(?2?\)?\s*year|2\s*year",),
    ],
    "LP_carlyle_pe_partners_lpa.pdf_Q3": [(r"30\s*%", r"thirty\s+percent")],
    "SP_first_avenue_networks_disclosure_schedule.pdf_Q1": [(r"14,?313,?868",)],
    "SP_first_avenue_networks_disclosure_schedule.pdf_Q2": [
        (r"20\s*%", r"twenty\s+percent"),
        (r"Neil\s+Subin", r"Subin"),
        (r"Aspen",),
    ],
    "SP_first_avenue_networks_disclosure_schedule.pdf_Q3": [
        (r"3\.8\s*million", r"3,?800,?000"),
        (r"use\s+tax", r"personal\s+property"),
    ],
    "SP_meta_shutterstock_giphy_spa.pdf_Q1": [(r"128,?000,?000", r"128\s*million")],
    "SP_meta_shutterstock_giphy_spa.pdf_Q2": [(r"20\s*%", r"twenty\s+percent")],
    "SP_meta_shutterstock_giphy_spa.pdf_Q3": [(r"75,?000,?000", r"75\s*million")],
    "out_of_scope_Q1": "DECLINE",
    "out_of_scope_Q2": "DECLINE",
}

DECLINE_PATTERN = (
    r"do(?:es)? not contain|not applicable|no answer|cannot.*answer|not.*provided"
)


def accuracy(answer, spec):
    """Fraction of required gold facts present (1.0/0.0 for DECLINE questions)."""
    if spec == "DECLINE":
        return 1.0 if re.search(DECLINE_PATTERN, answer, re.I) else 0.0
    matched = sum(1 for group in spec if any(re.search(v, answer, re.I) for v in group))
    return matched / len(spec)


def load_answers(mode):
    """Load ``ans/{mode}_{FA,LP,SP}.json`` into an ``{id: answer}`` map."""
    answers = {}
    for group in ["FA", "LP", "SP"]:
        path = f"{HERE}/ans/{mode}_{group}.json"
        if os.path.exists(path):
            for record in json.load(open(path)):
                answers[record["id"]] = record["answer"]
    return answers


inject_answers = load_answers("inject")
nav_answers = load_answers("nav")
print(f"loaded inject={len(inject_answers)}/20  nav={len(nav_answers)}/20")

if len(inject_answers) < 20 or len(nav_answers) < 20:
    missing = [i for i in questions if i not in inject_answers or i not in nav_answers]
    print("MISSING:", missing[:8], "..." if len(missing) > 8 else "")
    sys.exit(0)

rows = []
inject_total = nav_total = 0.0
for qid, question in questions.items():
    inject_acc = accuracy(inject_answers[qid], ANSWER_ANCHORS[qid])
    nav_acc = accuracy(nav_answers[qid], ANSWER_ANCHORS[qid])
    inject_total += inject_acc
    nav_total += nav_acc
    rows.append(
        {
            "id": qid,
            "question": question["text"],
            "reference": question["answer"],
            "inject": inject_answers[qid],
            "nav": nav_answers[qid],
            "acc_inject": inject_acc,
            "acc_nav": nav_acc,
        }
    )
    if abs(inject_acc - nav_acc) < 1e-9:
        flag = ""
    elif inject_acc > nav_acc:
        flag = "  <INJECT>"
    else:
        flag = "  <NAVEMBED>"
    print(f"  inj={inject_acc:.2f} nav={nav_acc:.2f}  {qid}{flag}")

json.dump(rows, open(f"{HERE}/judge_input.json", "w"), indent=2)
print(
    f"\nAUTO ANCHOR-ACCURACY (gold fact present in answer): "
    f"INJECT={inject_total / 20 * 100:.0f}%  NAVEMBED={nav_total / 20 * 100:.0f}%  (n=20)"
)
print("wrote judge_input.json")
