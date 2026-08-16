# CHANGELOG

このファイルは UTF-8 で記述されています。

---

## [2.0.0.a17] 2026-08-16

`power_tin` / `power_tout`（energy2）/ `passive` の `maxstep` を **`tmax_low` 固定**にした。
leak の `.MEASURE AVG` 区間に刻みが入らず、`.lib` の `internal_power` がゼロになる問題の是正（ISS-00236）。

> **a15 / a16 の CHANGELOG 追記漏れを本エントリで回収する**（`pyproject.toml` も `a14` のまま
> 止まっていた）。2026-08-05 の `a03` と同じ事故の再発。
> - **[2.0.0.a15] 2026-08-14** — 文書：`docs/SPEC_measure.md` §12 に `tmax` の考え方と
>   `tsim_end` の切り上げを追記。`tmax` は「刻み」ではなく「刻みの上限」であり実際の刻みは
>   LTE 制御が `delmin`(=1e-11×tmax) 〜 `tmax` で決めること、`pts` は実点数ではなく
>   「点数の下限見積り」であることを明記。§12.2.1 に `tsim_end` の 1ps 切り上げ（ISS-00230）を新設
> - **[2.0.0.a16] 2026-08-15** — 変更：sky130 の `tmax_low` を `0.01` に確定し
>   `tmax_low_power_tin` を廃止（ISS-00234）

### 変更

- **`maxstep` を `tmax_low` 固定に**（ISS-00236、ダーマツ判断）。対象は 3 経路。
  - `runSpicePowerTinSingle`：`maxstep = h.mls.tmax_low`
  - `runSpicePowerToutSingle`：**energy2 のみ** `param.maxstep = _clamp_maxstep(tmax_low × time_mag)`。
    energy1（`trans_out` の最適化＝ISS-00232 の `maxstep_fix`）は**従来どおり**
  - `runSpicePassiveSingle`：`maxstep = h.mls.tmax_low`

  leak は `.MEASURE TRAN i_*_leak AVG ... FROM={_t_in0-101*_tslew_min} TO={_t_in0-1*_tslew_min}` で
  測るため、**窓幅は `100 × simulation_slew_min`（sky130 で 100 ps）固定**。一方 ISS-00234 の統一式
  `maxstep = clamp(slope / points_per_transition, tmax_low, tmax_high)` は `index_1=1.5` で
  **750 ps** まで開き、窓に点が入らなくなっていた。

  | 窓内の点 | ngspice の挙動 | `.lib` |
  |---|---|---|
  | 2 点以上 | 正常に平均が出る | 正しい値 |
  | 1 点 | **`avg(TRIG) : out of interval` → `failed!`** | **ゼロ**（charao が 0 を代入） |
  | 0 点 | **エラーを出さず `0.000000e+00` を返す** | leak 減算が抜けた値（**無警告**） |

  `.meas` 欠損時の処理は `sys.exit()` だが**ワーカースレッド内なのでそのスレッドだけ終了**し、
  `Failed to launch spice` は増えないため **「0 failures」と表示されたまま値が欠ける**。

  検証（sky130 / full grid）：
  - `dfxtp_1` / `power_tin`：ゼロ **12 → 0**、`i_vdd_leak` が 7 点とも `-4.033396e-09` で一致
  - `dfrtp_1` / `power_tout`：ゼロ **11 → 0**、無警告の 0 A **9 → 0**、所要 6 分 → 22 分
  - `dfstp_1` ほか 5 セル / `passive`：ゼロ **6 → 0**

- **ISS-00219 / ISS-00234 で外していたガードの復元**。旧実装の
  `max(maxstep/20, min(maxstep/5, tslew_min*20))` は **ISS-00094/00095 が leak の AVG 区間に
  複数ステップを入れるために設けた制約**だったが、`power_tin`（ISS-00234）/ `power_tout`（ISS-00219）/
  `passive`（ISS-00234）の **3 箇所とも「根拠不明」として廃止**していた。根拠はこの窓にあった。

## [2.0.0.a14] 2026-08-14

const（setup / hold / recovery）の掃引を高速化した。初期化のやり直しを止め、
`nodeset` で状態を復元して測定区間だけを回す。**gf180 の full grid で 1.46 倍**。

### 追加

- **`const_start_offset_enable`**（既定 `true`、ISS-00220）。0 回目（準備 run）で
  `_t_init3 + 0.4 ns` 時点の内部ノード電圧を取得して `nodeset_<arc>_c<i1>_r<i2>.sp` を書き、
  1 回目以降は `.include` で復元しつつ **`start_offset`（負値）を全時刻に加算**して
  測定区間だけを回す。`false` で従来動作。仕様は `docs/SPEC_const.md` §7。
- **`[INFO] maxstep_fix`**（ダーマツ指示）。確定した `maxstep` と VOUT の遷移時間
  （`vout_trans`）、遷移あたりの点数（`pts`）を**ログに残す**。`.lib` に出ない量なので、
  従来は `work`（`.sp` / `.lis`）を回収しないと解析できなかった。識別子は **`.sp` の命名から
  `_sXX`（掃引点）を除いた形**で、マルチスレッド実行で行が混ざっても対象を特定できる。

  ```
  [INFO] maxstep_fix <cell>/vt_<vdd>_<temp>_<n>_<meas>/oir=<oirc>_arc=<arc>_c<i1>_r<i2> \
         maxstep=7.2553e-12 vout_trans=1.39407e-11 pts=1.92
  ```

### 修正

- **`MyTbParam` は `@dataclass` なのに pydantic の `Field(default_factory=...)` を既定値に
  使っている**ため、明示代入しないと `FieldInfo` が残る（jp2 で
  `TypeError: 'FieldInfo' object is not iterable`）。leakage 経路は必ず代入するので露見して
  いなかった。`set_common_value` で `internal_nodes` を確実に初期化する。
- **`WAVE_RAW` の保存信号に DUT 内部ノードが含まれていなかった**（TB トップの 14 本のみで、
  ICG の `vout_infos` がある場合に 1 本追加されるだけ）。jp2 の `write` 行で `internal_nodes` を
  展開し、**`nodeset` 対象の全ノードを raw に保存**する。波形での切り分けに必須だった。

### 確認

gf180 `latrnq_1` + `dffrnq_1` × const 6 measure × 10×10（全 1000 点）、両 run とも
**0 failures / 0 traceback**、const に `0.0000` の張り付き 0 件。

```
高精度（enable=false）  2503 秒（41.7 分）
中精度（enable=true）   1719 秒（28.7 分）      1.46 倍

値のずれ   |差| = 0     476/1000（47.6% が完全一致）
           |差| ≦ 0.010  837/1000
           |差| ≦ 0.050 1000/1000（全点）
           最大          0.0490 ns
```

参考として、同じデータの **charao vs orig は最大 0.393 ns**（`|0.1ns|` 以内 241/1000）なので、
**高速化由来のずれはその 1/8**。「長時間・高精度／短時間・中精度」で使い分ける。

### 注意

- **既知の限界**：`net9` のような **VDD を超えるブートストラップ的な定常値**を持つノードは、
  `nodeset`（DC 反復の初期推定値）では再現できない（DC に存在しない状態のため）。
  ずれの主因はこれで、`dffrnq_1` の `recovery_rising`（`index1` 小・`index2` 大）に集中する。
- **PWL の先頭固定点にも offset が要る**（`VPC_CTRL` 2 箇所・`VIN`/`VREL`/`VCLK` 15 箇所）。
  忘れると先頭だけ固定・2 点目以降が負値になり**時刻が逆行**して PWL が不正になる。
- **`nodeset` ファイル名に arc を含める**こと。含めないと同一格子点の rise/fall arc で
  **上書きが起きて論理が反転**する。
- `.tran` の `tstart` は **0 のまま**。`tstart` を使っても `0〜tstart` は計算されるので短縮にならない。

---

## [2.0.0.a13] 2026-08-13

`supress_sim_msg` / `supress_debug_msg` が書いても効かない状態を解消した。
`.lib` の値には一切影響しない（ログ出力の経路だけの変更）。

### 修正

- **`print_msg_sim` / `print_msg_dbg` が定義だけで呼び出し 0 箇所＝dead だった**（ISS-00226）。
  対応する設定 `supress_sim_msg` / `supress_debug_msg` は**書いても書かなくても出力が変わらない**
  状態で、ISS-00225 の `extra:"forbid"` 導入で値がモデルへ届くようになった後も無効のままだった。
  該当する出力を printer 経由に通して設定を生かした。

  ```
  [INFO] generate tb={spicef}                      -> h.mls.print_msg_sim()   charao_run.py の 8 箇所
  [DEBUG] sp count ... forcing os._exit(0)         -> mls.print_msg_dbg()     _check_dbg_sp（引数に mls 追加）
  ```

  `[Error]`（61 箇所）と他の `[INFO]` は**抑制対象にしない**（失敗を見逃す危険があるため）。

### 確認

gf180 `inv_1` × `delay` × 1 点 × `DEBUG_STOP=3`。jsonc 設定を反転した 2 run で
**2 つの設定が独立して効くこと**を実証した。

```
run  supress_sim_msg  supress_debug_msg   [INFO] generate tb   [DEBUG] sp count
 A       false             true                  3 行               0 行
 B       true              false                 0 行               1 行
```

**`--debug_stop` は CLI 引数、`supress_debug_msg` は jsonc 設定**と入り口が違うが、
両者が噛み合っていることも同時に確認した。

---

## [2.0.0.a12] 2026-08-13

const（setup / hold / recovery）の判定量と閾値の決め方を見直した。
**`.lib` の const 値は全面的に変わる**（delay / transition / power / leakage は不変）。

### 修正

- **判定量を `judge_dly` に一本化**（ISS-00227）。旧実装は **FF で `prop_clk_out` を流用**して
  いたが、これは `.lib` の `rising_edge` / `falling_edge` の値そのものなので TRIG 閾値を
  動かせない。`judge_dly` は判定専用（`.lib` 非出力）なので基準を自由に選べる。
  あわせて **FF の hold 用 `judge_dly` を jp2 に新規追加**した（従来この分岐には無かった）。
- **`--measures_only` に存在しない measure 名を渡すと静かに失敗する**（ISS-00228）。
  全 meas_type がスキップされ、**エラーも警告も出ないまま計測ゼロで `.lib` だけが生成される**
  （timing ブロック 0 件）。`debug_run.sh` の生成物確認は `.lib` のセル数しか見ないため
  **「0 failures / .lib N cells」と表示されて成功に見える**。起動時に名前を検証し、
  未知の名前があれば有効名一覧を出して停止する。有効名は `logic_dict` から動的に集めるので
  `--mylogic_user` で追加した logic の measure も自動で許容される。

### 変更

- **`judge_dly` の TRIG 側閾値を遷移の開始側へ**（ISS-00227）。新キー
  `const_judge_threshold_rise`（0.1）/ `const_judge_threshold_fall`（0.9）。
  TARG（出力 50%）と `.lib` に出る値・ヘッダ宣言は変えない。

  ```
  50% 基準  : nominal に「入力が 50% から実効的な確定点まで進む時間」が混入し、
              slew が緩いほど判定量が小さく評価される
  開始側    : slew とともに必ず大きくなる側に出るので、絶対値閾値の意味が corner 間で安定する
  完了側(0.9): judge_dly が負になり得て abs()+running-min の判定が壊れる（ISS-00221 と同型）ため不採用
  ```

- **劣化閾値に比例項を追加**（ISS-00227）。新キー `sim_time_const_threshold_ratio`（0.03）。
  実効閾値 = **`min(sim_time_const_threshold, d0 × 係数)`**（`d0` は `judge_dly` の running-min）。
  `0.0`（既定・未指定）で従来動作。**判定量が `judge_dly` なので閾値も同じ量のスケールに紐づける**。
- **`min_pulse_width` の閾値を分離**（ISS-00227）。新キー `sim_time_pulse_threshold`。
  const 側に比例項を入れたことで `sim_time_const_threshold` が measure によって違う意味を
  持つ状態になったため。**値は各 PDK の従来値と同一で挙動不変**。比例項を設けないのは、
  判定量が `prop` と `trans` の 2 つ（OR 判定）で **`trans` は掃引でほとんど変化しない**
  （実測 2%）ため。

### 確認

すべて gf180（TT / 5.0V / 25℃）、`index1` = 0.02・2.214 × `index2` 全 10 点、0 failures。

- **退行なし**：`latrnq_1` の recovery 10 点が変更前と**完全一致**（最大差 0.000000 ns）。
  TRIG の移動は running-min との差分判定で相殺され境界が動かない、という事前予測どおり。
  `.sp` 実測で rise arc `VAL=0.5` / fall arc `VAL=4.5` を確認。
- **`min_pulse_width` は挙動不変**：`latrnq_1` / `dffrnq_1` / `icgtp_1` の 9 項目・27 点が
  キー分離前と**完全一致（差 0）**。
- **orig との差**（\|0.1 ns\| 以内の点数）：

  ```
  recovery  latrnq_1                 3/20   最大|差| 0.869 -> 0.307 ns
  setup     dffrnq_1 + latrnq_1     23/80   「96/96 点で一方向に小さい」は解消（ISS-00222 クローズ）
  hold      dffrnq_1                15/40   rise は 15/20 と良好
  ```

### 注意

- **全点一致には到達していない**（合計 41/140）。orig の境界に対応する劣化量は
  **0.00005〜0.027 ns と 500 倍ばらつき**、`d0` にも `trans_out` にも比例しないため、
  **閾値則をどう作っても吸収できない**。`min(0.1, trans_out × K)` の案も試算して 6/20 止まり、
  判定量を `trans_out` の劣化にする案は掃引で 2% しか動かず原理的に不成立だった。
- **残課題**：`latrnq_1` の setup fall（0/20）と `dffrnq_1` の hold fall（0/20）が全点不合格で、
  いずれも `fall_constraint` 側。とくに **hold fall は `index1` 大側で符号が一致しない**
  （orig は 0 付近で符号が変わるのに charao は一貫してマイナス、10 点中 8 点で不一致）。
  詳細は ISS-00227 に記録。

---

## [2.0.0.a11] 2026-08-13

jsonc の未知キーを黙って無視せず、起動時にエラーとして検出するようにした。

### 修正

- **pydantic の未知キー黙殺を止める**（ISS-00225）。既定（`extra="ignore"`）では
  `config_lib.jsonc` / `std_*.jsonc` のキーを打ち間違えても**無警告で既定値のまま走り、
  変更が効いていないことに気付けない**。ISS-00219 の作業中に
  `simulation_points_per_transition` をリファクタで巻き添え削除し、**55 分の検証が丸ごと
  無効**になった実績がある。`MyLibrarySetting` / `MyLogicCell` / `MyItemTemplate` の
  3 モデルに **`model_config = ConfigDict(extra="forbid")`** を追加した。

### 変更

導入にあたり、**既に黙殺されていた 17 件**（モデル定義との全数突合で検出）を解消した。

- **`config_lib.jsonc` の 4 キーが実装のフィールド名と食い違っていた**（全 4 PDK）。
  jsonc 側を実装名へ合わせた。

  ```
  jsonc（旧）                実装のフィールド名（新しい jsonc のキー）
  run_sim                 -> runsim
  supress_message         -> supress_msg
  supress_sim_message     -> supress_sim_msg
  supress_debug_message   -> supress_debug_msg
  ```

  前 2 者は jsonc の値と既定値が偶然一致していたため実害は無かった。
  `supress_debug_message:"true"` だけ既定 `"false"` と食い違っていたが、
  対応する `print_msg_dbg` の呼び出しが 0 箇所のため出力は変わらない（→ ISS-00226）。
- **gf180 `std_seq.jsonc` の `"primitive"` 54 行を削除**。`MyLogicCell` に該当フィールドは
  無く（`git log -S` で過去にも無し）、sky130 の `std_seq` には 1 件も無い。
  **UDP 名と引数は `mylogic_*.py` の `vcode` 側が固定で持つ**ため jsonc から差し替える
  余地がなく、ISS-00172（primitive を `std_primitives.v` へ移設）の残骸だった。
  4 種（`udp_iq_ff_n` / `_ff_hn` / `_latch_n` / `_latch_hn`）とも `std_primitives.v` に
  定義済みのため、削除だけで重複が解消する。

### 確認

- **gf180 `dffq_1` × 2x2 corner × 全 measure の実 sim**（`run_forbid_gf1`、
  `EXEC_SCRIPT=local_repo`）＝ **0 failures / 0 traceback / .lib 1 cells**。
  `.lib` に値 0 の格子点は 0 個。本体 `.v` の primitive 定義は 0 件で、UDP 参照
  `udp_iq_ff_n` は `_primitives.v` の定義 4 件に含まれ**未定義参照ゼロ**。
- 4 PDK の jsonc を実構築するドライランで、gf180 229 / sky130 181 / OSU035 16 セルが通過。

### 注意

- **TRIP62 は本版では起動しない**。`templates` に旧スキーマの `"kind":"power"` が 9 件
  残っており（ISS-00224）、本機構が `9 validation errors` として検出する。
  **元から不正だった定義の可視化であり退行ではない**（従来は黙って無視され `templates`
  から欠落していた）。修正は TRIP62 の jsonc 全体見直しと併せて行う。
  なお `sample_target/TRIP62/` は `.gitignore` 対象のため本リポジトリには含まれない。

---

## [2.0.0.a10] 2026-08-12

`tmax_low` の決め方を「プロセスの出力遷移幅に対して十分細かいか」という判定基準に改め、
a09 で 4 PDK 一律 `0.002` にしたうちの gf180 / OSU035 / TRIP62 を **`0.02` へ戻した**。

※ TAG `2.0.0.a07` / `a08` / `a09` は CHANGELOG の更新が漏れていた（`pyproject.toml` は
   追随済み）。本版の作業時に気付いたため、**下記に各版のエントリを追記**した。

### 変更

- **`tmax_low` を gf180 / OSU035 / TRIP62 で `0.002` → `0.02`**（ISS-00223）。
  a09 の一律 `0.002` は SKY130 の実測を根拠にしたものだったが、gf180 で検証した結果
  **逆効果**と判明した（`run_gf_low002` 827 秒 vs `0.02` の 524 秒＝ +58%、
  transition 84 点中 **78 点が「減る」方向**へ動き、元から orig より鋭い charao の
  transition が **orig からさらに離れた**。例：`dffrnq_1` rise_transition (0.02, 0.001) は
  0.0704 → 0.0646 に対し orig 0.1158 ＝ 差 −0.0454 → −0.0512）。
  **sky130 は `0.002` のまま**（`tmax_low_power_tin` 0.02 も維持）。
- **判定基準を 4 PDK の `config_lib.jsonc` にコメントで明記**した。

  ```
               出力遷移    tmax_low=0.02 での点数   0.002 の効果        コスト
  sky130       17〜25 ps    約 1 点（測れていない）   誤差 18% 除去→必要  +64%
  gf180        70〜96 ps    約 4 点（足りている）     orig から遠ざかる→不要 +58%
  ```

  **遷移あたり 4 点以上**を目安とする。遷移幅は露払いを 1 回回せば `.lib` から読めるため、
  新 PDK でも同じ手順で判定できる。速度が要るときは `tmax_low` を粗くするのではなく
  ISS-00220（const の初期化やり直しを `nodeset` ＋時間軸シフトで約 2.1 倍速）で稼ぐ。

### 注意

- OSU035 / TRIP62 の `0.02` は**実測ではなく推論**（a07 以前の値＝`simulation_timestep_min`
  0.001 × 20 と等価で、OSU035 はこの値で ISS-00141 が 0 failures 完走している実績値。
  0.35um は gf180 より遅いプロセスのため遷移幅は広い側に倒れる）。実測での裏取りは
  ISS-00223 の露払いで行う。
- TRIP62 の `config_lib.jsonc` は `.gitignore` 対象（非公開セル）のためコミットに含まれない。
  同ファイルには旧スキーマの `"kind":"power"` が 9 件残っており、**そのままでは pydantic で
  弾かれる**（ISS-00224。ISS-00223 の TRIP62 露払いの前提条件）。

---

## [2.0.0.a09] 2026-08-12

透過ラッチの setup 判定を `judge_dly` へ切り替え、両 PDK で「張り付き」を解消した。

※ CHANGELOG の記載が漏れていたため a10 の作業時に追記した。

### 修正

- **LAT の setup を `judge_dly` 判定へ切替**（ISS-00221）。透過ラッチは enable が開いている間
  D→Q が素通りするため、`prop_clk_out`（enable→Q）は**掃引量そのもの＝幾何量**で判定に
  使えなかった。`is_lat` のとき `judge_dly` を見るよう `charao_run.py`（1299 / 1559 行）を
  修正し、`genFileLogic_Const1x` の `res_list` に `judge_dly` / `trans_out` を追加。
  `dlxtp_1` で **1.1700 → 0.3570** となり、探索が「平坦 → 劣化 → 収束」の正しい形に戻った。
  `prop_clk_out` 固定は 2026-06-26（`7e15e90`、ISS-00135 再編）に入り以降未変更で、
  ISS-00143 で LAT を統一パスへ移した際も **jp2 側だけが吸収され Python の判定側は
  そのまま**だった（`judge_dly` は measure として存在したが誰も読んでいなかった）。

### 変更

- **`simulation_points_per_transition = 2.0` を 4 PDK すべてに設定**（ISS-00223）。
- **`tmax_low` を 4 PDK すべて `0.002` に統一**（→ a10 で gf180 / OSU035 / TRIP62 は差し戻し）。
- **dead code を削除**。`runSpiceSetupMultiThread` / `runSpiceSetupSingle` は dispatch から
  呼ばれず参照は自分自身とコメントのみで、**ここに実装されていた probe は一度も実行されて
  いなかった**。`charao_run.py` の 1106〜1333 行 **228 行を削除**（2803 → 2575 行）。

### 確認

- 露払い（5 セル × 全 measure × index1/2 先頭 2 点）＝ gf180 `run_a08_gf3` **524 秒 /
  0 failures**、sky130 `run_a08_sky2` **1254 秒 / 0 failures**。
- orig 突合は **index / when ごとに 1 点ずつ**（orig 側 NLDM 補間、集約値は使わない）。
  const 各 112 点・delay/transition 各 168 点、orig 未対応 0 点。
  **`1.1700` / `0.9210` への張り付き 0 件・`0.0000` 0 件・orig と符号が逆の点 0 件**。
  `dlxtp_1` setup fall は **1.1700 → 0.0317**（orig 0.0374、差 −0.0057）。
- **ISS-00075(b) に退行なし**。旧 `run_seq_full` と `run_a08_gf3` を全 36 点比較して
  **差 ≤ 0.001 ns**＝本版の変更は delay に影響していない。

---

## [2.0.0.a08] 2026-08-11

`.tran` の刻みを `maxstep` へ一本化し、出力遷移にサンプルが乗らない問題を解消した。

※ CHANGELOG の記載が漏れていたため a10 の作業時に追記した。

### 修正

- **出力遷移にサンプルが 1 点も乗っていなかった**（ISS-00219）。`trans_out` 18 ps に対し
  `maxstep` 297 ps で、波形上 Q の立ち下がりが `1.80V → 0.30V` と 2 サンプルで終わっていた。
  その結果 `prop_clk_out` が ±70 ps ばらつき、**閾値 50 ps を誤って超えて探索が 2 点目で
  打ち切られる**（`dfxtp_1` setup で orig 0.4036 に対し **5.4100**）。recovery の 7×7 行列が
  16 表中 88% で非単調になっていたのも同一原因。

### 変更

- **`tstep` を廃し `maxstep` に一本化**。ngspice の `.tran tstep tstop <tstart <tmax>>` は
  **`tstep` が printing increment で解析に一切関与しない**（`tmax` 明示時）ことをマニュアルで
  確認したため。`maxstep = max(tmax_low, min(slew × 0.198, tmax_high))` へ書き換え、
  jsonc のキーも `simulation_timestep_max` / `_min` → **`tmax_high` / `tmax_low`** に改名した
  （旧値の 20 倍が等価）。**設定値が実際の値と一致**するようになった。
- **`simulation_points_per_transition` を追加**。出力遷移 `trans_out` に何点のサンプルを
  乗せるかを指定し、**掃引位置を固定したまま** `maxstep` を反復収束させる（位置と同時に
  動かすと変化の由来が分離できない）。297 → 49.5 → 8.3 → 5.1 → 3.89 ps と単調に収束する。
  `0.0`（既定）で完全に従来動作。適用は `trans_out` を読める **delay / mpw / const / setup**
  の 4 measure。

### 確認

- `dfxtp_1` setup fall (1.5, 1.5) が **5.0064 → 0.0474 ns（1/106）**。
  `buf_16` rise_transition (5, 0.0005) が **+0.1787 → +0.0013（1/137）**、
  fall_transition が +0.0774 → −0.0020（1/39）。
  **十分細かい点は 1 ビットも変わらない**（`buf_16` 294 点中 176 点が無変化）。
- コストは **const 1.13 倍 / delay 1.05 倍**。

---

## [2.0.0.a07] 2026-08-10

ICG（クロックゲート）の const 判定で、観測点の決定を Python 側へ一本化した。

※ CHANGELOG の記載が漏れていたため a10 の作業時に追記した。

### 修正

- **ICG の setup / hold は内部ラッチ出力で測る**（ISS-00218）。`GCLK = CLK AND QD` のため、
  **捕捉の成否が確定する場所（内部ラッチ出力）と出力の間に enable ゲートが挟まる**。
  出力で見ると `VIN→VOUT` は「E と CLK の幾何的な時間差」になり劣化を測れない
  （gf180 `icgtp_1` setup_rising は内部ノード版 +0.92 に対し VOUT 版 −5.07、orig −0.183）。
- **sky130 `sdlclkp_1/2/4` に `vout_infos` を追加**（gf180 だけが持っていた）。
  **内部ノード名はサイズごとに違う**（`_1` = `a_464_315#`、`_2`/`_4` = `a_465_315#`）ため
  netlist で実物を確認して記述した。

### 変更

- **観測点の決定を Python 側へ一本化**（リファクタ、計測結果は不変）。`myTbParam` に
  **`vout_path`**（判定に使わない measure ＝常に VOUT）と **`vout_judge_path`**
  （const 判定チェーン＝`judge_dly` / `judge_vlt_max`・`min` / `prop_clk_out` /
  `prop_in_out`）を新設し、jp2 は変数を書き出すだけにした（**jinja から条件式を全廃**、
  ベタ書きの `VOUT` も一掃）。旧実装は `setup_kind`（本来は MEASURE ブロック選択用）を
  置換ガードに流用しており、**各ブロック内では常に真＝ガードとして無効**だった。
- **EN 制御セルの識別子 `is_gated` を mylogic に新設**。`logic_type` は LATCH も ICG も
  `seq_lat` で区別できないため、`ICG_PC` / `ICG_NC` に `"is_gated":True` を追加し、
  置換条件を「`vout_infos` があれば無条件」→「**`is_gated` かつ const 系**」に明確化した。

### 確認

- sky130 `sdlclkp` 3 セル・full grid・orig の index グリッド上で NLDM 補間した共通 108 点
  （単位 ns、判定は絶対差）：**setup fall の最大 \|差\| が 4.10 → 1.14**、
  **hold fall は旧「全点 0.0000（判定不成立）」→ 新 −0.284 で orig −0.265 とほぼ一致**。
  setup rise は最大 2.38 → 0.82。hold rise は完全に不変（この arc は内部ノードと出力で
  同じ判定になる）。サイズ依存なし。
- **他セルへの無影響を .sp 差分で実証**（フル回帰は不要と判断）。`icgtp_1` の生成 .sp が
  **132 点すべて完全一致**（差分はリモート実行の一時ディレクトリ UUID のみ）。
  `vout_infos` を持つのは ICG だけなので、他セルは変数が `"VOUT"` に解決され文字列同一。
- **修正が要る ICG は残っていない**。mylogic を機械走査した結果、出力がゲートで隠れる
  logic は `ICG_PC` / `ICG_NC` の 2 つだけで、これを使う登録済みセルは全 PDK で 9 セル
  （gf180 `icgtp`/`icgtn` 各 3、sky130 `sdlclkp` 3）＝すべて設定済み。

---

## [2.0.0.a06] 2026-08-09

SKY130 の template を `util_make_template4json.py` で作り直した。

### 変更

- `sample_target/sky130/fd/sc_hd/` : `3.scan` -> sim/`4.analyze` -> `5.build` を通して
  template を更新した。プリレイアウト netlist で 181 セル・全巡回 0 failures、
  **3 巡（43 -> 153 -> 173/173）で収束**。グループ数 24（許容 5.0%）、
  `config_lib.jsonc` の template は 53 で従来と同数だが、**`template_kgn` は
  std_comb 62 セル・std_seq 8 セルで割り当てが変わった**。
  `5.build` を最後に通したのが 2026-08-02 で、ISS-00199（`max_cap` を最悪 arc で決める）の
  修正が `4.analyze` までしか反映されていなかったため。本版で初めて完全に行き渡る。

### 確認

- 露払い（181 セル × 2x2 corner × **全 measure**）で **0 failures / 0 traceback /
  .lib 181 セル**。`cell_rise` 1215・`rise_power` 3314・`rise_constraint` 120・
  `cell_leakage_power` 182 等、全 measure の出力を確認した。
  ISS-00188 の副作用（`power_tin` が `index_1[0]` で落ちる）の再発も無し。

---

## [2.0.0.a05] 2026-08-09

kpex（KLayout-PEX）による寄生抽出を charao へ取り込む一連のフローを追加した。
ISS-00201（駆動サイズ依存の系統差）の主因が **セル内配線抵抗が sim に入っていなかったこと**
であると特定し、`inv_16` の cell_rise 比が 0.825 → 0.929 まで改善することを確認した。

### 追加

- `tools/gds2pex.py` : GDS から複数セルを一括で PEX 抽出する（1 セルずつ lrPymRPC を呼ぶと
  38 秒/セルのところ 10 セル 23 秒）。`--patch_unnamed_nets` で上流 pip 版（0.3.12）の
  「内部ネットの抵抗が出ない」バグを実行時に回避する（ISS-00207。上流 main では 50a0549b で修正済み）
- `tools/pex2spice.py` : kpex 出力を charao が読める SPICE へ変換する。ポート名・順序の是正、
  M→X 変換、W/L/AS/AD/PS/PD の scale 換算、0Ω の扱い（`--zero_mode`）、デバイス端子の
  メッシュ再接続（`--reconnect`＝ISS-00205）、容量の再接続（ISS-00214）、LOD の付与
  （`--lod`＝ISS-00206）、浮きノード検査
- `charao` : `--spice_path` を追加。cell netlist のルートを CLI で差し替える。**ファイル名は
  変えない**ため target ツリーの複製と sed が不要になる（ISS-00205）
- `debug_run.sh` : `SPICE_PATH` env
- `docs/HOWTO_kpex.md` : 抽出から受け渡しまでの手順、上流の制限、踏んだ落とし穴

### 注意

kpex 側に未解決の制約がある（ISS-00208 の LVS 等価性、ISS-00210 のメッシュ粒度、
ISS-00212 の `xor3_4`、ISS-00213 の `dfxtp_4` に 128GΩ）。**単段セルでは実用できるが、
多段・順序セルは要検証**。

---

## [2.0.0.a04] 2026-08-05

実測から templates を決める `util_make_templates.py` を追加し、SKY130 をその出力へ移行した。
あわせて `.tran` の TSTEP 下限に起因する sim 失敗（ISS-00188）を measure 別の分離で解決した。

※ TAG `2.0.0.a03`（`変更：templates の index を有効 3 桁で生成する`）は
   `pyproject.toml` / CHANGELOG の更新が漏れていたため、本エントリでまとめて記載する。

### Added

- **`charao/script/util_make_templates.py`**（ISS-00189）。実測から `config_lib.jsonc` の
  `templates` を決める。**orig `.lib` が無い PDK でも使える**。
  `1.probe` / `2.report` / `3.scan` / `4.analyze` / `5.build` の 5 stage 構成。
  仕様は `docs/SPEC_make_templates.md`。
- **`simulation_timestep_min_power_tin`**（ISS-00188）。`power_tin` だけ `.tran` の
  TSTEP 下限を分ける。**未指定なら `simulation_timestep_min` にフォールバック**するため、
  既存 target（gf180 / OSU035）の挙動は変わらない。

### Changed

- **`templates` の index を有効 3 桁で生成する**（TAG `2.0.0.a03` 相当）。
  index は計算で作った値なので下位桁に意味がなく、丸めによるズレは 0.5% 以下。
- **SKY130 の `templates` を実測ベースへ移行**。旧 67 グループ（orig の index 由来）から
  **24 グループ**へ。`max_cap` はセル・出力ピンごとに反復で収束させた実測値
  （0.0371〜3.81 pF）。
- **`util_make_templates_from_origin.py`** の再生成対象 kind に `power_tout` / `power_tin`
  を追加し、index を有効 3 桁へ丸める `_sig3()` を適用。グリッド点数を引数化。
- 中間の target ツリーを **`tmp_` 前置**に改名（`tmp_1.probe_target` /
  `tmp_3.scan_target` / `tmp_5.build_target`）。`.gitignore` の `tmp_*` で除外する。

### Fixed

- **`power_tout` の `energy2` が `Timestep too small ... vrel#branch` で落ちる**（ISS-00188）。
  真因は `timestep_tstep = max(simulation_timestep_min, min(slope × 0.0099,
  simulation_timestep_max))` の**下限に張り付いていた**こと。SKY130 の `index_1` 下 3 点
  （0.01 / 0.0231 / 0.0531 ns）では slew エッジを 10 / 23 / 53 点しか刻めていなかった
  （設計意図は約 100 点）。SKY130 の `simulation_timestep_min` を **0.001 → 0.0001** とし、
  36 セル・84 格子点の欠損が全て解消した。
- **上記を一律に適用すると `power_tin` が逆に落ちる**（ISS-00188）。最速 slew 0.01ns で
  TSTEP が 0.1ps となり `Timestep too small ... vclk#branch` で **109 件失敗**（26 セル）。
  **`power_tin` だけ下限を 0.001 に分離**して解消。下限は ISS-00087（ngspice の LTE 暴走
  抑制）由来であり、**粗すぎても細かすぎても同じ `Timestep too small` になる**。
  **measure ごとに最適な下限が違う**。

### Verified

- **露払い**＝SKY130 全 181 セル × 2x2 corner × 全 measure、**0 failures / traceback 0**。
  `.lib` 181 セル・`.v` 181 module を生成。

---

## [2.0.0.a02] 2026-07-30

`2.0.0` に向けた開発版。他 PDK 対応（ISS-00141）を進め、UDP 契約を電源端子付きへ拡張した。

### Changed (breaking)

- **UDP 契約を 6 端子 → 8 端子へ拡張**（ISS-00183）。
  `(Q, C, P, CK, D, N)` → **`(Q, C, P, CK, D, N, VPWR, VGND)`**。
  パワーカット時にセルの入出力信号が影響を受けるため、電源状態を UDP の表に取り込む。
    - 表は SKY130 の `*_pp$PG$N` 版に倣い、**通常の全行で `VPWR=1` / `VGND=0` を要求**し、
      末尾に **電源変化 → `Q=x`** の 2 行を置く。論理シミュレーションでパワーカット時の
      `x` 伝播が正しく現れる。
    - `vcode` は `vdd` / `vss`（logic 側のポート名）を渡し、`ports_dict` 経由で
      **セルの実ピン名へ自動置換**される（gf180/OSU035 は `VDD`/`VSS`、SKY130 は `VPWR`/`VGND`）。
      同一 vcode が PDK ごとの電源ピン名へ展開されるため、PDK 追加時の作業は不要。
    - **既存の `std_primitives.v` は 8 端子へ更新が必要**（gf180 はバックポート済み）。
    - `.lib` 側の多電源対応（`KAPWR` のような第 2 電源、`is_isolation_cell`、`level_shifter`）は
      別課題として分離（ISS-00182）。

### Added

- **`tools/gen_udp.py`**（ISS-00176）: 実回路(SPICE)の挙動を測って UDP を生成・検証するツール。
  契約端子が固定なのでテストベンチは 1 本で足り、セル依存部は「インスタンス行」と「端子の極性」だけ。
  取り込みエッジ／clear・preset 単独／**同時アサート時の優先度**／保持を測定し、
  対応する正準表を出力する。ローカル simulator が PDK モデルに未対応の場合は
  `--tb-only` で TB のみ生成し、`--lis` でリモート実行の結果を読み込める。
- **`docs/SPEC_primitives.md`** に 2 節を追加。
    - **§5 配線規約**: 優先度と極性は「表」ではなく「配線」で作る。優先させたい信号を `P` へ渡し、
      出力を `IQ1` で受けてその反転を `Q` に出す（gf180 純正 `dffrsnq_func` と charao の vcode は同型）。
    - **§6 `gen_udp.py`** の使用方法と機能。
- **OSU035 target の V02.00 対応**（ISS-00177）: `std_primitives.v` 新規、`config_lib.jsonc` の
  templates を 7x7 で再定義（`Cin=0.0045pF`、slew 0.05〜8.0ns）、`template_kgn` を現行スキーマへ
  更新（`power` は無効 kind のため `power_tout` / `power_tin` へ）、旧パス体系（`sample/target`,
  `sample/src`）の是正。

### Changed

- **`debug_run.sh` の PDK パラメータを env 化**: `FAB` / `VENDOR` / `REV` / `GROUP` / `UV` /
  `CORNER` / `TEMP` / `VDD` / `CELL_PREFIX` / `MATCH`。`LIB_FILE` は `update_name()` と同じ規則で
  自動導出する。**gf180 の既定値は従来と完全に一致**（後方互換）。
- `--SOURCE_INCLUDE` に **`.spi`** を追加。gf180 は `.spice` のため露見しなかったが、
  `--SOURCE_INCLUDE` はパスの後方一致判定なので `.sp` では `.spi` に当たらず、
  OSU035 のセル netlist が転送されていなかった。

### Fixed

- `docs/SPEC_primitives.md` §3 の注記: 1.0.0 以前の `mylogic_seq_ff.py` のコメント
  「`n` = C (clear) dominates over P (preset)」は誤り。正しくは「`n` は C/P 同時 assert を
  未定義（x）とする」。

### Verified

- OSU035（`sample_target/OSU035/VENDOR/CB_REV2`）で **charao が完走**（0 failures）。
  `.lib` / `.md` / `.v` / `_primitives.v` の 4 点を生成＝**gf180 以外の PDK で初めて**。
- 生成 .v の UDP インスタンスが 8 端子で出力され（`udp_iq_ff_hn inst (…, notifier, VDD, VSS)`）、
  参照 UDP が定義に含まれ未定義参照ゼロ。`_primitives.v` は入力と diff ゼロ。

---

## [2.0.0.a01] 2026-07-28

`2.0.0` に向けた開発版（alpha）。**非互換変更を含む**ため major を上げる。

本バージョンから TAG 命名を **`x.y.z`（リリース）／ `x.y.z.aNN`（開発中）** とし、
x = 入力・出力仕様の非互換変更 / y = 機能追加（出力が増える）/ z = 修正（値が変わる）と定義した。

### Changed (breaking)

- **Verilog primitive を charao 本体から target 側へ移設**（ISS-00172）。
  従来は `mylogic_*.py` の `get_code_primitive()` が UDP を Python ソースに埋め込み、
  本体 `.v` の `` `ifndef SYNTHESIS `` ブロックへ出力していた。以下に変更する。
    - **入力**: `<target>/<vendor>/<rev>/std_primitives.v` を読む。
      **このファイルが無いと primitive は出力されない**（`[INF]` を表示してスキップ、実行は継続）。
      既存 target には配置が必要。
    - **出力**: `<result_path>/<lib_basename>_primitives.v` として**加工せずそのまま**出力する
      （`cell_group=std` のみ、build stamp は付けない）。**本体 `.v` からは primitive が消える**ため、
      シミュレータには 2 ファイルを渡すこと。論理合成へ渡すのは本体 `.v` のみ。
    - **API 廃止**: `mylogic_*.py` および `mylogic_user.py` の `get_code_primitive()` を削除した。
      user 定義による primitive 上書き経路も廃止。
    - 理由: (1) GF180 由来の UDP は Apache-2.0 であり、GPL-2.0-or-later の charao ソースへの
      埋め込みを解消する。(2) PDK ごとに UDP を差し替え可能にする。
    - 契約（4 UDP の名前・ポート順・意味論）は `docs/SPEC_primitives.md` に明文化した。

### Removed

- **dead primitive の削除**（ISS-00173）。
    - `lr_mux`: 定義され生成 `.v` にも出力されていたが、インスタンス化箇所はゼロだった
      （MUX2/MUX4 は `functions` の assign 文で出力されるため primitive を使わない）。
    - `lr_dff`: `myExportLib.py` が `lr_dff(...)` を出力していたが、**定義がどこにも存在しなかった**。
      到達条件は「vcode を持たない flop」で現行セルは全て vcode 持ちのため dead path だったが、
      未定義 primitive を参照する `.v` が生成されうる状態だった。該当分岐は ERR に変更した。

### Added

- `docs/SPEC_primitives.md`: `std_primitives.v` の入出力仕様、charao が要求する 4 UDP の
  インタフェース契約（`udp_iq_ff_n` / `udp_iq_ff_hn` / `udp_iq_latch_n` / `udp_iq_latch_hn`、
  ポート順 `(Q, C, P, CK, D, N)`）、`n` と `hn` の違い、他 PDK への移植手順。
- `sample_target/gf180/fd/mcuC7t20240817/std_primitives.v`: GF180 の UDP 4 種
  （open_pdks gf180mcu 由来、charao 命名へ改名。Apache-2.0 §4(b) の改変告知を付記）。
- `sample_target/gf180/LICENSE-Apache-2.0.txt`: Apache License 2.0 条文。
- `README.md` に License 節を追加（charao 本体＝GPL-2.0-or-later、`std_primitives.v`＝Apache-2.0）。

### Fixed

- **`n` / `hn` UDP の説明の誤記**を訂正。従来 `mylogic_seq_ff.py` のコメントは
  「`n` = C (clear) dominates over P (preset)」としていたが、実際の table は
  **C/P 同時 assert を未定義（Q=x）とする**。`hn` のみ P に優先度を与える。

### Changed

- `debug_run.sh`: `--SOURCE_INCLUDE` に `std_primitives.v` を追加（local / pip 両モード）。
  lrPymRPC の `--SOURCE_INCLUDE` はパスの**後方一致**判定のため、拡張子ではなくファイル名を指定する。
  `.v` を指定すると PDK 同梱の `*.v`（約 2 MB）まで転送対象になるため、この形にした。

### Verified

- seq_ff 24 セル × 2x2 corner × 全 measure（lrPymRPC 経由）: **0 failures**。
- 生成物: `_primitives.v` が入力と **diff ゼロ**、本体 `.v` に primitive 定義なし、
  本体 `.v` が参照する UDP がすべて `_primitives.v` に定義済み（未定義参照ゼロ）。
- `.lib` / `.md` / 本体 `.v` は変更前の run と **build date 行以外すべて同一**（回帰なし）。

---

## [1.0.0] 2026-07-27

`0.9.14`（main）からの正式リリース。`feature/1.0.0` 上の alpha a01〜a33 を統合し、GF180（`gf180mcu_fd_sc_mcu7t5v0`）の **全 229 セル**を full grid × 全 measure で特性化して Liberty / Verilog / Markdown を生成できる状態に到達した。

### Added

- **対象セルの完全網羅（229 セル）**: comb 161（基本 98・複合 48・三相態 15）＋ seq 54（dff 24・sdff 12・lat 12・icg 6、`_1`/`_2`/`_4` の全ドライブ）＋ physical 14。orig 標準ライブラリの全セルと 1:1（a31 ISS-00158／a33 ISS-00165）。
- **三相態・bus keeper 対応**（a03/a04、ISS-00066/00069/00073）: BUFZ/INVZ 14 セル＋HOLD。`three_state_enable`/`three_state_disable` アークと `oe_infos`・`sim_pullres`・`delay_disable` 1D template。
- **順序回路の全 family**: DFF 8 family（a06〜a23、ISS-00070）／SDFF 4 family（a14/a25、ISS-00086）／LAT 4 family（a16/a26、ISS-00090/00143）／**ICG 2 family**（a27、latch+AND / latch+OR）。
- **物理セル（fill/fillcap/endcap/filltie）14 種**（a33、ISS-00165）: timing アークを持たない measure-less 方式。`mylogic_physical.py`＋`std_physical.jsonc`＋専用ループ。
- **`--mylogic_only`（ISS-00169）**: mylogic モジュール単位で対象セルを選択（`comb_base` 等の短縮名指定、`mylogic_<name>.py` は charao 内で補完・存在確認）。`--cells_only` と AND。分割実行時の引数長制約を回避する。
- **`vout_infos` 機構**（a27、ISS-00152）: const 計測の観測点をセル固有の内部 net に差し替える汎用機構（ICG の Q=CLK&IQ2 を内部ラッチ出力 QD で観測）。
- **出力 port 別 template**（a29、ISS-00150）: `template_kgn` の第 4 要素で出力ピン別の load 軸を割当（adder 系の index 逸脱を解消）。
- **min_pulse_width の slew-index テーブル化**（a31、ISS-00160）: template システムに統合し Liberty `timing()` constraint として出力。
- **`leakage_offset` / `leakage_stable_time`**（a33、ISS-00165/00166）: leakage の一律加算値と op 前段 tran の静定時間（ともに config 側で tunable）。
- **波形取得と閲覧**（a08、ISS-00078）: `--wave_raw`（sim ごとの `sim.sp.raw`＋`.pinmap.json`）と、オフライン 1 ファイル完結の `tools/raw_viewer.html`。
- **`util_merge.py`**（a17、ISS-00096）: セル別 `.lib`/`.v`/`.md` を 1 ファイルへ統合。
- **`.md` の full-index 化**（a30）: DELAY / THREE_STATE / CONSTRAINTS を 10×10 全格子で出力（pandoc で PDF / HTML 化可）。
- **SPEC ドキュメント群**: `SPEC_measure` / `SPEC_const` / `SPEC_internal_power` / `SPEC_pin_oirc` / `SPEC_seq_lat` / `SPEC_specify` / `SPEC_three_state` / `SPEC_config_lib`。
- **`debug_run.sh` の運用強化**: `RESULT_ITEMS` / `SOURCE_ITEMS` / `MYLOGIC` / `RUN_NAME` / `DEBUG_STOP` / `WAVE_RAW` env。

### Changed

- **mylogic を 8 モジュールに分割**（ISS-00064 系）: comb_base / comb_complex / comb_tristate / seq_ff / seq_scan / seq_lat / io / physical を `charao.py` で merge（logic 名重複は ERR）。
- **internal_power を power_tout / power_tin に分離**（ISS-00065）: 出力ピンの active アークと入力ピンの出力不変 state を別計測。
- **刺激ピン基準への統一**（a24/a30、ISS-00142/00155）: 積分窓・slew 割当・cin 選択を「遷移するピンを駆動するスロット」に anchoring（power_tout=related／power_tin=target）。入力 slew 依存性を初再現。
- **const 計測の統一パス化**（a26〜a28、ISS-00138/00143/00153）: setup/hold/recovery/removal を単一経路へ集約し、判定方式を出力挙動の型で選択（**遷移型**＝FF の degradation 判定／**保持型**＝LAT・ICG の電圧化け判定）。
- **出力 transition に `slew_derate_from_library` を適用**（a31、ISS-00157）: Liberty 規約どおり格納値＝実測 30-70% ÷ derate。
- **seq/lat/icg の leakage を tran → DC(op) 化**（a33、ISS-00166）＋ **`pleak = min(p_supply, p_absorb)`**（ISS-00167）: μs 級時定数の保持ノード未静定と入力駆動電流の混入を排除。
- **`min_pulse_width_high/low` の scalar 属性を撤去**（a31）: Liberty 仕様上 `timing()` constraint が authoritative。
- **`util_merge` を順次上書き更新方式に変更（ISS-00171）**: 引数を `--out_dir <dir> <in_dir>...` とし、**先頭ディレクトリをベースに以降を順次適用**（同名セルは上書き・未登場は追加）。マージは同じファイル名同士で行うため PVT 別ファイル名も扱える。1 セルだけ再 sim した結果を既存 rslt へ差し戻せる。

### Fixed

- ngspice timestep collapse（a22、ISS-00117）: 最終 DC 点の理想電圧源枝電流による行列特異を、テール限定の SW 制御抵抗で解消。
- 入力 slew の切替スロット取り違えと ramp 換算の 2× 過大（a30、ISS-00155）。
- `is_lat` 判定の取得方法誤り（a28、ISS-00153）: `logic_dict` 辞書引きへ修正し、LAT/ICG の judge 分岐が初めて有効化。
- LAT const dispatch の未定義関数呼び出し（a26、ISS-00143）。
- latch min_pulse の precondition 取り違えによる 1 秒 transient ハング（a31、ISS-00159）。
- `.v` specify の Verilog 準拠化（a32、ISS-00147）: timing check の `&&&` 条件化・`reg notifier` と primitive N ポート接続・ifnone×edge の `ifdef` 切替。全 215 モジュールで iverilog EXIT=0。
- sim 時間の最適化（a05、ISS-00076）: WOUT pre-charge SW 導入で BUFZ_1 full INDEX が 1h51m → 4m20s（約 25 倍）。
- pre-charge と `tdelay_rel` の協調（a13、ISS-00089）: `sim_prop_max` を `sim_d2c_max` へ統一し sim 時間半減。
- **antenna セルの leakage が負値（ISS-00170）**: `pleak = min(p_supply, p_absorb)` が、電源間経路を持たない antenna（ダイオード 2 個のみ）で **入力ピン駆動電流の帰り道になった電源枝の負値**を拾っていた（−0.179 µW vs orig 7.5e−05。旧 `max()` でも +0.18＝約 2,400 倍で誤り）。`p_supply`/`p_absorb` を 0.0 でクランプしてから `min` を取る形に修正し、antenna は `leakage_offset` のみの 5e−05 に。全 229 セルで leakage 負値ゼロ、timing/power の統計は不変。

### Verified

- **真打ち（全 229 セル × full grid × 全 measure、mylogic モジュール別 7 バッチ、2026-07-26〜27、17h10m）**: **全バッチ 0 failures・timestep collapse 0**。`.lib` 229 cell / `.v` 229 / `.md` 229（全ユニーク）。統合 orig 比較（NLDM 補間＋`--keep_zero_new`、661,020 点／有効 635,806 点／212 セル＝対象外 17 は physical 14 と antenna/tieh/tiel）: cell_rise median **−0.171**（p95 0.484）／cell_fall **−0.114**（0.493）／rise_transition **−0.145**（0.328、a30 の −0.805 から改善＝ISS-00157）／fall_transition **−0.054**（0.118）／rise_power **−0.033**（0.878）／fall_power **−0.112**（0.487）／rise_constraint **−0.097**（0.616）／fall_constraint **−0.099**（0.559）。matched groups 12,580 は a32 と同一（when 分解カバレッジ不変＝ISS-00140/00149）。上位外れは `inv_20`/`clkinv_20` の rise_power @slew 3〜4（orig 16.67→charao 13.90＝−16%）で ISS-00155 の既知残差。
- **leakage（全 229 セル）**: **負値 0 件・貫通（ratio>3）0 件**、ratio median **1.002**（min 0.667 / max 1.255）。カテゴリ別 median＝comb 1.002／seq_ff 0.825／seq_scan 0.748／seq_lat 1.002／icg 0.816（残る 0.72〜0.83x は ISS-00168）。
- **露払い（全 229 セル × 2x2 corner × 全 measure、2026-07-26、1h33m）**: 0 failures・collapse 0。

### Known issues（post-1.0.0）

| ISS | 優先度 | 概要 |
|---|---|---|
| ISS-00140 | HIGH | delay/transition の when 状態分解未実装（orig の状態別 when に対応する arc を持たない） |
| ISS-00149 | MEDIUM | async 遷移の出力 internal_power 未計測＋入力 power の when 分解不足 |
| ISS-00086B | MEDIUM | SDFF の SE/SI 別 when 計測（delay/power の orig 照合が不成立） |
| ISS-00082 | MEDIUM | min_pulse / minimum_period の state 別 sim（FF/SCAN） |
| ISS-00154 | MEDIUM | power_tout の帰属分解方式（1.0.0 は総量計上で確定） |
| ISS-00141 | MEDIUM | OSU035 / TRIP62 での回帰未実施（GF180 外 PDK） |
| ISS-00155 残 | MEDIUM | 低 slew の comb rise_power 過小・高 slew の seq Q power 過大 |
| ISS-00168 | LOW | seq/lat/icg leakage の一律 0.72〜0.89x 系統オフセット |
| ISS-00075 残 | LOW | seq CLK→Q delay の −0.3〜0.5ns 系統オフセット |
| ISS-00145 | LOW | and2_1 pin(A1) power_tin の near-zero（when 分解ファミリーと同根） |
| ISS-00079 | LOW | num_thread の多スレッド劣化（暫定運用 `num_thread=4`） |

---

## [0.9.14a33] 2026-07-25

Alpha pre-release. 物理セル leakage 対応（ISS-00165）＋ seq/lat/icg leakage の DC(op) 化（ISS-00166）＋ set/reset ラッチ貫通の pleak=min 修正（ISS-00167）。全 229 セル leakage 回帰で貫通全滅・orig オーダー収束。

### Added
- **物理セル（fill/fillcap/endcap/filltie）14 種の leakage 対応（ISS-00165）**: orig 229 セルに対し charao は 215 セルだった差分 14（timing arc なし・leakage/area/pg_pin のみ）を追加し network を完全化。空 subckt（Tr 0）で sim 特性化できないため **measure-less 方式**：新規 `mylogic_physical.py`（logic_type "physical"）＋ `std_physical.jsonc`（14 セル、専用ループを `charao.py` に追加）。leakage は `leakage_offset` の一律加算で付与。
- **`leakage_offset`（leakage 嵩上げ値、ISS-00165）**: orig−charao が駆動 1x〜20x の全域で 4.90〜5.00e-05 一定＝clamp でなく全セルへの一律加算と実測判明。`myLibrarySetting.py` にフィールド追加（default 0.0）、gf180 config で 5e-05。orig と 0.02% 以内で一致。
- **`leakage_stable_time`（leakage op 前段 tran の絶対時間、ISS-00166）**: nodeset に渡す内部ノード電圧の静定用（tunable、default 1.0=1ns）。gf180 は 1ns で 10ns/40ns と同結果のため 1。
- **`SPEC_config_lib.md`**: config_lib.jsonc の leakage 系パラメータ仕様を記載。

### Fixed
- **seq/lat/icg leakage の tran→DC(op) 化（ISS-00166）**: 全 229 セル回帰で seq 54＋clkbuf が orig の 5〜640 倍過大（icgtn 640x／lat 200x／dff 5〜17x）と判明。原因＝内部保持ノード（クロスカップル feedback）の平衡時定数が μs 級で 10ns 窓では未静定、電流に変位電流（真 DC の 24〜46 倍）混入。**B案**（run→meas find→alterparam→reset→alter→op：tran 終端の全内部ノード電圧を nodeset に書き戻して op）で真の DC 動作点を取得。内部ノード名は netlist から自動取得（`myLogicCell.get_internal_nodes()`）。`temp_testbench.sp.jp2` の control ブロック一本化・`.MEASURE i_*_leak` 無効化。
- **set/reset ラッチ貫通の pleak=min 修正（ISS-00167）**: latrnq/latsnq/latrsnq の leakage op が貫通（72〜81x）。真因＝`pleak = max(p_supply, p_absorb)` が**入力ピン経由の駆動電流**（set active & D 競合時に片側電源のみに出る貫通）を拾っていた。**`pleak = min(p_supply, p_absorb)`** に修正（入力駆動は片側のみ、真リークは両側均等＝min で両方向の貫通を除去し真リークを保存）。あわせて LATCH_PE_NR/NS/NR_NS の leakage ival[c] を正規化（hold=pulse・active=static、`mylogic_seq_lat.py`）。

### Verified
- **全 229 セル leakage 回帰（0 failures、`pleak=min`／`leakage_stable_time=1`／`leakage_offset=5e-05`）**: 貫通ゼロ。comb 158=1.00x（実質不変）／seq(dff) 36=0.81x／lat 12=0.89x／icg 6=0.77x／physical 17=1.00x。全カテゴリ orig オーダー（0.72〜1.23x）に収束。seq/lat/icg の残る一律 0.72〜0.89x 系統オフセットは貫通と別種＝ISS-00168 に分離（post-1.0.0 検討事案）。

---

## [0.9.14a32] 2026-07-18

Alpha pre-release. `.v` specify を Verilog 準拠に修正（ISS-00147）。timing check 条件の `&&&` 化・`reg notifier` 宣言と primitive N ポート接続・ifnone×edge-sensitive の `ifdef 切替。

### Fixed
- **.v specify の Verilog 準拠化（ISS-00147）**: 全 54 seq セルの `specify` に 3 欠陥があり修正。①**timing check の条件付け**を `if (when) $check(...)` から `$check(evt1 &&& (when), ...)`（第 1 イベント引数の `&&&`）へ変更（`$setup`/`$hold`/`$width`/`$recovery`/`$removal` への `if` 前置は Verilog 文法違反で `syntax error in specify block`。module path への `if` 前置は合法なので path/check を判別して分岐）。②**`reg notifier;` 宣言と primitive N ポート接続**を seq vcode 18 本（`mylogic_seq_ff.py` 8・`mylogic_seq_scan.py` 4・`mylogic_seq_lat.py` 6）に追加（vcode 経路は `isflop` 分岐の notifier 宣言をスキップするため vcode 内で自己完結。`udp_iq_ff_n`/`_hn`/`udp_iq_latch_n`/`_hn` の末尾 N ポートへ接続）。③**ifnone×edge-sensitive path**（iverilog 非対応）を `` `ifdef D_USE_IFNONE_SIMPLE `` で simple/edge 切替（既定=edge のまま、iverilog は `+define+D_USE_IFNONE_SIMPLE` で simple path 化）。仕様は `docs/SPEC_specify.md` §5/§6.1/§6.2 に反映。

### Verified
- 全 215 モジュールを iverilog `-g2012 -tnull` で検証、両モード（既定/`+define+D_USE_IFNONE_SIMPLE`）とも EXIT=0。specify 全文型（module path SDPD・`&&&` timing check・`$width`・edge path `+:`/`-:`・ifnone）が合法 Verilog。define 時の残 warning は specify 外の implicit wire `Z_w`（`__hold` vcode、ISS-00163 へ分離）1 件のみ。

---

## [0.9.14a31] 2026-07-17

Alpha pre-release. 出力 transition の slew_derate 適用（ISS-00157）、seq ドライブ変種 _2/_4 の網羅拡張（ISS-00158）、latch min_pulse の precondition 修正（ISS-00159）、min_pulse_width の slew-index テーブル化（ISS-00160）。

### Fixed
- **出力 transition の slew_derate 未適用（ISS-00157）**: `.lib`(set_lut)・`.md`(myExportDoc) の fall/rise_transition 格納時に `slew_derate_from_library`（gf180=0.5 → 格納値=実測×2）を適用。Liberty 規約 stored=実測(30-70%)/slew_derate に整合し、orig 比ぴったり 0.5× だった transition 系統差を解消。delay/const 等「時刻」は非対象。
- **latch min_pulse の precondition ival[c] 取り違え（ISS-00159）**: `mylogic_seq_lat.py` で LATCH_PE 系（latq/latrnq/latsnq）の min_pulse init clock 値 `ival[c]` を基準 LATCH_PE_NR_NS（latrsnq）の `"f"` に統一（init 中に E を透過させ内部状態を書き込む precondition）。出力強制のみに依存していた latsnq は高駆動（_2/_4）で内部マスタ未確立 → 解放時 Q 反転 → chg_out 失敗 → 1 秒 transient ハングしていた。latrnq low-RN の arc[i] も基準に統一。全 12 latch セルでハング根絶を実測確認。

### Added
- **seq ドライブ変種 _2/_4 の網羅拡張（ISS-00158）**: `std_seq.jsonc` に dff/sdff/lat/icg 18 ファミリ × (_2,_4) 計 36 変種を追加（cell 名・area のみ差、SPICE subckt ピン順・logic・ports_dict は _1 と同一、area は orig lib 準拠）。target 179→215 で全 STD セル（timing 対象、物理セル除く）を網羅。
- **min_pulse_width の slew-index テーブル化（ISS-00160）**: min_pulse を template システムに統合（`config_lib.jsonc` に kind=mpw/grid=3x0/index_1=[0.02,0.8,4.0] を登録、全 seq セル template_kgn に `["mpw","3x0","d000"]`）。探索を index_1 の要素数ぶん汎用ループ化し、汎用 `set_lut` ＋ Liberty timing() constraint テーブルで出力。scalar 属性 `min_pulse_width_high/low` は撤去（仕様上 timing() constraint が authoritative）。`simulation_slew_for_pulse` 廃止。背景：素の最速 slew(0.02) 固定が orig 比 -50% の主因で、slew 依存テーブル化で解消（STA が実 slew で補間）。min_period は保留。

### Verified
- 全 215 セル露払い（2x2）0 failures（transition ×2・.v/.lib/.md 整合・網羅一致）。全 seq min_pulse 露払い 0 failures（`mpw_template_3x0` header ＋ timing() constraint テーブル正常、rise/fall・when 分解、値は slew 掃引と一致）。latch min_pulse 全 12 セル pass（旧ハング解消）。

## [0.9.14a30] 2026-07-15

Alpha pre-release. 入力 slew が delay/power_tout の実切替ピンに反映されないバグ修正＋slew_derate 反映（ISS-00155）、.md の full-index 化、template 取得エラー処理、debug_run env 拡張。

### Fixed
- **入力 slew の切替スロット取り違え（ISS-00155）**: `charao_run.py` の `runSpiceDelaySingle`/`runSpicePowerToutSingle` で index1(slew) を `tslew_clk`（VCLK, slot3）に固定割当していたため、comb（切替入力=VREL, slot2）で VREL エッジが `tslew_rel` 既定 1ns 固定となり、入力 slew 依存（遅延・貫通/crowbar 電力）が未生成だった。related pin(pin_tr[1]) のスロットを pin_oirc 逆引きし `_slope_s` をそのスロットの tslew に割当（comb→tslew_rel / seq→tslew_clk、power_tin の ISS-00142 と同方式）。seq(clk→Q) は元々 clk 切替のため従来動作維持。
- **slew→ramp 換算が slew_derate_from_library を無視（ISS-00155 cal）**: `_tslew_from_template` が `slew/span` としていたため derate=0.5 で ramp が 2× 過大（過応答）。`slew*slew_derate/span` に修正（inv_20 slew4.0 の rise_power 29.1→14.2、orig 16.9 に接近）。

### Added
- **.md の DELAY/THREE_STATE/CONSTRAINTS を full index（10×10）テーブル化**（`myExportDoc.py`）: 従来の代表 1 点から index1(slew)×index2(load) の全格子を arc 別に出力。THREE_STATE の disable は 1D（load 非依存）、CONSTRAINTS は `constrained-slew × related-slew`（const は index1=constrained/index2=related、旧 rep の const/rel 逆表示バグも是正）。pandoc で A4 縦 PDF / HTML 両出力可。
- **`debug_run.sh` に `RESULT_ITEMS`/`SOURCE_ITEMS` env**: lrPymRPC の `--RESULT`/`--SOURCE` を上書き可（未指定時は従来動作）。`RESULT_ITEMS="rslt"` で work 回収を除外（full grid 大量 sim で高速化・省ディスク）。

### Changed
- **`myLogicCell.py get_template` にエラー処理**: per-port template miss 時に `[TEMPLATE-FALLBACK]`（cell-level フォールバック）、最終取得不能時に `[TEMPLATE-FAIL]`（cell/kind/oport＋keys）＋ my_exit。全 179 セル単点で TEMPLATE-FAIL=0 を確認。

### Verified
- 全 179 セル full grid 再回帰（両修正込み）: **0 failures**。統合 .lib の orig 比較（316,503 点）＝ cell_fall −0.162 / cell_rise −0.192 / const −0.05〜−0.08 / power −0.08〜−0.14（tail max|diff|≈2.7、修正前 −14.6 から激減）/ rise_transition −0.805（系統差 ISS-00075 残）。
- 全 21,425 sim.sp で slew が切替ピンに正しく適用されることを確認（delay/power_tout/power_tin/const/passive、comb/seq とも）。

## [0.9.14a29] 2026-07-11

Alpha pre-release. ISS-00150（adder per-pin template）＋docs 整合性監査（ISS-00144 含む）。

### Added
- **出力 port 別 template（ISS-00150）**: `template_kgn` に省略可能な第 4 要素（logic 出力 port 名、 例 `["delay","10x10","d023","o0"]`）を追加。 `myLogicCell.py` に `template_pin`（key="<kind>@<oport>"）と `get_template(kind, oport)`（per-pin → セル単位フォールバック）、 `charao_run.py` の delay/power_tout の template 選択を `get_template(kind, mec.pin_oirc[0])` に変更。 第 4 要素なしの既存記述は完全従来動作。
- `std_comb.jsonc`: addh_2（S=d023）/ addf_2（S=d025）/ addf_4（S=d035）に S(o0) 用 per-pin 割当（CO は現行のまま）。 orig は同一セルでも出力ピン別 load 軸（addh_2 で S/CO 間 25.7% 差、 該当は adder 3 セルのみ・全ピンに ≤5% 既存テンプレあり）。

### Changed（docs 整合性監査、 2026-07-11）
- `SPEC_const.md`: ISS-00138/00143/00152/00153 を反映（判定方式の現行表＝degradation／保持型電圧判定の選択則、 統一 const パス・sweep 範囲・seg_start clamp、 prop_clk_out が判定実体で judge_dly は補助）。
- `SPEC_pin_oirc.md`（**ISS-00144 対応**）: §3/§5.2 を現行実パターンへ全面改訂＝同一 pin の重複指定不可（「[2]=同[1]」廃止）、 const の slot2 空・async-on-VREL、 power_tin の target スロット方式（energy_tgt_slot/energy_trig_slot）。
- `SPEC_internal_power.md`: ISS-00142（power_tin target スロット窓）・ISS-00151（power_tout 窓 margin 0.3ns＋フォールバック）・per-pin template 仕様（「出力 port 別 template」節）。
- `SPEC_seq_lat.md`: ICG は本 SPEC 枠で実装済み（別 SPEC 予定を解消）・vout_infos・判定方式・旧 LAT 関数の dead code 注記。
- `SPEC_measure.md`: const 判定方式の現行注記（掃引は CLK 側、 判定選択則、 SPEC_const 参照）。

### Verified
- adder 3 セル露払い（0 failures）: index 5% 超逸脱 **46 群 → 0**＝全 179 登録セルで orig index 構造一致。
- 全 179 セルの per-pin 軸調査: 複数出力 6 セル中、 per-pin 割当が必要なのは上記 3 セルのみ。 新規テンプレ定義は不要（全ピンに ≤5% の既存テンプレ実在）。

## [0.9.14a28] 2026-07-10

Alpha pre-release. LAT/ICG const 判定基盤の修正（ISS-00153）＝ ISS-00146（LAT const 値精度）解決。

### Fixed
- `myTbParam.py`（ISS-00153、 致命）: is_lat 判定が `getattr(h.mlc, "logic_type", "")` で**常に False** だった問題を修正（logic_type は Mlc の属性ではなく `mls.logic_dict[mlc.logic]` の辞書引き）。 このバグにより **jp2 の LAT 用 judge 分岐（setup/recovery の judge_dly）が ISS-00133 導入以来一度も描画されていなかった**。 ISS-00146 の setup 16〜18%／recovery 31〜32% 外れの本因。
- `temp_testbench.sp.jp2` / `charao_run.py`（ISS-00153）: **保持型 hold（LAT/ICG、 保持成功＝Q 無遷移）を degradation 判定から電圧化け判定へ分岐**。 jp2 hold ブロックに is_lat 時のみ judge_vlt_max/min（closure 後窓 _t_clk4.._tsim_end、 vout_infos 観測ノード置換対応）を出力し、 runSpiceConstSingle に removal と同方式の判定を追加（arc[0] 規約: "0"/"r"＝保持 L・違反で上昇、 "1"/"f"＝保持 H・違反で下降）。 FF hold は従来どおり degradation（autostop 維持）。 ISS-00146 の hold 36〜39% 外れ・逆符号の本因。
- `charao_run.py`（ISS-00152 続き）: hold の seg_end を t_in0 → t_in1+2*tslew_clk へ延長（fail 領域まで掃引しないと境界未検出）、 tsim_end の毎反復短縮に t_in1/t_rel1 を包含（D 戻り切り落とし防止）。
- `charao_run.py`（ISS-00153）: 保持型 hold の seg_start を _t_init3+2ns 以後に clamp。 clk_init pulse を持つセル（ICG）で seg_start が VIN の capture 遷移（_t_init3 固定アンカー）と衝突し、 観測ノードの正当な取り込み遷移を保持化けと誤判定 → 初手 FAIL で二分探索が進めず const=0 になる問題を解消。
- `myTbParam.py`: wave_raw 時に vout_infos ノード（判定対象）も raw へ保存。

### Verified
- **LAT 4 family（latq/latrnq/latsnq/latrsnq）× const 全 kind × full INDEX 真打ち（2,400 点、 0 failures）**: orig 比較で **|diff|>2ns 外れ 0.0%**（従来 setup 16〜18%／recovery 31〜32%／hold 36〜39%）、 median +0.05〜+0.45ns、 max|d| 1.58ns、 removal 無回帰。 ＝ **ISS-00146 解決**
- hold 電圧判定の境界分解能を波形で実証（latrsnq (4,4): last-pass は Q が 3.63V まで乱れて復帰、 first-fail は 1ps 差で完全反転）
- ICG 2 セル hold 露払い（2x2）: 0.0／1e9 全解消・全 corner 実値化・orig とオーダー一致（diff sub-ns〜1ns）。 setup+hold の full INDEX 真打ちは実行中（結果は課題ファイルに追記）

## [0.9.14a27] 2026-07-08

Alpha pre-release. ICG 2 family（icgtp/icgtn）新規実装＋framework 改善 3 件（ISS-00151/00152）。

### Added
- `mylogic_seq_lat.py`: ICG_PC / ICG_NC（integrated clock gating、latch+AND / latch+OR）各 36 entry を新規実装（ISS-00070 の ICG 残）。 CLK↔Q の comb 型 delay＋power_tout（代表 when E&!TE で orig 照合）、 E/TE の setup/hold（内部ラッチ closure 基準）、 leakage 8 状態（orig when 完全一致）、 power_tin/passive/min_pulse。
- **vout_infos 機構**（ISS-00152、 ダーマツ発案）: const 計測の観測点をセル固有の内部 net へ差し替える汎用機構。 `myLogicCell.py` に vout_infos field、 `myTbParam.py` に vout_node、 jp2 の const 系 8 箇所（prop_clk_out/prop_in_out/judge_dly×4/judge_vlt×2）を setup_kind 非空時のみ条件置換。 出力がクロックにマスクされるセル（ICG: Q=CLK&IQ2）で内部ラッチ出力 QD を観測し、 setup/hold を LAT 完全同型で計測。 `std_seq.jsonc` に icgtp_1/icgtn_1 登録（node=QD、 両セルの GF180 netlist で実在確認）。

### Fixed
- `charao_run.py`（ISS-00151、 全セルの power_tout に影響）: ① energy INTEG 窓の TO に尻尾 margin 0.3ns 追加（eend 以降の指数尻尾 7.2% 切り捨てを実測、 ISS-00075 系統誤差の一因。 SW_TAIL は time_energy[1] 参照のため自動追従）② energy2 の energy_start/end WHEN が大 slew で out of interval → 0 埋めとなる問題を、 energy1 確定値（Mtp.ener_estart/eend 新設）へのフォールバックで解消。
- `charao_run.py`（ISS-00152(a)）: const の tsim_end=1µs 固定を毎反復 t_clk5+3ns に短縮。「出力無遷移が成功」型ハーネス（ICG E/TE fall setup、 LAT hold）で autostop 不発 → 極小 timestep で 1µs 走行する擬似ハング（100 分実測）を解消。

### Verified
- icgtp_1 の measure 別確認（2x2）: leakage/delay/power_tin/passive/min_pulse は orig オーダー一致。 power_tout は 4/4 点実値化（orig との差は帰属分解の方式差＝pin(CLK)/pin(Q) 分解 vs 総量計上、 合算ではオーダー一致）。 setup/hold は vout_infos で実値化し、 hold は orig とほぼ一致（−0.87〜−0.01 vs −0.96〜0.01）。 残（hold 大 slew 隅 1 corner・ICG_NC 確認・full INDEX）は ISS-00152 で管理。

## [0.9.14a26] 2026-07-07

Alpha pre-release. seq_lat（LAT 4 family）の新方式展開＋LAT const dispatch 修正（ISS-00143）。 LAT 4 セルで合格基準①〜⑤確定（const 値精度は ISS-00146 に切り出し）。 **対象 mylogic（comb 3 カテゴリ＋seq_ff＋seq_scan＋seq_lat）の優先課題 横断検証が完了**。

### Fixed
- `charao_run.py`: LAT の setup/hold/recovery dispatch が未定義関数 `runSpiceLatSetupMultiThread_orig` を呼んでいた取り残し（ISS-00133/00138 統一リファクタ時）を解消し、 統一パス `runSpiceConstMultiThread` へ（jp2 の is_lat 分岐が LAT の judge_dly を吸収）。 旧 `*Single_orig` 2 関数は不達の参照残置（削除候補）。

### Changed
- `mylogic_seq_lat.py`: 全 4 family を新方式へ。 LATCH_PE_NS の世代移行（mondrv_oirc 削除・arc "s" を ival から解決、 Q の d/u 14 箇所は latch 論理＝SETN=0→Q=1／opaque→Q=D init／transparent→Q=D で導出、 min_pulse の p/n 表記化）、 pin_tr 全付与（leakage は空ペア）、 slot2 重複解消、 E-target を [o0,i0,"",c0]（E=VCLK）へ統一、 recovery/removal を async-on-VREL 構造へ（ISS-00133 jp2 の TRIG v(VREL)=async 前提に整合）、 hold の arc[0] を stable 化（Q=旧 D 値保持。 遷移期待 arc は autostop 不発の擬似ハングを誘発）。 latrsnq の rec/rem に代表 when s0/r0 を付与（orig 実測）。

### Verified
- LAT 4 セル × full INDEX × 全 measure で 0 failures・collapse 0。 delay/power/removal は orig とオーダー一致（power_tin は when 構造ごと照合成立、 中央 0.03〜0.14）。 const の外れ（setup 16〜18%／recovery 31〜32%／hold 36〜39%）は 4 family 一貫で ISS-00146 として管理。

## [0.9.14a25] 2026-07-06

Alpha pre-release. seq_scan（SDFF 4 family）の新方式展開＋const 代表 1 when。 SDFF 4 セルで合格基準①〜⑤確定（対象 mylogic 全確定）。

### Changed
- `mylogic_seq_scan.py`: seq_ff a23 新方式（DFF_PC/NR/NS/NR_NS）の expect を全 4 family へ移植（140 entries）。 slot2 複製廃止（ISS-00135）、 hold の ival r/f 化（ISS-00101）、 recovery/removal の VIN=i0(D) 駆動＋async-on-VREL、 min_pulse/leakage 新方式化、 delay specify に timing_default。
- const（setup/hold/recovery/removal 24 entry）に Phase B ハーネス状態と一致する代表 1 when を付与（例: sdffrsnq setup = "RN&!SE&SETN&!SI"）。 orig との constraint 照合が初成立。 SE/SI 全分解は ISS-00086B。

### Verified
- SDFF 4 セル × full INDEX × 全 measure で 0 failures。 constraint |diff| 中央: setup 0.19〜0.41 / hold 0.14〜0.41 / recovery 0.09〜0.12 / removal 0.21〜0.25 ns（seq_ff 同水準）。 delay は orig functional-mode 群と手動照合でオーダー一致。

## [0.9.14a24] 2026-07-06

Alpha pre-release. power_tin の target スロット方式（ISS-00142）。

### Fixed
- `charao_run.py`（`runSpicePowerTinSingle`）: エネルギー積分窓・tsim_end・slope→tslew 割当・cin 選択を、計測対象ピン（pin_tr[0]）を駆動するスロット基準に統一（窓 = [t_X0, t_X1+1ns]）。旧実装（窓 t_rel0 決め打ち／slope→tslew_clk 決め打ち）により seq_ff の pin(CLK) internal_power 全 0・index_1 軸の空回り・cin 破綻が発生していた。
- `myTbParam.py`: `energy_tgt_node`/`energy_tgt_slot` 追加（pin_tr[0] の c>r>i スロット逆引き。 power_tout 用 `energy_trig_*`（related）と対をなす target 版）。
- `mylogic_seq_scan.py`: SDFF 4 family の power_tin 32 entry の slot2 重複を解消（`[o0,i0,"",c0]` 化、同一ピン重複指定不可ルール準拠）。

### Verified
- 51 セル × full slew（MEAS_ONLY=power_tin）で 0 failures。 dffq/dffnq の pin(CLK) が orig とオーダー一致（charao 0.081〜1.11 vs orig 0.28〜0.79）、 入力ピン power の slew 依存傾向を orig と整合して初再現。

## [0.9.14a23] 2026-07-04

Alpha pre-release. seq_ff の全 measure export 対応（フレームワーク修正）＋ dffrsnq 新方式の全 10 family 展開。 GF180 seq_ff 8 セルで full INDEX 検証完了（0 failures・orig オーダー一致）。

### Fixed
- `charao_run.py`: prop を `pin_tr[1]` で `prop_clk_out`（CLK 駆動）/`prop_rel_out`（REL 駆動）に出し分け（旧 決め打ちで seq が my_exit）。
- `myTbParam.py`: `energy_trig_node`/`energy_trig_slot` 追加。 energy_start の TRIG ノードを related pin（VIN/VREL/VCLK）から選択（旧 `WHEN V(VREL)` 決め打ちで seq が不発）。
- `temp_testbench.sp.jp2`: `i_rel_leak`/`i_clk_leak` を退化窓から `i_vdd_leak` と同じ遷移前安定窓へ統一。
- `util_extract_lib_csv.py`: power table 認識を汎用化（`stable` テーブルで pin 丸ごと欠落するバグを修正）。
- `mylogic_seq_ff.py`: NC 系 min_pulse_width_low の退化ハーネス（D がパルス前に init 値へ復帰 → Q 無遷移 → MEASURE 不発 → autostop 無効の擬似ハング）を arc `["f","f","","n"]`→`["r","r","","n"]` で解消（4 family）。

### Changed
- `mylogic_seq_ff.py`: dffrsnq（DFF_PC_NR_NS）新方式を全 10 family（GF180 7 + DFFB 2）へ展開。
  - pin_oirc/arc slot2 の CLK/D 複製廃止（ISS-00135）
  - hold の ival i=r/f 化＋arc 入替（ISS-00101）
  - recovery/removal を VIN=i0(D) 駆動＋async-on-VREL 化
  - const に tmg_when 付与（orig .lib 裏取り：_NR=`r0` / _NS=`s0` / NR_NS=`r0&s0`＋rec/rem `s0`/`r0`、 DFFB_PC_PR=`!r0`、 DFFB_PC_NS=`s0`）
  - min_pulse clk の単一 entry 化（when 分割は ISS-00082）、 delay specify entry に `timing_default=True`
- 検証: 8 GF180 セル full INDEX 0 failures、 compare --interpolate 点比較で |diff| 中央 delay 0.21〜0.43 / setup 0.13〜0.24 / hold 0.13〜0.31 ns（dffrsnq 07-02 と同水準）。 DFFB（TRIP62）の実行検証は ISS-00141。

---

## [0.9.14a22] 2026-07-01

Alpha pre-release. ISS-00117: power_tout/energy2 の ngspice timestep collapse（最終 DC 点での理想電圧源 枝電流の行列特異による Newton 収束失敗）を、テール限定 SW 制御抵抗で解消。

### Fixed
- (ISS-00117) `temp_testbench.sp.jp2` / `charao_run.py`: power_tout/energy2 が full grid（特に小 slew）で `Timestep too small ... trouble with node <理想源>#branch` abort する問題を解消。 原因＝energy2 は INTEG のため autostop 不可 → 固定 sim_end へ最終ステップ強制着地 → 遷移後の高 Z 定常テールで理想電圧源の枝電流 i(源)#branch が cap-only ノードにより行列特異化 → Newton 収束失敗（timestep が 5e-24 まで半減して abort）。 積分法(gear)・margin・autostop-time はいずれも不可（whack-a-mole／条件数の問題）。
  - **対策＝テール限定 SW 制御抵抗による de-singularization**：`SW_TAIL`（pullres 同型）で VIN/VREL を、 計測窓の後（`eend+1ps`→`sim_end`）だけ自分の vdd/vss 両レール（`_vdd_vrel`/`_vss_vrel`, VIN 同）へ clamp し DC 経路(導通)を与える。 SW は INTEG 窓 [estart,eend] では OFF ＝ **cin/energy/leakage は無影響**（時間ゲート）。 VREL/VIN に DC 経路を与えると行列全体の条件数が改善し、 vss_dyn#branch 等の他枝 collapse も同時に解消。
  - `charao_run.py`: energy2 の `tsim_end2 = max(eend, param.t_rel1) + 2e-9`（SW が ON で居られる tail 区間を確保）。
  - 検証: aoi222_1 full grid で **121→0 failures**、 collapse 0。

---

## [0.9.14a21] 2026-06-26

Alpha pre-release. mylogic と jsonc の過不足解消（reset+set DFF の passive 欠落）＋ template load 軸（index_2）割当バグ修正。

### Added
- `mylogic_seq_ff.py`: `DFF_PC_NR_NS`（dffrsnq）/ `DFF_NC_NR_NS`（dffnrsnq）に passive measure を各 8 entry 追加（D×2・RN×2・SETN×2・CLK×2）。 兄弟 _NR/_NS・LATCH・SDFF は passive 保有、 orig .lib も入力ピン internal_power（CLK/D/RN/SETN）保有のところ、 reset+set 両対応の 2 logic だけ欠落していた定義漏れを補完。 過不足（mylogic 由来 kind vs jsonc template_kgn）を全 147 セルで突合し 0/147 達成

### Changed / Fixed
- `util_assign_templates.py`: load 軸（index_2）テンプレ割当バグ修正。 従来 `_read_grids_from_lib`/`_read_grids_from_csv` が delay の load 軸・constraint の slew 軸（0.02..4）・min_pulse の index_2 を全部 set に lump → constraint を持つ seq で長さ不一致 → max-only fallback で誤割当（dffq の load=0.001..0.24 を slew 軸 max=4 の d044 に誤マッチ, dev 55%）。 `_CONSTRAINT_TIMING_TYPES`（setup/hold/recovery/removal/min_period）blacklist で slew 軸を除外＋`_pick_load_grid` でアーク（pin/related/timing_type）単位の代表 load グリッド選定に修正。 多アーク（addf/bufz/invz）の fallback も解消
- `std_seq.jsonc` / `std_comb.jsonc`: 上記修正に基づく template_kgn 再割当（std_seq 15 セル d016→d018/d014 load 軸 dev 2.3〜3.3%、 std_comb 4 セル addf/addh d017→d018 等）。 delay/power_tout 整合・comb 単一アーク（aoi222 d006/mux4 d010）は 0% 維持

---

## [0.9.14a20] 2026-06-26

Alpha pre-release. min_pulse_width 計測の刷新（ISS-00137 解消・ISS-00133 min_pulse 部ひとまず修正）＋ ISS-00135 pin_oirc/pin_tr reorg。（a19 は CHANGELOG 未記載のため a18→a20 の差分として記述）

### Added
- `docs/SPEC_const.md` / `docs/SPEC_pin_oirc.md`: 新規（const MEASURE 仕様 / pin_oirc・pin_tr 設計）
- `config_lib.jsonc`: `simulation_slew_for_pulse`（min_pulse のパルス源 slew、 default 0.02ns＝LUT 最小 slew 目安）

### Changed / Fixed
- (ISS-00137) `myConditionsAndResults.py`: `set_direction` の出力（direction_prop/tran/power・constraint・passive_power）を 1 dict `direction_in_lib` に集約。 `arc_in=p/n`（min_pulse のパルス arc）で my_exit していたのを解消（p/n→""）。 消費側（myExportLib/myExportDoc/charao_run）を dict 参照に置換（出力 byte 不変）
- (ISS-00133) min_pulse_width 計測刷新（`charao_run.py` / `myTbParam.py` / `temp_testbench.sp.jp2`）: tpulse・prop を `pin_tr[0]` で振分（CLK→tpulse_clk・prop_clk_out / async→tpulse_rel・prop_rel_out）、 prop TRIG を logic 名サフィックス（_PC/_NC・_PS/_NS・_PR/_NR）の能動エッジ基準に、 secant 判定に trans（出力 slew）劣化を OR 追加、 保存値を実測 `pulse_width_clk`/`pulse_width_rel`（0.5×VDD）に変更。 → floor 収束解消・load 非依存化
- (ISS-00135) `mylogic_comb_{base,complex,tristate}.py` / `mylogic_seq_{ff,lat,scan}.py` / `myExportLib.py` / `myLogicCell.py` 他: pin_oirc/pin_tr reorg（spice 駆動＝pin_oirc[k]、 Liberty arc 属性＝pin_tr）

---

## [0.9.14a18] 2026-05-22

Alpha pre-release. LAT lib の when 整備（ISS-00090 Phase2 / ISS-00100）、 min_pulse_width の when 対応（ISS-00082）、 ival 波形仕様の策定（ISS-00101）。

### Added
- `docs/SPEC_specify.md`: 新規。 Verilog specify 記述仕様（specify 文の種類、 tmg_when、 ifnone（`;;`）、 .lib timing block との対応）
- `docs/SPEC_ival.md`: 新規。 ival / arc_oirc 波形仕様（ival 9 値・arc 3 値・期間定義・全条件網羅表。 ISS-00101 — mondrv_oirc/clk_role/clk_init を吸収する波形モデル）

### Changed
- (ISS-00090 Phase2) `charao/script/mylogic_seq_lat.py`: LAT 4 family の clear/preset を D×E(×RN) の when 別 entry に分割（+ ifnone=timing_default）、 setup_falling/hold_falling に when（RN/SETN/RN&SETN）付与、 min_pulse_width を D 2 分割の when 別に、 power_tin を D×E×RN×SETN の when 別に細分化（pin RN/SETN の power_tin を新規追加）
- (ISS-00082) `charao/script/myLogicCell.py`: `min_pulse_width_high/low` の key を `(port, when)` タプル化
- (ISS-00082) `charao/script/charao_run.py`: `set_min_pulse_width` に `when` 引数追加
- (ISS-00082) `charao/script/myExportLib.py`: min_pulse_width を when 別 `timing(){min_pulse_width}` block で出力（pin attribute は when 横断 max）
- (ISS-00082) `charao/script/myExportDoc.py`: `.md` の MIN PULSE WIDTH テーブルに When 列を追加
- (ISS-00082) `charao/script/mylogic_seq_ff.py`: dffq/dffnq の min_pulse_width を D 2 分割（when `!D`/`D`）。 dffrnq の pin(CLK) も同様、 pin(RN) は暫定 4 分割（ISS-00101 待ち）

### Verified
- LAT 4 family（latq/latrnq/latsnq/latrsnq）の clear/preset/setup/hold/min_pulse_width/power_tin の when 出力が orig vendor lib と when 構成一致、 各 sim 0 failures
- DFF dffq/dffnq の min_pulse_width when 別出力、 sim 0 failures

### Known issues
- (ISS-00101) ival 波形仕様の実装（mondrv_oirc/clk_role/clk_init 廃止、 全 mylogic リファクタ + 全セル回帰）は a19 以降
- (ISS-00082) DFF pin(RN/SETN) の min_pulse_width when 化は ISS-00101 待ち。 dffrnq の pin(RN) entry は暫定 4 分割のまま（min_pulse_width sim 不可の状態）
- (ISS-00099) `.v` specify の ifnone 位置（timing_when ソート起因）

---

## [0.9.14a17] 2026-05-21

Alpha pre-release. ISS-00096 解決: cell 別成果物のマージツール util_merge.py を追加。debug_run.sh のログ運用を改善。

### Added
- (ISS-00096) `charao/script/util_merge.py`: 新規。`run_each` が cell ごとに出力する .lib/.v/.md を 1 ファイルに統合
  - 引数 = .lib/.v/.md ファイルリスト（混在可、シェルのワイルドカードで展開）、`--out <prefix>` で `<prefix>.{lib,v,md}` を生成
  - ヘッダを date 行を除いて全ファイル照合（不一致は最初の差異行を表示して ERROR 停止）、date は引数末尾ファイルのものを採用
  - .lib=cell ブロック / .v=`` `celldefine ``〜`` `endcelldefine `` / .md=`# Cell Infomation` 以降の `## <cell>` セクションを結合、共通部（library ヘッダ・templates / primitive 定義 / .md frontmatter+settings）は 1 回のみ出力
  - 1 拡張子 1 file（=1 cell）の群はマージをスキップ（元ファイルをそのまま使えばよいため）
- `debug_run.sh`: `merge` サブコマンド追加（`${RUN_NAME}/rslt_*/` の .lib/.v/.md → `${RUN_NAME}/merged.{lib,v,md}`）

### Changed
- `debug_run.sh`: sim 実行中はログを非圧縮 .log に逐次書き込み（`tail -f` で進捗確認可）、取得完了後に gzip 圧縮する方式へ変更（従来は実行中も動的 gzip）

### Verified
- util_merge.py: round-trip（1 cell split→merge で元と一致）、2-cell マージ、ヘッダ不一致検出（date 以外）、date 末尾採用、1-cell スキップ — 全項目合格

---

## [0.9.14a16] 2026-05-21

Alpha pre-release. LAT（level-sensitive latch）対応一式: 4 family 実装、measure 仕様（SPEC_seq_lat.md）策定、clk_init 判定の一元化、大 input slew での internal_power 0 値修正。

### Added
- (ISS-00070) `charao/script/mylogic_seq_lat.py`: 新規。LAT 4 family（LATCH_PE / _NR / _NS / _NR_NS）の Logic 定義
- (ISS-00070) `charao/script/myExportLib.py`: latch グループ出力サポート（level-sensitive latch の .lib block）
- (ISS-00070) `charao/script/myLogicCell.py`: `islatch` フラグと latch dict を追加
- (ISS-00070) `sample/target/gf180/fd/mcuC7t20240817/std_seq.jsonc`: LAT 4 cell entry 追加（latq_1 / latrnq_1 / latsnq_1 / latrsnq_1）
- (ISS-00070) `charao/script/charao.py`: modules リストに `charao.script.mylogic_seq_lat` 追加
- (ISS-00090) `charao/script/charao_run.py`: LAT setup/hold 用 sim 関数群（`runSpiceLatSetupSingle` / `runSpiceLatHoldSingle` 等）と single-fall testbench 対応。`prop_in_out`→`prop_rel_out` リネーム + 新 `prop_in_out` 追加
- (ISS-00090) `charao/script/myTbParam.py` / `charao/script/temp_testbench.sp.jp2`: level-sensitive latch testbench 対応
- `docs/SPEC_seq_lat.md`: 新規。LAT measure 仕様書（measure 12 項目、clk_init 3 段判定原則、passive / leakage 条件、§7 実装記録）

### Changed
- (ISS-00092, §7-2) `charao/script/myConditionsAndResults.py` `set_target_clkport`: latch の clk_init を logic 名の極性サフィックス（`_PE`/`_NE`, `_PR`/`_NR`, `_PS`/`_NS`）パースで 3 段判定（① RN/SETN active→stable ② inactive かつ E 透過→stable ③ それ以外→pulse）。`*Single()` 個別指定から一元管理へ
- (§7-2) `charao/script/charao_run.py` `runSpiceLatSetupSingle` / `runSpiceLatHoldSingle`: clk_init の固定指定を `h.clk_init` 参照に変更
- (§7-3) `charao/script/mylogic_seq_lat.py`: leakage E=H entry の arc を s 化（`arc_oirc` 末尾を r→s、ival c=0→1、4 family）、passive / leakage entry を 3 条件化
- (§7-3) `charao/script/mylogic_comb_tristate.py`: INVZ の power_tin entry 6 個を追加（ZN=!I 極性）
- `charao/script/myExportDoc.py`: latch セルの .md 出力対応
- `docs/SPEC_seq_ff.md` / `docs/SPEC_internal_power.md` / `docs/SPEC_three_state.md`: コードとの整合性を修正

### Fixed
- (ISS-00093) `charao/script/myExportLib.py`: min_pulse_width の timing_type をクォート付きに統一（`timing_type : "min_pulse_width";`）
- (ISS-00094) `charao/script/charao_run.py` `runSpicePowerToutSingle`: 大 input slew で `.tran` の最大ステップが i_*_leak の AVG 区間幅（`100*tslew_min`）を超え、leakage measure が「out of interval」で失敗 → power 0 になる問題。2nd trial の `timestep_tmax` を `timestep_tstep` 下限つきでクランプ、energy 区間 / `tsim_end` を `compute_timing()` 既知時刻参照に変更
- (ISS-00095) `charao/script/charao_run.py` `runSpicePowerTinSingle` / `runSpicePassiveSingle`: ISS-00094 と同一原因の passive / power_tin の energy 0 値。`timestep_tmax` を同様にクランプ（`timestep_tstep` 下限が無いと収束破綻するため下限を併設）

### Removed
- `charao/script/mylogic_seq_lat.py`: 未使用の `LATCH_PE_PR_NS` 定義を削除

### Verified
- latrsnq_1 full INDEX: **0 failures**、0 値ブロック数 0（大 slew の power 0 値が完全解消）

---

## [0.9.14a14] 2026-05-17

Alpha pre-release. ISS-00086 Phase B 完了: SDFF 4 family 実装 (sdffq/sdffrnq/sdffsnq/sdffrsnq × _1)。

### Added
- (ISS-00086 Phase B) `charao/script/mylogic_seq_scan.py`: 新規ファイル、SDFF 4 family の Logic 定義
  - SDFF_PC / SDFF_PC_NR / SDFF_PC_NS / SDFF_PC_NR_NS
  - vcode は orig sdff*_func 準拠 (MUX2 OR-of-3-ANDs + udp_iq_ff_n/hn + Q invert)
  - expect 群は DFF_PC* pattern 継承 + ival["i"] 3 要素化 (SE=0/SI=0 functional mode 固定)
  - primitive は mylogic_seq_ff.py の 4 種 (udp_iq_ff_n/hn) を共有 (新規 primitive 不要)
- `sample/target/gf180/fd/mcuC7t20240817/std_seq.jsonc`: SDFF 4 cell entry 追加 (sdffq_1 / sdffrnq_1 / sdffsnq_1 / sdffrsnq_1)
- `charao/script/charao.py`: modules リストに `charao.script.mylogic_seq_scan` 追加 (5 modules → 6 modules)

### Verified
- DFF 8 family + SDFF 4 family × full INDEX × 全 measure × **0 failures** (12 cell regression、所要 約 2 時間)
- charao 出力 .v の functional logic が orig sdff*_func と完全一致 (MUX2 + primitive + Q invert)
- charao 出力 .lib の area orig 完全一致、主要値 (MPW / period / setup-hold) は既存 DFF と同等の系統誤差レベル
- 既存 DFF 8 family への副作用なし

### Known issues
- (ISS-00086B) orig 互角化 (SE/SI 別 when 計測): Phase A で対応予定。Phase B 現状は SE=0/SI=0 functional mode のみ → orig の when 構造 (leakage 16 / internal_power 8 等) と 1:1 比較不可

---

## [0.9.14a13] 2026-05-16

Alpha pre-release. a09〜a13 統合 entry（a09〜a12 は commit のみで CHANGELOG entry が omit されていた経緯あり）。ISS-00077 / 00080 / 00081 / 00083〜00085 / 00087 / 00089 解決、ISS-00088 検出。

### Added
- (ISS-00077, a09) `charao/script/temp_testbench.sp.jp2`: `.option reltol=1e-4` 追加（ngspice default の 10 倍 tight、setup_rising 精度向上）
- (ISS-00080, a10) `charao/script/myTbParam.py`: `Mtp` class 拡張（timing fields 18 個 + `compute_timing()` + `tsweep_for_rel0_at()`）
- (ISS-00081, a11) `charao/script/myExportLib.py`: pin(CLK) 内 `min_period` attribute + `timing(timing_type:min_pulse_width)` block 出力
- (ISS-00083, a12) DFF 7 family（DFF_NC / DFF_PC_NR / DFF_PC_NS / DFF_NC_NR / DFF_NC_NS / DFF_PC_NR_NS / DFF_NC_NR_NS）に power_tin (CLK/CLKN x 2 + D x 2 = 8 個) と power_tout 展開
- (ISS-00084, a12) DFF 8 family の `min_pulse_width_high` / `min_pulse_width_low` 両 polarity 実装
- (ISS-00086 準備, a12〜a13) `30_projects/SPEC_mylogic.md`、全 family pin mapping コメント
- (ISS-00087, a13) `charao/script/myLibrarySetting.py`: `simulation_timestep_min = 0.001 ns` 新設、下限保護 `timestep_tstep = max(min, min(slope*0.0099, max))`
- (ISS-00088, a13 検出) passive lib 出力形式の orig vendor 不整合（LOW 優先、後段）

### Changed
- (ISS-00080, a10) 全 sim 関数の interface 統一：`(targetHarness, spicef, param)` 型に変更、`runSpiceXxxSingle` で Mtp 早期 instantiate + `compute_timing()` 呼び出し
- (ISS-00080, a10) secant range の物理表現化（setup/hold は `t_init3` 基準で `tsweep_for_rel0_at()` 経由）
- (ISS-00080, a10) PowerTout 2 段階 sim 改善（1st: estart/eend 抽出、2nd: energy 測定、共通 param 流用）
- (ISS-00080, a10) jp2 の `.param _t_*` を `{{param.t_*}}` に置換、testbench timing は Mtp.compute_timing() が single source of truth
- (ISS-00080, a10) `charao_run.py` -530 行、`myTbParam.py` +70 行、`temp_testbench.sp.jp2` -66 行
- (ISS-00081, a11) min_period 値の決定方式：duty 50% 安全側 `min_period = 2 * max(mpw_high, mpw_low)`
- (ISS-00085, a12) `temp_testbench.sp.jp2`: VREL に `_t_rel2 / _t_rel3` 追加し VCLK と対称な cycle 化（RN/SETN min_pulse_width_low secant 失敗解消）
- (ISS-00087, a13) `charao/script/temp_testbench.sp.jp2`: VPC_CTRL release を `_t_in0 - tslew_min` から `_t_init3` に前倒し、VCLK PWL closure バグ修正
- (ISS-00087, a13) `charao_run.py` runSpice*Single 一連の Mtp param refactor（tdelay_in、seg_start、tsim_end、timestep_tstep）
- (ISS-00087, a13) `sample/target/gf180/fd/mcuC7t20240817/config_lib.jsonc`: `sim_c2d_min=10.0 / sim_c2d_max=200.0` 明示
- (ISS-00089, a13) `charao_run.py` の **Delay / PowerTout / PowerTin / Passive** で `tdelay_rel` を `h.mls.sim_prop_max` → `h.mls.sim_d2c_max` に統一
  - 真因：`sim_prop_max(25ns)` は propagation delay 最大値で、D→CLK 間隔としては誤用。setup/hold/min_pulse と同じ `sim_d2c_max(6ns)` 用法が正
  - 背景：ISS-00076 の WOUT pre-charge SW があるため、settling 余裕は不要
- (ISS-00089, a13) `debug_run.sh`: cmd_run_each の RUN_NAME / sim per-dir 強化

### Fixed
- (ISS-00077, a09) dffq_1 full INDEX bench (setup_rising): avg `+2.55 → +0.16` ns（**16 倍改善**）、σ `2.96 → 0.88`、max `+12.14 → +7.05` ns
- (ISS-00085, a12) RN/SETN min_pulse_width_low: secant 失敗 → 物理値（dffrnq_1 RN 76 ps、dffsnq_1 SETN 154 ps）
- (ISS-00087, a13) DFF 8 family full INDEX で 10 件発生していた `Timestep too small @ vclk#branch` を 0 件に解消（setup/hold/recovery/removal 系）
- (ISS-00089, a13) negedge CLK 系 (dffn*) の power_tout sim 失敗 4 件解消（slew=0.02 × energy2 trial × arc=ffff/rrff）

### Verified
- (ISS-00080, a10) dffq_1 INDEX(9,9) 全 meas_type で旧 charao と完全同値（setup_rising fall=2.2/rise=-0.644、hold_rising fall=-2.19/rise=0.647、min_pulse_low/high=0.128/0.212、cell_leakage_power=0.00341 等）
- (ISS-00089, a13) dffnsnq_1 / power_tout / arc=ffff / INDEX1=0 / INDEX2=0：A 修正前 abort → 修正後 0 failures、全 measurement 完了
- (ISS-00089, a13) DFF 8 family `_1` × full INDEX × 全 measure：**0 failures**（既知 14 件失敗解消、新規 failure 無し、所要時間 約 1 時間）

### Known issues
- (ISS-00086) SDFF 4 family 実装：次回
- (ISS-00088) passive lib 出力形式の orig 整合：別途
- (ISS-00079) num_thread 最適化：thread=4 で運用継続中

---

## [0.9.14a08] 2026-05-13

Alpha pre-release. ISS-00078 完成: wave_raw オプション + 汎用 raw viewer (tools/raw_viewer.html).

### Added
- `charao/script/charao.py`: `--wave_raw` CLI オプション追加
- `charao/script/myLibrarySetting.py`: `wave_raw : bool` field 追加
- `charao/script/myTbParam.py`:
  - `wave_save_list` (XCELL 渡し 14 信号、 小文字 vector 名) と `pinmap_dict` (DUT cell port → plot signal name) を生成
  - `write_pinmap_if_enabled()` メソッド: sim_dir に `.pinmap.json` sidecar を書き出し
- `charao/script/charao_run.py`: 各 `genFileLogic_*` で sim file 書き出し直後に `.pinmap.json` を出力
- `charao/script/temp_testbench.sp.jp2`: `.control / run / write sim.sp.raw <signals> / .endc` ブロック追加（wave_raw 有効時のみ、 XCELL 渡し 14 信号を小文字で指定）
- `debug_run.sh`: `WAVE_RAW` env var → `--wave_raw` CLI 自動展開
- `tools/raw_viewer.html` (新規、 ~75 KB): 汎用 ngspice raw viewer
  - 1 HTML 完結（uPlot inline、 オフライン動作）
  - D&D で `.raw` + optional `.pinmap.json` 読込
  - **multi-pane 表示**（1 signal = 1 plot pane、 x 軸 + cursor 同期）
  - 各 pane 左に **2 段 label**（上：DUT pin name、 下：raw signal name）
  - y 軸：全 pane 統一スケール（全 enabled signal の min/max ±5%）
  - **VLOW / VHIGH 罫線**（v(vss_dyn) / v(vdd_dyn) 最終値、 グレー破線）
  - **時間軸専用 pane** を最下段固定（枠なし、 数値 + 単位 label）
  - 電源系（V(VDD*)/V(VSS*)/V(VNW*)/V(VPW*)/V(VHIGH*)/V(VLOW*)）デフォルト OFF
  - pinmap がある場合は **pinmap 対応 signal のみ** sidebar 表示（DUT pin name 順）
  - **signal 並び替え**（↑↓ ボタン）
  - **pane height ピクセル設定**（footer、 min=20、 初期値 100 px）
  - 時間軸自動単位（ns/μs/ms/s/ps）＋手動切替
  - zoom（box drag）/ pan / cursor crosshair / autoscale
  - **2 cursor 差分計測**：plot click で marker A 固定 → mouse hover の cursor B との `Δt` / 各 signal の `Δv` を footer に表示

### Implementation notes
- ngspice raw 出力：`.save` directive ではなく `.control` ブロック内 `write` コマンドを使用（`.save` は HSpice 互換モード下で transient 結果が 1 point に圧縮される問題があった）
- ngspice の `write` は vector 名を小文字で要求（`v(vclk)` etc.）→ `wave_save_list` を小文字生成
- WOUT / WFLOAT は XCELL に渡される port ではないため保存対象外
- pinmap は 2 段 mapping（cell port name → logic port name → testbench top node）：`ports_dict[port] == h.target_inport` 等で照合

### Verified
- dffsnq_1 / INDEX1=9 / INDEX2=9 / setup_rising / WAVE_RAW=1: 0 spice failures、 raw 18 KB / sim、 No. Points: 149、 15 variables、 `.pinmap.json` 8 entries（D/SETN/CLK/Q/VDD/VNW/VPW/VSS）
- viewer: D&D で raw + pinmap 読込、 multi-pane 表示、 cursor / x scale 同期、 並び替え、 2 cursor 差分計測、 全動作確認

### Known issues
- DFF Q 初期値は ngspice DC OP の自然 state に依存（`.IC` 強制は val0="u"/"d" 時のみ。 通常 ival="0"/"1" では DC OP まかせ）。 setup secant は CLK 遷移の Q 変化で判定するため動作上は許容範囲

---

## [0.9.14a07] 2026-05-13

Alpha pre-release. ISS-00079 検証中の構造的改善（速度効果薄だが基盤として保持）.

### Changed
- `charao/script/charao_run.py`: sim 個別 subdir 化のためヘルパー `_build_spicef_base` / `_make_sim_path` 追加、 各 MultiThread 関数 (Delay/PowerTout/PowerTin/Setup/Hold/Passive/MinPulse/Leakage) と Single 関数で spicef path を `<cell>/vt_<v>_<t>_<n>_<meas>/oir=<o>_arc=<a>_..._s.../sim.sp` 形式に変更
- `charao/script/myLibrarySetting.py:exec_spice`: subprocess の cwd を sim 個別 dir に切替、 ngspice cmd 内 path を basename 化、 `.spiceinit` を sim_dir にコピーして並列 read 競合を回避

### Verified
- dffsnq_1 / INDEX2=0,8,9 / setup_rising bench (thread=8): base 5m 15.95s → subdir のみ 5m 21.82s → subdir + cwd 分離 + `.spiceinit` copy 5m 34.65s
- 速度効果は薄い（or 微悪化）が、 sim 個別 dir 化により raw 取得 (ISS-00078) で各 sim 波形を独立 file として整理可能、 将来 dir 分散最適化の基盤として有効
- `.lis` 分析で thread=8 の analysis time が thread=4 比 19 倍遅 (max 1032 倍) → ngspice 内部の serial bottleneck が dominant、 fs/cwd/OpenMP では説明できない

### Known issues
- ISS-00079 真因は依然不明。 次フェーズ: ngspice OpenMP 対応確認 (`ldd $(which ngspice) | grep omp`、 `strings ... | grep -i openmp`)、 BLAS 環境変数試行 (`OPENBLAS_NUM_THREADS=1` 等)、 遅化 sim の特徴抽出
- 暫定運用: `sample/target/gf180/fd/mcuC7t20240817/config_lib.jsonc` の `num_thread=4` を維持 (sweet spot)

---

## [0.9.14a06] 2026-05-13

Alpha pre-release toward `1.0.0`. ISS-00070 DFF 8 family 実装着手 + Phase 2 rename + lib CSV schema 拡張 + num_thread 安全網 (ISS-00079 暫定対策).

### Added
- ISS-00070 DFF 8 family (GF180):
  - `charao/script/mylogic_seq_ff.py` (新規): dffq/dffnq/dffrnq/dffnrnq/dffsnq/dffnsnq/dffrsnq/dffnrsnq の 8 logic 定義 (GF180 wrap 流 vcode: not gate + udp_iq_ff_n/hn + not gate)
  - `sample/target/gf180/fd/mcuC7t20240817/std_seq.jsonc` (新規): GF180 DFF 8 セル登録 (primitive 指定 + ports_dict)
  - `docs/SPEC_seq_ff.md` (新規): DFF/SDFF 規約 11 章 + GF180 wrap 流 vcode 仕様 + 新規 PDK 移植手順
  - `README.md`: SPEC_seq_ff.md リンク追加
- num_thread 自動 clamp 安全網:
  - `charao/script/myLibrarySetting.py`: `model_validator(mode='after')` で `max(1, cpu_count - 1)` に clamp (1 thread を汎用処理用に残す)
- lib CSV schema 拡張 (DFF 比較対応):
  - `charao/script/util_extract_lib_csv.py`: `timing_type` 列追加、 `rise_constraint`/`fall_constraint` テーブル対応、 scalar (NaN sentinel) 対応
  - `charao/script/util_compare_lib_csv.py`: `timing_type` を group key に含める、 NaN 行は補間スキップ + strict 1:1 照合

### Changed
- Phase 2 rename: `pin_oir` → `pin_oirc` / `mondrv_oir` → `mondrv_oirc` / `arc_oir` → `arc_oirc` (常に 4 要素、 [3] = clock pin、 comb cell は `""`)
  - `charao/script/myExpectCell.py`: コア field 4 要素化
  - `charao/script/charao_run.py`: 参照側 + `arc_c0` 自動生成削除 (jsonc/mylogic で明示指定する設計)
  - `charao/script/myConditionsAndResults.py`: 参照側 + typo `fallin_edge` → `falling_edge` 修正
  - 既存セル群 (`mylogic_comb_base.py` / `mylogic_comb_complex.py` / `mylogic_comb_tristate.py` / `mylogic_io.py`) を全て 4 要素対応に追従
- WOUT pre-charge SW 期間延長: `_t_init0 ~ _t_in0 - timestep` (comb/seq 共通)
  - `charao/script/temp_testbench.sp.jp2`
- `sample/target/gf180/fd/mcuC7t20240817/config_lib.jsonc`: 既存値 8 維持 (ISS-00079 で 100 検証後、 thread=4 sweet spot 判明 → subdir 化対策後に最終値決定)

### Removed
- `charao/script/mylogic_seq.py`: 旧 OSU035 用 DFF/Latch 定義を `mylogic_seq_ff.py` に統合 (GF180 wrap 流に書き直し)

### Verified
- DFF 8 family / 各 _1 サイズ full INDEX bg ジョブで **0 spice failures** (5/12〜5/13)
- compare 動作: matched groups 40 / matched points 4000、 `cell_fall falling_edge` diff avg -0.25〜-0.35 ns (既存系統誤差レベル、 ISS-00075 同種)
- `setup_rising` で diff avg +2〜+12 ns 観察 → **ISS-00077** として記録

### Known issues
- **ISS-00077**: DFF setup_rising 系統誤差 (charao > orig +2〜+12 ns、 INDEX2 大で diff 増大)
- **ISS-00078**: sim 実行時の波形取得オプション未実装 (`--wave_raw` + 階層参照 `V(XCELL.XDUT.<port>)` + 汎用 raw viewer `tools/raw_viewer.html`)、 仕様確定済
- **ISS-00079**: num_thread 最適化。 192.168.168.103 (物理 16/HT 32) で thread=4 sweet spot (thread=8 で 4 倍遅、 thread=31 で 17 倍遅) → btrfs 同 dir 並列新規 inode 作成の B-tree contention が原因。 sim ごと subdir 化で対策予定

### Next
- ISS-00079 subdir 分割で thread スケーラビリティ改善
- ISS-00078 波形取得オプション + raw viewer 実装
- ISS-00070 残: SDFF/LAT/ICG family、 DFF サイズ展開 (_2/_4)、 1.0.0 main マージ

---

## [0.9.14a05] 2026-05-12

Alpha pre-release toward `1.0.0`. Closes ISS-00076 (sim time optimization for comb/tristate/power). BUFZ_1 full INDEX で **約 25 倍高速化** (1h 51min → 4min 20s) を確認。

### Added
- `charao/script/temp_testbench.sp.jp2`: WOUT pre-charge SW を VOUT セクションに追加 (0.1ns~0.9ns active、 Ron=0.1Ω、 τ=10ps×80 で 99% 充電)。 商用ツール (SiliconSmart 等) の voltage pre-charge + SW 切替手法を ngspice に移植したもの。

### Changed
- `charao/script/charao_run.py`:
  - `genFileLogic_DelayTrial1x` (line 454-456) / `genFileLogic_PowerToutTrial1x` (line 648-651) / `genFileLogic_PowerTinTrial1x` (line 801-803): `tdelay_init` / `tpulse_init` / `tdelay_in` を `startswith(("delay","three","power"))` で 1ns 固定 (seq 系 setup/hold/min_pulse_width 等は実時間が意味あるため除外)。
  - `runSpicePowerTinSingle` (line 560-562): absolute 時刻計算用の `tdelay_init` / `tpulse_init` / `tdelay_in` も 1ns 固定 (template 側と整合)。

### Verified
- BUFZ_1 full INDEX (after):
  - 所要時間: **4 min 20 sec (= 約 25 倍速化、 before 1h 51min)**.
  - timing matched 4 groups / 440 pt, diff avg -0.0991 ns (before -0.0919、 同等).
  - power (output, active arc) matched 4 groups / 400 pt, diff avg -0.17 (before -0.17、 同等).
  - power (input, stable state) matched 4 groups / 40 pt (before と同等).
  - 0 spice failures、 構造的 regression なし.
- pre-charge SW: WOUT を 0.1ns~0.9ns で `_vss_vout` (or `_vdd_vout`) に強制駆動、 0.9ns 後 SW OFF (Roff=1GΩ) で release。 DC OP も pre-charge 状態で settle するため bias 不整合なし。
- 14 セル full INDEX (post-tag): scheduled separately、 約 1h 程度に短縮予想 (before 27h)。

### Not changed
- seq 系 (`setup`/`hold`/`recovery`/`removal`/`min_pulse_width_*`/`rising_edge`/`falling_edge`/`clear`/`preset`) は `tdelay_init` 等を従来通り `sim_d2c_max` (= 6 ns 等) に維持。
- `sim_end` は autostop で実質関係ないため修正なし。

---

## [0.9.14a04] 2026-05-11

Alpha pre-release toward `1.0.0`. Closes ISS-00073 by adding the BUFZ / INVZ A3-scope `internal_power`: pin(Z) related:EN (no when), pin(EN) when:"!I"/"I", and pin(I) when:"!EN". Output structure now matches orig liberty fully for tri-state buffer/inverter cells.

### Added
- `charao/script/mylogic_comb_tristate.py`:
  - BUFZ / INVZ three_state_enable arc に `power_tout` を併記 — `internal_power(related:"EN")` を orig 構造のまま出力。
  - pin(EN) when:"!I" / when:"I" の `power_tin` MyExpectCell 4 entries (rise/fall × 2 conditions)。
  - pin(I) when:"!EN" の `power_tin` MyExpectCell 2 entries (rise/fall)。
- `sample/target/gf180/fd/mcuC7t20240817/std_comb.jsonc`: BUFZ/INVZ 全 14 セルの `template_kgn` に `["power_tin","10x0","d000"]` を追加。

### Changed
- `sample/target/gf180/fd/mcuC7t20240817/config_lib.jsonc`: `sim_pullres_std_disable` を 100000 (= std_enable と同値) に override。 std セルの三相態 disable arc では internal driver と pullres が直接競合しないため、 enable と同じ pullres 値で十分。

### Verified
- BUFZ_1 full INDEX:
  - timing matched 4 groups / 440 pt (diff avg ≈ -0.09 ns、 既存系統誤差レベル)。
  - power (output, active arc) matched **4 groups / 400 pt** (新規 related:"EN" の 200 pt 追加)。
  - power (input, stable state) matched **4 groups / 40 pt** (新規 ISS-00073 範囲、 orig との match を確立)。
- 14 セル INDEX 0/9 一斉実行: 0 spice failures。 timing matched 56 groups / 6160 pt、 power output 56 groups / 5600 pt、 power input 28 groups / 280 pt。
- 14 セル full INDEX: scheduled separately (post-tag verification)。

### Remaining diff avg notes
- diff avg は既存の charao 系統誤差レベル (ISS-00075) と同オーダー (~ -0.1〜-0.2)。
- 個別に大きいズレ点 (pin EN slope=0.02 fall: charao 0.03 vs orig 0.17、 pin I rise: charao 正 vs orig 負) は ISS-00075 で深堀り対象。

---

## [0.9.14a03] 2026-05-08

Alpha pre-release toward `1.0.0`. Adds full tri-state / bus-keeper cell support: HOLD bus keeper (ISS-00069) and BUFZ / INVZ tri-state buffer/inverter all 14 cells (ISS-00066) with three_state_enable / three_state_disable timing arcs.

### Added
- `docs/SPEC_three_state.md`: developer-facing specification for tri-state / bus-keeper cell characterization. Covers Liberty output structure (biport vs output direction), `mylogic_*.py` logic_dict and cell-entry `oe_infos` rules, MyExpectCell patterns for active / enable / disable arcs, charao internal flow (dispatch / tb / pullres), and a step-by-step porting guide for new PDKs.
- `charao/script/mylogic_comb_tristate.py`: HOLD / BUFZ / INVZ logic definitions including three_state_enable / three_state_disable arc MyExpectCells.
- `delay_disable` template kind: 1D (10x0, slope only, load-independent) template for `three_state_disable` arc. Added across `myItem.py`, `myLogicCell.py`, `myLibrarySetting.py`, `myConditionsAndResults.py`, `charao_run.py`, `myExportDoc.py`, plus `delay_disable_10x0_d00` entry in `config_lib.jsonc`.
- `sample/target/gf180/fd/mcuC7t20240817/std_comb.jsonc`: 14 cell entries (`bufz_1/2/3/4/8/12/16`, `invz_1/2/3/4/8/12/16`) with `oe_infos` (NI_N / NI_P internal gate signals) and HOLD entry.
- `sim_pullres_std_enable` / `sim_pullres_std_disable` / `sim_pullres_io_enable` / `sim_pullres_io_disable` (`myLibrarySetting.py`): cell-type-aware pullres for three_state arcs (defaults: 100k / 0.1 / 100 / 1).

### Changed
- `charao/script/charao_run.py`:
  - `runSpicePowerTinSingle`: estart/eend now computed as absolute time (`_t_in1 + _tdelay_rel`) so the VREL transition window is covered for biport input pins (HOLD).
  - three_state dispatch generalized to `startswith("three_state_")` (no `_c2i` suffix required).
  - 1D template fallback: `delay_disable` accepts empty `index_2` and uses `[0.0]` as a single load corner.
- `charao/script/myConditionsAndResults.py`: dispatch generalized; `set_lut` accepts `delay_disable` kind.
- `charao/script/myExportLib.py`:
  - biport block emits `three_state` via `replace_by_portmap` so cell-side condition expressions (e.g. `(!i1)`) resolve to portmap'd port names (`(!EN)`).
  - output pin block now emits `driver_type` and `three_state` attributes from `logic_dict`.
- `charao/script/myExportDoc.py`: handles 1D template (empty `index_2`) when emitting three_state markdown tables.
- `charao/script/myTbParam.py`: `pullres` selection now branches on `h.mlc.isio` to pick std vs io variants.
- `charao/script/myLogicCell.py`, `myLibrarySetting.py`, `myItem.py`: `delay_disable` added to literal lists, dicts, and template-line scaffolding.
- `sample/target/TRIP62/LR/STDIO_24R03/config_lib.jsonc`: replaced legacy `sim_pullres_enable` / `sim_pullres_disable` with the new four-key form (std/io × enable/disable).

### Verified
- HOLD: full INDEX, all corners, 0 spice failures. Liberty `pin(Z)` matches orig structurally (direction:inout / function:Z / driver_type:bus_hold / three_state:"1" / internal_power power_tin 1D fall+rise).
- BUFZ_1 / INVZ_1 INDEX 0,9 + full INDEX:
  - 3 timing arcs all emitted with correct sense / type / template (combinational 2D, three_state_enable 2D, three_state_disable 1D).
  - timing matched 440 points; diff avg ≈ -0.09 ns (existing systematic offset, not specific to tri-state).
- BUFZ/INVZ all 14 cells: full INDEX run with 0 spice failures (compare run scheduled separately).

---

## [0.9.14a02] 2026-05-04

Alpha pre-release toward `1.0.0`. Adds the developer-facing internal_power specification document and a direction-split power compare utility.

### Added
- `docs/SPEC_internal_power.md`: developer-facing specification of charao `internal_power` handling: Liberty conventions, `meas_types` schema, mylogic entry rules for `power_tin`, sim path (`meas_energy=5`), CSV extraction (1D-aware), and verification guidelines. Linked from `README.md`.

### Changed
- `util_compare_lib_csv.py`: split `power.csv` compare by pin direction:
  - `=== power (output pin, active arc) ===`: rows with `related_pin != ""` (charao `power_tout` and IO `power_c2c` etc.).
  - `=== power (input pin, stable state) ===`: rows with `related_pin == ""` (charao `power_tin`).
  - Each section reports its own `matched groups` / `missing groups` / `matched points`.

### Verified
- AOI21_1 with `--keep_zero_new --cell gf180mcu_fd_sc_mcu7t5v0__aoi21_1` (INDEX 0/9):
  - timing: 12 matched / 8 missing (charao emits default block in addition to active arcs; orig has active arcs only).
  - power (output pin, active arc): **10 / 0 missing**.
  - power (input pin, stable state): **14 / 0 missing** (matches orig vendor exactly: A1x3 + A2x3 + Bx1 stable states x 2 directions).
- INV_1: power (input pin, stable state): 0 / 0 (no `power_tin` needed and orig has none).

---

## [0.9.14a01] 2026-05-04

This is an alpha pre-release toward `1.0.0`. Intermediate alphas (`0.9.14a01`, `0.9.14a02`, ...) are pushed on `feature/1.0.0` branch for diff visibility. Final release will be tagged `1.0.0` and merged to `main`.

### Added
- **Phase A2: `internal_power` separation by pin direction (power_tout / power_tin)**:
  - `meas_types` field becomes mandatory in MyExpectCell (`list[str]`, external input). `meas_type` is now internal-only (`init=False`, set per loop iteration in `runExpectation` via `set_meas_type()` setter).
  - Rename template `kind=power` to `kind=power_tout` (output pin, 2D: slope x load).
  - Add new template `kind=power_tin` (input pin, 1D: slope only, no output load).
  - Split `runSpicePowerMultiThread` into `runSpicePowerToutMultiThread` / `runSpicePowerTinMultiThread`.
  - Split `runSpicePowerSingle` and `genFileLogic_PowerTrial1x` into Tout / Tin variants.
  - `runSpicePowerTinSingle` uses `meas_energy=5` (new): autostop disabled, `energy_start`/`energy_end` `.MEASURE TRAN` skipped, `tsim_end` fixed to input transition window, `estart`/`eend` assigned directly from arguments (no SPICE measurement).
  - tb_template: add `meas_energy=5` branches.
  - `util_extract_lib_csv` extended for 1D tables (input pin internal_power CSV extraction).
  - `myExportLib.py`: emit `internal_power () { when:"..."; fall_power(...) rise_power(...) }` inside input pin blocks (related_pin omitted = Liberty default of input pin).
- **mylogic power_tin entries (2,030 total) auto-generated**:
  - comb_base: AND/OR/NAND/NOR 2/3/4-input + MUX2 (11 logics, 324 entries).
  - comb_complex: AOI21/22/211/221/222, OAI21/22/31/32/33/211/221/222, MUX4 (14 logics, 1,706 entries).
  - Generators: `tmp/insert_power_tin.py`, `tmp/insert_complex.py` (git-untracked, temporary).
- **ADDH/ADDF (ISS-00068, multi-output adders)**: 6 cells (addh_1/2/4 + addf_1/2/4) ported into `mylogic_comb_complex.py`, registered in `std_comb.jsonc`.
- **ANTENNA cell**: registered in `std_comb.jsonc`, `.model_gf180_TT.sp` includes `diode_typical` model.
- `debug_run.sh`: auto-activate venv at top (for claude-code invocation).

### Changed
- `myExportLib.py` / `myExportDoc.py`: replace `startswith("power")` with explicit enumeration (`power_tout`, `power_c`, `power_i`, `power_tin`) to avoid mixing input/output pin power.
- `std_comb.jsonc`: add `["power_tin","10x0","d000"]` template_kgn only to cells that need input pin internal_power (AND/OR/NAND/NOR, MUX, AOI/OAI families - 81 cells). Cells without input pin internal_power in orig vendor (INV/BUF/clkinv/clkbuf/DLY/TIE/ANTENNA/XOR/XNOR/ADDH/ADDF - 62 cells) are excluded.

### Fixed
- Bug: `mylogic_comb_complex.py` had 716 entries with `meas_types=["delay"]` only; corrected to `["delay","power_tout"]` (active arc was missing power_tout sim trigger except in AOI21).
- ADDH `ports_dict` key order must match SPICE subckt port order (`A B CO S`, not `A B S CO`); fixed to avoid `Pin Name missmatch` error.

### Removed
- ISS-00071 (filler/endcap/fillcap cells): closed as out-of-scope (not handled by STA/synthesis, charao does not target these).

### Verified
- INV / AND2_1 / AOI21_1: input pin internal_power `when` expressions match orig vendor exactly (AOI21_1 has 7 stable states: A1x3 + A2x3 + Bx1).
- comb_base 25 + comb_complex 14 cells (INDEX 0/9): SPICE failures 0, baseline regression OK.

### Known Issues
- Verilog output: `\`timescale` is inconsistent across modules (IEEE 1800-2017 violation; only addf_1 has it). Will be addressed in a later alpha.
- Full-grid compare against orig vendor (INDEX full grid) is not yet executed; planned before `1.0.0` final release.

---

## [0.9.14] 2026-04-26

### Added
- **複合セル mylogic 拡張（K4 既知 14 種別 + XOR3/XNOR3 計 16 セル、ISS-00064）**：1118 entries 実装。
  - AOI21/22/211/221/222、OAI21/22/211/221/222/31/32/33、MUX4、XOR3、XNOR3
  - 試走 0 failures、`tmg_when` same-group 省略（v2 形式）で 4 入力以上の AOI/OAI で timing matched 0→856 に大幅改善。
- `tmp/gen_logic_entries.py`：5 入力以上の複合ゲート entries 自動生成スクリプト（git 管理外、テンポラリ運用）。
  - truth table から active sensitization を抽出、`groups` フィールドで same-group 入力を `tmg_when` から省略。
- `sample/target/gf180/fd/mcuC7t20240817/std_comb.jsonc` に 14 セル直接登録（複合ゲートを `ports_dict` で orig SPICE subckt に mapping）。

### Changed
- **`mylogic_base.py` を 4 ファイルに分割**：
  - `mylogic_comb_base.py`（INV/BUF/AND/OR/NAND/NOR/XOR2/XNOR2/MUX2/XOR3/XNOR3 + lr_mux primitive）
  - `mylogic_comb_complex.py`（AOI/OAI/MUX4 系 14 種別）
  - `mylogic_seq.py`（DFF + lr_dff primitive）
  - `mylogic_io.py`（IO セル：P_VDD/P_VSS/P_ANA1/P_IP_*/P_IX_*）
- `charao.py`：4 module を merge する仕組みを追加（重複 logic 名は ERR、primitive は連結）。

### Removed
- `std_comb_debug.jsonc` 運用を廃止（プロトタイプ検証も本流 `std_comb.jsonc` に直接登録、`--cells_only` で対象を絞って試走）。
- `mylogic_base.py`（4 分割により役割完了）。

### Known Issues
- 複合ゲートの power matched は orig の全 state 展開慣習との差で完全 matched 不可 → ISS-00065（timing/internal_power 分離）で長期解決。
- 残対応：tristate（ISS-00066）/ clkbuf（ISS-00067）/ adders（ISS-00068）/ delay（ISS-00069）/ 順序（ISS-00070）/ filler（ISS-00071）。

## [0.9.13] 2026-04-17

### Fixed
- `.option rshunt=1e9` をコメントアウト。5V/1GΩ=5nA の人工電流が leakage を 330 倍過大にしていた。
- `.option gmin=1e-10` をコメントアウト。5V×0.1nS=0.5nA の人工電流が leakage に混入していた。
- `.option abstol=1e-11` をコメントアウト（ngspice デフォルト使用）。
- `.option autostop` を energy2/3/4 で無効化。leakage テストベンチで `.meas` が `out of interval` で失敗していた問題を解消。
- leakage テストベンチの `timestep_tmax` を `tsim_end*0.1` で上限キャップ。
- `charao_run.py:474` energy2 の `tsim_end` を `eend + 1ns` → `max(eend, estart + tslew_rel) + 1ns` に変更（2026-04-23）。組合せセル + 遅 slope で VREL midpoint が VOUT 完了 (`energy_end`) より後に来るケース（xor3_1 / inv_1 等で再現）の `prop_in_out` / `setup_in_rel` / `hold_rel_in` measure 失敗を解消。VREL 完了時刻 (`_t_rel1 ≈ estart + tslew_rel`) を sim 区間に包含。

### Changed
- pleak 計算式を全端子（VDD/VSS/VNW/VPW）対応に変更。
  `pleak = max(p_supply, p_absorb)`、`p_supply = i_vdd*(VDD-VSS) + i_vnw*(VNW-VPW)`。
  符号付き（abs 不使用）でエネルギー回生を表現可能。
- `i_vnw_leak`, `i_vpw_leak` の `.meas` を energy2/4 と leakage テストベンチに追加。

### Added
- `util_compare_lib_csv.py`: `--interpolate` 時の部分ラン検出ガード追加。
- `debug_run.sh`: `COMPARE_INTERPOLATE` 環境変数追加（0: off、1: on）。
- `debug_run.sh`: `grep -c` の `|| true` 修正（set -e 対策）。
- `myExpectCell.py`: `timing_default: bool = False` field 追加（2026-04-23）。Liberty default block 生成の on/off を verilog `ifnone` マーカー（`;;`）から独立制御。
- `myExportLib.py`: timing/power block 出力時、group 内に `timing_default=True` のエントリがあれば **when なし default block を自動生成**。STA/synthesis ツール互換性向上。
- `mylogic_base.py`: AND2/3/4, OR2/3/4, NAND2/3/4, NOR2/3/4 の delay entries 72 件に `tmg_when`（active sensitization）と `timing_default=True` を追加。orig との power arc match 向上（single-when missing 21,600 → 14,760、-32%）。

### Changed
- `mylogic_base.py` / `mylogic_user.py`: `specify=";;"` マーカーの再配置（Verilog LRM 準拠）。
  - **削除**（全 state 網羅セル、`ifnone` は redundant）：XOR2/XNOR2/MUX2/XOR3 の `;;` 15 件 → `;` へ戻す。
  - **追加**（補集合ありセル、`ifnone` で state cover）：AND/OR/NAND/NOR の fall entries 36 件に `;;` 付与。
  - 併せて全対象セルの最後のエントリに `timing_default=True` を付与（Liberty default block 生成）。

## [0.9.12] 2026-04-16

### Fixed
- internal_power 計算を min-rail 方式に変更（`min(|Q_vdd|, |Q_vss|) × Vdd`、libretto 互換）。
  従来の `|Q_vdd| × Vdd - Q_out × Vdd` は PMOS I²R 損失を含み STA switching と二重計上になっていた。
- `e_load` 計算を Liberty 仕様に修正（`× energy_meas_high_threshold_voltage` → `× vdd_voltage`）。
- テストベンチの load cap (`C0`) 接続先を `VSS_DYN` → 理想 GND (`0`) に変更。
  `I(VSS_DYN)` に cap 充放電電流が混入し `Q_vss` 測定が不正確だった問題を解消。
- `.option` から `reltol=1e-2` を削除（ngspice デフォルト `1e-3` を使用）。

### Added
- `util_compare_lib_csv.py` に `--interpolate` オプション追加。
  orig と charao で load グリッドが異なる場合に 2D bilinear 補間（線形外挿）で全点比較可能。
- `util_make_templates_from_new.py` 新規追加。
  Cin-fanout 方式で index_1/index_2 を生成し、orig .lib 不要で templates セクションを作成。

### Changed
- `util_make_templates.py` を `util_make_templates_from_origin.py` にリネーム。
- `debug_run.sh`: compare に `--interpolate` 追加。
  `MODE=local` で `python3 -m charao.script.charao` を使用（pip 版と分離）。

---

## [0.9.11] 2026-04-15

### Fixed
- energy2 を含む全セルで ngspice の `Timestep too small` 収束失敗を解消。
  `temp_testbench.sp.jp2` の `.option` に `gmin=1e-10 abstol=1e-11 rshunt=1e9 reltol=1e-2`
  を追加し、ill-conditioned matrix を広く救済。`rshunt=1e9` が決定打。
  2026-04-15 の gf180 91 セル × 2×2 コーナー検証で `Failed to launch spice` が 0 件。

### Changed
- `charao_run.py` の `.tran` タイムステップ算出ロジックを全面刷新：
  - `timestep_tstep = min(slope * 0.0099, simulation_timestep)`（従来の floor から ceiling へ）
  - `timestep_tmax = 20 * timestep_tstep`（delay / energy1 / setup / hold / passive）
  - `timestep_tmax = 4 * timestep_tstep`（energy2 のみ、`.tran` 終端着地対策）
  - 旧式の `slope/5` / `100×simulation_timestep` の min 制約は撤廃
  - 全 7 箇所（delay / power / setup_trial / setup / hold_trial / hold / passive）に適用
- `sample/target/gf180/fd/mcuC7t20240817/config_lib.jsonc`:
  - `simulation_timestep` を 1.0（ns、上限キャップとして機能）
  - `sim_segment_timestep_min` を 0.001（ns、setup/hold bisection 用、独立パラメータ）

---

## [0.9.10] 2026-04-15

### Fixed
- energy2 測定で最小 slew (slope=0.02 ns) 時に ngspice が `Timestep too small`
  （`vrel#branch` / `vhigh#branch` / `vlow#branch`）で abort する問題を修正。
  `charao/script/temp_testbench.sp.jp2` の `.option` 行に `gmin=1e-10 abstol=1e-11 rshunt=1e9`
  を追加することで、`.tran` 終端着地時の ill-conditioned matrix による数値発散を回避。
  `rshunt=1e9` が決定打。2026-04-14 の gf180 91セルフルランで発覚した spice エラー
  （energy2 系の `Failed to launch spice`）を解消。

### Changed
- `sample/target/gf180/fd/mcuC7t20240817/config_lib.jsonc`:
  `simulation_timestep` を 0.0001 → 0.0005、`sim_segment_timestep_min` を 0.001 → 0.0005
  に変更（最小 slew の約 1/40 目安）。実測で 0.0005 は全セル通過、それ未満への細分化は
  不要と判明。

---

## [0.9.9] 2026-04-14

### Fixed
- 入力 PWL ランプ時間の算出を orig `.lib` の `slew_derate_from_library` 規約に合わせて修正。
  `charao_run.py` でテンプレート `index_1` を「物理 threshold 区間（slew_lower→slew_upper）の時間」
  と解釈し、`index_1 / (logic_threshold_high - logic_threshold_low)` で全幅（0–100%）ランプ時間
  に換算するようにした。新ヘルパー `_tslew_from_template()` を 8 箇所に適用
  （組合せ delay/power、順序 setup/hold、three-state 系）。出力 transition は補正なしで
  そのまま書き出す（ルール：物理 threshold 区間の時間、derate 補正は書き出し時に入れない）。

### Added
- `slew_derate_from_library` フィールドを `MyLibrarySetting` に追加（デフォルト 1.0）。
  GF180 用 `config_lib.jsonc` には値 `0.5` を設定。`myExportLib.py` の `.lib` ヘッダ出力を
  ハードコード `1` から config 参照に変更。

### Changed
- `util_compare_lib_csv.py` の集計表示を ratio ベースから diff ベースに刷新
  （`diff avg / sigma / min / max`）。理由：ratio は orig 小値除算で暴れて本質を隠し、
  系統的オフセット（定数バイアス）を見落としやすい。per-point CSV から `ratio` 列を削除、
  `orig==0` のスキップも撤廃。
- サマリファイル出力を追加：`--out_csv <path.csv>` 指定時、同じ内容を `<path.summary.txt>`
  にも書き出す。対話での結果共有を容易にするため。

---

## [0.9.8] 2026-04-13

### Fixed
- Fix `.MEASURE TRAN` `TD={_t_rel0/_t_clk3}` by adding `-2*_timestep` offset: prevents
  `out of interval` failure of `energy_start` WHEN clause at slope=0.02ns, which previously
  blocked ngspice autostop and extended SIM runtime up to 3838s per run. Max SIM time now
  44s (about 87x faster) with zero MEASURE errors across full inv_1 run (600 .lis)
- Remove ngspice `.lis` unit ambiguity on compare: `util_extract_lib_csv.py` now parses
  `time/voltage/current/leakage/energy` units from .lib header and normalizes CSV output
  to canonical units (ns / pF / V / mA / uW / pJ). `energy_unit` is derived from
  `V × A × s` when not declared (standard Liberty behavior)

### Changed
- Rename CLI options `--only_template_index1` / `--only_template_index2` to
  `--template_index1_only` / `--template_index2_only` for consistency with `--cells_only`
  / `--measures_only`. Internal `MyLibrarySetting` field names also renamed
- `sample/target/gf180/fd/mcuC7t20240817/config_lib.jsonc`: switch `leakage_power_unit`
  from `pW` to `uW` and `energy_unit` from `fJ` to `pJ` to match original GF180 .lib
  convention (makes CSV values directly comparable without unit scaling)
- `util_extract_lib_csv.py`: CSV column names now carry parenthesized units
  (`index1 (ns)`, `index2 (pF)`, `value (ns)`, `value (pJ)`, `leakage_power (uW)`);
  single source of truth via `UNITS_IN_CSV` dict

### Added
- `charao/script/util_compare_lib_csv.py`: compare two CSV directories produced by
  `util_extract_lib_csv.py`. Uses numpy.interp for 2D bilinear interpolation to evaluate
  the new side on the original grid, and reports ratio/abs_diff statistics grouped
  by `table_type` (timing) and `rise_fall` (power). Optional `--out_csv` writes
  per-point comparison rows
- `charao/script/util_extract_sim_time.py`: scan `work/*.sp.lis` and extract SIM time,
  data rows, autostop status, and error count to `rslt/sim_time.csv`. Useful for
  SIM speed regression and bottleneck analysis

## [0.9.7] 2026-04-12
### Fixed
- Fix internal energy calculation for fall transition: remove conditional guard on e_load;
  use signed Cload energy (e_all - max(e_load, 0)) to correctly handle fall/rise asymmetry
- Remove `rm -rf` after tar in compressFiles: rm is blocked on remote server

### Added
- Add charao/script/util_extract_lib_csv.py: extract leakage/power/timing tables from Liberty .lib
  to CSV for reference comparison (supports single file and multi-corner directory modes)

## [0.9.6] 2026-04-11
### Added
- Add `--template_index1_only` / `--template_index2_only` options: limit simulation to specified index positions (0-based) for debug/fast-check use (renamed from `--only_template_index1/2` for consistency with `--cells_only` / `--measures_only`)

## [0.9.5] 2026-04-11
### Added
- Add GF180 support: sample/target/gf180/ with config_lib.jsonc and std_comb.jsonc (inv_1)
- Add `spiceinit` field to MyLibrarySetting: generates .spiceinit from config_lib.jsonc (e.g. `set ngbehavior=hsp`)
- Add `energy_unit` declaration to .lib header output (prevents EDA tools from misinterpreting fJ values as nJ)
- Add `i_vnw_leak` measurement to leakage SPICE template (temp_testbench.sp.jp2)

### Fixed
- Fix leakage power for I=1 state: include I(VNW_DYN)*VNW in pleak calculation (PMOS body-drain junction current was ignored, causing ~0 pW for I=1)
- Fix SyntaxWarning in myExportDoc.py: invalid escape sequence `\c` → `\\c` in `\clearpage`
- Fix GF180 model loading: use `.lib typical` instead of individual sections to include fets_mm subckt wrappers

## [0.9.4] 2026-03-27
### Added
- Add tests/test_e2e.py: E2E test for OSU035/INV_1X/leakage via lrPymRPC
- Add tests/conftest.py: E2E fixtures, lrPymRPC runner, .lib parser
- Add pytest.ini: --tb=short, --capture=tee-sys, lrpymrpc_verbose option
- Add tests/fixtures/std_comb_leakage_inv/expected.yaml: expected values for P2-0 scenario
- Add test_log/ output: test_e2e.log and per-scenario lrpymrpc.log
- Update tests/TEST_PLAN.md: reflect E2E infrastructure completion and SKY130 migration plan

## [0.9.3] 2026-03-26
### Added
- Add pytest to dev dependencies in pyproject.toml
- Add tests/test_myFunc.py: unit tests for f2s_ceil()
- Add tests/test_myLibrarySetting.py: unit tests for update_mag() / update_threshold_voltage()
- Add tests/TEST_PLAN.md: test plan including E2E strategy via lrPymRPC

## [0.9.2] 2026-03-26
### Fixed
- Fix bare `except:` to `except subprocess.CalledProcessError` with `my_exit()` in myLibrarySetting.py
- Fix typo `lunch` → `launch` in myLibrarySetting.py
- Add `my_exit()` to `except` clause in charao.py for proper error termination

## [0.9.1] 2026-03-26
### Fixed
- Fix typo in myLibrarySetting.py: `supress_debug_msglower()` → `supress_debug_msg.lower()` (ISS-00001)
- Remove undefined variable `nval` from error messages in myConditionsAndResults.py (ISS-00002)
- Change `[DEBUG]` to `[INFO]` in charao_run.py for stable operation monitoring (ISS-00003)
- Fix duplicate condition `self.cell == None` → `self.logic == None` in myLogicCell.py (ISS-00004)
- Replace `split('/')` with `pathlib.Path(...).name` in myFunc.py for Windows compatibility (ISS-00005)
- Remove dead comment code `#debug` / `#print(targetLib.templates)` in charao.py (ISS-00006)

## [0.9.0] 2026-01-24
### Changed
- Support --mylogic_user option for user-defined logic_dict().

## [0.8.5] 2026-01-10
### Changed
- Change default result directory to ./rslt.

## [0.8.4] 2025-12-18
### Changed
- Debug .lib output for TIE0/TIE1 cell.

## [0.8.3] 2025-12-11
### Changed
- Support TIE0/TIE1 cell(leakage).

## [0.8.2] 2025-12-04
### Changed
- Support ANTENNA cell(passive/leakage).

## [0.8.1] 2025-11-15
### Changed
- Support -w option to change work directory.

## [0.8.0] 2025-11-15
### Changed
- Change PATH to jsonc(target/[fab_process]/[cell_vendor]/[cell_revision]).
- Support Multi JSONC file for same [cell_group].
- Change JSONC format (Set spice_path in each [cell_group].jsonc).

## [0.7.6] 2025-11-13
### Changed
- Add build-stamp by -b option to output files(.lib, .md, .v).

## [0.7.5] 2025-11-13
### Changed
- Add revision in Verilog output.

## [0.7.4] 2025-11-11
### Changed
- Fix specify/libery CONDITION for MUX2.

## [0.7.3] 2025-11-06
### Changed
- Fix specify (recovery) and timescale in Verilog output.

## [0.7.2] 2025-10-24
### Changed
- DFFのverilog出力内容の訂正。

## [0.7.1] 2025-10-24
### Changed
- charao/target/OSU035/.model_OSU035_xx.spにて、spiceモデルのincludeパスを 実行場所(work)からの相対パスへ変更。

### Changed
- プロジェクト名を`charao_prj`へ変更
- モジュール化対応

## [0.6] 2025-09-01
### Changed
- ツール名を`charao`へ変更

## [0.5] 2025-xx-xx
### Added
- 複数のtemplateに対応
- パラメータ設定ファイルとして、`jsonc`を採用
- テストベンチの雛形生成に、`jinja2`を採用

## [0.2] 2025-xx-xx
### Added
- 複数の slope / load に対応

## [0.1] 2025-06-23
### Added
- `OriginalProject` (https://github.com/snishizawa/libretto) からフォーク
- SPICEモデルのパスを絶対パスに対応
