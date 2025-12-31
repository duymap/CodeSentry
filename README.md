# Code Diff Analyzer

A Python tool to analyze Java code changes between git branches and pack them using infiniloom for LLM consumption.

## Features

- Compares two git branches to identify changed files
- Automatically fetches remote branches if not available locally
- Filters only Java files from the changes
- Uses infiniloom pack to create an LLM-ready file with changed Java code
- Outputs to a dedicated output directory

## Prerequisites

- Python 3.6+
- Git
- infiniloom (must be installed and available in PATH)
- A git repository that's already checked out
- python-dotenv package

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

The tool generates:

1. **Console Output**: Shows execution progress and summary
2. **llm.txt**: Infiniloom-packed file containing all changed Java files (saved to `output/llm.txt` by default)

The output file uses infiniloom's toon format with balanced compression, optimized for LLM consumption.

## Configuration

The tool uses a `.env` file to store configuration:

- `REPO_PATH`: Path to the git repository (required if not using --repo-path flag)

Example `.env` file:
```
REPO_PATH=/Users/username/projects/myrepo
```

## How It Works

1. Loads configuration from `.env` file using python-dotenv
2. Validates the repository path from .env or --repo-path argument
3. Checks if branches exist locally, fetches from remote if needed
4. Runs `git diff --name-only source...destination` to get changed files
5. Filters only `.java` files from the changed files
6. Executes `infiniloom pack . --format toon --compression balanced --output llm.txt --include <file1> --include <file2> ...` with all Java files
7. Saves the output to the `output/` directory (or custom directory via --output-dir)

## Error Handling

The tool will exit with an error if:
- REPO_PATH is not set in .env file and --repo-path is not provided
- The repository path doesn't exist
- infiniloom is not installed or not in PATH
- Git commands fail (invalid branches, not a git repo, etc.)
- No Java files found in the changes
- The infiniloom pack command fails

## Return Value

When used as a module, the `main()` function returns a dictionary with:

```python
{
    'changed_files': ['file1.java', 'file2.py', 'file3.java', ...],
    'java_files': ['file1.java', 'file3.java', ...],
    'output_file': '/path/to/output/llm.txt'
}
```

## Notes

- The git diff uses three-dot syntax (`source...destination`) to show changes between the common ancestor and destination
- Only Java files (`.java` extension) are processed
- If branches are not found locally, the tool automatically runs `git fetch --all`
- The output directory is created automatically if it doesn't exist
