"""
Customer Feedback Integration System
Integrates customer feedback to improve future production quality
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re
import numpy as np
from loguru import logger


class SentimentAnalyzer:
    """Simple sentiment analysis for customer feedback"""

    def __init__(self):
        # Positive and negative word lists (simplified)
        self.positive_words = {
            'good', 'great', 'excellent', 'perfect', 'quality', 'satisfied',
            'happy', 'pleased', 'amazing', 'wonderful', 'outstanding',
            'reliable', 'durable', 'flawless', 'superior'
        }

        self.negative_words = {
            'bad', 'poor', 'defective', 'broken', 'damaged', 'issue',
            'problem', 'fault', 'disappointed', 'unsatisfied', 'terrible',
            'scratch', 'dent', 'crack', 'fail', 'failure', 'unreliable'
        }

        self.defect_keywords = {
            'scratch': 'scratch',
            'dent': 'dent',
            'crack': 'surface_defect',
            'chip': 'surface_defect',
            'rust': 'contamination',
            'color': 'color_defect',
            'paint': 'color_defect',
            'misaligned': 'assembly_error',
            'loose': 'assembly_error',
            'missing': 'assembly_error',
            'dimension': 'dimensional',
            'size': 'dimensional'
        }

    def analyze(self, text: str) -> Dict:
        """
        Analyze sentiment of text

        Args:
            text: Feedback text

        Returns:
            Sentiment analysis results
        """
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)

        # Count positive and negative words
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)

        # Calculate sentiment score (-1 to 1)
        total = positive_count + negative_count
        if total > 0:
            sentiment_score = (positive_count - negative_count) / total
        else:
            sentiment_score = 0.0

        # Determine sentiment category
        if sentiment_score > 0.3:
            sentiment = "positive"
        elif sentiment_score < -0.3:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Extract mentioned defects
        mentioned_defects = []
        for keyword, defect_type in self.defect_keywords.items():
            if keyword in text_lower:
                mentioned_defects.append(defect_type)

        return {
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "positive_words": positive_count,
            "negative_words": negative_count,
            "mentioned_defects": list(set(mentioned_defects))
        }


class CustomerFeedbackIntegration:
    """
    System for integrating customer feedback into quality improvement process
    """

    def __init__(self):
        """Initialize customer feedback system"""
        self.feedback_records: List[Dict] = []
        self.sentiment_analyzer = SentimentAnalyzer()

        # Feedback categories
        self.defect_feedback: List[Dict] = []
        self.positive_feedback: List[Dict] = []
        self.actionable_feedback: List[Dict] = []

        logger.info("Customer feedback integration initialized")

    def record_feedback(
        self,
        customer_id: str,
        product_id: str,
        feedback_text: str,
        rating: Optional[int] = None,
        feedback_date: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Record customer feedback

        Args:
            customer_id: Customer identifier
            product_id: Product/part identifier
            feedback_text: Feedback text
            rating: Optional rating (1-5)
            feedback_date: Feedback date
            metadata: Additional metadata

        Returns:
            Processed feedback record
        """
        feedback_date = feedback_date or datetime.now()

        # Analyze sentiment
        sentiment_analysis = self.sentiment_analyzer.analyze(feedback_text)

        # Create feedback record
        feedback = {
            "id": f"FB-{int(feedback_date.timestamp() * 1000)}",
            "customer_id": customer_id,
            "product_id": product_id,
            "feedback_text": feedback_text,
            "rating": rating,
            "date": feedback_date.isoformat(),
            "sentiment": sentiment_analysis["sentiment"],
            "sentiment_score": sentiment_analysis["sentiment_score"],
            "mentioned_defects": sentiment_analysis["mentioned_defects"],
            "metadata": metadata or {},
            "processed": True,
            "action_taken": False
        }

        # Store feedback
        self.feedback_records.append(feedback)

        # Categorize
        if sentiment_analysis["sentiment"] == "negative" and sentiment_analysis["mentioned_defects"]:
            self.defect_feedback.append(feedback)

            # Mark as actionable if critical
            if rating and rating <= 2:
                self.actionable_feedback.append(feedback)

        elif sentiment_analysis["sentiment"] == "positive":
            self.positive_feedback.append(feedback)

        logger.info(
            f"Recorded feedback from {customer_id}: "
            f"sentiment={sentiment_analysis['sentiment']}, "
            f"defects={len(sentiment_analysis['mentioned_defects'])}"
        )

        return feedback

    def analyze_feedback_trends(
        self,
        days: int = 30
    ) -> Dict:
        """
        Analyze feedback trends over time

        Args:
            days: Number of days to analyze

        Returns:
            Trend analysis
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        recent_feedback = [
            f for f in self.feedback_records
            if datetime.fromisoformat(f["date"]) > cutoff_date
        ]

        if not recent_feedback:
            return {"message": "No recent feedback to analyze"}

        # Calculate metrics
        total = len(recent_feedback)
        positive = sum(1 for f in recent_feedback if f["sentiment"] == "positive")
        negative = sum(1 for f in recent_feedback if f["sentiment"] == "negative")
        neutral = sum(1 for f in recent_feedback if f["sentiment"] == "neutral")

        # Average sentiment score
        avg_sentiment = np.mean([f["sentiment_score"] for f in recent_feedback])

        # Average rating (if available)
        ratings = [f["rating"] for f in recent_feedback if f["rating"] is not None]
        avg_rating = np.mean(ratings) if ratings else None

        # Most mentioned defects
        all_defects = []
        for f in recent_feedback:
            all_defects.extend(f["mentioned_defects"])

        defect_counts = defaultdict(int)
        for defect in all_defects:
            defect_counts[defect] += 1

        # Sort defects by frequency
        top_defects = sorted(
            defect_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        analysis = {
            "period_days": days,
            "total_feedback": total,
            "sentiment_distribution": {
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "positive_percentage": (positive / total) * 100 if total > 0 else 0
            },
            "average_sentiment_score": avg_sentiment,
            "average_rating": avg_rating,
            "top_mentioned_defects": top_defects[:5],
            "actionable_items": len(self.actionable_feedback)
        }

        return analysis

    def correlate_with_production(
        self,
        production_data: List[Dict]
    ) -> Dict:
        """
        Correlate customer feedback with production data

        Args:
            production_data: List of production records with defect data

        Returns:
            Correlation analysis
        """
        correlations = {}

        # Group feedback by defect type
        feedback_defects = defaultdict(list)
        for feedback in self.defect_feedback:
            for defect in feedback["mentioned_defects"]:
                feedback_defects[defect].append(feedback)

        # Group production data by defect type
        production_defects = defaultdict(list)
        for record in production_data:
            defect_type = record.get("defect_type")
            if defect_type:
                production_defects[defect_type].append(record)

        # Correlate
        for defect_type in set(list(feedback_defects.keys()) + list(production_defects.keys())):
            fb_count = len(feedback_defects.get(defect_type, []))
            prod_count = len(production_defects.get(defect_type, []))

            # Calculate correlation score (simplified)
            if prod_count > 0:
                correlation_score = fb_count / prod_count
            else:
                correlation_score = fb_count  # All customer reports, no production detection

            correlations[defect_type] = {
                "customer_reports": fb_count,
                "production_detections": prod_count,
                "correlation_score": correlation_score,
                "status": "aligned" if correlation_score < 0.5 else "gap"
            }

        return {
            "correlations": correlations,
            "summary": self._summarize_correlations(correlations)
        }

    def _summarize_correlations(self, correlations: Dict) -> Dict:
        """Summarize correlation findings"""

        high_gap_defects = [
            defect for defect, data in correlations.items()
            if data["correlation_score"] > 1.0 and data["customer_reports"] > 5
        ]

        summary = {
            "total_defect_types": len(correlations),
            "high_gap_defects": high_gap_defects,
            "recommendation": ""
        }

        if high_gap_defects:
            summary["recommendation"] = (
                f"ATTENTION: {len(high_gap_defects)} defect types are under-detected in production "
                f"but frequently reported by customers: {', '.join(high_gap_defects)}. "
                f"Consider retraining detection model for these defect types."
            )
        else:
            summary["recommendation"] = "Good alignment between production detection and customer feedback."

        return summary

    def generate_improvement_actions(self) -> List[Dict]:
        """
        Generate improvement actions based on customer feedback

        Returns:
            List of recommended actions
        """
        actions = []

        # Analyze trends
        trends = self.analyze_feedback_trends(days=30)

        # Action 1: Address frequently mentioned defects
        if trends.get("top_mentioned_defects"):
            for defect_type, count in trends["top_mentioned_defects"][:3]:
                if count > 5:
                    actions.append({
                        "priority": "high",
                        "category": "defect_detection",
                        "action": f"Improve detection for {defect_type}",
                        "description": (
                            f"{defect_type} mentioned in {count} customer feedbacks. "
                            f"Retrain model with more examples of this defect type."
                        ),
                        "defect_type": defect_type,
                        "customer_reports": count
                    })

        # Action 2: Address low ratings
        low_rated = [
            f for f in self.actionable_feedback
            if f.get("rating") and f["rating"] <= 2
        ]

        if len(low_rated) > 10:
            actions.append({
                "priority": "critical",
                "category": "quality_crisis",
                "action": "Investigate quality crisis",
                "description": (
                    f"{len(low_rated)} customers gave ratings of 2 or below in the last 30 days. "
                    f"Immediate investigation required."
                )
            })

        # Action 3: Positive reinforcement
        if trends.get("sentiment_distribution", {}).get("positive_percentage", 0) > 80:
            actions.append({
                "priority": "low",
                "category": "positive_reinforcement",
                "action": "Share success with production team",
                "description": (
                    f"{trends['sentiment_distribution']['positive_percentage']:.1f}% "
                    f"positive feedback. Acknowledge and reinforce good practices."
                )
            })

        # Action 4: Address sentiment decline
        if trends.get("average_sentiment_score", 0) < -0.2:
            actions.append({
                "priority": "high",
                "category": "sentiment_decline",
                "action": "Address declining customer satisfaction",
                "description": (
                    f"Average sentiment score is {trends['average_sentiment_score']:.2f}. "
                    f"Review recent process changes and quality metrics."
                )
            })

        logger.info(f"Generated {len(actions)} improvement actions from customer feedback")

        return actions

    def get_actionable_feedback(
        self,
        priority: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get actionable feedback items

        Args:
            priority: Filter by priority (critical, high, medium, low)
            limit: Maximum number of items

        Returns:
            List of actionable feedback
        """
        actionable = [f for f in self.actionable_feedback if not f.get("action_taken")]

        # Sort by rating and sentiment score
        actionable.sort(
            key=lambda x: (x.get("rating", 5), x.get("sentiment_score", 0))
        )

        return actionable[:limit]

    def mark_action_taken(self, feedback_id: str, action_description: str):
        """
        Mark that action was taken on feedback

        Args:
            feedback_id: Feedback ID
            action_description: Description of action taken
        """
        for feedback in self.feedback_records:
            if feedback["id"] == feedback_id:
                feedback["action_taken"] = True
                feedback["action_description"] = action_description
                feedback["action_date"] = datetime.now().isoformat()

                logger.info(f"Marked action taken on feedback {feedback_id}")
                break

    def export_feedback_summary(self) -> Dict:
        """
        Export comprehensive feedback summary

        Returns:
            Summary of all feedback data
        """
        summary = {
            "total_feedback": len(self.feedback_records),
            "defect_feedback": len(self.defect_feedback),
            "positive_feedback": len(self.positive_feedback),
            "actionable_feedback": len(self.actionable_feedback),
            "trends_30_days": self.analyze_feedback_trends(days=30),
            "trends_90_days": self.analyze_feedback_trends(days=90),
            "improvement_actions": self.generate_improvement_actions(),
            "top_actionable_items": self.get_actionable_feedback(limit=5)
        }

        return summary
