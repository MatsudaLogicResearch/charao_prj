# CHANGELOG

このファイルは UTF-8 で記述されています。

---

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
