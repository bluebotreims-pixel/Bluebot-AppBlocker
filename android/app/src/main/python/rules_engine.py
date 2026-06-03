"""
rules_engine.py — Moteur de décision Python.
Appelé depuis Java via Chaquopy :
    PyObject d = rulesEngine.callAttr("verifier", packageName);
    boolean bloquer = d.get("bloquer").toBoolean();
"""
from datetime import datetime, time
from storage import charger_regles, get_usage

DELAI = 10

def verifier(package):
    regles = charger_regles()
    if package not in regles: return {"bloquer": False, "message": ""}
    usage = get_usage(package)
    now = datetime.now()
    for r in regles[package].get("regles", []):
        if not r.get("active", True): continue
        t, v = r["type"], r["valeur"]
        if t == "temps":
            lim = int(v); used = usage.get("sec", 0)
            if used >= lim:
                return {"bloquer": True, "message": f"⏱️  Limite atteinte !\n\nUtilisé : {_fmt(used)} / {_fmt(lim)}\n\nFermeture dans {DELAI} secondes."}
        elif t == "lancements":
            lim = int(v); ouv = usage.get("ouv", 0)
            if ouv >= lim:
                return {"bloquer": True, "message": f"🚀  Limite d'ouvertures atteinte !\n\n{ouv}/{lim} ouvertures aujourd'hui.\n\nFermeture dans {DELAI} secondes."}
        elif t == "horaire":
            try:
                a, b = v.split("-")
                deb = _hm(a); fin = _hm(b)
                cur = now.time().replace(second=0, microsecond=0)
                bloque = (cur >= deb or cur <= fin) if deb > fin else (deb <= cur <= fin)
                if bloque:
                    return {"bloquer": True, "message": f"🌙  Heure de blocage !\n\nCette app est bloquée de {a} à {b}.\n\nFermeture dans {DELAI} secondes."}
            except: pass
    return {"bloquer": False, "message": ""}

def progression(package):
    regles = charger_regles()
    if package not in regles: return ""
    usage = get_usage(package); parts = []
    for r in regles[package].get("regles", []):
        if not r.get("active", True): continue
        t, v = r["type"], r["valeur"]
        if t == "temps":    parts.append(f"⏱ {_fmt(usage.get('sec',0))} / {_fmt(int(v))}")
        elif t == "lancements": parts.append(f"🚀 {usage.get('ouv',0)}/{v}")
        elif t == "horaire":    parts.append(f"🌙 {v}")
    return "  •  ".join(parts) if parts else "—"

def _hm(s):
    h, m = map(int, s.strip().split(":")); return time(h, m)

def _fmt(sec):
    h=sec//3600; m=(sec%3600)//60; s=sec%60
    if h>0: return f"{h}h {m:02d}min"
    if m>0: return f"{m}min {s:02d}s"
    return f"{s}s"
