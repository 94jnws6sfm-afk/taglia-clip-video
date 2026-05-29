#!/usr/bin/env python3
"""
⚽ Taglia Clip Video — App Mac
Taglia automaticamente i momenti salienti da un video di partita.
Doppio click su un clip per rinominarlo.
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, os, time, threading, json

# ── Colori stile macOS dark ────────────────────────────────────────────────
BG     = "#1C1C1E"
CARD   = "#2C2C2E"
BORDER = "#3A3A3C"
TEXT   = "#FFFFFF"
MUTED  = "#8E8E93"
GREEN  = "#30D158"
RED    = "#FF453A"
BLUE   = "#0A84FF"
YELLOW = "#FFD60A"


def fmt_display(secs: float) -> str:
    """Formato MM:SS.d per il timer"""
    secs = max(0.0, secs)
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    d = int((secs % 1) * 10)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}.{d}"
    return f"{m:02d}:{s:02d}.{d}"


def fmt_ffmpeg(secs: float) -> str:
    """Formato HH:MM:SS per ffmpeg"""
    secs = max(0.0, secs)
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("⚽ Taglia Clip Video")
        self.root.geometry("760x840")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        # Stato timer
        self._running     = False
        self._elapsed     = 0.0
        self._t0          = 0.0
        self._pend_start  = None   # inizio clip in attesa

        # Lista clip
        self.clips: list[dict] = []

        # Percorsi
        self.video_path = tk.StringVar()
        self.out_dir    = tk.StringVar(value="clips")

        self._build()
        self._tick()

    # ── Costruzione UI ────────────────────────────────────────────────────

    def _build(self):
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=18, pady=18)

        # Titolo
        tk.Label(main, text="⚽  Taglia Clip Video",
                 font=("Helvetica Neue", 22, "bold"),
                 bg=BG, fg=TEXT).pack(pady=(0, 14))

        # ── Scheda Timer ──────────────────────────────────────────────────
        tc = self._card(main)
        tc.pack(fill="x", pady=(0, 10))
        p = tk.Frame(tc, bg=CARD); p.pack(padx=22, pady=18)

        tk.Label(p, text="TIMER PARTITA",
                 font=("Helvetica Neue", 10), bg=CARD, fg=MUTED).pack()

        self.timer_lbl = tk.Label(p, text="00:00.0",
                                   font=("Menlo", 62, "bold"),
                                   bg=CARD, fg=TEXT)
        self.timer_lbl.pack(pady=6)

        br = tk.Frame(p, bg=CARD); br.pack()
        self.play_btn = self._btn(br, "▶  Avvia", self._toggle, BLUE, w=14)
        self.play_btn.pack(side="left", padx=6)
        self._btn(br, "⟳  Azzera", self._reset, "#636366", w=10).pack(side="left", padx=6)

        tk.Label(p, text="Avvia il timer quando premi play sul video, poi segna inizio e fine di ogni azione",
                 font=("Helvetica Neue", 11), bg=CARD, fg=MUTED,
                 wraplength=500).pack(pady=(10, 0))

        # ── Scheda Segna ─────────────────────────────────────────────────
        mc = self._card(main); mc.pack(fill="x", pady=(0, 10))
        p2 = tk.Frame(mc, bg=CARD); p2.pack(padx=22, pady=16)

        self.pend_lbl = tk.Label(p2, text="⏺  Inizio segnato: —",
                                  font=("Helvetica Neue", 14),
                                  bg=CARD, fg=MUTED)
        self.pend_lbl.pack(pady=(0, 12))

        mr = tk.Frame(p2, bg=CARD); mr.pack()
        self._btn(mr, "🔴   Segna INIZIO",  self._mark_start, RED,   w=20).pack(side="left", padx=10)
        self._btn(mr, "🟢   Segna FINE",    self._mark_end,   GREEN, w=20).pack(side="left", padx=10)

        # ── Scheda Lista Clip ─────────────────────────────────────────────
        lc = self._card(main); lc.pack(fill="both", expand=True, pady=(0, 10))
        p3 = tk.Frame(lc, bg=CARD); p3.pack(fill="both", expand=True, padx=22, pady=14)

        hr = tk.Frame(p3, bg=CARD); hr.pack(fill="x", pady=(0, 8))
        tk.Label(hr, text="CLIP SALVATE",
                 font=("Helvetica Neue", 10), bg=CARD, fg=MUTED).pack(side="left")
        self.cnt_lbl = tk.Label(hr, text="0 clip",
                                 font=("Helvetica Neue", 10), bg=CARD, fg=MUTED)
        self.cnt_lbl.pack(side="right")
        tk.Label(hr, text="(doppio click per rinominare)",
                 font=("Helvetica Neue", 10), bg=CARD, fg=MUTED).pack(side="right", padx=10)

        # Stile tabella
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("C.Treeview",
                    background=CARD, foreground=TEXT, fieldbackground=CARD,
                    rowheight=30, font=("Menlo", 12), borderwidth=0)
        s.configure("C.Treeview.Heading",
                    background=BORDER, foreground=MUTED,
                    font=("Helvetica Neue", 11), relief="flat")
        s.map("C.Treeview", background=[("selected", "#0A84FF55")])

        cols = ("#", "Inizio", "Fine", "Durata", "Nome")
        self.tree = ttk.Treeview(p3, columns=cols, show="headings",
                                  style="C.Treeview", selectmode="browse", height=7)
        for col, w, anch in zip(cols, [36, 90, 90, 80, 240],
                                       ["center"]*4 + ["w"]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=anch, stretch=(col == "Nome"))

        sb = ttk.Scrollbar(p3, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self._rename_clip)

        dr = tk.Frame(p3, bg=CARD); dr.pack(fill="x", pady=(10, 0))
        self._btn(dr, "🗑  Rimuovi",       self._remove_clip, "#636366", w=14).pack(side="left", padx=(0, 8))
        self._btn(dr, "💾  Salva lista",   self._save_list,   "#636366", w=14).pack(side="left", padx=(0, 8))
        self._btn(dr, "📂  Carica lista",  self._load_list,   "#636366", w=14).pack(side="left")

        # ── Scheda File ───────────────────────────────────────────────────
        fc = self._card(main); fc.pack(fill="x", pady=(0, 10))
        p4 = tk.Frame(fc, bg=CARD); p4.pack(fill="x", padx=22, pady=14)

        for lbl, var, cmd in [
            ("Video:",  self.video_path, self._pick_video),
            ("Cartella:", self.out_dir,    self._pick_outdir),
        ]:
            row = tk.Frame(p4, bg=CARD); row.pack(fill="x", pady=4)
            tk.Label(row, text=lbl, font=("Helvetica Neue", 13), width=7,
                     bg=CARD, fg=TEXT, anchor="w").pack(side="left")
            tk.Entry(row, textvariable=var, font=("Menlo", 12),
                     bg=BORDER, fg=TEXT, insertbackground=TEXT,
                     relief="flat", bd=4).pack(side="left", fill="x", expand=True, padx=(0, 8))
            self._btn(row, "Scegli", cmd, "#636366", w=8).pack(side="right")

        # ── Bottone Taglia ────────────────────────────────────────────────
        tk.Button(main, text="✂️   TAGLIA VIDEO",
                  font=("Helvetica Neue", 16, "bold"),
                  bg=GREEN, fg="#000000", activebackground="#28A846",
                  relief="flat", bd=0, pady=14, cursor="hand2",
                  command=self._cut).pack(fill="x", pady=(0, 6))

        self.status_lbl = tk.Label(main, text="",
                                    font=("Helvetica Neue", 12),
                                    bg=BG, fg=MUTED)
        self.status_lbl.pack()

    def _card(self, parent):
        return tk.Frame(parent, bg=CARD, highlightthickness=1,
                        highlightbackground=BORDER)

    def _btn(self, parent, text, cmd, color, w=None):
        kw = dict(font=("Helvetica Neue", 13), bg=color, fg=TEXT,
                  activebackground=color, relief="flat", bd=0,
                  padx=12, pady=8, cursor="hand2", command=cmd)
        if w:
            kw["width"] = w
        return tk.Button(parent, text=text, **kw)

    # ── Timer ─────────────────────────────────────────────────────────────

    def _tick(self):
        if self._running:
            self._elapsed = time.time() - self._t0
        self.timer_lbl.config(text=fmt_display(self._elapsed))
        self.root.after(100, self._tick)

    def _toggle(self):
        if self._running:
            self._elapsed = time.time() - self._t0
            self._running = False
            self.play_btn.config(text="▶  Riprendi")
        else:
            self._t0 = time.time() - self._elapsed
            self._running = True
            self.play_btn.config(text="⏸  Pausa")

    def _reset(self):
        self._running    = False
        self._elapsed    = 0.0
        self._pend_start = None
        self.play_btn.config(text="▶  Avvia")
        self.pend_lbl.config(text="⏺  Inizio segnato: —", fg=MUTED)

    # ── Segna ─────────────────────────────────────────────────────────────

    def _mark_start(self):
        self._pend_start = self._elapsed
        self.pend_lbl.config(
            text=f"⏺  Inizio segnato: {fmt_display(self._pend_start)}",
            fg=RED)

    def _mark_end(self):
        if self._pend_start is None:
            messagebox.showwarning("Attenzione", "Prima premi '🔴 Segna INIZIO'!")
            return
        end = self._elapsed
        if end <= self._pend_start:
            messagebox.showwarning("Attenzione", "La fine deve essere dopo l'inizio!")
            return
        self.clips.append({
            "start": self._pend_start,
            "end":   end,
            "label": f"Azione {len(self.clips) + 1}"
        })
        self._pend_start = None
        self.pend_lbl.config(text="⏺  Inizio segnato: —", fg=MUTED)
        self._refresh()

    # ── Lista clip ────────────────────────────────────────────────────────

    def _refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, c in enumerate(self.clips):
            dur = c["end"] - c["start"]
            self.tree.insert("", "end", iid=str(i), values=(
                i + 1,
                fmt_ffmpeg(c["start"]),
                fmt_ffmpeg(c["end"]),
                fmt_ffmpeg(dur),
                c["label"],
            ))
        self.cnt_lbl.config(text=f"{len(self.clips)} clip")

    def _remove_clip(self):
        sel = self.tree.selection()
        if not sel:
            return
        self.clips.pop(int(sel[0]))
        self._refresh()

    def _rename_clip(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        old = self.clips[idx]["label"]

        win = tk.Toplevel(self.root)
        win.title("Rinomina clip")
        win.configure(bg=CARD)
        win.geometry("360x130")
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="Nome clip:",
                 font=("Helvetica Neue", 13), bg=CARD, fg=TEXT).pack(pady=(18, 6))
        var = tk.StringVar(value=old)
        e = tk.Entry(win, textvariable=var, font=("Menlo", 13),
                     bg=BORDER, fg=TEXT, insertbackground=TEXT,
                     relief="flat", bd=4, width=30)
        e.pack()
        e.select_range(0, "end")
        e.focus()

        def ok(ev=None):
            self.clips[idx]["label"] = var.get().strip() or old
            self._refresh()
            win.destroy()

        tk.Button(win, text="Conferma", font=("Helvetica Neue", 13),
                  bg=BLUE, fg=TEXT, relief="flat", bd=0,
                  pady=7, padx=30, cursor="hand2",
                  command=ok).pack(pady=12)
        win.bind("<Return>", ok)

    def _save_list(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="tagli.json")
        if not path:
            return
        with open(path, "w") as f:
            json.dump(self.clips, f, indent=2)
        self.status_lbl.config(text=f"✅ Lista salvata: {os.path.basename(path)}", fg=GREEN)

    def _load_list(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path) as f:
                self.clips = json.load(f)
            self._refresh()
            self.status_lbl.config(text=f"📂 Caricati {len(self.clips)} clip", fg=BLUE)
        except Exception as ex:
            messagebox.showerror("Errore", f"Impossibile caricare: {ex}")

    # ── File ──────────────────────────────────────────────────────────────

    def _pick_video(self):
        p = filedialog.askopenfilename(
            filetypes=[("Video", "*.mp4 *.mov *.avi *.mkv *.m4v"), ("Tutti", "*.*")])
        if p:
            self.video_path.set(p)
            self.out_dir.set(os.path.join(os.path.dirname(p), "clips"))

    def _pick_outdir(self):
        p = filedialog.askdirectory()
        if p:
            self.out_dir.set(p)

    # ── Taglia ────────────────────────────────────────────────────────────

    def _cut(self):
        if not self.clips:
            messagebox.showwarning("Attenzione", "Nessuna clip salvata!")
            return
        video = self.video_path.get().strip()
        if not video or not os.path.exists(video):
            messagebox.showwarning("Attenzione", "Seleziona prima il file video!")
            return
        outdir = self.out_dir.get().strip() or "clips"
        os.makedirs(outdir, exist_ok=True)

        self.status_lbl.config(text="⏳ Taglio in corso…", fg=YELLOW)
        self.root.update()

        def run():
            errors = []
            total = len(self.clips)
            for i, c in enumerate(self.clips):
                start   = fmt_ffmpeg(c["start"])
                dur_s   = fmt_ffmpeg(c["end"] - c["start"])
                label   = "".join(ch if ch.isalnum() or ch in "_ -" else "_"
                                  for ch in c["label"]).strip().replace(" ", "_")
                outfile = os.path.join(outdir, f"{i+1:02d}_{label}.mp4")

                cmd = ["ffmpeg", "-y",
                       "-ss", start, "-i", video,
                       "-t", dur_s, "-c", "copy", outfile]
                try:
                    r = subprocess.run(cmd, capture_output=True, timeout=600)
                    if r.returncode != 0:
                        errors.append(f"Clip {i+1} ({c['label']}): errore ffmpeg\n"
                                      + r.stderr.decode(errors="replace")[:300])
                except FileNotFoundError:
                    errors.append(
                        "ffmpeg non trovato!\n\n"
                        "Installalo con:\n"
                        "  brew install ffmpeg")
                    break
                except Exception as ex:
                    errors.append(f"Clip {i+1}: {ex}")

                self.status_lbl.config(text=f"⏳ Clip {i+1}/{total}…", fg=YELLOW)
                self.root.update()

            if errors:
                self.status_lbl.config(text="❌ Alcuni errori — vedi popup", fg=RED)
                messagebox.showerror("Errori", "\n\n".join(errors))
            else:
                self.status_lbl.config(
                    text=f"✅ {total} clip salvate in: {outdir}", fg=GREEN)
                messagebox.showinfo("Completato! 🎉",
                    f"{total} clip salvate in:\n{outdir}")

        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
