# CRT text-generation result summary

- Generated at: `2026-10-24T10:01:56+00:00`
- Dataset: `hagendorff_crt:qwen_native`
- Dataset reference: 10.1038/s43588-023-00527-x
- Final responses: **120**

## Headline results

`Hallucination` is an operational bucket for final answers that are neither only the correct answer nor only the known lure. It includes unresolved `both` and `other` responses, so inspect the quality table before interpreting it as factual fabrication.

| Model | Mode | N | Correct | Lure | Hallucination | Accuracy | Retried |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | 60 | 54 | 6 | 0 | 90.0% | 0 |
| Qwen3.5-27B | thinking | 60 | 56 | 4 | 0 | 93.3% | 0 |

## Results by CRT family

Wilson intervals below treat rows as independent Bernoulli observations. When the same items are repeated across multiple sampling seeds, use an item-clustered bootstrap for inferential intervals instead of interpreting the pooled Wilson interval as a confidence interval.

| Model | Mode | Family | N | Correct | Lure | Other | Accuracy | Lure rate (Wilson 95% CI) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | crt_difference | 10 | 9 | 1 | 0 | 90.0% | 10.0% [1.8%, 40.4%] |
| Qwen3.5-27B | thinking | crt_difference | 10 | 10 | 0 | 0 | 100.0% | 0.0% [0.0%, 27.8%] |
| Qwen3.5-27B | non_thinking | crt_rate | 10 | 10 | 0 | 0 | 100.0% | 0.0% [0.0%, 27.8%] |
| Qwen3.5-27B | thinking | crt_rate | 10 | 10 | 0 | 0 | 100.0% | 0.0% [0.0%, 27.8%] |
| Qwen3.5-27B | non_thinking | crt_growth | 10 | 10 | 0 | 0 | 100.0% | 0.0% [0.0%, 27.8%] |
| Qwen3.5-27B | thinking | crt_growth | 10 | 10 | 0 | 0 | 100.0% | 0.0% [0.0%, 27.8%] |
| Qwen3.5-27B | non_thinking | crt_difference__control | 10 | 10 | 0 | 0 | 100.0% | 0.0% [0.0%, 27.8%] |
| Qwen3.5-27B | thinking | crt_difference__control | 10 | 10 | 0 | 0 | 100.0% | 0.0% [0.0%, 27.8%] |
| Qwen3.5-27B | non_thinking | crt_rate__control | 10 | 7 | 3 | 0 | 70.0% | 30.0% [10.8%, 60.3%] |
| Qwen3.5-27B | thinking | crt_rate__control | 10 | 8 | 2 | 0 | 80.0% | 20.0% [5.7%, 51.0%] |
| Qwen3.5-27B | non_thinking | crt_growth__control | 10 | 8 | 2 | 0 | 80.0% | 20.0% [5.7%, 51.0%] |
| Qwen3.5-27B | thinking | crt_growth__control | 10 | 8 | 2 | 0 | 80.0% | 20.0% [5.7%, 51.0%] |

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
