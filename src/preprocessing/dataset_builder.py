"""
Dataset Builder for SEC Case LLM Evaluation

Combines PDF extraction and ground truth extraction to create
a clean evaluation dataset for LLM prediction.
"""

import json
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from .pdf_extractor import PDFExtractor, get_complaint_url
from .ground_truth_extractor import GroundTruthExtractor


@dataclass
class ProcessedCase:
    """A fully processed case ready for LLM evaluation."""
    case_id: str
    metadata: Dict[str, Any]
    complaint_text: str  # From PDF - what LLM sees
    ground_truth: Dict[str, Any]  # From fullText - for comparison only
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SkippedCase:
    """A case that was skipped due to extraction failure."""
    case_id: str
    title: str
    reason: str
    url: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DatasetBuilder:
    """
    Builds evaluation dataset by:
    1. Extracting complaint text from PDFs
    2. Extracting ground truth from fullText
    3. Splitting into:
       - evaluation_dataset.json (resolved: settled + litigated)
       - prediction_dataset.json (ongoing: no resolution yet)
    """
    
    def __init__(self, pdf_timeout: int = 60):
        self.pdf_extractor = PDFExtractor(timeout=pdf_timeout)
        self.ground_truth_extractor = GroundTruthExtractor()
        
    def process_case(self, case: Dict) -> Tuple[Optional[ProcessedCase], Optional[SkippedCase]]:
        """
        Process a single case.
        
        Args:
            case: Raw case dictionary from sec-cases.json
            
        Returns:
            Tuple of (ProcessedCase if success, SkippedCase if failed)
        """
        case_id = case.get('releaseNumber', 'unknown')
        title = case.get('title', '')
        
        # Step 1: Get complaint URL
        complaint_url = get_complaint_url(case)
        
        if not complaint_url:
            return None, SkippedCase(
                case_id=case_id,
                title=title,
                reason='No complaint URL found in supportingDocuments',
                url=None
            )
        
        # Step 2: Extract PDF text
        result = self.pdf_extractor.extract_from_url(complaint_url)
        
        if not result.success:
            return None, SkippedCase(
                case_id=case_id,
                title=title,
                reason=f'PDF extraction failed: {result.error}',
                url=complaint_url
            )
        
        # Step 3: Clean and validate text
        complaint_text = self.pdf_extractor.clean_text(result.text)
        
        if len(complaint_text) < 500:  # Minimum text length check
            return None, SkippedCase(
                case_id=case_id,
                title=title,
                reason=f'Extracted text too short ({len(complaint_text)} chars) - likely failed extraction',
                url=complaint_url
            )
        
        # Step 4: Extract ground truth from fullText
        full_text = case.get('features', {}).get('fullText', '')
        ground_truth = self.ground_truth_extractor.extract(full_text)
        
        # Step 5: Build processed case
        processed = ProcessedCase(
            case_id=case_id,
            metadata={
                'release_date': case.get('releaseDate', ''),
                'title': title,
                'complaint_url': complaint_url,
                'case_url': case.get('url', ''),
                'court': case.get('features', {}).get('court', ''),
                'respondents': case.get('features', {}).get('respondents', []),
                'charges': case.get('features', {}).get('charges', [])
            },
            complaint_text=complaint_text,
            ground_truth=ground_truth.to_dict()
        )
        
        return processed, None
    
    def build_dataset(
        self,
        input_file: str,
        output_dir: str,
        max_cases: Optional[int] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Build evaluation dataset with all cases.
        
        Args:
            input_file: Path to sec-cases.json
            output_dir: Directory to save output files
            max_cases: Optional limit on number of cases
            verbose: Print progress updates
            
        Returns:
            Summary statistics dict
        """
        # Load input data
        if verbose:
            print(f"Loading data from {input_file}...")
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        cases = data.get('cases', [])
        if max_cases:
            cases = cases[:max_cases]
        
        total = len(cases)
        if verbose:
            print(f"Processing {total} cases...")
        
        # Process all cases
        processed_cases: List[ProcessedCase] = []
        skipped_cases: List[SkippedCase] = []
        
        for i, case in enumerate(cases):
            if verbose and (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{total} ({len(processed_cases)} successful, {len(skipped_cases)} skipped)")
            
            processed, skipped = self.process_case(case)
            
            if processed:
                processed_cases.append(processed)
            if skipped:
                skipped_cases.append(skipped)
        
        # Split into resolved (for evaluation) and ongoing (for prediction)
        resolved_cases = [c for c in processed_cases 
                         if c.ground_truth.get('resolution_type') in ('settled', 'litigated')]
        ongoing_cases = [c for c in processed_cases 
                        if c.ground_truth.get('resolution_type') == 'ongoing']
        
        if verbose:
            print(f"\nExtraction complete:")
            print(f"  Successful: {len(processed_cases)}")
            print(f"    - Resolved (for evaluation): {len(resolved_cases)}")
            print(f"    - Ongoing (for prediction): {len(ongoing_cases)}")
            print(f"  Skipped: {len(skipped_cases)}")
        
        # Calculate statistics for resolved cases
        stats = self._calculate_stats(resolved_cases)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Save evaluation dataset (resolved cases only - settled/litigated)
        evaluation_dataset = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'total_processed': total,
                'resolved_count': len(resolved_cases),
                'ongoing_count': len(ongoing_cases),
                'skipped': len(skipped_cases),
                'description': 'Resolved cases only (settled/litigated) for LLM evaluation'
            },
            'statistics': stats,
            'cases': [c.to_dict() for c in resolved_cases]
        }
        
        with open(os.path.join(output_dir, 'evaluation_dataset.json'), 'w') as f:
            json.dump(evaluation_dataset, f, indent=2)
        
        # Save prediction dataset (ongoing cases - no ground truth scoring)
        prediction_dataset = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'count': len(ongoing_cases),
                'description': 'Ongoing cases for LLM prediction (no scoring - outcomes unknown)'
            },
            'cases': [c.to_dict() for c in ongoing_cases]
        }
        
        with open(os.path.join(output_dir, 'prediction_dataset.json'), 'w') as f:
            json.dump(prediction_dataset, f, indent=2)
        
        # Save skipped cases log
        skipped_data = {
            'metadata': {
                'total_skipped': len(skipped_cases),
                'created_at': datetime.now().isoformat()
            },
            'cases': [s.to_dict() for s in skipped_cases]
        }
        
        with open(os.path.join(output_dir, 'skipped_cases.json'), 'w') as f:
            json.dump(skipped_data, f, indent=2)
        
        if verbose:
            print(f"\nFiles saved to {output_dir}:")
            print(f"  - evaluation_dataset.json ({len(resolved_cases)} resolved cases)")
            print(f"  - prediction_dataset.json ({len(ongoing_cases)} ongoing cases)")
            print(f"  - skipped_cases.json ({len(skipped_cases)} cases)")
        
        return {
            'total_processed': total,
            'resolved': len(resolved_cases),
            'ongoing': len(ongoing_cases),
            'skipped': len(skipped_cases),
            'statistics': stats
        }
    
    def _calculate_stats(self, cases: List[ProcessedCase]) -> Dict[str, Any]:
        """Calculate statistics about ground truth distribution."""
        if not cases:
            return {}
        
        resolution_counts = {}
        disgorgement_count = 0
        penalty_count = 0
        interest_count = 0
        injunction_count = 0
        officer_bar_count = 0
        conduct_restriction_count = 0
        
        for case in cases:
            gt = case.ground_truth
            
            # Resolution type counts
            res_type = gt.get('resolution_type', 'unknown')
            resolution_counts[res_type] = resolution_counts.get(res_type, 0) + 1
            
            # Monetary amount availability
            if gt.get('disgorgement_amount') is not None:
                disgorgement_count += 1
            if gt.get('penalty_amount') is not None:
                penalty_count += 1
            if gt.get('prejudgment_interest') is not None:
                interest_count += 1
            
            # Boolean flags
            if gt.get('has_injunction'):
                injunction_count += 1
            if gt.get('has_officer_director_bar'):
                officer_bar_count += 1
            if gt.get('has_conduct_restriction'):
                conduct_restriction_count += 1
        
        total = len(cases)
        
        return {
            'resolution_type_distribution': resolution_counts,
            'monetary_availability': {
                'disgorgement': {
                    'count': disgorgement_count,
                    'percentage': round(100 * disgorgement_count / total, 1)
                },
                'penalty': {
                    'count': penalty_count,
                    'percentage': round(100 * penalty_count / total, 1)
                },
                'prejudgment_interest': {
                    'count': interest_count,
                    'percentage': round(100 * interest_count / total, 1)
                }
            },
            'remedial_measures': {
                'has_injunction': {
                    'count': injunction_count,
                    'percentage': round(100 * injunction_count / total, 1)
                },
                'has_officer_director_bar': {
                    'count': officer_bar_count,
                    'percentage': round(100 * officer_bar_count / total, 1)
                },
                'has_conduct_restriction': {
                    'count': conduct_restriction_count,
                    'percentage': round(100 * conduct_restriction_count / total, 1)
                }
            }
        }


def build_evaluation_dataset(
    input_file: str,
    output_dir: str,
    max_cases: Optional[int] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to build the evaluation dataset.
    
    Args:
        input_file: Path to sec-cases.json
        output_dir: Directory to save output files
        max_cases: Optional limit on number of cases
        verbose: Print progress
        
    Returns:
        Summary statistics dict
    """
    builder = DatasetBuilder()
    return builder.build_dataset(
        input_file=input_file,
        output_dir=output_dir,
        max_cases=max_cases,
        verbose=verbose
    )


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Build SEC case evaluation dataset')
    parser.add_argument('--input', '-i', default='sec-cases.json', help='Input JSON file')
    parser.add_argument('--output', '-o', default='data/processed', help='Output directory')
    parser.add_argument('--max', '-m', type=int, default=None, help='Max cases to process')
    
    args = parser.parse_args()
    
    result = build_evaluation_dataset(
        input_file=args.input,
        output_dir=args.output,
        max_cases=args.max
    )
    
    print("\n" + "=" * 50)
    print("Dataset build complete!")
    print(f"Statistics: {json.dumps(result, indent=2)}")
