"""
MES (Manufacturing Execution System) Connector
Integrates with MES/ERP systems for quality data exchange
"""

from typing import Dict, List, Optional
import requests
from datetime import datetime
from loguru import logger

from ..config import settings


class MESConnector:
    """
    Connector for MES/ERP systems
    """

    def __init__(
        self,
        mes_api_url: Optional[str] = None,
        mes_api_key: Optional[str] = None,
        erp_api_url: Optional[str] = None,
        erp_api_key: Optional[str] = None
    ):
        """
        Initialize MES connector

        Args:
            mes_api_url: MES API URL
            mes_api_key: MES API key
            erp_api_url: ERP API URL
            erp_api_key: ERP API key
        """
        self.mes_api_url = mes_api_url or settings.integration.mes_api_url
        self.mes_api_key = mes_api_key or settings.integration.mes_api_key
        self.erp_api_url = erp_api_url or settings.integration.erp_api_url
        self.erp_api_key = erp_api_key or settings.integration.erp_api_key

        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })

        logger.info("MES/ERP connector initialized")

    def send_quality_data(
        self,
        inspection_results: List[Dict],
        batch_id: Optional[str] = None
    ) -> bool:
        """
        Send quality inspection data to MES

        Args:
            inspection_results: List of inspection results
            batch_id: Optional batch identifier

        Returns:
            True if successful
        """
        if not self.mes_api_url:
            logger.warning("MES API URL not configured")
            return False

        try:
            payload = {
                "timestamp": datetime.now().isoformat(),
                "batch_id": batch_id,
                "inspection_results": inspection_results,
                "total_inspected": len(inspection_results),
                "defects_found": sum(
                    1 for r in inspection_results
                    if r.get("defect_detected", False)
                )
            }

            response = self.session.post(
                f"{self.mes_api_url}/quality/inspection",
                json=payload,
                headers={"Authorization": f"Bearer {self.mes_api_key}"},
                timeout=30
            )

            response.raise_for_status()

            logger.info(
                f"Sent {len(inspection_results)} inspection results to MES "
                f"(batch: {batch_id})"
            )

            return True

        except Exception as e:
            logger.error(f"Error sending quality data to MES: {e}")
            return False

    def send_defect_alert(
        self,
        defect_data: Dict,
        severity: str = "medium"
    ) -> bool:
        """
        Send defect alert to MES

        Args:
            defect_data: Defect information
            severity: Alert severity

        Returns:
            True if successful
        """
        if not self.mes_api_url:
            logger.warning("MES API URL not configured")
            return False

        try:
            payload = {
                "timestamp": datetime.now().isoformat(),
                "severity": severity,
                "defect_type": defect_data.get("defect_type"),
                "confidence": defect_data.get("confidence"),
                "station_id": defect_data.get("station_id"),
                "product_id": defect_data.get("product_id"),
                "image_path": defect_data.get("image_path")
            }

            response = self.session.post(
                f"{self.mes_api_url}/alerts/defect",
                json=payload,
                headers={"Authorization": f"Bearer {self.mes_api_key}"},
                timeout=30
            )

            response.raise_for_status()

            logger.info(f"Sent defect alert to MES: {defect_data.get('defect_type')}")

            return True

        except Exception as e:
            logger.error(f"Error sending defect alert to MES: {e}")
            return False

    def get_production_schedule(self) -> Optional[List[Dict]]:
        """
        Get production schedule from MES

        Returns:
            Production schedule or None
        """
        if not self.mes_api_url:
            return None

        try:
            response = self.session.get(
                f"{self.mes_api_url}/production/schedule",
                headers={"Authorization": f"Bearer {self.mes_api_key}"},
                timeout=30
            )

            response.raise_for_status()
            schedule = response.json()

            logger.info(f"Retrieved production schedule: {len(schedule)} items")

            return schedule

        except Exception as e:
            logger.error(f"Error retrieving production schedule: {e}")
            return None

    def update_quality_metrics(
        self,
        metrics: Dict,
        time_period: str = "daily"
    ) -> bool:
        """
        Update quality metrics in ERP system

        Args:
            metrics: Quality metrics dictionary
            time_period: Time period for metrics

        Returns:
            True if successful
        """
        if not self.erp_api_url:
            logger.warning("ERP API URL not configured")
            return False

        try:
            payload = {
                "timestamp": datetime.now().isoformat(),
                "time_period": time_period,
                "metrics": metrics
            }

            response = self.session.post(
                f"{self.erp_api_url}/quality/metrics",
                json=payload,
                headers={"Authorization": f"Bearer {self.erp_api_key}"},
                timeout=30
            )

            response.raise_for_status()

            logger.info(f"Updated quality metrics in ERP ({time_period})")

            return True

        except Exception as e:
            logger.error(f"Error updating quality metrics in ERP: {e}")
            return False

    def get_supplier_data(self, supplier_id: str) -> Optional[Dict]:
        """
        Get supplier data from ERP

        Args:
            supplier_id: Supplier identifier

        Returns:
            Supplier data or None
        """
        if not self.erp_api_url:
            return None

        try:
            response = self.session.get(
                f"{self.erp_api_url}/suppliers/{supplier_id}",
                headers={"Authorization": f"Bearer {self.erp_api_key}"},
                timeout=30
            )

            response.raise_for_status()
            supplier_data = response.json()

            logger.info(f"Retrieved supplier data for {supplier_id}")

            return supplier_data

        except Exception as e:
            logger.error(f"Error retrieving supplier data: {e}")
            return None
