# SPEC_const.md — setup / hold / recovery / removal 計測仕様

charao の **const 系 measure**（setup / hold / recovery / removal、 別名 timing constraint）の計測仕様。

ISS-00133（2026-06-15 ダーマツ承認、 2026-06-11 起票）に基づく確定設計。

> **改訂（2026-07-11、 TAG:0.9.14a28 時点の現行実装）**
> 本書の初版（ISS-00133 設計）から以下が更新されている。 §1/§2/§4 は現行に改訂済み、 それ以外の節は初版のまま（考え方は有効）。
> - **ISS-00138**：setup/hold/recovery を統一パス `runSpiceConstMultiThread/Single` に集約し、 判定を **`prop_clk_out` の degradation（遅延劣化）** に統一（judge_dly は jp2 に出力されるが判定には未使用）。 removal のみ電圧判定の別関数のまま
> - **ISS-00143**：LAT の dispatch も統一パスへ（旧 LAT 専用関数は不達 dead code、 ISS-00148 で削除予定）
> - **ISS-00152**：**vout_infos 機構**＝const 系 MEASURE の観測点（VOUT）をセル固有の内部 net に置換可能（ICG は QD。 jsonc の `vout_infos` で指定）。 tsim_end を毎反復 `max(t_clk5, t_in1, t_rel1)+3ns` に短縮（擬似ハング解消）
> - **ISS-00153**：**保持型 hold（LAT/ICG＝is_lat、 保持成功＝Q 無遷移）は degradation 不可のため電圧化け判定に分岐**（judge_vlt_max/min、 窓=`_t_clk4.._tsim_end`）。 FF hold は degradation のまま。 is_lat は `mls.logic_dict[mlc.logic]["logic_type"]=="seq_lat"` の辞書引き（Mlc 属性ではない）。 hold の seg_end を `t_in1+2*tslew_clk` へ延長、 保持型は seg_start を `_t_init3+2ns` に clamp

---

## 1. 計測対象（4 measure × FF/LAT × clock/async）

8 entry の全体像（判定列は 2026-07-11 現行）：

| # | measure | FF/LAT | pin_tr | pin_oirc | 計測対象遅延 | 判定対象 | 判定種別 | sweep |
|---|---|---|---|---|---|---|---|---|
| 1 | setup | FF | `[i0, c0]` | `[o0, i0, "", c0]` | `dly_in_clk`: VIN→VCLK | `prop_clk_out` | 遅延 degradation | `_t_clk4` |
| 2 | setup | LAT | `[i0, c0]` | `[o0, i0, "", c0]` | `dly_in_clk`: VIN→VCLK(E↓) | `prop_clk_out`（vout_infos 置換可） | 遅延 degradation | `_t_clk4` |
| 3 | hold | FF | `[i0, c0]` | `[o0, i0, "", c0]` | `dly_clk_in`: VCLK→VIN | `prop_clk_out` | 遅延 degradation | `_t_clk4` |
| 4 | hold | LAT/ICG | `[i0, c0]` | `[o0, i0, "", c0]` | `dly_clk_in`: VCLK(E↓)→VIN | `judge_vlt_max/min`（vout_infos 置換可） | **電圧（ISS-00153）** | `_t_clk4` |
| 5 | recovery | FF | `[r0/s0, c0]` | `[o0, i0, r0/s0, c0]` | `dly_rel_clk`: VREL→VCLK | `prop_clk_out` | 遅延 degradation | `_t_clk4` |
| 6 | recovery | LAT | `[r0/s0, c0]` | `[o0, i0, r0/s0, c0]` | `dly_rel_clk`: VREL→VCLK(E↓) | `prop_clk_out`（vout_infos 置換可） | 遅延 degradation | `_t_clk4` |
| 7 | removal | FF | `[r0/s0, c0]` | `[o0, i0, r0/s0, c0]` | `dly_clk_rel`: VCLK→VREL | `judge_vlt_max/min` | 電圧 | `_t_clk4` |
| 8 | removal | LAT | `[r0/s0, c0]` | `[o0, i0, r0/s0, c0]` | `dly_clk_rel`: VCLK(E↓)→VREL | `judge_vlt_max/min` | 電圧 | `_t_clk4` |

**判定方式の選択則**：出力挙動の型で決まる。 **遷移型**（capture/解放で Q が必ず遷移＝FF setup/hold、 FF/LAT recovery、 LAT setup）→ degradation。 **保持型**（保持成功＝Q 無遷移＝LAT/ICG hold、 removal）→ 電圧化け判定（full-swing 反転で fail、 arc[0] 規約："0"/"r"=保持 L・違反で上昇、 "1"/"f"=保持 H・違反で下降）。

---

## 2. MEASURE 命名（jp2 出力の変数名、 7 個）

### 2.1 計測対象遅延（4 個、 各 measure 専用、 lib 出力値）

| MEASURE 名 | 内容 | 使用関数 |
|---|---|---|
| `dly_in_clk` | TRIG VIN → TARG VCLK | setup 関数 |
| `dly_clk_in` | TRIG VCLK → TARG VIN | hold 関数 |
| `dly_rel_clk` | TRIG VREL → TARG VCLK | recovery 関数 |
| `dly_clk_rel` | TRIG VCLK → TARG VREL | removal 関数 |

### 2.2 判定対象（2026-07-11 現行）

| MEASURE 名 | 内容 | 使用箇所 |
|---|---|---|
| `prop_clk_out` | TRIG VCLK → TARG VOUT（vout_infos 置換可）。 **degradation 判定の実体**（ISS-00138。 pass 側で不成立なら default=1 → step 検出） | 統一 const（setup / recovery / FF hold） |
| `judge_dly` | TRIG/TARG は **pin_tr × is_lat で切替**（次節参照）。 jp2 に出力されるが**現行判定では未使用**（補助計測） | setup / recovery（is_lat 分岐あり） |
| `judge_vlt_max` | hold: `MAX V(観測ノード) FROM={_t_clk4} TO={_tsim_end}`（ISS-00153、 is_lat のみ出力）／ removal: `TO={_t_clk5+10e-9}` | LAT/ICG hold・removal（電圧判定） |
| `judge_vlt_min` | 同上の MIN | 同上 |

観測ノードは `vout_infos` 指定時 `v(xcell.xdut.<net>)`、 未指定時 `v(VOUT)`（ISS-00152）。
FF hold に judge_vlt を出さないのは MAX/MIN measure が autostop を無効化するため（ISS-00138 の高速化を維持）。

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

## 4. charao_run.py の関数構成（2026-07-11 現行）

初版の「4 関数化」案から、 **ISS-00138 で setup/hold/recovery を統一 1 関数に集約**（removal のみ別関数）した。
FF/LAT 共通（jp2 の is_lat 分岐で吸収）。

| 関数 | 対象 measure | sweep | 計測 MEASURE | 判定 |
|---|---|---|---|---|
| `runSpiceConstSingle`（統一） | setup_\* / hold_\* / recovery_\* | `_t_clk4` | `dly_in_clk` / `dly_clk_in` / `dly_rel_clk`（measure_type で切替） | degradation（`prop_clk_out`）。 **hold × is_lat のみ電圧判定**（`judge_vlt_max/min`、 ISS-00153） |
| `runSpiceRemovalSingle` | removal_rising / removal_falling | `_t_clk4` | `dly_clk_rel` | `judge_vlt_max` / `judge_vlt_min`（電圧判定） |

### 4.0 統一 const の sweep 範囲（ISS-00152/00153）

- setup/recovery：`seg_start=0` → `seg_end = tsweep_for_clk4_at((t_init3+t_in0)/2)`
- hold：`seg_start = tsweep_for_clk4_at(t_in0) − 0.5*(t_in0−t_init3) − tslew_clk` → `seg_end = tsweep_for_clk4_at(t_in1 + 2*tslew_clk)`（fail 領域まで掃引）
- **保持型（is_lat）hold の clamp**：`seg_start = max(seg_start, tsweep_for_clk4_at(t_init3 + 2ns))`。 clk_init pulse を持つセル（ICG）は VIN の capture 遷移が `_t_init3` 固定アンカーのため、 clamp なしでは judge 窓に正当な取り込み遷移が入り初手 FAIL で探索不能になる
- tsim_end は毎反復 `max(t_clk5, t_in1, t_rel1) + 3ns` に短縮（autostop 不成立ケースの擬似ハング防止、 hold の D 戻りは max に含めて保護）

### 4.1 初版設計（ISS-00133）の擬似コード（参考。 現行実装は §4.0/§4.2 のとおり）

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

### 4.2 既存関数との対応（現行）

| 旧関数 | 現行 |
|---|---|
| `runSpiceSetupSingle` / `runSpiceHoldSingle`（FF 用） | `runSpiceConstSingle` に統合（ISS-00138） |
| `runSpiceLatSetupSingle_orig` / `genFileLogic_LatSetup1x_orig`（LAT 用） | 不達 dead code（ISS-00143 で dispatch 統一、 ISS-00148 で削除予定） |
| `runSpiceRemovalSingle` | 電圧判定のまま存置（保持型のため degradation 不可） |

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

## 7. sweep の時短（start_offset / nodeset、ISS-00220）

const は **1 格子点あたり約 30 sim** 回るが、掃引で変わるのは制約信号 / CLK の相対位置だけで、
**初期化フェーズより前の内部状態は全掃引点で共通**である。にもかかわらず毎回 0 から回し直していた。

```
sky130 dfxtp_1 setup_rising の 1 sim（24.509 ns）の内訳
  0      〜 19.009 ns   初期化（pre-charge / 状態確立 / 待機 / D 遷移）
  19.009 〜 24.509 ns   測定区間（CLK 遷移と Q の応答）
```

### 7.1 方式

```
0 回目（準備 run）  掃引位置は seg_start 固定、start_offset = 0
                    ・maxstep を反復収束（probe = simulation_points_per_transition）
                    ・_t_init3 + 0.4 ns 時点の内部ノード電圧を .meas find で取得
                    → <meas dir>/nodeset_<arc>_c<index1>_r<index2>.sp を書く

1 回目以降（掃引）   start_offset = -(_t_init3 + 0.4 ns) を負値で渡す
                    ・jp2 が .include で nodeset を読み、全時刻に + _t_ofs する
                    → 測定区間だけを回す。全掃引点が同一処理（分岐なし）
```

**Python 側は元の時間軸を保持し、加算は jp2 だけが行う**（`param.t_*` を書き換えると二重加算になる）。

### 7.2 実装上の要点

| 項目 | 内容 |
|---|---|
| **時刻のシフト** | jp2 が `.param _t_ofs` を置き、`_t_init0..3` / `_t_in0,1` / `_t_rel0..3` / `_t_clk0..7` / `_tsim_end` の **18 行に `+ _t_ofs`** する |
| **PWL の先頭点** | `VPC_CTRL` の `PWL(0 ...)` と `VIN`/`VREL`/`VCLK` の `PWL({_tslew_min} ...)` **17 箇所にも offset**。これを忘れると**先頭だけ固定・2 点目以降が負値で時刻が逆行**し PWL が不正になる |
| **負時刻 PWL** | `t=0` の値は「0ns に最も近い点から補間」される（実測確認済み）。`.tran` の `tstart` は **0 のまま**。`tstart` を使っても `0〜tstart` は計算されるので短縮にならない |
| **状態の復元** | **`nodeset` を使う**（`uic` は DC を飛ばすので捕捉漏れで破綻する）。内部ノードは `myLogicCell.get_internal_nodes()` が netlist から自動抽出 |
| **再開時刻** | `_t_init3 + 0.4 ns`。`_t_init3` は **pre-charge SW（`VPC_CTRL`）が OFF になる瞬間**で、内部ノードに約 0.4 ns のオーバーシュートが残る（実測で `net10` が VDD+1.38V） |
| **掃引の下限** | `seg_start` / `seg_end` を **`_t_init3 + 0.4 ns` 以降**にクランプし、CLK が再開時刻より前に来ないようにする |
| **nodeset ファイル名** | **arc を含める**（`nodeset_<arc>_c<i1>_r<i2>.sp`）。含めないと同一格子点の rise/fall arc で**上書きが起きて論理が反転する** |
| **`chg_out` の補正** | `chg_out` は `WHEN` 形式で**絶対時刻**を返すため、読み出し時に offset を戻す。`TRIG/TARG` 形式（`prop_*` / `dly_*` / `judge_dly` / `trans_out`）は**差分なので相殺され不要** |

### 7.3 有効化と効果

`config_lib.jsonc` の **`const_start_offset_enable`**（既定 `true`）。`false` で従来動作。

```
gf180 latrnq_1 + dffrnq_1 × const 6 measure × 10×10（全 1000 点）
  高精度（false）  2503 秒
  中精度（true）   1719 秒      1.46 倍

  値のずれ   |差| = 0     476/1000（47.6% が完全一致）
             |差| ≦ 0.010  837/1000
             |差| ≦ 0.050 1000/1000（全点）
             最大          0.0490 ns
```

**「長時間・高精度／短時間・中精度」で使い分ける。** 参考として、同じデータの
**charao vs orig は最大 0.393 ns**（`|0.1ns|` 以内 241/1000）なので、**高速化由来のずれはその 1/8**。

**既知の限界**：`net9` のような **VDD を超えるブートストラップ的な定常値**を持つノードは、
`nodeset`（DC 反復の初期推定値）では再現できない（DC に存在しない状態のため）。
ずれの主因はこれで、`dffrnq_1` の `recovery_rising`（`index1` 小・`index2` 大）に集中する。

### 7.4 ログ

`maxstep` 確定時に `[INFO] maxstep_fix` を出す。`.lib` に出ない量なので、
これが無いと `work`（`.sp` / `.lis`）を回収しないと解析できない。

```
[INFO] maxstep_fix <cell>/vt_<vdd>_<temp>_<n>_<meas>/oir=<oirc>_arc=<arc>_c<i1>_r<i2> \
       maxstep=7.6577e-12 vout_trans=1.48317e-11 pts=1.94
```

識別子は **`.sp` の命名から `_sXX`（掃引点）を除いた形**。マルチスレッド実行で行が混ざっても
対象を特定できる。

---

## 8. 参照

- ISS-00133（charao_prj.md）：本仕様の起票・確定経緯
- ISS-00127（charao_prj.md）：pin_oirc + pin_tr 分離（前提）
- SPEC_pin_oirc.md：pin_oirc / pin_tr の基本ルール
- SPEC_ival.md：ival / arc_oirc の定義
