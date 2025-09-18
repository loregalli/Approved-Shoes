# Approved Shoes Python Interface

import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk


EVENT_ORDER = ["Track", "Jumps", "Throws", "Road & RW", "Cross"]
PLACEHOLDERS = {
    "brand": "Select brand",
    "model": "Select model",
    "event": "Select event",
}

# --------------------------- DB ACCESS ---------------------------

# Open connection with the DataBase
def open_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# Query to retrieve Brands
def fetch_brands(conn: sqlite3.Connection) -> list[str]:
    cur = conn.cursor()
    cur.execute("SELECT name FROM brand ORDER BY name COLLATE NOCASE;")
    return [r[0] for r in cur.fetchall()]

# Query to retrieve Events
def fetch_events(conn: sqlite3.Connection) -> list[str]:
    cur = conn.cursor()
    cur.execute("SELECT name FROM event;")
    present = {r[0] for r in cur.fetchall()}
    return [e for e in EVENT_ORDER if e in present]

# Query to retrieve Models
def fetch_models_for_brand(conn: sqlite3.Connection, brand: str) -> list[str]:
    cur = conn.cursor()
    cur.execute("SELECT name FROM model WHERE brand = ? ORDER BY name COLLATE NOCASE;", (brand,))
    rows = [r[0] for r in cur.fetchall()]
    # Place "Other models" last
    others = [m for m in rows if m.lower().startswith("other (older models)")]
    normal = [m for m in rows if m not in others]
    return normal + others

# Check approval
def is_approved_today(conn: sqlite3.Connection, brand: str, model: str, event: str) -> bool:
    cur = conn.cursor()
    cur.execute("""
        SELECT EXISTS(
          SELECT 1
          FROM model_event_approval
          WHERE brand = ?
            AND model = ?
            AND event = ?
            AND (valid_from IS NULL OR valid_from <= DATE('now'))
            AND (valid_to   IS NULL OR valid_to   >= DATE('now'))
        );
    """, (brand, model, event))
    return cur.fetchone()[0] == 1


# --------------------------- GUI ---------------------------

class ShoeCheckerApp(tk.Tk):
    def __init__(self, db_path: str):
        super().__init__()
        self.title("👟 Shoe Approval Checker")
        self.geometry("600x460")
        self.minsize(560, 440)

        # --- White background + ttk styles ---
        self.configure(bg="white")
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("White.TFrame", background="white")
        style.configure("White.TLabel", background="white")
        style.configure("Header.TLabel", font=("TkDefaultFont", 18, "bold"), background="white")
        style.configure("Subheader.TLabel", foreground="#666", background="white")
        style.configure("Result.TLabel", font=("TkDefaultFont", 14, "bold"), background="white")

        # DB connection
        try:
            self.conn = open_connection(db_path)
        except Exception as e:
            messagebox.showerror("Database error", f"Cannot open DB:\n{e}")
            self.destroy()
            return

        # State
        self.brand_var = tk.StringVar(value=PLACEHOLDERS["brand"])
        self.model_var = tk.StringVar(value=PLACEHOLDERS["model"])
        self.event_var = tk.StringVar(value=PLACEHOLDERS["event"])
        self.result_var = tk.StringVar(value="—")

        # Main frame (vertical layout)
        root = ttk.Frame(self, padding=16, style="White.TFrame")
        root.pack(fill="both", expand=True)

        # Make root responsive with an inner grid
        root.grid_columnconfigure(0, weight=1)

        # --- Logo ---
        try:
            # Load original once
            self.logo_src = Image.open("logo.png")
            self.logo_img = None

            self.logo_lbl = ttk.Label(root, style="White.TLabel", anchor="center")
            self.logo_lbl.grid(row=0, column=0, pady=(0, 8), sticky="n")

            def update_logo(_evt=None):
                # Compute a max width/height based on window size
                max_w = max(140, int(self.winfo_width() * 0.28))
                max_h = max(60,  int(self.winfo_height() * 0.18))

                # Preserve aspect ratio
                w, h = self.logo_src.size
                scale = min(max_w / w, max_h / h, 1.0)
                new_size = (max(1, int(w * scale)), max(1, int(h * scale)))

                img = self.logo_src.resize(new_size, Image.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                self.logo_lbl.configure(image=self.logo_img)

            update_logo()
            self.bind("<Configure>", update_logo)

        except Exception:
            pass

        # --- Title and Description ---
        # ttk.Label(root, text="🏃‍♂️ Shoe Approval Checker", style="Header.TLabel", anchor="center", justify="center").grid(row=1, column=0, sticky="ew")
        ttk.Label(root, text="Select brand, model and event. Approval is checked for today's date.",
                  style="Subheader.TLabel", anchor="center", justify="center").grid(row=2, column=0, pady=(0, 16), sticky="ew")

        # --- Dropdowns ---
        form = ttk.Frame(root, style="White.TFrame")
        form.grid(row=3, column=0, sticky="ew")
        form.grid_columnconfigure(0, weight=0)
        form.grid_columnconfigure(1, weight=1)

        ttk.Label(form, text="Brand", style="White.TLabel").grid(row=0, column=0, sticky="w", pady=6, padx=(0, 8))
        self.brand_cb = ttk.Combobox(form, textvariable=self.brand_var, state="readonly")
        self.brand_cb.grid(row=0, column=1, sticky="ew", pady=6)

        ttk.Label(form, text="Model", style="White.TLabel").grid(row=1, column=0, sticky="w", pady=6, padx=(0, 8))
        self.model_cb = ttk.Combobox(form, textvariable=self.model_var, state="disabled")
        self.model_cb.grid(row=1, column=1, sticky="ew", pady=6)

        ttk.Label(form, text="Event", style="White.TLabel").grid(row=2, column=0, sticky="w", pady=6, padx=(0, 8))
        self.event_cb = ttk.Combobox(form, textvariable=self.event_var, state="readonly")
        self.event_cb.grid(row=2, column=1, sticky="ew", pady=6)

        # --- Buttons (Check + Reset) ---
        buttons = ttk.Frame(root, style="White.TFrame")
        buttons.grid(row=4, column=0, pady=(12, 8), sticky="ew")
        buttons.grid_columnconfigure(0, weight=1)
        buttons.grid_columnconfigure(1, weight=1)

        self.check_btn = ttk.Button(buttons, text="Check approval (today)", command=self.on_check)
        self.check_btn.grid(row=0, column=0, sticky="e", padx=(0, 6))

        self.reset_btn = ttk.Button(buttons, text="Reset", command=self.on_reset)
        self.reset_btn.grid(row=0, column=1, sticky="w", padx=(6, 0))

        # --- Result ---
        self.result_label = ttk.Label(root, textvariable=self.result_var, style="Result.TLabel",
                                      anchor="center", justify="center")
        self.result_label.grid(row=5, column=0, pady=(8, 0), sticky="ew")

        # Populate dropdowns
        try:
            brands = fetch_brands(self.conn)
            events = fetch_events(self.conn)
        except Exception as e:
            messagebox.showerror("Database error", f"Failed to load data:\n{e}")
            self.destroy()
            return

        self.brand_cb["values"] = [PLACEHOLDERS["brand"]] + brands
        self.event_cb["values"] = [PLACEHOLDERS["event"]] + events
        self.brand_cb.current(0)
        self.event_cb.current(0)

        # Bindings
        self.brand_cb.bind("<<ComboboxSelected>>", self.on_brand_changed)

        # Let the outermost row expand to keep spacing tidy on resize
        root.grid_rowconfigure(6, weight=1)

    # If the user hasn’t picked a real brand yet (only the placeholder), the model menu gets disabled and shows only its placeholder.
    def on_brand_changed(self, _evt=None):
        brand = self.brand_var.get()
        if brand == PLACEHOLDERS["brand"]:
            self.model_cb["values"] = [PLACEHOLDERS["model"]]
            self.model_var.set(PLACEHOLDERS["model"])
            self.model_cb.state(["disabled"])
            return

        try:
            models = fetch_models_for_brand(self.conn, brand)
        except Exception as e:
            messagebox.showerror("Database error", f"Failed to load models for '{brand}':\n{e}")
            models = []

        self.model_cb["values"] = [PLACEHOLDERS["model"]] + models
        self.model_var.set(PLACEHOLDERS["model"])
        self.model_cb.state(["!disabled", "readonly"])

    def on_check(self):
        brand = self.brand_var.get()
        model = self.model_var.get()
        event = self.event_var.get()

        if (brand == PLACEHOLDERS["brand"] or
            model == PLACEHOLDERS["model"] or
            event == PLACEHOLDERS["event"]):
            messagebox.showwarning("Missing fields", "Please select brand, model and event.")
            return

        try:
            ok = is_approved_today(self.conn, brand, model, event)
        except Exception as e:
            messagebox.showerror("Query error", f"Failed to check approval:\n{e}")
            return

        if ok:
            self.result_var.set("APPROVED ✅")
            self.result_label.configure(foreground="#0A7D00")
        else:
            self.result_var.set("NOT APPROVED ❌")
            self.result_label.configure(foreground="#B00020")

    def on_reset(self):
        """Restore placeholders and disable Model."""
        self.brand_var.set(PLACEHOLDERS["brand"])
        self.model_var.set(PLACEHOLDERS["model"])
        self.event_var.set(PLACEHOLDERS["event"])
        self.result_var.set("—")

        # Reset combobox values to keep placeholders visible (brand/event values lists already loaded)
        self.brand_cb.current(0)
        self.event_cb.current(0)

        self.model_cb["values"] = [PLACEHOLDERS["model"]]
        self.model_cb.state(["disabled"])

        # Reset result color
        self.result_label.configure(foreground="black")

    def destroy(self):
        try:
            if hasattr(self, "conn") and self.conn:
                self.conn.close()
        finally:
            super().destroy()

def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else "shoes.db"
    app = ShoeCheckerApp(db_path)
    try:
        app.mainloop()
    except Exception:
        pass

if __name__ == "__main__":
    main()
    
# Lorenzo Galli