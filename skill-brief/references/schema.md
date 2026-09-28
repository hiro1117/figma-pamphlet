# 依頼票 JSON(`pamphlet-brief/1`)

figma-pamphlet が Step 1 で読む。人が読む Markdown 版はこの JSON から作る(中身を食い違わせない)。

## 1. 値の書き方(Fact)

確かめる必要のある値は、すべて次の形で書く。

```json
{ "value": "050-1792-2310", "status": "確定", "source": "仕様整理書 第9版 §8 電話番号", "note": "10/1 受付開始" }
```

| status | 意味 | パンフへの載せ方 |
|---|---|---|
| `確定` | 資料で決まっている | そのまま載せる |
| `予定` | 案・予定・「概ね了承」 | 載せてよいが、印刷前に確認(引き渡しに載る) |
| `協議中` | 資料が「協議のうえ決定」「To Do」 | 載せない。`open_questions` へ |
| `要確認` | 資料に無い | 載せない。`value` は `null`。`open_questions` へ |
| `推測` | 一般知識からの候補(名所・地形だけ) | 確認が済むまで絵にしない |
| `草案` | こちらで書いた文言 | 確認を取ってから載せる |

`note` と `source` は任意だが、`確定` 以外では `note` に理由を書く。以下で「Fact」と書いた項目はこの形。

## 2. 全体

```text
schema            "pamphlet-brief/1"
meta
  case_name       案件名(figma-pamphlet の `案件/<案件名>`・フレーム名に使う。自治体名・地域名。例 "坂出市")
  created         作成日 YYYY-MM-DD
  revision        1 から。答えを反映するたびに +1
  sources[]       { name, version, date, note }  読んだ資料
  conflicts[]     { field, values:[{ value, source }], adopted, reason }  版・資料で食い違った値
project
  municipality    Fact  自治体名
  operators[]     Fact  運行事業者名(複数可)
  dispatch_center Fact  予約を受ける配車センター・コールセンター
  service_name    Fact  サービス名称(題字。「〇〇号」など愛称があればそれ。業務名は題字にしない)
  purpose         Fact  住民向けに言い換えた目的(1文)
deliverable
  kind            Fact  "booklet"(冊子=表紙+中面)| "single"(単票)
  spot_table      Fact  乗降スポット表を作るか(bool)
  split           Fact  "common"(全エリア共通1種)| "per_area"(エリア別)
  distribution    Fact  配り方(全戸配布・自治会・窓口など)
  schedule        Fact  配布開始・入稿の目安
service
  start_date      Fact  本運用の開始日
  trial           Fact  試験運行の期間と対象(住民が乗れるか)
  registration    Fact  利用者登録の受付開始と方法
  operating_days  Fact  運行日(毎日/平日など)
  closed_days     Fact  運休日(年末年始など)
  areas[]         → §3
  reservation     → §4
  fare            → §5
  rules[]         Fact  利用のきまり(予約のない便は運行しない、区域外どうしは不可、帰りは指定場所以外で降りられる など)
  stops           Fact  乗降場所の一覧 [{ area, name, note }]。無ければ value null・要確認
copy              → §6
assets            → §7
brand
  color           Fact  自治体・事業者のブランドカラー(hex か色名)。指定なしなら value null・status 確定・note「指定なし」
  genai_allowed   Fact  生成AIのイラストを使ってよいか(資料にはまず無い → 要確認)
illustration      → references/illustration.md
open_questions[]  → §8
```

## 3. エリア(`service.areas[]`)

```text
id              英小文字(例 "tohoku")
name            Fact  表記どおり(「東北エリア」)
districts[]     Fact  町名・字名(括弧内の字も落とさない)
coverage        Fact  利用できる区間(区域内のみ/区域外の指定乗降場所まで)
transfer        Fact  乗り継ぎ(路線バス・鉄道。場所と行き先)
destinations[]  Fact  区域外の行き先(坂出中心部・駅・店・病院)
trips_per_day   Fact  便数
timetable
  outbound[]    { time "7:55", from "東北エリア" }  上り(資料の呼び方の「上り」)
  inbound[]     { time, from }                     下り
  status/source 時刻表全体の Fact 属性(時刻ごとには付けない)
capacity        Fact  1便の定員と超過時の扱い
vehicles        Fact  車両の表記(分類は illustration 側)
reservation_override  このエリアだけ締切などが違うときの §4 の差分
```

## 4. 予約(`service.reservation`)

```text
phone
  number        Fact  表記どおり(ハイフン含む)
  hours         Fact  受付時間(曜日・時刻)
  opens_on      Fact  受付開始日
  window        Fact  導入後の受付期間(「7日前〜前日16時」など)。現行の値は note に
  legacy_number Fact  旧番号と移行の扱い(載せるかの判断用)
line
  account_name  Fact  LINE 公式アカウント・アプリの名前
  window        Fact  導入後の受付期間
  qr            Fact  QR の有無と入手先(画像は assets へ)
app             Fact  そのほかのアプリ・Web
cancel          Fact  キャンセルの締切と連絡先
```

## 5. 運賃(`service.fare`)

```text
system          Fact  方式(ゾーン運賃/定額/距離)
table           Fact  金額表 [{ from_zone, to_zone, adult, child, note }]。無ければ要確認
categories[]    Fact  区分(大人・小児・高齢者・障がい者・市民など)と割引
payment         Fact  支払う時点(乗車時/降車時)と方法(現金・QR・回数券)
special[]       Fact  無料デー・免許返納者向けなど(住民に関係するものだけ)
```

## 6. 文言(`copy`)

figma-pamphlet の `fill-text.js` の枠(役割 `#見出し` `#本文` `#注記`、スロット名は系統で違う)に後で当てる。依頼票ではスロット名を書かず、意味で分ける。**すべて `status: "草案"` か、資料・回答に文言があればその出所付き。**

```text
catch            Fact  キャッチコピー(15〜20字、2行まで)
lead             Fact  リード文(60〜80字)
scenes[]         { title Fact, body Fact }  利用シーン 3件(見出し 10字前後・本文 45字前後)
steps[]          { title Fact, body Fact }  使い方 STEP(登録 → 予約 → 乗車 → 支払い など)
notes[]          Fact  注意事項(運休日・予約のない便・区域外どうし不可 など、rules から)
cta              Fact  申込みの呼びかけ(「ご登録・ご予約は LINE またはお電話で」など)
inner_title      Fact  中面タイトル = 地名 + 「乗降スポット」(サービス名ではない)
```

## 7. 素材(`assets`)

各項目 `{ exists: bool|null, where: "入手先・受け取り方", status, source }`。画像そのものは figma-pamphlet 側で素材ページ `案件/<案件名>` に入れる。

`logo_municipality` `logo_service` `line_qr` `map`(乗降場所のピン入り)`photos`(実車・実風景)

## 8. 聞き返し(`open_questions[]`)

```text
id          "Q1" から
field       対象のパス(例 "service.reservation.phone.window")
question    相手に聞く文(やさしい言い方、選択肢があれば添える)
why         パンフのどこに効くか
blocking    true = これが無いと作れない
ask_to      聞く相手の目安(「自治体」「運行事業者」「社内」)。個人名は書かない
```

並べ順は SKILL.md Step 4。

## 9. figma-pamphlet の Step 1 との対応

| figma-pamphlet Step 1 | 依頼票 |
|---|---|
| 1 案件情報 | `meta.case_name` `project.municipality` `project.operators` `project.service_name` |
| 2 作るもの・スポット表 | `deliverable.kind` `deliverable.spot_table` `deliverable.split` |
| 3 載せる内容 | `service.*` `copy.*` |
| 4 ロゴ・QR・地図・写真 | `assets.*` |
| 5 色の指定 | `brand.color` |
| 6 生成AIのイラスト | `brand.genai_allowed` |
| 7 地域名と名所 | `illustration.region` |

figma-pamphlet は `確定` と `予定` を埋まっているものとして扱い、`協議中` `要確認` `推測` `草案` はヒアリングで確かめる。
