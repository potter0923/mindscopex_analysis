# CRT text-generation result summary

- Generated at: `2026-11-08T05:26:50+00:00`
- Dataset: `kanghun_traps_v5:qwen_native`
- Dataset reference: kanghun_traps_v5
- Final responses: **192**

## Headline results

`Hallucination` is an operational bucket for final answers that are neither only the correct answer nor only the known lure. It includes unresolved `both` and `other` responses, so inspect the quality table before interpreting it as factual fabrication.

| Model | Mode | N | Correct | Lure | Hallucination | Accuracy | Retried |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | 96 | 90 | 6 | 0 | 93.8% | 0 |
| Qwen3.5-27B | thinking | 96 | 96 | 0 | 0 | 100.0% | 0 |

## Results by CRT family

Wilson intervals below treat rows as independent Bernoulli observations. When the same items are repeated across multiple sampling seeds, use an item-clustered bootstrap for inferential intervals instead of interpreting the pooled Wilson interval as a confidence interval.

| Model | Mode | Family | N | Correct | Lure | Other | Accuracy | Lure rate (Wilson 95% CI) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | letter_count | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | thinking | letter_count | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | non_thinking | repeated_word | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | thinking | repeated_word | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | non_thinking | sequence_skip | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | thinking | sequence_skip | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | non_thinking | last_letter_concat | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | thinking | last_letter_concat | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | non_thinking | nested_relative | 6 | 5 | 1 | 0 | 83.3% | 16.7% [3.0%, 56.4%] |
| Qwen3.5-27B | thinking | nested_relative | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | non_thinking | belief_tracking | 6 | 2 | 4 | 0 | 33.3% | 66.7% [30.0%, 90.3%] |
| Qwen3.5-27B | thinking | belief_tracking | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | non_thinking | distinct_count | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | thinking | distinct_count | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | non_thinking | fact_tweak | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | thinking | fact_tweak | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | non_thinking | letter_count__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | thinking | letter_count__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | non_thinking | repeated_word__control | 6 | 5 | 1 | 0 | 83.3% | 16.7% [3.0%, 56.4%] |
| Qwen3.5-27B | thinking | repeated_word__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | non_thinking | sequence_skip__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | thinking | sequence_skip__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | non_thinking | last_letter_concat__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | thinking | last_letter_concat__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | non_thinking | nested_relative__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | thinking | nested_relative__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | non_thinking | belief_tracking__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | thinking | belief_tracking__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | non_thinking | distinct_count__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | thinking | distinct_count__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | non_thinking | fact_tweak__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |
| Qwen3.5-27B | thinking | fact_tweak__control | 6 | 6 | 0 | 0 | 100.0% | 0.0% [0.0%, 39.0%] |

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
