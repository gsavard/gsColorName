#!/usr/bin/env python3
"""gsColorName — trouver le nom d'une couleur et tous ses codes (HEX, RGB, CMJN, Lab, décimal…).

Pipette écran intégrée + assistant IA via LM Studio (local) ou OpenRouter.
"""
from __future__ import annotations

import os
import sys

from PySide6.QtCore import QSettings, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFont, QGuiApplication, QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QColorDialog, QComboBox, QFormLayout, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPushButton, QSizePolicy, QSplashScreen, QSplitter, QStatusBar, QTableWidget, QTableWidgetItem,
    QTabWidget, QTextBrowser, QToolButton, QVBoxLayout, QWidget,
)

import colorcore as cc
import llm
import picker

APP = "gsColorName"
from version import __version__ as VERSION


# ------------------------------------------------------------------ utilitaires
class Task(QThread):
    ok = Signal(object)
    err = Signal(str)

    def __init__(self, fn, *a, **kw):
        super().__init__()
        self.fn, self.a, self.kw = fn, a, kw

    def run(self):
        try:
            self.ok.emit(self.fn(*self.a, **self.kw))
        except Exception as e:  # noqa: BLE001
            self.err.emit(str(e))


def swatch_icon(hexcode: str, size=18) -> QIcon:
    pm = QPixmap(size, size)
    pm.fill(QColor(hexcode))
    return QIcon(pm)


def text_on(c: cc.Color) -> str:
    return "#000000" if cc.contrast_ratio(c.rgb, (0, 0, 0)) >= cc.contrast_ratio(c.rgb, (255, 255, 255)) else "#FFFFFF"


class Swatch(QFrame):
    clicked = Signal(object)

    def __init__(self, size=None, parent=None):
        super().__init__(parent)
        self.color = None
        self.setFrameShape(QFrame.StyledPanel)
        if size:
            self.setFixedSize(*size)
        self.setCursor(Qt.PointingHandCursor)

    def set_color(self, c: cc.Color, tip=None):
        self.color = c
        self.setStyleSheet(f"background:{c.hex}; border:1px solid #888; border-radius:4px;")
        self.setToolTip(tip or c.hex)

    def mousePressEvent(self, e):
        if self.color:
            self.clicked.emit(self.color)


# ------------------------------------------------------------------ fenêtre
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP} — Nom et codes de couleur")
        self.resize(1180, 780)
        self.settings = QSettings(APP, APP)
        self.names = cc.NameDB()
        self.color = cc.Color(0x1E, 0x90, 0xFF)
        self.tasks: list[QThread] = []
        self.history: list[str] = self.settings.value("history", [], list) or []
        self._portal_thread = None
        self._overlay = None

        self._build_ui()
        self._load_llm_settings()
        last = self.settings.value("last_color", "")
        self.set_color(cc.Color.from_hex(last) if last else self.color, add_history=False)
        self.statusBar().showMessage(f"{len(self.names):,} noms de couleurs chargés".replace(",", " "), 6000)

    # ---------------------------------------------------------- interface
    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)

        # barre de saisie
        bar = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Code ou nom : #1E90FF, rgb(30,144,255), cmyk(88,44,0,0), 2003199, "
                                      "hsl(210,100%,56%), dodgerblue, bleu roi…")
        self.input.returnPressed.connect(self.on_parse)
        f = self.input.font()
        f.setPointSize(f.pointSize() + 2)
        self.input.setFont(f)
        b_go = QPushButton("Analyser")
        b_go.clicked.connect(self.on_parse)
        self.b_pick = QPushButton("🎯  Pipette écran")
        self.b_pick.setToolTip("Choisir un pixel n'importe où à l'écran (Ctrl+P)")
        self.b_pick.clicked.connect(self.on_eyedropper)
        b_dlg = QPushButton("🎨  Sélecteur…")
        b_dlg.setToolTip("Ouvrir le sélecteur de couleur (roue, sliders)")
        b_dlg.clicked.connect(self.on_dialog)
        b_paste = QPushButton("📋  Coller")
        b_paste.setToolTip("Analyser le contenu du presse-papiers")
        b_paste.clicked.connect(self.on_paste)
        for w in (self.input,):
            bar.addWidget(w, 1)
        b_about = QToolButton()
        b_about.setText("ℹ")
        b_about.setToolTip("À propos de gsColorName")
        b_about.clicked.connect(self.on_about)
        for b in (b_go, self.b_pick, b_dlg, b_paste, b_about):
            bar.addWidget(b)
        root.addLayout(bar)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_color_tab(), "Couleur")
        self.tabs.addTab(self._build_ai_tab(), "Assistant IA")
        root.addWidget(self.tabs, 1)
        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

        act = QAction(self)
        act.setShortcut(QKeySequence("Ctrl+P"))
        act.triggered.connect(self.on_eyedropper)
        self.addAction(act)
        act2 = QAction(self)
        act2.setShortcut(QKeySequence("Ctrl+Shift+V"))
        act2.triggered.connect(self.on_paste)
        self.addAction(act2)

    def _build_color_tab(self):
        w = QWidget()
        lay = QHBoxLayout(w)
        split = QSplitter(Qt.Horizontal)
        lay.addWidget(split)

        # --- colonne gauche : aperçu + noms
        left = QWidget()
        lv = QVBoxLayout(left)
        self.big = QLabel()
        self.big.setMinimumHeight(170)
        self.big.setAlignment(Qt.AlignCenter)
        bf = QFont()
        bf.setPointSize(20)
        bf.setBold(True)
        self.big.setFont(bf)
        lv.addWidget(self.big)

        g = QGroupBox("Nom de la couleur")
        gf = QFormLayout(g)
        self.lbl_name = QLabel()
        nf = QFont()
        nf.setPointSize(14)
        nf.setBold(True)
        self.lbl_name.setFont(nf)
        self.lbl_name.setWordWrap(True)
        self.lbl_name.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_css = QLabel()
        self.lbl_fr = QLabel()
        for l in (self.lbl_css, self.lbl_fr):
            l.setTextInteractionFlags(Qt.TextSelectableByMouse)
        gf.addRow("Nom le plus proche :", self.lbl_name)
        gf.addRow("Nom CSS / HTML :", self.lbl_css)
        gf.addRow("Nom français (base) :", self.lbl_fr)
        lv.addWidget(g)

        g2 = QGroupBox("Couleurs nommées similaires (clic = sélectionner)")
        g2v = QVBoxLayout(g2)
        self.similar = QListWidget()
        self.similar.itemActivated.connect(self._pick_from_list)
        self.similar.itemClicked.connect(self._pick_from_list)
        g2v.addWidget(self.similar)
        lv.addWidget(g2, 1)

        g3 = QGroupBox("Historique")
        self.hist_lay = QHBoxLayout(g3)
        self.hist_lay.setSpacing(4)
        lv.addWidget(g3)
        split.addWidget(left)

        # --- colonne droite : formats + harmonies
        right = QWidget()
        rv = QVBoxLayout(right)
        g4 = QGroupBox("Codes de la couleur (double-clic ou bouton = copier)")
        g4v = QVBoxLayout(g4)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Format", "Valeur", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellDoubleClicked.connect(lambda r, _c: self._copy(self.table.item(r, 1).text()))
        mono = QFont("monospace")
        mono.setStyleHint(QFont.Monospace)
        self.table.setFont(mono)
        g4v.addWidget(self.table)
        rv.addWidget(g4, 3)

        g5 = QGroupBox("Harmonies (clic = sélectionner)")
        self.harm_grid = QGridLayout(g5)
        rv.addWidget(g5, 1)
        split.addWidget(right)
        split.setSizes([430, 750])
        return w

    def _build_ai_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        g = QGroupBox("Connexion")
        form = QFormLayout(g)
        self.cb_provider = QComboBox()
        self.cb_provider.addItems(list(llm.PROVIDERS))
        self.cb_provider.currentTextChanged.connect(self._provider_changed)
        self.ed_url = QLineEdit()
        self.ed_key = QLineEdit()
        self.ed_key.setEchoMode(QLineEdit.Password)
        self.ed_key.setPlaceholderText("sk-or-v1-… (ou variable d'environnement OPENROUTER_API_KEY)")
        show = QToolButton()
        show.setText("👁")
        show.setCheckable(True)
        show.toggled.connect(lambda on: self.ed_key.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password))
        keyrow = QHBoxLayout()
        keyrow.addWidget(self.ed_key, 1)
        keyrow.addWidget(show)
        self.cb_model = QComboBox()
        self.cb_model.setEditable(True)
        self.cb_model.setMinimumWidth(380)
        self.cb_model.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        b_models = QPushButton("Lister les modèles")
        b_models.clicked.connect(self.on_list_models)
        b_test = QPushButton("Tester")
        b_test.clicked.connect(self.on_test)
        mrow = QHBoxLayout()
        mrow.addWidget(self.cb_model, 1)
        mrow.addWidget(b_models)
        mrow.addWidget(b_test)
        self.chk_save_key = QCheckBox("Mémoriser la clé API (stockée en clair dans la config utilisateur)")
        form.addRow("Fournisseur :", self.cb_provider)
        form.addRow("URL de base :", self.ed_url)
        form.addRow("Clé API :", keyrow)
        form.addRow("Modèle :", mrow)
        form.addRow("", self.chk_save_key)
        v.addWidget(g)

        row = QHBoxLayout()
        self.ai_swatch = Swatch((36, 36))
        b_name = QPushButton("🔎  Demander le nom de la couleur actuelle")
        b_name.clicked.connect(self.on_ai_name)
        row.addWidget(self.ai_swatch)
        row.addWidget(b_name)
        row.addStretch(1)
        v.addLayout(row)

        qrow = QHBoxLayout()
        self.ed_question = QLineEdit()
        self.ed_question.setPlaceholderText("Question libre sur la couleur actuelle (ex. : « quel Pantone pour une "
                                            "enseigne extérieure ? ») ou « une couleur pour… »")
        self.ed_question.returnPressed.connect(self.on_ai_question)
        b_q = QPushButton("Envoyer")
        b_q.clicked.connect(self.on_ai_question)
        qrow.addWidget(self.ed_question, 1)
        qrow.addWidget(b_q)
        v.addLayout(qrow)

        self.ai_out = QTextBrowser()
        self.ai_out.setOpenExternalLinks(True)
        self.ai_out.setPlaceholderText("La réponse du modèle s'affichera ici. Les codes HEX détectés dans la "
                                       "réponse apparaissent ci-dessous et sont cliquables.")
        v.addWidget(self.ai_out, 1)
        self.ai_colors = QHBoxLayout()
        self.ai_colors.setSpacing(4)
        v.addLayout(self.ai_colors)
        return w

    # ---------------------------------------------------------- couleur
    def set_color(self, c: cc.Color, add_history=True):
        self.color = c
        fg = text_on(c)
        self.big.setText(c.hex)
        self.big.setStyleSheet(f"background:{c.hex}; color:{fg}; border-radius:8px; border:1px solid #777;")
        self.ai_swatch.set_color(c)
        self.input.setText(c.hex)

        near = self.names.nearest(c, 12)
        css = self.names.nearest_css(c)[0]
        fr = self.names.nearest_fr(c)[0]
        d, n, h = near[0]
        exact = " (exact)" if d < 0.05 else f"  — ΔE {d:.1f}, {cc.delta_label(d)}"
        if css[0] < 0.05 and css[1] != n.lower().replace(" ", ""):
            n = f"{css[1]} / {n}"
        self.lbl_name.setText(f"{n}{exact}")
        self.lbl_css.setText(f"{css[1]}  ({'#' + css[2].upper()}, ΔE {css[0]:.1f})")
        self.lbl_fr.setText(f"{fr[1]}  ({'#' + fr[2].upper()}, ΔE {fr[0]:.1f})")

        self.similar.clear()
        for d, n, h in near:
            it = QListWidgetItem(swatch_icon("#" + h), f"{n}   #{h.upper()}   ΔE {d:.1f}")
            it.setData(Qt.UserRole, h)
            self.similar.addItem(it)

        fmts = c.formats()
        self.table.setRowCount(len(fmts))
        for i, (k, val) in enumerate(fmts):
            self.table.setItem(i, 0, QTableWidgetItem(k))
            self.table.setItem(i, 1, QTableWidgetItem(val))
            b = QToolButton()
            b.setText("Copier")
            b.clicked.connect(lambda _=False, t=val: self._copy(t))
            self.table.setCellWidget(i, 2, b)

        self._fill_harmonies(c)
        if add_history:
            self._push_history(c.hex)
        self.settings.setValue("last_color", c.hex)

    def _fill_harmonies(self, c):
        while self.harm_grid.count():
            it = self.harm_grid.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for row, (name, cols) in enumerate(c.harmonies().items()):
            self.harm_grid.addWidget(QLabel(name), row, 0)
            for j, col in enumerate(cols):
                s = Swatch((46, 22))
                s.set_color(col, f"{col.hex}")
                s.clicked.connect(lambda col: self.set_color(col))
                self.harm_grid.addWidget(s, row, j + 1)
        self.harm_grid.setColumnStretch(7, 1)

    def _push_history(self, hx):
        if hx in self.history:
            self.history.remove(hx)
        self.history.insert(0, hx)
        self.history = self.history[:16]
        self.settings.setValue("history", self.history)
        self._render_history()

    def _render_history(self):
        while self.hist_lay.count():
            it = self.hist_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        for hx in self.history:
            s = Swatch((22, 22))
            s.set_color(cc.Color.from_hex(hx))
            s.clicked.connect(lambda col: self.set_color(col))
            self.hist_lay.addWidget(s)
        self.hist_lay.addStretch(1)

    def _pick_from_list(self, item):
        self.set_color(cc.Color.from_hex(item.data(Qt.UserRole)))

    def _copy(self, text):
        QGuiApplication.clipboard().setText(text)
        self.statusBar().showMessage(f"Copié : {text}", 3000)

    # ---------------------------------------------------------- actions
    def on_parse(self):
        try:
            self.set_color(cc.parse_color(self.input.text(), self.names))
        except Exception as e:  # noqa: BLE001
            self.statusBar().showMessage(f"⚠ {e}", 6000)

    def on_paste(self):
        txt = QGuiApplication.clipboard().text().strip()
        if txt:
            self.input.setText(txt)
            self.on_parse()

    def on_about(self):
        box = QMessageBox(self)
        box.setWindowTitle(f"À propos de {APP}")
        pm = QPixmap(cc.resource_path("assets", "gscolorname-512.png"))
        if not pm.isNull():
            box.setIconPixmap(pm.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        box.setTextFormat(Qt.RichText)
        n = f"{len(self.names):,}".replace(",", " ")
        box.setText(f"<h3>{APP} {VERSION}</h3>"
                    "<p>Nom et codes d'une couleur : HEX, RGB, CMJN, HSL, Lab, décimal…<br>"
                    "Pipette écran et assistant IA (LM Studio / OpenRouter).</p>"
                    f"<p>{n} noms de couleurs — "
                    "<a href='https://github.com/meodai/color-name-list'>color-name-list</a> (MIT)</p>"
                    "<p><a href='https://github.com/gsavard/gsColorName'>github.com/gsavard/gsColorName</a> — Licence MIT</p>")
        box.exec()

    def on_dialog(self):
        q = QColorDialog.getColor(QColor(self.color.hex), self, "Choisir une couleur")
        if q.isValid():
            self.set_color(cc.Color(q.red(), q.green(), q.blue()))

    def on_eyedropper(self):
        self.b_pick.setEnabled(False)
        if picker.mac_sampler_available():
            self.statusBar().showMessage("Cliquez sur un pixel à l'écran (Échap pour annuler)…")
            s = picker.MacColorSampler(self)
            s.picked.connect(self._picked)
            s.cancelled.connect(self._pick_cancel)
            s.failed.connect(self._portal_failed)
            self._mac_sampler = s
            s.start()
        elif picker.is_wayland() and picker.portal_available():
            self.statusBar().showMessage("Cliquez sur un pixel à l'écran (portail système)…")
            t = picker.PortalPickThread()
            t.picked.connect(self._picked)
            t.cancelled.connect(self._pick_cancel)
            t.failed.connect(self._portal_failed)
            self._portal_thread = t
            t.start()
        else:
            if picker.is_wayland():
                self.statusBar().showMessage("Wayland sans jeepney : la capture risque d'être noire "
                                             "(pip install jeepney)", 8000)
            self._overlay_pick()

    def _overlay_pick(self):
        self.hide()
        self._overlay = picker.start_overlay(self._picked, self._pick_cancel)

    def _portal_failed(self, msg):
        self.statusBar().showMessage(f"Portail indisponible ({msg}) — mode capture d'écran", 8000)
        self._overlay_pick()

    def _picked(self, r, g, b):
        self._restore()
        self.set_color(cc.Color(r, g, b))
        self.statusBar().showMessage(f"Pixel choisi : {self.color.hex}", 4000)

    def _pick_cancel(self):
        self._restore()
        self.statusBar().showMessage("Pipette annulée", 3000)

    def _restore(self):
        self.b_pick.setEnabled(True)
        if not self.isVisible():
            self.show()
        self.raise_()
        self.activateWindow()

    # ---------------------------------------------------------- IA
    def _load_llm_settings(self):
        prov = self.settings.value("llm/provider", list(llm.PROVIDERS)[0])
        self.chk_save_key.setChecked(self.settings.value("llm/save_key", False, bool))
        self.cb_provider.blockSignals(True)
        self.cb_provider.setCurrentText(prov)
        self.cb_provider.blockSignals(False)
        self._provider_changed(prov, save_previous=False)
        self._render_history()

    def _pkey(self, prov=None):
        return "lmstudio" if (prov or self.cb_provider.currentText()).startswith("LM") else "openrouter"

    def _save_llm_settings(self, prov=None):
        k = self._pkey(prov)
        self.settings.setValue(f"llm/{k}/url", self.ed_url.text().strip())
        self.settings.setValue(f"llm/{k}/model", self.cb_model.currentText().strip())
        self.settings.setValue("llm/save_key", self.chk_save_key.isChecked())
        if k == "openrouter":
            self.settings.setValue("llm/openrouter/key", self.ed_key.text().strip() if self.chk_save_key.isChecked() else "")
        self.settings.setValue("llm/provider", self.cb_provider.currentText())

    _current_prov = None

    def _provider_changed(self, prov, save_previous=True):
        if save_previous and self._current_prov:
            self._save_llm_settings(self._current_prov)
        self._current_prov = prov
        k = self._pkey(prov)
        info = llm.PROVIDERS[prov]
        self.ed_url.setText(self.settings.value(f"llm/{k}/url", info["url"]))
        self.cb_model.clear()
        m = self.settings.value(f"llm/{k}/model", "")
        if m:
            self.cb_model.addItem(m)
        elif k == "openrouter":
            self.cb_model.addItem("openai/gpt-4o-mini")
        key = self.settings.value("llm/openrouter/key", "") if k == "openrouter" else ""
        if k == "openrouter" and not key:
            key = os.environ.get("OPENROUTER_API_KEY", "")
        self.ed_key.setText(key)
        self.ed_key.setEnabled(info["needs_key"])

    def _conn(self):
        return self.ed_url.text().strip(), (self.ed_key.text().strip() or None), self.cb_model.currentText().strip()

    def _run(self, fn, ok, *a):
        t = Task(fn, *a)
        t.ok.connect(ok)
        t.err.connect(self._ai_error)
        t.finished.connect(lambda: self.tasks.remove(t) if t in self.tasks else None)
        self.tasks.append(t)
        t.start()

    def _ai_error(self, msg):
        QApplication.restoreOverrideCursor()
        self.ai_out.setMarkdown(f"**Erreur :** {msg}\n\n"
                                "- LM Studio : lancez le serveur (onglet *Developer* → *Start Server*) "
                                "et chargez un modèle.\n- OpenRouter : vérifiez la clé API et le nom du modèle.")
        self.statusBar().showMessage("Erreur IA", 5000)

    def on_list_models(self):
        url, key, _ = self._conn()
        self.statusBar().showMessage("Récupération des modèles…")

        def done(models):
            cur = self.cb_model.currentText()
            self.cb_model.clear()
            self.cb_model.addItems(models)
            if cur:
                self.cb_model.setCurrentText(cur)
            self.statusBar().showMessage(f"{len(models)} modèles disponibles", 5000)
            self._save_llm_settings()
        self._run(llm.list_models, done, url, key)

    def on_test(self):
        url, key, model = self._conn()
        self.ai_out.setMarkdown("_Test en cours…_")
        self._run(llm.chat, lambda r: self.ai_out.setMarkdown(f"✅ **Connexion OK** — {model}\n\n{r}"),
                  url, key, model, [{"role": "user", "content": "Réponds seulement : OK, connecté."}])

    def _ask(self, user_msg):
        url, key, model = self._conn()
        if not model:
            QMessageBox.warning(self, APP, "Choisissez un modèle (bouton « Lister les modèles »).")
            return
        self._save_llm_settings()
        self.tabs.setCurrentIndex(1)
        self.ai_out.setMarkdown(f"_Interrogation de **{model}**…_")
        QApplication.setOverrideCursor(Qt.BusyCursor)
        msgs = [{"role": "system", "content": llm.SYSTEM_PROMPT}, {"role": "user", "content": user_msg}]

        def done(text):
            QApplication.restoreOverrideCursor()
            self.ai_out.setMarkdown(text)
            self._extract_ai_colors(text)
            self.statusBar().showMessage("Réponse reçue", 3000)
        self._run(llm.chat, done, url, key, model, msgs)

    def on_ai_name(self):
        c = self.color
        self._ask(llm.color_prompt(c, self.names.nearest(c, 6), self.names.nearest_css(c), self.names.nearest_fr(c)))

    def on_ai_question(self):
        q = self.ed_question.text().strip()
        if not q:
            return
        c = self.color
        ctx = "\n".join(f"- {k} : {v}" for k, v in c.formats()[:11])
        self._ask(f"Couleur actuelle :\n{ctx}\n\nQuestion : {q}\n\n"
                  "Si tu proposes des couleurs, donne toujours leur code HEX.")

    def _extract_ai_colors(self, text):
        import re
        while self.ai_colors.count():
            it = self.ai_colors.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        seen = []
        for h in re.findall(r"#([0-9A-Fa-f]{6})\b", text):
            h = h.upper()
            if h not in seen:
                seen.append(h)
        if not seen:
            return
        self.ai_colors.addWidget(QLabel("Couleurs citées :"))
        for h in seen[:20]:
            s = Swatch((30, 22))
            s.set_color(cc.Color.from_hex(h), f"#{h} — cliquer pour analyser")
            s.clicked.connect(lambda col: (self.set_color(col), self.tabs.setCurrentIndex(0)))
            self.ai_colors.addWidget(s)
        self.ai_colors.addStretch(1)

    def closeEvent(self, e):
        self._save_llm_settings()
        for t in self.tasks:
            t.wait(200)
        super().closeEvent(e)


def main():
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP)
    app.setApplicationVersion(VERSION)
    app.setDesktopFileName("gscolorname")
    icon = QIcon()
    for name in ("gscolorname-512.png", "gscolorname.png"):
        path = cc.resource_path("assets", name)
        if os.path.exists(path):
            icon.addFile(path)
    app.setWindowIcon(icon)

    splash = None
    banner = cc.resource_path("assets", "banner.jpg")
    if os.path.exists(banner) and "--no-splash" not in sys.argv:
        pm = QPixmap(banner)
        pm = pm.scaledToWidth(min(720, pm.width()), Qt.SmoothTransformation)
        splash = QSplashScreen(pm, Qt.WindowStaysOnTopHint)
        splash.showMessage(f"gsColorName {VERSION}  —  chargement des noms de couleurs…",
                           Qt.AlignBottom | Qt.AlignHCenter, QColor("#DDDDDD"))
        splash.show()
        app.processEvents()

    win = MainWindow()
    win.setWindowIcon(icon)
    if splash:
        QTimer.singleShot(900, lambda: (win.show(), splash.finish(win)))
    else:
        win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
