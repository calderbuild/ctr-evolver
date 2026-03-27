"""Export evolved skills data as base64 tarball for download."""
import base64, io, json, os, tarfile
from pathlib import Path

root = Path(__file__).parent.parent
skills_dir = root / "skills"
data_dir = root / "data"

buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as tar:
    # Add all skills
    for p in sorted(skills_dir.rglob("*")):
        if p.is_file() and "frontier" not in str(p):
            tar.add(p, arcname=str(p.relative_to(root)))
    # Add frontier config
    for f in ["active_skills.json", "metrics.json"]:
        fp = skills_dir / "frontier" / f
        if fp.exists():
            tar.add(fp, arcname=str(fp.relative_to(root)))
    # Add data files
    for f in ["checkpoint.json", "evolution_memory.json", "interventions.jsonl"]:
        fp = data_dir / f
        if fp.exists():
            tar.add(fp, arcname=str(fp.relative_to(root)))

b64 = base64.b64encode(buf.getvalue()).decode()
out = root / "export.b64"
out.write_text(b64)
print(f"Exported {len(b64)} bytes to export.b64")
