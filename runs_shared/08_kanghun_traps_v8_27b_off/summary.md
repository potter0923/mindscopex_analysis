# CRT text-generation result summary

- Generated at: `2026-11-15T09:28:44+00:00`
- Dataset: `kanghun_traps_v8:qwen_native`
- Dataset reference: kanghun_traps_v8
- Final responses: **400**

## Headline results

`Hallucination` is an operational bucket for final answers that are neither only the correct answer nor only the known lure. It includes unresolved `both` and `other` responses, so inspect the quality table before interpreting it as factual fabrication.

| Model | Mode | N | Correct | Lure | Hallucination | Accuracy | Retried |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | 400 | 240 | 160 | 0 | 60.0% | 0 |

## Results by CRT family

Wilson intervals below treat rows as independent Bernoulli observations. When the same items are repeated across multiple sampling seeds, use an item-clustered bootstrap for inferential intervals instead of interpreting the pooled Wilson interval as a confidence interval.

| Model | Mode | Family | N | Correct | Lure | Other | Accuracy | Lure rate (Wilson 95% CI) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | belief_tracking | 200 | 40 | 160 | 0 | 20.0% | 80.0% [73.9%, 85.0%] |
| Qwen3.5-27B | non_thinking | belief_tracking__control | 200 | 200 | 0 | 0 | 100.0% | 0.0% [0.0%, 1.9%] |

## Quality and retry diagnostics

| Model | Mode | Format failures | Protocol failures | Retry attempts | Unresolved both | Other |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | 0 | 0 | 0 | 0 | 0 |

## Responses requiring review

This section includes hallucination/other outcomes, quality failures, and all retried responses so the final sample can be audited.

No responses require review.

## Retry audit

No response was regenerated.
