from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

print("Running Revision 7.2 source and manifest assurance tests...")
tests = subprocess.run([sys.executable, str(ROOT / "run_python_tests.py")], cwd=ROOT)
if tests.returncode:
    raise SystemExit(tests.returncode)

print("Running master compilation verifier...")
verification = subprocess.run([sys.executable, str(ROOT / "verify_master_compilation.py")], cwd=ROOT)
if verification.returncode not in (0, 2):
    raise SystemExit(verification.returncode)
if verification.returncode == 2:
    print("Precompilation pending is expected until all seven real artifact sets are recorded.")
else:
    print("All seven compilation records passed structural and cryptographic verification.")
