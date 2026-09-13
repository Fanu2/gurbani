<img width="1916" height="986" alt="image" src="https://github.com/user-attachments/assets/45dddcbe-3f77-4d3b-bc0f-bba6f8a1d50d" />

# JASS Gurbani Explorer

**JASS Gurbani Explorer v0.8 — Stable Base**

A PySide6 desktop application for searching, exploring, presenting, and creating visual quote cards from a Gurbani database.

The project is designed as a **local-first Gurbani exploration tool** with a strong foundation for future search, presentation, research, and card-generation features.

---

## Current Status

**Version:** `v0.8`  
**Status:** Stable Base / Foundation Checkpoint  
**Platform:** Windows / Linux (PySide6)  
**Database:** SQLite (`gurbani.db`)  
**Python:** Uses the system/global Python environment  
**Virtual environment:** Not required when PySide6 and required packages are installed globally

> **v0.8 is considered the protected base model.**
>
> Future development should be additive and should avoid unnecessary changes to the stable rendering and application architecture.

---

# Features

## 🔎 Gurbani Search

The application provides local database search for Gurbani text.

Current search direction includes:

- Gurmukhi text search
- Search result list
- Full-word matching
- Any-word matching
- First-letter search
- Search result navigation
- Result selection
- Search result context

The application is intended to evolve from simple line matching into **cohesive Gurbani discovery**.

---

# 📖 Cohesive Gurbani Presentation

A major design goal is to avoid displaying a search result as an isolated OCR/database line.

Instead of:

```text
...partial line containing the search term...
```

the application should present:

```text
Previous line
Previous line

Matched line

Following line
Following line
```

This provides enough context to make the displayed Gurbani meaningful and readable.

Current foundation supports selectable context around a matching database record.

Future versions can improve this further by identifying complete:

- Pauri
- Salok
- Shabad
- Ashtpadi
- Section
- Other logical Gurbani units

rather than relying only on neighboring database records.

---

# 🎨 Card Studio

The application includes a built-in Card Studio.

The intended workflow is:

```text
Search Gurbani
      ↓
Select result
      ↓
Create Card
      ↓
Edit Gurbani text
      ↓
Live Preview
      ↓
Choose design
      ↓
Export PNG
```

Card Studio supports the foundation for:

- Gurmukhi quote text
- Live preview
- Card designs
- Text sizing
- Title
- Footer / attribution
- Watermark
- Watermark visibility
- Card aspect ratios
- PNG export

Supported design directions include:

- Midnight Gold
- Saffron / warm devotional styles
- Amrit / blue styles
- Royal / deep purple styles
- Lotus-inspired styles
- Forest / natural styles

---

# 📐 Card Formats

The Card Studio is designed around social-media-friendly formats.

Current/future formats include:

| Format | Typical use |
|---|---|
| `1:1` | Square social posts |
| `4:5` | Instagram/Facebook portrait |
| `9:16` | Stories / Shorts / Reels |

The rendering system is designed to keep the card generation process independent from the preview widget.

---

# 🖼️ Rendering Architecture

The card renderer uses an off-screen image rendering approach:

```text
Gurbani Text
     │
     ▼
Card Settings
     │
     ▼
Card Renderer
     │
     ▼
QImage
     │
     ├──► Live Preview
     │
     └──► PNG Export
```

This is intentional.

The preview should not depend on painting directly into the main application widget.

This architecture helps avoid Qt painting problems such as:

```text
QBackingStore::endPaint()
QPaintDevice: Cannot destroy paint device that is being painted
```

and provides a cleaner foundation for future card templates.

---

# 🕉️ Gurmukhi Typography

Gurmukhi rendering is an important part of the application.

The application should prefer a font with proper Gurmukhi/OpenType support when available.

Possible fonts include:

- Nirmala UI
- Raavi
- Noto Sans Gurmukhi
- Other installed Gurmukhi-capable fonts

Future versions should provide explicit font selection rather than relying entirely on automatic detection.

---

# 🗄️ Database

The application uses a local SQLite database:

```text
gurbani.db
```

This keeps the application usable without an internet connection.

The database is intended to become more structured over time, eventually supporting metadata such as:

```text
Ang
Raag
Guru / Author
Shabad
Section
Source
Page
Sequence
Text
```

Database improvements should preserve compatibility with the current application wherever practical.

---

# ❤️ Favorites

The application provides a foundation for saving Gurbani that the user wants to revisit.

Future versions can expand this into a complete personal collection system:

```text
Favorites
   │
   ├── Daily Gurbani
   ├── Inspirational
   ├── Peace
   ├── Courage
   ├── Love / Compassion
   ├── Meditation
   └── Custom Collections
```

---

# 🎲 Random Discovery

Random Gurbani discovery is included as a way to explore the database without performing a search.

Future versions can make random discovery more intelligent by allowing:

- Random Ang
- Random Shabad
- Random Pauri
- Random Raag
- Random Guru/author
- Random saved collection
- Daily selection

---

# 🧭 Application Structure

The long-term interface is envisioned as:

```text
                 ੴ
          JASS GURBANI
                 │
      ┌──────────┼──────────┐
      │          │          │
    SEARCH     BROWSE     RANDOM
      │          │          │
      └──────────┼──────────┘
                 │
          GURBANI RESULT
                 │
       ┌─────────┼─────────┐
       │         │         │
      READ    RESEARCH    CARD
       │         │         │
       └─────────┼─────────┘
                 │
              EXPORT
```

The goal is for the application to become more than a search box: a **Gurbani reading, discovery, research and presentation workspace**.

---

# 🚀 Proposed Enhancements

The following roadmap is deliberately proposed as **future work**, not part of the v0.8 stability baseline.

## Phase 1 — Search Improvements

### 1. Better phrase search

Support exact multi-word Gurbani phrases.

Example:

```text
ਸਤਿਗੁਰੁ
```

and:

```text
ਸਤਿਗੁਰੁ ਸੇਵਿ
```

should return appropriately ranked results.

### 2. Search ranking

Rank results by:

1. Exact phrase
2. Exact full-word match
3. Multiple-word match
4. Partial match
5. Other contextual matches

### 3. Search highlighting

Highlight the matched word or phrase in the result and presentation panel.

### 4. Search history

Keep recently searched Gurbani terms.

### 5. Advanced filters

Potential filters:

- Ang
- Raag
- Guru
- Author
- Shabad
- Source

---

# Phase 2 — True Cohesive Gurbani

This is one of the most important future improvements.

Instead of assuming that database rows represent complete textual units, introduce a logical-text layer.

Possible structure:

```text
Document
   ↓
Ang
   ↓
Section
   ↓
Shabad
   ↓
Pauri / stanza
   ↓
Line
```

Then searching one line can display the complete relevant unit.

Example:

```text
SEARCH MATCH
     ↓
Complete Pauri
     ↓
Complete Shabad
     ↓
Metadata
```

This will be much better than simply showing `±3` database records.

---

# Phase 3 — Gurbani Reader

Create a dedicated reading mode.

Possible features:

- Large Gurmukhi typography
- Comfortable line spacing
- Full-screen mode
- Dark/light themes
- Adjustable font size
- Adjustable margins
- Previous / next navigation
- Ang navigation
- Shabad navigation
- Reading position

The reader should prioritize **clarity and respectful presentation**.

---

# Phase 4 — Ang Navigation

Add direct navigation across the complete Sri Guru Granth Sahib Ji structure when reliable metadata is available.

Possible interface:

```text
Ang: [ 930 ]  ◀ Previous   Next ▶

Raag:
Guru / Author:
Section:
Shabad:
```

Search results should eventually provide meaningful location information instead of an internal database record number.

---

# Phase 5 — Research Workspace

Create a research-oriented view inspired by modern Gurbani search applications.

Possible layout:

```text
┌──────────────────────────────────────────────────────────────┐
│ Search Gurbani                                    🔎         │
├──────────────────────┬───────────────────────────────────────┤
│ RESULTS              │ PRESENTATION                          │
│                      │                                       │
│ Match 1              │ Complete Gurbani passage             │
│ Match 2              │                                       │
│ Match 3              │ Ang / Raag / Author                  │
│                      │                                       │
├──────────────────────┴───────────────────────────────────────┤
│ Favorites │ History │ Copy │ Card │ Export                   │
└──────────────────────────────────────────────────────────────┘
```

---

# Phase 6 — Advanced Card Studio

The Card Studio can become a complete visual composition system.

### Templates

Provide reusable templates such as:

- Minimal
- Traditional
- Elegant
- Modern
- Dark devotional
- Light devotional
- Gold
- Floral
- Nature
- Khanda / Sikh-inspired decorative layouts

### Typography

Add:

- Font selection
- Font size
- Line spacing
- Letter spacing where appropriate
- Alignment
- Text position
- Maximum text width
- Automatic font scaling

### Layout

Allow control over:

- Top position
- Text block position
- Title position
- Footer position
- Margins
- Padding
- Decorative elements

### Watermark

Watermark controls should include:

- Text
- Position
- Size
- Opacity
- Alignment
- Show/hide

Example:

```text
JASS GURBANI
```

---

# Phase 7 — Background System

Allow the user to choose:

- Solid background
- Gradient
- Texture
- Local image
- User-selected photograph
- Decorative background

Future versions could include a local background library.

---

# Phase 8 — Batch Card Generator

A powerful future feature:

```text
Select 20 Gurbani quotes
        ↓
Choose template
        ↓
Choose 4:5
        ↓
Generate 20 cards
        ↓
Export folder
```

Possible controls:

- One card per search result
- One card per favorite
- Random quotes
- Custom text file
- CSV import
- SRT import

---

# Phase 9 — SRT / Video Integration

The Card Studio could eventually work with the user's existing subtitle/video workflows.

Possible workflow:

```text
Gurbani Database
      ↓
Selected Gurbani
      ↓
SRT Generator
      ↓
Quote Cards
      ↓
Video / Shorts
```

This would allow Gurbani text to become the basis for:

- Quote videos
- Short-form videos
- Slideshow videos
- Synchronized text presentations

---

# Phase 10 — Personal Collections

Allow users to organize saved Gurbani:

```text
My Collections

├── Favorites
├── Morning
├── Evening
├── Meditation
├── Inspirational
├── Peace
├── Courage
├── Family
└── Custom
```

Collections should remain local and user-controlled.

---

# Phase 11 — Export

Potential future export options:

- PNG
- JPG
- PDF
- Plain text
- Markdown
- SRT
- CSV
- JSON

For cards:

```text
1080 × 1080
1080 × 1350
1080 × 1920
```

---

# Phase 12 — Database Tools

A future database manager could provide:

- Database statistics
- Record inspection
- Duplicate detection
- Missing metadata detection
- Search indexing
- Backup
- Restore
- Import
- Export
- Database integrity checks

A backup should always be created before structural database migrations.

---

# Phase 13 — Quality & Stability

Future development should follow these rules:

### Protect the v0.8 baseline

Do not unnecessarily rewrite:

- Working search foundations
- Card rendering architecture
- Preview architecture
- Database loading
- Global Python/PySide6 setup

### Test before expanding

Every major enhancement should be tested for:

- Application startup
- Database loading
- Search
- Result selection
- Context display
- Card preview
- PNG export
- Gurmukhi rendering
- Window resizing
- Empty input
- Long text
- Missing database
- Invalid database

### Avoid fragile Qt painting

Card rendering should remain separated from widget painting.

Prefer:

```text
QImage → QPainter → QPixmap
```

over manually painting complex card content directly inside the preview widget.

---

# 🛠️ Installation

No separate virtual environment is required if PySide6 is already installed globally.

Install PySide6 if necessary:

```powershell
py -m pip install PySide6
```

Then run:

```powershell
py .\JASS_Gurbani_Explorer_v0.8.py
```

The application expects:

```text
JASS_Gurbani_Explorer_v0.8.py
gurbani.db
```

in the appropriate application directory.

---

# 📁 Suggested Project Structure

Future versions can evolve toward:

```text
JASS_Gurbani_Explorer/
│
├── app.py
├── gurbani.db
├── README.md
│
├── data/
│   └── backups/
│
├── assets/
│   ├── backgrounds/
│   ├── icons/
│   └── templates/
│
├── core/
│   ├── database.py
│   ├── search.py
│   ├── context.py
│   └── metadata.py
│
├── presentation/
│   ├── reader.py
│   └── presenter.py
│
├── cards/
│   ├── renderer.py
│   ├── templates.py
│   └── exporter.py
│
└── ui/
    ├── main_window.py
    ├── search_page.py
    ├── reader_page.py
    └── card_studio.py
```

This is a **future architectural direction**, not a requirement to immediately split the current v0.8 single-file application.

---

# 🎯 Project Vision

JASS Gurbani Explorer aims to become a simple but powerful local Gurbani workspace:

> **Search Gurbani. Read it in context. Explore it. Save it. Present it beautifully. Create meaningful cards and media from it.**

The emphasis is on:

- Local-first operation
- Simple searching
- Cohesive reading
- Respectful presentation
- Beautiful typography
- Reliable card generation
- User-controlled data
- Incremental development
- Stability before complexity

---

# 🧱 v0.8 Foundation Principle

**Do not keep rewriting the application.**

The current version is the base model.

Future work should follow:

```text
v0.8 Stable Base
       │
       ├── Search improvements
       ├── Cohesive Gurbani
       ├── Reader
       ├── Metadata
       ├── Research
       └── Card Studio
              │
              ├── Templates
              ├── Backgrounds
              ├── Typography
              └── Batch Export
```

Each major capability should be added without destabilizing the already-working foundation.

---

## License

Add the project's chosen open-source license here when the repository license is finalized.

---

## Acknowledgement

This project is intended as a personal/local Gurbani exploration and presentation tool.

Text, database contents, metadata, and source material should be handled carefully, with appropriate respect for Gurbani and with source attribution wherever applicable.
