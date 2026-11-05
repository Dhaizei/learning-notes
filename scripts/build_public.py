"""Export reviewed learning notes; keep private sources out of Git history."""
from __future__ import annotations

import argparse
import html
import os
from pathlib import Path
import re
from urllib.parse import quote, unquote

import markdown

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
PRIVATE_PREFIXES = ("00-收集箱/", "03-资料与复核/")
CSS = """
:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f3f4ee;color:#21352d;font:16px/1.85 system-ui,'Microsoft YaHei',sans-serif}main{max-width:900px;margin:auto;padding:26px 30px 64px}nav{display:flex;flex-wrap:wrap;gap:18px;border-bottom:1px solid #d4ddd3;padding-bottom:16px;font-size:14px}a{color:#206c4a;text-underline-offset:3px}h1{font-size:32px;line-height:1.4}h2{font-size:23px;margin-top:32px}h3{font-size:19px}p,li{overflow-wrap:anywhere}table{display:block;overflow-x:auto;border-collapse:collapse;width:100%;background:#fff;font-size:14px}th,td{border:1px solid #d4ddd3;padding:10px 13px;text-align:left;vertical-align:top}th{background:#e4eddf}pre{overflow-x:auto;padding:18px;background:#e8ede4;border-radius:9px;font-size:14px;line-height:1.65}code{font-family:Consolas,monospace}blockquote{border-left:4px solid #7fa587;margin-left:0;padding:8px 18px;background:#e4eddf}details{padding:12px 16px;border:1px solid #ccd8cb;border-radius:9px;margin:14px 0;background:#fff}summary{cursor:pointer;color:#206c4a;font-weight:600}.scope{font-size:13px;color:#56675a;background:#f4ead7;border-radius:7px;padding:10px 15px;margin:20px 0}.mermaid{overflow-x:auto;background:white;border-radius:8px;padding:14px}footer{border-top:1px solid #d4ddd3;margin-top:35px;padding-top:14px;color:#56675a;font-size:13px}:focus-visible{outline:3px solid #986719;outline-offset:3px}@media(max-width:600px){main{padding:18px 17px 40px}body{font-size:15px}h1{font-size:26px}}
"""


def is_private(target: str) -> bool:
    raw = unquote(target)
    return raw.startswith(("thread://", "file://", "codex://")) or bool(re.match(r"^[A-Za-z]:[/\\]", raw))


def sanitize(text: str, source: Path) -> str:
    def link(match: re.Match) -> str:
        label, target = match.group(1), match.group(2)
        if is_private(target):
            return label + "（私人资料，未公开）"
        if "://" not in target and not target.startswith("#"):
            raw = unquote(target.split("#")[0])
            resolved = (source.parent / raw).resolve()
            relative = os.path.relpath(resolved, ROOT).replace("\\", "/")
            if relative == "学习地图.html":
                return "[" + label + "](" + target.replace("学习地图.html", "index.html") + ")"
            if relative.startswith(PRIVATE_PREFIXES) or relative in {"学习偏好.md", "AGENTS.md"}:
                return label + "（本地维护资料，未公开）"
        return match.group(0)

    text = re.sub(r"\[([^\]\n]+)\]\(([^)\n]+)\)", link, text)
    text = re.sub(r"(?i)\b[A-Z]:[/\\][^\s`<>\"|，；。！？）)]*", "[本机路径已省略]", text)
    text = re.sub(r"\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b", "[私人记录标识已省略]", text, flags=re.I)
    return text


def page_link(target: str) -> str:
    if "://" in target or target.startswith(("#", "data:")):
        return target
    raw, sep, fragment = unquote(target).partition("#")
    raw = raw.replace("\\", "/")
    if raw == "学习地图.html":
        raw = "index.html"
    if raw == "学习偏好.md":
        raw = "关于这个学习库.md"
    if any(prefix in raw for prefix in PRIVATE_PREFIXES):
        raw = "核验与限制.md"
    if raw.endswith(".md"):
        raw = raw[:-3] + ".html"
    return quote(raw, safe="/.-_") + (sep + fragment if sep else "")


def rel(from_path: Path, target: Path) -> str:
    return quote(os.path.relpath(target, from_path.parent).replace("\\", "/"), safe="/.-_")


def render(source: Path) -> None:
    text = source.read_text(encoding="utf-8")
    title = next((line[2:] for line in text.splitlines() if line.startswith("# ")), source.stem)
    body = markdown.markdown(text, extensions=["fenced_code", "tables", "sane_lists", "toc"])
    body = re.sub(r'href="([^"]+)"', lambda m: 'href="' + page_link(html.unescape(m[1])) + '"', body)
    nav = f'<nav><a href="{rel(source, DOCS / "index.html")}">学习地图</a><a href="{rel(source, DOCS / "首页.html")}">文字首页</a><a href="{rel(source, DOCS / "学习路线.html")}">学习路线</a></nav>'
    scope = '<p class="scope">公开学习笔记。项目案例来自作者历史记录，并非公开可复现的测试报告；私人聊天、学习画像及本机文件不随站点发布。请结合文中适用范围与官方来源判断。</p>'
    script = """<script type="module">
const blocks=[...document.querySelectorAll('code.language-mermaid')];
if(blocks.length){try{const {default:mermaid}=await import('https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs');mermaid.initialize({startOnLoad:false,securityLevel:'strict',theme:'neutral'});const nodes=blocks.map(block=>{const div=document.createElement('div');div.className='mermaid';div.textContent=block.textContent;block.parentElement.replaceWith(div);return div;});await mermaid.run({nodes});}catch(error){const message=document.createElement('p');message.className='scope';message.textContent='结构图资源暂未成功加载；正文解释仍可阅读。';document.querySelector('main').append(message);}}
</script>"""
    output = f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} · 学习笔记</title><style>{CSS}</style></head><body><main>{nav}{scope}<article>{body}</article><footer>从实际问题出发，区分知识、假设与证据。</footer></main>{script}</body></html>'
    source.with_suffix(".html").write_text(output, encoding="utf-8")


def export_local() -> None:
    sources = [*sorted((ROOT / "01-知识库").rglob("*.md")), *sorted((ROOT / "02-回顾").glob("*.md")), ROOT / "学习路线.md"]
    if not sources or not (ROOT / "学习地图.html").is_file():
        raise SystemExit("未找到原始学习库；其他设备请使用默认构建模式。")
    for source in sources:
        if source.is_symlink() or not source.resolve().is_relative_to(ROOT):
            raise SystemExit("拒绝导出目录外或符号链接内容。")
        dest = DOCS / source.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(sanitize(source.read_text(encoding="utf-8-sig"), source), encoding="utf-8")

    about = """# 关于这个学习库

这是从实际问题中逐步整理的中文学习笔记，当前涵盖 Codex、Git、Python 和软件工程。重点是理解概念、提出具体要求，以及用证据判断结果。

每篇笔记区分建议掌握和用时查阅，并提供例子、回顾问题及可公开访问的来源。知识和平台行为会变化，发现问题欢迎提交 Issue，附上具体段落和可核查证据。

私人学习画像、原始聊天、助手权限和本机配置不公开。公开笔记中的历史实践仅代表作者当时观察，不能据此保证你的环境有相同结果。
"""
    limits = """# 核验与限制

笔记保留了知识与事实边界：合理设计不等于实现已经完整，接口跑通不等于任务正确，测试通过不等于真实体验提升。

- 模型上下文大小和压缩配置需按实际服务提供方及工具版本核对，不能照抄未经验证的数值。
- 超时兜底返回不证明子进程已经退出，实际残留需要运行证据或隔离故障实验。
- 命名、读取和跨聊天接口依赖当前版本与权限，不能把某次本机成功泛化到所有环境。
- 图解、学习卡和阅读顺序是辅助理解的安排，不代表学习效果已经得到验证。

官方文档与固定版本源码链接保留在各篇笔记中。私人项目源码与聊天没有公开，因此不能把作者的历史观察当作可公开复现的验证报告。
"""
    (DOCS / "关于这个学习库.md").write_text(about, encoding="utf-8")
    (DOCS / "核验与限制.md").write_text(limits, encoding="utf-8")
    links = [f'- [{p.stem}]({quote(p.relative_to(DOCS).as_posix(), safe="/.-_")})' for p in sorted((DOCS / "01-知识库").rglob("*.md"))]
    home = '# 学习笔记\n\n先理解概念与结构，再看例子、提出要求和检查证据。\n\n[学习地图](index.html) · [学习路线](学习路线.md) · [回顾练习](02-回顾/第一次回顾.md) · [核验与限制](核验与限制.md)\n\n## 知识目录\n\n' + '\n'.join(links) + '\n\n[关于这个学习库](关于这个学习库.md)\n'
    (DOCS / "首页.md").write_text(home, encoding="utf-8")

    board = (ROOT / "学习地图.html").read_text(encoding="utf-8")
    board = board.replace('href="学习偏好.md">学习偏好', 'href="关于这个学习库.md">关于笔记')
    board = re.sub(r'href="([^"]+)"', lambda m: 'href="' + page_link(m[1]) + '"', board)
    board = board.replace("查看复核依据 ↗", "了解核验边界 ↗")
    (DOCS / "index.html").write_text(board, encoding="utf-8")
    viz = DOCS / "可视化"
    viz.mkdir(exist_ok=True)
    example = (ROOT / "可视化/验收证据分层.html").read_text(encoding="utf-8")
    example = re.sub(r'href="([^"]+)"', lambda m: 'href="' + page_link(m[1]) + '"', example)
    (viz / "验收证据分层.html").write_text(example, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-local", action="store_true", help="导出本机原稿；先合并其他设备的公开笔记改动")
    args = parser.parse_args()
    DOCS.mkdir(exist_ok=True)
    if args.from_local:
        export_local()
    sources = sorted(DOCS.rglob("*.md"))
    if not sources:
        raise SystemExit("没有公开 Markdown 可构建。")
    for source in sources:
        render(source)
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"已生成 {len(sources)} 篇网页；公开目录：docs")


if __name__ == "__main__":
    main()
