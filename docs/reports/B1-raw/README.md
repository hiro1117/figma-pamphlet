# B1-raw — B.1 設計時の Figma 読み取り生データ(2026-09-26)

- fileKey `09Js7rndbabLAoCchqzX9j`、ページ「テンプレート」(0:1)。`use_figma` の read-only スクリプトで取得。書き込みなし。
- `face_<frame>.json`: 表紙面グループ(749:6 / 756:6 / 758:5 / 763:2)の全子孫。列は `id, depth, name, type, [x,y,w,h フレームローカル], visible, locked, fills, fontSize`。`direct` はフレーム直下の子。
  - ローカル座標は `absoluteBoundingBox` にフレームの `absoluteTransform` の逆行列を掛けたもの(18:2 の 180° 回転を打ち消してある)。
  - 24:2 の `イラスト:表紙(人物群)` 24:3104 は直下の子までしか展開していない(子孫 335)。
- スクショ: `../B1-shots/orig_<frame>.png`(get_screenshot、maxDimension 2392 = 等倍 1691×2392。18:2 はキャンバス上の見え方=上下逆)。
