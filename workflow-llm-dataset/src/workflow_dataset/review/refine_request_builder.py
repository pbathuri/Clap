"""
M12: Build RefineRequest from artifact, user instruction, and config.
"""

from __future__ import annotations

from workflow_dataset.review.review_models import RefineRequest
from workflow_dataset.utils.dates import utc_now_iso
from workflow_dataset.utils.hashes import stable_id


def build_refine_request(
    artifact_id: str,
    generation_id: str,
    use_llm: bool = False,
    user_instruction: str = "",
    style_constraints: list[str] | None = None,
    structural_constraints: list[str] | None = None,
) -> RefineRequest:
    """Build a RefineRequest for document refinement."""
    ts = utc_now_iso()
    refine_id = stable_id("refine", artifact_id, generation_id, ts, prefix="ref")
    return RefineRequest(
        refine_id=refine_id,
        artifact_id=artifact_id,
        generation_id=generation_id,
        refine_mode="llm" if use_llm else "deterministic",
        use_llm=use_llm,
        style_constraints=style_constraints or [],
        structural_constraints=structural_constraints or [],
        user_instruction=user_instruction.strip(),
        created_utc=ts,
    )
