import customtkinter as ctk
import psutil
import threading
import time
import os

try:
    from PIL import Image
    PIL_OK = True
except:
    PIL_OK = False

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BLEU, ROUGE, VERT, ORANGE = "#1565C0", "#C62828", "#2E7D32", "#E65100"
FOND, SURFACE, BLANC, GRIS = "#0D1117", "#161B22", "#FFFFFF", "#8B949E"

class Bloc:
    def __init__(self, process, nom, duree):
        self.process = process
        self.nom = nom
        self.duree = duree
        self.restant = duree
        self.actif = True
        self.expire = False

    def temps(self):
        s = max(0, self.restant)
        h, m, sec = s//3600, (s%3600)//60, s%60
        if h > 0: return f"{h}h {m:02d}min"
        if m > 0: return f"{m}min {sec:02d}s"
        return f"{sec}s"

    def pct(self):
        return max(0.0, min(1.0, self.restant/self.duree)) if self.duree > 0 else 0.0

class BlueBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.blocs = {}
        self.processus = []
        self.selection = None
        self.title("BlueBot — App Blocker")
        self.geometry("980x660")
        self.minsize(820, 560)
        self.configure(fg_color=FOND)
        self._ui()
        self._charger()
        self._loop()

    def _ui(self):
        # Header
        h = ctk.CTkFrame(self, fg_color=SURFACE, height=68, corner_radius=0)
        h.pack(fill="x"); h.pack_propagate(False)
        if PIL_OK:
            try:
                img = ctk.CTkImage(light_image=Image.open(_logo()), dark_image=Image.open(_logo()), size=(46,46))
                ctk.CTkLabel(h, image=img, text="").pack(side="left", padx=(14,6), pady=10)
            except: pass
        ctk.CTkLabel(h, text="BlueBot", font=ctk.CTkFont(size=22, weight="bold"), text_color=BLANC).pack(side="left")
        ctk.CTkLabel(h, text="  App Blocker  |  FIRST Tech Challenge Reims", font=ctk.CTkFont(size=12), text_color="#4FC3F7").pack(side="left")

        corps = ctk.CTkFrame(self, fg_color=FOND)
        corps.pack(fill="both", expand=True, padx=14, pady=14)
        self._gauche(corps)
        self._droite(corps)

    def _gauche(self, p):
        f = ctk.CTkFrame(p, fg_color=SURFACE, corner_radius=14)
        f.pack(side="left", fill="both", expand=True, padx=(0,8))
        ctk.CTkLabel(f, text="📱  Applications en cours", font=ctk.CTkFont(size=14, weight="bold"), text_color=BLANC).pack(padx=16, pady=(14,6), anchor="w")
        self.var_q = ctk.StringVar()
        self.var_q.trace_add("write", lambda *_: self._filtrer())
        ctk.CTkEntry(f, textvariable=self.var_q, placeholder_text="🔍  Rechercher...", height=38, corner_radius=8).pack(fill="x", padx=14, pady=(0,8))
        self.liste = ctk.CTkScrollableFrame(f, fg_color=FOND, corner_radius=8)
        self.liste.pack(fill="both", expand=True, padx=14, pady=(0,8))
        ctk.CTkLabel(f, text="Ou entrez directement le nom du processus :", font=ctk.CTkFont(size=11), text_color=GRIS).pack(padx=14, pady=(4,2), anchor="w")
        fm = ctk.CTkFrame(f, fg_color="transparent")
        fm.pack(fill="x", padx=14, pady=(0,8))
        self.var_manuel = ctk.StringVar()
        ctk.CTkEntry(fm, textvariable=self.var_manuel, placeholder_text="chrome.exe, discord.exe...", height=34).pack(side="left", fill="x", expand=True, padx=(0,6))
        ctk.CTkButton(fm, text="OK", width=60, height=34, fg_color=BLEU, command=self._manuel).pack(side="right")
        ctk.CTkButton(f, text="🔄  Rafraîchir", height=30, fg_color="transparent", hover_color="#1F2937", font=ctk.CTkFont(size=11), text_color=GRIS, border_width=1, border_color="#1F2937", command=self._charger).pack(fill="x", padx=14, pady=(0,12))

    def _droite(self, p):
        f = ctk.CTkFrame(p, fg_color=FOND, width=360)
        f.pack(side="right", fill="both"); f.pack_propagate(False)
        cfg = ctk.CTkFrame(f, fg_color=SURFACE, corner_radius=14)
        cfg.pack(fill="x", pady=(0,10))
        ctk.CTkLabel(cfg, text="⚙️  Configurer un bloc", font=ctk.CTkFont(size=14, weight="bold"), text_color=BLANC).pack(padx=16, pady=(14,4), anchor="w")
        ctk.CTkLabel(cfg, text="App sélectionnée :", font=ctk.CTkFont(size=11), text_color=GRIS).pack(padx=16, anchor="w")
        self.lbl_sel = ctk.CTkLabel(cfg, text="— Aucune —", font=ctk.CTkFont(size=13, weight="bold"), text_color="#4FC3F7")
        self.lbl_sel.pack(padx=16, pady=(2,12), anchor="w")
        ctk.CTkLabel(cfg, text="⏱  Temps autorisé avant blocage :", font=ctk.CTkFont(size=11), text_color=GRIS).pack(padx=16, anchor="w")
        df = ctk.CTkFrame(cfg, fg_color="transparent")
        df.pack(fill="x", padx=16, pady=(6,14))
        self.var_h = ctk.StringVar(value="0")
        self.var_m = ctk.StringVar(value="30")
        self.var_s = ctk.StringVar(value="0")
        for var, u in [(self.var_h,"h"),(self.var_m,"min"),(self.var_s,"s")]:
            ctk.CTkEntry(df, textvariable=var, width=56, height=40, justify="center", font=ctk.CTkFont(size=17, weight="bold")).pack(side="left", padx=(0,2))
            ctk.CTkLabel(df, text=u, font=ctk.CTkFont(size=12), text_color=GRIS, width=28).pack(side="left", padx=(0,8))
        ctk.CTkButton(cfg, text="🚫  Bloquer cette app", height=46, fg_color=BLEU, hover_color="#0D47A1", font=ctk.CTkFont(size=15, weight="bold"), command=self._bloquer).pack(fill="x", padx=16, pady=(0,14))
        ctk.CTkLabel(f, text="BLOCS ACTIFS", font=ctk.CTkFont(size=10), text_color=GRIS).pack(anchor="w", pady=(0,4))
        self.frame_blocs = ctk.CTkScrollableFrame(f, fg_color=FOND, corner_radius=0)
        self.frame_blocs.pack(fill="both", expand=True)

    def _charger(self):
        seen = set(); self.processus = []
        for p in psutil.process_iter(['name']):
            try:
                n = p.info['name']
                if not n or n in seen or n.lower() in SYSTEME: continue
                seen.add(n)
                aff = " ".join(w.capitalize() for w in os.path.splitext(n)[0].replace("_"," ").replace("-"," ").split())
                self.processus.append((aff, n))
            except: pass
        self.processus.sort(key=lambda x: x[0].lower())
        self._afficher(self.processus)

    def _filtrer(self):
        q = self.var_q.get().lower()
        self._afficher([(a,p) for a,p in self.processus if q in a.lower() or q in p.lower()] if q else self.processus)

    def _afficher(self, apps):
        for w in self.liste.winfo_children(): w.destroy()
        if not apps:
            ctk.CTkLabel(self.liste, text="Aucune app trouvée.", text_color=GRIS).pack(pady=20)
            return
        for aff, proc in apps:
            bloque = proc in self.blocs
            row = ctk.CTkFrame(self.liste, fg_color=ROUGE if bloque else "#1F2937", corner_radius=7, cursor="hand2")
            row.pack(fill="x", pady=2, ipady=1)
            lbl = ctk.CTkLabel(row, text=aff, anchor="w", font=ctk.CTkFont(size=13), text_color=BLANC)
            lbl.pack(side="left", fill="x", expand=True, padx=8, pady=7)
            ctk.CTkLabel(row, text=proc, font=ctk.CTkFont(size=9), text_color=GRIS).pack(side="right", padx=8)
            def sel(e=None, a=aff, p=proc): self.selection=(a,p); self.lbl_sel.configure(text=f"  {a}")
            row.bind("<Button-1>", sel); lbl.bind("<Button-1>", sel)

    def _manuel(self):
        v = self.var_manuel.get().strip()
        if not v: return
        if not v.endswith(".exe"): v += ".exe"
        aff = os.path.splitext(v)[0].capitalize()
        self.selection = (aff, v)
        self.lbl_sel.configure(text=f"  {aff}  ({v})")

    def _bloquer(self):
        if not self.selection: self._notif("⚠️  Sélectionnez une app d'abord."); return
        aff, proc = self.selection
        try:
            h,m,s = int(self.var_h.get() or 0), int(self.var_m.get() or 0), int(self.var_s.get() or 0)
            duree = h*3600 + m*60 + s
        except: self._notif("⚠️  Durée invalide."); return
        if duree <= 0: self._notif("⚠️  Durée doit être > 0."); return
        if proc in self.blocs: self._notif(f"⚠️  {aff} est déjà bloqué."); return
        b = Bloc(proc, aff, duree)
        self.blocs[proc] = b
        threading.Thread(target=self._run, args=(b,), daemon=True).start()
        self._notif(f"✅  {aff} bloqué dans {b.temps()}")

    def _run(self, b):
        while b.actif and b.restant > 0:
            time.sleep(1); b.restant -= 1
        if not b.actif: return
        b.expire = True; _kill(b.process)
        self.after(0, lambda: self._popup(b.nom))
        while b.actif: _kill(b.process); time.sleep(2)

    def _stop(self, proc):
        if proc in self.blocs: self.blocs[proc].actif = False; del self.blocs[proc]

    def _loop(self):
        for w in self.frame_blocs.winfo_children(): w.destroy()
        if not self.blocs:
            ctk.CTkLabel(self.frame_blocs, text="Aucun bloc actif.\n\nSélectionnez une app à gauche\net cliquez Bloquer.", text_color=GRIS, font=ctk.CTkFont(size=12), justify="center").pack(pady=30)
        else:
            for proc, b in list(self.blocs.items()):
                c = ctk.CTkFrame(self.frame_blocs, fg_color=SURFACE, corner_radius=12)
                c.pack(fill="x", pady=5)
                ctk.CTkLabel(c, text=f"🚫  {b.nom}", font=ctk.CTkFont(size=13, weight="bold"), text_color=BLANC).pack(padx=14, pady=(12,2), anchor="w")
                ctk.CTkLabel(c, text=b.process, font=ctk.CTkFont(size=10), text_color=GRIS).pack(padx=14, anchor="w")
                if b.expire:
                    ctk.CTkLabel(c, text="🔒  Bloqué — réouverture empêchée", font=ctk.CTkFont(size=12), text_color=ROUGE).pack(padx=14, pady=(4,2), anchor="w")
                else:
                    ctk.CTkLabel(c, text=f"⏱  {b.temps()} restant(es)", font=ctk.CTkFont(size=12, weight="bold"), text_color=ORANGE).pack(padx=14, pady=(4,2), anchor="w")
                    bar = ctk.CTkProgressBar(c, height=6, corner_radius=3, progress_color=BLEU)
                    bar.pack(fill="x", padx=14, pady=(2,6)); bar.set(b.pct())
                ctk.CTkButton(c, text="✖  Arrêter", height=30, fg_color=ROUGE, hover_color="#7B0000", font=ctk.CTkFont(size=12), command=lambda p=proc: self._stop(p)).pack(fill="x", padx=14, pady=(4,12))
        self.after(1000, self._loop)

    def _popup(self, nom):
        p = ctk.CTkToplevel(self); p.title("BlueBot"); p.geometry("380x280"); p.resizable(False,False); p.configure(fg_color=FOND); p.lift(); p.focus()
        if PIL_OK:
            try:
                img = ctk.CTkImage(light_image=Image.open(_logo()), dark_image=Image.open(_logo()), size=(50,50))
                ctk.CTkLabel(p, image=img, text="").pack(pady=(16,4))
            except: pass
        ctk.CTkLabel(p, text="⛔  Limite atteinte !", font=ctk.CTkFont(size=18, weight="bold"), text_color=ROUGE).pack(pady=(0,6))
        ctk.CTkLabel(p, text=f"Temps écoulé pour\n{nom}\n\nL'application a été fermée.", font=ctk.CTkFont(size=13), text_color=BLANC, justify="center").pack(pady=4)
        ctk.CTkButton(p, text="OK", height=36, fg_color=BLEU, command=p.destroy).pack(pady=12, padx=50, fill="x")

    def _notif(self, msg):
        n = ctk.CTkToplevel(self)
        n.geometry(f"380x46+{self.winfo_x()+self.winfo_width()//2-190}+{self.winfo_y()+self.winfo_height()-70}")
        n.overrideredirect(True); n.configure(fg_color=SURFACE)
        ctk.CTkLabel(n, text=msg, font=ctk.CTkFont(size=12), text_color=BLANC).pack(fill="both", expand=True, padx=14)
        n.after(2500, n.destroy)

def _kill(nom):
    for p in psutil.process_iter(['name']):
        try:
            if p.info['name'] and p.info['name'].lower() == nom.lower(): p.kill()
        except: pass

def _logo():
    base = os.path.dirname(os.path.abspath(__file__))
    for path in [os.path.join(base,"assets","logo.png"), os.path.join(base,"logo.png")]:
        if os.path.exists(path): return path
    raise FileNotFoundError

SYSTEME = {'system','registry','smss.exe','csrss.exe','wininit.exe','services.exe','lsass.exe','svchost.exe','dwm.exe','winlogon.exe','fontdrvhost.exe','spoolsv.exe','searchindexer.exe','taskhostw.exe','conhost.exe','dllhost.exe','runtimebroker.exe','sihost.exe','ctfmon.exe','startmenuexperiencehost.exe','textinputhost.exe','applicationframehost.exe','ntoskrnl.exe','audiodg.exe','wmiprvse.exe','securityhealthsystray.exe','securityhealthservice.exe','wuauclt.exe','msiexec.exe','taskmgr.exe','explorer.exe','idle','python.exe','pythonw.exe'}

if __name__ == "__main__":
    BlueBotApp().mainloop()
