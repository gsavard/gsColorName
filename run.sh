#!/usr/bin/env bash
# Lance gsColorName (crée l'environnement virtuel au premier lancement)
set -e
cd "$(dirname "$(readlink -f "$0")")"
if [ ! -x .venv/bin/python ]; then
  echo "Création de l'environnement virtuel…"
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip -q
  .venv/bin/pip install -r requirements.txt -q
fi
exec .venv/bin/python gscolorname.py "$@"
