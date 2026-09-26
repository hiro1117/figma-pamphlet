# 指示書 E: 第1層チェック preflight.js(最小版)

## 目的
Figma 上のパンフレット制作物フレームを走査し、印刷・可読性の機械的な合否を JSON で返す `use_figma` 用スクリプトを作り、複製ファイルの制作物/テストページでテストする。オペレータには後で ○/✗ 要約だけを見せる(スキル改訂 D で組み込む)。

## 先に読むもの(順番)
1. `CLAUDE.md`, `docs/PLAN.md`
2. `docs/prep/physical-size.md`(k=5.69、折り線、しきい値の px)
3. `docs/prep/text-inventory.md`(系統別の 本文/注記/見出し/電話/CTA 候補表と実名)、`docs/prep/face-table.md`(フレームの回転・面構成)、`docs/prep/fonts.md`
4. `docs/plan/plan-v5.1.md` の 6.5(第1層の表 P1〜P25)と E 章
5. Figma の `figma-use` スキル(use_figma の前に必読)

## 対象
- fileKey `09Js7rndbabLAoCchqzX9j`。テストに使ってよいのは `制作物` ページ(7:2)の既存4案件フレームと `テスト_真四角町_20260914` ページ(664:2)。`テンプレート`(0:1)の原本には書き込まない

## 成果物
- `skill/scripts/preflight.js` — use_figma にそのまま貼れる素の JavaScript(トップレベル await + `return`、async IIFE で包まない)。先頭に CONFIG(しきい値・役割の名前マッピング・対象フレームID配列・ページID・シート種別)。全体 25,000 字以内を目標(上限 50,000)
- `skill/references/preflight.md` — 仕様書: 各チェックの定義・しきい値・判定方法、実行手順(CONFIG の書き方、1回の呼び出しで1ページ)、出力の読み方(○/✗要約の作り方)、既知の限界、スクリプト全文の逐語収録
- `docs/reports/E-test-report.md` — 実行結果(生 JSON 抜粋)、誤検知/見逃しの分析、返り値サイズ、所要時間、次に直す点

## 実装するチェック(最小版)
シート種別 `CONFIG.sheet`: `A3_booklet`(1691×2392 または 2392×1691、k = 短辺px÷297、折り線 縦2本・横1本)| `A4_spot`(794×1123、k = 短辺px÷210、折り線なし)。しきい値は必ず k から計算。

| ID | 内容 | 基準 | 判定 |
|---|---|---|---|
| P1 | 作業寸法 | 冊子 1691×2392 / 2392×1691(±0)、スポット表 794×1123(±0) | ラッパー寸法・PDF実寸は次版 |
| P2 | 文字サイズ | 役割「本文」≥ 12pt(24px)、「注記」≥ 10pt(20px)、全 TEXT 絶対下限 6pt(12px)、白抜き ≥ 12pt | セグメント単位(`figma.mixed` は `getStyledTextSegments(['fontSize','fills','fontName'])`)。値は CONFIG で変更可 |
| P3-a | 文字あふれ | `textAutoResize==='NONE'` の TEXT のみ。0件 | フォントを全ロード → clone → `textAutoResize='HEIGHT'` → 高さ比較(+1px 超で Fail)→ **try/finally で clone.remove()**。`hasMissingFont` は Manual(clone しない) |
| P4 | コントラスト(単色背景) | 本文・注記・電話 7:1、見出し 4.5:1 | TEXT の絶対矩形を 90% 以上覆う可視 SOLID 矩形/フレーム背景のうち最前面と比較。IMAGE/GRADIENT/半透明/未検出は Manual |
| P6 | 折り安全域 | 全 TEXT が折り線から 46px(8mm)以上、折り線をまたがない | 折り線はシート種別と向きから計算。180°回転フレーム(あいとま表紙18:2系)も absoluteBoundingBox なら同じ式 |
| P7 | 仮置き文言 | `/[〇○◯]{2,}|0000|[（(]仮[)）]|ダミー|サンプル|XXX|TODO/` が 0件 | 名前が `サンプル:` で始まるテンプレ要素は CONFIG の除外パターンで外せる |
| P12 | 電話番号 | 役割「電話」の fontSize ≥ 本文中央値×3(倍率は CONFIG) | 「電話」が見つからなければ Manual |

役割の判定(NAME_MAP): 名前が `#本文` `#注記` `#見出し` `#電話` `#CTA` などで始まれば優先。無ければ CONFIG の正規表現(名前と characters の両方)で推定。既定値は text-inventory.md の候補表と実名(「ラベル:見出し」「見出し:」「本文」「注記」「TEL」「℡」、電話番号らしい数字列 `/0\d{1,4}-\d{1,4}-\d{3,4}/`)から決める。判定に使った役割を出力に含める。

## 共通ルール
- 対象フレーム内を `frame.findAll` で1回だけ走査して配列を作り、以後はそれを使う
- `visible===false` の枝、名前 `#tone` `#state` `#config` は除外
- 幾何は absoluteBoundingBox / absoluteRenderBounds。フレームの rotation を出力に含める
- 出力: `{frame:{id,name,w,h,k,rotation,sheet}, checks:[{id, status:'Pass'|'Fail'|'Manual'|'Error', count, items:[{node,name(先頭20字),role,value,limit,fix}], message?}], summary:{fail,manual,pass}}`。items は Fail/Manual のみ、1チェック最大20件、characters は先頭15字。合計 20KB 以内(超えそうなら frames を分ける旨を出力)
- エラーはチェック単位で `status:'Error'` にして続行

## 受け入れ条件
- 制作物ページの4案件(表紙・中面)とテストページのフレームで実行し、結果が 20KB 以内で返る
- 実行後に一時 clone が残っていない(名前で検索して0件)
- 誤検知(問題ないのに Fail)の原因を test-report に列挙し、CONFIG で回避できるものは回避済み
- `docs/tasks.md` の E を更新し、決めた既定値を `docs/decisions.md` に1行追記
