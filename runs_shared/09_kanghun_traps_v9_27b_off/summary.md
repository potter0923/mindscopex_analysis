# CRT text-generation result summary

- Generated at: `2026-11-15T14:47:53+00:00`
- Dataset: `kanghun_traps_v9:qwen_native`
- Dataset reference: kanghun_traps_v9
- Final responses: **190**

## Headline results

`Hallucination` is an operational bucket for final answers that are neither only the correct answer nor only the known lure. It includes unresolved `both` and `other` responses, so inspect the quality table before interpreting it as factual fabrication.

| Model | Mode | N | Correct | Lure | Hallucination | Accuracy | Retried |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | 190 | 151 | 39 | 0 | 79.5% | 0 |

## Results by CRT family

Wilson intervals below treat rows as independent Bernoulli observations. When the same items are repeated across multiple sampling seeds, use an item-clustered bootstrap for inferential intervals instead of interpreting the pooled Wilson interval as a confidence interval.

| Model | Mode | Family | N | Correct | Lure | Other | Accuracy | Lure rate (Wilson 95% CI) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | resisting_correction | 25 | 25 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.3%] |
| Qwen3.5-27B | non_thinking | aiw_sibling | 25 | 25 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.3%] |
| Qwen3.5-27B | non_thinking | transparent_contents | 25 | 0 | 25 | 0 | 0.0% | 100.0% [86.7%, 100.0%] |
| Qwen3.5-27B | non_thinking | inverse_monty | 20 | 6 | 14 | 0 | 30.0% | 70.0% [48.1%, 85.5%] |
| Qwen3.5-27B | non_thinking | resisting_correction__control | 25 | 25 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.3%] |
| Qwen3.5-27B | non_thinking | aiw_sibling__control | 25 | 25 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.3%] |
| Qwen3.5-27B | non_thinking | transparent_contents__control | 25 | 25 | 0 | 0 | 100.0% | 0.0% [0.0%, 13.3%] |
| Qwen3.5-27B | non_thinking | inverse_monty__control | 20 | 20 | 0 | 0 | 100.0% | 0.0% [0.0%, 16.1%] |

## Quality and retry diagnostics

| Model | Mode | Format failures | Protocol failures | Retry attempts | Unresolved both | Other |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3.5-27B | non_thinking | 1 | 0 | 0 | 0 | 0 |

## Responses requiring review

This section includes hallucination/other outcomes, quality failures, and all retried responses so the final sample can be audited.

| Model | Mode | Case | Outcome | Raw label | Final answer | Attempts | Retry reasons | Protocol issue | Format issue |
|---|---|---|---|---|---|---:|---|---|---|
| Qwen3.5-27B | non_thinking | kanghun_traps_v9_copy_becuase__control | correct | correct | because | 1 |  |  | label_or_explanation |

## Retry audit

No response was regenerated.
