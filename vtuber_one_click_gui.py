"""VTuber One-Click - standalone GUI.

Collects the model name, the filled-in reference sheet, the character traits
(checkboxes only) and where the finished model zip should be saved.

Standalone: if a `pipeline.py` with a `run(config, log)` function sits next to
this file, the Build button calls it. Otherwise the GUI does a dry run and
writes the job settings to `<output folder>/<model name>_job.json`.

Needs only the Python standard library (tkinter ships with Python on Windows).
"""

import json
import os
import re
import sys
import threading
import importlib.util
from datetime import datetime

APP_TITLE = "VTuber One-Click"
APP_VERSION = "0.1.0-alpha"

# Trait checkboxes: (key, label, enabled, note)
TRAITS = [
    ("horns", "Horns", True, ""),
    ("hat_hood", "Hat / Hood", True, ""),
    ("cat_ears", "Cat ears", True, ""),
    ("short_hair", "Short hair", True, ""),
    ("long_hair", "Long hair", False, "coming soon"),
    ("dress", "Dress", True, ""),
    ("jacket", "Jacket", True, ""),
    ("tail", "Tail", True, ""),
    ("wings", "Wings", True, ""),
]

SHEET_TYPES = [("Images", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")]


# ---------------------------------------------------------------- core logic
def safe_model_name(name):
    """Turn a model name into something safe for file and folder names."""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", name).strip().strip(".")
    return re.sub(r"\s+", "_", cleaned)


def build_config(model_name, sheet_path, output_dir, traits):
    """Validate inputs and return (config, errors)."""
    errors = []
    name = safe_model_name(model_name or "")
    if not name:
        errors.append("Enter a model name.")
    if not sheet_path:
        errors.append("Choose your reference sheet image.")
    elif not os.path.isfile(sheet_path):
        errors.append("The reference sheet file can't be found.")
    if not output_dir:
        errors.append("Choose where to save the model zip.")
    elif not os.path.isdir(output_dir):
        errors.append("The save folder doesn't exist.")

    enabled = {key for key, _, on, _ in TRAITS if on}
    chosen = sorted(k for k, v in traits.items() if v and k in enabled)

    config = {
        "app_version": APP_VERSION,
        "created": datetime.now().isoformat(timespec="seconds"),
        "model_name": name,
        "reference_sheet": os.path.abspath(sheet_path) if sheet_path else "",
        "output_dir": os.path.abspath(output_dir) if output_dir else "",
        "output_zip": os.path.join(os.path.abspath(output_dir), f"{name}.zip")
        if output_dir and name else "",
        "traits": chosen,
        # 8 GB GPU: never time out ComfyUI or PSD2Live.
        "timeouts": {"comfyui": 0, "psd2live": 0},
    }
    return config, errors


def load_pipeline(folder):
    """Return pipeline.run if pipeline.py exists next to the GUI, else None."""
    path = os.path.join(folder, "pipeline.py")
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("vtuber_pipeline", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "run", None)


def dry_run(config, log):
    """Standalone mode: save the job settings so the pipeline can pick them up."""
    job_path = os.path.join(config["output_dir"], f"{config['model_name']}_job.json")
    with open(job_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    log(f"No pipeline.py found - dry run only.")
    log(f"Saved job settings: {job_path}")
    return job_path


# ---------------------------------------------------------------------- GUI
def main():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    here = os.path.dirname(os.path.abspath(__file__))
    start_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.isdir(start_dir):
        start_dir = os.path.expanduser("~")

    root = tk.Tk()
    root.title(f"{APP_TITLE}  {APP_VERSION}")
    root.minsize(560, 600)

    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
    style.configure("Hint.TLabel", foreground="#666666")
    style.configure("Build.TButton", font=("Segoe UI", 11, "bold"), padding=8)

    main_frame = ttk.Frame(root, padding=16)
    main_frame.pack(fill="both", expand=True)
    main_frame.columnconfigure(0, weight=1)

    ttk.Label(main_frame, text=APP_TITLE, style="Title.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Label(main_frame, text="Reference sheet in, rigged model out.",
              style="Hint.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 12))

    # 1. Model name
    name_box = ttk.LabelFrame(main_frame, text=" 1. Model name ", padding=10)
    name_box.grid(row=2, column=0, sticky="ew", pady=4)
    name_box.columnconfigure(0, weight=1)
    name_var = tk.StringVar()
    ttk.Entry(name_box, textvariable=name_var).grid(row=0, column=0, sticky="ew")

    # 2. Reference sheet
    sheet_box = ttk.LabelFrame(main_frame, text=" 2. Reference sheet (front view) ", padding=10)
    sheet_box.grid(row=3, column=0, sticky="ew", pady=4)
    sheet_box.columnconfigure(0, weight=1)
    sheet_var = tk.StringVar()
    ttk.Entry(sheet_box, textvariable=sheet_var).grid(row=0, column=0, sticky="ew")

    def pick_sheet():
        p = filedialog.askopenfilename(title="Choose your filled-in reference sheet",
                                       initialdir=start_dir, filetypes=SHEET_TYPES)
        if p:
            sheet_var.set(p)

    ttk.Button(sheet_box, text="Browse…", command=pick_sheet).grid(row=0, column=1, padx=(8, 0))

    template = os.path.join(here, "templates", "reference_sheet_template.png")

    def open_template():
        if os.path.isfile(template):
            os.startfile(template) if sys.platform == "win32" else None
        else:
            messagebox.showinfo(APP_TITLE, "The sheet template isn't in the templates folder yet.")

    ttk.Button(sheet_box, text="Open sheet template", command=open_template).grid(
        row=1, column=0, sticky="w", pady=(8, 0))

    # 3. Traits
    traits_box = ttk.LabelFrame(main_frame, text=" 3. What does your character have? ", padding=10)
    traits_box.grid(row=4, column=0, sticky="ew", pady=4)
    trait_vars = {}
    for i, (key, label, enabled, note) in enumerate(TRAITS):
        var = tk.BooleanVar(value=False)
        trait_vars[key] = var
        text = f"{label} ({note})" if note else label
        cb = ttk.Checkbutton(traits_box, text=text, variable=var)
        if not enabled:
            cb.state(["disabled"])
        cb.grid(row=i // 3, column=i % 3, sticky="w", padx=(0, 24), pady=3)

    # 4. Save location
    out_box = ttk.LabelFrame(main_frame, text=" 4. Save the model zip to ", padding=10)
    out_box.grid(row=5, column=0, sticky="ew", pady=4)
    out_box.columnconfigure(0, weight=1)
    out_var = tk.StringVar()
    ttk.Entry(out_box, textvariable=out_var).grid(row=0, column=0, sticky="ew")

    def pick_out():
        p = filedialog.askdirectory(title="Choose where to save the model zip",
                                    initialdir=start_dir)
        if p:
            out_var.set(p)

    ttk.Button(out_box, text="Browse…", command=pick_out).grid(row=0, column=1, padx=(8, 0))

    # Build + progress + log
    build_btn = ttk.Button(main_frame, text="Build my model", style="Build.TButton")
    build_btn.grid(row=6, column=0, sticky="ew", pady=(12, 6))
    progress = ttk.Progressbar(main_frame, mode="indeterminate")
    progress.grid(row=7, column=0, sticky="ew")

    log_box = tk.Text(main_frame, height=8, state="disabled", wrap="word",
                      font=("Consolas", 9), background="#f6f6f6", relief="flat")
    log_box.grid(row=8, column=0, sticky="nsew", pady=(8, 0))
    main_frame.rowconfigure(8, weight=1)

    def log(msg):
        def write():
            log_box.configure(state="normal")
            log_box.insert("end", f"[{datetime.now():%H:%M:%S}] {msg}\n")
            log_box.see("end")
            log_box.configure(state="disabled")
        root.after(0, write)

    def finish(ok, msg):
        progress.stop()
        build_btn.state(["!disabled"])
        (messagebox.showinfo if ok else messagebox.showerror)(APP_TITLE, msg)

    def build():
        traits = {k: v.get() for k, v in trait_vars.items()}
        config, errors = build_config(name_var.get(), sheet_var.get(), out_var.get(), traits)
        if errors:
            messagebox.showwarning(APP_TITLE, "\n".join(errors))
            return
        build_btn.state(["disabled"])
        progress.start(12)
        log(f"Starting {config['model_name']}  traits: {', '.join(config['traits']) or 'none'}")

        def work():
            try:
                run = load_pipeline(here)
                if run:
                    run(config, log)
                    msg = f"Done! Your model is at:\n{config['output_zip']}"
                else:
                    dry_run(config, log)
                    msg = "Dry run finished - job settings saved."
                root.after(0, finish, True, msg)
            except Exception as e:  # show any pipeline error to the user
                log(f"Error: {e}")
                root.after(0, finish, False, f"Something went wrong:\n{e}")

        threading.Thread(target=work, daemon=True).start()

    build_btn.configure(command=build)
    root.mainloop()


if __name__ == "__main__":
    main()
