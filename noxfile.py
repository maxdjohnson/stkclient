"""Nox sessions."""

import os
import shutil
from pathlib import Path
from textwrap import dedent

import nox
from nox import Session, session

package = "stkclient"
python_versions = ["3.15", "3.14", "3.13", "3.12", "3.11"]
nox.options.default_venv_backend = "uv"
nox.needs_version = ">= 2026.8.17"
nox.options.sessions = [
    "pre-commit",
    "audit",
    "mypy",
    "tests",
    "typeguard",
    "xdoctest",
    "docs-build",
]


def sync(session: Session, group: str) -> None:
    """Install a dependency group and the package from the shared lockfile.

    Args:
        session: The Session object.
        group: The dependency group to install.
    """
    session.run_install(
        "uv",
        "sync",
        "--locked",
        "--no-default-groups",
        "--group",
        group,
        "--no-editable",
        f"--python={session.virtualenv.location}",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )


def activate_virtualenv_in_precommit_hooks(session: Session) -> None:
    """Activate virtualenv in hooks installed by pre-commit.

    This function patches git hooks installed by pre-commit to activate the
    session's virtual environment. This allows pre-commit to locate hooks in
    that environment when invoked from git.

    Args:
        session: The Session object.
    """
    assert session.bin is not None  # noqa: S101

    virtualenv = session.env.get("VIRTUAL_ENV")
    if virtualenv is None:
        return

    hookdir = Path(".git") / "hooks"
    if not hookdir.is_dir():
        return

    for hook in hookdir.iterdir():
        if hook.name.endswith(".sample") or not hook.is_file():
            continue

        text = hook.read_text()
        bindir = repr(session.bin)[1:-1]  # strip quotes
        if not (Path("A") == Path("a") and bindir.lower() in text.lower() or bindir in text):
            continue

        lines = text.splitlines()
        if not (lines[0].startswith("#!") and "python" in lines[0].lower()):
            continue

        header = dedent(f"""\
            import os
            os.environ["VIRTUAL_ENV"] = {virtualenv!r}
            os.environ["PATH"] = os.pathsep.join((
                {session.bin!r},
                os.environ.get("PATH", ""),
            ))
            """)

        lines.insert(1, header)
        hook.write_text("\n".join(lines))


@session(name="pre-commit", python="3.12")
def precommit(session: Session) -> None:
    """Lint using pre-commit."""
    args = session.posargs or ["run", "--all-files", "--show-diff-on-failure"]
    sync(session, "lint")
    session.run("pre-commit", *args)
    if args and args[0] == "install":
        activate_virtualenv_in_precommit_hooks(session)


@session(python="3.12")
def audit(session: Session) -> None:
    """Scan dependencies for insecure packages."""
    sync(session, "audit")
    requirements = Path(session.create_tmp()) / "requirements.txt"
    session.run(
        "uv",
        "export",
        "--locked",
        "--all-groups",
        "--no-emit-project",
        "--output-file",
        str(requirements),
        external=True,
        silent=True,
    )
    session.run("pip-audit", "--strict", "--disable-pip", "--no-deps", "-r", str(requirements))


@session(python="3.12")
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or ["src", "tests", "docs/conf.py"]
    sync(session, "typing")
    session.run("mypy", "--pretty", *args)
    if not session.posargs:
        session.run("mypy", "noxfile.py")


@session(python=python_versions)
def tests(session: Session) -> None:
    """Run the test suite."""
    sync(session, "test")
    try:
        session.run("coverage", "run", "--parallel", "-m", "pytest", *session.posargs)
    finally:
        if session.interactive:
            session.notify("coverage", posargs=[])


@session(python="3.12")
def coverage(session: Session) -> None:
    """Produce the coverage report."""
    args = session.posargs or ["report"]

    sync(session, "test")

    if not session.posargs and any(Path().glob(".coverage.*")):
        session.run("coverage", "combine")

    session.run("coverage", *args)


@session(python="3.12")
def typeguard(session: Session) -> None:
    """Runtime type checking using Typeguard."""
    sync(session, "typeguard")
    session.run("pytest", f"--typeguard-packages={package}", *session.posargs)


@session(python="3.12")
def xdoctest(session: Session) -> None:
    """Run examples with xdoctest."""
    if session.posargs:
        args = [package, *session.posargs]
    else:
        args = [f"--modname={package}", "--command=all"]
        if "FORCE_COLOR" in os.environ:
            args.append("--colored=1")

    sync(session, "doctest")
    session.run("python", "-m", "xdoctest", *args)


@nox.session(name="docs-build", python="3.12")
def docs_build(session: nox.Session) -> None:
    """Build HTML, EPUB, and LaTeX using the Read the Docs dependencies."""
    sync(session, "docs")

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    if session.posargs:
        session.run("sphinx-build", *session.posargs)
        return

    for builder in ("html", "epub", "latex"):
        args = ["-W", "--keep-going", "-b", builder]
        if "FORCE_COLOR" in os.environ:
            args.insert(0, "--color")
        session.run(
            "sphinx-build",
            *args,
            "-d",
            str(build_dir / "doctrees" / builder),
            "docs",
            str(build_dir / builder),
        )


@nox.session(python="3.12")
def docs(session: nox.Session) -> None:
    """Build and serve the documentation with live reloading on file changes."""
    args = session.posargs or ["--open-browser", "docs", "docs/_build/html"]
    sync(session, "docs-live")

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-autobuild", *args)
