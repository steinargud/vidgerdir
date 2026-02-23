# Viðhaldssíða fyrir húsið

Einföld Flask-vefsíða til að halda utan um viðgerðarsögu húss:
- innskráning
- skráning viðgerða
- lýsing + kostnaður + dagsetning
- myndir fyrir hvert verk
- heildarkostnaður yfir allar skráningar

## Keyra verkefnið

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Opnaðu svo: http://localhost:5000

## Sjálfgefin innskráning

- Notendanafn: `eigandi`
- Lykilorð: `hus1234`

> Mikilvægt: Skiptu út `SECRET_KEY` og sjálfgefnum aðgangi áður en þetta er sett í raunumhverfi.
