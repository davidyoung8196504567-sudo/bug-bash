"""Each guard is proved to work by planting a violation (IVRSIM_DESIGN.md, section 6).

This file is exempt from the guards, because it holds the planted violations.
"""
import subprocess

import pytest

import guards

VOCABULARY = ["not dead yet", "ndy", "pension"]


def names(violations):
    return [v.guard for v in violations]


# --- guard 1: engine-is-generic --------------------------------------------

@pytest.mark.parametrize("line", [
    'GROUP = "NDY_Hours"',
    "def pension_amount(): ...",
    "# the Not Dead Yet line needs this",
    'SERVICE = "not_dead_yet"',
    "class PensionerLookup: ...",
])
def test_engine_source_with_service_vocabulary_is_caught(line):
    found = guards.run_guards({"ivrsim/engine.py": f"x = 1\n{line}\n"}, VOCABULARY)
    assert names(found) == ["engine-is-generic"]
    assert found[0].line == 2


def test_generic_engine_source_passes():
    source = 'def evaluate_schedule_group(group, when):\n    return "open"  # handy, suspension\n'
    assert guards.run_guards({"ivrsim/engine.py": source}, VOCABULARY) == []


def test_packs_and_tests_inside_the_engine_directory_may_name_the_service():
    files = {
        "ivrsim/packs/ndy/flows/main.yaml": "group: NDY_Hours\n",
        "ivrsim/tests/test_trace.py": 'GROUP = "NDY_Hours"\n',
        "ivrsim/test_trace.py": 'GROUP = "NDY_Hours"\n',
        "ivrsim/FORMATS.md": "Example: `NDY_Hours`\n",
        "bugbash/harness.py": 'PACK = "ndy"\n',
    }
    assert guards.run_guards(files, VOCABULARY) == []


# --- guard 2: pack-is-fictitious -------------------------------------------

@pytest.mark.parametrize("text", [
    "transfer: 416-555-0142",
    "transfer: (416) 555-0199",
    "transfer: +1 613 555 0100",
    "transfer: 16135550123",
    "say: call 555-0111",
])
def test_fictitious_numbers_pass(text):
    assert guards.run_guards({"packs/x/config/queues.yaml": text}, []) == []


@pytest.mark.parametrize("text", [
    "transfer: 416-555-0242",        # 555, but outside 01xx
    "transfer: (416) 867-5309",
    "transfer: +1 613 992 4211",
    "transfer: 6139924211",
    "transfer: 1-800-622-6232",
    "say: call 867-5309",
    "say: call 867 5309",
])
def test_real_looking_numbers_are_caught(text):
    found = guards.run_guards({"packs/x/config/queues.yaml": text}, [])
    assert names(found) == ["pack-is-fictitious"]
    assert "telephone number" in found[0].message


@pytest.mark.parametrize("text", [
    "id: 123456789",
    "id: 123 456 789",
    "id: 123-456-789",
    "id: 123-45-6789",
    'id: "046454286"',
])
def test_nine_digit_identifier_shapes_are_caught(text):
    found = guards.run_guards({"packs/x/config/tables.yaml": text}, [])
    assert names(found) == ["pack-is-fictitious"]
    assert "9-digit" in found[0].message


@pytest.mark.parametrize("text", [
    'open: {mon-fri: "08:30-16:30"}',
    'holidays: ["2026-12-25", "2026-12-26"]',
    "Clients: {'000101': priority, '000202': standard}",
    "when: 2026-11-04T10:00:00-05:00",
    "digits: {min: 6, max: 6}",
    "run 42755855643 took 53s",
    "started: 1762790400",                       # a Unix time is not a phone number
    "sha: 4fa3e6a1234567890abcdef",
])
def test_ordinary_pack_content_is_not_flagged(text):
    assert guards.run_guards({"packs/x/config/schedules.yaml": text}, []) == []


def test_fictitious_check_covers_every_file_not_only_packs():
    found = guards.run_guards({"docs/spec.md": "Call 613-992-4211.\n"}, [])
    assert names(found) == ["pack-is-fictitious"]


# --- guard 3: catalogue-is-generic -----------------------------------------

@pytest.mark.parametrize("path", ["ivrsim/CATALOGUE.md", "catalogue.yaml", "docs/bug_catalog.md"])
def test_catalogue_with_service_vocabulary_is_caught(path):
    found = guards.run_guards({path: "holiday_drop: the pension line missed a holiday\n"}, VOCABULARY)
    assert names(found) == ["catalogue-is-generic"]


def test_generic_catalogue_passes():
    text = "holiday_drop: remove one holiday (holiday calendar not updated)\n"
    assert guards.run_guards({"ivrsim/CATALOGUE.md": text}, VOCABULARY) == []


# --- guard 4: engine-is-standalone -----------------------------------------

@pytest.mark.parametrize("line", [
    "import bugbash",
    "import bugbash.grader as g",
    "from bugbash import grader",
    "from bugbash.grader import grade",
    'importlib.import_module("bugbash.grader")',
    '__import__("bugbash")',
])
def test_engine_importing_bugbash_is_caught(line):
    source = f"import importlib\n\ndef f():\n    {line}\n"
    found = guards.run_guards({"ivrsim/runner.py": source}, [])
    assert names(found) == ["engine-is-standalone"]
    assert found[0].line == 4


def test_engine_imports_that_are_allowed():
    source = "import ast\nfrom . import loader\nfrom .session import IvrSession\nimport bugbashlike\n"
    assert guards.run_guards({"ivrsim/runner.py": source}, []) == []


def test_bugbash_may_import_ivrsim():
    assert guards.run_guards({"bugbash/harness.py": "import ivrsim\nimport bugbash.grader\n"}, []) == []


def test_unparseable_engine_source_is_a_violation_not_a_pass():
    found = guards.run_guards({"ivrsim/broken.py": "def f(:\n"}, [])
    assert names(found) == ["engine-is-standalone"]


# --- private terms ---------------------------------------------------------

def test_private_term_is_caught_in_any_file():
    files = {"JOURNAL.md": "Seen on the Acme-Widgets project.\n", "README.md": "Nothing here.\n"}
    found = guards.run_guards(files, [], private_terms=["acme widgets"])
    assert [(v.guard, v.path) for v in found] == [("private-terms", "JOURNAL.md")]


def test_the_private_terms_file_itself_is_refused():
    found = guards.run_guards({guards.LOCAL_TERMS_FILE: "acme widgets\n"}, [])
    assert names(found) == ["private-terms"]


# --- the repository as it stands -------------------------------------------

def test_vocabulary_file_has_terms():
    terms = guards.load_terms(guards.REPO / guards.VOCABULARY_FILE)
    assert "ndy" in terms and not any(t.startswith("#") for t in terms)


def test_this_repository_passes_its_own_guards():
    vocabulary = guards.load_terms(guards.REPO / guards.VOCABULARY_FILE)
    files = guards.working_tree_files(guards.REPO)
    assert "tools/guards.py" in files
    assert guards.run_guards(files, vocabulary) == []


# --- the command line and the hook, in a throwaway repository --------------

def git(repo, *args, check=True):
    return subprocess.run(
        ["git", "-c", "user.name=guard-test", "-c", "user.email=guard-test@example.invalid", *args],
        cwd=repo, check=check, capture_output=True, text=True,
    )


def run_guards_cli(repo, *args):
    import sys
    return subprocess.run([sys.executable, str(guards.REPO / "tools" / "guards.py"), *args],
                          cwd=repo, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    return tmp_path


BAD = "transfer: 613-992-4211\n"
GOOD = "transfer: 613-555-0142\n"


def test_staged_mode_checks_the_index_not_the_working_tree(repo):
    config = repo / "queues.yaml"
    config.write_text(BAD)
    git(repo, "add", "queues.yaml")
    config.write_text(GOOD)                      # fixed on disk, but not staged
    result = run_guards_cli(repo, "--staged")
    assert result.returncode == 1 and "pack-is-fictitious" in result.stdout

    git(repo, "add", "queues.yaml")
    config.write_text(BAD)                       # broken on disk, but not staged
    assert run_guards_cli(repo, "--staged").returncode == 0
    assert run_guards_cli(repo).returncode == 1  # the full scan reads the disk


def test_private_terms_are_read_from_the_checked_repository(repo):
    (repo / guards.LOCAL_TERMS_FILE).write_text("acme widgets\n")
    (repo / "notes.md").write_text("From the Acme Widgets job.\n")
    git(repo, "add", "notes.md")
    result = run_guards_cli(repo, "--staged")
    assert result.returncode == 1 and "private-terms" in result.stdout


def test_pre_commit_hook_blocks_a_bad_commit_and_allows_a_good_one(repo):
    git(repo, "config", "core.hooksPath", str(guards.REPO / "tools" / "hooks"))
    config = repo / "queues.yaml"

    config.write_text(BAD)
    git(repo, "add", "queues.yaml")
    blocked = git(repo, "commit", "-q", "-m", "bad", check=False)
    assert blocked.returncode != 0
    assert "pack-is-fictitious" in blocked.stdout + blocked.stderr
    assert git(repo, "rev-parse", "--verify", "-q", "HEAD", check=False).returncode != 0

    config.write_text(GOOD)
    git(repo, "add", "queues.yaml")
    assert git(repo, "commit", "-q", "-m", "good", check=False).returncode == 0
