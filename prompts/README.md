# System prompts

The five system prompts used by the pipeline, reproduced verbatim from the
paper (Appendix "System Prompts"). Runtime substitutions are shown as
`{placeholder}`.

| File | Prompt | Used by |
|---|---|---|
| `inject_answer_system.md` | `INJECT_ANSWER_SYSTEM` | INJECT baseline: answer from the full corpus |
| `navigate_answer_system.md` | `NAVIGATE_ANSWER_SYSTEM` | NAVIGATE answering: answer from the retrieved extract only |
| `navindex_scan_system.md` | `NAVINDEX_SCAN_SYSTEM` | NAVINDEX Step 1: plan which nodes to fetch from the structured index |
| `judge_groundtruth_system.md` | `JUDGE_GROUNDTRUTH_SYSTEM` | Scored judging: reference-anchored pairwise verdict |
| `judge_preference_system.md` | `JUDGE_PREFERENCE_SYSTEM` | Development judging: reference-free pairwise verdict |

The scored 20-question runs use the reference-anchored ground-truth judge;
the preference judge is included for completeness (it scored the development
phase). `NAVINDEX_SCAN_SYSTEM` describes the proprietary structured index,
which is not shipped here; it is included so the retrieval-planning prompt is
on the public record.
