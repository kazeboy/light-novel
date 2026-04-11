# prompt: plan-feature
> Copy-paste this prompt before asking Claude to build any non-trivial new feature.
> Always plan before building — especially for features that touch multiple files.

---

```
I want to add a new feature to the light-novel project. Please plan the implementation 
before writing any code.

Feature name: [short name, e.g. "AI chapter summaries" or "Anki vocabulary export"]

What it should do:
[2–4 sentences describing the desired behavior from the user's perspective]

Entry point:
[ ] Triggered from main.py (interactive prompt)
[ ] Standalone script
[ ] Called automatically during EPUB build
[ ] Other: [describe]

Inputs available:
[ ] The JSON archive (output/<slug>/chapters/)
[ ] The meta.json file
[ ] Raw scraped text
[ ] User-supplied arguments
[ ] Other: [describe]

Expected output:
[ ] Modifies the EPUB content
[ ] Generates a new file (e.g. vocabulary export, Anki deck)
[ ] Adds a field to chapter JSON
[ ] Prints to terminal
[ ] Other: [describe]

Constraints or preferences:
[e.g. "Should not require re-downloading chapters", "Should be skippable/optional",
 "Should work for both English and Japanese novels", "Should use the Anthropic API"]

Please produce:
1. A step-by-step implementation plan (which files to create/modify and why)
2. Any design decisions you'd want me to confirm before starting
3. Potential risks or edge cases to handle
```
