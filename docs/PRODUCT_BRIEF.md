# Product brief: SahiRFQ

## The product decision

Do not recommend a supplier merely because the product title resembles the buyer's enquiry. Establish the specifications that would change supplier eligibility, then show the evidence behind the match.

## Problem hypothesis

A small business buyer may submit “2 HP pump chahiye” without specifying pump type, electrical phase, quantity, delivery city or deadline. A title-level match can be relevant to the product category yet unusable for the order. A supplier must then spend time clarifying the requirement. This is a hypothesis worth investigating; no primary interviews have been conducted for this project.

IndiaMART's published investor material already describes AI-driven enrichment and matchmaking. SahiRFQ therefore explores RFQ readiness and evidence handling rather than claiming IndiaMART lacks AI. The published source is linked in the README; it supports workflow relevance, not a measured failure rate.

## Users and decisions

| User | Decision | Useful output |
|---|---|---|
| SME buyer | What must I specify before requesting quotes? | A short set of questions and a reviewable RFQ |
| Supplier | Does this enquiry fit my catalog and operating limits? | Specification, unit, MOQ and timing checks |
| Product/operations team | Why was a match made or withheld? | Field-level evidence, failure reasons and a trace |

The current prototype simulates catalog qualification. It does not model supplier incentives, BuyLead credit prices or actual marketplace transactions.

## MVP acceptance criteria

1. Missing buyer specifications stay unknown, even if one catalog option is common.
2. A missing critical specification prevents a recommendation; exploratory candidates remain clearly labeled.
3. A failed constraint excludes a candidate; unknown supplier evidence is distinguished from a failed constraint.
4. The buyer can answer questions and obtain an updated result without rewriting the request.
5. Every catalog claim has a resolvable record and field citation.
6. A quote with unknown tax or freight cannot be declared the lowest complete total.
7. An unsupported request falls back to clarification/manual sourcing.
8. The project includes an inspectable baseline and reproducible test cases.

## Scope and priorities

| Priority | Included behavior | Reason |
|---|---|---|
| P0 | Missing-field gates and exact compatibility checks | Defines the product's decision quality |
| P0 | Buyer clarification and supplier evidence | Makes decisions reviewable |
| P0 | Authored evaluation and simple baseline | Gives a measurable engineering claim |
| P1 | Hinglish normalization and character retrieval | Covers realistic language variation within a narrow scope |
| P1 | Cited catalog answers and quote completeness | Helps buyers move from discovery toward a clear quote |
| Later | Voice input, document OCR, broad translation | Needs separate data and quality evaluation |
| Later | Supplier outcome prediction | Requires genuine response/conversion labels unavailable here |
| Later | Live marketplace integration | Requires authorized data access, privacy review and operational validation |

## Trade-offs

The local matching path costs no API tokens and exposes its features and rules. Its language coverage is limited. LLM use is optional and bounded to catalog evidence selection; this prevents the app from depending on unrestricted prose generation. A supported API model can still misinterpret the question even when every returned value exists in the catalog.

The system intentionally withholds a shortlist when required fields are missing. Too many questions may increase buyer abandonment. Catalog entropy helps order questions by diversity, but it does not estimate the conversion benefit of asking them. The weights and routing thresholds are engineering defaults, not learned causal policies.

Exact numeric matching is easy to inspect but can reject a technically suitable alternative. For example, a compressor's pressure rating cannot be substituted based on numeric similarity alone. A category specialist would need to define suitability rules and validate them.

## Validation plan before a real pilot

1. Interview 5-8 SME buyers and 5-8 suppliers in one category. Observe how requests and quote clarification happen; do not ask only whether the idea sounds useful.
2. With consent, annotate real enquiries for critical missing fields and catalog compatibility. Keep buyer/company groups separate across model development and evaluation.
3. Run in shadow mode beside the existing workflow. Have category specialists review recommendations, exclusions and abstentions.
4. Pilot clarification prompts in one category. Randomize at buyer level; track buyer completion and supplier qualification together. Decide sample size from baseline rates and a predeclared minimum detectable effect.
5. Expand only after category-level quality, abandonment and latency guardrails pass. Have engineering and QA owners approve the parser, catalog freshness, auditability and fallback behavior.

## Metrics for that pilot

| Metric | Definition | Interpretation |
|---|---|---|
| Confirmed specification fit | Supplier-reviewed compatible recommendations / reviewed recommendations | Primary quality measure |
| Quote-ready enquiry rate | Enquiries with required buyer fields and a compatible supplier / submitted enquiries | Workflow readiness |
| Clarification completion | Buyers supplying requested fields / buyers shown questions | Friction guardrail |
| Buyer abandonment | Buyers leaving before sending an RFQ / started requests | Guardrail against excessive questioning |
| Supplier follow-up burden | Clarification contacts per qualified enquiry | Operational value, measured with actual logs |
| Unsupported-claim rate | Unsupported supplier claims / reviewed claims | Grounding guardrail |
| Time to first usable quote | Median time from enquiry to quote containing requested specifications and complete costs | Downstream value, distinct from model latency |

No conversion uplift, supplier retention gain or time saving has been measured. The current evaluation establishes regression behavior on fictional fixtures only.

## Economics to estimate using real data

Monthly value from clarification work = affected enquiries x verified minutes avoided per enquiry / 60 x loaded hourly cost. Subtract inference cost, human review time and maintenance cost. LLM inference cost = measured input tokens x account input rate + output tokens x account output rate. Do not treat local response latency as time saved in the business workflow.

The prototype's matching step makes zero LLM calls. Optional RAG returns token counts where available; no API pricing or monetization assumption is hard-coded.
