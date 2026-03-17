import time
import threading
import tkinter as tk
import random
from pynput import keyboard
from pynput.mouse import Controller as MouseController, Button
import requests
import os
import sys
import time


# ------- MAJ -------
# -------- CONFIG UPDATE --------
VERSION_FILE = "version.txt"
SCRIPT_NAME = os.path.basename(__file__)

GITHUB_VERSION_URL = "https://raw.githubusercontent.com/leobzh/HuntyZombieScript/main/Version.txt"
GITHUB_SCRIPT_URL = "https://raw.githubusercontent.com/leobzh/HuntyZombieScript/main/AutoClickerCapacity.py"

# -------- LECTURE VERSION LOCALE --------
def get_local_version():
    if not os.path.exists(VERSION_FILE):
        return "0"
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"⚠️ Impossible de lire {VERSION_FILE}: {e}")
        return "0"

# -------- RÉCUP VERSION DISTANTE --------
def get_remote_version():
    try:
        r = requests.get(GITHUB_VERSION_URL, timeout=5)
        if r.status_code == 200:
            return r.text.strip()
        else:
            print(f"⚠️ Erreur version distante (HTTP {r.status_code})")
            return None
    except Exception as e:
        print(f"⚠️ Erreur connexion GitHub: {e}")
        return None

# -------- TÉLÉCHARGEMENT FICHIER --------
def download_file(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.text
        else:
            print(f"⚠️ Erreur téléchargement {url} (HTTP {r.status_code})")
            return None
    except Exception as e:
        print(f"⚠️ Erreur téléchargement {url}: {e}")
        return None

# -------- MISE À JOUR --------
def update():
    print("🔄 Mise à jour...")

    new_script = download_file(GITHUB_SCRIPT_URL)
    new_version = download_file(GITHUB_VERSION_URL)

    # Si téléchargement échoue → abandon
    if new_script is None or new_version is None:
        print("❌ Update annulé (impossible de récupérer les fichiers)")
        return

    try:
        # écriture script temporaire
        with open("update_tmp.py", "w", encoding="utf-8") as f:
            f.write(new_script)

        # écriture version
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            f.write(new_version)

        # remplacement script actuel
        os.replace("update_tmp.py", SCRIPT_NAME)

        print("✅ Mise à jour terminée")

        # relancer le script
        time.sleep(1)
        os.execv(sys.executable, ["python"] + [SCRIPT_NAME])

    except Exception as e:
        print(f"❌ Erreur update: {e}")

# -------- CHECK UPDATE --------
def check_update():
    local = get_local_version()
    remote = get_remote_version()

    if remote is None:
        print("⚠️ Mise à jour ignorée (impossible de récupérer version distante)")
        return

    if local != remote:
        print(f"🔔 Nouvelle version disponible : {remote} (locale : {local})")
        update()
    else:
        print("✅ Script à jour")

# -------- LANCEMENT DE LA VÉRIFICATION --------
check_update()







# -------- CONFIG --------
ALL_KEYS = ["w", "x", "c"]
KEY_SEQUENCE = []

USE_Z_HOLD = False
USE_E_SPAM = False

CYCLE_PAUSE = 2
CLICK_BASE = 0.15
CLICK_VARIATION = 0.05

running = False
thread = None
z_thread = None

kb = keyboard.Controller()
mouse = MouseController()

# -------- Z HOLD --------
def z_hold_loop():
    global running

    kb.press("z")

    while running:
        time.sleep(0.1)

    kb.release("z")


# -------- LOGIQUE PRINCIPALE --------
def main_loop():
    global running

    while running:

        # -------- AUTO CLICK --------
        start_time = time.time()

        while running and (time.time() - start_time < CYCLE_PAUSE):
            mouse.press(Button.left)
            time.sleep(random.uniform(0.02, 0.05))
            mouse.release(Button.left)

            sleep_time = CLICK_BASE + random.uniform(-CLICK_VARIATION, CLICK_VARIATION)
            time.sleep(max(0.05, sleep_time))

        if not running:
            break

        time.sleep(0.15)

        # -------- TOUCHES --------
        for i, key in enumerate(KEY_SEQUENCE):
            if not running:
                break

            if i == 0:
                time.sleep(0.1)

            kb.press(key)
            time.sleep(random.uniform(0.08, 0.15))
            kb.release(key)

            time.sleep(random.uniform(0.12, 0.25))


# -------- TOGGLE --------
def toggle():
    global running, thread, z_thread

    running = not running
    update_ui()

    if running:
        if thread is None or not thread.is_alive():
            thread = threading.Thread(target=main_loop, daemon=True)
            thread.start()

        if USE_Z_HOLD:
            if z_thread is None or not z_thread.is_alive():
                z_thread = threading.Thread(target=z_hold_loop, daemon=True)
                z_thread.start()


# -------- UI --------
def update_ui():
    status_value.config(
        text="ON" if running else "OFF",
        fg="#00ff88" if running else "#ff5555"
    )


def start_move(e):
    root.x_offset = e.x
    root.y_offset = e.y


def on_move(e):
    x = e.x_root - root.x_offset
    y = e.y_root - root.y_offset
    root.geometry(f"+{x}+{y}")


# -------- FENÊTRE DE SÉLECTION --------
def launch_main():
    global KEY_SEQUENCE, USE_Z_HOLD, USE_E_SPAM

    KEY_SEQUENCE = [k for k, var in key_vars.items() if var.get()]
    USE_Z_HOLD = z_var.get()
    USE_E_SPAM = e_var.get()

    # ajout de E si activé
    if USE_E_SPAM:
        KEY_SEQUENCE.append("e")

    if not KEY_SEQUENCE and not USE_Z_HOLD:
        return

    select_window.destroy()
    build_main_ui()


select_window = tk.Tk()
select_window.title("Choix des touches")
select_window.geometry("260x260")
select_window.configure(bg="#151515")

tk.Label(
    select_window,
    text="Choisis les touches",
    bg="#151515",
    fg="white",
    font=("Segoe UI", 11)
).pack(pady=10)

key_vars = {}
for key in ALL_KEYS:
    var = tk.BooleanVar(value=True)
    key_vars[key] = var

    tk.Checkbutton(
        select_window,
        text=key.upper(),
        variable=var,
        bg="#151515",
        fg="white",
        selectcolor="#222222",
        activebackground="#151515"
    ).pack(anchor="w", padx=40)

# -------- Z HOLD --------
z_var = tk.BooleanVar(value=False)

tk.Checkbutton(
    select_window,
    text="Maintenir Z",
    variable=z_var,
    bg="#151515",
    fg="#00ffcc",
    selectcolor="#222222",
    activebackground="#151515"
).pack(anchor="w", padx=40, pady=(10, 0))

# -------- E SPAM --------
e_var = tk.BooleanVar(value=False)

tk.Checkbutton(
    select_window,
    text="Spam E",
    variable=e_var,
    bg="#151515",
    fg="#ffaa00",
    selectcolor="#222222",
    activebackground="#151515"
).pack(anchor="w", padx=40, pady=(5, 0))

tk.Button(
    select_window,
    text="Start",
    command=launch_main
).pack(pady=15)


# -------- UI PRINCIPALE --------
def build_main_ui():
    global root, status_value

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.92)
    root.geometry("300x220+60+60")
    root.configure(bg="#0f0f0f")

    frame = tk.Frame(root, bg="#151515", bd=1, relief="solid")
    frame.pack(expand=True, fill="both")

    topbar = tk.Frame(frame, bg="#202020", height=28)
    topbar.pack(fill="x")
    topbar.bind("<Button-1>", start_move)
    topbar.bind("<B1-Motion>", on_move)

    tk.Label(
        topbar, text="Smart Auto Farm",
        bg="#202020", fg="#cccccc",
        font=("Segoe UI", 10)
    ).place(x=10, y=5)

    close_btn = tk.Label(
        topbar, text="✕",
        bg="#202020", fg="#888888",
        font=("Segoe UI", 11, "bold")
    )
    close_btn.place(relx=1.0, x=-24, y=4)
    close_btn.bind("<Button-1>", lambda e: root.quit())

    content = tk.Frame(frame, bg="#151515")
    content.pack(expand=True, fill="both", padx=16, pady=12)

    tk.Label(
        content, text="STATUS",
        fg="#777777", bg="#151515",
        font=("Segoe UI", 9)
    ).pack(anchor="w")

    status_value = tk.Label(
        content, text="OFF",
        fg="#ff5555", bg="#151515",
        font=("Segoe UI", 28, "bold")
    )
    status_value.pack(anchor="w", pady=(0, 10))

    tk.Label(
        content,
        text=f"Touches : {' '.join(KEY_SEQUENCE).upper()}",
        fg="#aaaaaa",
        bg="#151515",
        font=("Segoe UI", 10)
    ).pack(anchor="w")

    if USE_Z_HOLD:
        tk.Label(
            content,
            text="Z maintenu en continu",
            fg="#00ffcc",
            bg="#151515",
            font=("Segoe UI", 9)
        ).pack(anchor="w")

    if USE_E_SPAM:
        tk.Label(
            content,
            text="Spam E activé",
            fg="#ffaa00",
            bg="#151515",
            font=("Segoe UI", 9)
        ).pack(anchor="w")

    tk.Label(
        content,
        text=") = ON / OFF",
        fg="#666666",
        bg="#151515",
        font=("Segoe UI", 8)
    ).pack(side="bottom", pady=(8, 0))

    update_ui()

    def on_key_press(key):
        try:
            if hasattr(key, "char") and key.char == ")":
                root.after(0, toggle)
        except:
            pass

    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    root.mainloop()


# lancer sélection
select_window.mainloop()