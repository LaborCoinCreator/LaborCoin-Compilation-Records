from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parent
cmd=[sys.executable,'-m','unittest','discover','-s',str(root/'tests'),'-p','test_*.py','-v']
raise SystemExit(subprocess.run(cmd, cwd=root).returncode)
