"""
LLM Runner for SEC Case Evaluation

Runs LLM predictions on test cases and collects results.
Supports multiple LLM providers (OpenAI, Anthropic, etc.)
"""

import json
import os
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime

from .llm_prompt_formatter import format_prompt
from .score_calculator import ScoreCalculator, PredictionResult, ModelScore, parse_llm_response

# Full system instruction for LLM providers
SYSTEM_INSTRUCTION = """You are a legal analyst evaluating SEC enforcement cases.

Read the following SEC complaint and predict the likely outcome.

Predict the following outcomes for this case:

1. Resolution Type: Choose one of:
   - settled (defendant will agree to terms - includes consent judgments and settled actions)
   - litigated (case will go to trial/judgment - court makes final decision)

2. Disgorgement Amount: The amount in dollars the defendant must return (ill-gotten gains). Enter a number or null if none expected.

3. Civil Penalty Amount: The civil penalty in dollars. Enter a number or null if none expected.

4. Prejudgment Interest: Interest on disgorgement in dollars. Enter a number or null if none expected.

5. Has Injunction: Will there be injunctive relief? (yes/no)

6. Has Officer/Director Bar: Will the defendant be barred from serving as an officer or director? (yes/no)

7. Has Conduct Restriction: Will there be conduct-based restrictions (e.g., trading restrictions, industry bar)? (yes/no)

Respond in the following JSON format with reasoning. Provide your prediction based solely on the complaint text provided."""

@dataclass
class EvaluationResult:
    """Complete evaluation result for a model."""
    model_name: str
    model_config: Dict[str, Any]
    score: ModelScore
    predictions: List[Dict[str, Any]]
    timestamp: str
    duration_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_name': self.model_name,
            'model_config': self.model_config,
            'score': self.score.to_dict(),
            'timestamp': self.timestamp,
            'duration_seconds': self.duration_seconds,
            'predictions': self.predictions
        }

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a response for the given prompt."""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name/identifier."""
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get the model configuration."""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI API provider (GPT-4, etc.)"""
    
    def __init__(
        self,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000
    ):
        self.model = model
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai library required. Install with: pip install openai")
    
    def generate(self, prompt: str) -> str:
        # Combine system instruction with user prompt for Responses API
        full_input = f"""{SYSTEM_INSTRUCTION}

{prompt}"""
        
        response = self.client.responses.create(
            model=self.model,
            input=full_input,
        )
        return response.output_text
    
    def get_model_name(self) -> str:
        return f"OpenAI/{self.model}"
    
    def get_config(self) -> Dict[str, Any]:
        return {
            'provider': 'openai',
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }

class AnthropicProvider(LLMProvider):
    """Anthropic API provider (Claude, etc.)"""
    
    def __init__(
        self,
        model: str = "claude-3-opus-20240229",
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000
    ):
        self.model = model
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic library required. Install with: pip install anthropic")
    
    def generate(self, prompt: str) -> str:
        response =         response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=SYSTEM_INSTRUCTION,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    
    def get_model_name(self) -> str:
        return f"Anthropic/{self.model}"
    
    def get_config(self) -> Dict[str, Any]:
        return {
            'provider': 'anthropic',
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }

class GoogleProvider(LLMProvider):
    """Google API provider (Gemini, etc.)"""
    
    def __init__(
        self,
        model: str = "gemini-3-flash-preview",
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000
    ):
        self.model = model
        self.api_key = api_key or os.environ.get('GOOGLE_API_KEY')
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except ImportError:
            raise ImportError("google-genai library required. Install with: pip install google-genai")
    
    def generate(self, prompt: str) -> str:
        # Use the same system prompt as OpenAI provider
        system_instruction = """You are a legal analyst evaluating SEC enforcement cases.

Read the following SEC complaint and predict the likely outcome:

---
COMPLAINT:
{complaint_text}
---

Predict the following outcomes for this case:

1. Resolution Type: Choose one of:
   - settled (defendant will agree to terms - includes consent judgments and settled actions)
   - litigated (case will go to trial/judgment - court makes final decision)

2. Disgorgement Amount: The amount in dollars the defendant must return (ill-gotten gains). Enter a number or null if none expected.

3. Civil Penalty Amount: The civil penalty in dollars. Enter a number or null if none expected.

4. Prejudgment Interest: Interest on disgorgement in dollars. Enter a number or null if none expected.

5. Has Injunction: Will there be injunctive relief? (yes/no)

6. Has Officer/Director Bar: Will the defendant be barred from serving as an officer or director? (yes/no)

7. Has Conduct Restriction: Will there be conduct-based restrictions (e.g., trading restrictions, industry bar)? (yes/no)

Respond in the following JSON format:
```json
{{
  "resolution_type": "settled" or "litigated",
  "disgorgement_amount": ...,
  "penalty_amount": ...,
  "prejudgment_interest": ...,
  "has_injunction": true/false,
  "has_officer_director_bar": true/false,
  "has_conduct_restriction": true/false,
  "reasoning": {{
    "resolution_type": "Brief explanation...",
    "monetary": "Brief explanation...",
    "remedial_measures": "Brief explanation..."
  }}
}}
```

Provide your prediction based solely on the complaint text provided."""
        
        # Prepend system instruction to the prompt for Gemini
        # Gemini models can handle system instructions in the content
        full_prompt = f"{system_instruction}\n\n{prompt}"
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=full_prompt
        )
        # Handle response - extract text from content parts
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'candidates') and response.candidates:
            # Extract text from candidates
            text_parts = []
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'text'):
                            text_parts.append(part.text)
            return ''.join(text_parts) if text_parts else str(response)
        else:
            return str(response)
    
    def get_model_name(self) -> str:
        return f"Google/{self.model}"
    
    def get_config(self) -> Dict[str, Any]:
        return {
            'provider': 'google',
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }

class MockProvider(LLMProvider):
    """Mock provider for testing."""
    
    def __init__(self, model_name: str = "MockModel"):
        self.model_name = model_name
    
    def generate(self, prompt: str) -> str:
        # Return a mock prediction for testing
        return json.dumps({
            "resolution_type": "settled_action",
            "disgorgement_amount": 100000,
            "penalty_amount": 50000,
            "prejudgment_interest": 10000,
            "has_injunction": True,
            "has_officer_director_bar": False,
            "has_conduct_restriction": True,
            "reasoning": {
                "resolution_type": "Mock reasoning for testing",
                "monetary": "Mock monetary reasoning",
                "remedial_measures": "Mock remedial reasoning"
            }
        })
    
    def get_model_name(self) -> str:
        return self.model_name
    
    def get_config(self) -> Dict[str, Any]:
        return {'provider': 'mock', 'model': self.model_name}

class LLMRunner:
    """
    Runs LLM evaluation on test cases.
    """
    
    def __init__(
        self,
        provider: LLMProvider,
        short_prompt: bool = False,
        max_text_length: Optional[int] = None,
        retry_count: int = 3,
        retry_delay: float = 1.0
    ):
        self.provider = provider
        self.short_prompt = short_prompt
        self.max_text_length = max_text_length
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.calculator = ScoreCalculator()
    
    def run_single(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run prediction on a single case.
        
        Args:
            case: Case dictionary with complaint_text and ground_truth
            
        Returns:
            Dictionary with prediction results
        """
        case_id = case['case_id']
        complaint_text = case['complaint_text']
        ground_truth = case['ground_truth']
        metadata = case.get('metadata', {})
        
        # Format prompt
        prompt = format_prompt(
            complaint_text,
            short_format=self.short_prompt,
            max_text_length=self.max_text_length
        )
        
        # Generate prediction with retries
        response = None
        error = None
        
        for attempt in range(self.retry_count):
            try:
                response = self.provider.generate(prompt)
                break
            except Exception as e:
                error = str(e)
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
        
        if response is None:
            return {
                'case_id': case_id,
                'success': False,
                'error': error,
                'predicted': {},
                'ground_truth': ground_truth,
                'metadata': metadata,
                'raw_response': None
            }
        
        # Parse response
        predicted = parse_llm_response(response)
        
        # Compare to ground truth
        comparison = self.calculator.compare_single(case_id, predicted, ground_truth)
        
        return {
            'case_id': case_id,
            'success': True,
            'predicted': predicted,
            'ground_truth': ground_truth,
            'metadata': metadata,
            'raw_response': response,
            'comparison': {
                'resolution_type_correct': comparison.resolution_type_correct,
                'disgorgement_correct': comparison.disgorgement_correct,
                'penalty_correct': comparison.penalty_correct,
                'interest_correct': comparison.interest_correct,
                'injunction_correct': comparison.injunction_correct,
                'officer_bar_correct': comparison.officer_bar_correct,
                'conduct_restriction_correct': comparison.conduct_restriction_correct,
                'errors': comparison.errors
            }
        }
    
    def run_evaluation(
        self,
        cases: List[Dict[str, Any]],
        verbose: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> EvaluationResult:
        """
        Run evaluation on all cases.
        
        Args:
            cases: List of case dictionaries
            verbose: Print progress
            progress_callback: Optional callback for progress updates
            
        Returns:
            EvaluationResult with all predictions and scores
        """
        start_time = time.time()
        model_name = self.provider.get_model_name()
        
        if verbose:
            print(f"Running evaluation with {model_name} on {len(cases)} cases...")
        
        predictions = []
        comparison_results = []
        
        for i, case in enumerate(cases):
            if verbose and (i + 1) % 5 == 0:
                print(f"  Progress: {i + 1}/{len(cases)}")
            
            if progress_callback:
                progress_callback(i + 1, len(cases))
            
            result = self.run_single(case)
            predictions.append(result)
            
            if result['success']:
                # Create PredictionResult for score calculation
                comp = result['comparison']
                pr = PredictionResult(
                    case_id=result['case_id'],
                    resolution_type_correct=comp['resolution_type_correct'],
                    disgorgement_correct=comp['disgorgement_correct'],
                    penalty_correct=comp['penalty_correct'],
                    interest_correct=comp['interest_correct'],
                    injunction_correct=comp['injunction_correct'],
                    officer_bar_correct=comp['officer_bar_correct'],
                    conduct_restriction_correct=comp['conduct_restriction_correct'],
                    predicted=result['predicted'],
                    ground_truth=result['ground_truth']
                )
                comparison_results.append(pr)
        
        # Calculate model score
        score = self.calculator.calculate_model_score(model_name, comparison_results)
        
        duration = time.time() - start_time
        
        if verbose:
            print(f"\nEvaluation complete!")
            print(f"  Duration: {duration:.1f} seconds")
            print(f"  Overall Score: {score.overall_score:.1f}%")
        
        return EvaluationResult(
            model_name=model_name,
            model_config=self.provider.get_config(),
            score=score,
            predictions=predictions,
            timestamp=datetime.now().isoformat(),
            duration_seconds=duration
        )

def run_evaluation(
    test_file: str,
    provider: LLMProvider,
    output_file: Optional[str] = None,
    short_prompt: bool = False,
    max_cases: Optional[int] = None,
    verbose: bool = True
) -> EvaluationResult:
    """
    Convenience function to run evaluation from test file.
    
    Args:
        test_file: Path to test.json
        provider: LLM provider instance
        output_file: Optional path to save results
        short_prompt: Use shorter prompt format
        max_cases: Optional limit on cases to evaluate
        verbose: Print progress
        
    Returns:
        EvaluationResult
    """
    # Load test cases
    with open(test_file, 'r') as f:
        data = json.load(f)
    
    cases = data.get('cases', [])
    if max_cases:
        cases = cases[:max_cases]
    
    # Run evaluation
    runner = LLMRunner(provider, short_prompt=short_prompt)
    result = runner.run_evaluation(cases, verbose=verbose)
    
    # Save results if output file specified
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        if verbose:
            print(f"\nResults saved to: {output_file}")
    
    return result

if __name__ == '__main__':
    # Example usage with mock provider
    print("Testing LLM Runner with MockProvider...")
    
    # Create mock test data
    test_cases = [
        {
            'case_id': 'TEST-001',
            'complaint_text': 'Sample complaint about securities fraud...',
            'ground_truth': {
                'resolution_type': 'settled_action',
                'disgorgement_amount': 100000,
                'penalty_amount': 50000,
                'prejudgment_interest': 10000,
                'has_injunction': True,
                'has_officer_director_bar': False,
                'has_conduct_restriction': True
            }
        }
    ]
    
    provider = MockProvider()
    runner = LLMRunner(provider)
    result = runner.run_evaluation(test_cases, verbose=True)
    
    print("\n" + "=" * 60)
    print("Evaluation Result:")
    print(json.dumps(result.to_dict(), indent=2, default=str))

