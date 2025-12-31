#!/usr/bin/env python3
"""
Code Diff Analyzer Tool
Analyzes changed files between git branches and extracts their information from codebase map.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
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


def execute_infiniloom_map(repo_path: str) -> str:
    """Execute infiniloom map command to generate codebase map."""
    output_file = os.path.join(repo_path, 'codebase-map.txt')

    try:
        # Change to repo directory and run infiniloom
        result = subprocess.run(
            ['infiniloom', 'map', '.', '--include', '**/*.java', '--output', 'codebase-map.txt'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Infiniloom map generated successfully: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to execute infiniloom map: {e.stderr}")
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


def parse_codebase_map(map_file_path: str, changed_files: List[str]) -> Dict[str, List[str]]:
    """Parse codebase-map.txt and extract information for changed files."""
    if not os.path.exists(map_file_path):
        raise FileNotFoundError(f"Codebase map file not found: {map_file_path}")

    file_info = {}

    with open(map_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # For each changed file, find its section in the codebase map
    for changed_file in changed_files:
        # Search for the file path in the map
        # The format might vary, so we'll look for lines containing the file path
        file_sections = []
        lines = content.split('\n')

        # Find sections related to this file
        in_section = False
        current_section = []

        for i, line in enumerate(lines):
            # Check if this line mentions our file
            if changed_file in line:
                # Collect context around this mention
                # Get a few lines before and after for context
                start_idx = max(0, i - 2)
                end_idx = min(len(lines), i + 10)
                section = '\n'.join(lines[start_idx:end_idx])
                file_sections.append(section)

        if file_sections:
            file_info[changed_file] = file_sections
        else:
            file_info[changed_file] = [f"No detailed information found in codebase map"]

    return file_info


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Analyze code changes between branches and extract codebase map information'
    )
    parser.add_argument('source_branch', help='Source branch name')
    parser.add_argument('destination_branch', help='Destination branch name')
    parser.add_argument('--repo-path', help='Path to repository (overrides REPO_PATH env var)', default=None)

    args = parser.parse_args()

    try:
        # Get repository path
        if args.repo_path:
            repo_path = args.repo_path
        else:
            repo_path = get_repo_path()

        print(f"Repository path: {repo_path}")
        print(f"Analyzing changes: {args.source_branch} -> {args.destination_branch}\n")

        # Step 1: Execute infiniloom map
        print("Step 1: Generating codebase map...")
        map_file = execute_infiniloom_map(repo_path)

        # Step 2: Get changed files
        print("\nStep 2: Getting changed files...")
        changed_files = get_changed_files(repo_path, args.source_branch, args.destination_branch)

        # Step 3: Parse codebase map for changed files
        print("\nStep 3: Extracting information from codebase map...")
        file_info = parse_codebase_map(map_file, changed_files)

        # Output results
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)

        print("\nChanged Files:")
        for idx, file in enumerate(changed_files, 1):
            print(f"{idx}. {file}")

        print("\n" + "="*80)
        print("FILE DETAILS FROM CODEBASE MAP")
        print("="*80)

        for file_path, sections in file_info.items():
            print(f"\n{'─'*80}")
            print(f"File: {file_path}")
            print(f"{'─'*80}")
            for section in sections:
                print(section)
                print()

        # Return data structure
        return {
            'changed_files': changed_files,
            'file_info': file_info
        }

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
