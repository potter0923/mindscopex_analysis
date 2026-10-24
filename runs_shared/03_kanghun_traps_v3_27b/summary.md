# CRT text-generation result summary

- Generated at: `2026-10-24T14:39:09+00:00`
- Dataset: `kanghun_traps_v3:qwen_native`
- Dataset reference: kanghun_traps_v3
- Final responses: **744**

## Headline results

`Hallucination` is an operational bucket for final answers that are neither only the correct answer nor only the known lure. It includes unresolved `both` and `other` responses, so inspect the quality table before interpreting it as factual fabrication.

| Model | Mode | N | Correct | Lure | Hallucination | Accuracy | Retried |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | 372 | 321 | 51 | 0 | 86.3% | 0 |
| Qwen3.5-27B | thinking | 372 | 358 | 14 | 0 | 96.2% | 0 |

## Results by CRT family

Wilson intervals below treat rows as independent Bernoulli observations. When the same items are repeated across multiple sampling seeds, use an item-clustered bootstrap for inferential intervals instead of interpreting the pooled Wilson interval as a confidence interval.

| Model | Mode | Family | N | Correct | Lure | Other | Accuracy | Lure rate (Wilson 95% CI) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | memo_override | 72 | 30 | 42 | 0 | 41.7% | 58.3% [46.8%, 69.0%] |
| Qwen3.5-27B | thinking | memo_override | 72 | 69 | 3 | 0 | 95.8% | 4.2% [1.4%, 11.5%] |
| Qwen3.5-27B | non_thinking | familiar_riddle_swap | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | thinking | familiar_riddle_swap | 24 | 22 | 2 | 0 | 91.7% | 8.3% [2.3%, 25.8%] |
| Qwen3.5-27B | non_thinking | negation_neglect | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | thinking | negation_neglect | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | non_thinking | surface_number_compare | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | thinking | surface_number_compare | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | non_thinking | pattern_break | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | thinking | pattern_break | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | non_thinking | false_premise | 18 | 9 | 9 | 0 | 50.0% | 50.0% [29.0%, 71.0%] |
| Qwen3.5-27B | thinking | false_premise | 18 | 13 | 5 | 0 | 72.2% | 27.8% [12.5%, 50.9%] |
| Qwen3.5-27B | non_thinking | memo_override__control | 72 | 72 | 0 | 0 | 100.0% | 0.0% [0.0%, 5.1%] |
| Qwen3.5-27B | thinking | memo_override__control | 72 | 72 | 0 | 0 | 100.0% | 0.0% [0.0%, 5.1%] |
| Qwen3.5-27B | non_thinking | familiar_riddle_swap__control | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | thinking | familiar_riddle_swap__control | 24 | 21 | 3 | 0 | 87.5% | 12.5% [4.3%, 31.0%] |
| Qwen3.5-27B | non_thinking | negation_neglect__control | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | thinking | negation_neglect__control | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | non_thinking | surface_number_compare__control | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | thinking | surface_number_compare__control | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | non_thinking | pattern_break__control | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | thinking | pattern_break__control | 24 | 24 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.8%] |
| Qwen3.5-27B | non_thinking | false_premise__control | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | thinking | false_premise__control | 18 | 17 | 1 | 0 | 94.4% | 5.6% [1.0%, 25.8%] |

## Quality and retry diagnostics

| Model | Mode | Format failures | Protocol failures | Retry attempts | Unresolved both | Other |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | 3 | 0 | 0 | 0 | 0 |
| Qwen3.5-27B | thinking | 3 | 0 | 0 | 0 | 0 |

## Responses requiring review

This section includes hallucination/other outcomes, quality failures, and all retried responses so the final sample can be audited.

| Model | Mode | Case | Outcome | Raw label | Final answer | Attempts | Retry reasons | Protocol issue | Format issue |
|---|---|---|---|---|---|---:|---|---|---|
| Qwen3.5-27B | non_thinking | kanghun_traps_v3_feathers_two_pounds__control | correct | correct | they are equal | 1 |  |  | label_or_explanation |
| Qwen3.5-27B | thinking | kanghun_traps_v3_feathers_two_pounds__control | correct | correct | they are equal | 1 |  |  | label_or_explanation |
| Qwen3.5-27B | non_thinking | kanghun_traps_v3_feathers_two_pounds__control | correct | correct | they are equal | 1 |  |  | label_or_explanation |
| Qwen3.5-27B | thinking | kanghun_traps_v3_feathers_two_pounds__control | correct | correct | they are equal | 1 |  |  | label_or_explanation |
| Qwen3.5-27B | non_thinking | kanghun_traps_v3_feathers_two_pounds__control | correct | correct | they are equal | 1 |  |  | label_or_explanation |
| Qwen3.5-27B | thinking | kanghun_traps_v3_feathers_two_pounds__control | correct | correct | they are equal | 1 |  |  | label_or_explanation |

## Retry audit

No response was regenerated.
