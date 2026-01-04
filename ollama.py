#!/usr/bin/env python3
"""
Ollama integration module for local LLM support.
"""

import subprocess
import requests
from typing import List


def check_ollama_installed() -> bool:
    """Check if Ollama is installed and available."""
    try:
        result = subprocess.run(
            ['ollama', '--version'],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_ollama_models() -> List[str]:
    """Get list of available Ollama models."""
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            check=True
        )
        # Parse output to get model names
        lines = result.stdout.strip().split('\n')
        if len(lines) <= 1:  # Only header or empty
            return []

        models = []
        for line in lines[1:]:  # Skip header
            if line.strip():
                # Model name is the first column
                model_name = line.split()[0]
                models.append(model_name)
        return models
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def verify_ollama_model(model_name: str) -> bool:
    """Verify that a specific Ollama model exists."""
    available_models = get_ollama_models()
    # Check if model name matches exactly or is a prefix match
    for available_model in available_models:
        if available_model == model_name or available_model.startswith(f"{model_name}:"):
            return True
    return False


def check_ollama_service_running() -> bool:
    """Check if Ollama service is running."""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


def call_ollama(prompt: str, model: str) -> str:
    """Call Ollama with a prompt and return the response using HTTP API."""
    if not check_ollama_service_running():
        raise RuntimeError("Ollama service is not running. Please start it with 'ollama serve'")
    
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'stream': False
            },
            timeout=300  # 5 minute timeout
        )
        response.raise_for_status()
        return response.json()['response']
    except requests.Timeout:
        raise RuntimeError(f"Ollama request timed out after 5 minutes")
    except requests.RequestException as e:
        raise RuntimeError(f"Ollama error: {str(e)}")

