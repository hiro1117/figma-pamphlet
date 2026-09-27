"""描法 abst(抽象グラフィック)のプロンプト。Hiro 提供の英語プロンプト(2026-09-27)を土台に、被写体・アクセント色・比率だけを差し替える。"""

ABST_STYLE = """The most important requirement is the LEVEL OF SIMPLIFICATION.

The subject must be highly abstracted and graphically simplified.

Do NOT draw a detailed illustration.
Do NOT draw realistic anatomy or realistic mechanical detail.
Do NOT carefully render faces, hands, clothing, hair, shoes, or vehicle parts.

Instead, treat the entire subject as a small collection of bold, simple graphic shapes.

{abstraction}

The subject should look intentionally designed and abstract,
not like a realistic subject that has been simplified afterward.

Think:
"graphic shapes representing the subject"
rather than
"an illustrated subject."

STYLE:
- highly simplified editorial illustration
- flat graphic shapes
- limited visual information
- bold areas of solid color
- minimal linework
- clean but slightly organic shapes
- distinctive artistic character
- playful and sophisticated
- slightly quirky
- contemporary
- not cute
- not realistic
- not corporate
- not clip-art
- not a typical Japanese municipal illustration
- no gradients, no texture, no shading, no highlights

COLOR:
Use a restrained, sophisticated palette.
Use {accent} as an accent color.
{palette_note}
{skin_note}Avoid bright generic colors.

COMPOSITION:
{composition}
- centered
- generous negative space
- {aspect} 
- entire subject visible
- do not touch the edges

BACKGROUND:
completely uniform pure green #00FF00.
No environment.
No floor.
No shadow.
No furniture.
No scenery.

No text, logo, license-plate characters, QR code, numbers, watermark or border.
No maker emblem. Do not resemble a real person, a real store, or a real car model.

IMPORTANT:
The final illustration should contain FEWER visual details than a normal flat illustration.

When deciding whether to add a detail, remove it unless it is essential for recognizing the subject or action.

Prioritize:
SILHOUETTE > SHAPE > COLOR > EXPRESSION > DETAIL.

The result should feel like a deliberately abstract graphic artwork, not a detailed illustration."""

PERSON_ABSTRACTION = """ABSTRACTION:
- simplify the human body into large geometric shapes
- simplify the face dramatically
- use only tiny, minimal shapes for the eyes, nose and mouth
- no detailed facial anatomy
- no detailed wrinkles
- no eyelashes
- no detailed eyebrows
- no realistic ears
- hair should be one or two simple solid shapes
- hands should be simple silhouettes with little or no finger detail
- arms and legs should be simple flat shapes
- clothing should be large uninterrupted color shapes
- remove clothing folds, seams, buttons, stitching and fabric texture
- shoes should be simple graphic shapes with almost no detail
- any held object (smartphone, handset, bag) should be a simple recognizable geometric shape

The face should contain only the minimum information necessary to communicate a calm, friendly expression.

The hands should contain only the minimum information necessary to communicate the action.

The clothing should be understood primarily through COLOR, SILHOUETTE and SHAPE,
not through detailed garment construction."""

VEHICLE_ABSTRACTION = """ABSTRACTION:
- simplify the van into a few large geometric shapes (body, roof, windows, wheels)
- windows as one or two flat shapes
- wheels as simple circles
- grille as one simple shape or two lines
- headlights as one simple shape each
- no door handles, mirrors, wipers, badges, trim lines, panel gaps, reflections or chrome
- no driver, no passengers; windows are empty flat shapes
- the taxi roof sign is a small simple shape in the accent color, clearly different from the white roof, with no text

The vehicle should be understood primarily through SILHOUETTE and COLOR BLOCKING,
not through mechanical detail."""

BG_SUBJECT = """Create a single background illustration for a landscape-format picture panel on a pamphlet cover: a quiet, generic rural Japanese landscape with only four elements: (a) a flat single-color sky, (b) one simple gentle ridge line of low hills at about {horizon_pct}% from the top (one solid color, one silhouette), (c) one road coming toward the viewer, (d) a flat single-color ground. Optionally up to three tiny simplified houses or trees near the ridge. No people, no vehicles, no animals, no landmarks, no clouds, no sun, no text.

The bottom 25% must be only road and ground (people and a vehicle will be placed in front later). Above the ridge there is only sky."""

BG_ABSTRACTION = """ABSTRACTION:
- treat the landscape as a few large flat color shapes stacked vertically
- the ridge is one uninterrupted silhouette shape
- the road is one or two simple shapes
- houses and trees, if any, are tiny simple geometric shapes
- no texture, no gradients, no shading, no atmospheric haze
- no outlines, or only minimal uniform outlines"""

SUBJECTS = {
    "person-01": "Create a single full-body illustration of a Japanese woman in her 70s making a reservation for a community ride-share taxi by talking on a smartphone (or a telephone handset). She looks calm and friendly. Her age is suggested by hair color and posture, not by a kimono, a cane or white hair alone.",
    "person-02": "Create a single full-body illustration of a Japanese man in his 70s and his daughter in her 40s standing side by side, the daughter lightly holding his arm, both looking relaxed and friendly. Their age is suggested by hair color and posture, not by a kimono, a cane or white hair alone.",
    "vehicle-01": "Create a single illustration of a white community ride-share taxi. VEHICLE TYPE: a mid-size Japanese minivan / people-mover used as a taxi (tall rounded body, long hood-less front, large windows, a rear sliding door), like a 7-seat family minivan taxi. NOT a kei microvan, NOT a sedan, NOT a bus. Right-hand drive. VIEWPOINT: three-quarter view from the FRONT-LEFT of the car. The car's LEFT side (the passenger side with the sliding door) faces the viewer and fills most of the image; the front of the car points toward the lower-left. No driver and no passengers: all windows are empty flat shapes. COLORS OF PARTS: the whole body INCLUDING THE ROOF is white / warm off-white; the small taxi roof sign (lamp) on top is the accent color {accent} so it clearly contrasts with the white roof; windows are one dark flat color (muted navy); wheels dark; one thin accent stripe on the side. Blank license plate shape. No text on the roof sign.",}
COMPOSITION_BG = "- full-bleed landscape, no margins\n- generous empty sky and ground"

COMPOSITION = {
    "person-01": "- one woman only\n- full body",
    "person-02": "- two people only\n- full body",
    "vehicle-01": "- one vehicle only\n- whole vehicle",
}
ASPECT = {"person-01": "3:4 vertical", "person-02": "3:4 vertical", "vehicle-01": "4:3 horizontal"}


SKIN_NOTE = "Skin: one flat pale pinkish-beige color, exactly #F5CEC1, the same for every character (face and hands). No tan, no peach, no orange skin, no blush, no shading on skin.\n"


def abst_bg_prompt(family_colors, aspect="4:5 vertical", horizon_pct=60):
    body = ABST_STYLE.format(abstraction=BG_ABSTRACTION, accent="", palette_note=family_colors, composition=COMPOSITION_BG, aspect=aspect, skin_note="")
    body = body.replace("Use  as an accent color.\n", "")
    body = body.replace("""BACKGROUND:
completely uniform pure green #00FF00.
No environment.
No floor.
No shadow.
No furniture.
No scenery.""", "This image IS the background scenery; it must fill the whole frame edge to edge.")
    return BG_SUBJECT.replace("{horizon_pct}", str(horizon_pct)) + "\n\n" + body


def abst_prompt(kind, accent_hex, palette_note):
    return SUBJECTS[kind].replace("{accent}", accent_hex) + "\n\n" + ABST_STYLE.format(
        abstraction=PERSON_ABSTRACTION if kind.startswith("person") else VEHICLE_ABSTRACTION,
        accent=accent_hex, palette_note=palette_note, composition=COMPOSITION[kind], aspect=ASPECT[kind],
        skin_note=SKIN_NOTE if kind.startswith("person") else "")
