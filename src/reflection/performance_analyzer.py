"""
Performance analysis and metrics tracking
"""

from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import numpy as np
from loguru import logger


class PerformanceAnalyzer:
    """
    Analyzes system performance and tracks metrics over time
    """

    def __init__(self):
        """Initialize performance analyzer"""
        self.detection_history: List[Dict] = []
        self.false_positives: List[Dict] = []
        self.false_negatives: List[Dict] = []
        self.ground_truth_comparisons: List[Dict] = []

        logger.info("Performance analyzer initialized")

    def record_detection(
        self,
        detection: Dict,
        ground_truth: Optional[Dict] = None,
        is_correct: Optional[bool] = None
    ):
        """
        Record a detection for analysis

        Args:
            detection: Detection result
            ground_truth: Ground truth annotation (if available)
            is_correct: Whether the detection was correct
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "detection": detection,
            "ground_truth": ground_truth,
            "is_correct": is_correct
        }

        self.detection_history.append(record)

        # Classify detection type
        if is_correct is False:
            if ground_truth is None:
                # False positive - detected but no ground truth
                self.false_positives.append(record)
            else:
                # Misclassification or poor localization
                self.false_negatives.append(record)

        if ground_truth is not None:
            self.ground_truth_comparisons.append(record)

    def calculate_metrics(
        self,
        time_window: Optional[timedelta] = None
    ) -> Dict:
        """
        Calculate performance metrics

        Args:
            time_window: Optional time window for metrics

        Returns:
            Dictionary of performance metrics
        """
        # Filter by time window if specified
        if time_window:
            cutoff = datetime.now() - time_window
            detections = [
                d for d in self.detection_history
                if datetime.fromisoformat(d["timestamp"]) > cutoff
            ]
        else:
            detections = self.detection_history

        if not detections:
            return {"error": "No detections to analyze"}

        # Calculate basic metrics
        total = len(detections)
        with_gt = [d for d in detections if d["ground_truth"] is not None]
        correct = [d for d in detections if d.get("is_correct") is True]

        metrics = {
            "total_detections": total,
            "detections_with_ground_truth": len(with_gt),
            "correct_detections": len(correct),
            "false_positives": len(self.false_positives),
            "false_negatives": len(self.false_negatives),
        }

        # Calculate precision, recall, F1
        if len(with_gt) > 0:
            true_positives = len(correct)
            false_positives = len([d for d in detections if d.get("is_correct") is False])
            false_negatives = len(self.false_negatives)

            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

            metrics.update({
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score
            })

        # Calculate average confidence
        confidences = [
            d["detection"].get("confidence", 0)
            for d in detections
            if "detection" in d
        ]

        if confidences:
            metrics.update({
                "avg_confidence": np.mean(confidences),
                "median_confidence": np.median(confidences),
                "min_confidence": np.min(confidences),
                "max_confidence": np.max(confidences)
            })

        # Defect type distribution
        defect_types = defaultdict(int)
        for d in detections:
            if "detection" in d:
                defect_type = d["detection"].get("defect_type", "unknown")
                defect_types[defect_type] += 1

        metrics["defect_type_distribution"] = dict(defect_types)

        logger.info(f"Calculated metrics: Precision={metrics.get('precision', 0):.3f}, Recall={metrics.get('recall', 0):.3f}")

        return metrics

    def analyze_false_positives(self) -> Dict:
        """
        Analyze patterns in false positives

        Returns:
            Analysis of false positive patterns
        """
        if not self.false_positives:
            return {"message": "No false positives to analyze"}

        # Analyze by defect type
        by_type = defaultdict(int)
        by_confidence = []
        by_time_of_day = defaultdict(int)

        for fp in self.false_positives:
            detection = fp["detection"]

            # By type
            defect_type = detection.get("defect_type", "unknown")
            by_type[defect_type] += 1

            # By confidence
            confidence = detection.get("confidence", 0)
            by_confidence.append(confidence)

            # By time of day
            timestamp = datetime.fromisoformat(fp["timestamp"])
            hour = timestamp.hour
            time_bucket = f"{hour:02d}:00"
            by_time_of_day[time_bucket] += 1

        analysis = {
            "total_false_positives": len(self.false_positives),
            "by_defect_type": dict(by_type),
            "confidence_stats": {
                "mean": np.mean(by_confidence),
                "median": np.median(by_confidence),
                "std": np.std(by_confidence)
            },
            "by_time_of_day": dict(by_time_of_day),
            "patterns": self._identify_fp_patterns(self.false_positives)
        }

        return analysis

    def analyze_missed_defects(self) -> Dict:
        """
        Analyze patterns in missed defects (false negatives)

        Returns:
            Analysis of missed defect patterns
        """
        if not self.false_negatives:
            return {"message": "No missed defects to analyze"}

        # Analyze patterns
        by_type = defaultdict(int)
        severity_distribution = defaultdict(int)

        for fn in self.false_negatives:
            gt = fn.get("ground_truth", {})

            # By type
            defect_type = gt.get("defect_type", "unknown")
            by_type[defect_type] += 1

            # By severity
            severity = gt.get("severity", "unknown")
            severity_distribution[severity] += 1

        analysis = {
            "total_missed_defects": len(self.false_negatives),
            "by_defect_type": dict(by_type),
            "by_severity": dict(severity_distribution),
            "patterns": self._identify_fn_patterns(self.false_negatives)
        }

        return analysis

    def _identify_fp_patterns(self, false_positives: List[Dict]) -> List[str]:
        """Identify common patterns in false positives"""
        patterns = []

        # Check if low confidence FPs are common
        low_conf_fp = [
            fp for fp in false_positives
            if fp["detection"].get("confidence", 1.0) < 0.6
        ]

        if len(low_conf_fp) > len(false_positives) * 0.5:
            patterns.append(
                f"Over 50% of false positives have low confidence (<0.6). "
                f"Consider raising confidence threshold."
            )

        # Check for specific defect types
        type_counts = defaultdict(int)
        for fp in false_positives:
            defect_type = fp["detection"].get("defect_type", "unknown")
            type_counts[defect_type] += 1

        for defect_type, count in type_counts.items():
            if count > len(false_positives) * 0.3:
                patterns.append(
                    f"Defect type '{defect_type}' accounts for {count}/{len(false_positives)} "
                    f"false positives. Model may need retraining for this type."
                )

        return patterns

    def _identify_fn_patterns(self, false_negatives: List[Dict]) -> List[str]:
        """Identify common patterns in false negatives"""
        patterns = []

        # Check for specific defect types being missed
        type_counts = defaultdict(int)
        for fn in false_negatives:
            defect_type = fn.get("ground_truth", {}).get("defect_type", "unknown")
            type_counts[defect_type] += 1

        for defect_type, count in type_counts.items():
            if count > len(false_negatives) * 0.3:
                patterns.append(
                    f"Defect type '{defect_type}' frequently missed ({count}/{len(false_negatives)}). "
                    f"More training data needed for this type."
                )

        # Check severity
        critical_missed = [
            fn for fn in false_negatives
            if fn.get("ground_truth", {}).get("severity") == "critical"
        ]

        if critical_missed:
            patterns.append(
                f"WARNING: {len(critical_missed)} critical defects were missed! "
                f"This requires immediate attention."
            )

        return patterns

    def calculate_confusion_matrix(self) -> Dict:
        """
        Calculate confusion matrix for defect types

        Returns:
            Confusion matrix as nested dictionary
        """
        matrix = defaultdict(lambda: defaultdict(int))

        for record in self.ground_truth_comparisons:
            gt = record.get("ground_truth", {})
            detection = record.get("detection", {})

            true_type = gt.get("defect_type", "none")
            pred_type = detection.get("defect_type", "none")

            matrix[true_type][pred_type] += 1

        return dict(matrix)

    def get_performance_trend(
        self,
        window_hours: int = 24,
        num_windows: int = 7
    ) -> Dict:
        """
        Get performance trend over time

        Args:
            window_hours: Hours per window
            num_windows: Number of windows to analyze

        Returns:
            Performance trend data
        """
        trend_data = []
        now = datetime.now()

        for i in range(num_windows):
            window_start = now - timedelta(hours=(i + 1) * window_hours)
            window_end = now - timedelta(hours=i * window_hours)

            # Filter detections in this window
            window_detections = [
                d for d in self.detection_history
                if window_start <= datetime.fromisoformat(d["timestamp"]) < window_end
            ]

            # Calculate metrics for window
            if window_detections:
                correct = [d for d in window_detections if d.get("is_correct") is True]
                accuracy = len(correct) / len(window_detections) if window_detections else 0
            else:
                accuracy = None

            trend_data.append({
                "window_start": window_start.isoformat(),
                "window_end": window_end.isoformat(),
                "detection_count": len(window_detections),
                "accuracy": accuracy
            })

        return {
            "trend_data": list(reversed(trend_data)),
            "improving": self._is_improving(trend_data)
        }

    def _is_improving(self, trend_data: List[Dict]) -> bool:
        """Check if performance is improving over time"""
        accuracies = [t["accuracy"] for t in trend_data if t["accuracy"] is not None]

        if len(accuracies) < 2:
            return None

        # Simple linear trend
        recent_avg = np.mean(accuracies[:len(accuracies)//2])
        older_avg = np.mean(accuracies[len(accuracies)//2:])

        return recent_avg > older_avg

    def generate_performance_report(self) -> Dict:
        """
        Generate comprehensive performance report

        Returns:
            Complete performance report
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_metrics": self.calculate_metrics(),
            "false_positive_analysis": self.analyze_false_positives(),
            "missed_defect_analysis": self.analyze_missed_defects(),
            "confusion_matrix": self.calculate_confusion_matrix(),
            "performance_trend": self.get_performance_trend()
        }

        logger.info("Generated performance report")

        return report
