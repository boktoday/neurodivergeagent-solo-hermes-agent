"""Repo integrity tests for the Individual Agent (neurodivergeagent-solo).

Guards against the failure modes that accumulate when skills are added or ported
in from the companion family repo: broken routing, stale skill counts, split
folder filenames, leftover personal paths, credential scraping, and artifacts
that quietly acquire a network dependency.

Run from the repository root:

    python -m unittest discover -s tests -v

Zero third-party dependencies. Only the standard library is used, so this runs
on a bare Python install with no venv and no pip step.

Two conventions to understand before editing this file
------------------------------------------------------

**Self-activating skips.** Some tests cover scripts that do not exist yet
(`install.py`, `capacity_mode.py`, `redact_doc.py`, `search-ndis.py`). They use
`skipUnless` on the file's existence, so the suite is honest today and those
tests come alive automatically the moment the script lands. Do not delete them.

**expectedFailure is a debt marker, not a rubber stamp.** A test decorated
`@unittest.expectedFailure` encodes a rule the repository currently violates.
It reports as "expected failure" while the bug exists. The moment somebody fixes
the underlying issue the test flips to an *unexpected success*, which unittest
reports as a FAILURE — that is the signal to delete the decorator and promote
the test to a permanent guard. Never remove one without fixing its cause.

Each marker names the task that will pay the debt.

Not covered here (cannot be tested from inside the tree)
--------------------------------------------------------
- The GitHub repo description, topics, and release notes. As of this writing the
  description still reads "eleven specialist skills". Check with:
      curl -s https://api.github.com/repos/boktoday/neurodivergeagent-solo-hermes-agent
- Whether the agent actually behaves correctly. This suite tests internals only.
"""

import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
SCRIPTS = REPO / "scripts"
ARTIFACTS = REPO / "templates" / "artifacts"
SHARED = REPO / "shared"
SCHEDULES = REPO / "schedules"

EXPECTED_SKILL_COUNT = 15
REQUIRED_FRONTMATTER = ("name:", "description:", "version:")
FULL_FRONTMATTER = ("author:", "license:", "platforms:", "related_skills:")

# lesson-chunks.html is a shipped React bundle that deliberately talks to
# openrouter.ai. It is the one artifact exempt from the offline rule.
NETWORK_EXEMPT_ARTIFACTS = {"lesson-chunks.html"}

FAMILY_REPO_LEFTOVERS = (
    "~/neurofamily",
    "Family Navigator",
    "Education Advocate",
    "Parent Companion",
    "Routine Architect",
    "NeuroFamily agent project",
    "family support use",
)

MINIMISING_WORDS = ("simply ", "obviously ")

# Placeholder paths that are fine in documentation examples.
PATH_PLACEHOLDERS = {"yourname", "username", "user", "name", "<user>", "%username%"}


def read(rel):
    """Read a repo-relative text file."""
    return (REPO / rel).read_text(encoding="utf-8", errors="replace")


def skill_slugs():
    """Every directory under skills/, sorted."""
    return sorted(p.name for p in SKILLS.iterdir() if p.is_dir())


def table_rows(text):
    """Markdown table rows only, so prose cannot satisfy a registry check."""
    return [line for line in text.splitlines() if line.strip().startswith("|")]


def listed_in_table(slug, text):
    """True when every token of the slug appears in order inside one table row.

    Docs use display names, not slugs: `Energy and Burnout Guardian`, not
    `energy-burnout-guardian`. A slug-only check reports those as missing and
    produces false alarms, so match the token sequence within a single row.
    """
    pattern = r"\b" + r"[\s\w,'\-]{0,14}?".join(map(re.escape, slug.split("-"))) + r"\b"
    return any(re.search(pattern, row, re.IGNORECASE) for row in table_rows(text))


def tracked_files(suffixes, exclude=()):
    """Repo files by extension, skipping .git, caches and the named paths."""
    out = []
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        rel = path.relative_to(REPO).as_posix()
        if any(part in rel for part in (".git/", "__pycache__/", "tests/")):
            continue
        if rel in exclude:
            continue
        out.append(rel)
    return sorted(out)


def run_script(name, *args, stdin=None, cwd=None):
    """Run a repo script with the current interpreter (never a bare python3)."""
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=cwd or str(REPO),
    )


class SkillRegistryTests(unittest.TestCase):
    """Every skill is discoverable, routed, and self-describing."""

    def test_every_skill_directory_has_a_skill_md(self):
        missing = [s for s in skill_slugs() if not (SKILLS / s / "SKILL.md").is_file()]
        self.assertEqual([], missing, "skill directories without a SKILL.md: %s" % missing)

    def test_skill_count_matches_the_documented_number(self):
        self.assertEqual(
            EXPECTED_SKILL_COUNT,
            len(skill_slugs()),
            "skills/ holds %d directories; if this is a deliberate addition, "
            "update EXPECTED_SKILL_COUNT and every document that states the count."
            % len(skill_slugs()),
        )

    def test_every_skill_has_frontmatter(self):
        """name, description and version are non-negotiable on every skill."""
        broken = {}
        for slug in skill_slugs():
            text = read("skills/%s/SKILL.md" % slug)
            if not text.startswith("---"):
                broken[slug] = "no YAML frontmatter block"
                continue
            header = text.split("---")[1]
            missing = [key for key in REQUIRED_FRONTMATTER if key not in header]
            if "name:" in header and ("name: %s" % slug) not in header:
                missing.append("name does not match directory")
            if missing:
                broken[slug] = missing
        self.assertEqual({}, broken, "skills with unusable frontmatter: %s" % broken)

    def test_every_skill_is_routed_in_readme_and_agents(self):
        """A skill nobody is routed to is a skill nobody can reach."""
        for doc in ("README.md", "AGENTS.md"):
            text = read(doc)
            missing = [slug for slug in skill_slugs() if not listed_in_table(slug, text)]
            self.assertEqual([], missing, "%s does not list: %s" % (doc, missing))

    def test_team_lists_are_identical_across_all_skills(self):
        """Every skill's '## The team' footer names every skill, identically."""
        slugs = skill_slugs()
        broken = {}
        for slug in slugs:
            text = read("skills/%s/SKILL.md" % slug)
            if "## The team" not in text:
                broken[slug] = "no '## The team' section"
                continue
            team = text.split("## The team")[-1]
            absent = [other for other in slugs if other not in team]
            if absent:
                broken[slug] = absent
        self.assertEqual({}, broken, "incomplete team lists: %s" % broken)

    def test_primary_documents_agree_on_the_count(self):
        """README, AGENTS.md and profile.yaml must agree on 'fifteen'."""
        stale = {}
        for doc in ("README.md", "AGENTS.md", "profile.yaml"):
            text = read(doc).lower()
            wrong = [
                word
                for word in ("eleven", "twelve", "thirteen", "fourteen", "sixteen")
                if word in text
            ]
            if wrong:
                stale[doc] = wrong
        self.assertEqual({}, stale, "documents stating a stale skill count: %s" % stale)

    def test_every_skill_has_full_frontmatter(self):
        """Every skill carries the same metadata, so tooling can rely on it."""
        broken = {}
        for slug in skill_slugs():
            header = read("skills/%s/SKILL.md" % slug).split("---")[1]
            missing = [key for key in FULL_FRONTMATTER if key not in header]
            if missing:
                broken[slug] = missing
        self.assertEqual({}, broken, "skills missing standard frontmatter keys: %s" % broken)

    def test_roadmap_states_the_current_skill_count(self):
        """ROADMAP must name the current count, not only a past release's.

        "Eleven skills" appears legitimately in the v1.0.0 shipped history and is
        left alone: rewriting a release record to satisfy a grep would be false.
        What matters is that the document also states the current position.
        """
        text = read("ROADMAP.md").lower()
        self.assertIn(
            "fifteen",
            text,
            "ROADMAP.md states no current skill count, only historical ones",
        )


class FolderTests(unittest.TestCase):
    """~/myfolder/ filenames are canonical, complete and safely initialised."""

    def _documented_files(self):
        """Filenames listed in the 'Your folder' table of AGENTS.md."""
        section = read("AGENTS.md").split("## Your folder")[-1]
        return set(re.findall(r"`([a-z0-9-]+\.md)`", "\n".join(table_rows(section))))

    def test_setup_creates_every_documented_file(self):
        documented = self._documented_files()
        self.assertTrue(documented, "could not parse the folder table from AGENTS.md")
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script("setup-my-folder.py", "--target", tmp)
            self.assertEqual(0, result.returncode, "setup failed: %s" % result.stderr)
            created = {p.name for p in pathlib.Path(tmp).glob("*.md")}
        self.assertEqual(documented, created, "setup and AGENTS.md disagree on the folder contents")

    def test_setup_is_idempotent(self):
        """Running setup twice must never overwrite what the user has written."""
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(0, run_script("setup-my-folder.py", "--target", tmp).returncode)
            victim = pathlib.Path(tmp) / "wins.md"
            victim.write_text("a win I wrote myself", encoding="utf-8")
            self.assertEqual(0, run_script("setup-my-folder.py", "--target", tmp).returncode)
            self.assertEqual(
                "a win I wrote myself",
                victim.read_text(encoding="utf-8"),
                "setup overwrote an existing file, destroying user data",
            )

    def test_no_stale_work_or_health_filenames(self):
        """The short forms work.md and health.md must never come back.

        Templates ship as work-notes.md and health-notes.md. A skill that names
        the short form writes to a file setup never creates, so the folder
        silently splits: the user writes to one file and the agent reads another.
        """
        offenders = {}
        paths = list(SKILLS.rglob("*.md")) + list(SCHEDULES.rglob("*.md"))
        if (REPO / "docs").is_dir():
            paths += list((REPO / "docs").rglob("*.md"))
        paths += [REPO / name for name in ("AGENTS.md", "README.md", "INSTALL.md")]
        for path in paths:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            hits = re.findall(r"(?<![\w-])(work|health)\.md\b", text)
            if hits:
                offenders[path.relative_to(REPO).as_posix()] = sorted(set(hits))
        self.assertEqual({}, offenders, "stale folder filenames: %s" % offenders)

    def test_every_referenced_folder_file_has_a_template(self):
        """Every folder file a skill names must actually be created by setup.

        Otherwise the agent writes to a path that does not exist, and the user's
        notes vanish from the agent's view without any error being raised.
        """
        have = {p.name.replace(".template.md", ".md") for p in SHARED.glob("*.template.md")}
        referenced = set()
        for path in list(SKILLS.rglob("*.md")) + [REPO / "AGENTS.md"]:
            text = path.read_text(encoding="utf-8", errors="replace")
            referenced.update(re.findall(r"myfolder/([a-z0-9-]+\.md)", text))
        missing = sorted(referenced - have)
        self.assertEqual([], missing, "referenced but never initialised: %s" % missing)

    def test_no_ghost_folder_filenames(self):
        """Every bare .md filename a skill names must resolve to a real file.

        This is the generic form of the work.md bug: a skill that names a file
        nobody creates sends the agent to write somewhere the user never looks,
        and neither side raises an error. Bare names only; path-qualified
        references are covered by the template test above.
        """
        known = {p.name for p in SHARED.glob("*.template.md")}
        known |= {name.replace(".template.md", ".md") for name in known}
        ndis_docs = REPO / "shared" / "ndis" / "docs"
        if ndis_docs.is_dir():
            known |= {p.name for p in ndis_docs.glob("*.md")}
        known |= {
            "SKILL.md", "README.md", "CHANGELOG.md", "INSTALL.md",
            "AGENTS.md", "SOUL.md", "ROADMAP.md", "LICENSE.md",
        }
        ghosts = {}
        for path in list(SKILLS.rglob("*.md")) + list(SCHEDULES.rglob("*.md")):
            text = path.read_text(encoding="utf-8", errors="replace")
            named = set(re.findall(r"(?<![\w/.-])([a-z0-9-]+\.md)\b", text))
            unknown = sorted(name for name in named if name not in known)
            if unknown:
                ghosts[path.relative_to(REPO).as_posix()] = unknown
        self.assertEqual({}, ghosts, "skills naming files that do not exist: %s" % ghosts)

    def test_folder_templates_keep_their_sections(self):
        """A template that has lost its structure is worse than none at all.

        Checking for markers, not byte counts: length measures nothing useful.
        """
        expectations = {
            "admin.template.md": ("Open items", "Trial and renewal register", "Closed admin wins"),
            "dopamine-menu.template.md": ("Entrées", "Mains", "Sides", "Desserts"),
            "routines.template.md": ("\U0001F7E2", "\U0001F7E1", "\U0001F534"),
        }
        broken = {}
        for name, markers in expectations.items():
            path = SHARED / name
            if not path.is_file():
                broken[name] = ["file missing"]
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            absent = [marker for marker in markers if marker not in text]
            if absent:
                broken[name] = absent
        self.assertEqual({}, broken, "templates missing their sections: %s" % broken)


class DriftTests(unittest.TestCase):
    """Nothing from the family repo, no personal paths, no credential scraping."""

    def test_no_minimising_language_in_skills(self):
        offenders = {}
        for slug in skill_slugs():
            text = read("skills/%s/SKILL.md" % slug).lower()
            hits = [word.strip() for word in MINIMISING_WORDS if word in text]
            if hits:
                offenders[slug] = hits
        self.assertEqual({}, offenders, "minimising words in user-facing skills: %s" % offenders)

    def test_no_family_repo_references(self):
        """No text ported from the companion family repo may survive.

        The solo agent speaks to one adult. Leftover references to parents,
        family co-ordinators and the other repo's skill names misroute the
        agent and read as though the user is being addressed as somebody else.

        CHANGELOG.md is excluded on purpose: the history may name the repo it
        was ported from.
        """
        offenders = {}
        targets = (
            [rel for rel in tracked_files({".md"}) if rel.startswith(("docs/", "skills/"))]
            + ["README.md", "AGENTS.md", "scripts/fetch-ndis-pages.py", "scripts/ndis_watch.py"]
        )
        for rel in targets:
            try:
                text = read(rel)
            except FileNotFoundError:
                continue
            hits = [phrase for phrase in FAMILY_REPO_LEFTOVERS if phrase in text]
            if hits:
                offenders[rel] = hits
        self.assertEqual({}, offenders, "family-repo leftovers: %s" % offenders)

    def test_no_hardcoded_machine_paths(self):
        """No absolute home directory from a maintainer's machine may be committed.

        Someone else's machine must never be assumed. Browser caches, temp dirs
        and tool installs all resolve differently per user, so scripts ask the
        environment or use a documented default instead of guessing a path.
        """
        pattern = re.compile(r"[A-Za-z]:[/\\]Users[/\\]([A-Za-z0-9._-]+)[/\\]")
        offenders = {}
        for rel in tracked_files({".py", ".sh", ".md", ".yaml", ".html"}):
            for match in pattern.finditer(read(rel)):
                if match.group(1).lower() not in PATH_PLACEHOLDERS:
                    offenders.setdefault(rel, []).append(match.group(0))
        self.assertEqual({}, offenders, "hardcoded home paths: %s" % offenders)

    def test_no_credential_scraping_in_scripts(self):
        """No script may read a credential store or put a secret on a command line.

        Command-line arguments are visible to other processes and land in error
        output and logs. Credentials belong to the credential helper, `gh
        auth setup-git`, an SSH key or the OS keychain, never to argv.
        """
        offenders = {}
        for rel in tracked_files({".sh", ".py", ".ps1"}):
            text = read(rel)
            hits = [marker for marker in (".git-credentials", "x-access-token") if marker in text]
            if hits:
                offenders[rel] = hits
        self.assertEqual({}, offenders, "credential scraping in scripts: %s" % offenders)

    def test_every_script_compiles(self):
        """A syntax error in a shipped script is invisible until someone runs it."""
        broken = {}
        for path in sorted(SCRIPTS.glob("*.py")):
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(path)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                broken[path.name] = result.stderr.strip().splitlines()[-1:] or ["unknown error"]
        self.assertEqual({}, broken, "scripts that do not compile: %s" % broken)


class ArtifactTests(unittest.TestCase):
    """Browser artifacts stay offline and stay documented."""

    def test_artifacts_have_no_external_dependencies(self):
        offenders = {}
        for path in sorted(ARTIFACTS.glob("*.html")):
            if path.name in NETWORK_EXEMPT_ARTIFACTS:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            hits = re.findall(r"https?://[^\s\"'<>)]+", text)
            if hits:
                offenders[path.name] = sorted(set(hits))[:5]
        self.assertEqual({}, offenders, "artifacts reaching the network: %s" % offenders)

    def test_artifacts_are_documented(self):
        readme = read("README.md")
        art_readme = read("templates/artifacts/README.md")
        missing = {
            path.name: [doc for doc, text in
                        (("README.md", readme), ("templates/artifacts/README.md", art_readme))
                        if path.name not in text]
            for path in sorted(ARTIFACTS.glob("*.html"))
        }
        missing = {k: v for k, v in missing.items() if v}
        self.assertEqual({}, missing, "undocumented artifacts: %s" % missing)

    def test_artifacts_declare_print_styles(self):
        """Every handout artifact must print. Screen-only CSS is a silent failure."""
        offenders = [
            path.name
            for path in sorted(ARTIFACTS.glob("*.html"))
            if path.name not in NETWORK_EXEMPT_ARTIFACTS
            and "@media print" not in path.read_text(encoding="utf-8", errors="replace")
        ]
        self.assertEqual([], offenders, "artifacts with no print styles: %s" % offenders)


class CliSmokeTests(unittest.TestCase):
    """Contract tests for helper scripts.

    Each skips until its script exists, then enforces the documented interface.
    """

    # --- install.py (review Task 4) -------------------------------------
    @unittest.skipUnless((SCRIPTS / "install.py").is_file(), "scripts/install.py not built yet")
    def test_install_copies_skills_and_initialises_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            profiles = tmpdir / "profiles"
            folder = tmpdir / "myfolder"
            result = run_script(
                "install.py",
                "--profiles-dir", str(profiles),
                "--profile", "me",
                "--folder", str(folder),
            )
            self.assertEqual(0, result.returncode, "install failed: %s" % result.stderr)
            installed = list((profiles / "me" / "skills").iterdir())
            self.assertEqual(len(skill_slugs()), len(installed), "installer dropped skills")
            self.assertTrue((folder / "profile.md").exists(), "folder was not initialised")

    @unittest.skipUnless((SCRIPTS / "install.py").is_file(), "scripts/install.py not built yet")
    def test_install_copies_the_agent_identity_files(self):
        """Skills without SOUL.md is an agent with no behavioural rules.

        A Hermes profile needs the standards, the routing table and the identity
        alongside the skills, or the instalment is quietly worse than useless.
        """
        with tempfile.TemporaryDirectory() as tmp:
            profiles = pathlib.Path(tmp) / "profiles"
            result = run_script(
                "install.py",
                "--profiles-dir", str(profiles),
                "--profile", "me",
                "--folder", str(pathlib.Path(tmp) / "myfolder"),
            )
            self.assertEqual(0, result.returncode, "install failed: %s" % result.stderr)
            missing = [
                name
                for name in ("SOUL.md", "AGENTS.md", "profile.yaml", "config.yaml")
                if not (profiles / "me" / name).is_file()
            ]
            self.assertEqual([], missing, "installer did not place: %s" % missing)

    @unittest.skipUnless((SCRIPTS / "install.py").is_file(), "scripts/install.py not built yet")
    def test_install_never_clobbers_user_edits(self):
        """An update must not destroy a folder entry or a tuned config."""
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            profiles = tmpdir / "profiles"
            folder = tmpdir / "myfolder"
            args = ("--profiles-dir", str(profiles), "--profile", "me", "--folder", str(folder))
            self.assertEqual(0, run_script("install.py", *args).returncode)

            (folder / "wins.md").write_text("a win I wrote", encoding="utf-8")
            (profiles / "me" / "config.yaml").write_text("my model config", encoding="utf-8")
            self.assertEqual(0, run_script("install.py", *args).returncode)

            self.assertEqual(
                "a win I wrote",
                (folder / "wins.md").read_text(encoding="utf-8"),
                "re-install overwrote the user's folder notes",
            )
            self.assertEqual(
                "my model config",
                (profiles / "me" / "config.yaml").read_text(encoding="utf-8"),
                "re-install overwrote the user's config",
            )

    # --- capacity_mode.py (review Task 6) ------------------------------
    @unittest.skipUnless((SCRIPTS / "capacity_mode.py").is_file(), "scripts/capacity_mode.py not built yet")
    def test_capacity_mode_defaults_to_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script("capacity_mode.py", "--folder", tmp, "get", "--json")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn('"mode": "green"', result.stdout.replace("'", '"'),
                          "a missing state file must read as green, not crash or guess")

    @unittest.skipUnless((SCRIPTS / "capacity_mode.py").is_file(), "scripts/capacity_mode.py not built yet")
    def test_capacity_mode_rejects_invalid_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script("capacity_mode.py", "--folder", tmp, "set", "purple")
            self.assertNotEqual(0, result.returncode, "an invalid mode must exit non-zero")

    # --- redact_doc.py (review Task 7) ---------------------------------
    @unittest.skipUnless((SCRIPTS / "redact_doc.py").is_file(), "scripts/redact_doc.py not built yet")
    def test_redact_doc_scrubs_identifiers_but_keeps_bill_detail(self):
        letter = (
            "Dear Brendan O'Keefe,\n"
            "Email: brendan.test@example.com | Mobile: 0412 345 678\n"
            "TFN: 123 456 782 | NDIS Number: 430123456 | BSB: 062-000 Acc: 12345678\n"
            "Notice of Overdue Parking Fine: $148.00\n"
            "Action required by 14 December 2026.\n"
        )
        result = run_script("redact_doc.py", "-", "--names", "Brendan O'Keefe", stdin=letter)
        self.assertEqual(0, result.returncode, result.stderr)
        out = result.stdout
        for secret in ("brendan.test@example.com", "0412 345 678", "123 456 782", "430123456"):
            self.assertNotIn(secret, out, "PII survived redaction: %s" % secret)
        for keep in ("$148.00", "14 December 2026"):
            self.assertIn(keep, out, "over-redacted: lost triage detail %r" % keep)

    # --- search-ndis.py (review Task 8) --------------------------------
    @unittest.skipUnless((SCRIPTS / "search-ndis.py").is_file(), "scripts/search-ndis.py not built yet")
    def test_search_ndis_returns_cited_excerpts(self):
        import json

        result = run_script(
            "search-ndis.py", "reasonable and necessary supports", "--top", "5", "--json"
        )
        self.assertEqual(0, result.returncode, result.stderr)
        results = json.loads(result.stdout)
        self.assertEqual(5, len(results), "expected 5 hits, got %d" % len(results))
        for hit in results:
            self.assertTrue(hit.get("source_url"), "a hit with no source URL: %s" % hit)
            self.assertTrue(hit.get("fetched_date"), "a hit with no fetch date: %s" % hit)
            self.assertLessEqual(len(hit.get("excerpt", "")), 3000, "excerpt too large for context")


if __name__ == "__main__":
    unittest.main(verbosity=2)
