# figma-pamphlet(スキル開発リポジトリ)

Cicac 乗合タクシー(MITT)パンフレットを Figma MCP で作る Claude スキル `figma-pamphlet` のソース。

- **Claude Code で作業するときは先に `CLAUDE.md` → `docs/PLAN.md` を読む**
- 計画書(目指すもの / そのために行うこと): `docs/plan/plan-v5.1.md`(Claude Doc の書き出し。原本: https://claude.ai/code/artifact/9ff55393-cd8f-42e0-96e6-33d1f88c8d86)
- 経緯・決定・制約の要約: `docs/context/session-digest.md`(生ログは `docs/context/session-2026-09-26.jsonl`)
- タスク指示書: `docs/briefs/`(E 第1層 / B1 表紙改修 / C ライブラリv0 / D スキル改訂)
- `skill/` — スキル本体(配布時にこのディレクトリを zip する)。`SKILL.md` と `references/`
- `docs/` — 決定事項・タスク台帳・引き継ぎメモ(開発用。配布物には含めない)
- `scripts/package.sh` — `skill/` を `dist/figma-pamphlet_<版>.skill` にパッケージ
- `dist/baseline/` — 改修前(2026-08-20版)のパッケージ

## 作業対象の Figma ファイル

改修中は **複製ファイル**(パンフレット制作 Cicac (Copy) / fileKey `09Js7rndbabLAoCchqzX9j`)だけを操作する。本番(`5qm3YRTEUDdb9RxFUI7ECL`)には触らない。
切り替え箇所は `skill/references/template-and-assets.md` 冒頭の1箇所。配布版では本番URLに戻し、スキルは Step 0 で対象ファイルを1行確認する。

## 配布

```
scripts/package.sh 2026-10
```
できた `dist/figma-pamphlet_2026-10.skill` を Claude Team の組織スキルにアップロードする。
