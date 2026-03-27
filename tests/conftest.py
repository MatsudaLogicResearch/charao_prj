"""
E2E test fixtures for charao_prj.
Runs charao via lrPymRPC on a remote Linux server and parses the resulting .lib file.
"""
import re
import subprocess
import sys
from pathlib import Path

import pytest

# --- constants ---
REPO_ROOT = Path(__file__).parent.parent
SERVER_IP = "192.168.168.103"
CHARAO_REPO_BASE = "git+https://github.com/MatsudaLogicResearch/charao_prj.git"
DEFAULT_TAG = "0.9.3"
TEST_RESULT_DIR = "rslt"
TEST_LOG_DIR = REPO_ROOT / "test_log"


# --- pytest hooks ---

def pytest_sessionstart(session):
    """Recreate test_log/ directory at the start of each test session."""
    import shutil
    if TEST_LOG_DIR.exists():
        shutil.rmtree(TEST_LOG_DIR)
    TEST_LOG_DIR.mkdir(parents=True)


def pytest_runtest_logreport(report):
    """Save test stdout and failure details to test_log/{script}.log."""
    if report.when not in ("setup", "call"):
        return
    stdout = "".join(
        content for name, content in report.sections if "stdout" in name.lower()
    )
    if not stdout and not report.failed:
        return
    log_file = TEST_LOG_DIR / f"{Path(report.fspath).stem}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        if report.when == "call":
            f.write(f"=== {report.nodeid} ===\n")
        if stdout:
            f.write(stdout)
        if report.failed:
            f.write(str(report.longrepr))
        if report.when == "call":
            f.write("\n")


def pytest_addoption(parser):
    parser.addini(
        "lrpymrpc_verbose",
        default=False,
        type="bool",
        help="Show lrPymRPC output on success (default: false)",
    )


# --- lrPymRPC runner ---

def run_lrpymrpc(
    cells_only: str,
    measures_only: str,
    tag: str = DEFAULT_TAG,
    result_dir: str = TEST_RESULT_DIR,
    verbose: bool = False,
    log_name: str = "lrpymrpc",
) -> Path:
    """
    Run charao via lrPymRPC on the remote server.
    Returns the local result directory path.
    verbose: if True, print lrPymRPC output on success (controlled by pytest.ini lrpymrpc_verbose).
    log_name: scenario name used to create test_log/{log_name}/lrpymrpc.log.
    """
    charao_cmd = (
        f"python3 -m charao -f OSU035 -v VENDOR -g std -u 5P00 -p TT -t 25.0 "
        f"--vdd 5.0 --target sample/target "
        f"--cells_only {cells_only} --measures_only {measures_only}"
    )
    cmd = [
        sys.executable, "-m", "lrPymRPC",
        "--SERVER_IP", SERVER_IP,
        "--REPO_URL", f"charao={CHARAO_REPO_BASE}@{tag}",
        "--SOURCE", "sample",
        "--RESULT", result_dir,
        "--CMD", charao_cmd,
    ]
    print(f"\n[E2E] Running: {' '.join(cmd)}")
    stdout_lines = []
    stderr_lines = []
    with subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, cwd=str(REPO_ROOT)
    ) as proc:
        for line in proc.stdout:
            stdout_lines.append(line)
        for line in proc.stderr:
            stderr_lines.append(line)
        proc.wait()

    # Save log to test_log/{log_name}/lrpymrpc.log
    log_dir = TEST_LOG_DIR / log_name
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "lrpymrpc.log"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("".join(stdout_lines))
        if stderr_lines:
            f.write("\n--- stderr ---\n")
            f.write("".join(stderr_lines))
    print(f"[E2E] Log saved: {log_file}")

    if proc.returncode != 0 or verbose:
        print("".join(stdout_lines))
    if proc.returncode != 0:
        print("".join(stderr_lines))
    assert proc.returncode == 0, (
        f"lrPymRPC failed (returncode={proc.returncode}):\n{''.join(stderr_lines)}"
    )
    return REPO_ROOT / result_dir


# --- .lib parser ---

def find_lib_file(result_dir: Path) -> Path:
    """Find the single .lib file in result_dir."""
    lib_files = list(result_dir.glob("*.lib"))
    assert len(lib_files) == 1, (
        f"Expected 1 .lib file in {result_dir}, found {len(lib_files)}: {lib_files}"
    )
    return lib_files[0]


def parse_cell_leakage(lib_path: Path, cell_name: str) -> dict:
    """
    Parse leakage_power values for a specific cell from a Liberty .lib file.

    Returns:
        {
            "cell_leakage_power": float,
            "leakage_when": {"!A": float, "A": float, ...}
        }
    All values are in the unit defined by leakage_power_unit (typically pW).
    """
    content = lib_path.read_text()

    # Find cell block (match until closing brace at indent level 2)
    pattern = rf'cell\s*\(\s*{re.escape(cell_name)}\s*\)\s*\{{(.*?)\n  \}}'
    match = re.search(pattern, content, re.DOTALL)
    assert match, f"Cell '{cell_name}' not found in {lib_path.name}"
    cell_block = match.group(1)

    # Extract cell_leakage_power
    clp_match = re.search(r'cell_leakage_power\s*:\s*([\d.eE+\-]+)', cell_block)
    assert clp_match, f"cell_leakage_power not found for cell '{cell_name}'"
    cell_leakage_power = float(clp_match.group(1))

    # Extract individual leakage_power() entries
    leakage_when = {}
    for lp_match in re.finditer(
        r'leakage_power\s*\(\s*\)\s*\{[^}]*when\s*:\s*"([^"]+)"[^}]*value\s*:\s*([\d.eE+\-]+)',
        cell_block,
        re.DOTALL,
    ):
        leakage_when[lp_match.group(1)] = float(lp_match.group(2))

    return {
        "cell_leakage_power": cell_leakage_power,
        "leakage_when": leakage_when,
    }


# --- pytest fixtures ---

@pytest.fixture(scope="session")
def e2e_inv_leakage(pytestconfig) -> Path:
    """Session-scoped fixture: run INV_1X leakage scenario via lrPymRPC."""
    verbose = pytestconfig.getini("lrpymrpc_verbose")
    return run_lrpymrpc(
        cells_only="INV_1X",
        measures_only="leakage",
        verbose=verbose,
        log_name="std_comb_leakage_inv",
    )
