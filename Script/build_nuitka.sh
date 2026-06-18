#!/usr/bin/env bash
# Build local d'Optic Vision Pro avec Nuitka (macOS / Linux).
# Sur Windows, voir build_nuitka.ps1 ou le workflow GitHub Actions.
#
# Prérequis :
#   pip install -r requirements.txt
#   pip install nuitka
#
# Le point d'entrée est newapp.py. La seule ressource externe lue au runtime
# est OPV3.png (logo) ; le reste (langue.py, etc.) est compilé dans le binaire.
set -euo pipefail

EXTRA="${1:-}"   # ex: "--macos-create-app-bundle" sur macOS, "--onefile" sinon

python -m nuitka \
    --standalone \
    --assume-yes-for-downloads \
    --enable-plugin=pyside6 \
    --include-data-files=OPV3.png=OPV3.png \
    --include-package=skimage \
    --include-package-data=skimage \
    --include-module=scipy.spatial.distance \
    --include-module=scipy.signal \
    --include-package=cv2 \
    --include-package-data=cv2 \
    --output-dir=build \
    ${EXTRA} \
    newapp.py

echo "Build terminé. Sortie dans ./build/"
