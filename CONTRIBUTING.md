# Contributing to LexArena

Thank you for your interest in contributing to LexArena! This document provides guidelines and instructions for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/newlex.git
   cd newlex
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create a .env file (it's already in .gitignore)
   export OPENAI_API_KEY=your_key_here
   # Optional: for other providers
   export ANTHROPIC_API_KEY=your_key_here
   export GOOGLE_API_KEY=your_key_here
   export REDUCTO_API_KEY=your_key_here
   ```

4. **Verify the setup**
   ```bash
   # Test the API server
   python api_server.py
   # Visit http://localhost:5000 to see the API documentation
   ```

## Development Workflow

### Making Changes

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes**
   - Write clear, readable code
   - Follow existing code style
   - Add comments for complex logic
   - Update documentation if needed

3. **Test your changes**
   ```bash
   # Test the API server
   python api_server.py
   
   # Run evaluations (if applicable)
   python run_evaluation.py --evaluate --max-eval-cases 10
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```
   
   Use clear, descriptive commit messages:
   - `feat: Add support for new LLM provider`
   - `fix: Resolve pagination issue in API`
   - `docs: Update README with setup instructions`

5. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   
   Then create a Pull Request on GitHub with:
   - Clear description of changes
   - Reference to any related issues
   - Screenshots (if UI changes)

## Code Style

### Python

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Keep functions focused and small
- Add docstrings for public functions and classes
- Use type hints where appropriate

### Example

```python
def calculate_score(predictions: List[Dict], ground_truth: Dict) -> float:
    """
    Calculate accuracy score for predictions.
    
    Args:
        predictions: List of prediction dictionaries
        ground_truth: Ground truth dictionary
        
    Returns:
        Accuracy score as a float between 0 and 1
    """
    # Implementation
    pass
```

## Adding New Features

### Adding a New LLM Provider

1. **Add provider class** in `src/evaluation/llm_runner.py`:
   ```python
   class NewProvider(LLMProvider):
       def __init__(self, model: str, api_key: Optional[str] = None):
           # Initialize provider
           pass
       
       def generate(self, prompt: str) -> str:
           # Generate response
           pass
       
       def get_model_name(self) -> str:
           return f"NewProvider/{self.model}"
       
       def get_config(self) -> Dict[str, Any]:
           return {'provider': 'newprovider', 'model': self.model}
   ```

2. **Update evaluation script** to support the new provider

3. **Run evaluation** and add results to the leaderboard

4. **Update documentation** with the new provider

### Adding New Metrics

1. **Update ground truth extraction** in `src/preprocessing/ground_truth_extractor.py`

2. **Update scoring logic** in `src/evaluation/score_calculator.py`

3. **Update prompts** in `src/evaluation/llm_prompt_formatter.py`

4. **Update documentation** and leaderboard display

## Reporting Bugs

### Before Reporting

- Check if the issue already exists
- Verify it's reproducible with the latest code
- Gather relevant information (error messages, logs, etc.)

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. See error

**Expected behavior**
What you expected to happen.

**Environment**
- OS: [e.g., macOS 14.0]
- Python version: [e.g., 3.9.0]
- Package versions: [run `pip list`]

**Additional context**
Add any other context, logs, or screenshots.
```

## Submitting Pull Requests

### PR Checklist

- [ ] Code follows the project's style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated (if needed)
- [ ] No new warnings or errors
- [ ] Tests pass (if applicable)
- [ ] Changes are backward compatible (if applicable)

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests pass
```

## Code Review Process

1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Once approved, your PR will be merged
4. Thank you for contributing! 🎉

## Questions?

- Open an issue for questions or discussions
- Check existing issues and discussions
- Review the README for general information

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
