# SPEC : セル定義 jsonc（`std_comb.jsonc` / `std_seq.jsonc` / `std_physical.jsonc` / `io_*.jsonc`）

target ディレクトリに置く「どのセルを、どの logic として、どのテンプレートで特性化するか」を
定義するファイルの仕様。`config_lib.jsonc`（ライブラリ共通の設定）は `SPEC_config_lib.md` を参照。

---

## 1. 配置とファイル名

```
<ARGS.target>/<ARGS.fab_process>/<ARGS.cell_vendor>/<ARGS.cell_revision>/
    config_lib.jsonc        必須
    std_comb.jsonc          cell_group=std のとき読まれる
    std_seq.jsonc                  〃
    std_physical.jsonc             〃
    std_primitives.v        UDP 定義（SPEC_primitives.md）
    io_*.jsonc              cell_group=io のとき読まれる
```

charao は **`<cell_group>` で始まり `.jsonc` で終わるファイルをすべて読む**（`charao.py` の
jsonc 探索）。ファイル名の後半は自由なので、`std_comb` / `std_seq` のような分割は運用上の都合。

---

## 2. ファイル構造

```jsonc
{
"spice_path":"./sample_src/<pdk>/.../spice",

"cell_info": [
  {"template_kgn":[["leakage","0x0","d000"],["delay","7x7","d000"],
                   ["power_tout","7x7","d000"],["power_tin","7x0","d000"]],
    "spice":"<netlist ファイル名>", "cell":"<subckt 名>","logic":"<logic 名>","area":<面積>,
    "ports_dict":{ ... }},
  ...
]
}
```

| キー | 内容 |
|---|---|
| `spice_path` | セル netlist が置かれたディレクトリ。**リポジトリルートからの相対**。charao が絶対パス化する |
| `spice` | netlist のファイル名。PDK によって「全セル 1 ファイル」（gf180 / SKY130 / IHP）と「セル 1 個 1 ファイル」（OSU035）がある |
| `cell` | SPICE の `.subckt` 名。**生成される .lib / .v のセル名になる** |
| `logic` | `mylogic_*.py` が定義する logic 名（`INV` / `NAND2` / `DFF_PC_NR` 等） |
| `area` | Liberty の `area`。orig `.lib` があればその値を使う |
| `template_kgn` | 使用するテンプレートの指定（§4） |
| `ports_dict` | SPICE ポートと logic ポートの対応（§3） |

---

## 3. `ports_dict` — 最重要

### 3.1 書き方

```jsonc
"ports_dict":{"A":"i0","B":"i1","VGND":"VGND","VNB":"VNB","VPB":"VPB","VPWR":"VPWR","Y":"o0"}
```

| | 内容 |
|---|---|
| **キー** | **SPICE subckt の実ポート名** |
| **値（信号ピン）** | **logic ポート名**（`o0` / `o1` / `i0`〜 / `c0` / `r0` / `s0`） |
| **値（電源ピン）** | **実ポート名をそのまま書く**（`"VGND":"VGND"` のように同じ文字列） |

### 3.2 ⚠️ 順序は SPICE subckt のピン順と完全一致させること

`myLogicCell.chk_ports()` が **`ports_dict.items()` の挿入順で SPICE の port 順を厳密照合**する
（Python 3.7+ の dict 挿入順保持と jsoncomment の順序保持に依存）。順序が違うとエラーで停止する。

```
.subckt sky130_fd_sc_hd__inv_1 A VGND VNB VPB VPWR Y
                               ↓  ↓    ↓   ↓   ↓    ↓
"ports_dict":{"A":"i0","VGND":"VGND","VNB":"VNB","VPB":"VPB","VPWR":"VPWR","Y":"o0"}
```

**PDK によってピン順の流儀が違う**ので、必ず実 netlist を見て書くこと。

| PDK | ピン順の例 |
|---|---|
| gf180 | `I Z VDD VNW VPW VSS`（出力が 2 番目） |
| OSU035 | `A B Y VDD VSS VNW VPW`（信号が先、電源が後） |
| **SKY130** | `A VGND VNB VPB VPWR Y`（**電源が中間、出力が末尾**） |
| IHP SG13G2 | `X A B VDD VSS`（**出力が先頭**、well 端子なし） |

### 3.3 ⚠️ 電源ピンの値に logic 名を書いてはいけない

**信号ピンは logic 名（`i0` 等）、電源ピンは実ポート名**という非対称なルールになっている。

```jsonc
// 正
"VPWR":"VPWR"   "VGND":"VGND"   "VPB":"VPB"   "VNB":"VNB"
// 誤（sim が [Error] not used port name=vss in XDUT で停止する）
"VPWR":"vdd"    "VGND":"vss"    "VPB":"vnw"   "VNB":"vpw"
```

**理由**：charao は testbench の instance 行を組むとき、ポート名を
**`config_lib.jsonc` の `vdd_name` / `vss_name` / `nwell_name` / `pwell_name` と直接比較**する。

```python
# myConditionsAndResults.py
if(w1.upper() == self.mls.vss_name.upper()):   # config の "VGND" と比較される
    tmp_line += ' VSS'
```

一方 `ports_dict` は `replace_by_portmap()` で **「値 → キー」に逆置換**されて実ポート名に戻る。
値に `vss` と書くと、逆置換の結果が config の `vss_name`（例 `VGND`）と一致せず、
「使われないポート」として弾かれる。

> **gf180 / OSU035 では露見しない**。これらは `vdd_name="VDD"` で値も `vdd` → 逆置換して `VDD`
> となり偶然一致するため。**SKY130（`VPWR`）で初めて顕在化した**（2026-07-31、ISS-00181）。

**規約（2026-08-01 明文化、ISS-00187）**：

> **電源ピンの値は、大文字化すると `config_lib.jsonc` の
> `vdd_name` / `vss_name` / `nwell_name` / `pwell_name` に一致すること。**

実ポート名をそのまま書けば自動的に満たされる（`"VPWR":"VPWR"`）。
値の大小文字は問わない（`"VPWR":"vpwr"` でもよい）が、**実ポート名そのまま**が読みやすい。

**この規約を破ると 2 段階で壊れる**（どちらも 2026-07-31〜08-01 に実際に起きた）。

| 破り方 | 症状 |
|--------|------|
| 値に logic 名（`"VPWR":"vdd"`）| sim が `[Error] not used port name=vdd in XDUT` で停止（上記） |
| 値が実名だが charao 側が大小文字を区別 | 生成 `.v` で**電源ポートが宣言されず** iverilog が通らない（ISS-00187 で `rvs_portmap` を大小文字非依存にして解消） |

**vcode 内の電源リテラル**：`mylogic_*.py` の vcode は UDP へ `..., vdd, vss);` と
charao の論理名で書く。これは `ports_dict` の値ではないため、`replace_by_portmap()` が
**`config_lib.jsonc` の `*_name` を使って実ポート名へ解決する**（ISS-00187）。
jsonc 側で意識する必要はないが、`vdd` / `vss` / `vnw` / `vpw` は
**vcode 内で予約語扱い**になる点に注意（語境界一致で置換される）。

### 3.4 logic ポート名の割り当て

| logic ポート | 意味 |
|---|---|
| `o0` / `o1` | 出力（`o1` は Q_N のような第 2 出力） |
| `i0` / `i1` / `i2` … | 入力。**`mylogic` の `functions` / `expect` が参照する順番に合わせる** |
| `c0` | クロック（FF）／ enable（LATCH） |
| `r0` | reset（active-Low の `RN` / `RESET_B` もここ。極性は vcode 側で吸収） |
| `s0` | set（同上） |

対応表の詳細は **`30_projects/SPEC_mylogic.md`**（my_escort 側）の family 別 `ports_dict` 早見表を参照。

---

## 4. `template_kgn`

`config_lib.jsonc` の `templates` で定義したテンプレートを、セルごとに選ぶ。

```jsonc
"template_kgn":[["leakage","0x0","d000"],["delay","7x7","d000"],
                ["power_tout","7x7","d000"],["power_tin","7x0","d000"]]
```

各要素は **`[kind, grid, name]`** の 3 要素（出力ピン別に分ける場合は第 4 要素を付ける＝ISS-00150）。
`config_lib.jsonc` 側に同じ `kind` / `grid` / `name` の定義が無いとエラーになる。

### 有効な `kind`

`myItem.py` の `Literal` で定義されている。**ここに無い名前を書くと Pydantic 検証で落ちる**。

| kind | grid の例 | 用途 |
|---|---|---|
| `leakage` | `0x0` | リーク電力（index なし） |
| `delay` | `7x7` / `10x10` | 伝搬遅延・出力遷移（slew × load） |
| `delay_disable` | `10x0` | 三相態の disable アーク（load 非依存） |
| `const` | `7x7` | setup / hold / recovery / removal。**両軸とも slew** |
| `mpw` | `3x0` | min_pulse_width（slew のみ、ISS-00160） |
| `passive` | `7x0` | 入力ピン容量など |
| **`power_tout`** | `7x7` | 出力ピンの internal_power |
| **`power_tin`** | `7x0` | 入力ピンの internal_power（load 非依存） |

> **`"power"` は無効**。旧スキーマの名残で、現在は `power_tout` / `power_tin` に分かれている
> （2026-07-30、OSU035 の jsonc がこれで落ちた）。

### セル種別ごとの典型

| セル種別 | `template_kgn` |
|---|---|
| 組合せ | `leakage` / `delay` / `power_tout` / `power_tin` |
| 順序 | 上記 ＋ `const` / `passive` / `mpw` |
| 三相態 | 上記 ＋ `delay_disable` |
| 物理（fill 等） | `leakage` のみ |

---

## 5. 新 PDK でセル jsonc を書く手順

1. **`.subckt` 行を全部拾う**（ピン順が命）

   ```bash
   grep -iE "^\.subckt" <netlist> | head -20
   ```

2. **電源ピンの役割を実接続で確認**する。名前から推測しない

   ```bash
   awk '/^\.subckt <cell> /,/^\.ends/' <netlist>
   # 例（SKY130 inv_1）: nMOS の bulk = VNB / pMOS の bulk = VPB
   ```

   確認した名前を `config_lib.jsonc` の `vdd_name` / `vss_name` / `nwell_name` / `pwell_name` に書く。

3. **セル機能を charao の logic へ対応づける**。既存 logic に無い機能は `mylogic_*.py` の追加が要る

4. **`ports_dict` を subckt のピン順どおりに書く**（§3）。電源は値も実ポート名

5. **`area` は orig `.lib` から拾う**（無ければ 1.0 で始めてよい）

6. **1 セルで露払い**してから全セルへ広げる

   ```bash
   FAB=<pdk> VENDOR=<v> REV=<r> UV=<uv> VDD=<v> MATCH=<pdk> CELL_PREFIX=<prefix> \
   INDEX1="0 6" INDEX2="0 6" CELLS="<1 セル>" MODE=local RESULT_ITEMS="rslt" \
   RUN_NAME=run_smoke bash debug_run.sh run_all
   ```

---

## 6. よくあるエラーと原因

| エラー | 原因 |
|---|---|
| `[Error] not used port name=<x> in XDUT` | **電源ピンの値に logic 名を書いた**（§3.3）／ `config_lib.jsonc` の `*_name` と綴りが違う |
| `chk_ports` 系のエラー | **`ports_dict` の順序が subckt のピン順と違う**（§3.2） |
| Pydantic 検証エラー（`kind`） | `template_kgn` に無効な kind を書いた（§4。`power` は無効） |
| `netlist is not exits` | `spice_path` が違う／リモート実行で **拡張子が `--SOURCE_INCLUDE` に無く転送されていない**（`.spi` 等） |
| テンプレート未定義 | `template_kgn` の `[kind, grid, name]` が `config_lib.jsonc` の `templates` に無い |

---

## 7. 関連

- `docs/SPEC_config_lib.md` — `config_lib.jsonc` のパラメータ仕様
- `docs/SPEC_primitives.md` — `std_primitives.v` の仕様と UDP 契約
- `docs/SPEC_pin_oirc.md` — `pin_oirc` / `pin_tr` の意味
- `30_projects/SPEC_mylogic.md`（my_escort）— logic ポート命名規約と family 別 `ports_dict` 早見表
- ISS-00181 — SKY130 対応（本仕様書の記述はここでの実作業に基づく）
