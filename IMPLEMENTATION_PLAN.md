# SEC Case LLM Evaluation Pipeline

## Overview

Transform raw SEC case JSON data into a clean format with complaint PDF text and ground truth outcomes. Evaluate LLM performance on predicting SEC case outcomes by comparing predictions against actual results.

**Critical Design Decision:** Only use complaint PDF text as LLM input (never fullText) to avoid data leakage, since fullText contains the actual outcomes.

---

## Phase 1: Data Cleaning and Text Extraction ✅

### Step 1.1: Extract Complaint Text from PDFs (ONLY SOURCE)
- Parse complaint PDF URLs from `supportingDocuments` (type="complaint")
- Extract full text from PDF files using pdfplumber/PyPDF2
- Store extracted PDF text as `complaint_text`
- **CRITICAL: Never use fullText as input for LLM** (it contains the answers)

### Step 1.2: Handle Missing/Failed PDFs
- If PDF URL is missing → Skip case
- If PDF download fails → Skip case
- If PDF parsing fails → Skip case
- Log all skipped cases to `skipped_cases.json`

---

## Phase 2: Ground Truth Extraction ✅

Extract from fullText (only used for comparison, never shown to LLM).

### Step 2.1: Resolution Type Priority Logic
1. `settled_action` - Check first: "settled action" or "filed settled action"
2. `consent_judgment` - Check second: "consent" + "judgment" (only if not settled_action)
3. `final_judgment` - "final judgment" (court-ordered, not consent)
4. `jury_verdict` - "jury" + "verdict"
5. `dismissed` - "dismiss" or "dismissed with prejudice"
6. `filed_charges` - Default for ongoing cases (no resolution indicators)

**Rationale:** `settled_action` indicates pre-filing settlement and is the stronger, earlier signal.

### Step 2.2: Monetary Outcomes
- `disgorgement_amount`: Extract "$X" after "disgorgement"
- `penalty_amount`: Extract "$X" after "civil penalty"
- `prejudgment_interest`: Extract "$X" after "prejudgment interest"

### Step 2.3: Remedial Measures (Boolean)
- `has_injunction`: "injunction" or "injunctive relief" in text
- `has_officer_director_bar`: "officer" + "director" + "bar"
- `has_conduct_restriction`: trading restrictions, industry bar, etc.

---

## Phase 3: Create Evaluation Dataset ✅

### Output Format
```json
{
  "case_id": "LR-26445",
  "metadata": {
    "release_date": "2025-12-16",
    "title": "Artur Khachatryan",
    "complaint_url": "https://..."
  },
  "complaint_text": "[Extracted from PDF - what LLM sees]",
  "ground_truth": {
    "resolution_type": "settled_action",
    "disgorgement_amount": 373885.0,
    "penalty_amount": 112165.0,
    "prejudgment_interest": 22629.34,
    "has_injunction": true,
    "has_officer_director_bar": false,
    "has_conduct_restriction": true
  }
}
```

### Files Generated
- `evaluation_dataset.json` - All successfully processed cases
- `skipped_cases.json` - Cases where PDF extraction failed

---

## Phase 4: LLM Evaluation ✅

### 7 Questions Per Case
| Question | Type | Scoring |
|----------|------|---------|
| Resolution Type | Categorical (6 options) | Exact match |
| Disgorgement Amount | Monetary | Within 10% |
| Civil Penalty Amount | Monetary | Within 10% |
| Prejudgment Interest | Monetary | Within 10% |
| Has Injunction | Yes/No | Exact match |
| Has Officer/Director Bar | Yes/No | Exact match |
| Has Conduct Restriction | Yes/No | Exact match |

### Scoring Rules
- **Monetary 10% Tolerance:** `|predicted - actual| / actual <= 0.10`
- **Null amounts:** Skip that question (don't penalize)
- **$0 amounts:** Require exact match
- **Overall Score:** Simple average of all accuracy metrics

---

## Implementation Files

```
newlex/
├── run_evaluation.py              # Main CLI
├── requirements.txt
├── sec-cases.json                 # Source data
├── data/processed/
│   ├── evaluation_dataset.json    # All cases for evaluation
│   └── skipped_cases.json         # Failed PDF extractions
└── src/
    ├── preprocessing/
    │   ├── pdf_extractor.py       # PDF download & text extraction
    │   ├── ground_truth_extractor.py  # Outcome extraction from fullText
    │   └── dataset_builder.py     # Combines both
    └── evaluation/
        ├── llm_prompt_formatter.py  # Prompt templates
        ├── llm_runner.py           # LLM providers (OpenAI, Anthropic, Mock)
        └── score_calculator.py     # 10% tolerance scoring
```

---

## Usage

```bash
# 1. Build dataset (extract PDFs, ground truth)
python run_evaluation.py --build-dataset

# 2. Run LLM evaluation
python run_evaluation.py --evaluate --provider openai --model gpt-4 --save-results

# 3. View sample case
python run_evaluation.py --show-sample
```

---

## Status

- [x] PDF extraction from complaint URLs
- [x] Ground truth extraction with priority logic
- [x] Evaluation dataset creation
- [x] LLM prompt template
- [x] Score calculator with 10% tolerance
- [x] Mock provider for testing
- [x] OpenAI/Anthropic provider support
- [ ] Process full dataset (4,155 cases)
- [ ] Run actual LLM evaluation


