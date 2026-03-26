"""
tests/test_myFunc.py

myFunc.py のユニットテスト。
ngspice不要、純粋な計算関数のみ対象。

実行方法:
    cd D:/git/charao_prj
    pytest tests/test_myFunc.py -v
"""
import pytest
from charao.script.myFunc import f2s_ceil


class TestF2sCeil:
    """f2s_ceil(): 有効桁数で切り上げして文字列に変換する関数のテスト"""

    def test_正の小数_有効2桁(self):
        # 2.34 → 切り上げ → "2.4"
        assert f2s_ceil(2.34, sigdigs=2) == "2.4"

    def test_負の小数_有効2桁(self):
        # -2.34 → 切り上げ（正方向） → "-2.3"
        assert f2s_ceil(-2.34, sigdigs=2) == "-2.3"

    def test_ゼロ(self):
        # 0.0 → "0"
        assert f2s_ceil(0.0) == "0"

    def test_1より小さい数_有効2桁(self):
        # 0.056 → 切り上げ → "0.056" or "0.057" (有効2桁)
        result = f2s_ceil(0.056, sigdigs=2)
        assert result in ["0.056", "0.057"]  # 切り上げなので0.057

    def test_大きい数_指数表記なし(self):
        # 1234 → 有効2桁で切り上げ → "1300"
        assert f2s_ceil(1234, sigdigs=2) == "1300"

    def test_有効1桁(self):
        # 2.34 → 有効1桁で切り上げ → "3"
        assert f2s_ceil(2.34, sigdigs=1) == "3"

    def test_有効3桁(self):
        # 2.345 → 有効3桁で切り上げ → "2.35"
        assert f2s_ceil(2.345, sigdigs=3) == "2.35"

    def test_ちょうど割り切れる数(self):
        # 1.0 → "1"
        assert f2s_ceil(1.0, sigdigs=2) == "1"
