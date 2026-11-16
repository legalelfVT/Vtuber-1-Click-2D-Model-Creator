# Vtuber 1-Click 2D Model Creator

Turn a VTuber character reference sheet into a rigged 2D model, with one click.

**Pipeline:** reference sheet → ComfyUI ([See-through](https://github.com/jtydhr88/ComfyUI-See-through) layer split) → [PSD2Live](https://github.com/tsunehimatoi/psd2live) → rigged Live2D model (.zip)

> Status: **alpha**. The GUI is in place; the pipeline is being connected.

## Quick start (Windows)

1. Install [Python 3.10+](https://www.python.org/downloads/) (tick "Add Python to PATH").
2. Download `vtuber_one_click.py`, put it in its own folder and double-click it.
3. The app opens in your web browser. It runs only on your PC; keep the small black window open while you use it and close it to quit.
4. **Build tab:** enter your character's name, choose or drop your character sheet (front view), tick what your character has, pick your options and where to save the model, then click **Build**.

Until the pipeline is connected, Build does a dry run and saves your settings as `<name>_job.json`.

## Screens

- **Build**: character, traits, options (movement, eye glow colour, emotes and extras), save folder.
- **Fix my model**: tick what looks wrong for a quick rebuild. *Coming soon.*
- **Fix with Claude**: describe the problem and let Claude fix the model with your own Claude account. *Coming soon.*

Long hair, ponytails, dresses/skirts and wings are shown as *soon* and can't be selected yet.

## Requirements

- Windows 10/11 with an NVIDIA GPU (8 GB VRAM tested)
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) with the See-through custom node
- [PSD2Live](https://github.com/tsunehimatoi/psd2live)

## License

This project's own code is MIT (see `LICENSE`). It runs ComfyUI and PSD2Live as separate programs; those are GPL-3.0 and are **not** included here. Model checkpoints have their own licenses.
