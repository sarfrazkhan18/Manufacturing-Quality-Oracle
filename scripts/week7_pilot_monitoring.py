"""
Week 7: Pilot Monitoring and Analysis
Real-time monitoring and reporting for pilot testing
"""

import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import json
import pandas as pd
from loguru import logger
from collections import defaultdict


class PilotMonitor:
    """Monitor and analyze pilot testing performance"""

    def __init__(self, output_dir: str = "data/pilot_results"):
        """
        Initialize pilot monitor

        Args:
            output_dir: Directory to save monitoring data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Tracking data
        self.inspections = []
        self.detections = []
        self.false_positives = []
        self.false_negatives = []
        self.operator_feedback = []

        # Session info
        self.session_start = datetime.now()
        self.session_id = self.session_start.strftime("%Y%m%d_%H%M%S")

        logger.info(f"Pilot monitor initialized: Session {self.session_id}")

    def log_inspection(
        self,
        part_id: str,
        defects_detected: int,
        detection_time_ms: float,
        ground_truth_defects: int = None,
        operator_agrees: bool = None
    ):
        """
        Log an inspection event

        Args:
            part_id: Unique part identifier
            defects_detected: Number of defects detected by AI
            detection_time_ms: Inference time in milliseconds
            ground_truth_defects: Actual number of defects (from operator)
            operator_agrees: Whether operator agrees with AI detection
        """
        inspection = {
            "timestamp": datetime.now().isoformat(),
            "part_id": part_id,
            "defects_detected": defects_detected,
            "detection_time_ms": detection_time_ms,
            "ground_truth_defects": ground_truth_defects,
            "operator_agrees": operator_agrees
        }

        self.inspections.append(inspection)

        # Check for false positives/negatives
        if ground_truth_defects is not None:
            if defects_detected > 0 and ground_truth_defects == 0:
                self.false_positives.append(inspection)
            elif defects_detected == 0 and ground_truth_defects > 0:
                self.false_negatives.append(inspection)

    def log_detection(
        self,
        part_id: str,
        defect_type: str,
        confidence: float,
        severity: str,
        is_correct: bool = None
    ):
        """
        Log individual defect detection

        Args:
            part_id: Part identifier
            defect_type: Type of defect
            confidence: Detection confidence
            severity: Defect severity
            is_correct: Whether detection was correct
        """
        detection = {
            "timestamp": datetime.now().isoformat(),
            "part_id": part_id,
            "defect_type": defect_type,
            "confidence": confidence,
            "severity": severity,
            "is_correct": is_correct
        }

        self.detections.append(detection)

    def log_operator_feedback(
        self,
        operator_id: str,
        feedback_text: str,
        rating: int,
        issues: List[str] = None
    ):
        """
        Log operator feedback

        Args:
            operator_id: Operator identifier
            feedback_text: Feedback text
            rating: Rating (1-5)
            issues: List of issues encountered
        """
        feedback = {
            "timestamp": datetime.now().isoformat(),
            "operator_id": operator_id,
            "feedback_text": feedback_text,
            "rating": rating,
            "issues": issues or []
        }

        self.operator_feedback.append(feedback)

    def calculate_metrics(self) -> Dict:
        """Calculate pilot performance metrics"""

        if not self.inspections:
            return {"error": "No inspection data"}

        total_inspections = len(self.inspections)

        # Count inspections with ground truth
        with_gt = [i for i in self.inspections if i['ground_truth_defects'] is not None]

        # Calculate accuracy
        if with_gt:
            correct = sum(
                1 for i in with_gt
                if i['defects_detected'] == i['ground_truth_defects']
            )
            accuracy = correct / len(with_gt)
        else:
            accuracy = None

        # Calculate precision and recall (for defects)
        true_positives = sum(
            1 for i in with_gt
            if i['defects_detected'] > 0 and i['ground_truth_defects'] > 0
        )
        false_positives_count = len(self.false_positives)
        false_negatives_count = len(self.false_negatives)

        precision = (
            true_positives / (true_positives + false_positives_count)
            if (true_positives + false_positives_count) > 0 else 0
        )

        recall = (
            true_positives / (true_positives + false_negatives_count)
            if (true_positives + false_negatives_count) > 0 else 0
        )

        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0 else 0
        )

        # Calculate detection time stats
        detection_times = [i['detection_time_ms'] for i in self.inspections]
        avg_detection_time = sum(detection_times) / len(detection_times)

        # Operator agreement rate
        operator_agreements = [
            i for i in self.inspections
            if i['operator_agrees'] is not None
        ]
        if operator_agreements:
            agreement_rate = (
                sum(1 for i in operator_agreements if i['operator_agrees']) /
                len(operator_agreements)
            )
        else:
            agreement_rate = None

        # System uptime
        elapsed = (datetime.now() - self.session_start).total_seconds()
        uptime_hours = elapsed / 3600
        throughput = total_inspections / uptime_hours if uptime_hours > 0 else 0

        metrics = {
            "session_id": self.session_id,
            "session_duration_hours": uptime_hours,
            "total_inspections": total_inspections,
            "inspections_with_ground_truth": len(with_gt),
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "false_positives": false_positives_count,
            "false_negatives": false_negatives_count,
            "avg_detection_time_ms": avg_detection_time,
            "throughput_per_hour": throughput,
            "operator_agreement_rate": agreement_rate,
            "total_detections": len(self.detections)
        }

        return metrics

    def generate_report(self) -> Dict:
        """Generate comprehensive pilot report"""

        logger.info("Generating pilot report...")

        # Calculate metrics
        metrics = self.calculate_metrics()

        # Analyze detections by type
        detections_by_type = defaultdict(int)
        for detection in self.detections:
            detections_by_type[detection['defect_type']] += 1

        # Analyze operator feedback
        if self.operator_feedback:
            avg_rating = sum(f['rating'] for f in self.operator_feedback) / len(self.operator_feedback)
            all_issues = []
            for f in self.operator_feedback:
                all_issues.extend(f['issues'])
            issue_counts = defaultdict(int)
            for issue in all_issues:
                issue_counts[issue] += 1
        else:
            avg_rating = None
            issue_counts = {}

        # Build report
        report = {
            "report_date": datetime.now().isoformat(),
            "session_info": {
                "session_id": self.session_id,
                "start_time": self.session_start.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_hours": metrics['session_duration_hours']
            },
            "performance_metrics": metrics,
            "detections_by_type": dict(detections_by_type),
            "operator_feedback_summary": {
                "total_feedback": len(self.operator_feedback),
                "average_rating": avg_rating,
                "common_issues": dict(issue_counts)
            },
            "false_positives": self.false_positives[:10],  # Sample
            "false_negatives": self.false_negatives[:10],  # Sample
        }

        # Save report
        report_path = self.output_dir / f"pilot_report_{self.session_id}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Report saved: {report_path}")

        # Print summary
        self._print_summary(report)

        return report

    def _print_summary(self, report: Dict):
        """Print report summary"""
        metrics = report['performance_metrics']

        print("\n" + "="*70)
        print("PILOT TESTING REPORT")
        print("="*70)
        print(f"\nSession: {report['session_info']['session_id']}")
        print(f"Duration: {metrics['session_duration_hours']:.1f} hours")
        print(f"\nPERFORMANCE METRICS:")
        print(f"  Total Inspections: {metrics['total_inspections']}")
        print(f"  Throughput: {metrics['throughput_per_hour']:.1f} parts/hour")
        print(f"  Avg Detection Time: {metrics['avg_detection_time_ms']:.2f}ms")

        if metrics['accuracy'] is not None:
            print(f"\nACCURACY METRICS:")
            print(f"  Accuracy: {metrics['accuracy']*100:.1f}%")
            print(f"  Precision: {metrics['precision']*100:.1f}%")
            print(f"  Recall: {metrics['recall']*100:.1f}%")
            print(f"  F1 Score: {metrics['f1_score']:.3f}")
            print(f"  False Positives: {metrics['false_positives']}")
            print(f"  False Negatives: {metrics['false_negatives']}")

        if metrics['operator_agreement_rate'] is not None:
            print(f"\nOPERATOR FEEDBACK:")
            print(f"  Agreement Rate: {metrics['operator_agreement_rate']*100:.1f}%")
            if report['operator_feedback_summary']['average_rating']:
                print(f"  Average Rating: {report['operator_feedback_summary']['average_rating']:.1f}/5")

        print("\nDETECTIONS BY TYPE:")
        for defect_type, count in report['detections_by_type'].items():
            print(f"  {defect_type}: {count}")

        print("="*70)

    def export_to_csv(self):
        """Export data to CSV files"""

        # Export inspections
        if self.inspections:
            df_inspections = pd.DataFrame(self.inspections)
            csv_path = self.output_dir / f"inspections_{self.session_id}.csv"
            df_inspections.to_csv(csv_path, index=False)
            logger.info(f"Exported inspections to {csv_path}")

        # Export detections
        if self.detections:
            df_detections = pd.DataFrame(self.detections)
            csv_path = self.output_dir / f"detections_{self.session_id}.csv"
            df_detections.to_csv(csv_path, index=False)
            logger.info(f"Exported detections to {csv_path}")

        # Export operator feedback
        if self.operator_feedback:
            df_feedback = pd.DataFrame(self.operator_feedback)
            csv_path = self.output_dir / f"feedback_{self.session_id}.csv"
            df_feedback.to_csv(csv_path, index=False)
            logger.info(f"Exported feedback to {csv_path}")

    def calculate_roi(
        self,
        labor_cost_per_hour: float,
        scrap_cost_per_defect: float,
        implementation_cost: float
    ) -> Dict:
        """
        Calculate ROI for pilot

        Args:
            labor_cost_per_hour: Cost of manual inspection labor
            scrap_cost_per_defect: Cost per escaped defect
            implementation_cost: Total implementation cost
        """
        metrics = self.calculate_metrics()

        # Labor savings (assuming AI replaces some manual inspection)
        hours_saved_per_week = metrics['session_duration_hours'] * 0.5  # Assume 50% time savings
        labor_savings_per_week = hours_saved_per_week * labor_cost_per_hour

        # Scrap reduction (escaped defects prevented)
        defects_prevented = metrics['false_negatives']  # These would have escaped
        scrap_savings_per_week = defects_prevented * scrap_cost_per_defect

        # Total weekly savings
        total_weekly_savings = labor_savings_per_week + scrap_savings_per_week

        # Annual projections
        annual_savings = total_weekly_savings * 52

        # ROI calculation
        roi_percentage = ((annual_savings - implementation_cost) / implementation_cost) * 100
        payback_months = implementation_cost / (total_weekly_savings * 4.33)  # 4.33 weeks per month

        roi_report = {
            "costs": {
                "implementation_cost": implementation_cost
            },
            "savings": {
                "labor_savings_per_week": labor_savings_per_week,
                "scrap_savings_per_week": scrap_savings_per_week,
                "total_weekly_savings": total_weekly_savings,
                "annual_savings": annual_savings
            },
            "roi": {
                "roi_percentage": roi_percentage,
                "payback_months": payback_months,
                "net_annual_benefit": annual_savings - implementation_cost
            }
        }

        print("\n" + "="*70)
        print("ROI ANALYSIS")
        print("="*70)
        print(f"\nImplementation Cost: ${implementation_cost:,.2f}")
        print(f"\nWEEKLY SAVINGS:")
        print(f"  Labor: ${labor_savings_per_week:,.2f}")
        print(f"  Scrap Reduction: ${scrap_savings_per_week:,.2f}")
        print(f"  Total: ${total_weekly_savings:,.2f}")
        print(f"\nANNUAL PROJECTION:")
        print(f"  Annual Savings: ${annual_savings:,.2f}")
        print(f"  ROI: {roi_percentage:.1f}%")
        print(f"  Payback Period: {payback_months:.1f} months")
        print("="*70)

        return roi_report


def main():
    """Main execution for testing"""

    # Create monitor
    monitor = PilotMonitor()

    # Simulate some data
    import random

    for i in range(100):
        # Random inspection
        has_defect = random.random() < 0.1  # 10% defect rate
        ai_detected = random.random() < 0.95 if has_defect else random.random() < 0.02

        monitor.log_inspection(
            part_id=f"PART-{i:04d}",
            defects_detected=1 if ai_detected else 0,
            detection_time_ms=random.uniform(30, 60),
            ground_truth_defects=1 if has_defect else 0,
            operator_agrees=ai_detected == has_defect
        )

        if ai_detected:
            monitor.log_detection(
                part_id=f"PART-{i:04d}",
                defect_type=random.choice(["scratch", "dent", "crack"]),
                confidence=random.uniform(0.7, 0.99),
                severity=random.choice(["low", "medium", "high"]),
                is_correct=ai_detected == has_defect
            )

    # Add some operator feedback
    for i in range(5):
        monitor.log_operator_feedback(
            operator_id=f"OP-{i+1}",
            feedback_text="System works well overall",
            rating=random.randint(3, 5),
            issues=random.sample(["false_positives", "slow", "lighting"], k=random.randint(0, 2))
        )

    # Generate report
    report = monitor.generate_report()

    # Export data
    monitor.export_to_csv()

    # Calculate ROI
    monitor.calculate_roi(
        labor_cost_per_hour=30,
        scrap_cost_per_defect=50,
        implementation_cost=5000
    )


if __name__ == "__main__":
    main()
