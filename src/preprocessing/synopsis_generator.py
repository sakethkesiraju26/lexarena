"""
Synopsis Generator - Uses GPT-4o to generate case summaries from SEC fullText.
"""

import os
from typing import Optional
from openai import OpenAI


SYNOPSIS_PROMPT = """Write 2-3 paragraphs summarizing this SEC enforcement case. Include:
- Who the defendants are and their roles
- What fraudulent conduct they engaged in
- The time period and scope of the scheme
- Who was harmed and how much money was involved
- What relief the SEC is seeking

Write in plain English for a general audience. Be concise but comprehensive.

SEC Case Text:
{full_text}"""


class SynopsisGenerator:
    """Generate case synopses using GPT-4o."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with OpenAI API key.
        
        Args:
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def generate(self, full_text: str, max_text_length: int = 12000) -> str:
        """
        Generate a 2-3 paragraph synopsis from SEC case text.
        
        Args:
            full_text: The SEC litigation release text
            max_text_length: Max chars to send to API (truncates if longer)
            
        Returns:
            Generated synopsis string
        """
        if not full_text or len(full_text.strip()) < 100:
            return ""
        
        # Truncate if too long (keep first part which usually has key info)
        text_to_use = full_text[:max_text_length] if len(full_text) > max_text_length else full_text
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal analyst who writes clear, concise case summaries for a general audience."
                    },
                    {
                        "role": "user",
                        "content": SYNOPSIS_PROMPT.format(full_text=text_to_use)
                    }
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Synopsis generation error: {e}")
            return ""


def generate_synopsis(full_text: str, api_key: Optional[str] = None) -> str:
    """
    Convenience function to generate a synopsis.
    
    Args:
        full_text: SEC case text
        api_key: Optional OpenAI API key
        
    Returns:
        Generated synopsis
    """
    generator = SynopsisGenerator(api_key=api_key)
    return generator.generate(full_text)


if __name__ == "__main__":
    import sys
    
    # Test with sample text
    test_text = """
    Litigation Release No. 26200 / December 15, 2025
    
    SEC v. John Smith, Civil Action No. 1:25-cv-12345 (S.D.N.Y.)
    
    The Securities and Exchange Commission today announced charges against John Smith, 
    the former CEO of Acme Corp., for orchestrating a fraudulent scheme that defrauded 
    investors of approximately $50 million over a five-year period from 2018 to 2023.
    
    According to the SEC's complaint, Smith made false and misleading statements to 
    investors about Acme Corp.'s financial condition and business prospects. Smith 
    allegedly told investors that the company was profitable when it was actually 
    operating at a significant loss, and used new investor funds to pay returns to 
    earlier investors in Ponzi-like fashion.
    
    The SEC's complaint charges Smith with violating the antifraud provisions of 
    Section 17(a) of the Securities Act of 1933 and Section 10(b) of the Securities 
    Exchange Act of 1934 and Rule 10b-5 thereunder.
    
    The SEC seeks permanent injunctive relief, disgorgement of ill-gotten gains plus 
    prejudgment interest, civil penalties, and an officer and director bar against Smith.
    """
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)
    
    print("Generating synopsis...")
    synopsis = generate_synopsis(test_text)
    print("\n" + "=" * 50)
    print("GENERATED SYNOPSIS:")
    print("=" * 50)
    print(synopsis)
