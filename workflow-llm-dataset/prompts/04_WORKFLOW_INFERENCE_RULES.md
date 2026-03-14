# Workflow Inference Rules

## Goal

Transform occupation-level evidence into ordered workflow units that are useful for:
- process understanding
- automation analysis
- business problem discovery
- LLM training and retrieval

## Workflow inference principle

A workflow may be inferred only by combining real evidence such as:
- task statements
- detailed work activities
- work context
- tools and technology
- private SOPs
- operational documents
- official manuals

Do not infer workflows from title semantics alone.

## Required workflow structure

Every workflow should try to capture:
- workflow_name
- trigger_event
- preconditions
- ordered steps
- actor role
- systems and tools used
- inputs handled
- outputs produced
- handoff targets
- exception points
- control points
- candidate KPIs
- automation candidacy

## Step template

Each workflow step should include:
- step_order
- step_name
- step_description
- input_objects
- output_objects
- systems_used
- documents_used
- likely tool references
- handoff_to_role
- automation_candidate
- automation_reason
- inference_method
- confidence_score

## Example workflow skeletons

### Towing dispatcher
1. receive service request
2. verify vehicle, location, urgency, and customer details
3. identify available truck and operator
4. assign route and dispatch driver
5. monitor job status
6. update customer or insurer
7. close service event
8. issue invoice and reconcile payment

### Wholesale tire buyer
1. review current inventory and open orders
2. estimate demand and stock risk
3. request or receive vendor quote
4. compare supplier price, lead time, and quantity
5. create purchase order
6. track shipment status
7. receive inventory and verify quantities
8. update inventory records
9. resolve discrepancies
10. submit supplier payment package

### Field service technician
1. receive work order
2. review job notes and required tools
3. travel to site
4. inspect issue
5. perform service or repair
6. record findings and parts used
7. obtain customer signoff
8. close job and submit documentation

## Inference rule

If the step is not explicitly stated in a source but is derived from multiple adjacent tasks, mark:
- inferred = true
- inference_method = clustered_task_evidence
- confidence_score accordingly
- review_status = reviewed or needs_review

## Automation classification guidance

Use one of:
- automate
- augment
- human_led
- unknown

Interpretation:
- automate = step is repetitive, rules-based, digital, and low judgment
- augment = AI can assist but human judgment or approval remains important
- human_led = physical, interpersonal, regulated, or high-risk judgment dominates
- unknown = insufficient evidence

Always provide a reason.
