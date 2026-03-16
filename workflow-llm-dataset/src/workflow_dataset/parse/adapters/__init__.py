"""
Domain adapters: interpret parsed artifacts and emit structured signals.

Each adapter declares supported artifact families, inspects metadata/content,
and infers domain relevance, style/workflow hints. Deterministic and explainable.
"""

from workflow_dataset.parse.adapters.base_adapter import BaseDomainAdapter, AdapterSignal
from workflow_dataset.parse.adapters.document_adapter import DocumentAdapter
from workflow_dataset.parse.adapters.tabular_adapter import TabularAdapter
from workflow_dataset.parse.adapters.creative_adapter import CreativeAdapter
from workflow_dataset.parse.adapters.design_adapter import DesignAdapter
from workflow_dataset.parse.adapters.finance_adapter import FinanceAdapter
from workflow_dataset.parse.adapters.ops_adapter import OpsAdapter

def get_adapters() -> list[BaseDomainAdapter]:
    return [
        DocumentAdapter(),
        TabularAdapter(),
        CreativeAdapter(),
        DesignAdapter(),
        FinanceAdapter(),
        OpsAdapter(),
    ]

__all__ = [
    "BaseDomainAdapter",
    "AdapterSignal",
    "DocumentAdapter",
    "TabularAdapter",
    "CreativeAdapter",
    "DesignAdapter",
    "FinanceAdapter",
    "OpsAdapter",
    "get_adapters",
]
