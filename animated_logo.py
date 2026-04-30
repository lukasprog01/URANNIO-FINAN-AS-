import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QBrush, QPen, QFont


class AnimatedLogo(QWidget):
    """
    Animated URANNIO logo — glowing emerald coin with orbiting amber value-dots.
    `size` is the coin diameter; the widget is larger to accommodate the glow halo.
    """

    def __init__(self, size: int = 40, parent=None):
        super().__init__(parent)
        self._size = size
        self._angle = 0.0
        self._pulse = 0.0
        self._pulse_dir = 1.0

        margin = size // 4
        self.setFixedSize(size + margin * 2, size + margin * 2)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(20)   # 50 fps

    def _tick(self):
        self._angle = (self._angle + 1.6) % 360
        self._pulse += 0.022 * self._pulse_dir
        if self._pulse >= 1.0:
            self._pulse = 1.0
            self._pulse_dir = -1.0
        elif self._pulse <= 0.0:
            self._pulse = 0.0
            self._pulse_dir = 1.0
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        cx = self.width() / 2
        cy = self.height() / 2
        r = self._size / 2

        # ── Outer glow halo ──────────────────────────────────────────────
        glow_a = int(38 + 72 * self._pulse)
        halo = QRadialGradient(QPointF(cx, cy), r * 1.60)
        halo.setColorAt(0.0, QColor(16, 185, 129, glow_a))
        halo.setColorAt(0.5, QColor(16, 185, 129, glow_a // 2))
        halo.setColorAt(1.0, QColor(16, 185, 129, 0))
        p.setBrush(QBrush(halo))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), r * 1.60, r * 1.60)

        # ── Coin body gradient ────────────────────────────────────────────
        coin = QRadialGradient(QPointF(cx - r * 0.28, cy - r * 0.32), r * 1.55)
        coin.setColorAt(0.0, QColor(52, 211, 153))   # emerald-400
        coin.setColorAt(0.45, QColor(16, 185, 129))  # emerald-500
        coin.setColorAt(1.0, QColor(4,  120,  87))   # emerald-700
        p.setBrush(QBrush(coin))
        p.drawEllipse(QPointF(cx, cy), r, r)

        # ── Inner shine highlight ─────────────────────────────────────────
        shine_a = int(22 + 44 * self._pulse)
        shine = QRadialGradient(QPointF(cx - r * 0.22, cy - r * 0.30), r * 0.80)
        shine.setColorAt(0.0, QColor(255, 255, 255, shine_a + 60))
        shine.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(shine))
        p.drawEllipse(QPointF(cx, cy), r, r)

        # ── Inner decorative ring ─────────────────────────────────────────
        ring_a = int(50 + 50 * self._pulse)
        ring_pen = QPen(QColor(255, 255, 255, ring_a))
        ring_pen.setWidthF(max(1.0, r * 0.05))
        p.setPen(ring_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r * 0.68, r * 0.68)

        # ── Orbiting amber value-dots ─────────────────────────────────────
        p.setPen(Qt.PenStyle.NoPen)
        orbit_r = r * 1.20
        # (phase_offset_degrees, dot_radius, alpha)
        dots = [
            (0,   r * 0.14, 255),
            (120, r * 0.10, 205),
            (240, r * 0.07, 150),
        ]
        for phase, ds, alpha in dots:
            ang = math.radians(self._angle + phase)
            dx = cx + orbit_r * math.cos(ang)
            dy = cy + orbit_r * math.sin(ang)
            # soft amber glow around each dot
            dg = QRadialGradient(QPointF(dx, dy), ds * 3.2)
            dg.setColorAt(0.0, QColor(251, 191, 36, int(alpha * 0.50)))
            dg.setColorAt(1.0, QColor(251, 191, 36, 0))
            p.setBrush(QBrush(dg))
            p.drawEllipse(QPointF(dx, dy), ds * 3.2, ds * 3.2)
            # solid amber core
            p.setBrush(QColor(251, 191, 36, alpha))
            p.drawEllipse(QPointF(dx, dy), ds, ds)

        # ── "U" lettermark ────────────────────────────────────────────────
        p.setPen(QColor(255, 255, 255, 245))
        f = QFont("Segoe UI", max(8, int(r * 0.76)), QFont.Weight.Bold)
        p.setFont(f)
        p.drawText(
            QRectF(cx - r, cy - r, r * 2, r * 2),
            Qt.AlignmentFlag.AlignCenter,
            "U",
        )

        p.end()
