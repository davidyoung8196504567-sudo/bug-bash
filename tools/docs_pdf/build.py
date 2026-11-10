"""Render the plan and design documents to PDF.

For each Markdown file listed in docs.txt:
1. draw each ```mermaid block to a PNG with mermaid-cli;
2. point relative links at the file on GitHub, so they work in the PDF;
3. convert to HTML with pandoc, then print to PDF with headless Chrome.

A PDF is rebuilt only when its source or this tool changes. The hashes are
kept in docs/pdf/SOURCES.json, so an unchanged document keeps its old PDF and
does not add a new binary to the history.

Usage: python tools/docs_pdf/build.py [--force]
Needs: pandoc, node, Chrome (CHROME_PATH), and `npm ci` in tools/docs_pdf.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = Path(__file__).resolve().parent
ROOT = TOOL.parents[1]
OUT = ROOT / "docs" / "pdf"
MERMAID = re.compile(r"^```mermaid\n(.*?)^```\n", re.S | re.M)
LINK = re.compile(r"(\]\()([^)#\s]+)((?:#[^)\s]*)?\))")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def repo_url() -> str:
    if os.environ.get("GITHUB_REPOSITORY"):
        return f"https://github.com/{os.environ['GITHUB_REPOSITORY']}"
    url = git("remote", "get-url", "origin")
    url = re.sub(r"^git@github\.com:", "https://github.com/", url)
    return url.removesuffix(".git")


def chrome() -> str:
    for c in (os.environ.get("CHROME_PATH"),
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/usr/bin/google-chrome", "/usr/bin/chromium"):
        if c and Path(c).exists():
            return c
    sys.exit("Chrome not found: set CHROME_PATH")


def tool_hash() -> str:
    h = hashlib.sha256()
    for name in ("build.py", "print.mjs", "style.css", "package-lock.json"):
        h.update((TOOL / name).read_bytes())
    return h.hexdigest()


def rewrite_links(text: str, src: Path, base: str) -> str:
    def fix(m: re.Match) -> str:
        target = m.group(2)
        if re.match(r"^[a-z]+:", target) or target.startswith("/"):
            return m.group(0)
        resolved = (src.parent / target).resolve()
        try:
            rel = resolved.relative_to(ROOT).as_posix()
        except ValueError:
            return m.group(0)
        kind = "tree" if resolved.is_dir() else "blob"
        return f"{m.group(1)}{base}/{kind}/main/{rel}{m.group(3)}"
    return LINK.sub(fix, text)


def render(src: Path, pdf: Path, env: dict, work: Path) -> None:
    text = src.read_text(encoding="utf-8")
    pcfg = work / "puppeteer.json"
    pcfg.write_text(json.dumps({"executablePath": env["CHROME_PATH"], "args": ["--no-sandbox"]}))
    mmdc = TOOL / "node_modules" / ".bin" / "mmdc"

    def draw(m: re.Match, n=[0]) -> str:
        n[0] += 1
        mmd, png = work / f"{src.stem}-{n[0]}.mmd", work / f"{src.stem}-{n[0]}.png"
        mmd.write_text(m.group(1), encoding="utf-8")
        subprocess.run([str(mmdc), "-q", "-p", str(pcfg), "-i", str(mmd), "-o", str(png),
                        "-s", "3", "-b", "white"], check=True, env=env)
        return f"![]({png.as_posix()})\n"

    text = rewrite_links(text, src, repo_url())  # before the diagrams go in
    text = MERMAID.sub(draw, text)
    md = work / f"{src.stem}.md"
    md.write_text(text, encoding="utf-8")
    title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), src.stem)
    html = work / f"{src.stem}.html"
    subprocess.run(["pandoc", "-f", "gfm", "-t", "html5", "--standalone", "--embed-resources",
                    "--css", str(TOOL / "style.css"), "--metadata", f"pagetitle={title}",
                    "--resource-path", str(work), "-o", str(html), str(md)], check=True)
    rel = src.relative_to(ROOT).as_posix()
    sha = git("log", "-1", "--format=%h", "--", rel) or "uncommitted"
    date = git("log", "-1", "--format=%cs", "--", rel) or ""
    footer = f"{rel} · {sha} {date}".strip()
    subprocess.run(["node", str(TOOL / "print.mjs"), str(html), str(pdf), footer],
                   check=True, env=env, cwd=TOOL)



def main() -> None:
    force = "--force" in sys.argv
    env = dict(os.environ, CHROME_PATH=chrome(), PUPPETEER_SKIP_DOWNLOAD="1")
    OUT.mkdir(parents=True, exist_ok=True)
    state_file = OUT / "SOURCES.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    tools = tool_hash()
    docs = [l.strip() for l in (TOOL / "docs.txt").read_text().splitlines()
            if l.strip() and not l.startswith("#")]
    built = 0
    with tempfile.TemporaryDirectory() as tmp:
        for rel in docs:
            src = ROOT / rel
            pdf = OUT / f"{src.stem}.pdf"
            key = hashlib.sha256(src.read_bytes() + tools.encode()).hexdigest()
            if not force and state.get(rel) == key and pdf.exists():
                print(f"unchanged  {rel}")
                continue
            render(src, pdf, env, Path(tmp))
            state[rel] = key
            built += 1
            print(f"built      {rel} -> {pdf.relative_to(ROOT)}")
    for rel in list(state):
        if rel not in docs:
            del state[rel]
    state_file.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    print(f"{built} PDF(s) built")


if __name__ == "__main__":
    main()
