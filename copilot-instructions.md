# Copilot PR Review Instructions

As Copilot, when reviewing pull requests in this repository, follow these guidelines:

- Enforce code style and formatting consistent with the project.
- Ensure all new and modified code is covered by appropriate tests.
- Check that all public functions, classes, and modules have clear docstrings.
- Verify that changes do not break existing functionality or tests.
- Confirm that dependency updates (if any) are justified and safe.
- For CLI or config changes, ensure documentation and usage examples are updated.
- For Python code, prefer type hints and explicit error handling.
- For Poetry projects, ensure `pyproject.toml` and `poetry.lock` are consistent.
- For pytest, check that fixtures are used efficiently and test isolation is maintained.
- Flag any security, performance, or maintainability concerns.
- If the PR description is unclear or missing context, request clarification.

If any of these guidelines are not met, leave a constructive comment or request changes.

---
These instructions are for Copilot and Copilot Chat PR review automation only.
