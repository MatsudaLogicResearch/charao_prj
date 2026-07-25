# charao config_lib.jsonc パラメータ仕様書

`sample_target/<pdk>/<vendor>/<rev>/config_lib.jsonc` に記述するライブラリ全体設定パラメータの意味・単位・使い方を定義する。

セル個別の定義（`std_comb.jsonc` / `std_seq.jsonc` / `std_physical.jsonc` の `cell_info`）ではなく、**ライブラリ全体に効くスカラー設定**を対象とする。

---

## 1. 前提

- `config_lib.jsonc` は `charao.py` で読み込まれ、**`Mls(**config_lib)` として pydantic モデル `MyLibrarySetting` に展開**される
- したがって **jsonc に書けるキーは `myLibrarySetting.py` にフィールド宣言があるものに限られる**（未宣言キーはエラー）
- 各フィールドには **default 値**があり、jsonc に書かなければ default が使われる。**新規パラメータは「書かなければ従来動作」となる default を選ぶこと**（他 PDK の後方互換のため）

---

## 2. 単位の扱い（重要）

`config_lib.jsonc` の物理量は、原則として **同ファイルで指定した表示単位**で書く。

| 単位指定キー | 例 | 対応する内部倍率 |
|-------------|-----|----------------|
| `leakage_power_unit` | `"uW"` | `leakage_power_mag = 1e-6` |
| `capacitance_unit` | `"pf"` | `capacitance_mag` |
| `time_unit` | `"ns"` | `time_mag` |
| `energy_unit` | `"pJ"` | `energy_mag` |

charao 内部（sim 結果 `h.pleak` 等）は **SI 生値（W / F / s）** で保持し、`.lib` 出力時に `/ <unit>_mag` して表示単位へ戻す。

→ **表示単位で書かれた設定値を内部で使うときは `× <unit>_mag` して生値へ換算する**必要がある。`leakage_offset` はこの換算を行う代表例（§3.1）。

---

## 3. パラメータ詳細

### 3.1 `leakage_offset`（ISS-00165、2026-07-24 追加）

**全セルの leakage に一律加算する「嵩上げ値」。**

| 項目 | 内容 |
|------|------|
| 型 / default | `float` / `0.0`（＝嵩上げ無し。書かなければ従来動作） |
| 単位 | `leakage_power_unit` と同じ（gf180 は `uW`） |
| gf180 設定値 | `5e-05` |
| 適用範囲 | **全セル**（measure あり／なしを問わない） |

#### 記述例

```jsonc
  ,"leakage_power_unit" : "uW"
  ,"leakage_offset"     : 5e-05
```

#### 何のための値か

vendor の orig Liberty は、**SPICE simulation では再現できない一律の leakage 成分**を全セルに持つ。charao の sim はこの成分を測れないため、設定値として与えて加算する。

**実測による裏付け（gf180、2026-07-24）** — orig と charao 生計測値を同 when で突合：

| セル | orig | charao 計測 | orig − charao | orig ÷ charao |
|------|------|------------|---------------|--------------|
| inv_1 | 7.5450e-05 | 2.5498e-05 | 4.995e-05 | 2.96 |
| inv_4 | 1.5180e-04 | 1.0199e-04 | 4.980e-05 | 1.49 |
| inv_8 | 2.5359e-04 | 2.0399e-04 | 4.960e-05 | 1.24 |
| inv_12 | 3.5539e-04 | 3.0598e-04 | 4.941e-05 | 1.16 |
| inv_16 | 4.5718e-04 | 4.0797e-04 | 4.920e-05 | 1.12 |
| inv_20 | 5.5895e-04 | 5.0997e-04 | 4.899e-05 | 1.10 |

**差が駆動 1x〜20x の全域で 4.90〜5.00e-05 のほぼ一定**（比は 2.96→1.10 と大きく変動）＝ orig は全セルに一律定数を加算している。charao の測定側にゲイン誤差は無い。

#### なぜ sim で取得できないのか（設定値にせざるを得ない理由）

1. **VNW/VPW は既に計上済みだが寄与ゼロ** — `charao_run.py` は `p_supply = i_vdd·V + i_vnw·V` / `p_absorb = i_vss·V + i_vpw·V` と well 電流を計算に入れているが、実測 `i_vnw` は **1e-20 レベルの数値ノイズ**（inv_1: -2.7e-20 / inv_4: +1.3e-20 / inv_20: 0.0）。抽出済み SPICE では **well 接合が実質モデル化されていない**
2. **fill セルは空 subckt** — `.SUBCKT ..._fill_1 VDD VNW VPW VSS` / `.ENDS` で **Tr ゼロ**。どの端子を測っても電流 0 だが、orig は 5e-05 を持つ＝netlist に情報が存在しない
3. **面積依存ですらない** — `fill_1`（area 2.1952）と `fill_64`（area 140.4928＝**64 倍**）で orig 値は 5e-05 → 5.0005e-05 と**ほぼ不変**。面積比例の物理リークではなく規約定数

→ **測定端子を増やしても（SUB 電位を測っても）取得できない。設定値として加算するのが正しい対応。**

#### 実装：加算箇所は 2 つ（役割が異なる）

| 対象 | 実装箇所 | 動作 |
|------|---------|------|
| **measure ありセル** | `charao_run.py: runSpiceLeakageSingle` | `h.pleak = rslt["pleak"] + leakage_offset × leakage_power_mag` |
| **measure なしセル**（物理セル＝`expect[]`） | `myLogicCell.py: set_max_pleak` の**初期値** | sim が走らず harness が空 → 初期値 `leakage_offset × leakage_power_mag` がそのまま `pleak_cell` になる |

**注意：`set_max_pleak` の for ループは「複数 leakage entry（when 別）の max を取る」比較のままにすること。**
ここで `+=` にすると **when の数だけ多重加算**になる。加算は上表の 2 箇所のみ。

`myExportLib.py` 側は加算済みの `h.pleak` を出力するだけなので、**export に offset 処理は不要**。この設計により `leakage_power()` の個別 value と `cell_leakage_power` が同一基準となり、両者の逆転が起きない。

#### 効果（gf180 実測、`cell_leakage_power` vs orig default）

| セル | charao | orig default | 差 |
|------|--------|-------------|-----|
| inv_1 | 7.65000e-05 | 7.64950e-05 | +0.01% |
| inv_4 | 1.56000e-04 | 1.55980e-04 | +0.01% |
| inv_8 | 2.62000e-04 | 2.61955e-04 | +0.02% |
| inv_20 | 5.80000e-04 | 5.79900e-04 | +0.02% |
| tieh / tiel | 5.01e-05 / 5.00e-05 | 5.0005e-05 / 4.9926e-05 | +0.19% / +0.15% |
| fill_1 / endcap | 5.00000e-05 | 5.00000e-05 | 0.00% |

残差 0.01〜0.02% は `f2s_ceil`（有効 3 桁への切り上げ）由来＝実質完全一致。

副次効果として、sim のゼロ近傍ノイズ（tiel の `-4.13e-13` など**物理的にありえない負値**）も解消される。

#### 他 PDK へ移植するときの決め方

1. orig Liberty がある場合：**代表セルを数点（小駆動〜大駆動）選び、`orig − charao(計測値)` を計算**する
   - 差がほぼ一定 → その値を `leakage_offset` に設定する（本ケース）
   - 差が面積や駆動力に比例 → offset ではなく計測側の問題。本パラメータで対処してはいけない
2. orig Liberty が無い場合：`0.0`（default）のままにする。物理セルの leakage を明示したい場合のみ設定する
3. **確認方法**：`MEAS_ONLY=leakage` で軽量に全セル回帰し、`cell_leakage_power` を orig と突合する

#### 関連

- 課題：ISS-00165（物理セル 14 の追加＋leakage 嵩上げ）
- 物理セル定義：`std_physical.jsonc`（`logic:"PHYSICAL"` / `template_kgn:[]` ＝ measure ゼロ）
- logic 定義：`charao/script/mylogic_physical.py`（`logic_type:"physical"`）

---

### 3.2 `leakage_stable_time`（ISS-00166、2026-07-25 追加）

**leakage を DC 動作点（`op`）で計測する前段の tran 静定時間（絶対時間）。**

#### 記述例

```jsonc
  ,"leakage_stable_time" : 1
```

#### 何のための値か

- leakage measure は `op`（DC 動作点）で電源電流を取るが、**内部保持ノードの電圧を op へ渡す前に tran で静定させる**必要がある（seq/lat の feedback ノードは高インピーダンスで初期値から緩和するのに時間がかかる）
- この **tran 長**を `tslew_in = leakage_stable_time × time_mag`（＝絶対時間、単位は `time_unit`）で与える。tran 終端の内部ノード電圧を `meas find` で取得し `.nodeset` として op に渡す（§SPEC_measure 4.12 B案）
- **貫通対策ではない**（貫通は `pleak = min` で別途処理＝§SPEC_measure 4.12）。本値は **nodeset に渡す内部ノード電圧の静定（精度）**のためだけに効く

#### 値の決め方

- **単位＝倍率ではなく絶対時間**（`leakage_stable_time × time_unit` 秒）。default `1.0`＝従来 1ns
- 長い方が静定は安全側だが **sim 時間に直結**（tran 長が伸びる）
- **gf180 は 1ns で 10ns/40ns と `cell_leakage_power` 完全同一を実測**（inv/dff/lat）→ sim 短縮のため `1` を採用。内部ノードが 1ns で静定するため延長不要だった
- 静定が足りない（op が metastable/未収束になる）プロセスでのみ増やす

#### 実装

| 箇所 | 内容 |
|------|------|
| `myLibrarySetting.py` | フィールド `leakage_stable_time : float = 1.0`（default＝従来 1ns 互換） |
| `charao_run.py` | `tslew_in = float("{:.5g}".format(leakage_stable_time × time_mag))` |
| `temp_testbench.sp.jp2` | `meas_energy==3` 分岐の tran 長に反映 |

#### 関連

- 課題：ISS-00166（seq/lat/icg leakage の DC op 化）／ISS-00167（settling は貫通と無関係と実証）
- 計測仕様：`docs/SPEC_measure.md` §4.12

---

## 4. パラメータ追加時の手順（新規パラメータ共通）

1. `charao/script/myLibrarySetting.py` に **フィールドを宣言**（型 + default）。default は **「書かなければ従来動作」**にする
2. `sample_target/<pdk>/.../config_lib.jsonc` に値を記述（**表示単位**で書く）
3. 内部で使うときは **`× <unit>_mag` で生値へ換算**する（§2）
4. 本仕様書 §3 に**単位・default・適用範囲・実装箇所**を追記する
5. 他 PDK（OSU035 / TRIP62 等）の `config_lib.jsonc` を**変更しなくても動く**ことを確認する
