"""Vtuber 1-Click 2D Model Creator - standalone app.

Double-click this file. It opens the app in your web browser (nothing is
installed and nothing leaves your PC: the page is served from your own
computer). Keep the small black window open while you use the app; close it
to quit.

If a `pipeline.py` with a `run(config, log)` function sits next to this file,
the Build button calls it. Otherwise Build does a dry run and saves the job
settings as `<save folder>/<character name>_job.json`.

Needs only Python 3.9+ (standard library).
"""

import importlib.util
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

APP_TITLE = "VTuber One-Click"
APP_VERSION = "0.2.0-alpha"
HERE = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(os.path.expanduser("~"), "VTuber One-Click")
TEMPLATE = os.path.join(HERE, "templates", "reference_sheet_template.png")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")

# ------------------------------------------------------------------ options
GROUPS = [
    ("Hair", ["Short hair", "Shoulder-length hair", "Long hair", "Bouncy / curly / wavy",
              "Bangs cover the eyebrows", "Ponytail / twin tails / buns"]),
    ("Face", ["Fangs", "Visible lips", "Small / delicate mouth", "Face markings / tattoos",
              "Glasses", "Remove the glasses"]),
    ("Ears", ["Human ears", "Pointed / elf ears", "Animal ears (cat, fox, bunny...)",
              "Earrings", "Swinging earrings"]),
    ("Head", ["Hat / cap / crown", "Hood", "Horns", "Headband / clips / halo"]),
    ("Outfit", ["Long coat / cape", "Open-front dress / cloak", "Jacket / short top",
                "Belt at the waist", "Dress / skirt"]),
    ("Body", ["Tattoos", "Tail", "Wings"]),
]
# Shown but not selectable yet.
SOON = ["Long hair", "Ponytail / twin tails / buns", "Dress / skirt", "Wings"]

MOVES = [("Body follows head", True), ("Bigger mouth", False), ("Big eyebrow movement", False)]
EXTRAS = [("Ears move with eyebrows", True), ("Eye glow", True), ("Angry, Stunned, DED emotes", True),
          ("Arm up / down hotkeys", True), ("Mouth O / E from microphone", True),
          ("Cheek puff + blush", False), ("Tail sways", True)]
GLOWS = [("Green", "#4ADE80"), ("Red", "#F87171"), ("Purple", "#C084FC"), ("Pink", "#F472B6"),
         ("Yellow", "#FDE047"), ("Blue", "#60A5FA"), ("Orange", "#FB923C"), ("White", "#F5F5F4")]

ISSUES = [
    ("No neck", "Gap or missing skin between chin and shoulders"),
    ("Mouth too small", "Open or closed mouth looks tiny on the face"),
    ("Hair specks", "Small bits of hair floating on clothes or skin"),
    ("Wrong colour behind the hair", "Grey, brown or red shows when the hair moves"),
    ("Hair comes off the head", "A strand or fringe slides away on turns"),
    ("Marks on the face", "Copies of eyes, lips or hair on the skin"),
    ("Face markings missing", "Whiskers, tattoos or blush were wiped"),
    ("Holes in skin or clothes", "See-through spots when moving"),
    ("White outline", "Thin white rim around the character"),
    ("Earrings wrong", "Behind the hair, doubled, or not moving"),
    ("Body does not move", "Turning your head leaves the body still"),
    ("Double hood", "Hood edge shows twice"),
]
FIXES = {
    "No neck": "Keeps the body's neck under the close-up neck.",
    "Mouth too small": "Mouth size 24% → 28% of the face.",
}
SHARES = ["Your character sheet", "The model's layers (PSD)", "Build log", "Your screenshots",
          "The finished VTube Studio model"]
RULES = [("Ask me before changing any file", True), ("Install the fix into VTube Studio", False),
         ("Share the fix back to improve the tool", False)]

PROMPT_INTRO = ("Fill in the attached character sheet template for my VTuber character. "
                "Keep the template's layout, corner marks and cells exactly as they are. "
                "Draw the character facing the front, in a flat anime style with clean outlines "
                "and a plain white background. Put each part in its own cell and leave a cell "
                "empty if the character doesn't have that part.\nMy character has:")
PROMPT_OUTRO = "Don't add text, logos or extra poses."
PROMPT_LINES = {
    "Horns": "Horns: draw them on their own in the horns cell as well as on the head.",
    "Tail": "A tail: draw it on its own in the tail cell, fully visible.",
    "Hood": "A hood: show it down and up if it can move.",
    "Remove the glasses": "Glasses in the art, but draw the face without them in the close-up.",
}


def default_out_dir():
    d = os.path.join(os.path.expanduser("~"), "Downloads")
    return d if os.path.isdir(d) else os.path.expanduser("~")


# ------------------------------------------------------------------ helpers
def image_size(path):
    """Return (width, height) for PNG/JPEG/WEBP without extra libraries."""
    try:
        with open(path, "rb") as f:
            head = f.read(32)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                return struct.unpack(">II", head[16:24])
            if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
                kind = head[12:16]
                if kind == b"VP8X":
                    w = int.from_bytes(head[24:27], "little") + 1
                    h = int.from_bytes(head[27:30], "little") + 1
                    return w, h
                f.seek(0)
                data = f.read(40)
                if kind == b"VP8 ":
                    w, h = struct.unpack("<HH", data[26:30])
                    return w & 0x3FFF, h & 0x3FFF
                if kind == b"VP8L":
                    b = data[21:25]
                    w = 1 + (((b[1] & 0x3F) << 8) | b[0])
                    h = 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
                    return w, h
            if head[:2] == b"\xff\xd8":
                f.seek(2)
                while True:
                    marker = f.read(2)
                    if len(marker) < 2 or marker[0] != 0xFF:
                        return None
                    if marker[1] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                        f.read(3)
                        h, w = struct.unpack(">HH", f.read(4))
                        return w, h
                    seg_len = struct.unpack(">H", f.read(2))[0]
                    f.seek(seg_len - 2, 1)
    except (OSError, struct.error):
        pass
    return None


def sheet_info(path):
    size = image_size(path)
    return {"name": os.path.basename(path), "path": path,
            "width": size[0] if size else None, "height": size[1] if size else None}


def safe_name(name):
    bad = '<>:"/\\|?*'
    cleaned = "".join(c for c in (name or "") if c not in bad and ord(c) >= 32).strip().strip(".")
    return "_".join(cleaned.split())


_dialog_lock = threading.Lock()


def native_dialog(kind, **kw):
    """Open a Windows file/folder dialog on top of the browser. Returns a path or ''."""
    with _dialog_lock:
        try:
            import tkinter as tk
            from tkinter import filedialog
        except ImportError:
            raise RuntimeError("File dialogs need tkinter (included with Python on Windows).")
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            fn = {"open": filedialog.askopenfilename, "folder": filedialog.askdirectory,
                  "save": filedialog.asksaveasfilename}[kind]
            return fn(parent=root, **kw) or ""
        finally:
            root.destroy()


def open_in_explorer(folder):
    if sys.platform == "win32":
        os.startfile(folder)  # noqa: S606 - opens the user's own folder
    elif sys.platform == "darwin":
        subprocess.Popen(["open", folder])
    else:
        subprocess.Popen(["xdg-open", folder])


def load_pipeline():
    path = os.path.join(HERE, "pipeline.py")
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("vtuber_pipeline", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "run", None)


# ------------------------------------------------------------------ app state
class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.sheet = None
        self.running = False
        self.log = []
        self.ok = None
        self.message = ""
        self.model_name = ""

    def add_log(self, msg):
        with self.lock:
            self.log.append(f"[{datetime.now():%H:%M:%S}] {msg}")


STATE = State()


def build_config(body):
    """Validate a Build request. Returns (config, errors)."""
    errors = []
    name = safe_name(body.get("name"))
    if not name:
        errors.append("Enter a character name")
    sheet = STATE.sheet
    if not sheet or not os.path.isfile(sheet["path"]):
        errors.append("Choose your character sheet")
    out = (body.get("output_dir") or "").strip()
    if not out or not os.path.isdir(out):
        errors.append("Choose a save folder that exists")
    allowed = {t for _, items in GROUPS for t in items} - set(SOON)
    traits = [t for t in body.get("traits", []) if t in allowed]
    moves = [m for m in body.get("movement", []) if m in dict(MOVES)]
    extras = [e for e in body.get("extras", []) if e in dict(EXTRAS)]
    glow = body.get("eye_glow") if body.get("eye_glow") in dict(GLOWS) else "Green"
    config = {
        "app_version": APP_VERSION,
        "created": datetime.now().isoformat(timespec="seconds"),
        "model_name": name,
        "reference_sheet": sheet["path"] if sheet else "",
        "output_dir": os.path.abspath(out) if out else "",
        "output_zip": os.path.join(os.path.abspath(out), f"{name}.zip") if out and name else "",
        "traits": traits,
        "movement": moves,
        "extras": extras,
        "eye_glow": {"name": glow, "hex": dict(GLOWS)[glow]},
        # 8 GB GPU: never time out ComfyUI or PSD2Live.
        "timeouts": {"comfyui": 0, "psd2live": 0},
    }
    return config, errors


def run_build(config):
    try:
        run = load_pipeline()
        if run:
            run(config, STATE.add_log)
            msg = f"Done! Your model is at {config['output_zip']}"
        else:
            job = os.path.join(config["output_dir"], f"{config['model_name']}_job.json")
            with open(job, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            STATE.add_log("No pipeline.py found - dry run only.")
            STATE.add_log(f"Saved job settings: {job}")
            msg = "Dry run finished - job settings saved"
        with STATE.lock:
            STATE.ok, STATE.message, STATE.model_name = True, msg, config["model_name"]
    except Exception as e:  # show any pipeline error in the app
        STATE.add_log(f"Error: {e}")
        with STATE.lock:
            STATE.ok, STATE.message = False, f"Something went wrong: {e}"
    finally:
        with STATE.lock:
            STATE.running = False


# ------------------------------------------------------------------ web server
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _local_only(self):
        # Only answer pages from this computer, never from other sites.
        host = (self.headers.get("Host") or "").split(":")[0]
        origin = self.headers.get("Origin")
        if host not in ("127.0.0.1", "localhost"):
            return False
        if origin and urlparse(origin).hostname not in ("127.0.0.1", "localhost"):
            return False
        return True

    def do_GET(self):
        if not self._local_only():
            return self._send(403, {"error": "forbidden"})
        path = urlparse(self.path).path
        if path == "/":
            return self._send(200, UI_HTML.encode(), "text/html; charset=utf-8")
        if path == "/api/config":
            return self._send(200, {
                "groups": [{"name": n, "items": i} for n, i in GROUPS], "soon": SOON,
                "moves": MOVES, "extras": EXTRAS, "glows": GLOWS, "issues": ISSUES, "fixes": FIXES,
                "shares": SHARES, "rules": RULES, "default_out": default_out_dir(),
                "prompt_intro": PROMPT_INTRO, "prompt_outro": PROMPT_OUTRO, "prompt_lines": PROMPT_LINES,
                "sheet": STATE.sheet, "version": APP_VERSION})
        if path == "/api/status":
            with STATE.lock:
                return self._send(200, {"running": STATE.running, "log": STATE.log[-200:], "ok": STATE.ok,
                                        "message": STATE.message, "model_name": STATE.model_name})
        if path == "/api/sheet_preview" and STATE.sheet and os.path.isfile(STATE.sheet["path"]):
            ext = os.path.splitext(STATE.sheet["path"])[1].lower()
            ctype = {".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
            with open(STATE.sheet["path"], "rb") as f:
                return self._send(200, f.read(), ctype)
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self._local_only():
            return self._send(403, {"error": "forbidden"})
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            if path == "/api/upload_sheet":
                return self._send(200, self.upload_sheet(raw))
            body = json.loads(raw or b"{}")
            handler = {
                "/api/pick_sheet": self.pick_sheet, "/api/pick_folder": self.pick_folder,
                "/api/save_template": self.save_template, "/api/open_folder": self.open_folder,
                "/api/build": self.build,
            }.get(path)
            if not handler:
                return self._send(404, {"error": "not found"})
            return self._send(200, handler(body))
        except Exception as e:
            return self._send(200, {"error": str(e)})

    # ---- actions
    def pick_sheet(self, _):
        p = native_dialog("open", title="Choose your character sheet", initialdir=default_out_dir(),
                          filetypes=[("Images", "*.png *.jpg *.jpeg *.webp"), ("All files", "*.*")])
        if not p:
            return {}
        STATE.sheet = sheet_info(os.path.abspath(p))
        return {"sheet": STATE.sheet}

    def upload_sheet(self, raw):
        name = os.path.basename(unquote(self.headers.get("X-Filename") or "sheet.png"))
        if not name.lower().endswith(IMAGE_EXT) or not raw:
            return {"error": "Use a PNG, JPG or WEBP image"}
        os.makedirs(os.path.join(WORK_DIR, "sheets"), exist_ok=True)
        dest = os.path.join(WORK_DIR, "sheets", name)
        with open(dest, "wb") as f:
            f.write(raw)
        STATE.sheet = sheet_info(dest)
        return {"sheet": STATE.sheet}

    def pick_folder(self, _):
        p = native_dialog("folder", title="Choose where to save the model zip", initialdir=default_out_dir())
        return {"folder": os.path.abspath(p)} if p else {}

    def save_template(self, _):
        if not os.path.isfile(TEMPLATE):
            return {"error": "The blank template isn't in the templates folder yet"}
        p = native_dialog("save", title="Save the blank template", initialdir=default_out_dir(),
                          initialfile="VTuber character sheet template.png", defaultextension=".png",
                          filetypes=[("PNG image", "*.png")])
        if not p:
            return {}
        shutil.copyfile(TEMPLATE, p)
        return {"message": f"Template saved: {os.path.basename(p)}"}

    def open_folder(self, body):
        folder = body.get("folder") or default_out_dir()
        if not os.path.isdir(folder):
            return {"error": "That folder doesn't exist"}
        open_in_explorer(folder)
        return {}

    def build(self, body):
        with STATE.lock:
            if STATE.running:
                return {"errors": ["A build is already running"]}
        config, errors = build_config(body)
        if errors:
            return {"errors": errors}
        with STATE.lock:
            STATE.running, STATE.log, STATE.ok, STATE.message = True, [], None, ""
        STATE.add_log(f"Starting {config['model_name']}  traits: {', '.join(config['traits']) or 'none'}")
        threading.Thread(target=run_build, args=(config,), daemon=True).start()
        return {"started": True}


def free_port(preferred=8765):
    for port in (preferred, 0):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", port))
                return s.getsockname()[1]
            except OSError:
                continue
    raise RuntimeError("No free port")


def main(open_browser=True):
    port = free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"{APP_TITLE} {APP_VERSION} is running at {url}")
    print("Keep this window open while you use the app. Close it to quit.")
    if open_browser:
        threading.Timer(0.6, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


UI_HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VTuber One-Click</title>
<style>
:root{--bg:#121118;--bar:#17161E;--panel:#1B1A23;--inset:#16151D;--line:#2A2833;--line2:#3A3747;--dash:#4C4466;--chip:#2A2540;
--text:#ECEAF2;--muted:#A7A3B5;--dim:#8F8A9E;--lav:#DDD6FE;--accent:#A78BFA;--ok:#86EFAC;--warn:#FCD34D;--bad:#FCA5A5}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--text);font-family:Manrope,"Segoe UI",system-ui,sans-serif;font-size:14px;display:flex;flex-direction:column;min-width:1100px}
button{font:inherit;color:inherit;cursor:pointer}
button:disabled{cursor:not-allowed;opacity:.55}
.top{height:64px;padding:0 24px;display:flex;align-items:center;gap:16px;border-bottom:1px solid var(--line);background:var(--bar);flex-shrink:0}
.logo{width:32px;height:32px;border-radius:8px;background:var(--accent);display:flex;align-items:center;justify-content:center}
.brand{font-size:17px;font-weight:800;letter-spacing:-.01em}
.grow{flex-grow:1}
.tabs{display:flex;gap:8px}
.tab{padding:6px 12px;border-radius:999px;border:1px solid var(--line2);background:transparent;color:var(--muted);font-weight:600;font-size:13px}
.tab.on{background:var(--chip);border-color:var(--chip);color:var(--lav)}
.page{flex-grow:1;min-height:0;padding:20px 24px 24px;display:none;gap:20px}
.page.on{display:grid}
#build{grid-template-columns:330px minmax(0,1fr) 360px}
#fix{grid-template-columns:300px minmax(0,1fr) 320px}
#claude{grid-template-columns:300px minmax(0,1fr) 330px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px;display:flex;flex-direction:column;gap:16px;min-height:0;overflow:auto}
.h{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.sub{color:var(--muted);font-size:12px;line-height:1.5}
.lbl{font-weight:600}
.field{display:flex;flex-direction:column;gap:6px}
input[type=text],textarea{height:44px;padding:0 12px;border-radius:10px;border:1px solid var(--line2);background:var(--bg);color:var(--text);font:inherit;font-size:15px;width:100%}
textarea{height:120px;padding:12px;font-size:14px;line-height:1.5;resize:none}
input[type=text]:focus,textarea:focus{outline:2px solid var(--accent);outline-offset:-1px}
.drop{border:2px dashed var(--dash);border-radius:12px;padding:14px;display:flex;gap:12px;align-items:center;background:var(--inset);cursor:pointer;width:100%;text-align:left}
.drop.over{border-color:var(--accent);background:#1E1B2B}
.thumb{width:96px;height:64px;border-radius:6px;background:var(--chip);display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:11px;text-align:center;flex-shrink:0;overflow:hidden}
.thumb img{width:100%;height:100%;object-fit:cover}
.check{display:flex;align-items:center;gap:8px;font-size:13px}
.check.ok{color:var(--ok)}.check.warn{color:var(--warn)}.check.bad{color:var(--bad)}
.btn{height:44px;border-radius:10px;border:1px solid var(--line2);background:transparent;font-weight:600}
.btn.alt{border-color:var(--dash);background:var(--chip);font-weight:700}
.btn.claude{border-color:#8B7BD8;background:#221F33;color:var(--lav);font-weight:700}
.big{height:56px;border-radius:12px;border:0;background:var(--accent);color:var(--bg);font-size:17px;font-weight:800}
.groups{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
fieldset{margin:0;border:1px solid var(--line);border-radius:12px;padding:10px 12px 12px;background:var(--inset)}
legend{padding:0 6px;font-weight:700;font-size:13px;color:var(--lav)}
.opt{display:flex;align-items:center;gap:10px;min-height:30px;font-size:13px;cursor:pointer}
.opt input{width:16px;height:16px;accent-color:var(--accent);margin:0;flex-shrink:0}
.opt.soon{color:var(--dim);cursor:default}
.opt span.t{flex-grow:1}
.pill{font-size:11px;padding:2px 8px;border-radius:999px;border:1px solid var(--line2);color:var(--muted)}
.swatches{display:flex;gap:8px;flex-wrap:wrap}
.sw{width:30px;height:30px;border-radius:999px;border:2px solid var(--line);padding:0}
.sw.on{border:3px solid var(--text)}
.row{display:flex;gap:8px}
.row input{flex-grow:1;font-size:13px;height:40px}
.row .btn{height:40px;padding:0 14px}
.center{text-align:center}
.log{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:10px;font-family:Consolas,monospace;font-size:12px;color:var(--muted);height:110px;overflow:auto;white-space:pre-wrap;display:none}
.bar{height:6px;border-radius:999px;background:var(--line);overflow:hidden;display:none}
.bar i{display:block;height:100%;width:30%;background:var(--accent);border-radius:999px;animation:slide 1.4s ease-in-out infinite}
@keyframes slide{0%{margin-left:-30%}100%{margin-left:100%}}
.issues{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.issue{display:flex;gap:12px;align-items:flex-start;padding:12px 14px;border-radius:12px;border:1px solid var(--line);background:var(--inset);cursor:pointer}
.issue.on{border-color:#8B7BD8;background:#221F33}
.issue input{width:18px;height:18px;accent-color:var(--accent);margin:2px 0 0}
.issue b{display:block;margin-bottom:3px}
.issue small{color:var(--muted);font-size:12px;line-height:1.45}
.card{padding:12px;border-radius:10px;background:var(--inset);border:1px solid var(--line)}
.card b{display:block}.card small{color:var(--muted);font-size:12px;display:block;margin-top:4px;line-height:1.45}
.ph{border-radius:12px;background:var(--chip);display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:12px}
.soonbox{border:1px dashed var(--line2);border-radius:10px;padding:10px 12px;color:var(--muted);font-size:12px;line-height:1.5}
.toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:var(--chip);color:var(--lav);padding:10px 16px;border-radius:10px;border:1px solid var(--dash);font-weight:600;opacity:0;transition:opacity .2s;pointer-events:none}
.toast.on{opacity:1}
</style>
</head>
<body>
<div class="top">
  <div class="logo"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#121118" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="10" r="6"></circle><path d="M6 6 4 2M18 6l2-4M9 10h.01M15 10h.01M10 13c1 .8 3 .8 4 0"></path><path d="M6 21c1.5-3 4-4 6-4s4.5 1 6 4"></path></svg></div>
  <div class="brand">VTuber One-Click</div>
  <div class="grow"></div>
  <div class="tabs" role="tablist">
    <button class="tab on" data-page="build" role="tab">Build</button>
    <button class="tab" data-page="fix" role="tab">Fix my model</button>
    <button class="tab" data-page="claude" role="tab">Fix with Claude</button>
  </div>
</div>

<!-- ============================== BUILD ============================== -->
<div class="page on" id="build">
  <div class="panel">
    <div class="h">1 · Your character</div>
    <div class="field">
      <label for="cname" class="lbl">Character name</label>
      <input id="cname" type="text" placeholder="Your character's name" autocomplete="off">
    </div>
    <div class="field">
      <div class="lbl">Character sheet</div>
      <button type="button" class="drop" id="drop">
        <div class="thumb" id="thumb">sheet preview</div>
        <div style="display:flex;flex-direction:column;gap:4px;min-width:0">
          <div style="font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" id="sheetName">No sheet yet</div>
          <div class="sub">Drop your sheet here or click to choose</div>
        </div>
      </button>
    </div>
    <div id="checks" style="display:flex;flex-direction:column;gap:8px"></div>
    <div class="grow"></div>
    <div style="display:flex;flex-direction:column;gap:10px">
      <div class="sub">No sheet yet? Give the template to ChatGPT with the prompt. The prompt adds a line for each trait you tick.</div>
      <button type="button" class="btn alt" id="copyPrompt">Copy ChatGPT prompt</button>
      <button type="button" class="btn" id="saveTemplate">Save blank template</button>
    </div>
  </div>

  <div class="panel">
    <div style="display:flex;align-items:baseline;gap:12px">
      <div class="h">2 · What does your character have?</div>
      <div class="sub">Tick everything that shows on the sheet</div>
    </div>
    <div class="groups" id="groups"></div>
  </div>

  <div class="panel">
    <div class="h">3 · Options</div>
    <div style="display:flex;flex-direction:column;gap:4px">
      <div class="lbl" style="margin-bottom:2px">Movement</div>
      <div id="moves"></div>
    </div>
    <div style="display:flex;flex-direction:column;gap:8px">
      <div class="lbl">Eye glow colour</div>
      <div class="swatches" id="glows"></div>
    </div>
    <div style="display:flex;flex-direction:column;gap:4px">
      <div class="lbl" style="margin-bottom:2px">Emotes and extras</div>
      <div id="extras"></div>
    </div>
    <div class="grow"></div>
    <div class="field">
      <label for="savef" class="lbl">Save to</label>
      <div class="row"><input id="savef" type="text"><button type="button" class="btn" id="browseOut">Browse…</button></div>
    </div>
    <div class="bar" id="bar"><i></i></div>
    <div class="log" id="log"></div>
    <button type="button" class="big" id="buildBtn">Build</button>
    <div class="sub center" id="buildNote">ComfyUI starts by itself. Takes about 1–2 hours on an 8 GB card.</div>
  </div>
</div>

<!-- ============================== FIX MY MODEL ============================== -->
<div class="page" id="fix">
  <div class="panel">
    <div class="h">Your model</div>
    <div class="ph" style="height:220px">model face icon</div>
    <div style="font-size:18px;font-weight:800" id="fixName">No model built yet</div>
    <div class="sub">Load it in VTube Studio and move around. If something looks off, tick it here. The fix re-runs only the quick steps.</div>
    <div class="grow"></div>
    <button type="button" class="btn" id="openFolder1">Open model folder</button>
    <button type="button" class="btn" disabled title="Coming soon">Save a debug pack</button>
  </div>
  <div class="panel">
    <div style="display:flex;align-items:baseline;gap:12px">
      <div class="h">What looks wrong?</div>
      <div class="sub">Tick all that apply</div>
    </div>
    <div class="issues" id="issues"></div>
  </div>
  <div class="panel">
    <div class="h">The fix</div>
    <div id="fixList" style="display:flex;flex-direction:column;gap:10px"></div>
    <div class="grow"></div>
    <div class="sub">Re-uses the cut-outs from your first build, so no AI step. Your current model is kept; the fixed one is saved next to it.</div>
    <button type="button" class="big" disabled>Fix and rebuild</button>
    <div class="sub center">Coming soon</div>
    <div style="height:1px;background:var(--line);margin:4px 0"></div>
    <div class="sub">Problem not on the list, or still there after a fix? Show it to Claude with your own Claude account.</div>
    <button type="button" class="btn claude" data-goto="claude">Fix with Claude instead</button>
  </div>
</div>

<!-- ============================== FIX WITH CLAUDE ============================== -->
<div class="page" id="claude">
  <div class="panel">
    <div class="h">Your model</div>
    <div class="ph" style="height:200px">model preview</div>
    <div style="font-size:18px;font-weight:800" id="claudeName">No model built yet</div>
    <div style="height:1px;background:var(--line)"></div>
    <div class="h">Claude</div>
    <div class="sub">Needs the Claude desktop app, signed in with your own account. Fixes use your Claude plan. Claude only gets the one model folder you share, never the rest of your PC.</div>
    <div class="grow"></div>
    <button type="button" class="btn" id="openFolder2">Open model folder</button>
  </div>
  <div class="panel">
    <div class="h">1 · Tell Claude what looks wrong</div>
    <label for="ask" class="lbl">In your own words</label>
    <textarea id="ask" placeholder="Example: when I tilt my head the hair swings out like a solid sheet, and strands break apart over the clothes."></textarea>
    <div class="field">
      <div class="lbl">Screenshots from VTube Studio</div>
      <div class="soonbox">Adding screenshots is coming soon. Circle the problem in red if you can, Claude reads the marks.</div>
    </div>
  </div>
  <div class="panel">
    <div class="h">What Claude gets</div>
    <div id="shares"></div>
    <div class="h" style="margin-top:6px">How Claude works</div>
    <div id="rules"></div>
    <div class="grow"></div>
    <div class="sub">Opens a chat in the Claude desktop app with everything above attached. You can keep talking to Claude there until it looks right.</div>
    <button type="button" class="big" disabled>Fix with Claude</button>
    <div class="sub center">Coming soon. Your current model is kept; the fixed one is saved next to it.</div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let cfg = null, glow = 'Green', sheet = null, polling = null;

function toast(msg) { const t = $('toast'); t.textContent = msg; t.classList.add('on'); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove('on'), 2600); }
async function api(path, body, raw) {
  const opt = body === undefined ? {} : { method: 'POST', body: raw ? body : JSON.stringify(body), headers: raw || {} };
  const r = await fetch(path, opt); return r.json();
}
function optRow(name, label, on, soon) {
  return `<label class="opt${soon ? ' soon' : ''}"><input type="checkbox" name="${esc(name)}" value="${esc(label)}"${on ? ' checked' : ''}${soon ? ' disabled' : ''}><span class="t">${esc(label)}</span>${soon ? '<span class="pill">soon</span>' : ''}</label>`;
}
function ticked(name) { return [...document.querySelectorAll(`input[name="${name}"]:checked`)].map((i) => i.value); }

// ---------- tabs
document.querySelectorAll('[data-page],[data-goto]').forEach((b) => b.addEventListener('click', () => {
  const p = b.dataset.page || b.dataset.goto;
  document.querySelectorAll('.tab').forEach((t) => t.classList.toggle('on', t.dataset.page === p));
  document.querySelectorAll('.page').forEach((pg) => pg.classList.toggle('on', pg.id === p));
}));

// ---------- render from config
function render() {
  $('groups').innerHTML = cfg.groups.map((g) => `<fieldset><legend>${esc(g.name)}</legend><div style="display:flex;flex-direction:column;gap:2px">${
    g.items.map((t) => optRow('trait', t, false, cfg.soon.includes(t))).join('')}</div></fieldset>`).join('');
  $('moves').innerHTML = cfg.moves.map(([l, on]) => optRow('move', l, on)).join('');
  $('extras').innerHTML = cfg.extras.map(([l, on]) => optRow('extra', l, on)).join('');
  $('glows').innerHTML = cfg.glows.map(([n, hex]) => `<button type="button" class="sw${n === glow ? ' on' : ''}" aria-label="${esc(n)}" title="${esc(n)}" data-glow="${esc(n)}" style="background:${hex}"></button>`).join('');
  $('issues').innerHTML = cfg.issues.map(([l, d]) => `<label class="issue"><input type="checkbox" name="issue" value="${esc(l)}"><span><b>${esc(l)}</b><small>${esc(d)}</small></span></label>`).join('');
  $('shares').innerHTML = cfg.shares.map((l) => optRow('share', l, true)).join('');
  $('rules').innerHTML = cfg.rules.map(([l, on]) => optRow('rule', l, on)).join('');
  $('savef').value = cfg.default_out;
  renderFix();
}
$('glows').addEventListener('click', (e) => {
  const b = e.target.closest('[data-glow]'); if (!b) return;
  glow = b.dataset.glow; document.querySelectorAll('.sw').forEach((s) => s.classList.toggle('on', s.dataset.glow === glow));
});
function renderFix() {
  const on = ticked('issue');
  document.querySelectorAll('.issue').forEach((l) => l.classList.toggle('on', l.querySelector('input').checked));
  $('fixList').innerHTML = on.length ? on.map((l) => `<div class="card"><b>${esc(l)}</b><small>${esc(cfg.fixes[l] || 'Will be fixed on the next quick rebuild.')}</small></div>`).join('')
    : '<div class="sub">Tick what looks wrong and the fixes show here.</div>';
}
$('issues').addEventListener('change', renderFix);

// ---------- sheet
function showSheet(s) {
  sheet = s;
  $('sheetName').textContent = s ? s.name : 'No sheet yet';
  $('thumb').innerHTML = s ? `<img alt="" src="/api/sheet_preview?t=${Date.now()}">` : 'sheet preview';
  const c = [];
  if (s) {
    c.push(['ok', 'Sheet found']);
    if (s.width) c.push([s.width >= 1024 && s.height >= 1024 ? 'ok' : 'warn', `${s.width} × ${s.height} pixels` + (s.width >= 1024 && s.height >= 1024 ? '' : ' (1024 or bigger works best)')]);
    else c.push(['warn', "Couldn't read the image size"]);
    c.push(['warn', 'Corner marks and part cells are checked when the build starts']);
  }
  const icon = { ok: '<path d="M20 6 9 17l-5-5"></path>', warn: '<path d="M12 8v5M12 17h.01"></path><circle cx="12" cy="12" r="9"></circle>', bad: '<path d="M18 6 6 18M6 6l12 12"></path>' };
  $('checks').innerHTML = c.map(([k, t]) => `<div class="check ${k}"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icon[k]}</svg>${esc(t)}</div>`).join('');
}
$('drop').addEventListener('click', async () => { const r = await api('/api/pick_sheet', {}); if (r.sheet) showSheet(r.sheet); else if (r.error) toast(r.error); });
['dragenter', 'dragover'].forEach((ev) => $('drop').addEventListener(ev, (e) => { e.preventDefault(); $('drop').classList.add('over'); }));
['dragleave', 'drop'].forEach((ev) => $('drop').addEventListener(ev, (e) => { e.preventDefault(); $('drop').classList.remove('over'); }));
$('drop').addEventListener('drop', async (e) => {
  const f = e.dataTransfer.files[0]; if (!f) return;
  if (!/\.(png|jpe?g|webp)$/i.test(f.name)) { toast('Use a PNG, JPG or WEBP image'); return; }
  const r = await api('/api/upload_sheet', await f.arrayBuffer(), { 'X-Filename': encodeURIComponent(f.name) });
  if (r.sheet) showSheet(r.sheet); else toast(r.error || 'Could not use that file');
});

// ---------- prompt + template
$('copyPrompt').addEventListener('click', async () => {
  const traits = ticked('trait');
  const lines = [cfg.prompt_intro, ...traits.map((t) => '- ' + (cfg.prompt_lines[t] || `The character has: ${t.toLowerCase()}.`))];
  if (!traits.length) lines.push('- (Tick traits in the app to add lines here.)');
  lines.push(cfg.prompt_outro);
  const text = lines.join('\n');
  try { await navigator.clipboard.writeText(text); toast('Prompt copied'); }
  catch { const ta = document.createElement('textarea'); ta.value = text; document.body.append(ta); ta.select(); document.execCommand('copy'); ta.remove(); toast('Prompt copied'); }
});
$('saveTemplate').addEventListener('click', async () => { const r = await api('/api/save_template', {}); toast(r.message || r.error); });
$('browseOut').addEventListener('click', async () => { const r = await api('/api/pick_folder', {}); if (r.folder) $('savef').value = r.folder; });
['openFolder1', 'openFolder2'].forEach((id) => $(id).addEventListener('click', async () => { const r = await api('/api/open_folder', { folder: $('savef').value }); if (r.error) toast(r.error); }));

// ---------- build
$('buildBtn').addEventListener('click', async () => {
  const body = { name: $('cname').value, traits: ticked('trait'), movement: ticked('move'), extras: ticked('extra'), eye_glow: glow, output_dir: $('savef').value };
  const r = await api('/api/build', body);
  if (r.errors) { toast(r.errors.join(' · ')); return; }
  $('buildBtn').disabled = true; $('bar').style.display = 'block'; $('log').style.display = 'block'; $('log').textContent = '';
  polling = setInterval(poll, 1000); poll();
});
async function poll() {
  const s = await api('/api/status');
  $('log').textContent = s.log.join('\n'); $('log').scrollTop = 1e9;
  if (!s.running) {
    clearInterval(polling); $('buildBtn').disabled = false; $('bar').style.display = 'none';
    if (s.message) toast(s.message);
    if (s.ok && s.model_name) { $('fixName').textContent = s.model_name; $('claudeName').textContent = s.model_name; }
  }
}

api('/api/config').then((c) => { cfg = c; render(); if (c.sheet) showSheet(c.sheet); });
</script>
</body>
</html>
'''


if __name__ == "__main__":
    main()
