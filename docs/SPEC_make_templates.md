# SPEC : `util_make_template4json.py` — 実測から templates を決める

`config_lib.jsonc` の `templates` を **実測から決める**ツール。orig `.lib` が無い PDK でも使える。

経緯・検討過程は ISS-00189 / ISS-00190 を参照。本書は**確定仕様のみ**を記す。

---

## 1. 前提となる template の構造

SKY130 orig を実測解析して得た構造（ISS-00189）。

### 1.1 セル依存なのは `index_2` の max だけ

| 軸 | min | max |
|---|---|---|
| `index_1`（入力 slew） | ライブラリ共通の定数 | **`max_transition`**（設計値） |
| `index_2`（出力 load） | ライブラリ共通の定数 | **`max_capacitance`**＝ transition が `max_transition` になる負荷。**セル・出力ピンごと** |

### 1.2 両軸とも等比級数

`n` 点なら公比 = `(max/min)^(1/(n-1))`。SKY130 orig の 1,261 arc すべてでズレ 0.000%。
**min / max / 点数が決まれば軸全体が一意に決まる。**

### 1.3 他の kind は `delay` から派生する

| kind | 導出 | 種類数 |
|---|---|---|
| `delay` | **基準**（`index_1` 共通 ＋ `index_2` セル別） | セル別 |
| `power_tout` | `delay` と**完全同一**。ただし **kind を分けないと measure が走らない**ので別エントリで出す | delay と同数 |
| `power_tin` | `index_1` のみ、`index_2` 空 | 1 |
| `passive` | `index_1` のみ、`index_2` 空 | 1 |
| `const` | `index_1` × `index_1`（両軸とも slew） | 1 |
| `mpw` | `index_1` の `[0]`, `[中央]`, `[max]` | 1 |
| `leakage` | index なし | 1 |

> `const`（setup/hold）は **load 軸を使わない**ため、`max_cap` の探索には無関係。

### 1.4 template は出力端子ごとに割り当てる

`max_cap` は**出力ピンごと**に決まるため、多出力セル（`fa` / `ha` 等）では
`SUM` と `COUT` で別の値になりうる。

- `3.scan` は **(セル, 出力ピン) ごとに別 template**（通し番号 `d000`〜）を作り、
  `4.analyze` が個別に `index_2` を収束させる
- `5.build` は収束値をグループ化し、**同一セル内で出力ピンが別グループになった場合だけ**
  `template_kgn` に第 4 要素（`o0` / `o1`）を付ける。同じグループなら 1 エントリにまとめる

```jsonc
// 2 出力が別グループ（fa_2）
["delay","7x7","d0p303","o0"], ["delay","7x7","d0p32","o1"],
["power_tout","7x7","d0p303","o0"], ["power_tout","7x7","d0p32","o1"]

// 2 出力が同じグループ（fa_1）／単出力（inv_1）
["delay","7x7","d0p154"], ["power_tout","7x7","d0p154"]
```

gf180 の ISS-00150（出力 port 別 template）と同じ構造。

---

## 2. 5 stage の流れ

```
1.probe  ──┐
           ├─→ charao sim ─→ 2.report      … index_1[min/max] と index_2[min] を決める
（条件変更）┘                                  （2 フロー繰り返す）
                    ↓
3.scan  ─→ charao sim ─→ 4.analyze ─┐        … 全セルの max_cap を収束させる
                    ↑                │
                    └────────────────┘        （3.scan は初期化専用。ループに入らない）
                    ↓
5.build                                        … 7x7 などフル template を作る
```

| stage | 出力先 | 役割 |
|---|---|---|
| `1.probe` / `2.report` | `tmp_1.probe_target/<fab>/<vendor>/<rev>` | `in_cap` と transition を実測 |
| `3.scan` / `4.analyze` | `tmp_3.scan_target/<fab>/<vendor>/<rev>` | `max_cap` を反復で収束 |
| `5.build` | `tmp_5.build_target/<fab>/<vendor>/<rev>` | 最終 template |

**`--jsonc_in` は書き換えない。**更新は `--jsonc_out` に出し、それが次 stage の入力になる。

---

## 3. 各 stage の引数

`--stage` は `1.probe` / `2.report` / `3.scan` / `4.analyze` / `5.build`（`1` や `probe` の省略形も可）。

**数値引数の単位は `config_lib.jsonc` の `time_unit` / `capacitance_unit` に従う**（引数は数値のみ）。

| stage | 必須 | 任意 |
|---|---|---|
| **1.probe** | `--jsonc_in` `--jsonc_out` | `--cell`（フル名、既定 `inv_1`）<br>`--slew_in`（既定 0.001、カンマ区切りリスト可）<br>`--load_out`（既定 0.001、リスト可） |
| **2.report** | `--lib` | `--cell` `--jsonc_out`（ログ追記先） |
| **3.scan** | `--jsonc_in` `--jsonc_out` | `--slew_in`（＝ `max_transition`。1 点でよい）<br>`--load_out`（初期 load）<br>`--load_out_rate`（**既定 2.0**）<br>`--load_limit` |
| **4.analyze** | `--lib` `--jsonc_out` | `--iter`（既定 1）<br>`--load_out_rate`（**既定 1.5**）<br>`--load_limit` |
| **5.build** | `--lib` `--jsonc_in` `--jsonc_out`<br>`--slew_min_max_num` `--load_min_max_num` | `--tolerance`（既定 0.05） |

`--slew_min_max_num` / `--load_min_max_num` は `min,max,num` のカンマ区切り（例 `0.01,1.5,7`）。
`--load_min_max_num` の `max` は使わず、各グループの `max_cap` を上限にする。

### ログ

`--jsonc_out` と同じフォルダに置く。

| stage | ファイル |
|---|---|
| `1.probe` / `2.report` | `2.report.log`（`1.probe` が上書き開始、`2.report` が追記） |
| `3.scan` | `3.scan.log` |
| `4.analyze` | **`4.analyze_<iter>.log`**（反復ごとに分割） |
| `5.build` | `5.build.log` |

`[cmd]` 行に実行コマンド全体（`sys.argv` から再構成）と結果を記録する。日時等の変動要素は入れないため**同じ入力なら同じログになる**。

---

## 4. 決め方

### 4.1 `index_1[min]` — 1 フロー目

```
--slew_in 0.001 --load_out 0.001      # 最速入力・無負荷
```

得られた `out_transition` が「そのライブラリで実現できる最速の出力遷移」。これを切りのいい値へ丸める。

> **無負荷 transition はドライブ能力にほとんど依存しない。**
> SKY130 で `inv_1` 0.0078ns 〜 `inv_16` 0.0066ns ＝ 16 倍のドライブ差に対し 1.2 倍しか変わらない。
> 無負荷ではセル自身の出力容量だけを駆動するため、駆動力と自己負荷が同じ比率で増減するから。
> よって**基準セル選びに神経質になる必要はない**。

### 4.2 `index_2[min]` — `in_cap` の 1/4 を目安

1 フロー目（**無負荷条件**）で測った `in_cap` を使う。

> `index_2[min]` は「ゲートを 1 個も駆動しない＝実質配線だけ」の下限。
> SKY130 orig の `0.0005pF` は対象 181 セルの最小 Cin `0.001349pF`（`or4_2` の `D`）の 0.37 倍。
> ライブラリ全体の最小 `0.000878pF` は `diode_2`（アンテナダイオード）で入力が pn 接合 1 個だけの
> 非論理セルのため基準にしない。次点も反転入力ピンでインバータ 1 段しか駆動しない。
> こうした特殊セルを避けつつ余裕を持たせる目安として **1/4**。

> **`in_cap` は測定条件で変わる**：`myLogicCell.set_cin_avg()` が delay measure の
> 全格子点で測った `c_in` の平均を採るため。出力負荷が重いとミラー結合で入力側に見える電荷が増える。
> SKY130 実測で無負荷 0.00215pF に対し fanout 70〜100 の 4 点平均 0.00223pF。
> **`index_2[min]` の算出には無負荷条件の値を使う。**

### 4.3 `index_1[max]` — 2 フロー目

```
--slew_in <index_1[min]> --load_out <in_cap x N のリスト>
```

`N` を振って transition を測り、目標値に近い点を探す。transition は load にほぼ線形なので数点で足りる。

> orig がある PDK では **orig の `max_transition` をそのまま採る**のが確実
> （SKY130 は 1.5ns。`default_max_transition` として宣言されている）。

> **「基準セルに fanout N を繋いだ transition」で決める方式は基準セル依存が強い**。
> transition = 1.5ns になる fanout は SKY130 で `inv_16` 51 〜 `clkinv_1` 88（rise）と 3 倍ばらつく。

### 4.4 `max_cap` — 3.scan / 4.analyze の反復

```
3.scan   : index_1 = [slew_in]（＝ max_transition。1 点でよい）
           index_2 = [load, load x load_out_rate]（初期値、全セル共通）
           セル・出力ピンごとに別 template（通し番号）を割り当てる
   ↓
charao sim
   ↓
4.analyze: index_2[0] の transition で収束判定、index_2[0,1] の 2 点で補間して
           次の load を算出し、各 template の index_2 を [a, a x rate] に更新
   ↓
（収束するまで sim ←→ 4.analyze を繰り返す。3.scan は再実行しない）
```

**判定は `index_2[0]`、補正は `index_2[0,1]` の 2 点補間**。
`index_2 = [a, a x rate]` なので末尾は目標より rate 倍ぶん大きく出る。末尾で判定すると
収束しているのに未達と誤判定する。

`--load_out_rate` は **3.scan=2.0 / 4.analyze=1.5** が既定。2 点の間隔が広いほうが傾きの推定が安定し
収束が速い（SKY130 で 2 巡目時点 rate 1.1 が 66%、1.5 が 84%）。

---

## 5. ⚠️ sim 実行時の注意

### 5.1 `--measures_only` に FF の measure 名を含めること

**FF / SDFF の delay は `measure_type` が `delay` ではない。**

| logic | delay に相当する `meas_types` |
|---|---|
| comb | `delay` |
| latch / ICG | `delay` |
| **FF / SDFF** | **`rising_edge` / `falling_edge`** |

`--measures_only delay` だけで流すと **FF が丸ごと抜ける**。
`[INFO]: no harness result exist for target=o0.` とだけ出て静かに落ちるため気づきにくい。

```
--measures_only delay rising_edge falling_edge
```

SKY130 で対象 arc が 154 → **173** になった（FF 19 セルぶん）。

### 5.2 `--SOURCE` にモデルファイルの置き場を含めること

`--jsonc_out` を元の target ツリーの外に置くと、`config_lib.jsonc` の `model_path`
（例 `./sample_target/sky130`）が指すモデルが転送対象から漏れる。

```
--SOURCE sample_src sample_target tmp_3.scan_target charao
```

---

## 6. SKY130 での実績（2026-08-02）

| stage | 結果 |
|---|---|
| 1 フロー目 | `in_cap` 0.00215pF / `out_transition` 0.0162ns → `index_1[min] = 0.01` |
| 2 フロー目 | fanout 70/80/90/100 → 1.40/1.60/1.81/2.00ns（傾き 9.23ns/pF）→ `index_1[max] = 1.5` |
| `index_2[min]` | `in_cap`/4 ＝ 0.000538 → **0.0005** |
| 3.scan / 4.analyze | **3 巡で 173/173 収束**（47 → 149 → 173）。ズレ中央 0.0% / 最大 1.3% |
| `max_cap` | **0.0371〜3.78pF（102 倍）**。最小 `nor4_1`、最大 `clkinv_16` |
| 5.build | **24 グループ**（許容 5%）。上位 3 種で 62%。セル 181 / 参照 750 / 未定義参照 0 |

---

## 7. 実行例（SKY130）

```bash
# ── 1 フロー目 : index_1[min] と index_2[min] の判断材料 ──────────────
python -m charao.script.util_make_template4json --stage 1.probe \
    --jsonc_in sample_target/sky130/fd/sc_hd \
    --jsonc_out tmp_1.probe_target/sky130/fd/sc_hd \
    --cell sky130_fd_sc_hd__inv_1 --slew_in 0.001 --load_out 0.001

python -u -m lrPymRPC --SERVER_IP 192.168.168.103 \
  --REPO_URL jsoncomment=jsoncomment,pydantic=pydantic,numpy=numpy,jinja2=jinja2 \
  --SOURCE sample_src sample_target tmp_1.probe_target charao \
  --SOURCE_INCLUDE .spice .spi .ngspice .sp .jsonc .py .jp2 std_primitives.v \
  --SOURCE_MATCH sky130 charao --RUN_NAME run_1.probe_target --RESULT rslt \
  --CMD "python3 -m charao.script.charao -f sky130 -v fd -r sc_hd -g std -u 1P80 \
         -p TT -t 25.0 --vdd 1.8 --target tmp_1.probe_target \
         --cells_only sky130_fd_sc_hd__inv_1"

python -m charao.script.util_make_template4json --stage 2.report \
    --lib run_1.probe_target/rslt/<lib> --cell sky130_fd_sc_hd__inv_1 \
    --jsonc_out tmp_1.probe_target/sky130/fd/sc_hd

# ── 2 フロー目 : index_1[max] の判断材料（fanout を振る）──────────────
#    --slew_in <index_1[min]>  --load_out <in_cap x N のリスト>
python -m charao.script.util_make_template4json --stage 1.probe \
    --jsonc_in sample_target/sky130/fd/sc_hd \
    --jsonc_out tmp_1.probe_target/sky130/fd/sc_hd \
    --cell sky130_fd_sc_hd__inv_1 --slew_in 0.01 \
    --load_out 0.1505,0.172,0.1935,0.215
#    → sim → 2.report（同上）

# ── 3.scan : 全セルの max_cap 測定用 ─────────────────────────────────
python -m charao.script.util_make_template4json --stage 3.scan \
    --jsonc_in sample_target/sky130/fd/sc_hd \
    --jsonc_out tmp_3.scan_target/sky130/fd/sc_hd \
    --slew_in 1.5 --load_out 0.16 --load_limit 5.0

# ── sim ←→ 4.analyze を収束するまで繰り返す（3.scan は再実行しない）──
python -u -m lrPymRPC ... --RUN_NAME run_3.scan_target --RESULT rslt \
  --CMD "python3 -m charao.script.charao ... --target tmp_3.scan_target \
         --measures_only delay rising_edge falling_edge"

python -m charao.script.util_make_template4json --stage 4.analyze \
    --lib run_3.scan_target/rslt/<lib> \
    --jsonc_out tmp_3.scan_target/sky130/fd/sc_hd --iter 1 --load_limit 5.0
#    → 「target +-5% に入っている arc」が全数になるまで sim と交互に繰り返す

# ── 5.build : 最終 template ──────────────────────────────────────────
python -m charao.script.util_make_template4json --stage 5.build \
    --lib run_3.scan_target/rslt/<lib> \
    --jsonc_in sample_target/sky130/fd/sc_hd \
    --jsonc_out tmp_5.build_target/sky130/fd/sc_hd \
    --slew_min_max_num 0.01,1.5,7 --load_min_max_num 0.0005,5.0,7 --tolerance 0.05
```

> `--jsonc_in` は常に**元の target**（書き換えない）。`--jsonc_out` が成果物。
> `RUN_NAME` は stage 名に揃える（`run_3.scan_target` 等）と `--lib` のパスが追いやすい。
> **中間の target ツリーは `tmp_` を前置**して（`tmp_1.probe_target` / `tmp_3.scan_target` /
> `tmp_5.build_target`）まとめて管理する。`.gitignore` の `tmp_*` で除外される（2026-08-04）。

---

## 8. 運用手順（SKY130 以降の新規 PDK、2026-08-04 確定）

**`sample_target` を正とし、template を更新するときだけ `tmp_5.build_target` を経由する。**

```
① sample_target の jsonc を編集      … セル追加・sim パラメータ変更など
        ↓
② template 更新が要るか？
   要らない  → そのまま charao を回す（sample_target が正）
   要る      → ③へ
        ↓
③ 3.scan → sim → 4.analyze（収束するまで反復）→ 5.build
        ↓                                  ← いずれも --jsonc_in は最新の sample_target を起点にする
④ cp tmp_5.build_target/<fab>/<vendor>/<rev>/*.jsonc sample_target/<fab>/<vendor>/<rev>/
        ↓
⑤ git diff sample_target/... で確認 → コミット
```

### ④ が単純コピーでよい理由

`_copy_jsonc()` が `--jsonc_in` の一式を `--jsonc_out` へ複製してから template だけ書き換えるため、
**両者の差は必ず次の 2 か所に限られる**（SKY130 で実測確認済み、2026-08-04）。

| ファイル | 差分の範囲 |
|---|---|
| `config_lib.jsonc` | **`templates` セクションの中だけ**。sim パラメータ・`model_path` 等は完全一致 |
| `std_*.jsonc` | **`template_kgn` の行だけ**。`ports_dict` 等は完全一致 |
| `std_primitives.v` | 完全一致（コピーのみ） |

`*.jsonc` に絞れば `5.build.log` はコピー対象から自然に外れる。
`config_lib.jsonc` の `templates` と `std_*.jsonc` の `template_kgn` は**必ず揃って移すこと**
（片方だけだと `[Error] unique template =delay/7x7/dXXX is not exist` で落ちる）。
丸ごとコピーする限りこの事故は起きない。

### ⚠️ 順序を守ること

**`3.scan` を回した後に `sample_target` を編集すると、その編集は `tmp_5.build_target` に入らない。**
その状態で ④ を実行すると**後から入れた編集が巻き戻る**。
必ず「① sample_target を編集 → ③ template 生成 → ④ 反映」の順で行う。

### gf180 は対象外

gf180 の `config_lib.jsonc`（10x10 / 46 グループ）は **削除済みの旧ツール** `util_make_templates_from_origin.py`（2026-08-06 に削除）の出力で、
**a33 全リグレッション（229 セル・635,806 点）の比較基準**になっている。
template を変えると過去の数値と直接突合できなくなるため据え置く（ISS-00191 (4) ＝案 A、ISS-00192）。
本手順は **SKY130 以降の新規 PDK に適用**する。

---

## 9. 関連

- **ISS-00189** — 本ツールの設計・検討経緯、template 構造の解析結果
- **ISS-00190** — `index_2`（テーブル軸）と `max_capacitance`（制約属性）の分離（検討事案）
- `docs/SPEC_config_lib.md` §3.3 — index の有効桁（3 桁）
- **旧方式の 3 本は 2026-08-06 に削除した**（ISS-00192）。`util_make_templates_from_origin.py`（orig `.lib` から生成）/ `util_make_templates_from_new.py`（`Cin x fanout` から生成）/ `util_assign_templates.py`（`template_kgn` の再割り当て）。本ツールが実測ベースで上位互換のため。履歴は tag `2.0.0.a04` 以前を参照。
