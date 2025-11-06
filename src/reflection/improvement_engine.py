"""
Automated improvement engine that implements reflection-driven optimizations
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json
from loguru import logger

from .reflection_agent import ReflectionAgent
from .performance_analyzer import PerformanceAnalyzer


class ImprovementEngine:
    """
    Orchestrates continuous improvement through reflection and automated actions
    """

    def __init__(
        self,
        reflection_agent: ReflectionAgent,
        performance_analyzer: PerformanceAnalyzer,
        auto_apply: bool = False
    ):
        """
        Initialize improvement engine

        Args:
            reflection_agent: Reflection agent instance
            performance_analyzer: Performance analyzer instance
            auto_apply: Whether to automatically apply improvements
        """
        self.reflection_agent = reflection_agent
        self.performance_analyzer = performance_analyzer
        self.auto_apply = auto_apply

        # Track improvements
        self.improvement_history: List[Dict] = []
        self.pending_improvements: List[Dict] = []
        self.applied_improvements: List[Dict] = []

        logger.info(f"Improvement engine initialized (auto_apply={auto_apply})")

    def run_improvement_cycle(self) -> Dict:
        """
        Run complete improvement cycle

        Returns:
            Results of improvement cycle
        """
        logger.info("Starting improvement cycle...")

        # Step 1: Generate performance report
        performance_report = self.performance_analyzer.generate_performance_report()

        # Step 2: Get AI reflection and recommendations
        reflection = self.reflection_agent.reflect_on_performance(
            performance_metrics=performance_report["overall_metrics"],
            recent_detections=self.performance_analyzer.detection_history[-100:],
            false_positives=self.performance_analyzer.false_positives[-20:],
            missed_defects=self.performance_analyzer.false_negatives[-20:]
        )

        # Step 3: Convert recommendations to actionable improvements
        improvements = self._create_improvements_from_recommendations(
            reflection["recommendations"],
            reflection["action_items"]
        )

        # Step 4: Prioritize improvements
        prioritized = self._prioritize_improvements(improvements, performance_report)

        # Step 5: Apply improvements if auto_apply is enabled
        if self.auto_apply:
            results = self._apply_improvements(prioritized)
        else:
            self.pending_improvements.extend(prioritized)
            results = {"status": "improvements_pending", "count": len(prioritized)}

        # Step 6: Log cycle results
        cycle_result = {
            "timestamp": datetime.now().isoformat(),
            "performance_report": performance_report,
            "reflection": reflection,
            "improvements_identified": len(improvements),
            "improvements_applied": results.get("applied", 0),
            "status": results.get("status", "completed")
        }

        self.improvement_history.append(cycle_result)

        logger.info(f"Improvement cycle completed: {len(improvements)} improvements identified")

        return cycle_result

    def _create_improvements_from_recommendations(
        self,
        recommendations: List[str],
        action_items: List[Dict]
    ) -> List[Dict]:
        """Convert AI recommendations to structured improvements"""
        improvements = []

        # Process action items
        for action in action_items:
            improvement = self._parse_action_to_improvement(action)
            if improvement:
                improvements.append(improvement)

        # Process recommendations
        for rec in recommendations:
            improvement = self._parse_recommendation_to_improvement(rec)
            if improvement:
                improvements.append(improvement)

        return improvements

    def _parse_action_to_improvement(self, action: Dict) -> Optional[Dict]:
        """Parse action item into structured improvement"""
        action_text = action.get("action", "").lower()

        improvement = {
            "id": f"IMP-{int(datetime.now().timestamp() * 1000)}",
            "source": "action_item",
            "description": action.get("action", ""),
            "priority": action.get("priority", "medium"),
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

        # Identify improvement type and parameters
        if "threshold" in action_text:
            improvement.update({
                "type": "adjust_threshold",
                "category": "configuration",
                "auto_applicable": True
            })

        elif "retrain" in action_text or "training" in action_text:
            improvement.update({
                "type": "retrain_model",
                "category": "model",
                "auto_applicable": False
            })

        elif "data" in action_text or "collect" in action_text:
            improvement.update({
                "type": "collect_data",
                "category": "data",
                "auto_applicable": False
            })

        elif "preprocessing" in action_text or "lighting" in action_text:
            improvement.update({
                "type": "adjust_preprocessing",
                "category": "preprocessing",
                "auto_applicable": True
            })

        else:
            improvement.update({
                "type": "manual_action",
                "category": "general",
                "auto_applicable": False
            })

        return improvement

    def _parse_recommendation_to_improvement(self, recommendation: str) -> Optional[Dict]:
        """Parse recommendation text into structured improvement"""
        rec_lower = recommendation.lower()

        # Skip if too short or generic
        if len(recommendation) < 20:
            return None

        improvement = {
            "id": f"IMP-{int(datetime.now().timestamp() * 1000)}",
            "source": "recommendation",
            "description": recommendation,
            "priority": "medium",
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }

        # Determine type
        if "threshold" in rec_lower or "confidence" in rec_lower:
            improvement.update({
                "type": "adjust_threshold",
                "category": "configuration",
                "auto_applicable": True
            })

        elif "preprocessing" in rec_lower or "normalization" in rec_lower:
            improvement.update({
                "type": "adjust_preprocessing",
                "category": "preprocessing",
                "auto_applicable": True
            })

        else:
            improvement.update({
                "type": "manual_review",
                "category": "general",
                "auto_applicable": False
            })

        return improvement

    def _prioritize_improvements(
        self,
        improvements: List[Dict],
        performance_report: Dict
    ) -> List[Dict]:
        """Prioritize improvements based on expected impact"""

        # Calculate priority scores
        for improvement in improvements:
            score = 0

            # Base score from stated priority
            priority_scores = {"high": 10, "medium": 5, "low": 2}
            score += priority_scores.get(improvement.get("priority", "medium"), 5)

            # Boost if auto-applicable
            if improvement.get("auto_applicable", False):
                score += 3

            # Boost based on performance issues
            metrics = performance_report.get("overall_metrics", {})

            if improvement["type"] == "adjust_threshold":
                # Boost if precision or recall are low
                precision = metrics.get("precision", 1.0)
                recall = metrics.get("recall", 1.0)

                if precision < 0.85 or recall < 0.85:
                    score += 5

            elif improvement["type"] == "retrain_model":
                # Boost if F1 score is low
                f1 = metrics.get("f1_score", 1.0)
                if f1 < 0.80:
                    score += 8

            improvement["priority_score"] = score

        # Sort by priority score
        prioritized = sorted(improvements, key=lambda x: x["priority_score"], reverse=True)

        return prioritized

    def _apply_improvements(self, improvements: List[Dict]) -> Dict:
        """Apply auto-applicable improvements"""
        applied = []
        skipped = []

        for improvement in improvements:
            if not improvement.get("auto_applicable", False):
                skipped.append(improvement)
                continue

            # Apply based on type
            success = False

            if improvement["type"] == "adjust_threshold":
                success = self._apply_threshold_adjustment(improvement)

            elif improvement["type"] == "adjust_preprocessing":
                success = self._apply_preprocessing_adjustment(improvement)

            if success:
                improvement["status"] = "applied"
                improvement["applied_at"] = datetime.now().isoformat()
                applied.append(improvement)
                self.applied_improvements.append(improvement)
            else:
                improvement["status"] = "failed"
                skipped.append(improvement)

        logger.info(f"Applied {len(applied)} improvements, skipped {len(skipped)}")

        return {
            "status": "completed",
            "applied": len(applied),
            "skipped": len(skipped),
            "applied_improvements": applied,
            "skipped_improvements": skipped
        }

    def _apply_threshold_adjustment(self, improvement: Dict) -> bool:
        """Apply threshold adjustment"""
        # This would interface with the actual detector configuration
        # Placeholder implementation

        logger.info(f"Applied threshold adjustment: {improvement['description']}")

        # In real implementation, this would:
        # 1. Parse recommended threshold from description
        # 2. Update detector configuration
        # 3. Verify the change

        return True

    def _apply_preprocessing_adjustment(self, improvement: Dict) -> bool:
        """Apply preprocessing adjustment"""
        # This would interface with the image processor configuration
        # Placeholder implementation

        logger.info(f"Applied preprocessing adjustment: {improvement['description']}")

        return True

    def get_pending_improvements(self) -> List[Dict]:
        """Get list of pending improvements"""
        return [imp for imp in self.pending_improvements if imp["status"] == "pending"]

    def approve_improvement(self, improvement_id: str) -> bool:
        """
        Manually approve and apply an improvement

        Args:
            improvement_id: Improvement ID

        Returns:
            True if applied successfully
        """
        # Find improvement
        improvement = None
        for imp in self.pending_improvements:
            if imp["id"] == improvement_id:
                improvement = imp
                break

        if not improvement:
            logger.error(f"Improvement not found: {improvement_id}")
            return False

        # Apply based on type
        results = self._apply_improvements([improvement])

        return results["applied"] > 0

    def reject_improvement(self, improvement_id: str, reason: str = "") -> bool:
        """
        Reject an improvement

        Args:
            improvement_id: Improvement ID
            reason: Reason for rejection

        Returns:
            True if rejected successfully
        """
        for imp in self.pending_improvements:
            if imp["id"] == improvement_id:
                imp["status"] = "rejected"
                imp["rejected_at"] = datetime.now().isoformat()
                imp["rejection_reason"] = reason

                logger.info(f"Rejected improvement {improvement_id}: {reason}")
                return True

        return False

    def get_improvement_history(self, limit: int = 10) -> List[Dict]:
        """Get recent improvement history"""
        return self.improvement_history[-limit:]

    def export_improvements(self, output_path: Path):
        """Export improvement history to file"""
        data = {
            "export_date": datetime.now().isoformat(),
            "total_cycles": len(self.improvement_history),
            "total_improvements": len(self.applied_improvements),
            "pending_improvements": self.get_pending_improvements(),
            "improvement_history": self.improvement_history,
            "applied_improvements": self.applied_improvements
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported improvements to {output_path}")
