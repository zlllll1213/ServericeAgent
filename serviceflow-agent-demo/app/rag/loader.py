from dataclasses import dataclass
from pathlib import Path

from app.config import KNOWLEDGE_BASE_DIR


@dataclass(frozen=True)
class KnowledgeDocument:
    knowledge_base: str
    source_file: str
    title: str
    content: str
    product_name: str
    category: str

    @property
    def source(self) -> str:
        return self.source_file


def load_documents(root: Path = KNOWLEDGE_BASE_DIR) -> list[KnowledgeDocument]:
    documents: list[KnowledgeDocument] = []
    if not root.exists():
        return documents

    for base_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        for path in sorted(base_dir.glob("*.md")):
            content = path.read_text(encoding="utf-8")
            title = path.stem.replace("_", " ")
            # Markdown 一级标题优先作为文档标题，便于检索结果展示。
            for line in content.splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            documents.append(
                KnowledgeDocument(
                    knowledge_base=base_dir.name,
                    source_file=str(path.relative_to(root.parent)),
                    title=title,
                    content=content,
                    product_name=infer_product_name(content),
                    category=path.stem,
                )
            )
    return documents


def infer_product_name(text: str) -> str:
    lowered = text.lower()
    if "smartrouter x1" in lowered:
        return "SmartRouter X1"
    if "smartcamera c2" in lowered:
        return "SmartCamera C2"
    return "通用"
