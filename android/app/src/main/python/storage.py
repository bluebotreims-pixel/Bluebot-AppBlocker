"""
storage.py — Sauvegarde JSON des règles et usages.
Appelé depuis Java via Chaquopy.
"""
import json, os
from datetime import date, datetime

DIR = os.environ.get("ANDROID_APP_DATA_DIR", os.path.join(os.path.expanduser("~"), ".bluebot"))
F_REGLES = os.path.join(DIR, "regles.json")
F_USAGE  = os.path.join(DIR, "usage.json")

def _mk(): os.makedirs(DIR, exist_ok=True)

def charger_regles():
    _mk()
    if not os.path.exists(F_REGLES): return {}
    try:
        with open(F_REGLES, encoding="utf-8") as f: return json.load(f)
    except: return {}

def _save_regles(r):
    _mk()
    with open(F_REGLES, "w", encoding="utf-8") as f: json.dump(r, f, indent=2, ensure_ascii=False)

def ajouter_regle(package, nom, type_regle, valeur):
    r = charger_regles()
    if package not in r: r[package] = {"nom": nom, "regles": []}
    for i, x in enumerate(r[package]["regles"]):
        if x["type"] == type_regle:
            r[package]["regles"][i] = {"type": type_regle, "valeur": valeur, "active": True}
            _save_regles(r); return
    r[package]["regles"].append({"type": type_regle, "valeur": valeur, "active": True})
    _save_regles(r)

def supprimer_regle(package):
    r = charger_regles()
    if package in r: del r[package]; _save_regles(r)

def toggler_regles(package, actif):
    r = charger_regles()
    if package not in r: return
    for x in r[package]["regles"]: x["active"] = actif
    _save_regles(r)

def _today(): return date.today().isoformat()

def charger_usage():
    _mk(); today = _today()
    if not os.path.exists(F_USAGE): return {"date": today, "apps": {}}
    try:
        with open(F_USAGE) as f: d = json.load(f)
        return d if d.get("date") == today else {"date": today, "apps": {}}
    except: return {"date": today, "apps": {}}

def _save_usage(u):
    _mk()
    with open(F_USAGE, "w") as f: json.dump(u, f, indent=2)

def enregistrer_ouverture(package):
    if package not in charger_regles(): return
    u = charger_usage()
    a = u["apps"].setdefault(package, {"sec": 0, "ouv": 0})
    a["ouv"] += 1
    _save_usage(u)

def get_usage(package):
    return charger_usage()["apps"].get(package, {"sec": 0, "ouv": 0})
