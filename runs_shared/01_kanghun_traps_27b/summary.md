# CRT text-generation result summary

- Generated at: `2026-10-24T04:42:14+00:00`
- Dataset: `kanghun_traps_v1:qwen_native`
- Dataset reference: kanghun_traps_v1
- Final responses: **60**

## Headline results

`Hallucination` is an operational bucket for final answers that are neither only the correct answer nor only the known lure. It includes unresolved `both` and `other` responses, so inspect the quality table before interpreting it as factual fabrication.

| Model | Mode | N | Correct | Lure | Hallucination | Accuracy | Retried |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | 30 | 28 | 2 | 0 | 93.3% | 0 |
| Qwen3.5-27B | thinking | 30 | 30 | 0 | 0 | 100.0% | 0 |

## Results by CRT family

Wilson intervals below treat rows as independent Bernoulli observations. When the same items are repeated across multiple sampling seeds, use an item-clustered bootstrap for inferential intervals instead of interpreting the pooled Wilson interval as a confidence interval.

| Model | Mode | Family | N | Correct | Lure | Other | Accuracy | Lure rate (Wilson 95% CI) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | prerequisite_or_order_omission | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | thinking | prerequisite_or_order_omission | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | non_thinking | capacity_or_compatibility_violation | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | thinking | capacity_or_compatibility_violation | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | non_thinking | entity_or_role_binding | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | thinking | entity_or_role_binding | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | non_thinking | heuristic_or_salience_substitution | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | thinking | heuristic_or_salience_substitution | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | non_thinking | relation_omission_or_reversal | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | thinking | relation_omission_or_reversal | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | non_thinking | familiar_pattern_retrieval | 4 | 2 | 2 | 0 | 50.0% | 50.0% [15.0%, 85.0%] |
| Qwen3.5-27B | thinking | familiar_pattern_retrieval | 4 | 4 | 0 | 0 | 100.0% | 0.0% [0.0%, 49.0%] |
| Qwen3.5-27B | non_thinking | prerequisite_or_order_omission__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | thinking | prerequisite_or_order_omission__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | non_thinking | capacity_or_compatibility_violation__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | thinking | capacity_or_compatibility_violation__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | non_thinking | entity_or_role_binding__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | thinking | entity_or_role_binding__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | non_thinking | heuristic_or_salience_substitution__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | thinking | heuristic_or_salience_substitution__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | non_thinking | relation_omission_or_reversal__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | thinking | relation_omission_or_reversal__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | non_thinking | familiar_pattern_retrieval__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |
| Qwen3.5-27B | thinking | familiar_pattern_retrieval__control | 1 | 1 | 0 | 0 | 100.0% | 0.0% [0.0%, 79.3%] |

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
