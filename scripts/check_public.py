"""Check the public artifact before uploading, without reading private sources."""
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if "id" in fields:
            self.ids.add(fields["id"])
        for key in ("href", "src"):
            if key in fields:
                self.links.append(fields[key])


errors = []
checked = 0
for path in sorted(DOCS.rglob("*")):
    if path.is_symlink():
        errors.append(f"符号链接：{path.relative_to(ROOT)}")
    if not path.is_file() or path.suffix not in {".html", ".md"}:
        continue
    text = path.read_text(encoding="utf-8")
    for pattern in [r"thread://", r"file://", r"\b[A-Za-z]:[/\\]", r"\bgh[pousr]_[A-Za-z0-9]{20,}", r"\bsk-[A-Za-z0-9_-]{25,}", r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b"]:
        if re.search(pattern, text, re.I):
            errors.append(f"需人工检查：{path.relative_to(ROOT)} 命中 {pattern}")
    if "\ufffd" in text:
        errors.append(f"乱码字符：{path.relative_to(ROOT)}")
    if path.suffix == ".html":
        parser = Links()
        parser.feed(text)
        targets = parser.links
    else:
        targets = re.findall(r"\]\(([^)\n]+)\)", text)
    for target in targets:
        if "://" in target or target.startswith("data:"):
            continue
        parsed = urlsplit(target)
        if not parsed.path:
            if path.suffix == ".html" and parsed.fragment and parsed.fragment not in parser.ids:
                errors.append(f"缺失锚点：{path.relative_to(ROOT)} → {target}")
            continue
        dest = (path.parent / unquote(parsed.path)).resolve()
        checked += 1
        if not dest.is_relative_to(DOCS.resolve()) or not dest.exists():
            errors.append(f"缺失或越界链接：{path.relative_to(ROOT)} → {target}")

if errors:
    raise SystemExit("\n".join(errors))
print(f"公开文件检查通过：{checked} 处本地链接；未发现所检查的私人链接、绝对路径或常见密钥模式。")
