import sys, sqlite3, re, json
from pathlib import Path

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QFont, QPainter, QLinearGradient, QColor, QPen, QBrush, QImage, QFontDatabase, QTextDocument
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QTextEdit, QSplitter,
    QFrame, QMessageBox, QFileDialog, QStackedWidget, QSpinBox, QStatusBar,
    QComboBox, QCheckBox, QFormLayout, QSlider, QButtonGroup
)

APP = "JASS Gurbani Explorer • Search • Presentation • Card Studio"
DB_FILE = Path(__file__).with_name("gurbani.db")


def clean(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def tokens(s):
    return [x for x in re.findall(r"[^\s]+", (s or "").strip()) if x]


class GurbaniDB:
    def __init__(self, path):
        self.path = Path(path)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.columns = {r[1] for r in self.conn.execute("PRAGMA table_info(gurbani_lines)")}

    def close(self):
        self.conn.close()

    def count(self):
        return self.conn.execute("SELECT COUNT(*) FROM gurbani_lines").fetchone()[0]

    def rows(self):
        return self.conn.execute("SELECT * FROM gurbani_lines ORDER BY id").fetchall()

    def get(self, rid):
        return self.conn.execute("SELECT * FROM gurbani_lines WHERE id=?", (rid,)).fetchone()

    def search(self, query, mode="All words", full_words=True, first_letter=False, limit=500):
        """Reliable local search. Uses Python matching over the small local corpus so
        Unicode/Gurmukhi search behaves predictably even when FTS tokenization differs."""
        q = clean(query)
        if not q:
            return []
        terms = tokens(q)
        all_rows = self.rows()
        scored = []
        for row in all_rows:
            text = row["text"] or ""
            hay = clean(text)
            if first_letter:
                ok_terms = [any(w.startswith(t[0]) for w in tokens(hay) if t) for t in terms]
            elif full_words:
                # Exact Unicode whitespace-delimited word matching.
                words = set(tokens(hay))
                ok_terms = [t in words for t in terms]
            else:
                ok_terms = [t in hay for t in terms]
            if (all(ok_terms) if mode == "All words" else any(ok_terms)):
                score = sum(hay.count(t) for t in terms if t)
                scored.append((score, row))
        scored.sort(key=lambda x: (-x[0], x[1]["id"]))
        return [r for _, r in scored[:limit]]

    def context(self, rid, radius):
        if radius <= 0:
            r = self.get(rid)
            return [r] if r else []
        # IDs are the safest local ordering for this corpus. source_line has gaps,
        # so context based on arbitrary source_line distances can skip material.
        rows = self.conn.execute(
            "SELECT * FROM gurbani_lines WHERE id BETWEEN ? AND ? ORDER BY id",
            (max(1, rid-radius), rid+radius)
        ).fetchall()
        return rows

    def random(self, n=100):
        return self.conn.execute("SELECT * FROM gurbani_lines ORDER BY RANDOM() LIMIT ?", (n,)).fetchall()


def best_gurmukhi_font():
    """Prefer Windows fonts known to cover Gurmukhi; fall back safely."""
    families = set(QFontDatabase.families())
    for name in ("Nirmala UI", "Raavi", "Noto Sans Gurmukhi", "Noto Sans", "Segoe UI"):
        if name in families:
            return name
    return "Sans Serif"


GURMUKHI_FONT = "Noto Sans Gurmukhi"


class CardPreview(QWidget):
    """Safe card renderer.

    The previous version painted directly in QWidget.paintEvent() and resized the
    widget during export. That can cause nested paint operations and the
    QBackingStore::endPaint() error. This version renders into an off-screen
    QImage and displays the resulting pixmap. Export never touches the widget's
    paint lifecycle.
    """
    THEMES = {
        "Midnight Gold": ("#080b12", "#29364d", "#d9b86c", "#ffffff"),
        "Saffron Dawn": ("#2a1208", "#7d421e", "#f5ca73", "#fff9ef"),
        "Amrit Glow": ("#061919", "#145b58", "#b7eee4", "#f7ffff"),
        "Royal Indigo": ("#0a0d2b", "#30346e", "#c9cdff", "#ffffff"),
        "Lotus Night": ("#210b1e", "#71355e", "#f1abd0", "#fff8fc"),
        "Forest Serenity": ("#07170f", "#255d3d", "#b9dfb4", "#f8fff7"),
        "Paper & Ink": ("#f5efe1", "#e5dac2", "#8a5b27", "#1e1a15"),
    }
    RATIOS = {"4:5": (1080, 1350), "1:1": (1080, 1080), "9:16": (1080, 1920)}

    def __init__(self):
        super().__init__()
        from PySide6.QtGui import QPixmap
        self.QPixmap = QPixmap
        self.text = "ੴ"
        self.title = ""
        self.footer = ""
        self.watermark = "JASS GURBANI"
        self.theme = "Midnight Gold"
        self.font_size = 34
        self.gurmukhi_font = best_gurmukhi_font()
        self.title_size = 16
        self.show_watermark = True
        self.ratio = "4:5"
        self._image = QImage()
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(360, 420)
        self.preview.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.preview)

    def set_content(self, text, title="", footer=""):
        self.text = text or "ੴ"
        self.title = title or ""
        self.footer = footer or ""
        self.refresh_image()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._show_image()

    def _show_image(self):
        if self._image.isNull():
            return
        pix = self.QPixmap.fromImage(self._image)
        target = self.preview.size()
        if target.width() > 10 and target.height() > 10:
            pix = pix.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview.setPixmap(pix)

    def _render_image(self, width, height):
        bg1, bg2, accent, fg = self.THEMES.get(self.theme, self.THEMES["Midnight Gold"])
        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(QColor(bg1))
        painter = QPainter(image)
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            r = QRectF(12, 12, width - 24, height - 24)

            gradient = QLinearGradient(r.topLeft(), r.bottomRight())
            gradient.setColorAt(0.0, QColor(bg1))
            gradient.setColorAt(0.5, QColor(bg2))
            gradient.setColorAt(1.0, QColor(bg1))
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(r, 28, 28)

            ring_color = QColor(accent)
            ring_color.setAlpha(45)
            pen = QPen(ring_color)
            pen.setWidth(max(2, width // 540))
            painter.setPen(pen)
            for inset in (28, 46, 64):
                if width > inset * 2 + 50 and height > inset * 2 + 50:
                    painter.drawRoundedRect(r.adjusted(inset, inset, -inset, -inset), 18, 18)

            painter.setPen(QColor(accent))
            painter.setFont(QFont("Segoe UI Symbol", max(24, width // 38), QFont.Bold))
            painter.drawText(QRectF(35, 28, width - 70, 55), Qt.AlignCenter, "ੴ")

            if self.title:
                painter.setPen(QColor(accent))
                painter.setFont(QFont("Segoe UI", max(12, int(self.title_size * width / 1080)), QFont.DemiBold))
                painter.drawText(QRectF(50, 88, width - 100, 48), Qt.AlignCenter, self.title)

            painter.setPen(QColor(fg))
            font_px = max(18, int(self.font_size * width / 1080))
            top = 145 if self.title else 120
            bottom = 145 if (self.footer or (self.show_watermark and self.watermark)) else 75
            text_rect = r.adjusted(55, top, -55, -bottom)

            # QTextDocument gives Qt's text engine a dedicated layout pass.
            # This is more reliable for Gurmukhi shaping and line wrapping than
            # repeatedly drawing a complex-script string directly on the canvas.
            doc = QTextDocument()
            doc.setDocumentMargin(0)
            font = QFont(self.gurmukhi_font, font_px, QFont.Medium)
            doc.setDefaultFont(font)
            doc.setTextWidth(text_rect.width())
            cursor = doc.find("")
            doc.setPlainText(self.text)
            painter.save()
            painter.translate(text_rect.left(), text_rect.top())
            painter.setPen(QColor(fg))
            doc.drawContents(painter, QRectF(0, 0, text_rect.width(), text_rect.height()))
            painter.restore()

            if self.footer:
                painter.setPen(QColor(accent))
                painter.setFont(QFont("Segoe UI", max(9, int(10 * width / 1080)), QFont.DemiBold))
                painter.drawText(QRectF(40, height - 112, width - 80, 28), Qt.AlignCenter, self.footer)

            if self.show_watermark and self.watermark:
                wm = QColor(fg)
                wm.setAlpha(150)
                painter.setPen(wm)
                painter.setFont(QFont("Segoe UI", max(8, int(9 * width / 1080)), QFont.DemiBold))
                painter.drawText(QRectF(35, height - 55, width - 70, 28), Qt.AlignCenter, self.watermark)
        finally:
            painter.end()
        return image

    def refresh_image(self):
        width, height = self.RATIOS.get(self.ratio, self.RATIOS["4:5"])
        self._image = self._render_image(width, height)
        self._show_image()
        self.update()

    def save_png(self, path):
        width, height = self.RATIOS.get(self.ratio, self.RATIOS["4:5"])
        image = self._render_image(width, height)
        return image.save(str(path), "PNG")


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP); self.resize(1580, 960)
        self.db = None; self.results = []; self.random_rows = []; self.current = None
        self.current_passage = ""; self.favorites = set(); self.history = []
        self.build_ui(); self.open_db(DB_FILE); self.dark = True; self.apply_style()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self.update_card)

    def build_ui(self):
        root = QWidget(); self.setCentralWidget(root); outer = QVBoxLayout(root); outer.setContentsMargins(18,15,18,12)
        head = QHBoxLayout(); v = QVBoxLayout()
        a = QLabel("ੴ  JASS GURBANI"); a.setObjectName("title")
        b = QLabel("SEARCH  •  PRESENTATION  •  RESEARCH  •  CARD STUDIO"); b.setObjectName("subtitle")
        v.addWidget(a); v.addWidget(b); head.addLayout(v); head.addStretch()
        self.badge = QLabel("DATABASE • —"); self.badge.setObjectName("badge"); head.addWidget(self.badge); outer.addLayout(head)
        self.stack = QStackedWidget(); self.stack.addWidget(self.search_page()); self.stack.addWidget(self.card_page()); self.stack.addWidget(self.random_page()); self.stack.addWidget(self.favorites_page()); self.stack.addWidget(self.about_page())
        nav = QFrame(); nav.setObjectName("nav"); nv = QVBoxLayout(nav)
        for label, idx in [("⌕  Search",0),("▣  Card Studio",1),("✦  Random",2),("♥  Favorites",3),("ⓘ  About",4)]:
            bt=QPushButton(label); bt.clicked.connect(lambda _,i=idx:self.stack.setCurrentIndex(i)); nv.addWidget(bt)
        nv.addStretch(); op=QPushButton("Open Database"); op.clicked.connect(self.choose_db); nv.addWidget(op)
        th=QPushButton("☾  Toggle Theme"); th.clicked.connect(self.toggle_theme); nv.addWidget(th)
        row=QHBoxLayout(); row.addWidget(nav); row.addWidget(self.stack,1); outer.addLayout(row,1); self.setStatusBar(QStatusBar())

    def search_page(self):
        page=QWidget(); lay=QVBoxLayout(page)
        bar=QHBoxLayout(); self.search=QLineEdit(); self.search.setPlaceholderText("Type a Gurmukhi word or phrase…"); self.search.setMinimumHeight(50); self.search.returnPressed.connect(self.do_search); bar.addWidget(self.search,1)
        bt=QPushButton("🔎 SEARCH"); bt.clicked.connect(self.do_search); bar.addWidget(bt); clear=QPushButton("Clear"); clear.clicked.connect(self.clear_search); bar.addWidget(clear); lay.addLayout(bar)
        tools=QFrame(); tools.setObjectName("toolbar"); tv=QHBoxLayout(tools)
        tv.addWidget(QLabel("Match")); self.mode=QComboBox(); self.mode.addItems(["All words","Any word"]); tv.addWidget(self.mode)
        self.full=QCheckBox("Full word(s)"); self.full.setChecked(True); tv.addWidget(self.full)
        self.first=QCheckBox("First letter"); tv.addWidget(self.first)
        tv.addWidget(QLabel("Context")); self.ctx=QComboBox(); self.ctx.addItems(["Matched only","±1","±2","±3","±5","±8"]); self.ctx.setCurrentIndex(2); tv.addWidget(self.ctx)
        self.coh=QCheckBox("Cohesive passage"); self.coh.setChecked(True); tv.addWidget(self.coh); tv.addStretch(); lay.addWidget(tools)
        self.info=QLabel("Search uses the complete local corpus. Context is assembled by database record order."); self.info.setObjectName("muted"); lay.addWidget(self.info)
        split=QSplitter(Qt.Horizontal); self.list=QListWidget(); self.list.currentRowChanged.connect(self.select_result); split.addWidget(self.list)
        panel=QFrame(); panel.setObjectName("panel"); pv=QVBoxLayout(panel)
        self.meta=QLabel("Select a search result"); self.meta.setObjectName("muted"); pv.addWidget(self.meta)
        self.reader=QTextEdit(); self.reader.setReadOnly(True); self.reader.setFont(QFont("Noto Sans Gurmukhi",27)); pv.addWidget(self.reader,1)
        actions=QHBoxLayout()
        for label, fn in [("♥ Favorite",self.favorite_current),("✦ Create Card",self.use_current_for_card),("📋 Copy Passage",self.copy_passage),("💾 Export TXT",self.export_passage),("◀ Prev",self.prev_result),("Next ▶",self.next_result)]:
            x=QPushButton(label); x.clicked.connect(fn); actions.addWidget(x)
        pv.addLayout(actions); split.addWidget(panel); split.setSizes([620,900]); lay.addWidget(split,1); return page

    def card_page(self):
        page=QWidget(); lay=QHBoxLayout(page)
        left=QFrame(); left.setObjectName("panel"); lv=QVBoxLayout(left)
        lab=QLabel("CARD STUDIO"); lab.setObjectName("panelTitle"); lv.addWidget(lab)
        self.card_text=QTextEdit(); self.card_text.setPlaceholderText("Paste Gurmukhi Gurbani here… the preview updates immediately."); self.card_text.setMinimumHeight(230); lv.addWidget(self.card_text)
        form=QFormLayout()
        self.design=QComboBox(); self.design.addItems(CardPreview.THEMES.keys()); form.addRow("Design",self.design)
        self.ratio=QComboBox(); self.ratio.addItems(CardPreview.RATIOS.keys()); form.addRow("Size",self.ratio)
        self.card_font=QSlider(Qt.Horizontal); self.card_font.setRange(20,60); self.card_font.setValue(34); form.addRow("Text size",self.card_font)
        self.card_title=QLineEdit(); self.card_title.setPlaceholderText("Optional title"); form.addRow("Title",self.card_title)
        self.card_footer=QLineEdit(); self.card_footer.setPlaceholderText("Optional Ang / Raag / attribution"); form.addRow("Footer",self.card_footer)
        self.card_water=QLineEdit("JASS GURBANI"); form.addRow("Watermark",self.card_water)
        self.water_on=QCheckBox("Show watermark"); self.water_on.setChecked(True); form.addRow("",self.water_on)
        lv.addLayout(form)
        row=QHBoxLayout(); exp=QPushButton("🖼 Export PNG"); exp.clicked.connect(self.export_card); row.addWidget(exp); ref=QPushButton("↻ Refresh Preview"); ref.clicked.connect(self.update_card); row.addWidget(ref); clr=QPushButton("Clear"); clr.clicked.connect(lambda:self.card_text.clear()); row.addWidget(clr); lv.addLayout(row)
        note=QLabel("Paste directly, or use Search → Create Card. No separate editor is required."); note.setObjectName("muted"); lv.addWidget(note); lay.addWidget(left,1)
        right=QFrame(); right.setObjectName("panel"); rv=QVBoxLayout(right); ph=QLabel("LIVE PREVIEW"); ph.setObjectName("panelTitle"); rv.addWidget(ph)
        self.canvas=CardPreview(); rv.addWidget(self.canvas,1); lay.addWidget(right,1)
        for w in [self.card_text,self.card_title,self.card_footer,self.card_water]: w.textChanged.connect(self.update_card)
        self.design.currentTextChanged.connect(self.update_card); self.ratio.currentTextChanged.connect(self.update_card); self.card_font.valueChanged.connect(self.update_card); self.water_on.stateChanged.connect(self.update_card)
        return page

    def random_page(self):
        page=QWidget(); lay=QVBoxLayout(page); h=QHBoxLayout(); x=QLabel("✦ RANDOM DISCOVERY"); x.setObjectName("panelTitle"); h.addWidget(x); h.addStretch(); b=QPushButton("New Selection"); b.clicked.connect(self.load_random); h.addWidget(b); lay.addLayout(h)
        self.random_list=QListWidget(); self.random_list.currentRowChanged.connect(self.select_random); lay.addWidget(self.random_list,1); return page

    def favorites_page(self):
        page=QWidget(); lay=QVBoxLayout(page); h=QHBoxLayout(); x=QLabel("♥ FAVORITES"); x.setObjectName("panelTitle"); h.addWidget(x); h.addStretch(); b=QPushButton("Refresh"); b.clicked.connect(self.refresh_favorites); h.addWidget(b); lay.addLayout(h); self.fav_list=QListWidget(); self.fav_list.currentRowChanged.connect(self.select_favorite); lay.addWidget(self.fav_list,1); return page

    def about_page(self):
        page=QWidget(); lay=QVBoxLayout(page); x=QLabel("JASS GURBANI EXPLORER"); x.setObjectName("panelTitle"); lay.addWidget(x); t=QTextEdit(); t.setReadOnly(True); t.setPlainText("Offline Gurbani search, cohesive presentation and quote-card workspace.\n\nThe search engine deliberately avoids depending on SQLite FTS tokenization for normal searching. It scans the local corpus in Python, giving predictable Unicode/Gurmukhi matching.\n\nContext is assembled from adjacent database records, not arbitrary source-line distances. This prevents the previous context logic from jumping over gaps.\n\nCard Studio is live: pasted text, design, size, title, footer and watermark all update the preview immediately.\n\nFuture: verified Ang/page mapping, scanned-page viewer, shabad-aware grouping, metadata filters and richer card templates."); lay.addWidget(t,1); return page

    def open_db(self,path):
        try:
            if self.db: self.db.close()
            self.db=GurbaniDB(path); n=self.db.count(); self.badge.setText(f"DATABASE • {Path(path).name} • {n:,} records"); self.statusBar().showMessage(f"Loaded {n:,} records"); self.load_random(); self.refresh_favorites()
        except Exception as e: QMessageBox.critical(self,"Database error",str(e))

    def choose_db(self):
        p,_=QFileDialog.getOpenFileName(self,"Open Gurbani Database",str(Path.home()),"SQLite (*.db *.sqlite *.sqlite3)")
        if p:self.open_db(p)

    def clear_search(self): self.search.clear(); self.results=[]; self.list.clear(); self.info.setText("Search cleared."); self.reader.clear(); self.meta.setText("Select a search result")

    def do_search(self):
        if not self.db:return
        q=self.search.text().strip()
        if not q:self.info.setText("Enter a Gurmukhi word or phrase."); return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:self.results=self.db.search(q,self.mode.currentText(),self.full.isChecked(),self.first.isChecked(),500)
        finally: QApplication.restoreOverrideCursor()
        self.list.clear()
        for r in self.results:
            preview=clean(r["text"]); it=QListWidgetItem(f"#{r['id']}  •  source {r['source_line']}\n{preview[:220]}"); it.setData(Qt.UserRole,r["id"]); self.list.addItem(it)
        self.info.setText(f"{len(self.results):,} result(s) • {'cohesive context' if self.coh.isChecked() else 'matched record only'}")
        if self.results:self.list.setCurrentRow(0)

    def radius(self): return [0,1,2,3,5,8][self.ctx.currentIndex()]

    def select_result(self,i):
        if 0<=i<len(self.results):self.show_row(self.results[i])

    def show_row(self,r):
        self.current=r; rid=r["id"]
        if rid in self.history:self.history.remove(rid)
        self.history.append(rid); self.history=self.history[-100:]
        rows=self.db.context(rid,self.radius()) if self.coh.isChecked() else [r]
        # Preserve source record boundaries as lines; don't flatten Gurbani into a run-on sentence.
        blocks=[]; seen=set()
        for x in rows:
            if x and x["id"] not in seen:seen.add(x["id"]); blocks.append(clean(x["text"]))
        self.current_passage="\n".join(x for x in blocks if x)
        self.reader.setPlainText(self.current_passage)
        parts=[f"Match #{rid}",f"Source {r['source_line']}"]
        if len(rows)>1:parts.append(f"{len(rows)} adjacent records")
        for k,l in [("ang","Ang"),("raag","Raag"),("author","Author"),("section","Section")]:
            if r[k]:parts.append(f"{l}: {r[k]}")
        self.meta.setText("  •  ".join(parts)); self.statusBar().showMessage("Cohesive passage ready",2000)

    def prev_result(self):
        row=self.list.currentRow(); self.list.setCurrentRow(max(0,row-1))
    def next_result(self):
        row=self.list.currentRow(); self.list.setCurrentRow(min(self.list.count()-1,row+1))

    def favorite_current(self):
        if not self.current:return
        rid=self.current["id"]; self.favorites.symmetric_difference_update({rid}); self.refresh_favorites(); self.statusBar().showMessage("Favorite updated",1500)

    def refresh_favorites(self):
        if not hasattr(self,"fav_list") or not self.db:return
        self.fav_list.clear()
        for rid in sorted(self.favorites):
            r=self.db.get(rid)
            if r:self.fav_list.addItem(f"#{rid}  {clean(r['text'])[:220]}")

    def select_favorite(self,i):
        if i<0:return
        ids=sorted(self.favorites)
        if i<len(ids):self.show_row(self.db.get(ids[i])); self.stack.setCurrentIndex(0)

    def use_current_for_card(self):
        if not self.current:return
        self.stack.setCurrentIndex(1); self.card_text.setPlainText(self.current_passage or self.current["text"])
        footer=[]
        if self.current["ang"]:footer.append(f"Ang {self.current['ang']}")
        if self.current["raag"]:footer.append(self.current["raag"])
        if self.current["author"]:footer.append(self.current["author"])
        self.card_footer.setText("  •  ".join(footer)); self.update_card()

    def update_card(self,*args):
        if not hasattr(self,"canvas"): return
        try:
            text = self.card_text.toPlainText()
            self.canvas.theme = self.design.currentText()
            self.canvas.ratio = self.ratio.currentText()
            self.canvas.font_size = self.card_font.value()
            self.canvas.title = self.card_title.text()
            self.canvas.footer = self.card_footer.text()
            self.canvas.watermark = self.card_water.text()
            self.canvas.show_watermark = self.water_on.isChecked()
            self.canvas.set_content(text, self.card_title.text(), self.card_footer.text())
            self.statusBar().showMessage(f"Preview updated • {len(text)} characters", 1200)
        except Exception as e:
            self.statusBar().showMessage(f"Preview error: {e}", 5000)
            # Keep the last valid preview visible rather than crashing the paint path.

    def export_card(self):
        if not self.card_text.toPlainText().strip():QMessageBox.information(self,"Empty card","Paste or select Gurbani first."); return
        p,_=QFileDialog.getSaveFileName(self,"Export Gurbani Card",str(Path.home()/"gurbani_card.png"),"PNG Image (*.png)")
        if p:
            self.update_card(); QApplication.setOverrideCursor(Qt.WaitCursor)
            try: ok=self.canvas.save_png(p)
            finally: QApplication.restoreOverrideCursor()
            if ok:self.statusBar().showMessage(f"Exported: {p}",3000)

    def copy_passage(self):
        if self.current_passage:QApplication.clipboard().setText(self.current_passage)
    def export_passage(self):
        if not self.current_passage:return
        p,_=QFileDialog.getSaveFileName(self,"Export Gurbani Passage",str(Path.home()/"gurbani_passage.txt"),"Text (*.txt)")
        if p:Path(p).write_text(self.current_passage,encoding="utf-8")

    def load_random(self):
        if not self.db:return
        self.random_rows=self.db.random(100)
        if hasattr(self,"random_list"):
            self.random_list.clear()
            for r in self.random_rows:self.random_list.addItem(f"#{r['id']}  •  source {r['source_line']}\n{clean(r['text'])[:220]}")
            if self.random_rows:self.random_list.setCurrentRow(0)
    def select_random(self,i):
        if 0<=i<len(self.random_rows):self.show_row(self.random_rows[i]); self.stack.setCurrentIndex(0)
    def toggle_theme(self):self.dark=not self.dark; self.apply_style()

    def apply_style(self):
        if self.dark:bg,panel,field,text,muted,border,accent="#080c12","#151b24","#10151d","#eef2f7","#929dac","#2a3442","#788fff"
        else:bg,panel,field,text,muted,border,accent="#eef2f7","#ffffff","#f8fafc","#17202c","#617080","#d5dce6","#526ad7"
        self.setStyleSheet(f'''QWidget{{background:{bg};color:{text};font-family:"Segoe UI"}} QLabel#title{{font-size:31px;font-weight:850}} QLabel#subtitle,QLabel#muted{{color:{muted}}} QLabel#badge{{background:{panel};border:1px solid {border};border-radius:12px;padding:9px 14px;color:{muted}}} QFrame#nav,QFrame#panel{{background:{panel};border:1px solid {border};border-radius:16px}} QFrame#toolbar{{background:{panel};border:1px solid {border};border-radius:12px}} QLabel#panelTitle{{color:{muted};font-weight:800;letter-spacing:1px}} QLineEdit,QTextEdit,QComboBox,QSpinBox{{background:{field};color:{text};border:1px solid {border};border-radius:10px;padding:9px}} QLineEdit:focus,QTextEdit:focus{{border:2px solid {accent}}} QPushButton{{background:{panel};color:{text};border:1px solid {border};border-radius:10px;padding:10px 13px;font-weight:650}} QPushButton:hover{{border-color:{accent}}} QListWidget{{background:{field};border:none}} QListWidget::item{{background:{panel};border:1px solid {border};border-radius:10px;padding:10px;margin:2px}} QListWidget::item:selected{{background:{field};border:1px solid {accent}}} QCheckBox{{color:{text}}} QStatusBar{{background:{bg};color:{muted}}} QSlider::groove:horizontal{{height:6px;background:{border};border-radius:3px}} QSlider::handle:horizontal{{width:16px;margin:-5px 0;border-radius:8px;background:{accent}}}''')

    def closeEvent(self,e):
        if self.db:self.db.close()
        e.accept()


def main():
    app=QApplication(sys.argv); app.setApplicationName(APP); w=Main(); w.show(); sys.exit(app.exec())

if __name__=="__main__":main()
