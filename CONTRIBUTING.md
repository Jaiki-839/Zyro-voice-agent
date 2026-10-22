# Contributing to ZYRO

First off, thank you for considering contributing to **ZYRO**! It's people like you who make ZYRO a great open-source personal AI voice assistant for everyone.

---

## Code of Conduct

This project and everyone participating in it is governed by the [ZYRO Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## How Can I Contribute?

### Reporting Bugs
- Check the [GitHub Issues](https://github.com/zyro-ai/zyro/issues) to make sure the issue hasn't been reported already.
- Provide a clear and descriptive title.
- Describe the exact steps to reproduce the problem.
- Include your Windows version, Python version, and relevant excerpts from `zyro.log`.

### Suggesting Enhancements / New Tools
- Feature suggestions are very welcome!
- Describe the voice commands that would trigger the new tool.
- Specify whether the tool is `READ_ONLY`, `USER_ACTION`, or `SYSTEM_WRITE`.
- Outline how the tool behaves in `ZYRO_MOCK_MODE=true`.

### Submitting Pull Requests
1. Fork the repo and create your branch from `main`:
   ```bash
   git checkout -b feat/my-new-tool
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Make your changes adhering to PEP 8 styling.
4. Ensure all tests pass:
   ```bash
   pytest
   ```
5. Follow Conventional Commits for commit messages:
   - `feat(tools): add calculator voice tool`
   - `fix(audio): fix playback jitter on high load`
   - `docs: update setup guide`
6. Push to your fork and submit a Pull Request!

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
