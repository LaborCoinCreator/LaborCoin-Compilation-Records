from pathlib import Path
from manifest_tools import atomic_write_text, load_json, render_manifest_markdown

ROOT = Path(__file__).resolve().parent
manifest = load_json(ROOT / "MASTER_COMPILATION_MANIFEST.json")
atomic_write_text(ROOT / "MASTER_COMPILATION_MANIFEST.md", render_manifest_markdown(manifest))
print("MASTER_COMPILATION_MANIFEST.md updated from authoritative JSON.")
