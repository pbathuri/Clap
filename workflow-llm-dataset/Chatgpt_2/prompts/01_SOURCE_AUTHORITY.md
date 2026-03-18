# Source Authority Policy

## Source priority order

Always use sources in this order.
Higher-tier sources override lower-tier sources for taxonomy, occupation grounding, and task grounding.

### Tier 1 — authoritative structured sources
Use these first and anchor the dataset to them.
- UNSD / ISIC hierarchy and explanatory notes
- U.S. Census / NAICS structure and concordances
- BLS / SOC occupation hierarchy
- O*NET database and O*NET documentation
- BLS Employment Projections, OEWS, Occupational Outlook Handbook, Industry-Occupation Matrix, skills-related releases
- ESCO downloadable occupation-skill relationships

### Tier 2 — authoritative operational context sources
Use these for workflow enrichment when structured taxonomy/task sources are insufficient.
- government manuals
- regulatory guidance
- standards documents
- public technical manuals
- official training material
- official vendor documentation for tools and software used in work

### Tier 3 — enrichment sources only
Use these only after Tier 1 and Tier 2 are exhausted or to add business realism.
- high-quality employer job descriptions
- company SOPs
- implementation guides
- employer process documentation
- trade association publications
- industry case studies
- high-quality public workflow examples

### Tier 4 — weak sources, use sparingly
Use only if no better evidence exists, and never as the sole basis for canonical task definitions.
- blogs
- SEO articles
- generic productivity articles
- unsourced summary pages

## Hard rules

- Never let Tier 3 or Tier 4 override official taxonomy or occupation definitions.
- Never infer a task from job title alone.
- Never assign a tool just because it "sounds common."
- Never create an occupation-industry mapping from vibes or keyword similarity alone.
- Every row must retain provenance.
- If evidence conflicts, preserve both and flag for review.
- Every source must store publisher, version, retrieval date, and path or URL.
- Every inferred workflow step must carry a confidence score.

## Acceptable evidence for "what workers actually do"

Prefer in this order:
1. O*NET task statements
2. O*NET detailed work activities
3. O*NET work context
4. O*NET tools and technology / technology skills
5. official manuals or training material
6. private business documents uploaded into the project
7. corroborated employer workflow documentation

## Handling ambiguity

If a mapping or workflow step is uncertain:
- do not guess
- mark review_status = needs_review
- set confidence_score conservatively
- write the ambiguity into the QA review output
