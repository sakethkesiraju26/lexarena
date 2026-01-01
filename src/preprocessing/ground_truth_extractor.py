"""
Ground Truth Extractor for SEC Case Outcomes

Extracts resolution types, monetary amounts, and remedial measures from fullText.
This data is used as ground truth for LLM evaluation - never shown to the LLM.
"""

import re
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class GroundTruth:
    """Ground truth outcome data for a case."""
    resolution_type: str
    disgorgement_amount: Optional[float]
    penalty_amount: Optional[float]
    prejudgment_interest: Optional[float]
    has_injunction: bool
    has_officer_director_bar: bool
    has_conduct_restriction: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GroundTruthExtractor:
    """
    Extracts ground truth outcomes from SEC case fullText.
    
    Resolution Type Categories (3 outcomes):
    1. settled - Defendant agreed to terms (settled_action + consent_judgment)
    2. litigated - Court made decision (final_judgment + jury_verdict + dismissed)
    3. ongoing - Case still in progress (filed_charges, no resolution indicators)
    """
    
    # Regex patterns for monetary amounts
    # Matches formats like: $1,234,567.89 or $1.2 million
    MONEY_PATTERN = r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:million|billion)?'
    MONEY_MILLIONS_PATTERN = r'\$\s*([\d,]+(?:\.\d+)?)\s*million'
    MONEY_BILLIONS_PATTERN = r'\$\s*([\d,]+(?:\.\d+)?)\s*billion'
    
    def __init__(self):
        pass
    
    def extract_resolution_type(self, text: str) -> str:
        """
        Extract resolution type into 3 categories.
        
        Categories:
        1. settled - Defendant agreed to terms (settled_action + consent_judgment)
        2. litigated - Court made decision (final_judgment + jury_verdict + dismissed)
        3. ongoing - Case still in progress (no resolution indicators)
        
        Args:
            text: The fullText content from the case
            
        Returns:
            Resolution type string: "settled", "litigated", or "ongoing"
        """
        if not text:
            return "ongoing"
        
        text_lower = text.lower()
        
        # Category 1: SETTLED - defendant agreed to terms
        # Includes: settled_action, consent_judgment
        if "settled action" in text_lower or "filed settled action" in text_lower:
            return "settled"
        if "consent" in text_lower and "judgment" in text_lower:
            return "settled"
        
        # Category 2: LITIGATED - court made the decision
        # Includes: final_judgment, jury_verdict, dismissed
        if "final judgment" in text_lower:
            return "litigated"
        if "jury" in text_lower and "verdict" in text_lower:
            return "litigated"
        if "dismiss" in text_lower or "dismissed with prejudice" in text_lower:
            return "litigated"
        
        # Category 3: ONGOING - no resolution yet
        return "ongoing"
    
    def _parse_money_amount(self, amount_str: str, is_millions: bool = False, is_billions: bool = False) -> float:
        """
        Parse a money amount string to float.
        
        Args:
            amount_str: String like "1,234,567.89" or "1.5"
            is_millions: Whether to multiply by 1,000,000
            is_billions: Whether to multiply by 1,000,000,000
            
        Returns:
            Float amount
        """
        # Remove commas
        clean_str = amount_str.replace(',', '')
        
        try:
            amount = float(clean_str)
            
            if is_billions:
                amount *= 1_000_000_000
            elif is_millions:
                amount *= 1_000_000
                
            return amount
        except ValueError:
            return None
    
    def _extract_amount_after_keyword(self, text: str, keywords: list) -> Optional[float]:
        """
        Extract monetary amount that appears after specific keywords.
        
        Args:
            text: The text to search
            keywords: List of keywords to look for
            
        Returns:
            Float amount or None if not found
        """
        if not text:
            return None
        
        text_lower = text.lower()
        
        for keyword in keywords:
            # Find positions of keyword
            pos = 0
            while True:
                pos = text_lower.find(keyword, pos)
                if pos == -1:
                    break
                
                # Look for money amount in the next 200 characters
                search_text = text[pos:pos + 200]
                
                # Try billions first
                match = re.search(self.MONEY_BILLIONS_PATTERN, search_text, re.IGNORECASE)
                if match:
                    return self._parse_money_amount(match.group(1), is_billions=True)
                
                # Try millions
                match = re.search(self.MONEY_MILLIONS_PATTERN, search_text, re.IGNORECASE)
                if match:
                    return self._parse_money_amount(match.group(1), is_millions=True)
                
                # Try regular amount
                match = re.search(self.MONEY_PATTERN, search_text, re.IGNORECASE)
                if match:
                    return self._parse_money_amount(match.group(1))
                
                pos += len(keyword)
        
        return None
    
    def extract_disgorgement_amount(self, text: str) -> Optional[float]:
        """
        Extract disgorgement amount from text.
        
        Args:
            text: The fullText content
            
        Returns:
            Float amount or None
        """
        return self._extract_amount_after_keyword(
            text, 
            ['disgorgement of', 'disgorgement totaling', 'disgorge', 'disgorgement']
        )
    
    def extract_penalty_amount(self, text: str) -> Optional[float]:
        """
        Extract civil penalty amount from text.
        
        Args:
            text: The fullText content
            
        Returns:
            Float amount or None
        """
        return self._extract_amount_after_keyword(
            text,
            ['civil penalty of', 'civil penalties of', 'civil penalty totaling', 
             'penalty of', 'penalties of', 'civil monetary penalty']
        )
    
    def extract_prejudgment_interest(self, text: str) -> Optional[float]:
        """
        Extract prejudgment interest amount from text.
        
        Args:
            text: The fullText content
            
        Returns:
            Float amount or None
        """
        return self._extract_amount_after_keyword(
            text,
            ['prejudgment interest of', 'prejudgment interest totaling', 
             'pre-judgment interest of', 'prejudgment interest']
        )
    
    def extract_has_injunction(self, text: str) -> bool:
        """
        Check if case includes injunctive relief.
        
        Args:
            text: The fullText content
            
        Returns:
            Boolean flag
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        return (
            'injunction' in text_lower or 
            'injunctive relief' in text_lower or
            'enjoin' in text_lower or 
            'permanently restrained' in text_lower or
            'permanent restraining' in text_lower
        )
    
    def extract_has_officer_director_bar(self, text: str) -> bool:
        """
        Check if case includes officer/director bar.
        
        Args:
            text: The fullText content
            
        Returns:
            Boolean flag
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Look for officer/director bar patterns
        return (
            ('officer' in text_lower and 'director' in text_lower and 'bar' in text_lower) or
            'barred from serving as an officer' in text_lower or
            'barred from serving as a director' in text_lower or
            'officer and director bar' in text_lower or
            'o&d bar' in text_lower
        )
    
    def extract_has_conduct_restriction(self, text: str) -> bool:
        """
        Check if case includes conduct-based restrictions.
        
        Args:
            text: The fullText content
            
        Returns:
            Boolean flag
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        return (
            'conduct-based injunction' in text_lower or
            'trading restriction' in text_lower or
            'penny stock bar' in text_lower or
            'industry bar' in text_lower or
            'barred from the securities industry' in text_lower or
            'barred from associating' in text_lower or
            'prohibited from participating' in text_lower or
            'prohibit' in text_lower and 'trading' in text_lower or
            'prohibited from' in text_lower and 'trading' in text_lower or
            'restrict' in text_lower and 'trading' in text_lower or
            'trading in any brokerage account' in text_lower
        )
    
    def extract(self, text: str) -> GroundTruth:
        """
        Extract all ground truth outcomes from case text.
        
        Args:
            text: The fullText content from the case
            
        Returns:
            GroundTruth dataclass with all extracted outcomes
        """
        return GroundTruth(
            resolution_type=self.extract_resolution_type(text),
            disgorgement_amount=self.extract_disgorgement_amount(text),
            penalty_amount=self.extract_penalty_amount(text),
            prejudgment_interest=self.extract_prejudgment_interest(text),
            has_injunction=self.extract_has_injunction(text),
            has_officer_director_bar=self.extract_has_officer_director_bar(text),
            has_conduct_restriction=self.extract_has_conduct_restriction(text)
        )


def extract_ground_truth(text: str) -> Dict[str, Any]:
    """
    Convenience function to extract ground truth and return as dict.
    
    Args:
        text: The fullText content
        
    Returns:
        Dictionary with ground truth outcomes
    """
    extractor = GroundTruthExtractor()
    ground_truth = extractor.extract(text)
    return ground_truth.to_dict()


if __name__ == '__main__':
    # Example usage
    sample_text = """
    On December 16, 2025, the SEC filed settled action against John Doe.
    The defendant has consented to the entry of a final judgment that includes
    disgorgement of $373,885, prejudgment interest of $22,629.34, and a civil 
    penalty of $112,165. The judgment also includes a permanent injunction
    against future violations and bars the defendant from serving as an officer
    or director of any public company.
    """
    
    extractor = GroundTruthExtractor()
    result = extractor.extract(sample_text)
    
    print("Ground Truth Extraction Test:")
    print("-" * 40)
    print(f"Resolution Type: {result.resolution_type}")
    print(f"Disgorgement: ${result.disgorgement_amount:,.2f}" if result.disgorgement_amount else "Disgorgement: None")
    print(f"Penalty: ${result.penalty_amount:,.2f}" if result.penalty_amount else "Penalty: None")
    print(f"Prejudgment Interest: ${result.prejudgment_interest:,.2f}" if result.prejudgment_interest else "Prejudgment Interest: None")
    print(f"Has Injunction: {result.has_injunction}")
    print(f"Has Officer/Director Bar: {result.has_officer_director_bar}")
    print(f"Has Conduct Restriction: {result.has_conduct_restriction}")
