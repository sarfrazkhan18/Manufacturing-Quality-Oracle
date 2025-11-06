"""
Process Deviation Detection with Automatic Corrective Actions
Uses Statistical Process Control (SPC) and anomaly detection
"""

from typing import List, Dict, Optional, Callable, Tuple
from datetime import datetime, timedelta
from collections import deque
import numpy as np
from scipy import stats
from loguru import logger

from ..config import settings


class ProcessDeviationMonitor:
    """
    Monitor manufacturing processes for deviations and trigger corrective actions
    """

    def __init__(
        self,
        deviation_threshold: Optional[float] = None,
        window_size: int = 50
    ):
        """
        Initialize process monitor

        Args:
            deviation_threshold: Number of standard deviations for alert
            window_size: Number of samples for rolling window
        """
        self.deviation_threshold = deviation_threshold or settings.thresholds.process_deviation_threshold
        self.window_size = window_size

        # Process metrics storage
        self.metrics: Dict[str, deque] = {}
        self.baselines: Dict[str, Dict] = {}

        # Deviation history
        self.deviations: List[Dict] = []

        # Corrective actions registry
        self.corrective_actions: Dict[str, List[Callable]] = {}

        logger.info(
            f"Process deviation monitor initialized "
            f"(threshold={self.deviation_threshold} sigma)"
        )

    def register_metric(
        self,
        metric_name: str,
        baseline_mean: Optional[float] = None,
        baseline_std: Optional[float] = None,
        upper_control_limit: Optional[float] = None,
        lower_control_limit: Optional[float] = None
    ):
        """
        Register a process metric to monitor

        Args:
            metric_name: Name of the metric
            baseline_mean: Baseline mean value
            baseline_std: Baseline standard deviation
            upper_control_limit: Upper control limit (UCL)
            lower_control_limit: Lower control limit (LCL)
        """
        self.metrics[metric_name] = deque(maxlen=self.window_size)

        self.baselines[metric_name] = {
            "mean": baseline_mean,
            "std": baseline_std,
            "ucl": upper_control_limit,
            "lcl": lower_control_limit,
            "auto_baseline": baseline_mean is None
        }

        logger.info(f"Registered metric: {metric_name}")

    def record_measurement(
        self,
        metric_name: str,
        value: float,
        timestamp: Optional[datetime] = None
    ) -> Optional[Dict]:
        """
        Record a measurement and check for deviations

        Args:
            metric_name: Metric name
            value: Measured value
            timestamp: Measurement timestamp

        Returns:
            Deviation alert if detected, None otherwise
        """
        if metric_name not in self.metrics:
            logger.warning(f"Unknown metric: {metric_name}")
            return None

        timestamp = timestamp or datetime.now()

        # Store measurement
        measurement = {
            "value": value,
            "timestamp": timestamp.isoformat()
        }

        self.metrics[metric_name].append(measurement)

        # Update baseline if auto-calculating
        if self.baselines[metric_name]["auto_baseline"]:
            self._update_baseline(metric_name)

        # Check for deviation
        deviation = self._check_deviation(metric_name, value, timestamp)

        if deviation:
            # Store deviation
            self.deviations.append(deviation)

            # Trigger corrective actions
            self._trigger_corrective_actions(metric_name, deviation)

            return deviation

        return None

    def _update_baseline(self, metric_name: str):
        """Update baseline statistics from recent measurements"""

        values = [m["value"] for m in self.metrics[metric_name]]

        if len(values) >= 10:  # Need minimum samples
            mean = np.mean(values)
            std = np.std(values)

            # Control limits (3-sigma)
            ucl = mean + (3 * std)
            lcl = mean - (3 * std)

            self.baselines[metric_name].update({
                "mean": mean,
                "std": std,
                "ucl": ucl,
                "lcl": lcl
            })

    def _check_deviation(
        self,
        metric_name: str,
        value: float,
        timestamp: datetime
    ) -> Optional[Dict]:
        """Check if value represents a process deviation"""

        baseline = self.baselines[metric_name]

        if baseline["mean"] is None or baseline["std"] is None:
            return None  # Not enough data for baseline

        # Calculate z-score
        z_score = (value - baseline["mean"]) / baseline["std"] if baseline["std"] > 0 else 0

        # Check control limits
        deviation_detected = False
        deviation_type = None

        if abs(z_score) > self.deviation_threshold:
            deviation_detected = True
            deviation_type = "statistical"

        elif baseline["ucl"] and value > baseline["ucl"]:
            deviation_detected = True
            deviation_type = "upper_limit"

        elif baseline["lcl"] and value < baseline["lcl"]:
            deviation_detected = True
            deviation_type = "lower_limit"

        # Check for trend violations (7 consecutive points on one side of mean)
        elif self._check_trend_violation(metric_name):
            deviation_detected = True
            deviation_type = "trend"

        # Check for variability violations (unusual variation pattern)
        elif self._check_variability_violation(metric_name):
            deviation_detected = True
            deviation_type = "variability"

        if deviation_detected:
            # Determine severity
            severity = "critical" if abs(z_score) > 4 else "high" if abs(z_score) > 3 else "medium"

            deviation = {
                "metric_name": metric_name,
                "value": value,
                "baseline_mean": baseline["mean"],
                "baseline_std": baseline["std"],
                "z_score": z_score,
                "deviation_type": deviation_type,
                "severity": severity,
                "timestamp": timestamp.isoformat(),
                "corrective_actions_triggered": False
            }

            logger.warning(
                f"DEVIATION DETECTED: {metric_name}={value:.2f} "
                f"(z={z_score:.2f}, type={deviation_type}, severity={severity})"
            )

            return deviation

        return None

    def _check_trend_violation(self, metric_name: str) -> bool:
        """Check for trend violations (7+ consecutive points on one side of mean)"""

        values = [m["value"] for m in self.metrics[metric_name]]
        baseline_mean = self.baselines[metric_name]["mean"]

        if len(values) < 7:
            return False

        # Check last 7 values
        recent_7 = values[-7:]

        # All above mean
        if all(v > baseline_mean for v in recent_7):
            return True

        # All below mean
        if all(v < baseline_mean for v in recent_7):
            return True

        return False

    def _check_variability_violation(self, metric_name: str) -> bool:
        """Check for unusual variability patterns"""

        values = [m["value"] for m in self.metrics[metric_name]]

        if len(values) < 10:
            return False

        # Calculate recent variance vs baseline
        recent_std = np.std(values[-10:])
        baseline_std = self.baselines[metric_name]["std"]

        if baseline_std and baseline_std > 0:
            # Variance increased significantly
            if recent_std > baseline_std * 2:
                return True

        return False

    def register_corrective_action(
        self,
        metric_name: str,
        action: Callable[[Dict], None],
        description: str = ""
    ):
        """
        Register a corrective action for a metric

        Args:
            metric_name: Metric name
            action: Callable that takes deviation dict as parameter
            description: Description of the action
        """
        if metric_name not in self.corrective_actions:
            self.corrective_actions[metric_name] = []

        action_info = {
            "function": action,
            "description": description,
            "registered_at": datetime.now().isoformat()
        }

        self.corrective_actions[metric_name].append(action_info)

        logger.info(f"Registered corrective action for {metric_name}: {description}")

    def _trigger_corrective_actions(self, metric_name: str, deviation: Dict):
        """Trigger registered corrective actions"""

        actions = self.corrective_actions.get(metric_name, [])

        if not actions:
            logger.info(f"No corrective actions registered for {metric_name}")
            return

        logger.info(f"Triggering {len(actions)} corrective actions for {metric_name}")

        for action_info in actions:
            try:
                action_func = action_info["function"]
                action_func(deviation)

                logger.info(f"Executed corrective action: {action_info['description']}")

            except Exception as e:
                logger.error(f"Error executing corrective action: {e}")

        deviation["corrective_actions_triggered"] = True

    def get_process_status(self, metric_name: Optional[str] = None) -> Dict:
        """
        Get current process status

        Args:
            metric_name: Optional specific metric, or all metrics if None

        Returns:
            Process status summary
        """
        if metric_name:
            metrics_to_check = [metric_name] if metric_name in self.metrics else []
        else:
            metrics_to_check = list(self.metrics.keys())

        status = {}

        for name in metrics_to_check:
            values = [m["value"] for m in self.metrics[name]]

            if not values:
                status[name] = {"status": "no_data"}
                continue

            baseline = self.baselines[name]
            current_value = values[-1]

            # Calculate current z-score
            if baseline["mean"] is not None and baseline["std"] is not None and baseline["std"] > 0:
                z_score = (current_value - baseline["mean"]) / baseline["std"]
            else:
                z_score = 0

            # Determine status
            if abs(z_score) > self.deviation_threshold:
                process_status = "out_of_control"
            elif abs(z_score) > self.deviation_threshold * 0.7:
                process_status = "warning"
            else:
                process_status = "in_control"

            status[name] = {
                "status": process_status,
                "current_value": current_value,
                "baseline_mean": baseline["mean"],
                "z_score": z_score,
                "sample_count": len(values)
            }

        return status

    def get_recent_deviations(
        self,
        metric_name: Optional[str] = None,
        hours: int = 24,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent deviations

        Args:
            metric_name: Optional metric filter
            hours: Hours to look back
            limit: Maximum number of deviations

        Returns:
            List of recent deviations
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        deviations = [
            d for d in self.deviations
            if datetime.fromisoformat(d["timestamp"]) > cutoff
        ]

        if metric_name:
            deviations = [d for d in deviations if d["metric_name"] == metric_name]

        # Sort by timestamp (most recent first)
        deviations.sort(key=lambda x: x["timestamp"], reverse=True)

        return deviations[:limit]

    def generate_control_chart_data(self, metric_name: str) -> Dict:
        """
        Generate data for Statistical Process Control (SPC) chart

        Args:
            metric_name: Metric name

        Returns:
            Control chart data
        """
        if metric_name not in self.metrics:
            return {"error": "Unknown metric"}

        baseline = self.baselines[metric_name]
        measurements = list(self.metrics[metric_name])

        chart_data = {
            "metric_name": metric_name,
            "measurements": measurements,
            "baseline_mean": baseline["mean"],
            "baseline_std": baseline["std"],
            "ucl": baseline["ucl"],
            "lcl": baseline["lcl"],
            "deviation_threshold": self.deviation_threshold
        }

        # Calculate additional control lines
        if baseline["mean"] is not None and baseline["std"] is not None:
            chart_data["upper_warning"] = baseline["mean"] + (2 * baseline["std"])
            chart_data["lower_warning"] = baseline["mean"] - (2 * baseline["std"])

        return chart_data

    def calculate_process_capability(self, metric_name: str) -> Dict:
        """
        Calculate process capability indices (Cp, Cpk)

        Args:
            metric_name: Metric name

        Returns:
            Process capability metrics
        """
        if metric_name not in self.metrics:
            return {"error": "Unknown metric"}

        baseline = self.baselines[metric_name]
        values = [m["value"] for m in self.metrics[metric_name]]

        if not values or baseline["ucl"] is None or baseline["lcl"] is None:
            return {"error": "Insufficient data for capability calculation"}

        # Process capability indices
        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return {"error": "Zero standard deviation"}

        # Cp: Process capability (centered process)
        cp = (baseline["ucl"] - baseline["lcl"]) / (6 * std)

        # Cpk: Process capability index (accounts for centering)
        cpu = (baseline["ucl"] - mean) / (3 * std)
        cpl = (mean - baseline["lcl"]) / (3 * std)
        cpk = min(cpu, cpl)

        # Interpretation
        if cpk >= 1.67:
            capability = "excellent"
        elif cpk >= 1.33:
            capability = "adequate"
        elif cpk >= 1.0:
            capability = "marginal"
        else:
            capability = "inadequate"

        return {
            "metric_name": metric_name,
            "cp": cp,
            "cpk": cpk,
            "cpu": cpu,
            "cpl": cpl,
            "capability": capability,
            "interpretation": self._interpret_capability(cp, cpk)
        }

    def _interpret_capability(self, cp: float, cpk: float) -> str:
        """Generate capability interpretation"""

        if cpk < 1.0:
            return (
                f"Process is not capable (Cpk={cpk:.2f}). "
                f"Defect rate is high. Immediate process improvement required."
            )

        elif cpk < 1.33:
            return (
                f"Process is marginally capable (Cpk={cpk:.2f}). "
                f"Some defects expected. Process improvement recommended."
            )

        elif cpk < 1.67:
            return (
                f"Process is adequate (Cpk={cpk:.2f}). "
                f"Low defect rate. Continue monitoring."
            )

        else:
            return (
                f"Process is excellent (Cpk={cpk:.2f}). "
                f"Very low defect rate. Process is well-controlled."
            )
