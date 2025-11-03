#!/usr/bin/env python
"""
DIRECT EXECUTION - Batch Evaluation with DeepSeek
Bypasses shell issues by running everything in Python
"""
import os
import sys

# Set up environment
os.environ["OPENROUTER_API_KEY"] = "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"
os.environ["LLM_MODE"] = "openrouter::deepseek/deepseek-chat-v3.1:free"

# Execute the batch runner
exec(open("batch_eval_runner.py").read())
