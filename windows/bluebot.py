"""
bluebot.py — Application Windows BlueBot App Blocker
=====================================================
Lance avec :  python bluebot.py
Dépendances : pip install customtkinter psutil pillow
"""

import customtkinter as ctk
import psutil
import threading
import time
import os
import sys
from pathlib import Path

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ─── Thème ────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BLEU       = "#1565C0"
BLEU_CLAIR = "#4FC3F7"
ROUGE      = "#C62828"
VERT       = "#2E7D32"
ORANGE     = "#E65100"
FOND       = "#0D1117"
SURFACE    = "#161B22"
SURFACE2   = "#1F2937"
BLANC      = "#FFFFFF"
GRIS       = "#8B949E"

POLICE_TITRE  = ("Segoe UI", 20, "bold")
POLICE_NORMAL = ("Segoe UI", 13)
POLICE_PETIT  = ("Segoe UI", 11)


# ═══════════════════════════════════════════════════════════════
# Modèle de données
# ═══════════════════════════════════════════════════════════════

class Bloc:
    """Représente un bloc actif sur une application."""

    def __init__(self, nom_process: str, nom_affiche: str, duree_sec: int):
        self.nom_process  = nom_process   # ex: "chrome.exe"
        self.nom_affiche  = nom_affiche   # ex: "Google Chrome"
        self.duree_sec    = duree_sec     # durée totale
        self.restant_sec  = duree_sec     # compteur
        self.actif        = True
        self.expire       = False         # True quand le timer est à 0

    def temps_formate(self) -> str:
        s = max(0, self.restant_sec)
        h = s // 3600
        m = (s % 3600) // 60
        sec = s % 60
        if h > 0:
            return f"{h}h {m:02d}min"
        if m > 0:
            return f"{m}min {sec:02d}s"
        return f"{sec}s"

    def pourcentage(self) -> float:
        if self.duree_sec <= 0:
            return 0.0
        return max(0.0, min(1.0, self.restant_sec / self.duree_sec))


# ═══════════════════════════════════════════════════════════════
# Application principale
# ═══════════════════════════════════════════════════════════════

class BlueBotApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.blocs: dict[str, Bloc] = {}
        self.processus: list[tuple[str, str]] = []   # [(nom_affiche, nom_process)]
        self.selection: tuple | None = None
        self._widgets_blocs: dict[str, dict] = {}    # pour les mises à jour live

        self._configurer_fenetre()
        self._construire_interface()
        self._charger_processus()
        self._boucle_rafraichissement()

    # ─── Fenêtre ──────────────────────────────────────────────

    def _configurer_fenetre(self):
        self.title("BlueBot — App Blocker")
        self.geometry("980x660")
        self.minsize(820, 560)
        self.configure(fg_color=FOND)

    # ─── Interface ────────────────────────────────────────────

    def _construire_interface(self):
        # ── Header ─────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=SURFACE, height=68, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        if PIL_OK:
            try:
                img = ctk.CTkImage(
                    light_image=Image.open(_logo()),
                    dark_image=Image.open(_logo()),
                    size=(46, 46)
                )
                ctk.CTkLabel(header, image=img, text="").pack(side="left", padx=(14, 6), pady=10)
            except Exception:
                pass

        ctk.CTkLabel(header, text="BlueBot",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=BLANC).pack(side="left", pady=10)

        ctk.CTkLabel(header, text=" — App Blocker   |   FIRST Tech Challenge Reims",
                     font=ctk.CTkFont(size=12), text_color=BLEU_CLAIR).pack(side="left")

        # ── Corps ──────────────────────────────────────────────
        corps = ctk.CTkFrame(self, fg_color=FOND)
        corps.pack(fill="both", expand=True, padx=14, pady=14)

        self._colonne_gauche(corps)
        self._colonne_droite(corps)

    # ─── Colonne gauche : liste d'apps ────────────────────────

    def _colonne_gauche(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=14)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        ctk.CTkLabel(frame, text="📱  Applications",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=BLANC).pack(padx=16, pady=(14, 6), anchor="w")

        # Recherche
        self.var_recherche = ctk.StringVar()
        self.var_recherche.trace_add("write", lambda *_: self._filtrer())
        ctk.CTkEntry(frame, textvariable=self.var_recherche,
                     placeholder_text="🔍  Rechercher...",
                     height=38, corner_radius=8
                     ).pack(fill="x", padx=14, pady=(0, 8))

        # Liste scrollable
        self.frame_liste = ctk.CTkScrollableFrame(frame, fg_color=FOND, corner_radius=8)
        self.frame_liste.pack(fill="both", expand=True, padx=14, pady=(0, 8))

        # Saisie manuelle (pour apps pas encore ouvertes)
        sep = ctk.CTkFrame(frame, fg_color=SURFACE2, height=1)
        sep.pack(fill="x", padx=14)

        ctk.CTkLabel(frame, text="Ou saisissez le nom du processus (ex: chrome.exe) :",
                     font=ctk.CTkFont(size=11), text_color=GRIS
                     ).pack(padx=14, pady=(8, 2), anchor="w")

        frame_manuel = ctk.CTkFrame(frame, fg_color="transparent")
        frame_manuel.pack(fill="x", padx=14, pady=(0, 12))

        self.var_manuel = ctk.StringVar()
        ctk.CTkEntry(frame_manuel, textvariable=self.var_manuel,
                     placeholder_text="chrome.exe, notepad.exe...",
                     height=34).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(frame_manuel, text="Sélect.",
                      width=74, height=34, fg_color=BLEU,
                      command=self._selectionner_manuel
                      ).pack(side="right")

        # Rafraîchir
        ctk.CTkButton(frame, text="🔄  Rafraîchir la liste",
                      height=30, fg_color="transparent", hover_color=SURFACE2,
                      font=ctk.CTkFont(size=11), text_color=GRIS,
                      border_width=1, border_color=SURFACE2,
                      command=self._charger_processus
                      ).pack(fill="x", padx=14, pady=(0, 12))

    # ─── Colonne droite : config + blocs actifs ───────────────

    def _colonne_droite(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=FOND, width=360)
        frame.pack(side="right", fill="both")
        frame.pack_propagate(False)

        # ── Carte configuration ─────────────────────────────────
        config = ctk.CTkFrame(frame, fg_color=SURFACE, corner_radius=14)
        config.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(config, text="⚙️  Configurer un bloc",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=BLANC).pack(padx=16, pady=(14, 4), anchor="w")

        ctk.CTkLabel(config, text="App sélectionnée :",
                     font=ctk.CTkFont(size=11), text_color=GRIS
                     ).pack(padx=16, anchor="w")

        self.lbl_selection = ctk.CTkLabel(config, text="— Aucune sélection —",
                                          font=ctk.CTkFont(size=13, weight="bold"),
                                          text_color=BLEU_CLAIR)
        self.lbl_selection.pack(padx=16, pady=(2, 12), anchor="w")

        ctk.CTkLabel(config, text="⏱  Temps autorisé (après quoi l'app sera bloquée) :",
                     font=ctk.CTkFont(size=11), text_color=GRIS
                     ).pack(padx=16, anchor="w")

        # Sélecteur de durée
        duree_frame = ctk.CTkFrame(config, fg_color="transparent")
        duree_frame.pack(fill="x", padx=16, pady=(6, 14))

        self.var_h = ctk.StringVar(value="0")
        self.var_m = ctk.StringVar(value="30")
        self.var_s = ctk.StringVar(value="0")

        for var, unite, largeur in [(self.var_h, "h", 56), (self.var_m, "min", 56), (self.var_s, "s", 56)]:
            ctk.CTkEntry(duree_frame, textvariable=var, width=largeur, height=40,
                         justify="center",
                         font=ctk.CTkFont(size=17, weight="bold")
                         ).pack(side="left", padx=(0, 2))
            ctk.CTkLabel(duree_frame, text=unite,
                         font=ctk.CTkFont(size=12), text_color=GRIS,
                         width=28).pack(side="left", padx=(0, 8))

        self.btn_bloquer = ctk.CTkButton(
            config, text="🚫  Bloquer cette app",
            height=46, fg_color=BLEU, hover_color="#0D47A1",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._demarrer_bloc
        )
        self.btn_bloquer.pack(fill="x", padx=16, pady=(0, 14))

        # ── Blocs actifs ─────────────────────────────────────────
        ctk.CTkLabel(frame, text="BLOCS ACTIFS",
                     font=ctk.CTkFont(size=10), text_color=GRIS
                     ).pack(anchor="w", pady=(0, 4))

        self.frame_blocs = ctk.CTkScrollableFrame(frame, fg_color=FOND, corner_radius=0)
        self.frame_blocs.pack(fill="both", expand=True)

        self.lbl_vide = ctk.CTkLabel(
            self.frame_blocs,
            text="Aucun bloc actif.\n\nSélectionnez une app à gauche,\ndéfinissez une durée et cliquez Bloquer.",
            text_color=GRIS, font=ctk.CTkFont(size=12), justify="center"
        )
        self.lbl_vide.pack(pady=30)

    # ─── Chargement des processus ─────────────────────────────

    def _charger_processus(self):
        seen = set()
        self.processus = []
        for p in psutil.process_iter(['name']):
            try:
                nom = p.info['name']
                if not nom or nom in seen or _est_systeme(nom):
                    continue
                seen.add(nom)
                affiche = os.path.splitext(nom)[0].replace("_", " ").replace("-", " ")
                affiche = " ".join(w.capitalize() for w in affiche.split())
                self.processus.append((affiche, nom))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        self.processus.sort(key=lambda x: x[0].lower())
        self._afficher_liste(self.processus)

    def _filtrer(self):
        q = self.var_recherche.get().lower()
        result = [(a, p) for a, p in self.processus
                  if q in a.lower() or q in p.lower()] if q else self.processus
        self._afficher_liste(result)

    def _afficher_liste(self, apps):
        for w in self.frame_liste.winfo_children():
            w.destroy()
        if not apps:
            ctk.CTkLabel(self.frame_liste, text="Aucun résultat.",
                         text_color=GRIS).pack(pady=20)
            return
        for nom_affiche, nom_process in apps:
            self._ligne_app(nom_affiche, nom_process)

    def _ligne_app(self, nom_affiche: str, nom_process: str):
        bloque = nom_process in self.blocs
        couleur = ROUGE if bloque else SURFACE2

        row = ctk.CTkFrame(self.frame_liste, fg_color=couleur,
                           corner_radius=7, cursor="hand2")
        row.pack(fill="x", pady=2, ipady=1)

        ctk.CTkLabel(row, text="🔴" if bloque else "●",
                     text_color=ROUGE if bloque else "#3D4451",
                     font=ctk.CTkFont(size=10), width=16
                     ).pack(side="left", padx=(8, 0))

        lbl = ctk.CTkLabel(row, text=nom_affiche, anchor="w",
                           font=ctk.CTkFont(size=13), text_color=BLANC)
        lbl.pack(side="left", fill="x", expand=True, padx=8, pady=7)

        ctk.CTkLabel(row, text=nom_process,
                     font=ctk.CTkFont(size=9), text_color=GRIS
                     ).pack(side="right", padx=8)

        def select(e=None, a=nom_affiche, p=nom_process):
            self.selection = (a, p)
            self.lbl_selection.configure(text=f"  {a}")

        row.bind("<Button-1>", select)
        lbl.bind("<Button-1>", select)

    def _selectionner_manuel(self):
        val = self.var_manuel.get().strip()
        if not val:
            return
        if not val.endswith(".exe"):
            val += ".exe"
        affiche = os.path.splitext(val)[0].replace("_", " ").capitalize()
        self.selection = (affiche, val)
        self.lbl_selection.configure(text=f"  {affiche}  ({val})")

    # ─── Gestion des blocs ────────────────────────────────────

    def _demarrer_bloc(self):
        if self.selection is None:
            self._notif("⚠️  Sélectionnez d'abord une app dans la liste.")
            return
        nom_affiche, nom_process = self.selection
        try:
            h = int(self.var_h.get() or 0)
            m = int(self.var_m.get() or 0)
            s = int(self.var_s.get() or 0)
            duree = h * 3600 + m * 60 + s
        except ValueError:
            self._notif("⚠️  Entrez une durée valide.")
            return
        if duree <= 0:
            self._notif("⚠️  La durée doit être supérieure à 0.")
            return
        if nom_process in self.blocs:
            self._notif(f"⚠️  {nom_affiche} est déjà bloqué.")
            return

        bloc = Bloc(nom_process, nom_affiche, duree)
        self.blocs[nom_process] = bloc
        t = threading.Thread(target=self._thread_bloc, args=(bloc,), daemon=True)
        t.start()
        self._notif(f"✅  Bloc démarré pour {nom_affiche} — {bloc.temps_formate()} autorisé(es).")

    def _thread_bloc(self, bloc: Bloc):
        """Thread de surveillance : décompte puis bloque l'app."""
        # Phase 1 : décompte du timer autorisé
        while bloc.actif and bloc.restant_sec > 0:
            time.sleep(1)
            bloc.restant_sec -= 1

        if not bloc.actif:
            return

        # Phase 2 : timer expiré → tuer + empêcher réouverture
        bloc.expire = True
        _tuer(bloc.nom_process)
        self.after(0, lambda: self._popup_bloque(bloc.nom_affiche))

        # Surveiller continuellement (empêcher réouverture)
        while bloc.actif:
            _tuer(bloc.nom_process)
            time.sleep(2)

    def _arreter_bloc(self, nom_process: str):
        if nom_process in self.blocs:
            self.blocs[nom_process].actif = False
            del self.blocs[nom_process]

    # ─── Rafraîchissement live ────────────────────────────────

    def _boucle_rafraichissement(self):
        """Met à jour l'affichage toutes les secondes."""
        self._rafraichir_blocs()
        self.after(1000, self._boucle_rafraichissement)

    def _rafraichir_blocs(self):
        for w in self.frame_blocs.winfo_children():
            w.destroy()

        if not self.blocs:
            self.lbl_vide = ctk.CTkLabel(
                self.frame_blocs,
                text="Aucun bloc actif.\n\nSélectionnez une app à gauche,\ndéfinissez une durée et cliquez Bloquer.",
                text_color=GRIS, font=ctk.CTkFont(size=12), justify="center"
            )
            self.lbl_vide.pack(pady=30)
            return

        for nom_process, bloc in list(self.blocs.items()):
            self._carte_bloc(bloc)

    def _carte_bloc(self, bloc: Bloc):
        carte = ctk.CTkFrame(self.frame_blocs, fg_color=SURFACE, corner_radius=12)
        carte.pack(fill="x", pady=5)

        # En-tête
        ctk.CTkLabel(carte,
                     text=f"🚫  {bloc.nom_affiche}",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=BLANC).pack(padx=14, pady=(12, 2), anchor="w")

        ctk.CTkLabel(carte, text=bloc.nom_process,
                     font=ctk.CTkFont(size=10), text_color=GRIS
                     ).pack(padx=14, anchor="w")

        # Timer ou statut bloqué
        if bloc.expire:
            ctk.CTkLabel(carte, text="🔒  Bloqué — réouverture empêchée",
                         font=ctk.CTkFont(size=12), text_color=ROUGE
                         ).pack(padx=14, pady=(4, 2), anchor="w")
        else:
            ctk.CTkLabel(carte, text=f"⏱  {bloc.temps_formate()} restant(es)",
                         font=ctk.CTkFont(size=12, weight="bold"), text_color=ORANGE
                         ).pack(padx=14, pady=(4, 2), anchor="w")

            # Barre de progression
            barre = ctk.CTkProgressBar(carte, height=6, corner_radius=3,
                                       progress_color=BLEU)
            barre.pack(fill="x", padx=14, pady=(2, 6))
            barre.set(bloc.pourcentage())

        # Bouton arrêter
        ctk.CTkButton(carte, text="✖  Arrêter ce bloc",
                      height=30, fg_color=ROUGE, hover_color="#7B0000",
                      font=ctk.CTkFont(size=12),
                      command=lambda p=bloc.nom_process: self._arreter_bloc(p)
                      ).pack(fill="x", padx=14, pady=(4, 12))

    # ─── Popups ───────────────────────────────────────────────

    def _popup_bloque(self, nom_app: str):
        p = ctk.CTkToplevel(self)
        p.title("BlueBot — Limite atteinte !")
        p.geometry("400x300")
        p.resizable(False, False)
        p.configure(fg_color=FOND)
        p.lift(); p.focus()

        if PIL_OK:
            try:
                img = ctk.CTkImage(light_image=Image.open(_logo()),
                                   dark_image=Image.open(_logo()), size=(56, 56))
                ctk.CTkLabel(p, image=img, text="").pack(pady=(18, 6))
            except Exception:
                pass

        ctk.CTkLabel(p, text="⛔  Limite atteinte !",
                     font=ctk.CTkFont(size=19, weight="bold"),
                     text_color=ROUGE).pack(pady=(0, 6))

        ctk.CTkLabel(p,
                     text=f"Ta limite de temps pour\n{nom_app}\nest écoulée.\n\nL'application a été fermée.",
                     font=ctk.CTkFont(size=13), text_color=BLANC,
                     justify="center").pack(pady=4)

        ctk.CTkButton(p, text="OK  👍", height=38, fg_color=BLEU,
                      command=p.destroy).pack(pady=14, padx=50, fill="x")

    def _notif(self, msg: str):
        n = ctk.CTkToplevel(self)
        x = self.winfo_x() + self.winfo_width() // 2 - 200
        y = self.winfo_y() + self.winfo_height() - 80
        n.geometry(f"400x48+{x}+{y}")
        n.overrideredirect(True)
        n.configure(fg_color=SURFACE)
        ctk.CTkLabel(n, text=msg, font=ctk.CTkFont(size=12),
                     text_color=BLANC).pack(fill="both", expand=True, padx=14)
        n.after(2800, n.destroy)


# ═══════════════════════════════════════════════════════════════
# Utilitaires
# ═══════════════════════════════════════════════════════════════

def _tuer(nom: str):
    """Tue tous les processus portant ce nom."""
    for p in psutil.process_iter(['name']):
        try:
            if p.info['name'] and p.info['name'].lower() == nom.lower():
                p.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


SYSTEME = {
    'system', 'registry', 'smss.exe', 'csrss.exe', 'wininit.exe', 'services.exe',
    'lsass.exe', 'svchost.exe', 'dwm.exe', 'winlogon.exe', 'fontdrvhost.exe',
    'spoolsv.exe', 'searchindexer.exe', 'taskhostw.exe', 'conhost.exe',
    'dllhost.exe', 'runtimebroker.exe', 'sihost.exe', 'ctfmon.exe',
    'startmenuexperiencehost.exe', 'textinputhost.exe', 'applicationframehost.exe',
    'ntoskrnl.exe', 'audiodg.exe', 'wmiprvse.exe', 'securityhealthsystray.exe',
    'securityhealthservice.exe', 'wuauclt.exe', 'msiexec.exe', 'taskmgr.exe',
    'explorer.exe', 'idle', 'python.exe', 'pythonw.exe',
}

def _est_systeme(nom: str) -> bool:
    return nom.lower() in SYSTEME


def _logo() -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    for p in [os.path.join(base, "assets", "logo.png"),
              os.path.join(base, "logo.png")]:
        if os.path.exists(p):
            return p
    raise FileNotFoundError


# ═══════════════════════════════════════════════════════════════
# Point d'entrée
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = BlueBotApp()
    app.mainloop()
