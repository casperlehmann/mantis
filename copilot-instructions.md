# Copilot Usage Instructions

## Overview
This project supports GitHub Copilot and Copilot Chat for code suggestions, documentation, and automation. Follow these guidelines to get the most out of Copilot in this repository.

## Best Practices
- **Write clear, descriptive comments and docstrings** to help Copilot understand your intent.
- **Use type hints** and explicit variable names for better suggestions.
- **Break down complex problems** into smaller functions or classes for more accurate completions.
- **Review Copilot suggestions** for correctness, security, and style before accepting.

## Common Tasks
- **Generate tests:**
  - Write a function or class, then type `# test` or `# pytest` below it to get test suggestions.
- **Refactor code:**
  - Select code and ask Copilot Chat for refactoring or optimization tips.
- **Documentation:**
  - Type `# docstring` or `# documentation` above a function/class for docstring suggestions.
- **Regex and formatting:**
  - Ask Copilot Chat for help with regular expressions or string formatting best practices.

## Project-Specific Tips
- **Poetry:**
  - Copilot can help with dependency management and `pyproject.toml` edits.
- **Pytest:**
  - Use Copilot to generate fixtures, parameterized tests, and test utilities.
- **Jira/Mantis CLI:**
  - Ask Copilot for CLI usage examples, config file templates, or integration patterns.

## Limitations
- Copilot does not automatically bump your project version or handle release automation. Use GitHub Actions or manual steps for versioning.
- Always review Copilot’s code for project-specific conventions and security.

## Getting Help
- Use Copilot Chat for:
  - Explaining code
  - Debugging errors
  - Generating documentation
  - Exploring best practices

---
For more, see the [GitHub Copilot documentation](https://docs.github.com/en/copilot).
