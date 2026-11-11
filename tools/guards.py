#!/usr/bin/env python3
"""Repository guards (IVRSIM_DESIGN.md, section 6).

1. engine-is-generic      no service-specific vocabulary in ivrsim/ source
2. pack-is-fictitious     no telephone number outside the fictitious 555-01xx
                          range, and no 9-digit identifier shapes
3. catalogue-is-generic   guard 1 run over the bug catalogue
4. engine-is-standalone   the ivrsim package imports nothing from the
                          bugbash package (see below)
5. no-invisible-characters  no character a reader cannot see in any file:
                          control characters other than newline (so no tab
                          or carriage return), format characters such as
                          the zero-width space or byte-order mark, and any
                          space other than the plain one (such as the
                          no-break space). Write them as escapes instead.

The bug-bash repository holds two Python packages. bugbash/ is the harness
(tasks, mutants, grading, scoring, walkers); ivrsim/ is the engine, a generic
IVR simulator that knows nothing about bug bashes or scores. The harness may
import the engine, never the other way round (IVRSIM_DESIGN.md, sections 2 E
and 2 G), because:
  - ivrsim must work installed on its own: BLINDMAN depends on it alone, the
    browser version loads it alone through Pyodide, and it may later move to
    its own repository;
  - rewards stay in the harness, so the engine cannot behave differently
    because it is being graded.

Inside this repository a wrong-way import works and every test passes,
because both packages sit side by side. It fails only once ivrsim runs alone:
    # ivrsim/runner.py
    from bugbash.grader import grade
    -> ModuleNotFoundError: No module named 'bugbash'
Guard 4 rejects that line when it is committed:
    ivrsim/runner.py:2: [engine-is-standalone] imports 'bugbash.grader'

A fifth check, private-terms, applies the terms in .guards-local.txt to every
file. That file is ignored by git, because a public list of real organisation
names would itself be the leak.

Usage:
    python tools/guards.py            check every file in the working tree
    python tools/guards.py --staged   check what is staged (the pre-commit hook)

Standard library only, so the hook needs nothing installed.
"""
from __future__ import annotations

import ast
import re
import unicodedata
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parent.parent
VOCABULARY_FILE = "tools/guard_vocabulary.txt"
LOCAL_TERMS_FILE = ".guards-local.txt"

ENGINE_DIR = "ivrsim"          # the engine package
BANNED_IMPORT = "bugbash"      # the harness package (not the repository name)
# Inside the engine directory, these are not engine source.
NOT_ENGINE_DIRS = {"packs", "tests"}
MAX_BYTES = 2_000_000

# Files the content guards skip, each for a stated reason.
EXEMPT = {
    "tests/test_guards.py": "plants the violations that prove the guards work",
    "tools/guard_vocabulary.txt": "is the vocabulary",
    "tools/docs_pdf/package-lock.json": "generated; integrity hashes",
    "docs/pdf/SOURCES.json": "generated; content hashes",
}


@dataclass(frozen=True)
class Violation:
    guard: str
    path: str
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: [{self.guard}] {self.message}"


# --- which guard covers which file -----------------------------------------

def is_engine_source(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return (
        len(parts) > 1
        and parts[0] == ENGINE_DIR
        and path.endswith(".py")
        and not NOT_ENGINE_DIRS.intersection(parts[1:-1])
        and not parts[-1].startswith("test_")
    )


def is_catalogue(path: str) -> bool:
    return "catalog" in PurePosixPath(path).name.lower()  # also "catalogue"


# --- guards 1 and 3: vocabulary --------------------------------------------

def parse_terms(text: str) -> list[str]:
    terms = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            terms.append(line)
    return terms


def term_pattern(terms: list[str]) -> re.Pattern[str] | None:
    if not terms:
        return None
    alternatives = [
        r"[\s_-]*".join(re.escape(word) for word in term.split()) for term in terms
    ]
    return re.compile(r"(?<![A-Za-z])(?:" + "|".join(alternatives) + ")", re.IGNORECASE)


def check_terms(guard: str, path: str, text: str, terms: list[str]) -> list[Violation]:
    pattern = term_pattern(terms)
    if pattern is None:
        return []
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        for match in pattern.finditer(line):
            found.append(Violation(guard, path, number, f"service-specific term {match.group(0)!r}"))
    return found


# --- guard 2: telephone numbers and 9-digit identifiers --------------------

# North American numbers: area code and exchange both start 2-9.
PHONE_10 = re.compile(
    r"(?<![A-Za-z0-9-])(?:\+?1[\s.-]?)?\(?([2-9]\d\d)\)?[\s.-]?([2-9]\d\d)[\s.-]?(\d{4})(?![A-Za-z0-9-])"
)
PHONE_7 = re.compile(r"(?<![A-Za-z0-9-])([2-9]\d\d)[\s.-](\d{4})(?![A-Za-z0-9-])")
NINE_DIGIT = re.compile(
    r"(?<![A-Za-z0-9-])(?:\d{9}|\d{3}[ -]\d{3}[ -]\d{3}|\d{3}-\d{2}-\d{4})(?![A-Za-z0-9-])"
)


def is_fictitious(exchange: str, line_number: str) -> bool:
    """555-0100 to 555-0199 is reserved for fiction in every area code."""
    return exchange == "555" and line_number.startswith("01")


def check_fictitious(path: str, text: str) -> list[Violation]:
    guard = "pack-is-fictitious"
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        def phone10(match: re.Match[str]) -> str:
            if not is_fictitious(match.group(2), match.group(3)):
                found.append(Violation(guard, path, number,
                                       f"telephone number {match.group(0)!r} is outside 555-01xx"))
            return " " * len(match.group(0))

        def phone7(match: re.Match[str]) -> str:
            if not is_fictitious(match.group(1), match.group(2)):
                found.append(Violation(guard, path, number,
                                       f"telephone number {match.group(0)!r} is outside 555-01xx"))
            return " " * len(match.group(0))

        # Blank out each number once reported, so one number gives one report.
        rest = PHONE_7.sub(phone7, PHONE_10.sub(phone10, line))
        for match in NINE_DIGIT.finditer(rest):
            found.append(Violation(guard, path, number,
                                   f"9-digit identifier shape {match.group(0)!r}"))
    return found


# --- guard 4: the engine stands alone --------------------------------------

def _is_banned(module: str | None) -> bool:
    return bool(module) and (module == BANNED_IMPORT or module.startswith(BANNED_IMPORT + "."))


def check_imports(path: str, text: str) -> list[Violation]:
    guard = "engine-is-standalone"
    try:
        tree = ast.parse(text)
    except SyntaxError as error:
        return [Violation(guard, path, error.lineno or 1, "cannot be parsed, so its imports cannot be checked")]
    found = []
    for node in ast.walk(tree):
        modules: list[str | None] = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            modules = [node.module]
        elif isinstance(node, ast.Call):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if name in {"__import__", "import_module"} and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    modules = [first.value]
        for module in modules:
            if _is_banned(module):
                found.append(Violation(guard, path, node.lineno, f"imports {module!r}"))
    return found


# --- guard 5: no invisible characters --------------------------------------

def is_invisible(char: str) -> bool:
    if char == "\n":
        return False
    category = unicodedata.category(char)
    return category in {"Cc", "Cf", "Zl", "Zp"} or (category == "Zs" and char != " ")


def check_invisible(path: str, text: str) -> list[Violation]:
    found = []
    for number, line in enumerate(text.split("\n"), 1):
        for column, char in enumerate(line, 1):
            if is_invisible(char):
                name = unicodedata.name(char, "control character")
                found.append(Violation("no-invisible-characters", path, number,
                                       f"column {column}: U+{ord(char):04X} {name}"))
    return found


# --- all guards over a set of files ----------------------------------------

def run_guards(files: dict[str, str], vocabulary: list[str],
               private_terms: list[str] | None = None) -> list[Violation]:
    """files maps a repository-relative POSIX path to the file's text."""
    found: list[Violation] = []
    for path in sorted(files):
        text = files[path]
        if path == LOCAL_TERMS_FILE:
            found.append(Violation("private-terms", path, 1,
                                   "this file must never be committed; it is in .gitignore"))
            continue
        if is_engine_source(path):
            found += check_terms("engine-is-generic", path, text, vocabulary)
            found += check_imports(path, text)
        if path in EXEMPT:
            continue
        if is_catalogue(path):
            found += check_terms("catalogue-is-generic", path, text, vocabulary)
        found += check_fictitious(path, text)
        found += check_invisible(path, text)
        found += check_terms("private-terms", path, text, private_terms or [])
    return found


def coverage(files: dict[str, str]) -> dict[str, int]:
    return {
        "engine source": sum(is_engine_source(p) for p in files),
        "catalogue": sum(is_catalogue(p) and p not in EXEMPT for p in files),
        "all text": sum(p not in EXEMPT for p in files),
    }


# --- reading files ---------------------------------------------------------

def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True).stdout


def _decode(data: bytes) -> str | None:
    if len(data) > MAX_BYTES or b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def working_tree_files(repo: Path) -> dict[str, str]:
    """Tracked files, plus untracked files that git does not ignore."""
    names = _git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    files = {}
    for name in filter(None, names.decode("utf-8").split("\0")):
        path = repo / name
        if path.is_file():
            text = _decode(path.read_bytes())
            if text is not None:
                files[name] = text
    return files


def staged_files(repo: Path) -> dict[str, str]:
    """The staged content of every file added or changed in the index."""
    names = _git(repo, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    files = {}
    for name in filter(None, names.decode("utf-8").split("\0")):
        text = _decode(_git(repo, "show", f":{name}"))
        if text is not None:
            files[name] = text
    return files


def load_terms(path: Path) -> list[str]:
    return parse_terms(path.read_text(encoding="utf-8")) if path.is_file() else []


def main(argv: list[str]) -> int:
    staged = "--staged" in argv
    repo = Path(_git(Path.cwd(), "rev-parse", "--show-toplevel").decode("utf-8").strip())
    # The vocabulary comes from beside this script, so the hook works from any
    # repository; the private terms belong to the repository being checked.
    vocabulary = load_terms(REPO / VOCABULARY_FILE)
    private_terms = load_terms(repo / LOCAL_TERMS_FILE)
    files = staged_files(repo) if staged else working_tree_files(repo)
    violations = run_guards(files, vocabulary, private_terms)
    for violation in violations:
        print(violation)
    counts = ", ".join(f"{count} {kind}" for kind, count in coverage(files).items())
    scope = "staged files" if staged else "files"
    print(f"guards: {len(violations)} violation(s). Checked {scope}: {counts}; "
          f"{len(vocabulary)} vocabulary term(s), {len(private_terms)} private term(s).")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
