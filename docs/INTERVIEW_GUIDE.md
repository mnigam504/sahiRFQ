# Explain SahiRFQ in an interview

## 45-second explanation

“SahiRFQ helps a business buyer turn an incomplete enquiry into a clear request for quotation. If someone asks for a pump, a product title match is not enough: pump type, power, phase, quantity and delivery requirements can change which supplier fits. The prototype asks about those missing details and checks each candidate against catalog evidence. I used a supervised category classifier, hybrid vector retrieval and explicit constraint checks. It also gives cited catalog answers and compares quote completeness. The current data is fictional, and I evaluated the workflow against authored scenarios. The next step would be validating it with real buyers and suppliers in one category.”

Use this after running the project and reviewing the code. The implementation was prepared with AI assistance; be clear about the decisions you can explain and changes you personally tested.

## What the demo proves

It shows an incomplete request becoming complete through buyer answers, a wrong phase being excluded, unknown supplier evidence staying unknown, and an unsupported catalog claim producing abstention. It also shows that quote totals need tax and freight amounts before comparison. It does not prove commercial demand, production scalability or conversion uplift.

## What is actually ML?

The category router learns logistic regression weights from 200 template-derived requests. Word and character TF-IDF features help it distinguish product categories. Catalog retrieval uses TF-IDF vectors and a learned LSA projection. The extraction grammar, numerical comparisons, abstention gates, question weights and quote arithmetic are application policy/rules. The optional LLM RAG step uses OpenAI only to select evidence from retrieved fields.

## Why not use an LLM for everything?

The local path is cheap, quick and easy to inspect. It is suitable for demonstrating exact decisions in five categories. Its drawback is narrow language coverage. A broader parser could use structured LLM extraction, but values would still need source attribution, validation, correction and a missing-field policy. I kept optional LLM use separate so that the main workflow can run without an API key.

## What are embeddings and vector search here?

A TF-IDF vector weights words or character sequences according to their frequency and distinctiveness. Similarity compares a request vector with catalog document vectors. Truncated SVD reduces the word-vector matrix into 16 learned numerical dimensions, called LSA vectors. These are not transformer embeddings. Retrieval finds candidates; it does not prove eligibility.

## Why both a trained classifier and coverage rules?

The classifier produces category scores. The coverage gate prevents it from confidently routing an unsupported product into the nearest known category and catches obvious multi-category enquiries. This is deliberately conservative. On real data I would compare it with a keyword-only router, measure category-level precision/coverage, and calibrate the decision thresholds. The current 48-case evaluation does not prove the ML router outperforms a good rule system.

## How are clarification questions selected?

First, identify missing required fields. Then measure the diversity of known values among candidates using entropy: H = -sum(p x log2(p)). A field with more distinct plausible values can separate more candidates. Category questions receive extra priority. This is a transparent heuristic; it is not a trained expected-conversion or causal information-gain policy.

## How do you prevent hallucinations?

The main matcher never generates supplier specifications. It checks structured values. A missing value remains null. Catalog QA requires an existing record, an existing field and a value that exactly matches the retrieved evidence. Invalid generated claims are rejected. A valid citation still does not prove supplier truth or freshness, so catalog verification and human review remain necessary.

## Is it an agent or RAG chatbot?

It is a bounded sourcing workflow with a separate evidence-based catalog Q&A path. Optional OpenAI mode retrieves catalog evidence before model selection, so that path is RAG. Local mode is extractive retrieval. It is not an autonomous agent that contacts suppliers, negotiates, places orders or handles money.

## What results can you defend?

“The checked-in development evaluation passes 48 authored scenarios. On 29 fully specified scenarios, the constrained shortlist returned 23 records with zero incompatible IDs under the fixture labels. Raw word TF-IDF returned 87 candidates, 64 of which violated those labels. Both had the same compatible recall@3. That shows the value of explicit filtering on these examples; it is not a real marketplace benchmark.”

The unit/integration suite has 26 tests. Timing figures are warm local inference only, excluding startup/model fitting and any LLM call. A separate grouped seed-family validation is recorded in `reports/model_inspection.json`; describe it as a synthetic sanity check.

That harder grouped check scored 70% category accuracy on 50 synthetic examples. If asked about model generalization, mention it directly: the router has a vocabulary limitation, which is why the coverage gates and human clarification exist and why a real-data evaluation is needed.

## What would be the first business metric?

Supplier-confirmed specification fit, paired with buyer clarification completion and abandonment. I would then measure time to the first usable quote and supplier clarification contacts. A model that asks too many questions could improve apparent accuracy while harming the workflow.

## What would you build next with IndiaMART data?

I would begin with one category, consented buyer requests, structured catalogs and category experts. I would annotate compatibility and missing fields, split by buyer/supplier group and time, and run shadow evaluation. I would replace the narrow parser only after measuring its failure patterns. Response/conversion prediction would come later because it needs genuine outcome labels and is affected by supplier behavior and marketplace exposure.

## How does this fit your background?

“At VizExperts, I worked on software used by clients and learned that a feature works only when the requirement and workflow are clear. My MBA is helping me think about priorities, user friction and business measures. This project combines those interests: define a small user problem, build a working system, make its decisions explainable, and test the limits.”

Do not claim any specific VizExperts improvement percentage unless you can explain the actual measurement and source.

## Five details to know before submission

1. Trace the example through `engine.analyze`, `check` and `questions`.
2. Explain the difference between `excluded`, `unverified` and `compatible`.
3. Explain why per-unit versus total budget changes the answer.
4. Run a scenario you create yourself, then inspect its output and failure behavior.
5. Read the optional provider adapter and its mocked test. Do not say you tested a live LLM call unless you actually run it with your account.
