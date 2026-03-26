"""
tests/test_myLibrarySetting.py

myLibrarySetting.py の update_mag() / update_threshold_voltage() のユニットテスト。
ngspice不要、純粋な計算処理のみ対象。

実行方法:
    cd D:/git/charao_prj
    pytest tests/test_myLibrarySetting.py -v
"""
import pytest
from charao.script.myLibrarySetting import MyLibrarySetting


class TestUpdateMag:
    """update_mag(): 単位文字列からスケール係数を計算するテスト"""

    @pytest.mark.parametrize("unit, expected", [
        ("V",  1.0),
        ("mV", 1e-3),
        ("v",  1.0),   # 小文字
        ("MV", 1e-3),  # 大文字
    ])
    def test_電圧単位(self, unit, expected):
        mls = MyLibrarySetting(voltage_unit=unit)
        mls.update_mag()
        assert mls.voltage_mag == expected

    @pytest.mark.parametrize("unit, expected", [
        ("nF", 1e-9),
        ("pF", 1e-12),
        ("fF", 1e-15),
        ("pf", 1e-12),  # 小文字
        ("PF", 1e-12),  # 大文字
    ])
    def test_容量単位(self, unit, expected):
        mls = MyLibrarySetting(capacitance_unit=unit)
        mls.update_mag()
        assert mls.capacitance_mag == expected

    @pytest.mark.parametrize("unit, expected", [
        ("ps", 1e-12),
        ("ns", 1e-9),
        ("us", 1e-6),
        ("PS", 1e-12),  # 大文字
        ("NS", 1e-9),   # 大文字
    ])
    def test_時間単位(self, unit, expected):
        mls = MyLibrarySetting(time_unit=unit)
        mls.update_mag()
        assert mls.time_mag == expected

    @pytest.mark.parametrize("unit, expected", [
        ("A",  1.0),
        ("mA", 1e-3),
        ("uA", 1e-6),
        ("nA", 1e-9),
        ("MA", 1e-3),  # 大文字
        ("UA", 1e-6),  # 大文字
    ])
    def test_電流単位(self, unit, expected):
        mls = MyLibrarySetting(current_unit=unit)
        mls.update_mag()
        assert mls.current_mag == expected

    @pytest.mark.parametrize("unit, expected", [
        ("fW", 1e-15),
        ("pW", 1e-12),
        ("nW", 1e-9),
        ("uW", 1e-6),
        ("FW", 1e-15),  # 大文字
        ("PW", 1e-12),  # 大文字
    ])
    def test_リーク電力単位(self, unit, expected):
        mls = MyLibrarySetting(leakage_power_unit=unit)
        mls.update_mag()
        assert mls.leakage_power_mag == expected

    @pytest.mark.parametrize("unit, expected", [
        ("fJ", 1e-15),
        ("pJ", 1e-12),
        ("nJ", 1e-9),
        ("FJ", 1e-15),  # 大文字
    ])
    def test_エネルギー単位(self, unit, expected):
        mls = MyLibrarySetting(energy_unit=unit)
        mls.update_mag()
        assert mls.energy_mag == expected


class TestUpdateThresholdVoltage:
    """update_threshold_voltage(): 論理閾値電圧の計算テスト"""

    @pytest.mark.parametrize("vdd, threshold_high, expected", [
        (5.0, 0.8, 4.0),    # 標準5V
        (3.3, 0.8, 2.64),   # 3.3V系
        (1.8, 0.8, 1.44),   # 1.8V系
        (5.0, 0.7, 3.5),    # 閾値70%
    ])
    def test_HIGH閾値電圧(self, vdd, threshold_high, expected):
        mls = MyLibrarySetting(vdd_voltage=vdd, logic_threshold_high=threshold_high, voltage_unit="V")
        mls.update_mag()
        mls.update_threshold_voltage()
        assert mls.logic_threshold_high_voltage == pytest.approx(expected)

    @pytest.mark.parametrize("vdd, threshold_low, expected", [
        (5.0, 0.2, 1.0),    # 標準5V
        (3.3, 0.2, 0.66),   # 3.3V系
        (1.8, 0.2, 0.36),   # 1.8V系
        (5.0, 0.3, 1.5),    # 閾値30%
    ])
    def test_LOW閾値電圧(self, vdd, threshold_low, expected):
        mls = MyLibrarySetting(vdd_voltage=vdd, logic_threshold_low=threshold_low, voltage_unit="V")
        mls.update_mag()
        mls.update_threshold_voltage()
        assert mls.logic_threshold_low_voltage == pytest.approx(expected)

    @pytest.mark.parametrize("vdd, threshold, expected", [
        (5.0, 0.5, 2.5),   # 標準5V 50%
        (3.3, 0.5, 1.65),  # 3.3V系 50%
        (5.0, 0.4, 2.0),   # 40%
    ])
    def test_LOW_to_HIGH閾値電圧(self, vdd, threshold, expected):
        mls = MyLibrarySetting(vdd_voltage=vdd, logic_low_to_high_threshold=threshold, voltage_unit="V")
        mls.update_mag()
        mls.update_threshold_voltage()
        assert mls.logic_low_to_high_threshold_voltage == pytest.approx(expected)
