# 🤖 BlueBot — App Blocker

> Bloque les applications sur **Windows** et **Android** avec un simple minuteur.  
> FIRST Tech Challenge — Reims

---

## ⚡ Installation rapide

### 🖥️ Windows

**1 — Installer Python** (si pas déjà fait)  
→ https://www.python.org/downloads/ *(cocher "Add to PATH" lors de l'installation)*

**2 — Cloner le projet**
```
git clone https://github.com/TON_PSEUDO/bluebot.git
cd bluebot
```

**3 — Installer les dépendances**
```
pip install -r windows/requirements.txt
```

**4 — Lancer**
```
python windows/bluebot.py
```

---

### 📱 Android

**1 — Installer Android Studio**  
→ https://developer.android.com/studio

**2 — Ouvrir le projet**  
`File → Open` → sélectionner le dossier `android/`

**3 — Brancher ton téléphone** en USB (activer le Mode développeur)

**4 — Appuyer sur ▶️ Run**

**5 — Accorder les permissions** (l'app te guidera au premier lancement)

---

## 🎯 Comment utiliser

### Windows
1. Cherche une app dans la liste de gauche
2. Clique dessus pour la sélectionner
3. Règle le minuteur (heures/minutes/secondes)
4. Clique **"🚫 Bloquer cette app"**
5. Quand le temps est écoulé, l'app est fermée automatiquement

### Android
1. Active le **Service d'accessibilité** (bouton rouge → paramètres)
2. Appuie sur **+** pour choisir une app
3. Configure : temps autorisé, nombre d'ouvertures, ou plage horaire
4. Sauvegarde → BlueBot surveille en arrière-plan

---

## 🏗️ Stack technique

| Plateforme | Langages |
|---|---|
| Windows | Python (customtkinter + psutil) |
| Android | Java (AccessibilityService) + Python via Chaquopy |

---

## ⚠️ iOS
Apple interdit le blocage d'apps tierces — utilisez l'app native **Temps d'écran**.

---

## 📁 Structure
```
BlueBot/
├── windows/
│   ├── bluebot.py          ← Application Windows (lancer directement)
│   ├── requirements.txt    ← Dépendances Python
│   └── assets/logo.png
└── android/                ← Ouvrir ce dossier dans Android Studio
    ├── app/src/main/
    │   ├── java/           ← Code Java (AccessibilityService, activités)
    │   └── python/         ← Moteur de règles Python (Chaquopy)
    ├── build.gradle
    └── ...
```
