import subprocess
import sys
import os

os.environ["OPENROUTER_API_KEY"] = "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"
os.environ["LLM_MODE"] = "openrouter::deepseek/deepseek-chat-v3.1:free"

result = subprocess.run([sys.executable, "batch_eval_runner.py"], 
                       capture_output=True, 
                       text=True,
                       cwd=r"C:\Users\oumme\OneDrive\Desktop\RESEARCH-PAPER-ANALYZER")

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print("Return code:", result.returncode)
