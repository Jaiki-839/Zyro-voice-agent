# Contributing to ZYRO

First off, thank you for considering contributing to **ZYRO**!

**Creator & Lead Developer:** **Jaiki Kushwaha**

---

## ⚠️ Important Copyright & Re-publishing Policy

> [!WARNING]
> **YOU CAN CONTRIBUTE VIA PULL REQUEST, BUT YOU CANNOT RE-PUBLISH AS YOUR OWN REPOSITORY.**
> 
> - ✅ **Pull Requests Welcome**: You are encouraged to submit enhancements, bug fixes, and new tools to this official repository.
> - ✅ **Personal & Educational Use**: You are free to fork for personal development, testing, and learning.
> - ❌ **No Cloning & Re-publishing**: You **CANNOT** clone this codebase and upload/re-publish it publicly under your own name or organization on GitHub or other platforms.
> - ❌ **No Stripping Credits**: Author attribution (**"Developed by Jaiki Kushwaha"**) must remain intact across all files, prompts, and interfaces.
> 
> Copyright © 2026 Jaiki Kushwaha. All Rights Reserved. Unauthorized re-publishing is subject to immediate DMCA takedown.

---

## Code of Conduct

This project is governed by the [ZYRO Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## How Can I Contribute?

### 1. Suggesting Enhancements / New Tools
- Describe the voice commands that would trigger the new tool.
- Specify whether the tool is `READ_ONLY`, `USER_ACTION`, or `SYSTEM_WRITE`.
- Ensure the tool respects `ZYRO_MOCK_MODE=true` for safe testing.

### 2. Submitting Pull Requests
1. Fork the official repo and create your branch from `main`:
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
4. Run tests:
   ```bash
   pytest
   ```
5. Follow Conventional Commits:
   - `feat(tools): add calculator voice tool`
   - `fix(audio): fix playback jitter on high load`
   - `docs: update setup guide`
6. Push to your fork and submit a Pull Request to the upstream repository!
