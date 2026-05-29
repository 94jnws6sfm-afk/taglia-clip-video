# ⚽ Taglia Clip Video

App Mac per tagliare automaticamente i momenti salienti da video di partite di calcio.

## Funzionalità
- ⏱ **Timer integrato** — avvialo quando premi play sul video
- 🔴 **Segna INIZIO** e 🟢 **Segna FINE** per marcare ogni azione al volo
- ✂️ **Taglia automatico** con ffmpeg — crea tutti i clip in un click
- 💾 **Salva/Carica lista** tagli per riprendere in un altro momento
- ✏️ **Rinomina** ogni clip con doppio click

## Installazione

### Requisiti
- macOS
- Python 3 (`brew install python`)
- ffmpeg (`brew install ffmpeg`)

### Prima volta
```bash
# Installa Homebrew (se non ce l'hai)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Installa Python e ffmpeg
brew install python ffmpeg

# Rendi eseguibile l'avviatore
chmod +x "Avvia App.command"
```

## Utilizzo
1. Doppio click su **Avvia App.command**
2. Premi **▶ Avvia** insieme al play del video
3. **🔴 Segna INIZIO** quando inizia un'azione
4. **🟢 Segna FINE** quando finisce
5. Scegli il file video e premi **✂️ TAGLIA VIDEO**

I clip vengono salvati nella cartella `clips/` accanto al video originale.
