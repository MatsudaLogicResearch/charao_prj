# HOWTO: KLayout-PEX（kpex）で寄生抽出する

charao が使う標準セルの SPICE ネットリストは **プリレイアウト（寄生 R/C を含まない）** である。
実レイアウトの配線寄生を織り込んだネットリストを得るために **KLayout-PEX（kpex）** を使う。

- 起票元：ISS-00201（駆動サイズが大きいほど charao の transition/delay が orig より速く出る系統差）
- 検証チケット：ISS-00202
- 初回実施：2026-08-07（`sky130_fd_sc_hd__inv_16`）

---

## 1. なぜ kpex か

寄生抽出の定番は magic（`extract all` → `ext2spice cthresh 0 rthresh 0`）だが、
**ダーマツ環境では magic が使えない**。

| 手段 | 可否 | 理由 |
|---|---|---|
| PDK 同梱の抽出済みネットリスト | **無い** | `libs.ref/sky130_fd_sc_hd/` の 9 views（cdl/gds/lef/lib/mag/maglef/spice/techlef/verilog）に `pex`/`rcx` は無い。`cdl` も回路図レベル（`inv_16` が M 2 個のみ） |
| ローカル magic | 未インストール（GUI 必須） | `apt` 候補はあるが GUI でしか起動しない |
| lrPymRPC 経由の magic | **不可** | 許可コマンド一覧に `magic` はあるが実体が無い。`magic -nowrapper -dnull -noconsole` でも `Cannot start application: No such file or directory` |
| **kpex（2.5D エンジン）** | **可** | pip で入る／完全バッチ／magic 不要／R と C の両方 |

---

## 2. kpex の概要

KLayout に統合された寄生抽出ツール（IIC-JKU / Johannes Kepler University ＋ Silicon Austria Labs）。

- PyPI：`klayout-pex`（実施時 0.3.12、依存で klayout 0.30.10 が入る）
- **Python モジュール名は `klayout_pex`**（CLI 名の `kpex` ではモジュール実行できない）
- 対応 PDK：**sky130A** / gf180mcuD / ihp-sg13g2
- 完全ヘッドレス。GUI・X ディスプレイ不要

### エンジンは 3 種

| エンジン | 容量 C | 抵抗 R | 外部実行体 | 備考 |
|---|---|---|---|---|
| **`--2.5D`** | ✓ | ✓ | 不要 | magic の考え方を KLayout 上に解析式で実装。**charao では これを使う** |
| `--fastercap` | ✓ | ✗ | FasterCap | 3D 場の解法。R が出ない |
| `--magic` | ✓ | ✓ | magic | magic のラッパ。環境上使えない |

### 処理の流れ

```
GDS ──[KLayout LVS]──> LVSDB ──[2.5D 解析エンジン]──> 寄生付き SPICE
                                                  └──> 容量/抵抗テーブル CSV
```

LVS を内部で走らせてネット名とデバイスを確定させてから、寄生を載せる。
`--schematic` を渡さない場合は **dummy schematic が自動生成**される（LVS 比較はせず抽出のみ）。

---

## 3. 実行コマンド（実施したもの）

lrPymRPC 経由でリモート（192.168.168.103）実行する。

```bash
python -m lrPymRPC --SERVER_IP 192.168.168.103 \
  --REPO_URL klayout-pex=klayout-pex \
  --SOURCE sample_src --SOURCE_INCLUDE .gds --SOURCE_MATCH sky130_fd_sc_hd \
  --RUN_NAME run_kpex_inv16 --RESULT kpex_out \
  --CMD "python3 -m klayout_pex --pdk sky130A --gds sample_src/sky130A/libs.ref/sky130_fd_sc_hd/gds/sky130_fd_sc_hd.gds --cell sky130_fd_sc_hd__inv_16 --2.5D --mode RC --out_dir kpex_out --out_spice kpex_out/inv_16_pex.spice"
```

### lrPymRPC 側の引数

| 引数 | 値 | 意味 |
|---|---|---|
| `--REPO_URL` | `klayout-pex=klayout-pex` | リモートに pip install するパッケージ。`<名前>=<pip 指定>` の形式 |
| `--SOURCE` | `sample_src` | 転送するディレクトリ |
| `--SOURCE_INCLUDE` | `.gds` | 転送対象の拡張子（**後方一致**） |
| `--SOURCE_MATCH` | `sky130_fd_sc_hd` | パスに含まれる語で絞る。これが無いと sample_src 全体（他 PDK 込み）を送ってしまう |
| `--RUN_NAME` | `run_kpex_inv16` | 結果の格納先ディレクトリ |
| `--RESULT` | `kpex_out` | 回収対象。**トップレベル名のみ**（`tmp/xxx` のようなサブパスは迷子になる＝ISS-00197） |
| `--CMD` | 下記 | リモートで実行するコマンド。先頭は許可コマンド（`python3` 等）でなければならない |

### kpex 側の引数

| 引数 | 値 | 意味 |
|---|---|---|
| `--pdk` | `sky130A` | PDK 選択。`{gf180mcuD, ihp-sg13g2, sky130A}` から選ぶ。**レイヤ定義・プロセススタック・寄生係数は kpex 同梱**なので PDK 本体のパス指定は不要 |
| `--gds` / `-g` | ライブラリ GDS | LVS の入力レイアウト。**ライブラリ全体の GDS をそのまま渡してよい**（4.1MB） |
| `--cell` / `-c` | `sky130_fd_sc_hd__inv_16` | 抽出対象セル。省略すると **top cell** になる。**セル単位で抽出したいので必ず指定する** |
| `--2.5D` | （フラグ） | 2.5D 解析エンジンを使う。既定はどのエンジンも走らないので**明示が必須** |
| `--mode` | `RC` | 2.5D の抽出モード。`{CC, RC, R}`。**既定は `CC`（容量のみ）なので R も欲しければ `RC` を指定する** |
| `--out_dir` | `kpex_out` | 実行ディレクトリ。既定 `output` |
| `--out_spice` / `-o` | `kpex_out/inv_16_pex.spice` | SPICE の追加出力先。指定しなくても `--out_dir` 配下には出るが、回収しやすい位置に置くために指定する |

### 指定しなかったが関係する引数

| 引数 | 既定 | 備考 |
|---|---|---|
| `--blackbox` | `False` | `True` にすると MIM/MOM cap 等をブラックボックス化する。**デバイスを抽出したいので既定のまま** |
| `--schematic` / `-s` | なし | LVS 用の回路図ネットリスト。未指定なら dummy が自動生成される |
| `--lvsdb` / `-l` | なし | 既存 LVSDB を渡して LVS をスキップする。**同じセルを条件違いで何度も抽出するときに有効** |
| `--cache-lvs` | `True` | LVSDB をキャッシュして再利用する |
| `--halo` | tech 既定（sky130A は 8µm） | サイドウォール halo 距離。寄生を拾う範囲 |
| `--log_level` | `subprocess` | `all` / `debug` / `verbose` 等 |
| `--threads` | 128 | FasterCap 用 |

`--magic_*` 系（`--magic_cthresh` / `--magic_rthresh` 等）は magic エンジン専用なので 2.5D では無関係。

### 複数セルをまとめて抽出する（`tools/gds2pex.py`）

kpex の `--cell` は 1 つしか取れないため、上のコマンドをセルごとに回すと
**1 セルあたり約 38 秒**かかる。抽出そのものは**セルあたり約 2 秒**で、残りは
pip install と GDS 転送のオーバーヘッドなので、**サーバ側でループを回す**ほうがよい。

```bash
python3 -m lrPymRPC --SERVER_IP 192.168.168.103 \
  --REPO_URL klayout-pex=klayout-pex \
  --SOURCE sample_src tools --SOURCE_INCLUDE .gds .py \
  --SOURCE_MATCH sky130_fd_sc_hd tools \
  --RUN_NAME run_kpex_all --RESULT kpex_out \
  --CMD "python3 tools/gds2pex.py --gds sample_src/sky130A/libs.ref/sky130_fd_sc_hd/gds/sky130_fd_sc_hd.gds --pdk sky130A --prefix sky130_fd_sc_hd__ --out_dir kpex_out --cells inv_1 inv_2 inv_4"
```

- **`--SOURCE` に `tools` を、`--SOURCE_INCLUDE` に `.py` を、`--SOURCE_MATCH` に `tools` を足す**こと
  （足さないとドライバがサーバへ届かない）
- セル数が多いときは `--cells_file`（1 行 1 セル、`#` はコメント）
- `--schematic` に cdl を渡すと **kpex 内蔵の LVS が回路図と比較**する（未指定だと dummy schematic が
  自動生成され、**比較しない**）
- セルごとに `OK`/`NG` と素子数（`M=` / `R=` / `C=`）を出し、最後に集計する。
  **空の netlist を見逃さないため**に素子数を必ず確認する

実測（10 セル）：

```
[OK ]   1/ 10 sky130_fd_sc_hd__inv_2       1.8s  M=4  R=76  C=10
[OK ]   7/ 10 sky130_fd_sc_hd__dfrtp_1     4.2s  M=28 R=219 C=72
[OK ]  10/ 10 sky130_fd_sc_hd__decap_12    1.8s  M=2  R=120 C=3
  total   : 10 cells / 23.0 s      ← lrPymRPC 込みの実時間は 57 秒
```

---

## 4. 出力物

`--out_dir` 配下に `<lib>__<cell>/` が作られる。

| ファイル | 内容 |
|---|---|
| `<cell>_k25d_pex_netlist.spice` | **寄生付き SPICE ネットリスト**（`--out_spice` で指定した先にもコピーされる） |
| `<cell>_k25d_pex_netlist.csv` | 容量・抵抗の一覧（`Device;Net1;Net2;Capacitance [fF];Resistance [Ω]`） |
| `<cell>_extracted.cir` | LVS が抽出した素のネットリスト（寄生なし） |
| `<cell>.lvsdb.gz` | LVSDB（`--lvsdb` で再利用できる） |
| `<cell>_k25d_pex_report.rdb.gz` | KLayout で開けるレポート |
| `<cell>_dummy_schematic.spice` | 自動生成された dummy schematic |
| `kpex.log` / `kpex_plain.log` | ログ（LVS の経過を含む） |

### `inv_16` の実測結果（2026-08-07）

```
inv_16_pex.spice   521 行
素子内訳: {'M': 32, 'R': 437, 'C': 10}
```

```spice
*** Extraction Engine: KPEX/2.5D
*** Technology: sky130a
.SUBCKT sky130_fd_sc_hd__inv_16 VGND A Y VPWR VPB sky130_gnd
M$1 Y A VPWR VPB sky130_fd_pr__pfet_01v8_hvt L=0.15U W=1U AS=0.26P AD=0.135P
+ PS=2.52U PD=1.27U
...
```

CSV の容量（fF）：

```
C1;A;VGND;0.337     C2;A;VPWR;0.399     C3;A;VSUBS;3.098    C4;A;Y;1.693
C5;VGND;VPWR;0.147  C6;VGND;VSUBS;0.943 C7;VGND;Y;1.022     C8;VPWR;VSUBS;0.986
C9;VPWR;Y;1.401     C10;VSUBS;Y;0.311
```

- トランジスタ 32 個は `spice/` 版のフィンガ構成と一致（デバイス抽出は正しい）
- `AS`/`AD`/`PS`/`PD`（拡散の面積・周長）も付く。**`spice/` 版はこれを持たない**ため、
  抽出版のほうが接合容量まで含んだ情報量になる（後述 4.5 の実測差）

---

## 4.5 整形（`tools/pex2spice.py`）

kpex の出力は**そのままでは ngspice / charao に渡せない**（ISS-00203）。
整形は 6 章に挙げた個別の症状に対応するが、**手作業では再現性が無い**ため
`tools/pex2spice.py` に集約した（2026-08-08）。

```bash
python3 tools/pex2spice.py \
  --in  run_kpex_inv16/kpex_out/inv_16_pex.spice \
  --ref sample_src/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice \
  --out sample_src/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd_pex.spice
```

| 処理 | 内容 | 対応する症状（6 章） |
|---|---|---|
| 基板ポート名 | `sky130_gnd` → `VNB`（`--sub_alias` / `--sub_port`） | `VNB` が消える |
| ポート順 | `--ref` の `.subckt` 行から取得して並べ替え。**ポート集合が違えばエラーで停止** | `ports_dict` と順序が合わない |
| デバイス行 | `M` → `X`、`W`/`L`/`AS`/`AD`/`PS`/`PD` を scale 前提の値へ換算 | `could not find a valid modelname` |
| 抵抗行 | 末尾のモデル名 `R` を削除 | `can't find model 'r'` × 437 |
| 0Ω 抵抗 | `--rmin`（既定 `1e-6`）へ置換 | 行列破綻（エラーが出ない） |
| 浮きノード | `VSUBS` 等が**実際に浮いていれば**基板ポートへ結線 | 基板容量 5.34fF が宙に浮く |
| デバイス接続 | `--reconnect` で端子を抵抗メッシュへ張り替え（**4.6**、既定 off） | 抽出した R が電流経路に入らない（ISS-00205） |
| 0Ω の扱い | `--zero_mode merge` で union-find 統合（**4.6**、既定は微小抵抗代用） | `--reconnect` と併用しないと `Timestep too small` |

**単位換算（`--scale` 既定 1e-6 ＝ `.option scale=1u`）**

| 項目 | kpex 出力 | SI 値 | 換算 | 出力 |
|---|---|---|---|---|
| `L` / `W` | `0.65U` | 0.65 µm | `SI / scale` | `w=650000u`（＝0.65） |
| `AS` / `AD` | `0.169P` | 0.169 µm² | `SI / scale²` | `as=0.169` |
| `PS` / `PD` | `1.82U` | 1.82 µm | `SI / scale` | `ps=1.82` |

**⚠️ `AS`/`AD`/`PS`/`PD` は落とさずに換算して渡すこと**（2026-08-08 ダーマツ判断）。
`spice/` 版はこれらを持たない＝**接合容量ゼロ**で、`inv_16` の実測では
`cell_rise` の charao/orig 比が **RC のみ 0.785 → 接合容量込み 0.825** と、
配線寄生 RC 単独（0.713 → 0.785）に匹敵する寄与があった（ISS-00202）。
フィンガ共有も正しく反映される（端のフィンガ `as=0.26` / 中間 `as=0.135`）。

実行後にサマリが出るので、**ポート順の並べ替え・0Ω 置換数・浮きノードの結線**を必ず確認する。

```
[INF] subckt          : sky130_fd_sc_hd__inv_16 (port order reordered to ref)
[INF] device M -> X   : 32
[INF] resistor        : 437 (zero-ohm replaced by 1e-6 : 102)
[INF] capacitor       : 10
[INF] sky130_gnd -> VNB   : 17 node(s) renamed
[INF] floating node   : sky130_fd_sc_hd__inv_16.VSUBS tied to VNB via 1e-6
```

---

## 4.6 デバイス端子をメッシュへ接続する（`--reconnect`）

```bash
python3 tools/pex2spice.py \
  --in  run_kpex_inv16/kpex_out/inv_16_pex.spice \
  --ref sample_src/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice \
  --zero_mode merge --reconnect \
  --out sample_src/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd_pexrc.spice
```

層 → デバイス種別の対応は**曖昧さの無いネットから学習する**（`VPWR` には pMOS の端子しか無く
層プールも 1 つ → その層＝pMOS 側、と決まる）ので、PDK 固有の決め打ちを持たない。
層が 1 つしか無いネット（ゲート側）は種別を混ぜて 1 プールを共有する。

### 内部ネットは端子数 > ノード数になる

段間などの内部ネットでは、**複数のデバイス端子が同じ拡散コンタクトを共有**するため、
端子数がメッシュノード数を上回る（`buf_1` は端子 2・ノード 1＝両方が同じ点で正しい）。
ポート側でぴったり一致するのは、ピンがフィンガごとに別コンタクトを持つため。

この場合はノードを使い回すが、**どの端子がどのノードかは SPICE 側に情報が無いので
割り当ては近似**になる。必ず警告が出るので見逃さないこと。

```
[WARN] approximate map  : 12 net(s) have more terminals than mesh nodes
[WARN]   $2  nfet : 11 terminal(s) -> 3 node(s) (shared diffusion; assignment is a guess)
```

**順序感度**：`--reconnect_order index` と `reverse` の相対差は、ポート側フィンガだけなら
**median 0.000%**（`inv_16`）だが、**内部ネットを含むと median 0.27% / max 15.4%**
（`buf_*` 7 セル 1372 点）。内部ネットを含むセルの**個別値は近似**として扱うこと。

### ⚠️ 内部ネットの抵抗には kpex 側の当て木が要る（ISS-00207 / ISS-00209）

**pip 版（0.3.12）は内部ネットの抵抗を 1 本も出さない。** `tools/gds2pex.py` の
**`--patch_unnamed_nets`** で実行時に回避する。

```bash
python3 tools/gds2pex.py ... --patch_unnamed_nets --cells buf_8 dfrtp_1
```

効果＝`buf_8` R 222→294 本・被覆 67%→100%／`dfrtp_1` R 219→341 本・被覆 33%→100%。

> **上流 main では既に修正済み**（`50a0549b "R Extraction: use cluster id (e.g. $4)
> if net.name is empty"`）。**当て木は次リリースまでの暫定**で、`50a0549b` を含む
> バージョンが PyPI に出たら削除する（ISS-00209）。

### ⚠️ `--zero_mode merge` が必須

`--reconnect` だけだと **全格子点が失敗する**（`inv_16` で 98 failures）。

```
doAnalyses: TRAN: Timestep too small; time = 2.00563e-15, timestep = 2.5e-24:
            trouble with node "vpw_dyn#branch"
```

メッシュが導通した途端に、0Ω の代用値 **1e-6Ω と 585Ω の 9 桁レンジ**が電流経路に乗って
行列が硬くなる（後述「0Ω 抵抗で ngspice の行列が破綻する」と同じ現象が、今度は本番経路で再発）。
**0Ω を union-find でノード統合する** `--zero_mode merge` で解決する。

| | 抵抗本数 | 値のレンジ | 結果 |
|---|---|---|---|
| `--zero_mode resistor`（既定） | 437 | 1e-6〜585Ω ＝ **9 桁** | **98 failures** |
| **`--zero_mode merge`** | **333** | 0.12〜585Ω ＝ **3.69 桁** | **0 failures** |

`VSUBS` も `VNB` へ畳まれるので、人工素子 `Rvsubs_fix` 自体が不要になる（代表ノードは
**ポート名を最優先**で選ぶ。しないと `VSUBS` 側が代表になってポートが消える）。

### ⚠️ 順序は「再接続 → 統合」

先に統合すると**短絡された `.P*` ノードが畳まれて端子との対応が取れない**
（`VGND` が 16 端子に対し 6 ノードへ減り、スクリプトが停止する）。実装もこの順で固定してある。

### 2 つのオプションの役割は別物

| オプション | 何をするか | 単独で使うと |
|---|---|---|
| **`--reconnect`** | 端子を `.P*` へ張り替え、**R を電流経路に入れる** | **本質**。`merge` 無しだと数値破綻 |
| **`--zero_mode merge`** | 0Ω 短絡をノード統合として畳む | **何も解決しない**（デバイスは主ネットに直付けのまま **0/96**、実測確認済み） |

`--reconnect` を使わないなら `merge` は不要（R が死んでいるので微小抵抗も害が無い。
ISS-00203 の時点で気づけなかったのはこのため）。

### 効果（`inv_16`、orig の 49 点 × 4 kind）

| kind | C のみ | **R 接続** | 差の回収率 |
|---|---|---|---|
| `cell_rise` | 0.825 | **0.929** | 59% |
| `cell_fall` | 0.728 | **0.890** | 60% |
| `rise_transition` | 0.763 | **0.961** | **84%** |
| `fall_transition` | 0.847 | **0.951** | 68% |

最大負荷（1.6818pF）の `cell_rise` も 0.715 → **0.872**。集中直列抵抗 263Ω では 0.815 止まり
だったので、**分布メッシュ（実効 pull-up 180Ω / pull-down 115Ω）のほうがはるかに効く**
（電源側の抵抗も同時に効くため）。

**割り当て順序の任意性は無視できる**：`--reconnect_order index` と `reverse` の相対差は
**中央値 0.000% / 最大 4.5%**（同一形状フィンガのため）。

---

## 4.7 charao へ渡す（`--spice_path`）

**ファイル名は変えず、ルートだけ差し替える**（2026-08-08 ダーマツ判断、ISS-00205）。

```
sample_src/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice   ← プリレイアウト（PDK 純正）
<PEX ルート>/sky130_fd_sc_hd.spice                                        ← PEX 版（同名・全セル入り）
```

```bash
# 4.6 で全セルを 1 本にまとめる（--in は複数指定可）
python3 tools/pex2spice.py --in kpex_out/*_pex.spice \
  --ref sample_src/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice \
  --zero_mode merge --reconnect \
  --out <PEX ルート>/sky130_fd_sc_hd.spice

# charao 側はルートを指すだけ
SPICE_PATH=<PEX ルート> ... bash debug_run.sh run_all
```

`charao --spice_path <dir>` は**各 `std_*.jsonc` の `"spice_path"` を上書き**する
（未指定なら jsonc の値。`--result_path` と同じ流儀）。

**これで target ツリーの複製と jsonc の `sed` が不要になる。**
以前は PEX 版へ切り替えるたびに `cp -r tmp_rc1_target tmp_xxx_target` ＋
`sed -i 's/…_pex.spice/…/'` を手でやっており、条件を変えるたびに事故る余地があった。

> **⚠️ PEX 版に無いセルがあると `chk_netlist()` で止まる。**
> ルートを差し替えると**全セルがそのルートを見る**ので、一部セルだけ PEX 版で回したい場合は
> `--cells_only` / `--mylogic_only` で対象を絞ること。

---

## 5. 抽出に必要なレイヤ情報

`--pdk` を指定すると、kpex 同梱の **JSON-protobuf 形式の Technology 定義**が使われる。
実体は `klayout_pex_protobuf/sky130A_tech.pb.json`（gf180mcuD / ihp-sg13g2 も同梱）。
**独自 PDK に適用するときはこのファイル相当を用意することになる。**

構成は 4 ブロック。

### (1) `layers` — 正規レイヤ（21 種）

抽出が認識するレイヤの名前と GDS 番号の対応。

```
dnwell  nwell  diff  tap  psdm  nsdm  poly
licon1  li1  mcon  met1  via  met2  via2  met3
via3  capm  met4  capm2  via4  met5
```

### (2) `lvs_computed_layers` — LVS 派生レイヤ（54 種）

`layers` から演算で導かれるレイヤ（PMOS 用の diff、NMOS 用の diff など）。
KLayout の LVS ルールデック（`sky130A/libs.tech/kpex/sky130.lvs`）が生成する。

### (3) `process_stack` — 断面の積層（34 層）

各層の **種別・高さ z・厚み・コンタクト情報**。これが 2.5D の幾何計算の土台になる。

```json
{"name": "li1", "layer_type": "LAYER_TYPE_METAL",
 "metal_layer": {"z": 0.9361, "thickness": 0.1,
   "contact_above": {"name": "mcon_con", "layer_below": "li1", "metal_above": "met1",
                     "thickness": 0.34, "width": 0.17, "spacing": 0.19}}}
```

層の種別は 5 つ。

| `layer_type` | 意味 | 例 |
|---|---|---|
| `substrate_layer` | 基板 | `subs` |
| `nwell_layer` / `diffusion_layer` | ウェル・拡散 | `nwell` / `nsd` / `psd` |
| `metal_layer` | 導体 | `poly` / `li1` / `met1`〜`met5` / `capm` |
| `simple_dielectric_layer` | 平坦な絶縁膜 | `psg` / `nild2` / `nild3` … |
| `conformal_dielectric_layer` / `sidewall_dielectric_layer` | コンフォーマル膜・側壁膜 | `lint` / `iox` / `spnit` / `nild3c` |

### (4) `process_parasitics` — 寄生の係数

| キー | 件数 | 例 | 単位の目安 |
|---|---|---|---|
| `side_halo` | — | `8` | µm。寄生を拾う横方向の範囲 |
| `resistance.layers` | 7 | `{"layer_name":"poly","resistance":48200}` | mΩ/□ |
| `resistance.contacts` | 3 | `{"contact_name":"licon_nsd_con","device_layer_name":"nsdm","layer_above":"li1","resistance":185000}` | mΩ/個 |
| `resistance.vias` | 6 | `{"via_name":"poly","resistance":152000}` | mΩ/個 |
| `capacitance.substrates` | 7 | `{"layer_name":"poly","area_capacitance":106.13,"perimeter_capacitance":55.27}` | aF/µm² と aF/µm |
| `capacitance.overlaps` | 43 | `{"top_layer_name":"pwell","bottom_layer_name":"dnwell","capacitance":120}` | aF/µm²（面間） |
| `capacitance.sidewalls` | 7 | `{"layer_name":"poly","capacitance":16}` | aF/µm（同一層の隣接） |
| `capacitance.sideoverlaps` | 62 | `{"in_layer_name":"poly","out_layer_name":"nwell","capacitance":55.27}` | aF/µm（フリンジ） |

### (5) KLayout 側の 3 ファイル

Technology 定義（`*_tech.pb.json`）とは別に、PDK ごとに以下が同梱されている
（`klayout_pex/pdk/<pdk>/libs.tech/kpex/`）。

| ファイル | 役割 |
|---|---|
| **`sky130.lvs`**（2,603 行） | KLayout LVS ルールデック。デバイス認識・レイヤ導出・接続関係を定義し、LVSDB を作る |
| **`sky130A.lyt`**（169 行） | KLayout technology ファイル。GDS レイヤ番号とレイヤ名の対応、読み込み設定 |
| **`sky130A.lyp`**（8,563 行） | レイヤ表示プロパティ。レポート（`.rdb`）を KLayout で見るときの配色 |

kpex はこれを次のように呼ぶ（`kpex_plain.log` の 6 行目に実コマンドが残る）。

```bash
klayout -b -r <kpex>/pdk/sky130A/libs.tech/kpex/sky130.lvs \
  -rd input=<cell>_exported.gds.gz -rd report=<cell>.lvsdb.gz \
  -rd schematic=<cell>_dummy_schematic.spice \
  -rd thr=22 -rd run_mode=deep -rd spice_net_names=true -rd spice_comments=false \
  -rd scale=false -rd verbose=false -rd schematic_simplify=false -rd net_only=false \
  -rd top_lvl_pins=true -rd combine=false -rd combine_devices=false \
  -rd purge=false -rd purge_nets=false -rd no_simplify=true
```

### ⚠️ この `.lvs` は通常の DRC/LVS 用デックではない

`sky130.lvs` の冒頭に明記されている。

```
#===!====!===!===!====!===!===!====!===!===!====!===!===!====!===!===!====!===!===!====!===
# WARNING: this version is not a regular LVS script,
#          instead tailored for parasitic extraction (PEX) by the klayout-pex tool
#===!====!===!===!====!===!===!====!===!===!====!===!===!====!===!===!====!===!===!====!===
```

Efabless 版の sky130A LVS デックをベースに、**PEX 用の改変**が入っている。
デック内は `# [PEX]` でマークされている。違いは 4 点。

**① 通常 LVS は「合わせるために簡約する」が、PEX は「簡約してはいけない」**

上記コマンドラインの `-rd` を見ると、簡約系がすべて off になっている。

| オプション | kpex | 通常 LVS |
|---|---|---|
| `no_simplify` | **true** | false（`netlist.simplify` を掛ける） |
| `combine` / `combine_devices` | **false** | true（並列・直列デバイスをまとめる） |
| `purge` / `purge_nets` | **false** | true（浮きネット・ダミーを掃除する） |
| `schematic_simplify` | **false** | true |
| `top_lvl_pins` | **true** | 用途次第 |

通常 LVS の目的は「レイアウトと回路図が一致するか」なので、**フィンガに分かれた 32 個の MOS を 1 個にまとめる**ような簡約が有利に働く。
PEX では逆で、**フィンガ 1 本ずつ・配線セグメント 1 本ずつの形状が残っていないと寄生を計算できない**。
実際、抽出された `inv_16` は M が 32 個のまま（`cdl` の LVS 用ネットリストは M 2 個に集約されている）。

**② コンタクトを種類別に分割する**

```ruby
# [PEX] NOTE: this was missing in the original sky130A LVS script!
#       we want to split mcon into mcon_con and mcon_vpp
#       (might not cause an issue in regular LVS, but in PEX context necessary)
licon_poly_con = licon.and(poly)
licon_nsd_con  = licon.and(nsd)
licon_psd_con  = licon.and(psd)
```

通常 LVS は「繋がっているか」だけ分かればよいので `licon` を 1 種として扱える。
PEX では**下地が poly か nsd か psd かでコンタクト抵抗が違う**ため分割が必須。
これが `process_parasitics.resistance.contacts` の `licon_poly_con` / `licon_nsd_con` / `licon_psd_con` に対応する。

**③ ピン形状を明示的に接続する**

```ruby
# [PEX] Pins (NOTE: a regular LVS would not do this, we need it for PEX)
poly_pin_con = poly_pin & poly_con
li_pin_con   = li_pin   & li_con
...
# [PEX] Attaching pins (NOTE: a regular LVS would not do this, we need it for PEX)
connect(poly_con, poly_pin_con)
connect(li_con,   li_pin_con)
```

通常 LVS はピンラベルでネット名が付けば十分だが、
PEX では**ピンが「どの形状のどこにあるか」まで必要**になる（抵抗網の端子をそこに繋ぐため）。

**④ レイヤ名を LVSDB へ書き出す**

```ruby
# [PEX] export layer names
# [PEX] naming splitted licon (can be licon over nsd/psd/poly)
# [PEX] naming pins
```

抽出後の形状を**正規レイヤ名に逆引きできる**ようにしておかないと、
`process_parasitics` の係数を引けない。通常 LVS には不要な情報。

> なお、この改変が行き届いていない箇所もある。`inv_16` の抽出で出た
> `Unable to find info about extracted LVS layer 'licon'` は、
> LVS が出した `licon` に対して Technology 定義側の名前が `licon1` で食い違っているもの。

---

**まとめると、独自 PDK で寄生抽出したければ必要なのは**

1. **レイヤの GDS 番号の対応表**（`layers` ＋ `.lyt`）
2. **PEX 用に改変した LVS ルールデック**（`.lvs`。簡約を全部止め、コンタクトを下地別に分割し、ピン形状を接続し、レイヤ名を書き出す）
3. **断面の積層情報**（`process_stack`。各導体の高さ・厚み、絶縁膜の種類と厚み、コンタクト/ビアの寸法）
4. **寄生の係数**（`process_parasitics`。シート抵抗、コンタクト/ビア抵抗、面間容量、側壁容量、フリンジ容量）

の 4 つ（＋表示用の `.lyp`）。3 と 4 は**ファウンドリの断面図と寄生パラメータ表**から作ることになる。
2 は既存の LVS デックを流用できるが、**そのままでは使えず PEX 用の改変が要る**（上記 ①〜④）。

---

## 6. 注意点（実施時に踏んだもの）

### モジュール名は `kpex` ではなく `klayout_pex`

```
$ python3 -m kpex --help
No module named kpex          ← 失敗

$ python3 -m klayout_pex --help
Usage: __main__.py [--help] ... ← 成功
```

CLI の実行ファイル名は `kpex` だが、lrPymRPC は許可コマンド（`python3` 等）しか起動できないため
`python3 -m klayout_pex` の形で呼ぶ。

### 端子の並びと構成が `spice/` 版と違う

| 由来 | `.SUBCKT` 行 |
|---|---|
| `spice/sky130_fd_sc_hd.spice` | `(VGND VNB VPB VPWR A Y)` |
| **kpex 抽出版** | `(VGND A Y VPWR VPB sky130_gnd)` |

**`VNB` が無く、代わりに基板ノード `sky130_gnd` が付く。**
基板ノード名は LVS の既定（ログに `No substrate name given, default name is sky130_gnd`）。

**→ 4.5 のスクリプトが `sky130_gnd`→`VNB` の置換とポート順の並べ替えを行うので、
`ports_dict`（jsonc）は `spice/` 版と同じまま使える。**

### ⚠️ KLayout のバージョンでポート順が変わる（ISS-00211）

サーバの KLayout を 0.29 系 → **0.30.10** へ上げた前後で同条件の抽出を比較した結果：

| | 変化 |
|---|---|
| **抵抗値・容量値** | **完全一致**（`inv_16` R 437 本・C 10 個／`buf_8` R 294 本・C 15 個、値の多重集合が同一） |
| `.SUBCKT` のポート順 | `VGND A Y VPWR VPB` → **`A VGND VPB VPWR Y`（アルファベット順）** |
| 内部ネットの自動採番 | `\$2` → `\$3` |
| 抵抗行の順序・連番 | 変化 |

**物理量は不変で、変わるのは表記だけ**。ポート順は `--ref` 基準の並べ替えが、
内部ネット名は `.P*` ノードと端子の対応で処理しているため、いずれも吸収される。

> **KLayout を上げたときは、まず値の多重集合が一致するかを確認する。**
> ポート順は charao の `ports_dict` と厳密照合される（`myLogicCell.py` の `chk_ports`）ので、
> 並べ替えが無ければ sim が壊れる。

### 同一ネット間の抵抗の警告（SPICE からは落ちない）

```
WARNING Invalid attempt to create resistor ext_1   between same net ...:A with value 24.53
WARNING Invalid attempt to create resistor ext_288 between same net ...:Y with value 13.19
```

**この 2 本は SPICE 出力には残る**（CSV / SPICE とも R=437 で一致、1 本も欠けていない）。

```
Rext_1   A A  24.5333333333 R      ← 両端とも A
Rext_2   A A.$1.19  3.46666666667 R
Rext_288 Y Y  13.1878787879 R      ← 両端とも Y
Rext_289 Y Y.$80.19 15.1272727273 R
```

kpex は 1 本のネットを多数のサブノード（`A.$1.19` 等）に刻んで抵抗網を作るが、
**隣り合う 2 つのサブノードが両方ともトップレベルのネット名にラベル付けされる**と自己ループになる。
警告の出どころは `netlist_expander.py:129`＝**KLayout の netlist オブジェクトを組む側**で、
そちらは同一ネット間のデバイスを弾く。**SPICE テキスト出力側にはその判定が無い**。

**実害**：ngspice では両端が同一ノードの抵抗に電流は流れないので**動作上は無害**。
ただし裏を返せば **そのサブノード間が短絡された＝その抵抗分が失われている**。
`inv_16` では入力 A に 24.5Ω、出力 Y に 13.2Ω。`inv_16` の駆動抵抗（1.682pF を 1.5ns で振る＝数百Ω相当）
に対し Y の 13Ω は数 % 程度。

### ⚠️ R は分布、C は集中（最重要）

`--mode RC` でも **R と C で粒度がまったく違う**。

| | 素子数 | ノード |
|---|---|---|
| **R** | **437 本** | **365 ノード**（トップレベルは `A` `VGND` `VPWR` `Y` の 4 つのみ、**残り 361 は内部サブノード**） |
| **C** | **10 個** | **5 ノードのみ**（`A` `Y` `VGND` `VPWR` `VSUBS`）＝**全てトップレベル** |

C の 10 個は **5 ネットの全組合せ C(5,2) = 10** にちょうど一致する。

```
Cext_1  A    VGND   337.311a      Cext_6  VGND VSUBS  943.232a
Cext_2  A    VPWR   398.928a      Cext_7  VGND Y      1.02235f
Cext_3  A    VSUBS  3.09816f      Cext_8  VPWR VSUBS  986.485a
Cext_4  A    Y      1.69256f      Cext_9  VPWR Y      1.40064f
Cext_5  VGND VPWR   147.109a      Cext_10 VSUBS Y     311.176a
```

つまり **C はネット単位に集約されてピンノードに 1 個ずつ貼られ、抵抗網の内部 361 ノードには容量が 1 つも付かない**。

**帰結（2026-08-08 ダーマツ指摘で訂正）**：

ネット容量は全て**ピンノードに集中**する。
**ただし単一標準セルのスケールでは、分布か集中かは実質的に効かない。**

```
R_max = 585Ω × C_total(Y) = 4.42fF  →  τ = 2.59 ps
実測の transition = 0.1〜1.5 ns      →  τ は 400〜600 倍小さい
```

セル内配線は電気的に短く、**抵抗網は単なる直列抵抗として DC 的に振る舞う**。
容量を分布させても集中させても、**合計値が同じなら結果は変わらない**。
（当初「分布 RC 遅延が再現されない」ことを制限として挙げたが、これは誤り。
長い配線を含むブロックレベルの抽出では意味を持つが、標準セル単体では無関係）

理由は 2.5D エンジンが容量を**ネット対ごとの総量として解析式で算出**する設計だから
（`process_parasitics.capacitance` が `overlaps` / `sidewalls` / `sideoverlaps` の**係数**で、
面積・周長から総量を出す形）。抵抗側は形状を刻んで網にするが、容量はその網に分配されない。

**ソースで確認済み（2026-08-08）＝分布定数には対応していない**。
`klayout_pex/rcx25/netlist_expander.py` を見ると、C と R は**まったく同じループ構造**で貼られる。

```python
summary = extraction_results.summarize()
cap_items = sorted(summary.capacitances.items())     # キーは (net1, net2)
res_items = sorted(summary.resistances.items())      # キーは (net1, net2)

for idx, (key, cap_value_femto) in enumerate(cap_items):
    net1 = name2net[key.net1]; net2 = name2net[key.net2]
    c = top_circuit.create_device(cap, f"ext_{idx+1}")
    c.connect_terminal('A', net1); c.connect_terminal('B', net2)
```

違いは `summarize()` が返す中身にある。

- **抵抗抽出はネットをサブネットに分割する**（`A.$1.19` 等が新規ネットとして作られる）
- **容量抽出は分割前の元ネット単位で総量を集計する**

両者は独立に走っており、**C を R 網へ分配する処理は存在しない**。`--mode CC/RC/R` は
`need_capacitance()` / `need_resistance()` の真偽を切り替えるだけで（`rcx25/pex_mode.py`）、粒度は変わらない。
本家 GitHub も 2.5D エンジンを **"under development"** とするのみで、この制限の明記は無い。

同ファイルから、以下 2 点も裏付けが取れた。

```python
r.set_parameter('R', res_value)
if net1 == net2:
    warning(f"Invalid attempt to create resistor {r.name} between same net ...")
```

→ **警告を出すだけで素子は作られる**（SPICE に残る）。

```python
vsubs_net = top_circuit.create_net("VSUBS")   # 作るだけで基板へ結線しない
fc_gnd_net = top_circuit.create_net('FC_GND') # 同上、未使用
```

→ **`VSUBS` は生成のみで結線されない**（浮きノードの原因、ISS-00203(b)）。

### 🛑 R は電気的に無効（2026-08-08 判明、ISS-00205）

上の「抵抗網は直列に入る」という前提そのものが**誤り**だった。生出力（`inv_16_pex.spice`）の
接続を全数解析した結果：

| 対象 | 繋がっているノード |
|---|---|
| **トランジスタ 32 個** | `A` / `VGND` / `VNB` / `VPB` / `VPWR` / `Y` ＝**トップレベルのネット名のみ** |
| **容量 10 個** | `A` / `VGND` / `VPWR` / `VSUBS` / `Y` ＝**同上** |
| **抵抗 437 本** | 367 ノード。**うち 361 ノードには素子も容量もポートも繋がっていない** |
| **主ネット間をつなぐ抵抗** | **0 本**（唯一の 1 本は整形時に足した `Rvsubs_fix`） |

**つまり抵抗網は主ネットからぶら下がる行き止まりの枝で、電流経路に一切入らない。**
ngspice から見れば `--mode RC` の出力は **「容量のみの集中モデル」と等価**である。

原因は上記ソースのとおり、**容量は元ネット名（`name2net[key.net1]`）に貼られる**一方で
**抵抗抽出だけがネットをサブネットへ分割する**ため。デバイス端子は LVS が抽出した時点の
元ネットに付いたままで、**サブネットへ張り替える処理が無い**。

**ただし後処理で直せる**（`--reconnect`、下記 4.6）。メッシュノード名 `<net>.P<n>.<layer>` の
**`.P*` がデバイス端子そのもの**で、`.SUBCKT` のポート（素の `net` 名）が外部ピンだった。
ノード数は端子数と**完全に一致**する。

| net | `.P*` ノード数 | 層コード | デバイス端子数 |
|---|---|---|---|
| `Y` | 32 | 14×16 ／ 16×16 | 32（pMOS drain 16 ＋ nMOS drain 16） |
| `A` | 32 | 18（poly）×32 | 32（ゲート） |
| `VPWR` | 16 | 16×16 | 16（pMOS source） |
| `VGND` | 16 | 14×16 | 16（nMOS source） |

層コードも 14＝nMOS 側／16＝pMOS 側／18＝poly と整合する。公式ドキュメントの R テストパターン
（`nfet_li1`）も同じ命名（`G.$1.17` / `G.P0.16`）で、この規約は kpex 共通とみてよい。

### 上流に分布接続の手段は無い（2026-08-08 調査）

- `--mode {CC, RC, R}` は `rcx25/pex_mode.py` の `need_capacitance()` / `need_resistance()` を
  切り替えるだけで、**lumped / distributed を選ぶフラグは存在しない**
- `rcx25/netlist_expander.py` は R も C も**ネット名を指定して新規デバイスとして作るだけ**。
  該当箇所に **`# TODO: ... we only want to replace resistor / capacitor devices and for example not transitors`**
  とあり、**トランジスタを扱えていないことを上流自身が明記**している
- 分布 RC を運ぶ出力形式は**どちらも未実装の要望**：**DSPF ＝ issue #164** ／
  **ngspice 互換 netlist ＝ issue #165**（後者は 4.5 の整形が必要な理由そのもの）
- magic エンジンなら `ext2spice` 経由で正しく繋がるが、ダーマツ環境では magic が使えない。
  FasterCap は容量専用

> **帰結**：将来 #164（DSPF）が入れば本筋の解決。それまでは **4.6 の `--reconnect` が代替**。

---

### ⚠️ 0Ω 抵抗で ngspice の行列が破綻する

kpex は「短絡」を **値 0 の抵抗**として書き出す（`inv_16` で **103 本 / 全 437 本**）。
ngspice はこれを **1e-12Ω にクランプ**するため、抵抗値のレンジが **1e-12〜585Ω ＝ 15 桁**になり
解が壊れる。症状は分かりにくい。

| 観測 | 意味 |
|---|---|
| `vout = 2.584V` が定常 | 回路内の最大電源 1.8V（`VFORCE_VAL`=1.8 / `Ron`=0.1Ω）を**超えており物理的にあり得ない** |
| 入力 `vrel=1.8V` で `i(vss)=5.8mA` が流れ続けるのに出力が下がらない | **KCL が成立していない** |
| 入力が 0V のまま `vout` が 1.80→2.59V へ跳躍 | 入力と無関係に電圧が生成されている |
| ngspice のエラー | **出ない**（`Warning: Value of resistor ... too small, set to 1.000000e-12` が 103 件出るのみ） |
| charao 側の症状 | `.meas` が `out of interval` → `Value res_prop_rel_out is not defined!!` → `my_exit()` で全体停止 |

**対処＝0Ω を 1µΩ（`1e-6`）に置換する**（2026-08-08 ダーマツ判断）。これで
レンジが 1e-6〜585Ω（9 桁）に収まり、**0 failures・`.meas` 成功**になった。

**kpex 側に回避オプションは無い**。閾値系（`--magic_cthresh` 0.01fF / `--magic_rthresh` 100Ω /
`--magic_short {none,resistor,voltage}` / `--magic_merge {none,conservative,aggressive}`）は
**すべて magic エンジン専用**で、2.5D には効かない。

> より正しいのは「0Ω＝ノードの同一視」として **Union-Find でノードを統合する**方式だが、
> 1µΩ 置換で実用上問題なく動いたため当面はこちらを採る。

### ⚠️ デバイス行と抵抗行は charao に渡す前に変換が必要

**→ 4.5 の `tools/pex2spice.py` が自動で処理する。以下は症状の記録。**

| 項目 | kpex の出力 | 必要な形 | 症状 |
|---|---|---|---|
| MOSFET | `M$17 Y A VGND VNB sky130_fd_pr__nfet_01v8 L=0.15U W=0.65U ...` | `X$17 Y A VGND VNB sky130_fd_pr__nfet_01v8 w=650000u l=150000u ...` | sky130 は `.subckt` なので `M` では `could not find a valid modelname` |
| W/L の単位 | `W=0.65U`（＝0.65µm） | `w=650000u`（`.option scale=1u` 前提） | 換算しないと 1e6 倍ずれる |
| AS/AD/PS/PD | `AS=0.169P` / `PS=1.82U` | `as=0.169` / `ps=1.82` | 落とすと**接合容量が入らない**（`spice/` 版と同じ状態＝比較の意味が減る） |
| 抵抗 | `Rext_1 A A 24.5333333333 R` | `Rext_1 A A 24.5333333333` | 末尾のモデル名で `can't find model 'r'` が 437 件 |

`.option scale=1e-06` が効いていることは `.lis` の
`option SCALE: Scale is set to 1e-06 for instance and model parameters` で確認できる。

### `licon` のレイヤ情報が無いという警告

```
Unable to find info about extracted LVS layer 'licon'
```

LVS が抽出した `licon` に対応する寄生情報が Technology 定義に無い、という意味。
`layers` にあるのは `licon1` で、名前が食い違っている。コンタクト抵抗は
`resistance.contacts` の `licon_*_con` で扱われるため致命的ではないと見ているが、未確認。

### `model_section` の扱い

抽出ネットリストの R は素の `R` 素子（モデル参照なし）に見えるため、
`config_lib.jsonc` の `model_section` は `["mos"]` のままで足りる可能性がある。
`["mos","rc"]` が要るかは sim を通して確認すること（ISS-00184 の機構）。

---

## 6.5 転送量を絞る（lrPymRPC 経由で回す場合）

既定の `--SOURCE_INCLUDE` は拡張子だけで拾うため、sky130A では **59.93MB / 1,215 ファイル**を毎回運ぶ
（SRAM マクロ 5.17MB・IO セル 0.79MB・montecarlo 1.22MB・未使用コーナーのデバイスモデル多数）。
`debug_run.sh` に **`SOURCE_INCLUDE_ITEMS`** を追加したので、ファイル名を並べて絞れる（ISS-00204）。

モデルの include 閉包は **10 ファイル / 2.73MB** だけである（`.model_sky130_TT.sp` から再帰的に解決）。

```
sky130_fd_pr__nfet_01v8__tt.pm3.spice            1110.6 KB
sky130_fd_pr__pfet_01v8_hvt__tt.pm3.spice        1323.4 KB
typical.spice                                     339.9 KB
sky130_fd_pr__model__r+c.model.spice               10.6 KB
res_typical__cap_typical__lin.spice                 2.0 KB
res_typical__cap_typical.spice                      0.9 KB
sky130_fd_pr__nfet_01v8__mismatch.corner.spice      0.9 KB
sky130_fd_pr__pfet_01v8_hvt__mismatch.corner.spice  1.0 KB
sky130_fd_pr__res_generic_nd.model.spice            0.9 KB
sky130_fd_pr__res_generic_pd.model.spice            0.9 KB
```

**`model_section=['mos']` でも `r+c` セクションの include 先まで必要**（ngspice がファイル全体を
読む際に解決しようとするため）。落とすと `Error: Could not find include file ...` で全滅する。

---

## 7. 関連

- `tools/gds2pex.py` — GDS → PEX netlist（複数セル一括、3 章）
- `tools/pex2spice.py` — PEX netlist → charao 用 SPICE（整形＝4.5／再接続＝4.6）
- `docs/SPEC_make_templates.md` — template 決定の 5 stage
- `docs/SPEC_config_lib.md` — `model_section`
- ISS-00201 — 駆動サイズ依存の系統差（本 HOWTO の動機）
- ISS-00202 — `inv_16` での比較（orig / RC 無し / RC あり / RC＋接合容量あり）
- ISS-00203 — 抽出ネットリストの整形（4.5 のスクリプト化で対応済み）
- ISS-00205 — **抽出した R が電気的に無効**（デバイス端子がメッシュへ繋がらない）
- ISS-00206 — charao の netlist に `sa`/`sb`/`sd` が無く LOD が無効
- KLayout-PEX: https://github.com/iic-jku/klayout-pex
- ドキュメント: https://iic-jku.github.io/klayout-pex-website/doc/doc.html
