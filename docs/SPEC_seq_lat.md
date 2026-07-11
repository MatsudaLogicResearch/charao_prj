# Sequential LATCH cell support specification

このドキュメントは charao における順序回路（level-sensitive Latch）の
キャラクタライズ規約をまとめたものです。
GF180 PDK の `latq` / `latrnq` / `latsnq` / `latrsnq` を対象とします。

D-Flip-Flop / Scan-DFF は `docs/SPEC_seq_ff.md` を参照。

> **改訂（2026-07-11、 TAG:0.9.14a27〜a28 反映）**
> - **ICG（clock gating cell、 icgtp/icgtn）は本 SPEC の枠組みで `mylogic_seq_lat.py` に実装済み**
>   （logic_type="seq_lat"、 ICG_PC/ICG_NC 各 36 entry。 内部ラッチ＋AND/OR 構造、
>   E/TE の setup/hold は内部ラッチ closure 基準＝LAT と同型）。 「別 SPEC 追加予定」 は解消
> - **vout_infos 機構（ISS-00152）**：ICG は Q がクロックにマスクされる（Q=CLK&IQ2）ため、
>   const 系 MEASURE の観測点を jsonc の `"vout_infos":{"o0":{"node":"QD"}}` で内部ラッチ出力へ置換する
> - **const の判定方式（ISS-00138/00153）**：setup/recovery＝prop_clk_out の degradation、
>   **LAT/ICG の hold＝電圧化け判定（judge_vlt、 removal と同方式）**。 詳細は `SPEC_const.md` §1 の
>   現行表を参照。 §7-1 の旧関数（runSpiceLat*Single）は ISS-00143 で統一パスに置換済み（dead code、
>   ISS-00148 で削除予定）

## 1. 目的

- level-sensitive Latch family を charao で characterize する規約を定める
- DFF（edge-triggered）との harness 差異、 特に **clk_init（E 端子の初期化方式）** の判定基準を明確化
- LATCH 必要 measure 項目（12 項目）を確定する

## 2. GF180 命名規則と charao logic 名のマッピング

GF180 std cell の `lat[r][s]nq` 命名規則：

| 要素 | 意味 |
|---|---|
| `lat` | level-sensitive Latch |
| `[r]` | active-low reset `RN` 入力 |
| `[s]` | active-low set `SETN` 入力 |
| `nq` | 末尾の `n` は表記上の慣例、 **出力は Q-direct** |

| GF180 cell | charao logic | enable | reset | set |
|---|---|---|---|---|
| latq | LATCH_PE | E=H 透過 | – | – |
| latrnq | LATCH_PE_NR | E=H 透過 | active-low | – |
| latsnq | LATCH_PE_NS | E=H 透過 | – | active-low |
| latrsnq | LATCH_PE_NR_NS | E=H 透過 | active-low | active-low |

`PE` = **Positive Enable**（E=H で transparent、 E=L で latch）。
SPICE 実動作（真理値表）で確定：
- E=H → transparent（D→Q 透過）、 E=L → latch（hold）
- RN=0 → reset（Q=0）、 SETN=0 → set（Q=1）、 ともに active-low
- RN=0 & SETN=0 の競合は **set 優先（Q=1）**
- RN=1 & SETN=1（両 inactive）で通常 latch 動作

## 3. LATCH の timing 制約は closure edge（E↓）基準

latch は transparent window `[E↑(open) … E↓(close)]` の中で D が安定すべき。
D / RN / SETN の setup / hold / recovery / removal 制約は、 **すべて closure edge
（enable が inactive になる edge = LATCH_PE では E↓）基準**で定義される（`_falling`）。

| 制約 | related edge | timing_type |
|---|---|---|
| setup（D vs E）| E↓（closure）| `setup_falling` |
| hold（D vs E）| E↓（closure）| `hold_falling` |
| recovery（RN/SETN vs E）| E↓（closure）| `recovery_falling` |
| removal（RN/SETN vs E）| E↓（closure）| `removal_falling` |

これは **gf180 オリジナル Liberty（latrsnq_1 等）と一致**する。 gf180 の latrsnq_1 では
pin(D) が `hold_falling`/`setup_falling`、 pin(RN)/pin(SETN) が `recovery_falling`/
`removal_falling`（いずれも related=E）。 hold も「E↓ closure 後に D が保持すべき時間」
として E↓ 基準（`hold_rising` ではない）。

**falling_edge（E↓→Q）が無い理由**：E↓（latch close）で Q は直前の透過値を保持し
変化しないため、 E↓→Q の遷移 arc は物理的に存在しない（`rising_edge`（E↑→Q）のみ）。

## 4. LATCH 必要 measure 項目（12 項目）

`t_rel` 列は related pin の遷移（measure の arc 構造）を、 `t_init* での状態` 列は
init phase 初期状態の E / RN・SETN を示す。 **clk_init は後者（t_init*）で決まる**（§5 参照）。

| # | measure 項目 | measure_type | t_rel（related 遷移）| t_init* での状態 | clk_role | clk_init |
|---|---|---|---|---|---|---|
| 1 | reset | `clear` | RN↓ | E=L, RN/SETN inactive | nouse | pulse |
| 2 | preset | `preset` | SETN↓ | E=L, RN/SETN inactive | nouse | pulse |
| 3 | setup | `setup_falling` | E↓ | E=H, RN/SETN inactive | related | stable |
| 4 | hold | `hold_falling` | E↓ | E=H, RN/SETN inactive（→§5 段2）| related | stable |
| 5 | recovery | `recovery_falling` | E↓ | RN/SETN active（解除前、→§5 段1）| related | stable |
| 6 | removal | `removal_falling` | E↓ | RN/SETN active（→§5 段1）| related | stable |
| 7 | delay | `delay`（D→Q 透過）| D 遷移 | E=H, RN/SETN inactive | nouse | stable |
| 7′ | delay | `rising_edge`（E↑→Q）| E↑ | E=L, RN/SETN inactive | related | pulse |
| 8 | power_tout | `power_tout` | 併記 arc に従う | 併記 arc に従う | — | 併記 arc 準拠 |
| 9 | power_tin | `power_tin` | D/E/RN/SETN 遷移 | entry 個別 | input / nouse | entry 個別判定 |
| 10 | min_pulse_width | `min_pulse_width_high`（E）| E↑ | E=L, RN/SETN inactive | related | pulse |
| 10′ | min_pulse_width | `min_pulse_width_low`（RN/SETN）| RN/SETN↓ | E=L, RN/SETN inactive | nouse | pulse |
| 11-A | passive | `passive` | なし | RN active or SETN active | nouse | stable |
| 11-C | passive | `passive` | なし | RN/SETN inactive & E=L | nouse | pulse |
| 12-A | leakage | `leakage` | なし | RN active or SETN active | nouse | stable |
| 12-B | leakage | `leakage` | なし | RN/SETN inactive & E=H | nouse | stable |
| 12-C | leakage | `leakage` | なし | RN/SETN inactive & E=L | nouse | pulse |

注：
- `t_rel`（related 遷移）と `t_init* での状態` は別軸。 clear は t_rel で RN↓ するが
  t_init* では RN inactive、 setup は t_rel で E↓ するが t_init* では E=H、 のように
  **遷移する信号は t_init* 時点（遷移前）の状態を記載**している
- `power_tout` は独立 measure ではなく、 各 arc（delay/rising_edge/clear/preset）entry の
  `meas_types` に併記される（clk_init は併記 arc に従う）
- `power_tin` は振る pin（D/E/RN/SETN）と when 条件で t_init* の状態が変わるため entry 個別判定
- `passive` は 2 条件（A・C）、 `leakage` は 3 条件（A・B・C）で entry を分ける（§6.1 参照）

## 5. clk_init 判定原則

`clk_init` は sim 開始時の VCLK（E 端子）の初期化方式：
- `stable` … E を DC 一定で印加（latch を D で制御）
- `pulse` … E に init phase の pulse を与え、 E↑ で D を透過させて Q を初期化

**判定は t_init*（init phase の初期状態）における E / RN / SETN の状態で行う**。
clk_init は E 端子の「初期化」 方式なので、 判定軸は初期状態（t_init*）でなければならない。
RN/SETN や E は measure 中に遷移する（clear で RN↓、 setup/hold で E↓/E↑ 等）が、
clk_init 判定には遷移後ではなく **t_init* 時点（遷移前）の状態**を使う。
clk_role（`pin_oirc[2]=="c0"→related` 等）は c0 の役割を見るだけで clk_init を決められない。

判定原則（t_init* の初期状態で判定、 上から優先、 全 measure 共通）：

| 優先 | t_init* での状態 | clk_init | 理由 |
|---|---|---|---|
| 1 | **RN active or SETN active**（Q が reset/set で固定）| stable | Q 初期化は reset/set で可、 E の pulse 不要 |
| 2 | RN/SETN inactive & **E=H**（init phase で transparent）| stable | latch transparent、 D で Q 初期化可 |
| 3 | RN/SETN inactive & **E=L**（init phase で closed）| pulse | latch closed、 init phase の E↑ で Q 初期化 |

t_init* は初期状態なので E は H/L の固定値（rising/falling という遷移概念は無い）。
要約：**t_init* で RN/SETN active なら無条件 stable**、 inactive なら **E=H → stable / E=L → pulse**。

注意（遷移する信号の扱い）：
- 判定は t_init*（init phase の初期状態）で行う。 measure 中に遷移する信号は遷移前
  （t_init*）の状態を使う
- **setup / hold**：t_init* で RN/SETN inactive & E=H → **段2 → stable**
- **recovery / removal**：対象の RN/SETN が t_init* で **active**（recovery は t_rel で
  release、 removal は E↓ 後も保持）→ **段1（RN/SETN active）→ stable**。
  E は t_init* で H だが、 判定は段1（active）で先に確定する
- **clear / preset**：t_init* で RN/SETN inactive & E=L → **段3 → pulse**

旧実装は `clk_init = "stable" if (islatch and clk_role=="nouse") else "pulse"`（clk_role
基準）で clear/preset/min_pulse_width_low（nouse だが pulse 必要）等を誤判定していたが、
§7（実装記録）の通り **t_init* 基準の 3 段判定に置き換え済み**（myConditionsAndResults.py）。

## 6. 補足知見

### 6.1 input capacitance の取得方法と passive の計測条件

#### input capacitance の計測方法

input capacitance は **C = Q / V** で求める：
- **Q** = related pin（振った pin）の電源（VIN/VREL/VCLK）を流れた電流の積分
  （`.MEASURE TRAN q_*_dyn INTEG I(V*)`）
- **V** = vdd_voltage（pin の遷移幅）
- charao_run.py の各 Single 関数で `c_in/c_rel/c_clk = abs(q_*_dyn)/vdd`、
  `cin = related pin の容量` を算出する

pin の電源電流は **その pin 自身の容量（ゲート容量＋透過負荷）の充放電のみ**で、
出力遷移の電流は VDD/VSS 側（`q_vdd_dyn`/`q_vss_dyn`）に出る。
→ **出力 Q が変化する条件でも input capacitance は正しく計測できる**。

#### input capacitance は passive 専用ではない

- 各 timing measure（delay/rising_edge/setup/hold/clear/preset/...）の sim でも、
  related pin の `cin` が計測される（power_tout 併載）
- `.lib` の `capacitance` は、 その pin を related にした**全 measure の cin の最大値**を
  採用する（`set_cin_max()`、 charao_run.py で呼ばれる。 `set_cin_avg` は不使用）

#### passive の計測条件（2 条件 A・C、 B は削除）

passive measure は、 timing arc で related にならない条件の input capacitance を
補完計測する。 計測条件は次の 2 条件：

| 条件 | 内部状態 | passive で測るか |
|---|---|---|
| A | RN active or SETN active（Q は reset/set で固定）| ○ |
| ~~B~~ | ~~RN/SETN inactive & E=H（D 透過、 Q 動く）~~ | **✗ 削除** |
| C | RN/SETN inactive & E=L（closed、 Q 不変）| ○ |

**条件 B を削除する理由**：条件 B（RN/SETN inactive & E=H で D を振る）は delay measure
（D→Q transparent）の sim 条件そのもので、 delay measure が related=D として D pin の
cin を計測する。 input capacitance は全 measure の最大値を採用するため、 passive で
条件 B を重複計測する必要はない。 passive は条件 A・C をカバーする。

### 6.2 power_tin と passive の違い

両者は **入力波形（振る pin・遷移方向・slew）が同じ**だが、 計測量と Liberty 出力先が異なる：

| | passive | power_tin |
|---|---|---|
| 計測量 | 入力 pin 電荷 → `capacitance` | VDD/VSS 電荷 → `internal_power` |
| Liberty 出力先 | pin の `capacitance` / `rise/fall_capacitance` | `internal_power` グループ |

testbench template（`temp_testbench.sp.jp2`）は共通で、 `meas_energy in [2,4,5]` のとき
`q_in_dyn`（容量）と `q_vdd_dyn`（電力）を同一 sim で同時に .meas している。
物理的には統合可能だが、 計測条件（passive は 2 条件 A・C、 power は slew index）が
異なるため **現状は別 measure_type として分離する**（2026-05-21 決定）。

### 6.3 leakage の Q 端子状態

leakage は Q の H/L で出力段リークパスが変わるため Q 状態も条件。 ただし Q は
基本的に入力（D/E/RN/SETN）の組合せから一意に決まる。 例外は条件 C（E=L closed &
RN/SETN inactive = hold 状態）で、 Q が過去依存になるため `ival o`（Q=0/1）で両状態を測る。

## 7. 実装記録

> §7-1（hold/removal の `_rising` 化）は **撤回**。 gf180 オリジナル Liberty（latrsnq_1）の
> latch timing は `hold_falling`/`setup_falling`/`recovery_falling`/`removal_falling` で
> 全て closure edge（E↓）基準であり、 charao の現状実装（`hold_falling`/`removal_falling`）
> が正しい（§3 参照）。 `_rising` 化は不要。

1. **clk_init ロジックの t_init* 基準 3 段判定化（myConditionsAndResults.py で一元管理）**【実装済み】：
   - `myConditionsAndResults.py` の `set_target_clkport()` の clk_init 計算を、 §5 の
     t_init* 基準 3 段判定（① RN/SETN active → stable、 ② inactive & E=H → stable、
     ③ inactive & E=L → pulse）に置き換え。 判定情報（`islatch` / `ival` の r,s,c）は
     `mec`（MyExpectCell）から参照し、 Single 関数を経由せず完結する
   - `runSpiceLatSetupSingle` / `runSpiceLatHoldSingle` の `param.clk_init="stable"`
     ハードコード上書きを削除し、 `h.clk_init`（一元判定値）を渡すよう変更。 clk_init の
     決定ロジックを myConditionsAndResults.py 1 箇所に集約（二重管理の解消）
   - これにより clear/preset/min_pulse_width_low が正しく `pulse` に決まり、
     **ISS-00092（latrsnq_1 clear の Q=1 初期化失敗）が解決**した

2. **leakage entry の E=H 条件を `arc s` 化**【実装済み】：leakage は静的測定なので
   E=H 条件を `ival c="1"`+`arc=[s,s,s,s]`（完全 stable）で表現する。 全 4 family
   （+PR_NS）の E=H 条件 leakage entry を修正済み。

3. **passive entry**【変更不要】：現状の passive entry は条件 A・C をカバーし、 条件 B は
   元々含まれていない（§6.1 修正後の「passive 2 条件、 B 削除」 に合致）。 input
   capacitance も `set_cin_max` 経由で .lib に正しく出力されるため、 変更不要。

## 8. 参照

- 関連 issue: ISS-00070（DFF/LAT/SDFF/ICGT 順序系）、 ISS-00090（LAT setup/hold harness）、
  ISS-00092（latrsnq_1 clear の Q=1 初期化）
- 関連 spec: `docs/SPEC_seq_ff.md`、 `docs/SPEC_internal_power.md`
- 実装ファイル: `charao/script/mylogic_seq_lat.py`、 `charao/script/charao_run.py`、
  `charao/script/myConditionsAndResults.py`、 `charao/script/temp_testbench.sp.jp2`、
  `sample/target/gf180/fd/mcuC7t20240817/std_seq.jsonc`
