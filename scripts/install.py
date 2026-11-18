#!/usr/bin/env python3
"""One-command installer for the Individual Agent.

Copies every skill into a Hermes profile and initialises your personal folder,
so a new user is not left hand-copying directories and guessing at paths.

    python scripts/install.py                      # profile "me", auto-detected paths
    python scripts/install.py --profile sarah      # a different profile name
    python scripts/install.py --dry-run            # show what would happen, change nothing
    python scripts/install.py --folder ~/min       # a folder that is not ~/myfolder

Standard library only. This script needs no third-party packages, which is
deliberate: it must run on a bare Python before anything else in the repo works.

What it will not do
-------------------
It never overwrites an existing config.yaml, because that file holds the user's
model keys and preferences. Pass --force-config if you genuinely want it replaced.
It never overwrites SOUL.md, AGENTS.md or profile.yaml once they exist, because a
user who has tuned the agent's voice should not lose that to an update. Pass
--force-identity to replace them anyway.
It never deletes a skill directory it did not just write.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
CONFIG = REPO / "config.yaml"
FOLDER_SETUP = REPO / "scripts" / "setup-my-folder.py"

# A Hermes profile is more than skills: these files carry the agent's standards,
# its routing table and its identity. An install without them produces an agent
# with no behavioural rules, which is worse than no install at all.
IDENTITY_FILES = ("SOUL.md", "AGENTS.md", "profile.yaml")


def default_profiles_dir() -> pathlib.Path:
    """The Hermes profiles directory for this platform.

    Windows keeps it under %LOCALAPPDATA%. Linux and macOS use an XDG-style
    data directory, falling back to the older ~/.hermes location when that is
    the one that already exists on this machine.
    """
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        root = pathlib.Path(base) if base else pathlib.Path.home() / "AppData" / "Local"
        return root / "hermes" / "profiles"

    candidates = [
        pathlib.Path.home() / ".local" / "share" / "hermes" / "profiles",
        pathlib.Path.home() / ".hermes" / "profiles",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return candidates[0]


def say(message: str, *, dry_run: bool = False) -> None:
    print(("  [dry-run] " if dry_run else "  ") + message)


def install_skills(profile_dir: pathlib.Path, *, dry_run: bool) -> list[str]:
    """Copy every skill directory into the profile. Returns the slugs installed."""
    target = profile_dir / "skills"
    slugs = sorted(p.name for p in SKILLS.iterdir() if p.is_dir())
    for slug in slugs:
        source = SKILLS / slug
        destination = target / slug
        if dry_run:
            say("would copy skill %s" % slug, dry_run=True)
            continue
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
    say("copied %d skills into %s" % (len(slugs), target))
    return slugs


def install_config(profile_dir: pathlib.Path, *, dry_run: bool, force: bool) -> str:
    """Copy the example config unless the user already has one."""
    destination = profile_dir / "config.yaml"
    if destination.exists() and not force:
        say("kept your existing config.yaml (pass --force-config to replace it)")
        return "kept"
    if dry_run:
        say("would copy config.yaml", dry_run=True)
        return "would copy"
    if not CONFIG.is_file():
        say("no config.yaml in the repo; skipped")
        return "missing"
    shutil.copy2(CONFIG, destination)
    say("copied config.yaml")
    return "copied"


def install_identity(profile_dir: pathlib.Path, *, dry_run: bool, force: bool) -> list[str]:
    """Copy SOUL.md, AGENTS.md and profile.yaml. Returns the names written."""
    written = []
    for name in IDENTITY_FILES:
        source = REPO / name
        destination = profile_dir / name
        if not source.is_file():
            say("no %s in the repo; skipped" % name)
            continue
        if destination.exists() and not force:
            say("kept your existing %s (pass --force-identity to replace it)" % name)
            continue
        if dry_run:
            say("would copy %s" % name, dry_run=True)
            continue
        shutil.copy2(source, destination)
        written.append(name)
    if written:
        say("copied %d identity files: %s" % (len(written), ", ".join(written)))
    return written


def install_folder(folder: pathlib.Path, *, dry_run: bool) -> bool:
    """Run the folder setup script, which is the only supported way to build it."""
    if dry_run:
        say("would initialise the folder at %s" % folder, dry_run=True)
        return True
    result = subprocess.run(
        [sys.executable, str(FOLDER_SETUP), "--target", str(folder)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        say("folder setup failed: %s" % (result.stderr.strip() or "unknown error"))
        return False
    say("initialised the folder at %s" % folder)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install the Individual Agent skills into a Hermes profile.",
    )
    parser.add_argument("--profile", default="me", help="Hermes profile name (default: me)")
    parser.add_argument(
        "--profiles-dir",
        default=None,
        help="Hermes profiles directory (default: auto-detected for this platform)",
    )
    parser.add_argument(
        "--folder",
        default=None,
        help="Personal folder to initialise (default: ~/myfolder)",
    )
    parser.add_argument("--force-config", action="store_true", help="Replace an existing config.yaml")
    parser.add_argument(
        "--force-identity",
        action="store_true",
        help="Replace an existing SOUL.md, AGENTS.md or profile.yaml",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show the plan without changing anything")
    args = parser.parse_args(argv)

    if not SKILLS.is_dir():
        print("error: run this from inside the repository; skills/ was not found", file=sys.stderr)
        return 1

    profiles_dir = pathlib.Path(args.profiles_dir).expanduser() if args.profiles_dir else default_profiles_dir()
    profile_dir = profiles_dir / args.profile
    folder = pathlib.Path(args.folder).expanduser() if args.folder else pathlib.Path.home() / "myfolder"

    print("Individual Agent installer")
    print("  profile : %s" % profile_dir)
    print("  folder  : %s" % folder)
    if args.dry_run:
        print("  mode    : dry run, nothing will change")
    print()

    profile_existed = profile_dir.is_dir()
    if not args.dry_run:
        profile_dir.mkdir(parents=True, exist_ok=True)

    slugs = install_skills(profile_dir, dry_run=args.dry_run)
    identity = install_identity(profile_dir, dry_run=args.dry_run, force=args.force_identity)
    install_config(profile_dir, dry_run=args.dry_run, force=args.force_config)
    folder_ok = install_folder(folder, dry_run=args.dry_run)

    if args.dry_run:
        print("\nDry run complete. Re-run without --dry-run to apply.")
        return 0

    print("\nDone: %d skills%s in place." % (
        len(slugs),
        (" and %d identity files" % len(identity)) if identity else "",
    ))
    if not profile_existed:
        print(
            "\nThe profile directory was created fresh. If Hermes does not recognise it,\n"
            "run `hermes profile create %s`, then run this installer again." % args.profile
        )
    if not folder_ok:
        return 1
    print(
        "\nNext:\n"
        "  1. Add a model key to your .env (see INSTALL.md step 5)\n"
        "  2. Start the agent and say: Let's build my profile."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
