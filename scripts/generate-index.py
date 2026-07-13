from datetime import datetime, timezone
from pathlib import Path
import json
import re


repo_root = Path(__file__).resolve().parents[1]
docs_root = repo_root / "docs"
entries_root = docs_root / "entries" / "skills"
output_path = docs_root / "content-index.json"


def read_markdown_metadata(path: Path) -> dict[str, str]:
    content = path.read_text(encoding="utf-8")
    front_matter = re.match(r"^---\s*\r?\n(.*?)\r?\n---", content, re.DOTALL)
    if not front_matter:
        raise ValueError(f"{path} has no front matter.")

    metadata = {}
    for line in front_matter.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("\"'")
    return metadata


def read_resource_identity(path: Path) -> tuple[str, str]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a JSON object.")
        return str(payload.get("type", "")).strip(), str(payload.get("id", "")).strip()

    metadata = read_markdown_metadata(path)
    return metadata.get("type", "").strip(), metadata.get("id", "").strip()


def generate_index() -> dict:
    if not entries_root.is_dir():
        raise ValueError(f"Skills content folder does not exist: {entries_root}")

    resources = []
    seen_ids = set()

    for path in sorted(entries_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".json", ".md"}:
            continue

        resource_type, resource_id = read_resource_identity(path)
        if not resource_type:
            raise ValueError(f"{path} is missing type.")
        if not resource_id:
            raise ValueError(f"{path} is missing id.")
        if resource_id in seen_ids:
            raise ValueError(f"Duplicate resource id: {resource_id}")

        seen_ids.add(resource_id)
        resources.append(path.relative_to(docs_root).as_posix())

    return {
        "version": 2,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "files": resources,
    }


def main() -> None:
    index = generate_index()
    output_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {output_path} with {len(index['files'])} files.")


if __name__ == "__main__":
    main()
