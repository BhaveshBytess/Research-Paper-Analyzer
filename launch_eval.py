import subprocess
import sys
import os
from pathlib import Path

# Change to project directory
project_dir = Path(r"C:\Users\oumme\OneDrive\Desktop\RESEARCH-PAPER-ANALYZER")
os.chdir(project_dir)

# Set up environment
env = os.environ.copy()
env["OPENROUTER_API_KEY"] = "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"
env["LLM_MODE"] = "openrouter::deepseek/deepseek-chat-v3.1:free"

print("="*60)
print("LAUNCHING BATCH EVALUATION")
print("="*60)
print(f"Working directory: {os.getcwd()}")
print(f"Python: {sys.executable}")
print(f"Script: batch_deepseek_inline.py")
print("="*60 + "\n")

# Execute the batch script
try:
    result = subprocess.run(
        [sys.executable, "batch_deepseek_inline.py"],
        env=env,
        capture_output=False,  # Show output in real-time
        text=True,
        timeout=600  # 10 minute timeout
    )
    
    print("\n" + "="*60)
    if result.returncode == 0:
        print("✓ EXECUTION COMPLETED SUCCESSFULLY")
    else:
        print(f"✗ EXECUTION FAILED (exit code: {result.returncode})")
    print("="*60)
    
    sys.exit(result.returncode)
    
except subprocess.TimeoutExpired:
    print("\n" + "="*60)
    print("✗ EXECUTION TIMEOUT (>10 minutes)")
    print("="*60)
    sys.exit(1)
    
except Exception as e:
    print("\n" + "="*60)
    print(f"✗ EXECUTION ERROR: {e}")
    print("="*60)
    import traceback
    traceback.print_exc()
    sys.exit(1)
