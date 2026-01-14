"""
Score Calculator for SEC Case LLM Evaluation

Compares LLM predictions to ground truth and calculates accuracy scores.
Uses 10% tolerance for monetary amounts.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import json


@dataclass
class PredictionResult:
    """Result of comparing a single prediction to ground truth."""
    case_id: str
    
    # Individual question results (True = correct, False = incorrect, None = skipped)
    resolution_type_correct: Optional[bool] = None
    disgorgement_correct: Optional[bool] = None
    penalty_correct: Optional[bool] = None
    interest_correct: Optional[bool] = None
    injunction_correct: Optional[bool] = None
    officer_bar_correct: Optional[bool] = None
    conduct_restriction_correct: Optional[bool] = None
    
    # Actual values for reference
    predicted: Dict[str, Any] = field(default_factory=dict)
    ground_truth: Dict[str, Any] = field(default_factory=dict)
    
    # Error details for incorrect predictions
    errors: List[str] = field(default_factory=list)


@dataclass
class ModelScore:
    """Aggregate scores for a model."""
    model_name: str
    
    # Individual accuracies (0-100%)
    resolution_type_accuracy: float = 0.0
    disgorgement_accuracy: float = 0.0
    penalty_accuracy: float = 0.0
    interest_accuracy: float = 0.0
    injunction_accuracy: float = 0.0
    officer_bar_accuracy: float = 0.0
    conduct_restriction_accuracy: float = 0.0
    
    # Combined monetary accuracy (average of disgorgement, penalty, interest)
    monetary_accuracy: float = 0.0
    
    # Overall score (simple average)
    overall_score: float = 0.0
    
    # Counts for transparency
    total_cases: int = 0
    resolution_scorable: int = 0
    disgorgement_scorable: int = 0
    penalty_scorable: int = 0
    interest_scorable: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_name': self.model_name,
            'overall_score': round(self.overall_score, 2),
            'individual_scores': {
                'resolution_type': round(self.resolution_type_accuracy, 2),
                'disgorgement': round(self.disgorgement_accuracy, 2),
                'penalty': round(self.penalty_accuracy, 2),
                'prejudgment_interest': round(self.interest_accuracy, 2),
                'monetary_average': round(self.monetary_accuracy, 2),
                'has_injunction': round(self.injunction_accuracy, 2),
                'has_officer_director_bar': round(self.officer_bar_accuracy, 2),
                'has_conduct_restriction': round(self.conduct_restriction_accuracy, 2)
            },
            'scorable_counts': {
                'total_cases': self.total_cases,
                'resolution_type': self.resolution_scorable,
                'disgorgement': self.disgorgement_scorable,
                'penalty': self.penalty_scorable,
                'interest': self.interest_scorable
            }
        }


class ScoreCalculator:
    """
    Calculates accuracy scores comparing LLM predictions to ground truth.
    
    Scoring Rules:
    - Resolution Type: Exact match required
    - Monetary Amounts: Within 10% of actual required (or exact match for $0)
    - Boolean Flags: Exact match required
    
    Cases with null ground truth for a question are skipped for that question.
    """
    
    TOLERANCE = 0.10  # 10% tolerance for monetary amounts
    
    def __init__(self, tolerance: float = 0.10):
        self.tolerance = tolerance
    
    def _normalize_resolution_type(self, value: Any) -> str:
        """Normalize resolution type string for comparison."""
        if value is None:
            return ''
        return str(value).lower().strip().replace(' ', '_').replace('-', '_')
    
    def _normalize_boolean(self, value: Any) -> Optional[bool]:
        """Normalize boolean value for comparison."""
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lower = value.lower().strip()
            if lower in ('yes', 'true', '1'):
                return True
            if lower in ('no', 'false', '0'):
                return False
        return None
    
    def _normalize_monetary(self, value: Any) -> Optional[float]:
        """Normalize monetary value for comparison."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = value.replace('$', '').replace(',', '').strip()
            if cleaned.lower() in ('null', 'none', 'n/a', ''):
                return None
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None
    
    def _check_monetary_within_tolerance(
        self, 
        predicted: Optional[float], 
        actual: Optional[float]
    ) -> Optional[bool]:
        """
        Check if predicted monetary amount is within tolerance of actual.
        
        Returns:
            True if within tolerance, False if not, None if not scorable
        """
        # Skip if actual is null (not scorable)
        if actual is None:
            return None
        
        # If actual is 0, require exact match
        if actual == 0:
            return predicted == 0
        
        # If predicted is null but actual isn't, incorrect
        if predicted is None:
            return False
        
        # Check if within tolerance
        error_ratio = abs(predicted - actual) / actual
        return error_ratio <= self.tolerance
    
    def compare_single(
        self,
        case_id: str,
        predicted: Dict[str, Any],
        ground_truth: Dict[str, Any]
    ) -> PredictionResult:
        """
        Compare a single prediction to ground truth.
        
        Args:
            case_id: Case identifier
            predicted: LLM prediction dictionary
            ground_truth: Ground truth dictionary
            
        Returns:
            PredictionResult with individual question results
        """
        result = PredictionResult(
            case_id=case_id,
            predicted=predicted,
            ground_truth=ground_truth
        )
        
        # 1. Resolution Type (exact match)
        pred_res = self._normalize_resolution_type(predicted.get('resolution_type'))
        actual_res = self._normalize_resolution_type(ground_truth.get('resolution_type'))
        
        if actual_res:
            result.resolution_type_correct = (pred_res == actual_res)
            if not result.resolution_type_correct:
                result.errors.append(f"Resolution type: predicted '{pred_res}', actual '{actual_res}'")
        
        # 2. Disgorgement Amount (10% tolerance)
        pred_disg = self._normalize_monetary(predicted.get('disgorgement_amount'))
        actual_disg = self._normalize_monetary(ground_truth.get('disgorgement_amount'))
        
        result.disgorgement_correct = self._check_monetary_within_tolerance(pred_disg, actual_disg)
        if result.disgorgement_correct is False:
            result.errors.append(f"Disgorgement: predicted ${pred_disg}, actual ${actual_disg}")
        
        # 3. Penalty Amount (10% tolerance)
        pred_pen = self._normalize_monetary(predicted.get('penalty_amount'))
        actual_pen = self._normalize_monetary(ground_truth.get('penalty_amount'))
        
        result.penalty_correct = self._check_monetary_within_tolerance(pred_pen, actual_pen)
        if result.penalty_correct is False:
            result.errors.append(f"Penalty: predicted ${pred_pen}, actual ${actual_pen}")
        
        # 4. Prejudgment Interest (10% tolerance)
        pred_int = self._normalize_monetary(predicted.get('prejudgment_interest'))
        actual_int = self._normalize_monetary(ground_truth.get('prejudgment_interest'))
        
        result.interest_correct = self._check_monetary_within_tolerance(pred_int, actual_int)
        if result.interest_correct is False:
            result.errors.append(f"Interest: predicted ${pred_int}, actual ${actual_int}")
        
        # 5. Has Injunction (exact match)
        pred_inj = self._normalize_boolean(predicted.get('has_injunction'))
        actual_inj = ground_truth.get('has_injunction')
        
        if actual_inj is not None:
            result.injunction_correct = (pred_inj == actual_inj)
            if not result.injunction_correct:
                result.errors.append(f"Injunction: predicted {pred_inj}, actual {actual_inj}")
        
        # 6. Has Officer/Director Bar (exact match)
        pred_bar = self._normalize_boolean(predicted.get('has_officer_director_bar'))
        actual_bar = ground_truth.get('has_officer_director_bar')
        
        if actual_bar is not None:
            result.officer_bar_correct = (pred_bar == actual_bar)
            if not result.officer_bar_correct:
                result.errors.append(f"Officer bar: predicted {pred_bar}, actual {actual_bar}")
        
        # 7. Has Conduct Restriction (exact match)
        pred_cond = self._normalize_boolean(predicted.get('has_conduct_restriction'))
        actual_cond = ground_truth.get('has_conduct_restriction')
        
        if actual_cond is not None:
            result.conduct_restriction_correct = (pred_cond == actual_cond)
            if not result.conduct_restriction_correct:
                result.errors.append(f"Conduct restriction: predicted {pred_cond}, actual {actual_cond}")
        
        return result
    
    def calculate_model_score(
        self,
        model_name: str,
        results: List[PredictionResult]
    ) -> ModelScore:
        """
        Calculate aggregate scores for a model.
        
        Args:
            model_name: Name of the model
            results: List of PredictionResult for all cases
            
        Returns:
            ModelScore with all accuracy metrics
        """
        score = ModelScore(model_name=model_name, total_cases=len(results))
        
        # Count correct predictions for each category
        res_correct = 0
        res_total = 0
        
        disg_correct = 0
        disg_total = 0
        
        pen_correct = 0
        pen_total = 0
        
        int_correct = 0
        int_total = 0
        
        inj_correct = 0
        inj_total = 0
        
        bar_correct = 0
        bar_total = 0
        
        cond_correct = 0
        cond_total = 0
        
        for r in results:
            # Resolution type
            if r.resolution_type_correct is not None:
                res_total += 1
                if r.resolution_type_correct:
                    res_correct += 1
            
            # Disgorgement
            if r.disgorgement_correct is not None:
                disg_total += 1
                if r.disgorgement_correct:
                    disg_correct += 1
            
            # Penalty
            if r.penalty_correct is not None:
                pen_total += 1
                if r.penalty_correct:
                    pen_correct += 1
            
            # Interest
            if r.interest_correct is not None:
                int_total += 1
                if r.interest_correct:
                    int_correct += 1
            
            # Injunction
            if r.injunction_correct is not None:
                inj_total += 1
                if r.injunction_correct:
                    inj_correct += 1
            
            # Officer bar
            if r.officer_bar_correct is not None:
                bar_total += 1
                if r.officer_bar_correct:
                    bar_correct += 1
            
            # Conduct restriction
            if r.conduct_restriction_correct is not None:
                cond_total += 1
                if r.conduct_restriction_correct:
                    cond_correct += 1
        
        # Calculate individual accuracies
        score.resolution_type_accuracy = (100 * res_correct / res_total) if res_total > 0 else 0
        score.disgorgement_accuracy = (100 * disg_correct / disg_total) if disg_total > 0 else 0
        score.penalty_accuracy = (100 * pen_correct / pen_total) if pen_total > 0 else 0
        score.interest_accuracy = (100 * int_correct / int_total) if int_total > 0 else 0
        score.injunction_accuracy = (100 * inj_correct / inj_total) if inj_total > 0 else 0
        score.officer_bar_accuracy = (100 * bar_correct / bar_total) if bar_total > 0 else 0
        score.conduct_restriction_accuracy = (100 * cond_correct / cond_total) if cond_total > 0 else 0
        
        # Store scorable counts
        score.resolution_scorable = res_total
        score.disgorgement_scorable = disg_total
        score.penalty_scorable = pen_total
        score.interest_scorable = int_total
        
        # Calculate monetary average (only for scorable categories)
        monetary_scores = []
        if disg_total > 0:
            monetary_scores.append(score.disgorgement_accuracy)
        if pen_total > 0:
            monetary_scores.append(score.penalty_accuracy)
        if int_total > 0:
            monetary_scores.append(score.interest_accuracy)
        
        score.monetary_accuracy = sum(monetary_scores) / len(monetary_scores) if monetary_scores else 0
        
        # Calculate overall score (simple average of 5 categories)
        # Categories: resolution_type, monetary_avg, injunction, officer_bar, conduct_restriction
        category_scores = []
        
        if res_total > 0:
            category_scores.append(score.resolution_type_accuracy)
        if monetary_scores:
            category_scores.append(score.monetary_accuracy)
        if inj_total > 0:
            category_scores.append(score.injunction_accuracy)
        if bar_total > 0:
            category_scores.append(score.officer_bar_accuracy)
        if cond_total > 0:
            category_scores.append(score.conduct_restriction_accuracy)
        
        score.overall_score = sum(category_scores) / len(category_scores) if category_scores else 0
        
        return score


def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """
    Parse LLM response text into structured prediction dict.
    
    Args:
        response_text: Raw LLM response
        
    Returns:
        Parsed prediction dictionary
    """
    # Try to find JSON in the response
    import re
    
    # Look for JSON block
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try parsing entire response as JSON
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Try finding any JSON object in the response
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, response_text, re.DOTALL)
    
    for match in matches:
        try:
            parsed = json.loads(match)
            if 'resolution_type' in parsed or 'has_injunction' in parsed:
                return parsed
        except json.JSONDecodeError:
            continue
    
    # Return empty dict if parsing fails
    return {}


if __name__ == '__main__':
    # Example usage
    calculator = ScoreCalculator(tolerance=0.10)
    
    # Sample prediction vs ground truth
    predicted = {
        'resolution_type': 'settled_action',
        'disgorgement_amount': 370000,  # Within 10% of 373885
        'penalty_amount': 120000,  # Within 10% of 112165
        'prejudgment_interest': 22000,
        'has_injunction': True,
        'has_officer_director_bar': False,
        'has_conduct_restriction': True
    }
    
    ground_truth = {
        'resolution_type': 'settled_action',
        'disgorgement_amount': 373885.0,
        'penalty_amount': 112165.0,
        'prejudgment_interest': 22629.34,
        'has_injunction': True,
        'has_officer_director_bar': False,
        'has_conduct_restriction': True
    }
    
    result = calculator.compare_single('LR-26445', predicted, ground_truth)
    
    print("Comparison Result:")
    print("=" * 50)
    print(f"Case: {result.case_id}")
    print(f"Resolution Type Correct: {result.resolution_type_correct}")
    print(f"Disgorgement Correct: {result.disgorgement_correct}")
    print(f"Penalty Correct: {result.penalty_correct}")
    print(f"Interest Correct: {result.interest_correct}")
    print(f"Injunction Correct: {result.injunction_correct}")
    print(f"Officer Bar Correct: {result.officer_bar_correct}")
    print(f"Conduct Restriction Correct: {result.conduct_restriction_correct}")
    
    if result.errors:
        print(f"\nErrors:")
        for e in result.errors:
            print(f"  - {e}")
    
    # Test model score calculation
    score = calculator.calculate_model_score('TestModel', [result])
    print(f"\nModel Score: {json.dumps(score.to_dict(), indent=2)}")

