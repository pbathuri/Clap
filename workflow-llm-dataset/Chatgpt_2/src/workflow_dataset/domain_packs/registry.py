"""
M23U: Built-in domain pack definitions and recommendation by field/job family.
"""

from __future__ import annotations

from typing import Any

from workflow_dataset.domain_packs.models import DomainPack

# Built-in domain packs: founder ops, office admin, logistics, research, coding, document-heavy, multilingual, OCR-heavy
BUILTIN_DOMAIN_PACKS: list[DomainPack] = [
    DomainPack(
        domain_id="founder_ops",
        name="Founder / small-team operations",
        description="Light ops, reporting, stakeholder updates, meeting prep.",
        suggested_job_packs=["weekly_status", "status_action_bundle", "stakeholder_update_bundle", "meeting_brief_bundle"],
        suggested_routines=["morning_reporting", "weekly_review"],
        suggested_model_classes=["llama3.2", "mistral", "phi"],
        suggested_embedding_classes=["nomic-embed-text", "mxbai-embed-large"],
        suggested_ocr_vision_classes=[],
        suggested_integration_classes=[],
        suggested_recipe_id="retrieval_only",
        expected_approvals=["path_workspace", "apply_confirm"],
        trust_notes="Simulate-first; real apply only after approval.",
        field_keywords=["founder", "operations", "ops", "startup", "small_team"],
        job_family_keywords=["founder", "ops", "manager"],
    ),
    DomainPack(
        domain_id="office_admin",
        name="Office administration",
        description="Scheduling, documents, correspondence, filing.",
        suggested_job_packs=["weekly_status", "status_action_bundle"],
        suggested_routines=["daily_admin", "weekly_report"],
        suggested_model_classes=["llama3.2", "mistral", "phi"],
        suggested_embedding_classes=["nomic-embed-text"],
        suggested_ocr_vision_classes=[],
        suggested_integration_classes=[],
        suggested_recipe_id="retrieval_only",
        expected_approvals=["path_workspace", "apply_confirm"],
        trust_notes="Document handling; approve paths and apply.",
        field_keywords=["office", "admin", "administration", "secretary"],
        job_family_keywords=["admin", "assistant", "coordinator"],
    ),
    DomainPack(
        domain_id="logistics_ops",
        name="Logistics / operations",
        description="Inventory, shipping, tracking, supplier communication.",
        suggested_job_packs=["weekly_status", "status_action_bundle"],
        suggested_routines=["daily_ops", "inventory_check"],
        suggested_model_classes=["llama3.2", "mistral"],
        suggested_embedding_classes=["nomic-embed-text"],
        suggested_ocr_vision_classes=[],
        suggested_integration_classes=[],
        suggested_recipe_id="retrieval_only",
        expected_approvals=["path_workspace", "apply_confirm", "external_api"],
        trust_notes="External systems; explicit approval for any API.",
        field_keywords=["logistics", "operations", "supply_chain", "inventory"],
        job_family_keywords=["logistics", "operations", "planner"],
    ),
    DomainPack(
        domain_id="research_analyst",
        name="Research / analyst",
        description="Data analysis, literature, reports, dashboards.",
        suggested_job_packs=["weekly_status", "status_action_bundle", "meeting_brief_bundle"],
        suggested_routines=["research_digest", "weekly_analysis"],
        suggested_model_classes=["llama3.2", "mistral", "codellama"],
        suggested_embedding_classes=["nomic-embed-text", "mxbai-embed-large"],
        suggested_ocr_vision_classes=[],
        suggested_integration_classes=[],
        suggested_recipe_id="adapter_finetune",
        expected_approvals=["path_workspace", "apply_confirm", "data_export"],
        trust_notes="Sensitive data; retrieval and local adapter preferred.",
        field_keywords=["research", "analyst", "data", "analytics"],
        job_family_keywords=["analyst", "researcher", "data"],
    ),
    DomainPack(
        domain_id="coding_development",
        name="Coding / development",
        description="Code assistance, scaffolding, review, docs.",
        suggested_job_packs=[],
        suggested_routines=[],
        suggested_model_classes=["codellama", "llama3.2", "mistral", "deepseek-coder"],
        suggested_embedding_classes=["nomic-embed-text"],
        suggested_ocr_vision_classes=[],
        suggested_integration_classes=[],
        suggested_recipe_id="coding_agent",
        expected_approvals=["path_repo", "apply_confirm"],
        trust_notes="Code changes require explicit apply; simulate-first.",
        field_keywords=["coding", "development", "software", "engineering"],
        job_family_keywords=["developer", "engineer", "programmer"],
    ),
    DomainPack(
        domain_id="document_knowledge_worker",
        name="Document-heavy knowledge worker",
        description="Long-form docs, knowledge bases, summarization.",
        suggested_job_packs=["weekly_status", "meeting_brief_bundle"],
        suggested_routines=["doc_review", "weekly_digest"],
        suggested_model_classes=["llama3.2", "mistral", "phi"],
        suggested_embedding_classes=["nomic-embed-text", "mxbai-embed-large"],
        suggested_ocr_vision_classes=[],
        suggested_integration_classes=[],
        suggested_recipe_id="embedding_refresh",
        expected_approvals=["path_workspace", "apply_confirm"],
        trust_notes="Local corpus and embeddings only by default.",
        field_keywords=["document", "knowledge", "writing", "content"],
        job_family_keywords=["writer", "knowledge", "content"],
    ),
    DomainPack(
        domain_id="multilingual",
        name="Multilingual support",
        description="Multiple languages, translation, localisation.",
        suggested_job_packs=["weekly_status", "status_action_bundle"],
        suggested_routines=[],
        suggested_model_classes=["llama3.2", "mistral", "aya"],
        suggested_embedding_classes=["nomic-embed-text", "multilingual-e5"],
        suggested_ocr_vision_classes=[],
        suggested_integration_classes=[],
        suggested_recipe_id="retrieval_only",
        expected_approvals=["path_workspace", "apply_confirm"],
        trust_notes="Model choice affects language coverage.",
        field_keywords=["multilingual", "translation", "localisation", "i18n"],
        job_family_keywords=["translator", "localisation"],
    ),
    DomainPack(
        domain_id="document_ocr_heavy",
        name="Document / OCR heavy workflows",
        description="Scanned docs, forms, tables, OCR-heavy pipelines.",
        suggested_job_packs=["weekly_status"],
        suggested_routines=[],
        suggested_model_classes=["llama3.2", "mistral", "llava"],
        suggested_embedding_classes=["nomic-embed-text"],
        suggested_ocr_vision_classes=["llava", "minicpm-v"],
        suggested_integration_classes=[],
        suggested_recipe_id="ocr_doc",
        expected_approvals=["path_workspace", "apply_confirm", "ocr_output"],
        trust_notes="OCR output should be reviewed before apply.",
        field_keywords=["ocr", "document", "forms", "scanning"],
        job_family_keywords=["document", "forms", "data_entry"],
    ),
]


def list_domain_packs() -> list[str]:
    """Return list of domain pack IDs."""
    return [p.domain_id for p in BUILTIN_DOMAIN_PACKS]


def get_domain_pack(domain_id: str) -> DomainPack | None:
    """Return domain pack by id, or None."""
    for p in BUILTIN_DOMAIN_PACKS:
        if p.domain_id == domain_id:
            return p
    return None


def recommend_domain_packs(
    field: str = "",
    job_family: str = "",
    daily_task_style: str = "",
    **kwargs: Any,
) -> list[tuple[DomainPack, float]]:
    """
    Recommend domain packs by user profile. Returns list of (DomainPack, score) sorted by score descending.
    Score in [0, 1]; keyword match on field, job_family, daily_task_style.
    """
    field_lower = (field or "").strip().lower()
    job_lower = (job_family or "").strip().lower()
    task_lower = (daily_task_style or "").strip().lower()
    scored: list[tuple[DomainPack, float]] = []
    for pack in BUILTIN_DOMAIN_PACKS:
        score = 0.0
        if field_lower:
            for kw in pack.field_keywords:
                if kw in field_lower or field_lower in kw:
                    score += 0.4
                    break
        if job_lower:
            for kw in pack.job_family_keywords:
                if kw in job_lower or job_lower in kw:
                    score += 0.4
                    break
        if task_lower:
            if "document" in task_lower and "document" in pack.domain_id:
                score += 0.2
            if "code" in task_lower and pack.domain_id == "coding_development":
                score += 0.2
        if score <= 0.0:
            score = 0.1  # minimal so all packs can appear if no match
        scored.append((pack, min(1.0, score)))
    scored.sort(key=lambda x: -x[1])
    return scored
