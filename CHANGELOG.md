# Changelog

What changed in each version of VTuber One-Click, newest first.

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
