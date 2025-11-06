"""
AI Reflection Agent for continuous system improvement
"""

from typing import List, Dict, Optional, Any
import json
from datetime import datetime
from loguru import logger

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from ..config import settings


class ReflectionAgent:
    """
    AI agent that reflects on system performance and suggests improvements
    Uses advanced language models to analyze patterns and recommend optimizations
    """

    def __init__(
        self,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        provider: str = "openai"
    ):
        """
        Initialize reflection agent

        Args:
            model: Model name to use
            api_key: API key for the provider
            provider: AI provider ('openai' or 'anthropic')
        """
        self.model = model or settings.reflection.model
        self.provider = provider
        self.api_key = api_key or (
            settings.reflection.openai_api_key if provider == "openai"
            else settings.reflection.anthropic_api_key
        )

        # Initialize client
        if provider == "openai":
            if OpenAI is None:
                raise ImportError("openai package not installed")
            self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        elif provider == "anthropic":
            if Anthropic is None:
                raise ImportError("anthropic package not installed")
            self.client = Anthropic(api_key=self.api_key) if self.api_key else None
        else:
            raise ValueError(f"Unknown provider: {provider}")

        # Reflection history
        self.reflection_history: List[Dict] = []

        logger.info(f"Reflection agent initialized with {provider}/{model}")

    def reflect_on_performance(
        self,
        performance_metrics: Dict,
        recent_detections: List[Dict],
        false_positives: List[Dict],
        missed_defects: List[Dict]
    ) -> Dict[str, Any]:
        """
        Reflect on system performance and generate insights

        Args:
            performance_metrics: Current performance metrics
            recent_detections: Recent detection results
            false_positives: List of false positive cases
            missed_defects: List of missed defect cases

        Returns:
            Dictionary with reflection insights and recommendations
        """
        if not self.client:
            logger.warning("Reflection agent not configured (missing API key)")
            return {"error": "Reflection agent not configured"}

        # Prepare analysis prompt
        prompt = self._create_reflection_prompt(
            performance_metrics,
            recent_detections,
            false_positives,
            missed_defects
        )

        # Get reflection from AI
        reflection = self._query_ai(prompt)

        # Parse and structure the reflection
        result = {
            "timestamp": datetime.now().isoformat(),
            "raw_reflection": reflection,
            "recommendations": self._extract_recommendations(reflection),
            "insights": self._extract_insights(reflection),
            "action_items": self._extract_action_items(reflection)
        }

        # Store in history
        self.reflection_history.append(result)

        logger.info("Performance reflection completed")
        return result

    def _create_reflection_prompt(
        self,
        metrics: Dict,
        detections: List[Dict],
        false_positives: List[Dict],
        missed_defects: List[Dict]
    ) -> str:
        """Create detailed prompt for reflection"""

        prompt = f"""You are an AI quality assurance expert analyzing a manufacturing defect detection system.
Analyze the following performance data and provide insights for improvement.

CURRENT PERFORMANCE METRICS:
{json.dumps(metrics, indent=2)}

RECENT DETECTIONS SAMPLE:
{json.dumps(detections[:10], indent=2)}

FALSE POSITIVES (Cases where system incorrectly flagged defects):
{json.dumps(false_positives[:5], indent=2)}

MISSED DEFECTS (Cases where system failed to detect actual defects):
{json.dumps(missed_defects[:5], indent=2)}

Please provide a comprehensive analysis covering:

1. PATTERN ANALYSIS:
   - What patterns do you see in false positives?
   - What patterns do you see in missed defects?
   - Are there specific defect types that are problematic?
   - Are there environmental factors (lighting, angles, etc.) affecting performance?

2. ROOT CAUSE ANALYSIS:
   - What are the likely root causes of detection failures?
   - Are there systematic issues vs random errors?
   - Is the model confidence threshold appropriate?

3. IMPROVEMENT RECOMMENDATIONS:
   - Specific threshold adjustments needed
   - Additional training data requirements (what types of images/scenarios)
   - Preprocessing improvements needed
   - Model architecture considerations

4. PRIORITY ACTION ITEMS:
   - List 3-5 concrete actions ranked by impact and feasibility
   - Each action should include: what to do, why, and expected impact

5. RETRAINING STRATEGY:
   - Should the model be retrained?
   - What data should be prioritized for retraining?
   - Recommended augmentation strategies

Format your response as a structured analysis with clear sections.
"""

        return prompt

    def _query_ai(self, prompt: str) -> str:
        """Query AI provider for reflection"""

        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert AI system analyzing manufacturing quality control performance. Provide detailed, actionable insights."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=settings.reflection.temperature,
                    max_tokens=2000
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=settings.reflection.temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                return response.content[0].text

        except Exception as e:
            logger.error(f"Error querying AI: {e}")
            return f"Error during reflection: {str(e)}"

    def _extract_recommendations(self, reflection: str) -> List[str]:
        """Extract specific recommendations from reflection text"""
        recommendations = []

        # Simple extraction - look for numbered lists or bullet points
        lines = reflection.split('\n')
        in_recommendations = False

        for line in lines:
            line = line.strip()

            if 'recommendation' in line.lower() or 'improve' in line.lower():
                in_recommendations = True

            if in_recommendations and (
                line.startswith('-') or
                line.startswith('*') or
                (len(line) > 0 and line[0].isdigit())
            ):
                recommendations.append(line.lstrip('-*0123456789. '))

        return recommendations[:10]  # Top 10 recommendations

    def _extract_insights(self, reflection: str) -> List[str]:
        """Extract key insights from reflection"""
        insights = []

        # Look for insight-related sections
        lines = reflection.split('\n')

        for line in lines:
            line = line.strip()

            if any(keyword in line.lower() for keyword in ['pattern', 'trend', 'issue', 'problem', 'finding']):
                if len(line) > 20:  # Filter out section headers
                    insights.append(line)

        return insights[:10]

    def _extract_action_items(self, reflection: str) -> List[Dict]:
        """Extract prioritized action items"""
        action_items = []

        # Look for action items section
        lines = reflection.split('\n')
        in_actions = False

        for line in lines:
            line = line.strip()

            if 'action' in line.lower() or 'priority' in line.lower():
                in_actions = True

            if in_actions and (line.startswith('-') or line.startswith('*') or
                              (len(line) > 0 and line[0].isdigit())):
                action_items.append({
                    "action": line.lstrip('-*0123456789. '),
                    "priority": "high" if len(action_items) < 3 else "medium",
                    "status": "pending"
                })

        return action_items[:5]  # Top 5 action items

    def analyze_model_weaknesses(
        self,
        confusion_matrix: Dict,
        misclassifications: List[Dict]
    ) -> Dict:
        """
        Analyze specific model weaknesses

        Args:
            confusion_matrix: Model confusion matrix
            misclassifications: List of misclassification cases

        Returns:
            Analysis of model weaknesses
        """
        if not self.client:
            return {"error": "Reflection agent not configured"}

        prompt = f"""Analyze these model weaknesses and suggest targeted improvements:

CONFUSION MATRIX:
{json.dumps(confusion_matrix, indent=2)}

MISCLASSIFICATION EXAMPLES:
{json.dumps(misclassifications[:10], indent=2)}

Identify:
1. Which defect types are most commonly confused with each other?
2. What features might help distinguish these similar defect types?
3. Specific data augmentation strategies to address these confusions
4. Recommended changes to training strategy
"""

        analysis = self._query_ai(prompt)

        return {
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "recommendations": self._extract_recommendations(analysis)
        }

    def suggest_threshold_adjustments(
        self,
        current_threshold: float,
        precision: float,
        recall: float,
        target_precision: float = 0.95,
        target_recall: float = 0.90
    ) -> Dict:
        """
        Suggest optimal threshold adjustments

        Args:
            current_threshold: Current confidence threshold
            precision: Current precision
            recall: Current recall
            target_precision: Target precision
            target_recall: Target recall

        Returns:
            Threshold adjustment recommendations
        """
        if not self.client:
            return {"error": "Reflection agent not configured"}

        prompt = f"""As a quality control expert, suggest optimal confidence threshold adjustments:

CURRENT STATE:
- Confidence Threshold: {current_threshold}
- Precision: {precision:.3f}
- Recall: {recall:.3f}

TARGETS:
- Target Precision: {target_precision}
- Target Recall: {target_recall}

Provide:
1. Recommended new threshold value
2. Expected impact on precision and recall
3. Trade-offs and considerations
4. Alternative strategies if threshold adjustment alone is insufficient
"""

        suggestion = self._query_ai(prompt)

        return {
            "timestamp": datetime.now().isoformat(),
            "current_threshold": current_threshold,
            "suggestion": suggestion,
            "recommendations": self._extract_recommendations(suggestion)
        }

    def generate_retraining_plan(
        self,
        current_performance: Dict,
        available_data: Dict,
        business_priorities: List[str]
    ) -> Dict:
        """
        Generate comprehensive retraining plan

        Args:
            current_performance: Current model performance
            available_data: Available training data statistics
            business_priorities: List of business priorities

        Returns:
            Detailed retraining plan
        """
        if not self.client:
            return {"error": "Reflection agent not configured"}

        prompt = f"""Create a comprehensive model retraining plan:

CURRENT PERFORMANCE:
{json.dumps(current_performance, indent=2)}

AVAILABLE DATA:
{json.dumps(available_data, indent=2)}

BUSINESS PRIORITIES:
{json.dumps(business_priorities, indent=2)}

Provide a detailed retraining plan including:
1. Whether retraining is recommended (yes/no and why)
2. Data collection priorities
3. Recommended data augmentation strategies
4. Training hyperparameters to adjust
5. Validation strategy
6. Rollback plan if new model underperforms
7. Timeline and resource estimates
"""

        plan = self._query_ai(prompt)

        return {
            "timestamp": datetime.now().isoformat(),
            "plan": plan,
            "action_items": self._extract_action_items(plan)
        }

    def get_reflection_summary(self, last_n: int = 5) -> Dict:
        """
        Get summary of recent reflections

        Args:
            last_n: Number of recent reflections to summarize

        Returns:
            Summary of recent reflections
        """
        recent = self.reflection_history[-last_n:]

        summary = {
            "total_reflections": len(self.reflection_history),
            "recent_reflections": len(recent),
            "common_recommendations": self._find_common_themes(recent),
            "pending_actions": sum(
                len(r.get("action_items", []))
                for r in recent
            )
        }

        return summary

    def _find_common_themes(self, reflections: List[Dict]) -> List[str]:
        """Find common themes across multiple reflections"""
        all_recommendations = []

        for reflection in reflections:
            all_recommendations.extend(reflection.get("recommendations", []))

        # Simple frequency analysis (could be more sophisticated)
        theme_counts = {}
        for rec in all_recommendations:
            # Extract key themes (simple word matching)
            for word in ['threshold', 'lighting', 'training', 'data', 'angle', 'preprocessing']:
                if word in rec.lower():
                    theme_counts[word] = theme_counts.get(word, 0) + 1

        # Return top themes
        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, count in sorted_themes[:5]]
