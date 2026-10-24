# CRT text-generation result summary

- Generated at: `2026-10-24T15:46:12+00:00`
- Dataset: `kanghun_traps_v4:qwen_native`
- Dataset reference: kanghun_traps_v4
- Final responses: **288**

## Headline results

`Hallucination` is an operational bucket for final answers that are neither only the correct answer nor only the known lure. It includes unresolved `both` and `other` responses, so inspect the quality table before interpreting it as factual fabrication.

| Model | Mode | N | Correct | Lure | Hallucination | Accuracy | Retried |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | 144 | 132 | 12 | 0 | 91.7% | 0 |
| Qwen3.5-27B | thinking | 144 | 140 | 4 | 0 | 97.2% | 0 |

## Results by CRT family

Wilson intervals below treat rows as independent Bernoulli observations. When the same items are repeated across multiple sampling seeds, use an item-clustered bootstrap for inferential intervals instead of interpreting the pooled Wilson interval as a confidence interval.

| Model | Mode | Family | N | Correct | Lure | Other | Accuracy | Lure rate (Wilson 95% CI) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | relative_reference | 18 | 15 | 3 | 0 | 83.3% | 16.7% [5.8%, 39.2%] |
| Qwen3.5-27B | thinking | relative_reference | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | non_thinking | percent_symmetry | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | thinking | percent_symmetry | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | non_thinking | instruction_inversion | 18 | 15 | 3 | 0 | 83.3% | 16.7% [5.8%, 39.2%] |
| Qwen3.5-27B | thinking | instruction_inversion | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | non_thinking | wordplay_referent | 18 | 15 | 3 | 0 | 83.3% | 16.7% [5.8%, 39.2%] |
| Qwen3.5-27B | thinking | wordplay_referent | 18 | 15 | 3 | 0 | 83.3% | 16.7% [5.8%, 39.2%] |
| Qwen3.5-27B | non_thinking | relative_reference__control | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | thinking | relative_reference__control | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | non_thinking | percent_symmetry__control | 18 | 15 | 3 | 0 | 83.3% | 16.7% [5.8%, 39.2%] |
| Qwen3.5-27B | thinking | percent_symmetry__control | 18 | 17 | 1 | 0 | 94.4% | 5.6% [1.0%, 25.8%] |
| Qwen3.5-27B | non_thinking | instruction_inversion__control | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | thinking | instruction_inversion__control | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | non_thinking | wordplay_referent__control | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | thinking | wordplay_referent__control | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |

## Quality and retry diagnostics

| Model | Mode | Format failures | Protocol failures | Retry attempts | Unresolved both | Other |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | 0 | 0 | 0 | 0 | 0 |
| Qwen3.5-27B | thinking | 0 | 0 | 0 | 0 | 0 |

## Responses requiring review

This section includes hallucination/other outcomes, quality failures, and all retried responses so the final sample can be audited.

No responses require review.

## Retry audit

No response was regenerated.
