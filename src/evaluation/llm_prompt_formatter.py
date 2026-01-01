"""
LLM Prompt Formatter for SEC Case Evaluation

Creates prompts for LLMs to predict SEC case outcomes
based on complaint text.
"""

from typing import Dict, Any

# Standard prompt template
PROMPT_TEMPLATE = """You are a legal analyst evaluating SEC enforcement cases.

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


# Shorter prompt for models with limited context
SHORT_PROMPT_TEMPLATE = """Analyze this SEC complaint and predict the case outcome.

COMPLAINT:
{complaint_text}

Predict in JSON format:
- resolution_type: "settled" (defendant agrees) or "litigated" (court decides)
- disgorgement_amount: number or null
- penalty_amount: number or null  
- prejudgment_interest: number or null
- has_injunction: true/false
- has_officer_director_bar: true/false
- has_conduct_restriction: true/false
- reasoning: brief explanation

Respond with JSON only."""


def format_prompt(
    complaint_text: str,
    short_format: bool = False,
    max_text_length: int = None
) -> str:
    """
    Format a prompt for LLM evaluation.
    
    Args:
        complaint_text: The complaint text extracted from PDF
        short_format: Use shorter prompt template
        max_text_length: Truncate complaint text if longer
        
    Returns:
        Formatted prompt string
    """
    text = complaint_text
    
    if max_text_length and len(text) > max_text_length:
        # Truncate with indicator
        text = text[:max_text_length] + "\n\n[...TRUNCATED...]"
    
    template = SHORT_PROMPT_TEMPLATE if short_format else PROMPT_TEMPLATE
    
    return template.format(complaint_text=text)


def format_case_for_evaluation(case: Dict[str, Any], short_format: bool = False) -> Dict[str, Any]:
    """
    Format a case from the evaluation dataset for LLM evaluation.
    
    Args:
        case: Case dictionary with complaint_text and ground_truth
        short_format: Use shorter prompt template
        
    Returns:
        Dictionary with case_id, prompt, and ground_truth
    """
    return {
        'case_id': case['case_id'],
        'prompt': format_prompt(case['complaint_text'], short_format=short_format),
        'ground_truth': case['ground_truth'],
        'metadata': case.get('metadata', {})
    }


def create_batch_prompts(
    cases: list,
    short_format: bool = False,
    max_text_length: int = None
) -> list:
    """
    Create prompts for a batch of cases.
    
    Args:
        cases: List of case dictionaries
        short_format: Use shorter prompt template
        max_text_length: Truncate complaint text if longer
        
    Returns:
        List of formatted evaluation items
    """
    results = []
    
    for case in cases:
        text = case['complaint_text']
        
        if max_text_length and len(text) > max_text_length:
            text = text[:max_text_length] + "\n\n[...TRUNCATED...]"
        
        template = SHORT_PROMPT_TEMPLATE if short_format else PROMPT_TEMPLATE
        
        results.append({
            'case_id': case['case_id'],
            'prompt': template.format(complaint_text=text),
            'ground_truth': case['ground_truth'],
            'metadata': case.get('metadata', {})
        })
    
    return results


if __name__ == '__main__':
    # Example usage
    sample_case = {
        'case_id': 'LR-26445',
        'complaint_text': 'This is a sample complaint about securities fraud...',
        'ground_truth': {
            'resolution_type': 'settled',  # Binary: settled or litigated
            'disgorgement_amount': 373885.0,
            'penalty_amount': 112165.0,
            'prejudgment_interest': 22629.34,
            'has_injunction': True,
            'has_officer_director_bar': False,
            'has_conduct_restriction': True
        }
    }
    
    formatted = format_case_for_evaluation(sample_case)
    print("Sample formatted prompt:")
    print("=" * 60)
    print(formatted['prompt'][:1000])
    print("..." if len(formatted['prompt']) > 1000 else "")
