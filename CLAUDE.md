# figma-pamphlet — Claude Code 向けルール

Cicac 乗合タクシー(MITT)パンフレットを Figma MCP で作る Claude スキルの改修リポジトリ。全体像は `docs/PLAN.md`、経緯と決定事項は `docs/context/session-digest.md`、計画書本体は `docs/plan/plan-v5.1.md`。

## 絶対に守ること

- Figma は **複製ファイル fileKey `09Js7rndbabLAoCchqzX9j` だけ**を操作する。本番 `5qm3YRTEUDdb9RxFUI7ECL` は読むのも避ける(URL・fileKey をコードや資料に書くときは複製の方)
- 複製ファイル内でも、`テンプレート` ページ(0:1)の原本フレームと `参照` ページ(6:2)は直接編集しない。改修は作業用ページ(例: `テンプレ改修_作業`)に複製してから行い、検証後に差し替える
- `use_figma` を呼ぶ前に Figma の `figma-use` スキル(`skill://figma/figma-use/SKILL.md`)を読む。1呼び出しでページ切替は1回、返り値は 20KB 以内、`figma.root.findAll` は使わない、フォントは先に `loadFontAsync`、`setPluginData` と `FrameNode.description` への書き込みは不可
- 一時的に作ったノード(計測用 clone など)は try/finally で必ず消す
- 物理サイズは A3 シート・6面(1面 99×210mm)・k = 5.69 px/mm(`docs/prep/physical-size.md`)。しきい値は必ず k から計算し、旧計画の「A4 / k=8.05 / 34px」を使わない
- 秘密情報(Gemini API キー等)はコミットしない。`.env` は gitignore 済み

## 作業の流れ

1. `docs/PLAN.md` → 担当の `docs/briefs/<task>.md` を読む
2. 成果物は指示書のパスへ。結果・所感は `docs/reports/<task>-*.md`
3. 決定・制約は `docs/decisions.md` に追記、`docs/tasks.md` の状態を更新
4. 小さくコミット(作者設定済み)。push は `git push origin main`

## リポジトリ構成

- `skill/` — スキル本体(`SKILL.md`, `references/`, これから `scripts/`)。配布時に `scripts/package.sh` で `.skill` に固める
- `docs/prep/` — Figma 実測(面表・TEXT・フォント・imageHash・色・物理サイズ)
- `docs/plan/` — 計画書 v5.1 と履歴
- `docs/briefs/` — タスク指示書、`docs/reports/` — 実行結果
- `docs/context/` — オーケストレーションセッションの要約と生ログ
