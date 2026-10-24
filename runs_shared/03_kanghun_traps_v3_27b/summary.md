# CRT text-generation result summary

- Generated at: `2026-10-24T08:46:13+00:00`
- Dataset: `kanghun_traps_v3:qwen_native`
- Dataset reference: kanghun_traps_v3
- Final responses: **248**

## Headline results

`Hallucination` is an operational bucket for final answers that are neither only the correct answer nor only the known lure. It includes unresolved `both` and `other` responses, so inspect the quality table before interpreting it as factual fabrication.

| Model | Mode | N | Correct | Lure | Hallucination | Accuracy | Retried |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | 124 | 107 | 17 | 0 | 86.3% | 0 |
| Qwen3.5-27B | thinking | 124 | 120 | 4 | 0 | 96.8% | 0 |

## Results by CRT family

Wilson intervals below treat rows as independent Bernoulli observations. When the same items are repeated across multiple sampling seeds, use an item-clustered bootstrap for inferential intervals instead of interpreting the pooled Wilson interval as a confidence interval.

| Model | Mode | Family | N | Correct | Lure | Other | Accuracy | Lure rate (Wilson 95% CI) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | memo_override | 24 | 10 | 14 | 0 | 41.7% | 58.3% [38.8%, 75.5%] |
| Qwen3.5-27B | thinking | memo_override | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | non_thinking | familiar_riddle_swap | 8 | 8 | 0 | 0 | 100.0% | 0.0% [0.0%, 32.4%] |
| Qwen3.5-27B | thinking | familiar_riddle_swap | 8 | 7 | 1 | 0 | 87.5% | 12.5% [2.2%, 47.1%] |
| Qwen3.5-27B | non_thinking | negation_neglect | 8 | 8 | 0 | 0 | 100.0% | 0.0% [0.0%, 32.4%] |
| Qwen3.5-27B | thinking | negation_neglect | 8 | 8 | 0 | 0 | 100.0% | 0.0% [0.0%, 32.4%] |
| Qwen3.5-27B | non_thinking | surface_number_compare | 8 | 8 | 0 | 0 | 100.0% | 0.0% [0.0%, 32.4%] |
| Qwen3.5-27B | thinking | surface_number_compare | 8 | 8 | 0 | 0 | 100.0% | 0.0% [0.0%, 32.4%] |
| Qwen3.5-27B | non_thinking | pattern_break | 8 | 8 | 0 | 0 | 100.0% | 0.0% [0.0%, 32.4%] |
| Qwen3.5-27B | thinking | pattern_break | 8 | 8 | 0 | 0 | 100.0% | 0.0% [0.0%, 32.4%] |
| Qwen3.5-27B | non_thinking | false_premise | 6 | 3 | 3 | 0 | 50.0% | 50.0% [18.8%, 81.2%] |
| Qwen3.5-27B | thinking | false_premise | 6 | 5 | 1 | 0 | 83.3% | 16.7% [3.0%, 56.4%] |
| Qwen3.5-27B | non_thinking | memo_override__control | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | thinking | memo_override__control | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | non_thinking | familiar_riddle_swap__control | 8 | 8 | 0 | 0 | 100.0% | 0.0% [0.0%, 32.4%] |
| Qwen3.5-27B | thinking | familiar_riddle_swap__control | 8 | 7 | 1 | 0 | 87.5% | 12.5% [2.2%, 47.1%] |
| Qwen3.5-27B | non_thinking | negation_neglect__control | 8 | 8 | 0 | 0 | 100.0% | 0.0% [0.0%, 32.4%] |
| Qwen3.5-27B | thinking | negation_neglect__control | 8 | 8 | 0 | 0 | 100.0% | 0.0% [0.0%, 32.4%] |
| Qwen3.5-27B | non_thinking | surface_number_compare__control | 8 | 8 | 0 | 0 | 100.0% | 0.0% [0.0%, 32.4%] |
| Qwen3.5-27B | thinking | surface_number_compare__control | 8 | 8 | 0 | 0 | 100.0% | 0.0% [0.0%, 32.4%] |
| Qwen3.5-27B | non_thinking | pattern_break__control | 8 | 8 | 0 | 0 | 100.0% | 0.0% [0.0%, 32.4%] |
| Qwen3.5-27B | thinking | pattern_break__control | 8 | 8 | 0 | 0 | 100.0% | 0.0% [0.0%, 32.4%] |
| Qwen3.5-27B | non_thinking | false_premise__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | thinking | false_premise__control | 6 | 5 | 1 | 0 | 83.3% | 16.7% [3.0%, 56.4%] |

## Quality and retry diagnostics

| Model | Mode | Format failures | Protocol failures | Retry attempts | Unresolved both | Other |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | 1 | 0 | 0 | 0 | 0 |
| Qwen3.5-27B | thinking | 1 | 0 | 0 | 0 | 0 |

## Responses requiring review

This section includes hallucination/other outcomes, quality failures, and all retried responses so the final sample can be audited.

| Model | Mode | Case | Outcome | Raw label | Final answer | Attempts | Retry reasons | Protocol issue | Format issue |
|---|---|---|---|---|---|---:|---|---|---|
| Qwen3.5-27B | non_thinking | kanghun_traps_v3_feathers_two_pounds__control | correct | correct | they are equal | 1 |  |  | label_or_explanation |
| Qwen3.5-27B | thinking | kanghun_traps_v3_feathers_two_pounds__control | correct | correct | they are equal | 1 |  |  | label_or_explanation |

## Retry audit

No response was regenerated.
