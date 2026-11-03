"""Pipette écran : portail XDG (Wayland/GNOME/KDE) ou superposition plein écran (X11/Windows/macOS)."""
from __future__ import annotations

import os
import secrets
import sys

from PySide6.QtCore import QPoint, QRect, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QFont, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QWidget


def is_wayland() -> bool:
    return sys.platform.startswith("linux") and (
        os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland" or bool(os.environ.get("WAYLAND_DISPLAY"))
    )


def portal_available() -> bool:
    if not sys.platform.startswith("linux"):
        return False
    try:
        import jeepney  # noqa: F401
        return True
    except ImportError:
        return False


class PortalPickThread(QThread):
    """Appelle org.freedesktop.portal.Screenshot.PickColor via D-Bus (jeepney)."""

    picked = Signal(int, int, int)
    failed = Signal(str)
    cancelled = Signal()

    def run(self):
        try:
            from jeepney import DBusAddress, MatchRule, message_bus, new_method_call
            from jeepney.io.blocking import Proxy, open_dbus_connection

            conn = open_dbus_connection(bus="SESSION")
            try:
                token = "gscolor" + secrets.token_hex(4)
                sender = conn.unique_name[1:].replace(".", "_")
                path = f"/org/freedesktop/portal/desktop/request/{sender}/{token}"
                rule = MatchRule(type="signal", interface="org.freedesktop.portal.Request",
                                 member="Response", path=path)
                Proxy(message_bus, conn).AddMatch(rule)
                with conn.filter(rule) as queue:
                    portal = DBusAddress("/org/freedesktop/portal/desktop",
                                         bus_name="org.freedesktop.portal.Desktop",
                                         interface="org.freedesktop.portal.Screenshot")
                    msg = new_method_call(portal, "PickColor", "sa{sv}",
                                          ("", {"handle_token": ("s", token)}))
                    reply = conn.send_and_get_reply(msg, timeout=10)
                    if reply.header.message_type.name == "error":
                        raise RuntimeError(str(reply.body))
                    resp = conn.recv_until_filtered(queue, timeout=300)
                code, results = resp.body
                if code != 0:
                    self.cancelled.emit()
                    return
                r, g, b = results["color"][1]
                self.picked.emit(round(r * 255), round(g * 255), round(b * 255))
            finally:
                conn.close()
        except Exception as e:  # noqa: BLE001
            self.failed.emit(f"{type(e).__name__}: {e}")


class ScreenPickerOverlay(QWidget):
    """Capture l'écran sous le curseur, affiche une loupe et renvoie le pixel cliqué."""

    picked = Signal(int, int, int)
    cancelled = Signal()

    ZOOM = 12
    CELLS = 11  # nombre de pixels visibles dans la loupe

    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        self.screen_geo = screen.geometry()
        self.pix = screen.grabWindow(0)
        self.img = self.pix.toImage()
        self.dpr = self.pix.devicePixelRatio() or 1.0
        self.pos_ = self.mapFromGlobal(QCursor.pos())
        self.setGeometry(self.screen_geo)

    def start(self):
        self.showFullScreen()
        self.activateWindow()
        self.raise_()
        self.grabKeyboard()

    def _color_at(self, p: QPoint) -> QColor:
        x = int(p.x() * self.dpr)
        y = int(p.y() * self.dpr)
        x = max(0, min(self.img.width() - 1, x))
        y = max(0, min(self.img.height() - 1, y))
        return self.img.pixelColor(x, y)

    def paintEvent(self, _):
        p = QPainter(self)
        p.drawPixmap(self.rect(), self.pix)
        pos = self.pos_
        c = self._color_at(pos)
        size = self.ZOOM * self.CELLS
        half = self.CELLS // 2
        # position de la loupe (évite de sortir de l'écran)
        lx, ly = pos.x() + 24, pos.y() + 24
        if lx + size + 10 > self.width():
            lx = pos.x() - size - 24
        if ly + size + 40 > self.height():
            ly = pos.y() - size - 50
        p.setRenderHint(QPainter.Antialiasing, False)
        p.fillRect(lx - 3, ly - 3, size + 6, size + 34, QColor(30, 30, 30, 230))
        cx, cy = int(pos.x() * self.dpr), int(pos.y() * self.dpr)
        for i in range(self.CELLS):
            for j in range(self.CELLS):
                sx, sy = cx + i - half, cy + j - half
                if 0 <= sx < self.img.width() and 0 <= sy < self.img.height():
                    col = self.img.pixelColor(sx, sy)
                else:
                    col = QColor(0, 0, 0)
                p.fillRect(lx + i * self.ZOOM, ly + j * self.ZOOM, self.ZOOM, self.ZOOM, col)
        p.setPen(QPen(QColor(255, 255, 255), 2))
        p.drawRect(lx + half * self.ZOOM, ly + half * self.ZOOM, self.ZOOM, self.ZOOM)
        p.setPen(QPen(QColor(0, 0, 0), 1))
        p.drawRect(lx + half * self.ZOOM - 1, ly + half * self.ZOOM - 1, self.ZOOM + 2, self.ZOOM + 2)
        p.fillRect(lx, ly + size + 4, 24, 24, c)
        p.setPen(QColor(255, 255, 255))
        f = QFont("monospace")
        f.setPointSize(10)
        p.setFont(f)
        p.drawText(QRect(lx + 30, ly + size + 4, size - 30, 24), Qt.AlignVCenter,
                   f"{c.name().upper()}  {c.red()},{c.green()},{c.blue()}")
        p.drawText(QRect(10, 10, 600, 24), Qt.AlignLeft,
                   "Clic : choisir   •   Flèches : ajuster   •   Échap : annuler")

    def mouseMoveEvent(self, e):
        self.pos_ = e.position().toPoint()
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            c = self._color_at(e.position().toPoint())
            self._finish()
            self.picked.emit(c.red(), c.green(), c.blue())
        else:
            self._finish()
            self.cancelled.emit()

    def keyPressEvent(self, e):
        k = e.key()
        moves = {Qt.Key_Left: (-1, 0), Qt.Key_Right: (1, 0), Qt.Key_Up: (0, -1), Qt.Key_Down: (0, 1)}
        if k == Qt.Key_Escape:
            self._finish()
            self.cancelled.emit()
        elif k in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            c = self._color_at(self.pos_)
            self._finish()
            self.picked.emit(c.red(), c.green(), c.blue())
        elif k in moves:
            dx, dy = moves[k]
            self.pos_ += QPoint(dx, dy)
            QCursor.setPos(self.mapToGlobal(self.pos_))
            self.update()

    def _finish(self):
        self.releaseKeyboard()
        self.close()


def start_overlay(on_pick, on_cancel, delay_ms=250):
    """Lance la superposition après un court délai (le temps de masquer la fenêtre)."""
    holder = {}

    def go():
        ov = ScreenPickerOverlay()
        ov.picked.connect(on_pick)
        ov.cancelled.connect(on_cancel)
        holder["ov"] = ov
        ov.start()

    QTimer.singleShot(delay_ms, go)
    return holder
