# CRT text-generation result summary

- Generated at: `2026-10-24T17:33:33+00:00`
- Dataset: `external_traps_v1:qwen_native`
- Dataset reference: external_traps_v1
- Final responses: **70**

## Headline results

`Hallucination` is an operational bucket for final answers that are neither only the correct answer nor only the known lure. It includes unresolved `both` and `other` responses, so inspect the quality table before interpreting it as factual fabrication.

| Model | Mode | N | Correct | Lure | Hallucination | Accuracy | Retried |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | 35 | 30 | 5 | 0 | 85.7% | 0 |
| Qwen3.5-27B | thinking | 35 | 35 | 0 | 0 | 100.0% | 0 |

## Results by CRT family

Wilson intervals below treat rows as independent Bernoulli observations. When the same items are repeated across multiple sampling seeds, use an item-clustered bootstrap for inferential intervals instead of interpreting the pooled Wilson interval as a confidence interval.

| Model | Mode | Family | N | Correct | Lure | Other | Accuracy | Lure rate (Wilson 95% CI) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | prerequisite_filter | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | thinking | prerequisite_filter | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | non_thinking | capacity_cap | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | thinking | capacity_cap | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | non_thinking | designated_option | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | thinking | designated_option | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | non_thinking | scope_exclusion | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | thinking | scope_exclusion | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | non_thinking | threshold_eligibility | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | thinking | threshold_eligibility | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | non_thinking | limited_scope | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | thinking | limited_scope | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | non_thinking | exception_override | 4 | 0 | 4 | 0 | 0.0% | 100.0% [51.0%, 100.0%] |
| Qwen3.5-27B | thinking | exception_override | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | non_thinking | prerequisite_filter__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | thinking | prerequisite_filter__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | non_thinking | capacity_cap__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | thinking | capacity_cap__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | non_thinking | designated_option__control | 1 | 0 | 1 | 0 | 0.0% | 100.0% [20.7%, 100.0%] |
| Qwen3.5-27B | thinking | designated_option__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | non_thinking | scope_exclusion__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | thinking | scope_exclusion__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | non_thinking | threshold_eligibility__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | thinking | threshold_eligibility__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | non_thinking | limited_scope__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | thinking | limited_scope__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | non_thinking | exception_override__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | thinking | exception_override__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |

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
