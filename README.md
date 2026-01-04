# Code Sentry

An AI-powered code review tool that analyzes code changes between git branches using Claude Code and infiniloom.

## Features

- Compares two git branches to identify changed files
- Automatically fetches remote branches if not available locally
- Uses AI (Claude Code or local LLM via Ollama) to analyze git diffs and identify dependency classes
- Packs related dependencies using infiniloom for LLM context
- Generates comprehensive AI-powered code reviews
- Supports both Claude Code CLI (default) and local LLMs via Ollama
- Reviews focus on code quality, potential bugs, performance, security, and improvements
- Outputs diff, dependencies, prompts, and review results to a dedicated output directory

## Prerequisites

Before using this tool, you must install the following:

### Required Tools

1. **Python 3.9.x or above**
   ```bash
   python --version  # Should be 3.9.x or higher
   ```

2. **Git**
   ```bash
   git --version
   ```

3. **infiniloom** - Code packing tool for LLM consumption
   - Installation: https://github.com/Topos-Labs/infiniloom
   - Must be available in PATH
   ```bash
   infiniloom --version  # Verify installation
   ```

4. **Claude Code** - Claude AI CLI tool (default)
   - Must be installed and authenticated
   - Used for AI-powered diff analysis and code reviews
   ```bash
   claude --version  # Verify installation
   ```

5. **Ollama** - Optional local LLM runtime (alternative to Claude Code)
   - Installation: https://ollama.ai/
   - Use if you prefer running LLMs locally
   ```bash
   ollama --version  # Verify installation
   ollama list       # List installed models
   ```

### Python Dependencies

- python-dotenv

## Installation

1. Install required Python packages:

```bash
pip install -r requirements.txt
```

2. Copy the example environment file and configure it:

```bash
cp .env.example .env
# Edit .env and set your REPO_PATH
```

3. Make the script executable:

```bash
chmod +x main.py
```

4. (Optional) Set up local LLM with Ollama:

```bash
# Install Ollama from https://ollama.ai/

# Pull a model (examples)
ollama pull mistral
ollama pull llama2
ollama pull codellama
ollama pull deepseek-coder

# Verify the model is available
ollama list

# Add to your .env file:
# LOCAL_LLM=mistral
```

## Usage

### Basic Usage

The tool reads `REPO_PATH` from the `.env` file automatically:

```bash
# Ensure your .env file contains: REPO_PATH=/path/to/your/repo
./main.py source_branch destination_branch
```

### Alternative: Specify repo path directly

```bash
./main.py source_branch destination_branch --repo-path /path/to/your/repo
```

### Examples

```bash
# Compare main branch with feature branch (using .env)
./main.py main feature/new-feature

# Compare using explicit repo path (bypasses .env)
./main.py develop staging --repo-path /var/projects/myapp

# Specify custom output directory
./main.py main feature/auth --output-dir my-output
```

## Output

The tool generates multiple files in the output directory (default: `output/`):

1. **Console Output**: Shows execution progress and summary
2. **diff.txt**: Raw git diff between the two branches
3. **llm.txt**: Infiniloom-packed file containing identified dependency classes (uses toon format with balanced compression)
4. **prompt.txt**: The final prompt sent to Claude Code for review
5. **code_review_result.md**: AI-generated code review from Claude Code

The infiniloom output uses toon format with balanced compression, optimized for LLM consumption.

## Configuration

The tool uses a `.env` file to store configuration:

- `REPO_PATH`: Path to the git repository (required if not using --repo-path flag)
- `LOCAL_LLM`: (Optional) Name of Ollama model to use instead of Claude Code CLI

### LLM Configuration

**Option 1: Claude Code CLI (Default)**
```bash
# .env file
REPO_PATH=/Users/username/projects/myrepo
# LOCAL_LLM not set - uses Claude Code CLI
```

**Option 2: Local LLM via Ollama**
```bash
# .env file
REPO_PATH=/Users/username/projects/myrepo
LOCAL_LLM=mistral
```

Available Ollama models (examples):
- `mistral` - Fast and capable general-purpose model
- `llama2` - Meta's Llama 2 model
- `codellama` - Specialized for code understanding
- `deepseek-coder` - Optimized for code analysis
- `qwen2.5-coder` - Alibaba's coding model

To see all installed models: `ollama list`

## How It Works

1. **Setup & Validation**
   - Loads configuration from `.env` file using python-dotenv
   - Determines which LLM to use (Claude Code CLI or Ollama)
   - Validates Ollama setup if LOCAL_LLM is configured
   - Validates the repository path from .env or --repo-path argument
   - Checks if branches exist locally, fetches from remote if needed

2. **Diff Analysis**
   - Runs `git diff source...destination` to get full diff between branches
   - Saves raw diff to `diff.txt`

3. **AI-Powered Dependency Detection**
   - Sends the diff to configured LLM for analysis (Claude Code or Ollama)
   - AI identifies relevant dependency classes that provide context for the changes
   - Excludes library classes and focuses on project-specific dependencies

4. **Context Packing**
   - Checks out the destination branch
   - Uses infiniloom to pack identified dependency classes:
     - Format: `toon`
     - Compression: `balanced`
     - Options: `--remove-comments --remove-empty-lines --no-symbols`
     - Max tokens: 16000
   - Saves packed context to `llm.txt`

5. **AI Code Review**
   - Constructs a comprehensive prompt with:
     - The git diff
     - Packed dependency classes as reference context
   - Sends to configured LLM for review focusing on:
     - Code quality and best practices
     - Potential bugs or issues
     - Performance considerations
     - Security concerns
     - Suggestions for improvements
   - Saves review to `code_review_result.md`

6. **Output**
   - All files saved to the `output/` directory (or custom directory via --output-dir)
   - Summary printed to console

## Error Handling

The tool will exit with an error if:
- REPO_PATH is not set in .env file and --repo-path is not provided
- The repository path doesn't exist
- infiniloom is not installed or not in PATH
- Claude Code CLI (`claude` command) is not installed when using default mode
- Ollama is not installed when LOCAL_LLM is set
- The specified Ollama model is not found locally
- Git commands fail (invalid branches, not a git repo, etc.)
- The infiniloom pack command fails

The tool will continue with warnings if:
- No dependency classes are identified by the LLM (review will proceed without context)
- LLM requests timeout (partial results may be available)
- Infiniloom packing fails (review will proceed without packed context)

### Common Errors and Solutions

**Error: "Model 'xyz' not found in Ollama"**
```bash
# Solution: Pull the model first
ollama pull xyz
```

**Error: "LOCAL_LLM is set but Ollama is not installed"**
```bash
# Solution 1: Install Ollama from https://ollama.ai/
# Solution 2: Remove LOCAL_LLM from .env to use Claude Code CLI
```

**Error: "'claude' command not found"**
```bash
# Solution: Install Claude Code CLI or use Ollama instead
# To use Ollama, add LOCAL_LLM=model_name to your .env file
```

## Return Value

When used as a module, the `main()` function returns a dictionary with:

```python
{
    'diff_file': '/path/to/output/diff.txt',
    'classes': ['com/example/Class1', 'com/example/Class2', ...],
    'output_file': '/path/to/output/llm.txt',
    'prompt_file': '/path/to/output/prompt.txt',
    'review_file': '/path/to/output/code_review_result.md',
    'review': '... full review text ...'
}
```

## Notes

- The git diff uses three-dot syntax (`source...destination`) to show changes between the common ancestor and destination
- AI (Claude Code CLI or Ollama) is used twice in the workflow:
  1. To identify relevant dependency classes from the diff
  2. To perform the final code review
- If branches are not found locally, the tool automatically runs `git fetch --all`
- The tool automatically checks out the destination branch to pack dependency classes
- The output directory is created automatically if it doesn't exist
- LLM requests have timeouts: 3 minutes for dependency analysis, 5 minutes for code review
- The infiniloom pack command uses specific options optimized for LLM consumption:
  - Removes comments and empty lines
  - Excludes symbols
  - Limits output to 16000 tokens
- When using Ollama, ensure your system has enough resources (RAM/GPU) for the selected model
- For best code review results with Ollama, use code-specialized models like `codellama`, `deepseek-coder`, or `qwen2.5-coder`
