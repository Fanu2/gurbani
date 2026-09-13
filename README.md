# JASS Gurbani Explorer v0.8

## Stable Qt Font Initialization + Card Preview

This release fixes the startup error:

```text
QFontDatabase: Must construct a QGuiApplication before accessing QFontDatabase
```

The Gurmukhi font is now selected **after `QApplication` exists**, so Qt's font database is queried safely.

It also preserves the v0.7 card renderer fixes, including off-screen `QImage` rendering and safe PNG export.

## Run

No separate virtual environment is required.

```powershell
py .\JASS_Gurbani_Explorer_v0.8.py
```

## Included

- Gurbani database
- Search
- Cohesive context around search results
- Presentation reader
- Random Gurbani
- Favorites
- Card Studio
- Live card preview
- 4:5, 1:1 and 9:16 cards
- Editable title/footer/watermark
- PNG export
- Windows Gurmukhi font detection

## Important

The application now avoids querying `QFontDatabase` at module-import time. This is required because Qt needs a live `QGuiApplication` before font database APIs are accessed.

## Future direction

The next feature work can focus on Ang/page mapping, Shabad-aware grouping, richer presentation controls, background images, templates and batch card creation without changing the stable rendering foundation.
