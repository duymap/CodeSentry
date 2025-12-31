#!/usr/bin/env python3
"""
Code Diff Analyzer Tool
Analyzes Java code changes between git branches and packs them using infiniloom.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List
from dotenv import load_dotenv


def get_repo_path() -> str:
    """Get repository path from environment variable or .env file."""
    # Load .env file if it exists
    load_dotenv()

    repo_path = os.getenv('REPO_PATH')
    if not repo_path:
        raise ValueError("REPO_PATH is not set. Please set it in .env file or environment variable")

    if not os.path.isdir(repo_path):
        raise ValueError(f"Repository path does not exist: {repo_path}")

    return repo_path


def git_ref_exists(repo_path: str, ref: str) -> bool:
    """Check if a git reference (branch, tag, commit) exists."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--verify', ref],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False


def fetch_all_branches(repo_path: str) -> None:
    """Fetch all branches from remote repositories."""
    try:
        print("Fetching all branches from remote...")
        result = subprocess.run(
            ['git', 'fetch', '--all'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        print("Successfully fetched all branches")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to fetch branches: {e.stderr}")


def ensure_branch_exists(repo_path: str, branch: str) -> str:
    """Ensure a branch exists locally, fetching if necessary. Returns the full ref name."""
    # Try different ref formats
    possible_refs = [
        branch,                    # local branch or commit hash
        f'origin/{branch}',        # remote branch
        f'refs/heads/{branch}',    # full local ref
        f'refs/remotes/origin/{branch}'  # full remote ref
    ]

    # Check if any ref exists
    for ref in possible_refs:
        if git_ref_exists(repo_path, ref):
            print(f"Found ref: {ref}")
            return ref

    # If not found, try fetching
    print(f"Branch '{branch}' not found locally, fetching from remote...")
    fetch_all_branches(repo_path)

    # Try again after fetch
    for ref in possible_refs:
        if git_ref_exists(repo_path, ref):
            print(f"Found ref after fetch: {ref}")
            return ref

    # Still not found, raise error
    raise ValueError(f"Branch '{branch}' not found even after fetching. Please check the branch name.")


def filter_java_files(files: List[str]) -> List[str]:
    """Filter only Java files from the list."""
    java_files = [f for f in files if f.endswith('.java')]
    return java_files


def execute_infiniloom_pack(repo_path: str, java_files: List[str], output_dir: str) -> str:
    """Execute infiniloom pack command for changed Java files."""
    if not java_files:
        raise ValueError("No Java files found in the changed files")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Build the output path relative to the script location
    output_file = os.path.join(output_dir, 'llm.txt')

    # Build the command
    cmd = ['infiniloom', 'pack', '.', '--format', 'toon', '--compression', 'balanced', '--output', output_file]

    # Add --include for each Java file
    for java_file in java_files:
        cmd.extend(['--include', java_file])

    try:
        print(f"Executing infiniloom pack with {len(java_files)} Java files...")
        print(f"Command: {' '.join(cmd)}\n")

        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        print(f"Infiniloom pack completed successfully!")
        print(f"Output saved to: {output_file}")

        return output_file
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to execute infiniloom pack: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("infiniloom command not found. Please ensure it's installed and in PATH")


def get_changed_files(repo_path: str, source_branch: str, destination_branch: str) -> List[str]:
    """Get list of changed files between two branches using git diff."""
    try:
        # Ensure both branches exist, fetching if necessary
        print(f"Checking source branch: {source_branch}")
        source_ref = ensure_branch_exists(repo_path, source_branch)

        print(f"Checking destination branch: {destination_branch}")
        dest_ref = ensure_branch_exists(repo_path, destination_branch)

        # Get the list of changed files
        print(f"\nComparing {source_ref} ... {dest_ref}")
        result = subprocess.run(
            ['git', 'diff', '--name-only', f'{source_ref}...{dest_ref}'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )

        # Filter out empty lines
        changed_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
        print(f"Found {len(changed_files)} changed files")

        return changed_files
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to execute git diff: {e.stderr}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Analyze Java code changes between branches and pack them with infiniloom'
    )
    parser.add_argument('source_branch', help='Source branch name')
    parser.add_argument('destination_branch', help='Destination branch name')
    parser.add_argument('--repo-path', help='Path to repository (overrides REPO_PATH env var)', default=None)
    parser.add_argument('--output-dir', help='Output directory for llm.txt', default='output')

    args = parser.parse_args()

    try:
        # Get repository path
        if args.repo_path:
            repo_path = args.repo_path
        else:
            repo_path = get_repo_path()

        # Get script directory for output
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, args.output_dir)

        print(f"Repository path: {repo_path}")
        print(f"Analyzing changes: {args.source_branch} -> {args.destination_branch}")
        print(f"Output directory: {output_dir}\n")

        # Step 1: Get changed files
        print("Step 1: Getting changed files...")
        changed_files = get_changed_files(repo_path, args.source_branch, args.destination_branch)

        # Step 2: Filter Java files only
        print("\nStep 2: Filtering Java files...")
        java_files = filter_java_files(changed_files)

        if not java_files:
            print("No Java files found in the changes.")
            return {
                'changed_files': changed_files,
                'java_files': [],
                'output_file': None
            }

        print(f"Found {len(java_files)} Java file(s):")
        for idx, file in enumerate(java_files, 1):
            print(f"  {idx}. {file}")

        # Step 3: Execute infiniloom pack
        print("\nStep 3: Packing Java files with infiniloom...")
        output_file = execute_infiniloom_pack(repo_path, java_files, output_dir)

        # Output results
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        print(f"\nTotal changed files: {len(changed_files)}")
        print(f"Java files processed: {len(java_files)}")
        print(f"Output file: {output_file}")

        # Return data structure
        return {
            'changed_files': changed_files,
            'java_files': java_files,
            'output_file': output_file
        }

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
