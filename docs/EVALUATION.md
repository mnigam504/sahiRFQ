# Evaluation and model card

## Data provenance

All catalog records are fictional. Supplier names, prices, MOQ and lead times are illustrative examples, not claims about actual businesses. Training requests are built from 40 authored category seeds and five templates per seed, producing 200 examples. The evaluation contains 48 separately authored scenarios with explicit expected statuses, outputs and compatibility labels.

Evaluation text is checked against exact normalized training strings. This avoids exact row reuse but does not make the scenarios statistically independent of their author or taxonomy. The evaluation has been viewed during development and used for repairs. Treat it as a development regression suite.

## Models and policy

The supervised category classifier is logistic regression with regularization parameter C=8, maximum 1,000 iterations and deterministic random state 42. It uses word unigrams/bigrams and character n-grams of length 3-5. An explicit vocabulary coverage gate and top-score/margin thresholds can abstain. Thresholds 0.45 and 0.15 are hand-chosen defaults; model scores are not calibrated confidence for customer traffic.

Catalog retrieval combines word cosine similarity (0.55), character cosine similarity (0.30) and normalized LSA similarity (0.15). LSA is a rank-16 truncated SVD projection, fitted on the 30 catalog documents. These are statistical vectors, not a deep-learning or multilingual transformer embedding model. Constraints are checked separately; a high retrieval score cannot override a failed constraint.

Every requested numeric specification is matched exactly. Quantity must use the catalog's price unit. MOQ must not exceed order quantity. Declared lead time must not exceed the requested days. Budgets require an explicit per-unit or total scope and constrain goods base cost only. Local-only requests also constrain dispatch city. Unknown catalog fields remain unknown.

## What the report measures

| Check | Denominator | Meaning |
|---|---|---|
| Scenario pass count | 48 authored requests | Expected status, shortlist, selected field values and required questions agree |
| Raw category accuracy | 45 scenarios with a supported expected category | Top logistic regression category agrees with the authored label; abstention gates are separate |
| Constraint violations | Shortlist records on 29 fully specified scenarios | Returned record IDs outside the independent authored compatible sets |
| Compatible recall@3 | Fully specified requests with at least one compatible record | Compatible IDs returned / min(3, compatible set size), averaged across requests |
| Warm local latency | 144 repeated matching calls | Three repetitions per case, excluding startup, training, network and optional LLM calls |

The baseline is raw word TF-IDF retrieval of three records. It always retrieves three candidates, including for cases where none satisfies the request. It represents a simple retrieval-only approach, not IndiaMART's system or a strong learned production recommender.

## Observed result

All 48 scenario checks passed. On the 29 fully specified cases, the constrained method returned 23 records with zero fixture-labeled violations. The raw baseline returned 87 records with 64 violations (73.56%). Both methods reached compatible recall@3 of 1.0. Filtering removed invalid suggestions while retaining the valid catalog records on these scenarios; there was no observed recall improvement.

The small, authored dataset makes these favorable results unsurprising. They do not establish accuracy on real traffic, a safe deployment threshold, a broad translation capability or business impact. Re-run `scripts/evaluate.py` for timing numbers on your machine; use the checked-in JSON for the exact environment and dataset fingerprint.

`scripts/inspect_ml.py` separately holds out two seed families per category and reports a grouped synthetic sanity check. It is a second classifier fit for inspection; the shipped workflow fits all 200 training examples at startup. Grouping avoids placing different template versions of the same seed in both parts, but it still does not provide a real-world test set.

The grouped check scored **70% category accuracy** on 50 synthetic validation examples after fitting 150 training examples. Some held-out phrases use vocabulary absent from that training subset. This illustrates limited language generalization and why the 100% raw category result on the 45 supported development scenarios should not be treated as predictive performance.

## Grounding and workflow checks

The 26 unit/integration tests cover absent specifications, unknown supplier fields, conflicting inputs, numeric validation, budget scope, MOQ, unsupported products, exact evidence validation, mocked OpenAI requests, prompt injection text in local QA, quote cost completeness, cross-origin API rejection and static path allowlisting.

Evidence validation establishes that a selected value exists in the retrieved catalog. It does not establish catalog truth, freshness, question relevance, engineering suitability or supplier reliability. Optional live OpenAI calls have not been benchmarked. The quote calculator trusts explicitly buyer-entered quoted amounts and does not validate tax law or supplier confirmations.

## UI verification

API integration and JavaScript syntax checks pass. Browser rendering and click-through visual inspection could not be completed in the build environment: the local browser endpoint was blocked and the headless browser download failed. A DOM-based interaction check is recorded separately if available. Do not claim cross-browser visual QA or a live provider demonstration on the basis of these tests.
