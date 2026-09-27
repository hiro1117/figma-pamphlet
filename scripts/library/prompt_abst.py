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
Avoid bright generic colors.

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
- the driver, if visible, is a single flat silhouette
- the taxi roof sign is a small simple shape with no text

The vehicle should be understood primarily through SILHOUETTE and COLOR BLOCKING,
not through mechanical detail."""

SUBJECTS = {
    "person-01": "Create a single full-body illustration of a Japanese woman in her 70s making a reservation for a community ride-share taxi by talking on a smartphone (or a telephone handset). She looks calm and friendly. Her age is suggested by hair color and posture, not by a kimono, a cane or white hair alone.",
    "person-02": "Create a single full-body illustration of a Japanese man in his 70s and his daughter in her 40s standing side by side, the daughter lightly holding his arm, both looking relaxed and friendly. Their age is suggested by hair color and posture, not by a kimono, a cane or white hair alone.",
    "vehicle-01": "Create a single illustration of a white community ride-share taxi: a box-shaped Japanese minivan, right-hand drive, seen from the front-left so that the left-side sliding door is visible. White body with one accent stripe. Blank license plate shape. A small roof sign with no text.",
}
COMPOSITION = {
    "person-01": "- one woman only\n- full body",
    "person-02": "- two people only\n- full body",
    "vehicle-01": "- one vehicle only\n- whole vehicle",
}
ASPECT = {"person-01": "3:4 vertical", "person-02": "3:4 vertical", "vehicle-01": "4:3 horizontal"}


def abst_prompt(kind, accent_hex, palette_note):
    return SUBJECTS[kind] + "\n\n" + ABST_STYLE.format(
        abstraction=PERSON_ABSTRACTION if kind.startswith("person") else VEHICLE_ABSTRACTION,
        accent=accent_hex, palette_note=palette_note, composition=COMPOSITION[kind], aspect=ASPECT[kind])
