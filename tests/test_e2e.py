"""
E2E regression tests for charao_prj.
Runs charao via lrPymRPC and verifies .lib output against expected.yaml.

Usage:
    pytest tests/test_e2e.py -v -s
"""
from pathlib import Path

import pytest
import yaml

from conftest import find_lib_file, parse_cell_leakage

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# --- helpers ---

def load_expected(scenario: str) -> dict:
    path = FIXTURES_DIR / scenario / "expected.yaml"
    assert path.exists(), f"expected.yaml not found: {path}"
    with open(path) as f:
        return yaml.safe_load(f)


def check_value(actual: float, expected: float, tolerance: float, label: str):
    """Assert that actual is within tolerance of expected.

    expected != 0: relative error  abs(actual - expected) / abs(expected) <= tolerance
    expected == 0: absolute error  abs(actual) <= tolerance
    """
    if expected == 0:
        diff = abs(actual)
        diff_str = f"absolute_diff={diff:.4e}"
    else:
        diff = abs(actual - expected) / abs(expected)
        diff_str = f"relative_diff={diff:.4f}"
    assert diff <= tolerance, (
        f"\n[NG] [value] in .lib {label}: actual={actual}, expected={expected}, "
        f"{diff_str} > tolerance={tolerance:.4f}"
    )
    print(
        f"\n[OK] [value] in .lib {label}: actual={actual}, expected={expected}, "
        f"{diff_str}, tolerance={tolerance:.4f}"
    )


# --- scenario: std_comb_leakage_inv ---

class TestStdCombLeakageInv:
    """
    Simplest E2E scenario: OSU035 / INV_1X / leakage only.
    Purpose: verify lrPymRPC execution, .lib generation, and value comparison.
    Library: OSU035 (0.35um, CB_REV2)
    """

    SCENARIO = "std_comb_leakage_inv"

    def test_lib_file_exists(self, e2e_inv_leakage):
        """Verify .lib file is generated."""
        lib = find_lib_file(e2e_inv_leakage)
        assert lib.exists(), f"\n[NG] [file] {lib.name} not exist"
        print(f"\n[OK] [file] {lib.name} exist")

    def test_v_file_exists(self, e2e_inv_leakage):
        """Verify Verilog .v file is generated."""
        v_files = list(e2e_inv_leakage.glob("*.v"))
        assert len(v_files) >= 1, f"\n[NG] [file] *.v not exist in {e2e_inv_leakage}"
        print(f"\n[OK] [file] {v_files[0].name} exist")

    def test_md_file_exists(self, e2e_inv_leakage):
        """Verify Markdown .md file is generated."""
        md_files = list(e2e_inv_leakage.glob("*.md"))
        assert len(md_files) >= 1, f"\n[NG] [file] *.md not exist in {e2e_inv_leakage}"
        print(f"\n[OK] [file] {md_files[0].name} exist")

    def test_leakage_values(self, e2e_inv_leakage):
        """Verify INV_1X leakage_power values match expected.yaml within tolerance."""
        expected = load_expected(self.SCENARIO)
        scenario_info = expected["scenario"]
        lib = find_lib_file(e2e_inv_leakage)

        print(
            f"\n[INFO] Library: {scenario_info['library']} "
            f"({scenario_info['process']}, {scenario_info['lib_revision']}) "
            f"charao@{scenario_info['charao_tag']}"
        )

        cell = "INV_1X"
        result = parse_cell_leakage(lib, cell)
        exp = expected["expected"][cell]
        tol = exp["tolerance"]

        # cell_leakage_power
        label = f"{cell}.cell_leakage_power"
        check_value(result["cell_leakage_power"], exp["cell_leakage_power"], tol, label)

        # leakage_power per when condition
        for when, exp_val in exp["leakage_when"].items():
            actual_val = result["leakage_when"].get(when)
            assert actual_val is not None, (
                f"leakage_power when='{when}' not found in .lib for {cell}"
            )
            label = f"{cell}.leakage_when['{when}']"
            check_value(actual_val, exp_val, tol, label)
