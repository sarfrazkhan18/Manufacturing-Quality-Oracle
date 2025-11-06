"""
Supplier Quality Prediction System
Predicts supplier quality based on historical performance data
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import pandas as pd
from loguru import logger

from ..config import settings


class SupplierQualityPredictor:
    """
    ML-based supplier quality prediction system
    """

    def __init__(self, min_score: Optional[float] = None):
        """
        Initialize supplier quality predictor

        Args:
            min_score: Minimum acceptable quality score
        """
        self.min_score = min_score or settings.thresholds.supplier_min_score

        # Supplier database
        self.suppliers: Dict[str, Dict] = {}

        # Historical data
        self.delivery_history: List[Dict] = []
        self.quality_history: List[Dict] = []
        self.defect_history: List[Dict] = []

        # ML models
        self.quality_predictor: Optional[RandomForestRegressor] = None
        self.risk_classifier: Optional[GradientBoostingClassifier] = None
        self.scaler = StandardScaler()

        # Model trained flag
        self.is_trained = False

        logger.info(f"Supplier quality predictor initialized (min_score={self.min_score})")

    def register_supplier(
        self,
        supplier_id: str,
        name: str,
        metadata: Optional[Dict] = None
    ):
        """
        Register a new supplier

        Args:
            supplier_id: Unique supplier identifier
            name: Supplier name
            metadata: Additional supplier metadata
        """
        self.suppliers[supplier_id] = {
            "id": supplier_id,
            "name": name,
            "registered_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "quality_score": None,
            "risk_level": "unknown",
            "total_deliveries": 0,
            "defect_rate": 0.0
        }

        logger.info(f"Registered supplier: {name} ({supplier_id})")

    def record_delivery(
        self,
        supplier_id: str,
        parts_count: int,
        defective_count: int,
        delivery_date: Optional[datetime] = None,
        on_time: bool = True,
        metadata: Optional[Dict] = None
    ):
        """
        Record a delivery from supplier

        Args:
            supplier_id: Supplier ID
            parts_count: Number of parts delivered
            defective_count: Number of defective parts
            delivery_date: Delivery date
            on_time: Whether delivery was on time
            metadata: Additional delivery metadata
        """
        if supplier_id not in self.suppliers:
            logger.warning(f"Unknown supplier: {supplier_id}")
            return

        delivery_date = delivery_date or datetime.now()

        # Record delivery
        delivery_record = {
            "supplier_id": supplier_id,
            "parts_count": parts_count,
            "defective_count": defective_count,
            "defect_rate": defective_count / parts_count if parts_count > 0 else 0,
            "delivery_date": delivery_date.isoformat(),
            "on_time": on_time,
            "metadata": metadata or {}
        }

        self.delivery_history.append(delivery_record)

        # Update supplier stats
        self.suppliers[supplier_id]["total_deliveries"] += 1

        # Record defects
        if defective_count > 0:
            self.defect_history.append({
                "supplier_id": supplier_id,
                "count": defective_count,
                "rate": delivery_record["defect_rate"],
                "date": delivery_date.isoformat()
            })

        # Update quality score
        self._update_supplier_score(supplier_id)

        logger.debug(
            f"Recorded delivery from {supplier_id}: "
            f"{parts_count} parts, {defective_count} defects"
        )

    def _update_supplier_score(self, supplier_id: str):
        """Update supplier quality score based on recent performance"""

        # Get recent deliveries (last 90 days)
        cutoff_date = datetime.now() - timedelta(days=90)

        recent_deliveries = [
            d for d in self.delivery_history
            if d["supplier_id"] == supplier_id and
            datetime.fromisoformat(d["delivery_date"]) > cutoff_date
        ]

        if not recent_deliveries:
            return

        # Calculate metrics
        total_parts = sum(d["parts_count"] for d in recent_deliveries)
        total_defects = sum(d["defective_count"] for d in recent_deliveries)
        defect_rate = total_defects / total_parts if total_parts > 0 else 0

        on_time_deliveries = sum(1 for d in recent_deliveries if d["on_time"])
        on_time_rate = on_time_deliveries / len(recent_deliveries)

        # Calculate quality score (0-100)
        # Weighted: 70% defect rate, 30% on-time delivery
        defect_score = (1 - defect_rate) * 100
        delivery_score = on_time_rate * 100

        quality_score = (defect_score * 0.7) + (delivery_score * 0.3)

        # Update supplier
        self.suppliers[supplier_id].update({
            "quality_score": quality_score,
            "defect_rate": defect_rate,
            "on_time_rate": on_time_rate,
            "recent_deliveries": len(recent_deliveries)
        })

        # Determine risk level
        if quality_score >= 90:
            risk_level = "low"
        elif quality_score >= 75:
            risk_level = "medium"
        elif quality_score >= 60:
            risk_level = "high"
        else:
            risk_level = "critical"

        self.suppliers[supplier_id]["risk_level"] = risk_level

        logger.debug(
            f"Updated supplier {supplier_id} score: {quality_score:.2f} (risk: {risk_level})"
        )

    def predict_supplier_quality(
        self,
        supplier_id: str,
        future_days: int = 30
    ) -> Dict:
        """
        Predict future supplier quality

        Args:
            supplier_id: Supplier ID
            future_days: Days to predict into future

        Returns:
            Prediction results
        """
        if supplier_id not in self.suppliers:
            return {"error": "Unknown supplier"}

        supplier = self.suppliers[supplier_id]

        # Get historical trend
        recent_deliveries = [
            d for d in self.delivery_history[-20:]
            if d["supplier_id"] == supplier_id
        ]

        if len(recent_deliveries) < 3:
            return {
                "supplier_id": supplier_id,
                "prediction": "insufficient_data",
                "current_score": supplier.get("quality_score"),
                "message": "Need at least 3 deliveries for prediction"
            }

        # Calculate trend
        defect_rates = [d["defect_rate"] for d in recent_deliveries]
        trend = "stable"

        if len(defect_rates) >= 5:
            recent_avg = np.mean(defect_rates[-3:])
            older_avg = np.mean(defect_rates[:-3])

            if recent_avg > older_avg * 1.2:
                trend = "declining"
            elif recent_avg < older_avg * 0.8:
                trend = "improving"

        # Predict future score
        current_score = supplier.get("quality_score", 75)

        if trend == "improving":
            predicted_score = min(100, current_score + 5)
        elif trend == "declining":
            predicted_score = max(0, current_score - 10)
        else:
            predicted_score = current_score

        prediction = {
            "supplier_id": supplier_id,
            "supplier_name": supplier["name"],
            "current_score": current_score,
            "predicted_score": predicted_score,
            "trend": trend,
            "risk_level": supplier["risk_level"],
            "confidence": self._calculate_prediction_confidence(recent_deliveries),
            "recommendation": self._generate_recommendation(supplier, trend)
        }

        return prediction

    def _calculate_prediction_confidence(self, deliveries: List[Dict]) -> float:
        """Calculate confidence in prediction based on data quality"""

        # More deliveries = higher confidence
        delivery_confidence = min(1.0, len(deliveries) / 20)

        # Consistent performance = higher confidence
        defect_rates = [d["defect_rate"] for d in deliveries]
        if len(defect_rates) > 1:
            variance = np.var(defect_rates)
            consistency_confidence = 1.0 / (1.0 + variance * 10)
        else:
            consistency_confidence = 0.5

        # Overall confidence
        confidence = (delivery_confidence * 0.6) + (consistency_confidence * 0.4)

        return confidence

    def _generate_recommendation(self, supplier: Dict, trend: str) -> str:
        """Generate recommendation for supplier"""

        score = supplier.get("quality_score", 0)
        risk = supplier["risk_level"]

        if risk == "critical":
            return f"URGENT: Consider alternative suppliers. Quality score ({score:.1f}) is below acceptable threshold."

        elif risk == "high":
            if trend == "declining":
                return f"WARNING: Quality declining. Schedule supplier audit and quality improvement meeting."
            else:
                return f"Monitor closely. Current score ({score:.1f}) requires attention."

        elif risk == "medium":
            if trend == "declining":
                return f"Quality declining. Request corrective action plan from supplier."
            elif trend == "improving":
                return f"Quality improving. Continue monitoring and provide positive feedback."
            else:
                return f"Acceptable quality. Maintain current monitoring schedule."

        else:  # low risk
            return f"Excellent supplier performance. Consider for preferred supplier status."

    def get_supplier_ranking(self, limit: int = 10) -> List[Dict]:
        """
        Get top suppliers ranked by quality score

        Args:
            limit: Number of suppliers to return

        Returns:
            List of suppliers ranked by quality score
        """
        # Filter suppliers with scores
        scored_suppliers = [
            s for s in self.suppliers.values()
            if s.get("quality_score") is not None
        ]

        # Sort by quality score
        ranked = sorted(
            scored_suppliers,
            key=lambda x: x.get("quality_score", 0),
            reverse=True
        )

        return ranked[:limit]

    def get_at_risk_suppliers(self, threshold: Optional[float] = None) -> List[Dict]:
        """
        Get suppliers at risk (below threshold)

        Args:
            threshold: Quality score threshold

        Returns:
            List of at-risk suppliers
        """
        threshold = threshold or self.min_score

        at_risk = [
            s for s in self.suppliers.values()
            if s.get("quality_score") is not None and
            s["quality_score"] < threshold
        ]

        # Sort by score (worst first)
        at_risk.sort(key=lambda x: x.get("quality_score", 100))

        return at_risk

    def generate_supplier_report(self, supplier_id: str) -> Dict:
        """
        Generate comprehensive supplier report

        Args:
            supplier_id: Supplier ID

        Returns:
            Detailed supplier report
        """
        if supplier_id not in self.suppliers:
            return {"error": "Unknown supplier"}

        supplier = self.suppliers[supplier_id]

        # Get all deliveries
        deliveries = [
            d for d in self.delivery_history
            if d["supplier_id"] == supplier_id
        ]

        # Get defects
        defects = [
            d for d in self.defect_history
            if d["supplier_id"] == supplier_id
        ]

        # Calculate statistics
        if deliveries:
            total_parts = sum(d["parts_count"] for d in deliveries)
            total_defects = sum(d["defective_count"] for d in deliveries)
            avg_defect_rate = total_defects / total_parts if total_parts > 0 else 0
            on_time_count = sum(1 for d in deliveries if d["on_time"])
            on_time_percentage = (on_time_count / len(deliveries)) * 100
        else:
            total_parts = 0
            total_defects = 0
            avg_defect_rate = 0
            on_time_percentage = 0

        # Get prediction
        prediction = self.predict_supplier_quality(supplier_id)

        report = {
            "supplier_id": supplier_id,
            "supplier_name": supplier["name"],
            "current_score": supplier.get("quality_score"),
            "risk_level": supplier["risk_level"],
            "statistics": {
                "total_deliveries": len(deliveries),
                "total_parts": total_parts,
                "total_defects": total_defects,
                "average_defect_rate": avg_defect_rate,
                "on_time_percentage": on_time_percentage
            },
            "prediction": prediction,
            "recent_deliveries": deliveries[-10:],
            "recommendation": supplier.get("recommendation", "")
        }

        return report

    def export_supplier_data(self) -> pd.DataFrame:
        """
        Export supplier data as DataFrame

        Returns:
            DataFrame with supplier metrics
        """
        data = []

        for supplier_id, supplier in self.suppliers.items():
            data.append({
                "supplier_id": supplier_id,
                "supplier_name": supplier["name"],
                "quality_score": supplier.get("quality_score"),
                "risk_level": supplier["risk_level"],
                "defect_rate": supplier.get("defect_rate", 0),
                "on_time_rate": supplier.get("on_time_rate", 0),
                "total_deliveries": supplier["total_deliveries"]
            })

        return pd.DataFrame(data)
