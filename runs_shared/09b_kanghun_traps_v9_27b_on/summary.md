# CRT text-generation result summary

- Generated at: `2026-11-15T15:57:23+00:00`
- Dataset: `kanghun_traps_v9s2:qwen_native`
- Dataset reference: kanghun_traps_v9s2
- Final responses: **39**

## Headline results

`Hallucination` is an operational bucket for final answers that are neither only the correct answer nor only the known lure. It includes unresolved `both` and `other` responses, so inspect the quality table before interpreting it as factual fabrication.

| Model | Mode | N | Correct | Lure | Hallucination | Accuracy | Retried |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | thinking | 39 | 27 | 12 | 0 | 69.2% | 0 |

## Results by CRT family

Wilson intervals below treat rows as independent Bernoulli observations. When the same items are repeated across multiple sampling seeds, use an item-clustered bootstrap for inferential intervals instead of interpreting the pooled Wilson interval as a confidence interval.

| Model | Mode | Family | N | Correct | Lure | Other | Accuracy | Lure rate (Wilson 95% CI) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | thinking | transparent_contents | 25 | 19 | 6 | 0 | 76.0% | 24.0% [11.5%, 43.4%] |
| Qwen3.5-27B | thinking | inverse_monty | 14 | 8 | 6 | 0 | 57.1% | 42.9% [21.4%, 67.4%] |

## Quality and retry diagnostics

| Model | Mode | Format failures | Protocol failures | Retry attempts | Unresolved both | Other |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | thinking | 0 | 0 | 0 | 0 | 0 |

## Responses requiring review

This section includes hallucination/other outcomes, quality failures, and all retried responses so the final sample can be audited.

No responses require review.

## Retry audit

No response was regenerated.
