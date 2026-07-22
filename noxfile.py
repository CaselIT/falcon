"""Nox configuration for Falcon.

This file replaces tox.ini with Nox sessions. Run with:

    nox          # run all default sessions
    nox -s <session_name>
    nox -l       # list all sessions
"""

from __future__ import annotations

import pathlib
import sys

import nox

ROOT = pathlib.Path(__file__).resolve().parent
FALCON = ROOT / "falcon"
E2E_TESTS = ROOT / "e2e-tests"
TOOLS = ROOT / "tools"

# ---------------------------------------------------------------------------
# Python versions
# ---------------------------------------------------------------------------
PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14", "3.15"]
PYTHON_DEFAULT = "3.12"

# ---------------------------------------------------------------------------
# Default session list
# ---------------------------------------------------------------------------
DEFAULT_SESSIONS = [
    "pytest",
    "coverage",
    "cleanup",
    "mintest",
    "ruff",
    "pep8",
    "pep8_docstrings",
    "mypy",
    "mypy_tests",
    "pyright_tests",
    "docs",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(session: nox.Session) -> None:
    """Run the clean.py script on the falcon directory."""
    session.run("python", str(TOOLS / "clean.py"), str(FALCON))


def _install_test_deps(session: nox.Session) -> None:
    """Install Falcon in editable mode plus test requirements."""
    session.install("-e", ".", "-r", str(ROOT / "requirements/tests"))


def _install_bench_deps(session: nox.Session) -> None:
    """Install Falcon in editable mode plus benchmark requirements."""
    session.install("-e", ".", "-r", str(ROOT / "requirements/bench"))


def _install_docs_deps(session: nox.Session) -> None:
    """Install documentation requirements."""
    session.install("-r", str(ROOT / "requirements/docs"))


# ---------------------------------------------------------------------------
# Default sessions
# ---------------------------------------------------------------------------

@nox.session(python=PYTHON_VERSIONS)
def pytest(session: nox.Session) -> None:
    """Run the full test suite with coverage."""
    _install_test_deps(session)
    session.install("pytest-randomly", "jsonschema", "testtools")
    session.run(
        "coverage", "run", "-m", "pytest", "tests", *session.posargs,
        env={
            "PIP_CONFIG_FILE": str(ROOT / "pip.conf"),
            "PYTHONASYNCIODEBUG": "1",
            "FALCON_DISABLE_CYTHON": "Y",
        },
    )


@nox.session
def coverage(session: nox.Session) -> None:
    """Combine and report coverage."""
    session.install("-r", str(ROOT / "requirements/tests"))
    session.run(
        "coverage", "combine",
    )
    session.run(
        "coverage", "html", "-d", str(ROOT / ".coverage_html"),
    )
    session.run(
        "coverage", "report", "--fail-under", "100",
    )


@nox.session
def cleanup(session: nox.Session) -> None:
    """Clean intermediate files and erase coverage data."""
    _install_test_deps(session)
    _clean(session)
    session.run("coverage", "erase")


@nox.session
def mintest(session: nox.Session) -> None:
    """Run tests with minimal dependencies."""
    session.install("-e", ".", "-r", str(ROOT / "requirements/mintest"))
    session.run(
        "coverage", "run", "-m", "pytest", "tests", "-k", "not slow",
        env={
            "PIP_CONFIG_FILE": str(ROOT / "pip.conf"),
            "PYTHONASYNCIODEBUG": "0",
            "FALCON_DISABLE_CYTHON": "Y",
        },
    )


# ---------------------------------------------------------------------------
# Lint
# ---------------------------------------------------------------------------

@nox.session(python=[PYTHON_DEFAULT])
def ruff(session: nox.Session) -> None:
    """Check code formatting with ruff."""
    session.install("ruff>=0.11.6")
    session.run("ruff", "format", "--check", ".", *session.posargs)


@nox.session(python=[PYTHON_DEFAULT])
def pep8(session: nox.Session) -> None:
    """Check code style with ruff."""
    session.install("ruff>=0.11.6")
    session.run("ruff", "check", ".", *session.posargs)


@nox.session(python=[PYTHON_DEFAULT])
def pep8_docstrings(session: nox.Session) -> None:
    """Check docstring conventions with ruff."""
    session.install("ruff>=0.11.6")
    session.run(
        "ruff", "check",
        "--exclude=.ecosystem,.eggs,.git,.tox,.venv,build,dist,docs,examples,tests,falcon/bench/nuts",
        "--select=D205,D212,D400,D401,D403,D404",
        ".", *session.posargs,
    )


@nox.session(python=[PYTHON_DEFAULT])
def reformat(session: nox.Session) -> None:
    """Reformat code with ruff."""
    session.install("ruff>=0.11.6")
    session.run("ruff", "format", ".")
    session.run("ruff", "check", "--fix")


# ---------------------------------------------------------------------------
# Typing
# ---------------------------------------------------------------------------

@nox.session(python=[PYTHON_DEFAULT])
def mypy(session: nox.Session) -> None:
    """Run mypy on the falcon package."""
    session.install("mypy", "types-jsonschema")
    _clean(session)
    session.run("mypy", "--strict", "falcon")


@nox.session(python=[PYTHON_DEFAULT])
def mypy_tests(session: nox.Session) -> None:
    """Run mypy on e2e-tests and typing tests."""
    session.install(
        "mypy", "cheroot", "types-requests", "types-PyYAML",
        "types-ujson", "types-waitress", "types-aiofiles", "types-jsonschema",
    )
    _clean(session)
    session.run("mypy", "--strict", str(E2E_TESTS / "server"))
    session.run("mypy", "--strict", "tests/test_typing.py")
    session.run(
        "mypy", "tests",
        "--allow-untyped-calls", "--allow-untyped-defs",
        "--no-check-untyped-defs",
    )


@nox.session(python=[PYTHON_DEFAULT])
def pyright_tests(session: nox.Session) -> None:
    """Run pyright on e2e-tests and typing tests."""
    session.install("pyright")
    _clean(session)
    session.run("pyright", str(E2E_TESTS / "server"))
    session.run("pyright", "tests/test_typing.py")


# ---------------------------------------------------------------------------
# Cython
# ---------------------------------------------------------------------------

@nox.session(python=PYTHON_VERSIONS, name="cython")
def cython(session: nox.Session) -> None:
    """Run tests with Cython extensions enabled."""
    session.install("-r", str(ROOT / "requirements/tests"))
    session.install("Cython")
    # pyximport requires distutils.extension; setuptools provides it
    if session.python in ["3.12", "3.13", "3.14", "3.15"]:
        session.install("setuptools")
    session.run(
        "pytest", "tests", *session.posargs,
        env={
            "PIP_CONFIG_FILE": str(ROOT / "pip.conf"),
            "FALCON_DISABLE_CYTHON": "",
            "FALCON_ASGI_WRAP_NON_COROUTINES": "Y",
            "FALCON_TESTING_SESSION": "Y",
            "PYTHONASYNCIODEBUG": "1",
        },
    )


# ---------------------------------------------------------------------------
# WSGI / ASGI server tests
# ---------------------------------------------------------------------------

@nox.session(python=PYTHON_VERSIONS)
def wsgi_servers(session: nox.Session) -> None:
    """Run WSGI server tests with Cython."""
    session.install("-r", str(ROOT / "requirements/tests"))
    session.install("Cython", "cheroot", "gunicorn", "uwsgi", "waitress")
    if session.python in ["3.12", "3.13", "3.14", "3.15"]:
        session.install("setuptools")
    session.run(
        "pytest", "-v", "tests/test_wsgi_servers.py", *session.posargs,
        env={
            "PIP_CONFIG_FILE": str(ROOT / "pip.conf"),
            "FALCON_DISABLE_CYTHON": "",
            "FALCON_ASGI_WRAP_NON_COROUTINES": "Y",
            "FALCON_TESTING_SESSION": "Y",
            "PYTHONASYNCIODEBUG": "1",
        },
    )


@nox.session(python=["3.9"])
def wsgi_meinheld(session: nox.Session) -> None:
    """Run WSGI server tests with meinheld (Python 3.9 only)."""
    session.install("-r", str(ROOT / "requirements/tests"))
    session.install("Cython", "gunicorn", "meinheld")
    session.run(
        "pytest", "-v", "tests/test_wsgi_servers.py", *session.posargs,
        env={
            "PIP_CONFIG_FILE": str(ROOT / "pip.conf"),
            "FALCON_DISABLE_CYTHON": "",
            "FALCON_ASGI_WRAP_NON_COROUTINES": "Y",
            "FALCON_TESTING_SESSION": "Y",
            "PYTHONASYNCIODEBUG": "1",
        },
    )


@nox.session(python=[PYTHON_DEFAULT])
def daphne(session: nox.Session) -> None:
    """Run ASGI server tests with daphne."""
    _install_test_deps(session)
    session.install("daphne")
    session.run(
        "pytest", "-v", "tests/asgi/test_asgi_servers.py", *session.posargs,
    )


@nox.session(python=[PYTHON_DEFAULT])
def hypercorn(session: nox.Session) -> None:
    """Run ASGI server tests with hypercorn."""
    _install_test_deps(session)
    session.install("hypercorn")
    session.run(
        "pytest", "-v", "tests/asgi/test_asgi_servers.py", *session.posargs,
    )


# ---------------------------------------------------------------------------
# Debugging
# ---------------------------------------------------------------------------

@nox.session(python=[PYTHON_DEFAULT])
def py_debug(session: nox.Session) -> None:
    """Install debug tools (pdbpp, uvicorn) for development."""
    session.install("-r", str(ROOT / "requirements/tests"))
    session.install("pdbpp", "uvicorn", "jsonschema")


# ---------------------------------------------------------------------------
# Smoke testing
# ---------------------------------------------------------------------------

@nox.session(python=["3.10"])
def smoke(session: nox.Session) -> None:
    """Run smoke tests with a sample app."""
    _install_bench_deps(session)
    session.run(
        "python", "-c", "import falcon.asgi; falcon.asgi.App()",
    )
    session.run("falcon-bench", "-t", "1", "-b", "falcon-ext")


@nox.session(python=["3.10"])
def smoke_cython(session: nox.Session) -> None:
    """Run smoke tests with Cython."""
    session.install("-r", str(ROOT / "requirements/bench"))
    session.install("cython")
    session.run(
        "python", "-c", "import falcon.asgi; falcon.asgi.App()",
        env={
            "PIP_CONFIG_FILE": str(ROOT / "pip.conf"),
            "FALCON_DISABLE_CYTHON": "",
            "FALCON_ASGI_WRAP_NON_COROUTINES": "Y",
            "FALCON_TESTING_SESSION": "Y",
            "PYTHONASYNCIODEBUG": "1",
        },
    )
    session.run("falcon-bench", "-t", "1", "-b", "falcon-ext")


# ---------------------------------------------------------------------------
# Benchmarking
# ---------------------------------------------------------------------------

@nox.session(python=["3.10"])
def bench(session: nox.Session) -> None:
    """Run benchmarks."""
    _install_bench_deps(session)
    session.run("falcon-bench", *session.posargs)


@nox.session(python=["3.10"])
def bench_cython(session: nox.Session) -> None:
    """Run benchmarks with Cython."""
    session.install("-r", str(ROOT / "requirements/bench"))
    session.install("cython")
    session.run(
        "falcon-bench", *session.posargs,
        env={
            "PIP_CONFIG_FILE": str(ROOT / "pip.conf"),
            "FALCON_DISABLE_CYTHON": "",
            "FALCON_ASGI_WRAP_NON_COROUTINES": "Y",
            "FALCON_TESTING_SESSION": "Y",
            "PYTHONASYNCIODEBUG": "1",
        },
    )


@nox.session(python=["pypy", "pypy3"])
def pypy_bench(session: nox.Session) -> None:
    """Run benchmarks on PyPy."""
    session.install("-r", str(ROOT / "requirements/bench"))
    session.run("falcon-bench", *session.posargs)


# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------

@nox.session(python=[PYTHON_DEFAULT])
def docs(session: nox.Session) -> None:
    """Build documentation."""
    _install_docs_deps(session)
    session.run(
        "sphinx-build", "-j", "auto", "-W", "-E", "-b", "html",
        "docs", "docs/_build/html", *session.posargs,
        env={"SOURCE_DATE_EPOCH": str(int(pathlib.Path().stat().st_mtime))},
    )


@nox.session(python=[PYTHON_DEFAULT])
def changelog_release(session: nox.Session) -> None:
    """Run changelog release scripts."""
    _install_docs_deps(session)
    session.install("toml")
    session.run("python", str(TOOLS / "add_contributors.py"))
    session.run("python", str(TOOLS / "towncrier_draft.py"))


@nox.session(python=[PYTHON_DEFAULT])
def changelog_draft(session: nox.Session) -> None:
    """Preview changelog draft."""
    _install_docs_deps(session)
    session.install("toml")
    session.run(
        "python", str(TOOLS / "add_contributors.py"), "--dry-run",
    )
    session.run(
        "python", str(TOOLS / "towncrier_draft.py"), "--dry-run",
    )


@nox.session(python=["3.10"])
def dash(session: nox.Session) -> None:
    """Build documentation and generate Dash archive."""
    _install_docs_deps(session)
    session.run(
        "sphinx-build", "-j", "4", "-W", "-E", "-b", "html",
        "docs", "docs/_build/html",
    )
    session.run(
        str(ROOT / "tools" / "generate_dash.sh"),
        env={"DASHBUILD": "True"},
    )


# ---------------------------------------------------------------------------
# Tutorial tests
# ---------------------------------------------------------------------------

@nox.session(python=[PYTHON_DEFAULT])
def look(session: nox.Session) -> None:
    """Run tutorial 'look' tests."""
    session.install("-r", str(ROOT / "examples/look/requirements/test"))
    session.run("pytest", str(ROOT / "examples/look/tests"), *session.posargs)


@nox.session(python=[PYTHON_DEFAULT])
def asgilook(session: nox.Session) -> None:
    """Run tutorial 'asgilook' tests with coverage."""
    session.install(
        "-r", str(ROOT / "examples/asgilook/requirements/asgilook"),
        "-r", str(ROOT / "examples/asgilook/requirements/test"),
    )
    session.run(
        "pytest",
        "--cov", "asgilook",
        "--cov-config", str(ROOT / "examples/asgilook/.coveragerc"),
        "--cov-fail-under", "100",
        "--cov-report", "term-missing",
        str(ROOT / "examples/asgilook/tests"), *session.posargs,
    )


@nox.session(python=[PYTHON_DEFAULT])
def ws_tutorial(session: nox.Session) -> None:
    """Run tutorial 'ws_tutorial' tests with coverage."""
    session.install(
        "-r", str(ROOT / "examples/ws_tutorial/requirements/app"),
        "-r", str(ROOT / "examples/ws_tutorial/requirements/test"),
    )
    session.run(
        "pytest",
        "--cov", "ws_tutorial",
        "--cov-config", str(ROOT / "examples/ws_tutorial/.coveragerc"),
        "--cov-fail-under", "100",
        "--cov-report", "term-missing",
        str(ROOT / "examples/ws_tutorial/tests"), *session.posargs,
    )


# ---------------------------------------------------------------------------
# E2E tests
# ---------------------------------------------------------------------------

@nox.session(python=[PYTHON_DEFAULT])
def e2e_chrome(session: nox.Session) -> None:
    """Run E2E tests with Chrome."""
    session.install("-r", str(ROOT / "requirements/e2e"))
    session.run(
        "pytest", str(E2E_TESTS), "--browser=chrome", *session.posargs,
    )


@nox.session(python=[PYTHON_DEFAULT])
def e2e_firefox(session: nox.Session) -> None:
    """Run E2E tests with Firefox."""
    session.install("-r", str(ROOT / "requirements/e2e"))
    session.run(
        "pytest", str(E2E_TESTS), "--browser=firefox", *session.posargs,
    )


# ---------------------------------------------------------------------------
# Package sanity
# ---------------------------------------------------------------------------

@nox.session(python=["3.12"])
def twine_check(session: nox.Session) -> None:
    """Check package with twine."""
    session.install("build", "twine")
    session.run("python", "-m", "build")
    session.run("twine", "check", str(ROOT / "dist") + "/*")


# ---------------------------------------------------------------------------
# Security auditing
# ---------------------------------------------------------------------------

@nox.session(python=["3.12"])
def zizmor(session: nox.Session) -> None:
    """Audit GitHub workflows with zizmor."""
    session.install("zizmor")
    session.run("zizmor", ".github/workflows/")


@nox.session(python=["3.12"])
def zizmor_github(session: nox.Session) -> None:
    """Audit GitHub workflows with zizmor in GitHub format."""
    session.install("zizmor")
    session.run("zizmor", "--format", "github", ".github/workflows/")


# ---------------------------------------------------------------------------
# WSGI environ dump helpers
# ---------------------------------------------------------------------------

@nox.session(python=[PYTHON_DEFAULT])
def dump_gunicorn(session: nox.Session) -> None:
    """Run gunicorn to view environ dict (localhost:8000)."""
    session.install("gunicorn")
    session.run("gunicorn", "-b", "localhost:8000", "tests.dump_wsgi")


@nox.session(python=[PYTHON_DEFAULT])
def dump_waitress(session: nox.Session) -> None:
    """Run waitress-serve to view environ dict (localhost:8000)."""
    session.install("waitress")
    session.run(
        "waitress-serve", "--listen=localhost:8000", "tests.dump_wsgi:application",
    )


@nox.session(python=[PYTHON_DEFAULT])
def dump_wsgiref(session: nox.Session) -> None:
    """Run wsgiref to view environ dict."""
    session.run("python", "tests/dump_wsgi.py")


# ---------------------------------------------------------------------------
# Default session list
# ---------------------------------------------------------------------------

nox.options.sessions = DEFAULT_SESSIONS
