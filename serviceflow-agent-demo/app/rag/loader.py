from dataclasses import dataclass
from pathlib import Path

from app.config import KNOWLEDGE_BASE_DIR


@dataclass(frozen=True)
class KnowledgeDocument:
    knowledge_base: str
    source: str
    title: str
    content: str


def load_documents(root: Path = KNOWLEDGE_BASE_DIR) -> list[KnowledgeDocument]:
    documents: list[KnowledgeDocument] = []
    if not root.exists():
        return documents

    for base_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        for path in sorted(base_dir.glob("*.md")):
            content = path.read_text(encoding="utf-8")
            title = path.stem.replace("_", " ")
            for line in content.splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            documents.append(
                KnowledgeDocument(
                    knowledge_base=base_dir.name,
                    source=str(path.relative_to(root.parent)),
                    title=title,
                    content=content,
                )
            )
    return documents
