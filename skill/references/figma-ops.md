# Figma操作の必須ルール(use_figma)

use_figmaはFigmaファイル内でJavaScript(Plugin API)を実行する。以下はFigma公式figma-useスキルの要点をパンフレット制作向けに凝縮したもの。環境に公式figma-useスキルがあればそちらを正とする。

## 基本ルール

1. **少しずつ作る。** 大きな操作は複数呼び出しに分割し、1ステップごとに検証する
2. 結果は`return`で返す(`console.log`は返らない)。作成・変更した全ノードIDを`return { createdNodeIds: [...], mutatedNodeIds: [...] }`で返し、次の呼び出しで参照する
3. 素のJavaScriptで書く。トップレベル`await`と`return`が使える。async即時関数で包まない。`figma.notify()`は使えない
4. 色は0〜1の範囲。`{r: 1, g: 0, b: 0}`が赤
5. fills / strokesは読み取り専用配列。複製→変更→再代入:
   ```js
   const fills = JSON.parse(JSON.stringify(node.fills));
   fills[0].color = { r: 1, g: 0.95, b: 0.85 };
   node.fills = fills;
   ```
6. エラー時は即リトライしない。失敗したスクリプトは何も実行されていないので、エラー文を読み、直してから再実行する
7. すべてのPromiseに`await`を付ける(付け忘れは無言の失敗になる)
8. ページ直下の新規ノードは(0,0)を避け、既存ノードの右側など空き位置に置く

## テキスト編集の定型

フォントを読み込まずにテキストを触ると必ずエラーになる。定型: フォント読み込み→await→変更→ID返却。

```js
const node = await figma.getNodeByIdAsync("123:45");
const segments = node.getStyledTextSegments(["fontName"]);
for (const seg of segments) {
  await figma.loadFontAsync(seg.fontName);  // 現在のフォントを取得して読む。決め打ちしない
}
node.characters = "新しい文言";
return { mutatedNodeIds: [node.id] };
```

- 日本語フォントのスタイル名が不確かなら、先に`await figma.listAvailableFontsAsync()`で確認する
- **loadFontAsyncが失敗する(テンプレのフォントが環境にない)場合**は、同等ウェイトのNoto Sans JPに置換して続行し、置換した旨を利用者に報告する。対応例: Source Han Sans JP の Regular/Medium/Bold/Heavy → Noto Sans JP の Regular/Medium/Bold/Black。置換時はそのテキストノードのfontNameを新フォントに設定してからcharactersを変更する
- 文言差し替えではフォント・サイズを変えない。テンプレートのテキストスタイルを崩さない
- 文字数が元より大幅に増えたら、差し替え後にget_screenshotであふれを確認する

## ページ

- 切り替えは`await figma.setCurrentPageAsync(page)`。同期代入はエラー
- 1回の呼び出しで切り替えは1回まで。ページ状態は呼び出しごとに先頭ページへリセットされる
- 素材ページ→作業ページの複製は、素材ページでclone→作業ページにappendChildを1スクリプト内で行う(切り替え1回で済む)

## レイアウト

- 関連する子要素を並べる容器は`figma.createAutoLayout()`。絶対座標の手並べは文字量の変化で崩れる
- 子の`layoutSizingHorizontal/Vertical`(`'FIXED'|'HUG'|'FILL'`)は、親にappendChildしてから設定する
- フレーム自身の`primaryAxisSizingMode / counterAxisSizingMode`は`'FIXED'|'AUTO'`。子用の値と混同しない
- テンプレート複製ベースでは既存構造を尊重し、構造変更は最小限にする

## 画像

use_figma内から外部URLの画像取得はできない。手段は2つ:

**手段A(本線): ファイル内の既存画像を複製する。** 「素材」ページの画像をcloneするか、既存ノードの`imageHash`を使い回す:
```js
node.fills = [{ type: 'IMAGE', scaleMode: 'FILL', imageHash: '既存ノードのhash' }];
```

**手段B: upload_assetsツール。** チャット添付の画像を取り込める環境でのみ有効。失敗したらリトライせず手段Aに切り替え、「素材」ページへのドラッグ&ドロップを案内する。

SVGは`figma.createNodeFromSvg('<svg>...</svg>')`で直接生成できる。雲・帯・バッジ等の装飾はこれで自作してよい。

## 回転・面付けフレームへの配置

冊子テンプレートは面付けのため180°回転した面を含む。回転した親の中ではx/yの直接指定が見た目とズレ、新規ノードが逆さ・枠外になる。

- **第一原則: 逆さ面では既存の空欄テキスト・プレースホルダの差し替えで済ませ、新規ノードの追加を避ける**
- 新規追加が必要な場合のみ、`relativeTransform = 親のabsoluteTransformの逆行列 × 目標の絶対変換` で配置する:

```js
function inv(m) {
  const [a, c, e] = m[0], [b, d, f] = m[1];
  const det = a * d - c * b;
  return [[d / det, -c / det, (c * f - d * e) / det],
          [-b / det, a / det, (b * e - a * f) / det]];
}
function mul(A, B) {
  return [0, 1].map(i => [
    A[i][0] * B[0][0] + A[i][1] * B[1][0],
    A[i][0] * B[0][1] + A[i][1] * B[1][1],
    A[i][0] * B[0][2] + A[i][1] * B[1][2] + A[i][2]
  ]);
}
parent.appendChild(node);
// ページ絶対座標(ax, ay)に絶対回転angle(逆さ面に沿わせるならMath.PI)で置く
const t = [[Math.cos(angle), -Math.sin(angle), ax], [Math.sin(angle), Math.cos(angle), ay]];
node.relativeTransform = mul(inv(parent.absoluteTransform), t);
```

- 配置後は必ずget_screenshotで向きと位置を確認する

## 検証

- 1ブロック作業するごとにget_screenshotで対象フレームを取得し、崩れを目視確認する
- 構造の確認(ノード名・階層・ID)はget_metadataを使う。findAllでの全走査を先にしない
