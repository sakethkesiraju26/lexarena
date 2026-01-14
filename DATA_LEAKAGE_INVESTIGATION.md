# Data Leakage Investigation Report

## Current Status & Acknowledgment

**Current Implementation:** The dataset uses Reducto's `case_synopsis` field, which contains litigation release text (outcomes) rather than pure complaint text (allegations).

**Future Plan:** When resources permit, we will extract raw complaint PDF text directly using Reducto to provide clean, outcome-free input data for evaluation.

**Transparency:** We acknowledge this limitation and are transparent about it in our methodology documentation. All evaluation results should be interpreted with this context in mind, and we welcome peer review and feedback on our approach.

## Problem Identified

The evaluation dataset contains **data leakage**: the `complaint_text` field (what LLMs see during evaluation) contains **litigation release text** (which describes case outcomes) instead of **complaint text** (which describes allegations before resolution).

## Evidence

### Sample Cases Analyzed

1. **LR-26444 (James O Ward, Jr.)**
   - `complaint_text` starts with: "Litigation Release No. 26444..."
   - Contains: "Court Enters Final Judgment", "obtained a final judgment"
   - Contains: "The text explicitly states that the court ordered Ward to pay a civil penalty of $85,000"

2. **LR-26445 (Artur Khachatryan)**
   - `complaint_text` starts with: "Litigation Release No. 26445..."
   - Contains: "SEC Files Settled Action"

3. **LR-26443 (Irfan Mohammed)**
   - `complaint_text` starts with: "Litigation Release No. 26443..."
   - Contains: "SEC Files Settled Action"

### Key Indicators of Data Leakage

All sample cases contain outcome language:
- "Litigation Release"
- "Court Enters Final Judgment"
- "obtained a final judgment"
- "SEC Files Settled Action"
- "consented to"
- "final judgment"

**These phrases indicate the text describes outcomes that occurred AFTER the complaint was filed, not the complaint itself.**

## Root Cause Analysis

### Code Flow

1. **Dataset Builder** (`src/preprocessing/dataset_builder.py`):
   - Line 125: Gets complaint PDF URL from `supportingDocuments`
   - Line 136: Calls `reducto_extractor.extract_from_url(complaint_url)`
   - Line 149: Uses `reducto_data.get("case_synopsis", "")` as `complaint_text`

2. **Reducto Extractor** (`src/preprocessing/reducto_extractor.py`):
   - Uses Reducto pipeline ID: `k97bn9ne73pkmqk8c0ar2pt41s7ydwy4`
   - Extracts structured data from complaint PDF URLs
   - Returns `case_synopsis` field

### The Problem

**Reducto's `case_synopsis` field appears to extract litigation release text (outcome descriptions) instead of complaint text (allegation descriptions).**

This could happen if:
1. Reducto's pipeline is misconfigured to extract from litigation releases
2. The complaint PDFs themselves contain litigation release text (unlikely)
3. There's URL confusion between complaint PDFs and litigation release pages
4. Reducto's `case_synopsis` field is designed to extract summaries that include outcomes

## Impact

### Evaluation Validity

**ALL model evaluations are potentially invalid** because:

1. **Data Leakage**: Models are seeing outcome information instead of just complaints
2. **Inflated Scores**: Models can infer answers from the leaked outcome text
3. **Invalid Benchmark**: The evaluation doesn't test prediction ability, only text comprehension

### Affected Models

- ✅ OpenAI (GPT-4o) - 64.9% score potentially inflated
- ✅ Anthropic (Claude Opus 4) - 46.8% score potentially inflated  
- ✅ Google (Gemini 3 Flash) - 62.8% score potentially inflated

All three models were evaluated on the same corrupted dataset.

## Evidence from Model Reasoning

Gemini's reasoning for LR-26444 demonstrates the leakage:

> "The defendant, Ward, 'consented' to the court orders and the final judgment without admitting or denying the allegations..."
> 
> "The text explicitly states that the court ordered Ward to pay a civil penalty of $85,000..."
>
> "The judgment included a permanent injunction..."

These phrases reference **judgments and outcomes**, not complaint allegations.

## Next Steps

1. **Verify Reducto Output**: Check what Reducto actually extracts from complaint PDFs
2. **Compare with Actual Complaint PDFs**: Download a sample complaint PDF and verify its content
3. **Fix the Dataset**: Either:
   - Fix Reducto pipeline configuration
   - Use a different Reducto field that contains complaint text
   - Extract complaint text directly from PDFs
4. **Re-run Evaluations**: Re-evaluate all models with corrected dataset
5. **Update Documentation**: Document the issue and fix in methodology

## Files to Investigate

- `src/preprocessing/dataset_builder.py` - Dataset building logic
- `src/preprocessing/reducto_extractor.py` - Reducto extraction logic
- `data/processed/evaluation_dataset.json` - Current (corrupted) dataset
- Reducto pipeline configuration (external)

## Questions to Answer

1. What does Reducto's `case_synopsis` field actually extract?
2. Is there a different Reducto field that contains complaint-only text?
3. Can the Reducto pipeline be reconfigured?
4. Should we extract complaint text directly from PDFs instead?
