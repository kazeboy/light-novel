# COMMANDS.md

## 1. First Time Setup (after cloning the repo)

```bash
cd light-novel
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install
```

- requirements.txt installs all Python libraries
- playwright install downloads the browser binaries used by Playwright

## 2. Every Time I Come Back to the Project

```bash
cd light-novel
source .venv/bin/activate
python lngrab.py
```

## 4. If Something Breaks (Rebuild Environment)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install
python lngrab.py
```

## 7. Project Structure Reminder

- lngrab.py → main entry point (run this file)
- README.md → project overview and instructions
- requirements.txt → Python dependencies
- playwright.config.js → Playwright configuration
- /src → source code files
