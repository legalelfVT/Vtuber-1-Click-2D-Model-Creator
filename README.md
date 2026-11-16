# Vtuber 1-Click 2D Model Creator

Turn a VTuber character reference sheet into a rigged 2D model, with one click.

**Pipeline:** reference sheet → ComfyUI ([See-through](https://github.com/jtydhr88/ComfyUI-See-through) layer split) → [PSD2Live](https://github.com/tsunehimatoi/psd2live) → rigged Live2D model (.zip)

> Status: **alpha**. The GUI is in place; the pipeline is being connected.

## Quick start (Windows)

1. Install [Python 3.10+](https://www.python.org/downloads/) (tick "Add Python to PATH").
2. Download `vtuber_one_click_gui.py` and double-click it.
3. Enter your model name, pick your filled-in reference sheet (front view), tick your character's traits, and choose where to save the model zip.
4. Click **Build my model**.

Until the pipeline is connected, the button does a dry run and saves your job settings as `<model name>_job.json`.

## Traits

Horns · Hat/Hood · Cat ears · Short hair · Dress · Jacket · Tail · Wings
Long hair: coming soon.

## Requirements

- Windows 10/11 with an NVIDIA GPU (8 GB VRAM tested)
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) with the See-through custom node
- [PSD2Live](https://github.com/tsunehimatoi/psd2live)

## License

This project's own code is MIT (see `LICENSE`). It runs ComfyUI and PSD2Live as separate programs; those are GPL-3.0 and are **not** included here. Model checkpoints have their own licenses.
