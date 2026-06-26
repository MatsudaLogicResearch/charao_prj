# SPEC_const.md — setup / hold / recovery / removal 計測仕様

charao の **const 系 measure**（setup / hold / recovery / removal、 別名 timing constraint）の計測仕様。

ISS-00133（2026-06-15 ダーマツ承認、 2026-06-11 起票）に基づく確定設計。

---

## 1. 計測対象（4 measure × FF/LAT × clock/async）

8 entry の全体像：

| # | measure | FF/LAT | pin_tr | pin_oirc | 計測対象遅延 | 判定対象 | 判定種別 | sweep |
|---|---|---|---|---|---|---|---|---|
| 1 | setup | FF | `[i0, c0]` | `[o0, i0, c0, c0]` | `dly_in_clk`: VIN→VCLK | `judge_dly`: VCLK→VOUT | 遅延 | `_t_clk4` |
| 2 | setup | LAT | `[i0, c0]` | `[o0, i0, c0, c0]` | `dly_in_clk`: VIN→VCLK(E↓) | `judge_dly`: VIN→VOUT | 遅延 | `_t_clk4` |
| 3 | hold | FF | `[i0, c0]` | `[o0, i0, c0, c0]` | `dly_clk_in`: VCLK→VIN | `judge_vlt_max/min` | 電圧 | `_t_clk4` |
| 4 | hold | LAT | `[i0, c0]` | `[o0, i0, c0, c0]` | `dly_clk_in`: VCLK(E↓)→VIN | `judge_vlt_max/min` | 電圧 | `_t_clk4` |
| 5 | recovery | FF | `[r0/s0, c0]` | `[o0, i0, r0/s0, c0]` | `dly_rel_clk`: VREL→VCLK | `judge_dly`: VCLK→VOUT | 遅延 | `_t_clk4` |
| 6 | recovery | LAT | `[r0/s0, c0]` | `[o0, i0, r0/s0, c0]` | `dly_rel_clk`: VREL→VCLK(E↓) | `judge_dly`: VREL→VOUT | 遅延 | `_t_clk4` |
| 7 | removal | FF | `[r0/s0, c0]` | `[o0, i0, r0/s0, c0]` | `dly_clk_rel`: VCLK→VREL | `judge_vlt_max/min` | 電圧 | `_t_clk4` |
| 8 | removal | LAT | `[r0/s0, c0]` | `[o0, i0, r0/s0, c0]` | `dly_clk_rel`: VCLK(E↓)→VREL | `judge_vlt_max/min` | 電圧 | `_t_clk4` |

---

## 2. MEASURE 命名（jp2 出力の変数名、 7 個）

### 2.1 計測対象遅延（4 個、 各 measure 専用、 lib 出力値）

| MEASURE 名 | 内容 | 使用関数 |
|---|---|---|
| `dly_in_clk` | TRIG VIN → TARG VCLK | setup 関数 |
| `dly_clk_in` | TRIG VCLK → TARG VIN | hold 関数 |
| `dly_rel_clk` | TRIG VREL → TARG VCLK | recovery 関数 |
| `dly_clk_rel` | TRIG VCLK → TARG VREL | removal 関数 |

### 2.2 判定対象（3 個、 setup/recovery と hold/removal で共通）

| MEASURE 名 | 内容 | 使用関数 |
|---|---|---|
| `judge_dly` | TRIG/TARG は **pin_tr × is_lat で切替**（次節参照） | setup / recovery 関数（遅延判定） |
| `judge_vlt_max` | `MAX V(VOUT) FROM={_t_clk4} TO={_t_clk5+10e-9}` | hold / removal 関数（電圧判定） |
| `judge_vlt_min` | `MIN V(VOUT) FROM={_t_clk4} TO={_t_clk5+10e-9}` | hold / removal 関数（電圧判定） |

---

## 3. jp2 内の `judge_dly` の TRIG/TARG 分岐

`pin_tr[0]` × `is_lat` の 4 パターンで切替：

| pin_tr[0] | is_lat | TRIG | TARG | 物理意味 |
|---|---|---|---|---|
| `i0` | False (FF) | `v(VCLK)` | `v(VOUT)` | CLK active edge → Q（CLK→Q delay） |
| `i0` | True (LAT) | `v(VIN)` | `v(VOUT)` | D → Q（D→Q transparent delay） |
| `r0` / `s0` | False (FF) | `v(VCLK)` | `v(VOUT)` | CLK active edge → Q（CLK→Q delay） |
| `r0` / `s0` | True (LAT) | `v(VREL)` | `v(VOUT)` | async → Q（async→Q delay） |

### 3.1 jp2 実装イメージ

```jinja
{# ====== 計測対象遅延（pin_tr[0] で切替） ====== #}
{%- if param.pin_tr[0] == "i0" %}
  .MEASURE TRAN dly_in_clk  TRIG v(VIN)  TARG v(VCLK)
  .MEASURE TRAN dly_clk_in  TRIG v(VCLK) TARG v(VIN)
{%- elif param.pin_tr[0] in ["r0", "s0"] %}
  .MEASURE TRAN dly_rel_clk TRIG v(VREL) TARG v(VCLK)
  .MEASURE TRAN dly_clk_rel TRIG v(VCLK) TARG v(VREL)
{%- endif %}

{# ====== 判定対象（遅延） ====== #}
{%- if param.pin_tr[0] == "i0" %}
  {%- if param.is_lat %}
    .MEASURE TRAN judge_dly TRIG v(VIN) TARG v(VOUT)
  {%- else %}
    .MEASURE TRAN judge_dly TRIG v(VCLK) TARG v(VOUT)
  {%- endif %}
{%- elif param.pin_tr[0] in ["r0", "s0"] %}
  {%- if param.is_lat %}
    .MEASURE TRAN judge_dly TRIG v(VREL) TARG v(VOUT)
  {%- else %}
    .MEASURE TRAN judge_dly TRIG v(VCLK) TARG v(VOUT)
  {%- endif %}
{%- endif %}

{# ====== 判定対象（電圧） ====== #}
.MEASURE TRAN judge_vlt_max MAX V(VOUT) FROM={_t_clk4} TO={_t_clk5+10e-9}
.MEASURE TRAN judge_vlt_min MIN V(VOUT) FROM={_t_clk4} TO={_t_clk5+10e-9}
```

### 3.2 pin_oirc[i]=="" による voltage source 駆動省略

`pin_oirc[i]=""` の voltage source 駆動を省略すると、 「変化のないパタン」 で sim 早期終了が可能：

```jinja
{%- if param.pin_oirc[1] != "" %}
  VIN VIN 0 PWL(...)
{%- endif %}
{%- if param.pin_oirc[2] != "" %}
  VREL VREL 0 PWL(...)
{%- endif %}
{%- if param.pin_oirc[3] != "" %}
  VCLK VCLK 0 PWL(...)
{%- endif %}
```

---

## 4. charao_run.py の 4 関数化

const 系を **4 関数** に整理。 FF/LAT 共通（関数内に FF/LAT 分岐なし、 jp2 で吸収）。

| 関数 | 対象 measure | sweep | 計測 MEASURE | 判定 MEASURE |
|---|---|---|---|---|
| `runSpiceSetupSingle` | setup_rising / setup_falling | `_t_clk4` | `dly_in_clk` | `judge_dly`（遅延判定、 degradation 検出） |
| `runSpiceHoldSingle` | hold_rising / hold_falling | `_t_clk4` | `dly_clk_in` | `judge_vlt_max` / `judge_vlt_min`（電圧判定） |
| `runSpiceRecoverySingle` | recovery_rising / recovery_falling | `_t_clk4` | `dly_rel_clk` | `judge_dly`（遅延判定） |
| `runSpiceRemovalSingle` | removal_rising / removal_falling | `_t_clk4` | `dly_clk_rel` | `judge_vlt_max` / `judge_vlt_min`（電圧判定） |

### 4.1 関数の擬似コード

```python
# setup（遅延判定、 degradation 検出）
def runSpiceSetupSingle(harness, ...):
    rslt = run_sim(...)
    meas_val  = float(rslt["dly_in_clk"])      # lib 出力値（setup time）
    judge_val = abs(float(rslt["judge_dly"])) # 判定値
    # secant: judge_val 前回比較で degradation 検出
    ...

# hold（電圧判定）
def runSpiceHoldSingle(harness, ...):
    rslt = run_sim(...)
    meas_val = float(rslt["dly_clk_in"])
    o_max_v  = float(rslt["judge_vlt_max"])
    o_min_v  = float(rslt["judge_vlt_min"])
    # secant: ival_o から逸脱で break
    if   ival_o == "0" and o_max_v > threshold_low:  break
    elif ival_o == "1" and o_min_v < threshold_high: break
    ...

# recovery（setup と類似、 遅延判定）
def runSpiceRecoverySingle(harness, ...):
    rslt = run_sim(...)
    meas_val  = float(rslt["dly_rel_clk"])
    judge_val = abs(float(rslt["judge_dly"]))
    ...

# removal（hold と類似、 電圧判定）
def runSpiceRemovalSingle(harness, ...):
    rslt = run_sim(...)
    meas_val = float(rslt["dly_clk_rel"])
    o_max_v  = float(rslt["judge_vlt_max"])
    o_min_v  = float(rslt["judge_vlt_min"])
    ...
```

### 4.2 既存関数との対応

| 旧関数 | 新関数 |
|---|---|
| `runSpiceSetupSingle`（既存、 FF 専用） | `runSpiceSetupSingle`（FF/LAT 統合） |
| `runSpiceLatSetupSingle`（既存、 LAT 専用） | `runSpiceSetupSingle` に統合 |
| `runSpiceHoldSingle`（既存、 FF 専用） | `runSpiceHoldSingle`（FF/LAT 統合） |
| `runSpiceLatHoldSingle`（既存、 LAT 専用） | `runSpiceHoldSingle` に統合 |
| （recovery/removal は既存関数で setup/hold と共用） | `runSpiceRecoverySingle` / `runSpiceRemovalSingle` で分離 |

---

## 5. pin_oirc 規則（const 系）

### 5.1 規則

- `pin_oirc[0]=o0`（VOUT=Q 出力観察）
- `pin_oirc[1]=i0`（VIN=D 駆動、 const 系全 measure 共通）
- `pin_oirc[2]` = **`pin_tr` の中で sweep される側**：
  - setup / hold（pin_tr=[i0,c0]）：`pin_oirc[2]=c0`（VREL=CLK/E 駆動、 sweep される側）
  - recovery / removal（pin_tr=[r0/s0,c0]）：`pin_oirc[2]=r0/s0`（VREL=async 駆動、 sweep される側）
- `pin_oirc[3]=c0`（VCLK=CLK/E 駆動）

### 5.2 sweep される側 = pin_oirc[2] の理由

charao の secant は **`_t_clk4` を sweep**（VCLK position）。 ただし「sweep される物理的対象」 は const 系の文脈で：
- setup/hold：CLK/E のタイミング（VREL=CLK/E と VCLK=CLK/E は同一 pin 駆動 → どちらが動いても同じ）
- recovery/removal：async のタイミング（VREL=async が driver、 VCLK=CLK/E が固定）

実装上は **`_t_clk4`（VCLK position）を動かす**ことで両ケース対応。

---

## 6. FF/LAT 差の吸収方法

| 観点 | FF | LAT | 吸収方法 |
|---|---|---|---|
| VCLK 波形 | CLK pulse（init phase）+ active edge（計測 phase） | E=H stable（init）+ E↓ closure（計測） | `ival[c]` / `arc[3]` の値で表現 |
| `judge_dly` の TRIG | VCLK | VIN（setup/hold）or VREL（recovery/removal） | jp2 で `is_lat` 分岐 |
| `judge_vlt_max/min` | 共通 | 共通 | 分岐不要 |
| charao_run 関数 | 共通 | 共通 | 関数内 FF/LAT 分岐なし |

---

## 7. 参照

- ISS-00133（charao_prj.md）：本仕様の起票・確定経緯
- ISS-00127（charao_prj.md）：pin_oirc + pin_tr 分離（前提）
- SPEC_pin_oirc.md：pin_oirc / pin_tr の基本ルール
- SPEC_ival.md：ival / arc_oirc の定義
