# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CodeSentry is an AI-powered code review tool that analyzes git diffs between branches. It supports two LLM backends: Claude Code CLI (default) or local LLMs via Ollama. It uses infiniloom for packing dependency context optimized for LLM consumption. The tool is language-agnostic, supporting Java, .NET, Python, Rust, JavaScript/TypeScript, and other languages.

## Setup and Development

### Environment Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure repository path:
   ```bash
   cp .env.example .env
   # Edit .env and set REPO_PATH to the repository you want to analyze
   ```

### Running the Tool

Basic usage (requires `.env` with `REPO_PATH` configured):
```bash
./main.py source_branch destination_branch
```

With explicit repo path (bypasses `.env`):
```bash
./main.py source_branch destination_branch --repo-path /path/to/repo
```

Custom output directory:
```bash
./main.py main feature/branch --output-dir custom-output
```

Using local LLM via Ollama:
```bash
# Set in .env file:
# LOCAL_LLM=mistral
./main.py source_branch destination_branch
```

### External Dependencies

This tool requires these external CLI tools to be installed:

**Required:**
- **infiniloom**: Code packing tool for LLM consumption (https://github.com/Topos-Labs/infiniloom)

**LLM Backend (one required):**
- **claude**: Claude Code CLI (default if LOCAL_LLM not set)
- **ollama**: Local LLM runtime (required if LOCAL_LLM is set in .env)

The tool validates dependencies at startup and provides clear error messages if missing.

## Architecture

### Execution Flow

The tool executes in a linear pipeline with 5 main phases:

1. **LLM Configuration & Validation** (main.py:87-113, 449-452)
   - Loads `.env` file and checks for `LOCAL_LLM` setting
   - If `LOCAL_LLM` is set: validates Ollama is installed and model exists
   - If `LOCAL_LLM` not set: defaults to Claude Code CLI
   - Provides clear error messages for missing dependencies or invalid models

2. **Branch Validation & Diff Generation** (main.py:468-480)
   - Validates branches exist locally or fetches from remote
   - Uses `git diff source...destination` (three-dot syntax) to get changes from common ancestor
   - Saves raw diff to `output/diff.txt`

3. **AI-Powered Dependency Detection** (main.py:282-419)
   - Sends diff to configured LLM (Claude Code CLI or Ollama) via subprocess
   - AI analyzes the diff and returns JSON list of dependency classes
   - Filters out standard library and framework components
   - Supports multiple languages with appropriate path formats (Java: `com/example/Class`, .NET: `Namespace.Class`, Python: `package/module.py`, etc.)
   - Ollama uses `ollama run <model>` command; Claude uses `claude -p <prompt> --output-format json`

4. **Context Packing with infiniloom** (main.py:492-520)
   - Checks out destination branch to ensure correct file versions
   - Executes infiniloom with identified dependency classes
   - Uses toon format with balanced compression, removes comments/empty lines
   - Limited to 16000 tokens max
   - Saves packed context to `output/llm.txt`

5. **Final Code Review** (main.py:522-606)
   - Constructs comprehensive prompt combining diff + packed dependencies
   - Sends to configured LLM for full review
   - Reviews focus on: code quality, bugs, performance, security, business logic, improvements
   - Saves review to `output/code_review_result.md`

### Key Design Patterns

**LLM Abstraction**: The tool supports pluggable LLM backends through configuration (main.py:87-113). The `get_llm_config()` function determines which LLM to use, and both dependency detection and code review functions handle both backends transparently.

**Subprocess Integration**: All external tools (git, infiniloom, claude, ollama) are called via `subprocess.run()` with proper error handling, timeouts, and output capture.

**Graceful Degradation**: If dependency analysis or packing fails, the tool continues with warnings rather than failing completely. Reviews proceed without packed context if necessary.

**Multi-Language Support**: The dependency detection prompt (main.py:285-352) contains language-specific rules for path formats and exclusions. This allows the same tool to work across Java, .NET, Python, Rust, and JavaScript/TypeScript codebases.

**Branch Reference Resolution**: The `ensure_branch_exists()` function (main.py:162-189) tries multiple reference formats (local, remote, full refs) and automatically fetches if needed, making the tool resilient to different git configurations.

**Early Validation**: Ollama setup is validated at startup (main.py:18-64) before any git operations, providing immediate feedback about missing dependencies or invalid models.

### Output Files

All output goes to `output/` directory (or custom via `--output-dir`):
- `diff.txt`: Raw git diff
- `llm.txt`: infiniloom-packed dependency classes (toon format)
- `prompt.txt`: Final prompt sent to Claude
- `code_review_result.md`: AI-generated review

### Configuration

Environment variables loaded via python-dotenv from `.env` file:
- `REPO_PATH`: Path to repository to analyze (required if `--repo-path` not provided)
- `LOCAL_LLM`: (Optional) Ollama model name to use instead of Claude Code CLI (e.g., `mistral`, `codellama`, `deepseek-coder`)

### Timeout Settings

- Dependency analysis (Claude): 180s (3 minutes) - main.py:378
- Code review (Claude): 300s (5 minutes) - main.py:569
- Ollama operations: 300s (5 minutes) - main.py:76

### Return Value

When used as a Python module, `main()` returns a dictionary with all output paths and the review text, useful for programmatic integration.
