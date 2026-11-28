# Changelog

What changed in each version of VTuber One-Click, newest first.

## Alpha 1.55 (2026-11-27)

Versions are now named **Alpha** with a number; Alpha 1.55 comes right after 0.3.5.

- **New license: free for noncommercial use.** VTuber One-Click is now under the PolyForm Noncommercial
  License 1.0.0 instead of MIT: free for personal and hobby use only. No commercial use: no selling
  it, no paid work with it, no selling models made with it. Copies received before 27 November 2026
  stay MIT.
- **Long hair is turned on.** Tick **Long hair** and the app asks for three more pictures besides your
  sheet: the **sheet with hair**, the **hair page** and the **front hair + headwear page**. Your main sheet
  becomes the **bald sheet** (the same sheet with the hair removed). All four are 3072 × 2048. The
  **Save hair templates** button gives you the two hair templates, and **Open the guide** shows how to make
  the pictures with ChatGPT, prompts included.
- **New templates with ruler marks.** The sheet and hair templates have small ruler ticks round the edges,
  so ChatGPT draws the hair pages at exactly the size and place of your sheet. The hair then goes on 1:1:
  no guessing, no stretching.
- **Long hair lines up with the face.** The bald sheet is never drawn exactly like the sheet with hair, so
  the hair is now lined up on the face itself (eyes, brows, glasses, mouth). No more locks over the cheeks
  or a fringe that sits off to one side.
- **No holes in long hair.** The hair is cut out of the hair page by where it is, not only by its colour:
  shading between the strands stays solid, and only real gaps between curls are see-through. The hair
  behind the swaying side curtains is whole, so nothing opens up beside the arms when the hair moves.
- **Back hair follows the head.** On a head turn the back hair and crown move with the face instead of
  swinging the other way.
- **Older hair pages still fit.** Pages made before the ruler templates are sized on the head as before
  (headwear like bonnets included).
- **Faces.** Drawn lips, nose and face markings stay on every build. The mouth line only shows when the
  mouth opens, and a mouth can no longer come out wider than the face. Glasses no longer cut slots in the
  cheeks, and skin the AI leaves out of the face is put back.
- **Bigger, more natural teeth.** The teeth are sized on the open mouth instead of a fixed share of it: the
  upper row runs edge to edge under the upper lip, the lower row follows the lower lip, and the tongue sits
  behind it. Fangs drawn in the UPPER TEETH cell are kept. A new `teeth_scale` setting (in `config.yaml`)
  makes them taller or shorter.
- **Human ears move with the head.** Ears beside the face that the AI painted into the back hair (so they
  swung with the hair) are moved onto the head. Hair in a colour close to the skin is left alone.
- **Hats with animal ears.** A hat with ears behind it comes out as a whole hat with the ears moving on
  their own behind it. The hat is no longer mistaken for a cloak, and when the close-up loses the hat, the
  full-body hat is sized and placed on the close-up's drawing (no more band of stray pixels on the crown).
- **Skirts, shorts and pants: pick one.** A new **Legs** row asks what the legs wear: **Skirt / dress**,
  **Shorts** or **Pants / trousers / leggings**. Build won't start without it. Only skirts and dresses get the
  skirt handling, so trousers (even in a colour close to the skin tone) are no longer cut at the waist. The
  build also checks the layers and adds a note to the log if they look different from your pick, but your
  pick always wins. An open long coat over pants no longer counts as a skirt. A black shirt no longer gets
  cut out because it matches black hair.
- **Cleaner edges.** No grey squares on hair tips, no blocks of sheet background in the clothes when two
  pictures have different background colours, horns come out solid and animal ears clean.
- **Fix with Claude knows more.** For long hair the fix kit now includes the sheet with hair and both hair
  pages, and the notes Claude reads cover long hair, the Legs pick, teeth, ears and hats, with the log
  lines to look for.
- The guide (**VTuber One-Click Guide.pdf**) and the ChatGPT prompts (**CHATGPT_PROMPTS.md**) are installed
  with the app.

## 0.3.5 (2026-11-23)

- **Fix with Claude knows the new parts.** The brief that comes with the Fix with Claude folder now covers the
  layered mouth, all the emotes, how skirts and legs are handled, and how long hair works (the four pictures it
  needs and how the hair is fitted), plus faster ways to redo only the rigging (a few minutes), only the emotes
  (about 3 minutes) or a quick mouth check (about 1 minute).
- Long hair is still turned off in the app.

## 0.3.4 (2026-11-23)

- **Better mouth.** The open mouth is now built in layers like a hand-rigged model: the inside of the
  mouth, the upper teeth, the lower teeth and the tongue are separate, so the teeth slide apart as the
  mouth opens instead of one picture being squashed. Smiles get wider and frowns narrower (an open
  frown reads as an "o"), and the closed mouth is a little smaller than the open one.
- **More emotes.** Besides Angry, Stunned and DED there are now **Love** (heart eyes and a blush),
  **Shocked** (blank round eyes and a small "o" mouth), **Frustrated** (`><` eyes and a wavy mouth) and
  **Grossed Out** (purple face and gritted teeth). Each one gets a hotkey in VTube Studio.
- **Angry is redone.** The anger mark sits on the head, the face gets a light red flush, and the mouth
  shows gritted teeth.
- **Emotes replace the face parts they draw.** When an emote draws its own eyes or mouth, the normal
  eyes or mouth are hidden while it shows, so you never see both at once.
- **Complete jaw.** If the sides of the face came out ragged, the jaw line is rebuilt from your sheet's
  close-up, so the face has a clean outline from the cheeks to the chin.
- **Gap check.** Before rigging, the app slides the head as if turning and saves `gap_check.png` in the
  model's build folder, showing where holes could open on head turns. It is added to the Fix with Claude folder.
- Long hair is still turned off in the app.

## 0.3.3 (2026-11-20)

- **Grey templates.** The blank character sheet and the hair pages that come with the app (and the
  "Save template" button) now have flat grey boxes instead of white. White clothes, aprons, tights,
  frills, fur and white or silver hair no longer blend into a white page, so they don't get cut out
  as background. The app measures each sheet's background colour, so sheets made on the old white
  template still work.
- If a grey sheet gives you trouble, use the white one for now and please report it on the Issues page.

## 0.3.2 (2026-11-18)

- **Faces keep their shading.** Faces no longer come out flat white. The skin you can see keeps the soft shading
  from your sheet, and only the skin hidden under the eyes and mouth is filled in. This helps every character, whatever the hair.

## 0.3.1 (2026-11-17)

- **Fix with Claude works.** Describe what looks wrong, click the button, and the app makes a folder with
  everything Claude needs plus a ready-made message. See [How to fix your model with Claude](FIX_WITH_CLAUDE.md).
- **Short hair looks like your sheet.** No more ring of spiky hair with white edges around the head.
- **Dark hair stays clean.** No more pale specks in dark fringes.
- **Patterned coats.** Fewer blocky patches, and shoulder straps and buckles are kept.
- **Ears.** The hidden part of the ear is a smooth colour instead of a striped block.
- **The app knows when a build is done.** It no longer keeps saying "still building" after the model is ready.
- Builds now save your settings and build log in the model's folder.

## 0.3.0 (2026-11-16)

- First public version.
- New app screen with three tabs: **Build**, **Fix my model** and **Fix with Claude**.
- One installer sets up everything (ComfyUI, See-through, PSD2Live and the app), and you pick the install folder.
- You choose where the finished model zip is saved.
- Long hair is turned off for now.

## Known problems

- Small gaps can show beside the neck under earrings.
- Mouth shapes O / E are sometimes left out when the open mouth on the sheet is drawn too big.
- Not supported yet: long hair, ponytails, dresses and wings.

Found something else? Please report it on the [Issues page](https://github.com/legalelfVT/Vtuber-1-Click-2D-Model-Creator/issues).
