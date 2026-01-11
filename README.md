# LexArena

**A live benchmark for evaluating AI models on SEC enforcement case predictions.**

LexArena tests whether AI systems can correctly predict real SEC enforcement outcomes before they happen. Models are given complaint text and must forecast resolution type, monetary penalties, and remedial measures.

## 🎯 Overview

Legal prediction is a challenging domain requiring both factual extraction and probabilistic reasoning. LexArena provides:

- **Real cases** — 500+ resolved SEC enforcement actions with verified outcomes
- **Blind evaluation** — Models see only the original complaint, never the outcome
- **Standardized metrics** — 6 prediction targets with consistent scoring
- **Open leaderboard** — Compare models on the same benchmark

## 📊 Current Results

| Model | Overall | Resolution | Monetary | Injunction | Officer Bar |
|-------|---------|------------|----------|------------|-------------|
| GPT-4o | **64.9%** | 38.6% | 53.0% | 78.8% | 89.2% |
| Claude 3.5 | — | — | — | — | — |
| Gemini 2.0 | — | — | — | — | — |

## 🔮 Prediction Metrics

Models predict 6 outcome metrics for each case:

| Metric | Description | Scoring |
|--------|-------------|---------|
| **Resolution Type** | Settled vs. litigated | Exact match |
| **Disgorgement** | Amount of ill-gotten gains returned | ±10% tolerance |
| **Civil Penalty** | Fine amount imposed | ±10% tolerance |
| **Prejudgment Interest** | Interest on disgorgement | ±10% tolerance |
| **Injunction** | Court order preventing future violations | Exact match |
| **Officer/Director Bar** | Ban from serving as company officer | Exact match |

## 🏗️ How It Works

```
SEC Complaint PDF → Text Extraction → LLM Prediction → Compare to Ground Truth → Score
```

1. **Data Collection** — SEC litigation releases are scraped with complaint PDFs
2. **Synopsis Generation** — GPT-4o generates plain-English case summaries
3. **Prediction** — Models receive synopsis and predict 6 outcomes
4. **Scoring** — Predictions compared against actual SEC release outcomes

## 🚀 Getting Started

### Prerequisites

```bash
pip install -r requirements.txt
```

Required environment variables:
```bash
export OPENAI_API_KEY=your_key_here
```

### Run Evaluation

```bash
# Evaluate GPT-4o on all cases
python run_evaluation.py --evaluate --provider openai --model gpt-4o

# Limit to first 50 cases
python run_evaluation.py --evaluate --max-eval-cases 50 --save-results
```

### Generate Synopses

```bash
# Generate case summaries for all cases
python generate_synopses.py

# Limit to specific number
python generate_synopses.py --limit 100
```

### Update Website

```bash
python generate_viewer.py
```

## 📁 Project Structure

```
lexarena/
├── index.html              # Landing page with leaderboard
├── cases.html              # All cases viewer with search
├── run_evaluation.py       # Main evaluation script
├── generate_synopses.py    # GPT-4o synopsis generation
├── generate_viewer.py      # HTML generation from results
├── litigation-cases.json   # Raw SEC case data
├── data/
│   └── processed/
│       ├── evaluation_results_openai.json
│       └── evaluation_dataset.json
└── src/
    ├── evaluation/
    │   ├── llm_prompt_formatter.py
    │   ├── llm_runner.py
    │   └── score_calculator.py
    └── preprocessing/
        ├── dataset_builder.py
        ├── ground_truth_extractor.py
        └── synopsis_generator.py
```

## 🤝 Contributing

We welcome contributions! To add a new model:

1. Add provider support in `src/evaluation/llm_runner.py`
2. Run evaluation: `python run_evaluation.py --evaluate --provider your_provider`
3. Submit a PR with results

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

**Built by [Saketh Kesiraju](https://github.com/sakethkesiraju26)**
