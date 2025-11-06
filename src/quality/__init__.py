"""
Quality management components
"""

from .supplier_quality import SupplierQualityPredictor
from .customer_feedback import CustomerFeedbackIntegration
from .process_monitor import ProcessDeviationMonitor

__all__ = [
    "SupplierQualityPredictor",
    "CustomerFeedbackIntegration",
    "ProcessDeviationMonitor"
]
