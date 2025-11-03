#!/usr/bin/env python
"""
Direct runner - loads .env and executes batch evaluation with DeepSeek
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    print(f"Loading environment from {env_path}")
    load_dotenv(env_path)
else:
    print("Warning: .env file not found. Checking environment variables...")

# Set DeepSeek as default
if not os.environ.get("LLM_MODE"):
    os.environ["LLM_MODE"] = "openrouter::deepseek/deepseek-chat-v3.1:free"

# Check API key
api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    print("\n" + "="*60)
    print("ERROR: OPENROUTER_API_KEY not found!")
    print("="*60)
    print("\nPlease set up your API key:")
    print("1. Create a .env file in the project root")
    print("2. Add: OPENROUTER_API_KEY=your_key_here")
    print("\nOr set it as an environment variable:")
    print("  Windows: set OPENROUTER_API_KEY=your_key_here")
    print("  Linux/Mac: export OPENROUTER_API_KEY=your_key_here")
    print("="*60)
    sys.exit(1)

print(f"✓ API Key loaded: {api_key[:8]}...")
print(f"✓ LLM Mode: {os.environ.get('LLM_MODE')}")

# Now import and run the batch evaluation
print("\nStarting batch evaluation...\n")

# Import the main function from batch_eval_runner
sys.path.insert(0, str(Path(__file__).parent))
from batch_eval_runner import main

# Run it
if __name__ == "__main__":
    main()
