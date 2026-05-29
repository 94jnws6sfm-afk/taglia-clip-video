#!/bin/bash
# ⚽ Video Clip Cutter — Avviatore
# Fai doppio click su questo file per aprire l'app!

DIR="$(cd "$(dirname "$0")" && pwd)"

# Cerca python3
if command -v python3 &>/dev/null; then
    python3 "$DIR/VideoClipCutter.py"
elif command -v /usr/local/bin/python3 &>/dev/null; then
    /usr/local/bin/python3 "$DIR/VideoClipCutter.py"
elif command -v /opt/homebrew/bin/python3 &>/dev/null; then
    /opt/homebrew/bin/python3 "$DIR/VideoClipCutter.py"
else
    osascript -e 'display alert "Python 3 non trovato" message "Installa Python con:\n  brew install python\n\nSe non hai Homebrew:\n  https://brew.sh"'
fi
