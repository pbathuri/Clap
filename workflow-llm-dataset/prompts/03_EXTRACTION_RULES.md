# Extraction and Normalization Rules

## Core requirement

The goal is to extract what workers actually do, not just what a job title implies.

## Industry hierarchy extraction

1. Build ISIC hierarchy first.
2. Build NAICS hierarchy second.
3. Preserve all hierarchy levels.
4. Store descriptions and explanatory notes where available.
5. Maintain parent-child integrity.

Do not flatten the hierarchy into a single text label.

## Occupation extraction

Ground occupations in official occupation taxonomies first:
- SOC
- O*NET
- ESCO as enrichment

Do not create synthetic occupations unless a business-specific role clearly exists in private data, and even then mark it as a business-role variant rather than a canonical occupation.

## Task extraction

For each occupation, extract the following if present:
- task statements
- detailed work activities
- work context
- tools and technology
- technology skills
- knowledge
- skills
- abilities
- work styles

Do not collapse all of this into a single summary paragraph.
Keep the atomic rows.

## Tool extraction

Capture real execution artifacts, including:
- software
- machinery
- equipment
- spreadsheets
- dashboards
- forms
- checklists
- maps
- handheld devices
- scanners
- vehicles
- sensors
- invoices
- purchase orders
- route sheets
- work orders
- CAD tools
- EHR / ERP / CRM systems
- GIS or routing systems

Examples of acceptable tool entities:
- Microsoft Excel
- handheld barcode scanner
- tow truck winch
- dispatch board
- GPS map
- invoice PDF
- maintenance checklist
- forklift
- warehouse management system
- EHR portal
- CAD drafting software

## Physicality and environment extraction

Use work context or official occupational context to capture:
- standing or walking requirements
- hand and finger dexterity
- outdoor exposure
- contamination exposure
- vehicle operation
- safety risks
- repetitive motion
- phone intensity
- computer intensity
- time pressure
- multi-party coordination
- customer interaction intensity

## Private-document extraction

If private examples are present:
- parse filenames and metadata
- extract document type
- extract field names and workflow evidence
- identify real objects handled in work such as forms, invoices, route sheets, order forms, service tickets, checklists
- use these as workflow enrichment, not as replacements for taxonomy grounding

## Normalization rules

- normalize whitespace and punctuation
- preserve original raw text in a raw field when possible
- create stable IDs
- never overwrite raw extracted text with paraphrases
- separate canonical value and display value if needed
- preserve original source code and title

## Confidence guidance

- explicit official record = high confidence
- corroborated private document + official occupation grounding = medium to high confidence
- derived inference from clustered evidence = medium confidence
- weak public web evidence = low confidence and needs review
