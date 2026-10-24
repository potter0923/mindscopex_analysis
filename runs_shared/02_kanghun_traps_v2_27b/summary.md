# CRT text-generation result summary

- Generated at: `2026-10-24T17:09:07+00:00`
- Dataset: `kanghun_traps_v2:qwen_native`
- Dataset reference: kanghun_traps_v2
- Final responses: **216**

## Headline results

`Hallucination` is an operational bucket for final answers that are neither only the correct answer nor only the known lure. It includes unresolved `both` and `other` responses, so inspect the quality table before interpreting it as factual fabrication.

| Model | Mode | N | Correct | Lure | Hallucination | Accuracy | Retried |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | 108 | 93 | 15 | 0 | 86.1% | 0 |
| Qwen3.5-27B | thinking | 108 | 104 | 4 | 0 | 96.3% | 0 |

## Results by CRT family

Wilson intervals below treat rows as independent Bernoulli observations. When the same items are repeated across multiple sampling seeds, use an item-clustered bootstrap for inferential intervals instead of interpreting the pooled Wilson interval as a confidence interval.

| Model | Mode | Family | N | Correct | Lure | Other | Accuracy | Lure rate (Wilson 95% CI) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | trivialized_classic | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | thinking | trivialized_classic | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | non_thinking | redefinition | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | thinking | redefinition | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | non_thinking | memo_override | 18 | 6 | 12 | 0 | 33.3% | 66.7% [43.7%, 83.7%] |
| Qwen3.5-27B | thinking | memo_override | 18 | 16 | 2 | 0 | 88.9% | 11.1% [3.1%, 32.8%] |
| Qwen3.5-27B | non_thinking | trivialized_classic__control | 18 | 15 | 3 | 0 | 83.3% | 16.7% [5.8%, 39.2%] |
| Qwen3.5-27B | thinking | trivialized_classic__control | 18 | 16 | 2 | 0 | 88.9% | 11.1% [3.1%, 32.8%] |
| Qwen3.5-27B | non_thinking | redefinition__control | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | thinking | redefinition__control | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | non_thinking | memo_override__control | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |
| Qwen3.5-27B | thinking | memo_override__control | 18 | 18 | 0 | 0 | 100.0% | 0.0% [0.0%, 17.6%] |

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
