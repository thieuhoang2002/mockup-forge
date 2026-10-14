# Contributing to MockupForge

Thank you for your interest in contributing to **MockupForge**! We welcome bug fixes, optical engine optimizations, UI enhancements, and new feature ideas for Print-on-Demand (POD) creators and e-commerce sellers worldwide.

---

## How to Contribute

### 1. Reporting Bugs
- Search existing [Issues](https://github.com/thieuhoang2002/mockup-forge/issues) to verify if the issue has already been reported.
- Open a new issue using our **Bug Report** template, providing your OS, Python version, steps to reproduce, and sample images/logs.

### 2. Suggesting Features
- Open a **Feature Request** issue detailing the use case, desired behavior, and potential workflow improvements.

### 3. Submitting Pull Requests
1. Fork the repository and create your feature branch from `main`:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Test your modifications:
   ```bash
   python validator.py
   python run_demo.py
   ```
4. Commit your changes using standard Conventional Commits:
   ```bash
   git commit -m "feat(engine): optimize displacement interpolation speed"
   ```
5. Push to your branch and submit a Pull Request against `main`.

---

## Technical Guidelines
- **Zero GPU Requirement:** Ensure core optical processing in `engine.py` remains 100% CPU-compatible via OpenCV and NumPy.
- **Performance:** Keep rendering execution time under 0.2s for high-resolution (3000x3000px) canvases.
- **Code Style:** Write clean, documented Python adhering to PEP 8 standards.

Thank you for helping empower indie sellers with photorealistic, zero-subscription mockups! 👕🚀
