"""toolbar_icons.py - Generate crisp vector toolbar icons using QPainter.

Replaces emoji-based toolbar icons with proper QPainter-rendered QIcon objects
for consistent cross-platform appearance.
"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor, QFont, QBrush, QPainterPath, QPolygonF
from PyQt6.QtCore import Qt, QRectF, QPointF


def _create_icon(size, draw_func, color="#455A64"):
    """Helper to create a QIcon from a drawing function."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    draw_func(painter, size, QColor(color))
    painter.end()
    return QIcon(pixmap)


# ---------------------------------------------------------------------------
# Project Management Icons
# ---------------------------------------------------------------------------

def gear_icon(size=32, color="#546E7A"):
    """Project Settings - gear/cog icon."""
    def draw(p, s, c):
        pen = QPen(c, s * 0.06)
        p.setPen(pen)
        p.setBrush(QBrush(c))
        center = s / 2
        outer_r = s * 0.38
        inner_r = s * 0.26
        tooth_count = 8

        import math
        path = QPainterPath()
        for i in range(tooth_count):
            a1 = math.radians(i * 360 / tooth_count - 12)
            a2 = math.radians(i * 360 / tooth_count + 12)
            a3 = math.radians((i + 0.5) * 360 / tooth_count - 12)
            a4 = math.radians((i + 0.5) * 360 / tooth_count + 12)
            if i == 0:
                path.moveTo(center + outer_r * math.cos(a1), center + outer_r * math.sin(a1))
            path.lineTo(center + outer_r * math.cos(a2), center + outer_r * math.sin(a2))
            path.lineTo(center + inner_r * math.cos(a3), center + inner_r * math.sin(a3))
            path.lineTo(center + inner_r * math.cos(a4), center + inner_r * math.sin(a4))
            next_a1 = math.radians((i + 1) * 360 / tooth_count - 12)
            path.lineTo(center + outer_r * math.cos(next_a1), center + outer_r * math.sin(next_a1))
        path.closeSubpath()
        p.drawPath(path)

        # Inner hole
        p.setBrush(QBrush(QColor(0, 0, 0, 0)))
        p.setPen(Qt.PenStyle.NoPen)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        p.drawEllipse(QPointF(center, center), s * 0.1, s * 0.1)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

    return _create_icon(size, draw, color)


def save_icon(size=32, color="#1E88E5"):
    """Save Project - floppy disk icon."""
    def draw(p, s, c):
        pen = QPen(c, s * 0.05)
        p.setPen(pen)
        p.setBrush(QBrush(c))
        m = s * 0.15  # margin

        # Outer floppy shape (with corner cut)
        path = QPainterPath()
        path.moveTo(m, m)
        path.lineTo(s - m - s * 0.12, m)  # top-right with cut
        path.lineTo(s - m, m + s * 0.12)  # cut corner
        path.lineTo(s - m, s - m)
        path.lineTo(m, s - m)
        path.closeSubpath()
        p.drawPath(path)

        # Label area (dark rectangle at bottom center)
        p.setBrush(QBrush(QColor(40, 40, 40)))
        p.setPen(Qt.PenStyle.NoPen)
        label_m = s * 0.25
        p.drawRect(QRectF(label_m, s * 0.52, s - 2 * label_m, s * 0.32))

        # Shutter slot (dark rectangle at top)
        p.drawRect(QRectF(s * 0.28, m + s * 0.02, s * 0.32, s * 0.22))

    return _create_icon(size, draw, color)


def export_excel_icon(size=32, color="#4CAF50"):
    """Export to Excel - spreadsheet/table icon with green tint."""
    def draw(p, s, c):
        m = s * 0.15
        # Document shape
        p.setPen(QPen(c, s * 0.04))
        p.setBrush(QBrush(c))
        p.drawRoundedRect(QRectF(m, m, s - 2 * m, s - 2 * m), s * 0.05, s * 0.05)

        # Grid lines (table look)
        line_color = QColor(30, 30, 30)
        p.setPen(QPen(line_color, s * 0.03))
        # Horizontal lines
        y1 = s * 0.35
        y2 = s * 0.55
        p.drawLine(QPointF(m + s * 0.05, y1), QPointF(s - m - s * 0.05, y1))
        p.drawLine(QPointF(m + s * 0.05, y2), QPointF(s - m - s * 0.05, y2))
        # Vertical line
        cx = s * 0.45
        p.drawLine(QPointF(cx, m + s * 0.1), QPointF(cx, s - m - s * 0.1))

    return _create_icon(size, draw, color)


def export_pdf_icon(size=32, color="#E53935"):
    """Export to PDF - document with PDF label."""
    def draw(p, s, c):
        m = s * 0.15
        # Document with folded corner
        path = QPainterPath()
        fold = s * 0.18
        path.moveTo(m, m)
        path.lineTo(s - m - fold, m)
        path.lineTo(s - m, m + fold)
        path.lineTo(s - m, s - m)
        path.lineTo(m, s - m)
        path.closeSubpath()
        p.setPen(QPen(c, s * 0.04))
        p.setBrush(QBrush(c))
        p.drawPath(path)

        # Fold triangle
        p.setBrush(QBrush(c.darker(140)))
        fold_path = QPainterPath()
        fold_path.moveTo(s - m - fold, m)
        fold_path.lineTo(s - m - fold, m + fold)
        fold_path.lineTo(s - m, m + fold)
        fold_path.closeSubpath()
        p.drawPath(fold_path)

        # "PDF" text
        p.setPen(QPen(QColor(255, 255, 255)))
        font = QFont("Arial", int(s * 0.2), QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(QRectF(m, s * 0.4, s - 2 * m, s * 0.3), Qt.AlignmentFlag.AlignCenter, "PDF")

    return _create_icon(size, draw, color)


# ---------------------------------------------------------------------------
# Task Management Icons
# ---------------------------------------------------------------------------

def add_task_icon(size=32, color="#4FC3F7"):
    """Add Task - plus in a circle."""
    def draw(p, s, c):
        center = s / 2
        r = s * 0.34
        p.setPen(QPen(c, s * 0.06))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(center, center), r, r)

        # Plus sign
        arm = s * 0.18
        p.drawLine(QPointF(center - arm, center), QPointF(center + arm, center))
        p.drawLine(QPointF(center, center - arm), QPointF(center, center + arm))

    return _create_icon(size, draw, color)


def bulk_add_icon(size=32, color="#4FC3F7"):
    """Bulk Add Tasks - stacked documents with plus."""
    def draw(p, s, c):
        pen = QPen(c, s * 0.05)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        # Back document (offset)
        offset = s * 0.06
        m = s * 0.18
        p.drawRoundedRect(QRectF(m + offset, m, s - 2 * m - offset, s - 2 * m - offset), 
                          s * 0.04, s * 0.04)

        # Front document
        p.setBrush(QBrush(QColor(c.red(), c.green(), c.blue(), 40)))
        p.drawRoundedRect(QRectF(m, m + offset, s - 2 * m - offset, s - 2 * m - offset),
                          s * 0.04, s * 0.04)

        # Plus sign on front
        cx = s * 0.40
        cy = s * 0.55
        arm = s * 0.10
        p.setPen(QPen(c, s * 0.06))
        p.drawLine(QPointF(cx - arm, cy), QPointF(cx + arm, cy))
        p.drawLine(QPointF(cx, cy - arm), QPointF(cx, cy + arm))

    return _create_icon(size, draw, color)


def add_subtask_icon(size=32, color="#4FC3F7"):
    """Add Subtask - indented plus with tree connector."""
    def draw(p, s, c):
        pen = QPen(c, s * 0.05)
        p.setPen(pen)

        # Tree connector (L-shape)
        lx = s * 0.25
        ty = s * 0.2
        by = s * 0.58
        rx = s * 0.45
        p.drawLine(QPointF(lx, ty), QPointF(lx, by))
        p.drawLine(QPointF(lx, by), QPointF(rx, by))

        # Plus sign (to the right)
        cx = s * 0.65
        cy = s * 0.58
        arm = s * 0.13
        p.setPen(QPen(c, s * 0.06))
        p.drawLine(QPointF(cx - arm, cy), QPointF(cx + arm, cy))
        p.drawLine(QPointF(cx, cy - arm), QPointF(cx, cy + arm))

    return _create_icon(size, draw, color)


def milestone_icon(size=32, color="#FFB300"):
    """Add Milestone - diamond shape."""
    def draw(p, s, c):
        center = s / 2
        r = s * 0.3
        diamond = QPolygonF([
            QPointF(center, center - r),
            QPointF(center + r, center),
            QPointF(center, center + r),
            QPointF(center - r, center),
        ])
        p.setPen(QPen(c, s * 0.05))
        p.setBrush(QBrush(c))
        p.drawPolygon(diamond)

    return _create_icon(size, draw, color)


def edit_icon(size=32, color="#5C6BC0"):
    """Edit Task - pencil icon."""
    def draw(p, s, c):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(c))

        # Pencil body (rotated rectangle)
        p.save()
        p.translate(s * 0.5, s * 0.5)
        p.rotate(-45)

        # Body
        body_w = s * 0.18
        body_h = s * 0.45
        p.drawRect(QRectF(-body_w / 2, -body_h, body_w, body_h))

        # Tip (triangle)
        tip = QPainterPath()
        tip.moveTo(-body_w / 2, 0)
        tip.lineTo(body_w / 2, 0)
        tip.lineTo(0, s * 0.1)
        tip.closeSubpath()
        p.drawPath(tip)

        # Eraser
        p.setBrush(QBrush(c.darker(130)))
        p.drawRect(QRectF(-body_w / 2, -body_h - s * 0.06, body_w, s * 0.06))

        p.restore()

    return _create_icon(size, draw, color)


def delete_icon(size=32, color="#EF5350"):
    """Delete Task - trash can icon."""
    def draw(p, s, c):
        p.setPen(QPen(c, s * 0.04))
        p.setBrush(QBrush(c))

        # Lid
        lid_y = s * 0.2
        lid_h = s * 0.06
        p.drawRect(QRectF(s * 0.18, lid_y, s * 0.64, lid_h))
        # Handle on lid
        p.drawRect(QRectF(s * 0.36, lid_y - s * 0.06, s * 0.28, s * 0.06))

        # Can body (tapered)
        body = QPainterPath()
        body.moveTo(s * 0.22, lid_y + lid_h + s * 0.02)
        body.lineTo(s * 0.78, lid_y + lid_h + s * 0.02)
        body.lineTo(s * 0.74, s * 0.82)
        body.lineTo(s * 0.26, s * 0.82)
        body.closeSubpath()
        p.drawPath(body)

        # Vertical lines on can
        p.setPen(QPen(QColor(40, 40, 40), s * 0.03))
        for x_frac in [0.38, 0.50, 0.62]:
            x = s * x_frac
            p.drawLine(QPointF(x, lid_y + lid_h + s * 0.08), QPointF(x, s * 0.76))

    return _create_icon(size, draw, color)


def insert_below_icon(size=32, color="#546E7A"):
    """Insert Task Below - down arrow with line."""
    def draw(p, s, c):
        pen = QPen(c, s * 0.06)
        p.setPen(pen)

        cx = s / 2
        # Horizontal line at top
        p.drawLine(QPointF(s * 0.2, s * 0.25), QPointF(s * 0.8, s * 0.25))

        # Down arrow
        p.drawLine(QPointF(cx, s * 0.38), QPointF(cx, s * 0.72))
        # Arrowhead
        p.drawLine(QPointF(cx, s * 0.72), QPointF(cx - s * 0.12, s * 0.60))
        p.drawLine(QPointF(cx, s * 0.72), QPointF(cx + s * 0.12, s * 0.60))

    return _create_icon(size, draw, color)


def expand_icon(size=32, color="#546E7A"):
    """Expand - plus in a square."""
    def draw(p, s, c):
        pen = QPen(c, s * 0.05)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        m = s * 0.18
        p.drawRoundedRect(QRectF(m, m, s - 2 * m, s - 2 * m), s * 0.06, s * 0.06)

        # Plus
        center = s / 2
        arm = s * 0.16
        p.drawLine(QPointF(center - arm, center), QPointF(center + arm, center))
        p.drawLine(QPointF(center, center - arm), QPointF(center, center + arm))

    return _create_icon(size, draw, color)


# ---------------------------------------------------------------------------
# Move Icons
# ---------------------------------------------------------------------------

def move_up_icon(size=32, color="#455A64"):
    """Move Up - upward arrow."""
    def draw(p, s, c):
        pen = QPen(c, s * 0.07)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)

        cx = s / 2
        p.drawLine(QPointF(cx, s * 0.75), QPointF(cx, s * 0.25))
        p.drawLine(QPointF(cx, s * 0.25), QPointF(cx - s * 0.18, s * 0.42))
        p.drawLine(QPointF(cx, s * 0.25), QPointF(cx + s * 0.18, s * 0.42))

    return _create_icon(size, draw, color)


def move_down_icon(size=32, color="#455A64"):
    """Move Down - downward arrow."""
    def draw(p, s, c):
        pen = QPen(c, s * 0.07)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)

        cx = s / 2
        p.drawLine(QPointF(cx, s * 0.25), QPointF(cx, s * 0.75))
        p.drawLine(QPointF(cx, s * 0.75), QPointF(cx - s * 0.18, s * 0.58))
        p.drawLine(QPointF(cx, s * 0.75), QPointF(cx + s * 0.18, s * 0.58))

    return _create_icon(size, draw, color)


# ---------------------------------------------------------------------------
# Indent / Outdent Icons
# ---------------------------------------------------------------------------

def indent_icon(size=32, color="#455A64"):
    """Indent Task - right arrow with lines."""
    def draw(p, s, c):
        pen = QPen(c, s * 0.05)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)

        # Horizontal guide lines
        for y_frac in [0.28, 0.50, 0.72]:
            p.drawLine(QPointF(s * 0.45, s * y_frac), QPointF(s * 0.82, s * y_frac))

        # Right arrow
        p.setPen(QPen(c, s * 0.06, cap=Qt.PenCapStyle.RoundCap, join=Qt.PenJoinStyle.RoundJoin))
        cx = s * 0.28
        cy = s / 2
        p.drawLine(QPointF(s * 0.12, cy - s * 0.16), QPointF(cx, cy))
        p.drawLine(QPointF(s * 0.12, cy + s * 0.16), QPointF(cx, cy))

    return _create_icon(size, draw, color)


def outdent_icon(size=32, color="#455A64"):
    """Outdent Task - left arrow with lines."""
    def draw(p, s, c):
        pen = QPen(c, s * 0.05)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)

        # Horizontal guide lines
        for y_frac in [0.28, 0.50, 0.72]:
            p.drawLine(QPointF(s * 0.45, s * y_frac), QPointF(s * 0.82, s * y_frac))

        # Left arrow
        p.setPen(QPen(c, s * 0.06, cap=Qt.PenCapStyle.RoundCap, join=Qt.PenJoinStyle.RoundJoin))
        cx = s * 0.12
        cy = s / 2
        p.drawLine(QPointF(s * 0.28, cy - s * 0.16), QPointF(cx, cy))
        p.drawLine(QPointF(s * 0.28, cy + s * 0.16), QPointF(cx, cy))

    return _create_icon(size, draw, color)


def bulk_indent_icon(size=32, color="#455A64"):
    """Bulk Indent - double right arrows."""
    def draw(p, s, c):
        pen = QPen(c, s * 0.06)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)

        cy = s / 2
        # First arrow
        x1 = s * 0.15
        p.drawLine(QPointF(x1, cy - s * 0.2), QPointF(x1 + s * 0.15, cy))
        p.drawLine(QPointF(x1, cy + s * 0.2), QPointF(x1 + s * 0.15, cy))
        # Second arrow
        x2 = s * 0.35
        p.drawLine(QPointF(x2, cy - s * 0.2), QPointF(x2 + s * 0.15, cy))
        p.drawLine(QPointF(x2, cy + s * 0.2), QPointF(x2 + s * 0.15, cy))

        # Lines
        p.setPen(QPen(c, s * 0.04, cap=Qt.PenCapStyle.RoundCap))
        for y_frac in [0.30, 0.50, 0.70]:
            p.drawLine(QPointF(s * 0.58, s * y_frac), QPointF(s * 0.85, s * y_frac))

    return _create_icon(size, draw, color)


def bulk_outdent_icon(size=32, color="#455A64"):
    """Bulk Outdent - double left arrows."""
    def draw(p, s, c):
        pen = QPen(c, s * 0.06)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)

        cy = s / 2
        # First arrow
        x1 = s * 0.35
        p.drawLine(QPointF(x1, cy - s * 0.2), QPointF(x1 - s * 0.15, cy))
        p.drawLine(QPointF(x1, cy + s * 0.2), QPointF(x1 - s * 0.15, cy))
        # Second arrow
        x2 = s * 0.55
        p.drawLine(QPointF(x2, cy - s * 0.2), QPointF(x2 - s * 0.15, cy))
        p.drawLine(QPointF(x2, cy + s * 0.2), QPointF(x2 - s * 0.15, cy))

        # Lines
        p.setPen(QPen(c, s * 0.04, cap=Qt.PenCapStyle.RoundCap))
        for y_frac in [0.30, 0.50, 0.70]:
            p.drawLine(QPointF(s * 0.62, s * y_frac), QPointF(s * 0.88, s * y_frac))

    return _create_icon(size, draw, color)


# ---------------------------------------------------------------------------
# Formatting Icons
# ---------------------------------------------------------------------------

def bold_icon(size=32, color="#37474F"):
    """Bold - letter B."""
    def draw(p, s, c):
        font = QFont("Arial", int(s * 0.45), QFont.Weight.Bold)
        p.setFont(font)
        p.setPen(QPen(c))
        p.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, "B")
    return _create_icon(size, draw, color)


def italic_icon(size=32, color="#37474F"):
    """Italic - letter I."""
    def draw(p, s, c):
        font = QFont("Arial", int(s * 0.45), QFont.Weight.Normal)
        font.setItalic(True)
        p.setFont(font)
        p.setPen(QPen(c))
        p.drawText(QRectF(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, "I")
    return _create_icon(size, draw, color)


def underline_icon(size=32, color="#37474F"):
    """Underline - letter U with underline."""
    def draw(p, s, c):
        font = QFont("Arial", int(s * 0.40), QFont.Weight.Normal)
        p.setFont(font)
        p.setPen(QPen(c))
        p.drawText(QRectF(0, -s * 0.06, s, s), Qt.AlignmentFlag.AlignCenter, "U")
        # Underline bar
        p.setPen(QPen(c, s * 0.06))
        y = s * 0.78
        p.drawLine(QPointF(s * 0.22, y), QPointF(s * 0.78, y))
    return _create_icon(size, draw, color)


def font_color_icon(size=32, color="#37474F"):
    """Font Color - letter A with colored bar."""
    def draw(p, s, c):
        font = QFont("Arial", int(s * 0.40), QFont.Weight.Bold)
        p.setFont(font)
        p.setPen(QPen(c))
        p.drawText(QRectF(0, -s * 0.08, s, s), Qt.AlignmentFlag.AlignCenter, "A")
        # Color bar at bottom (rainbow-ish gradient)
        bar_y = s * 0.76
        bar_h = s * 0.1
        colors = ["#E53935", "#FF9800", "#4CAF50", "#2196F3"]
        bar_w = (s * 0.56) / len(colors)
        for i, col in enumerate(colors):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(col)))
            p.drawRect(QRectF(s * 0.22 + i * bar_w, bar_y, bar_w, bar_h))
    return _create_icon(size, draw, color)


def bg_color_icon(size=32, color="#546E7A"):
    """Background Color - paint bucket icon."""
    def draw(p, s, c):
        pen = QPen(c, s * 0.05)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(QBrush(QColor(c.red(), c.green(), c.blue(), 60)))

        # Bucket shape
        path = QPainterPath()
        path.moveTo(s * 0.2, s * 0.3)
        path.lineTo(s * 0.65, s * 0.3)
        path.lineTo(s * 0.6, s * 0.75)
        path.lineTo(s * 0.25, s * 0.75)
        path.closeSubpath()
        p.drawPath(path)

        # Handle
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(QRectF(s * 0.3, s * 0.12, s * 0.25, s * 0.25), 0, 180 * 16)

        # Paint drop
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(c))
        drop = QPainterPath()
        drop.moveTo(s * 0.75, s * 0.5)
        drop.cubicTo(s * 0.75, s * 0.5, s * 0.82, s * 0.65, s * 0.75, s * 0.72)
        drop.cubicTo(s * 0.68, s * 0.72, s * 0.68, s * 0.65, s * 0.75, s * 0.5)
        p.drawPath(drop)

    return _create_icon(size, draw, color)


# ---------------------------------------------------------------------------
# Resource & Analysis Icons
# ---------------------------------------------------------------------------

def resource_icon(size=32, color="#5C6BC0"):
    """Add Resource - person/user icon with plus."""
    def draw(p, s, c):
        p.setPen(QPen(c, s * 0.05))
        p.setBrush(QBrush(c))

        # Head
        head_cx = s * 0.4
        head_cy = s * 0.28
        head_r = s * 0.12
        p.drawEllipse(QPointF(head_cx, head_cy), head_r, head_r)

        # Body (arc/shoulders)
        body = QPainterPath()
        body.moveTo(s * 0.12, s * 0.72)
        body.cubicTo(s * 0.12, s * 0.48, s * 0.25, s * 0.42, head_cx, s * 0.42)
        body.cubicTo(s * 0.55, s * 0.42, s * 0.68, s * 0.48, s * 0.68, s * 0.72)
        body.closeSubpath()
        p.drawPath(body)

        # Plus sign
        plus_cx = s * 0.78
        plus_cy = s * 0.28
        arm = s * 0.09
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(c, s * 0.07))
        p.drawLine(QPointF(plus_cx - arm, plus_cy), QPointF(plus_cx + arm, plus_cy))
        p.drawLine(QPointF(plus_cx, plus_cy - arm), QPointF(plus_cx, plus_cy + arm))

    return _create_icon(size, draw, color)



def evm_icon(size=32, color="#26C6DA"):
    """EVM Analysis - rising chart/graph icon."""
    def draw(p, s, c):
        pen = QPen(c, s * 0.05)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)

        # Axes
        p.drawLine(QPointF(s * 0.18, s * 0.18), QPointF(s * 0.18, s * 0.82))
        p.drawLine(QPointF(s * 0.18, s * 0.82), QPointF(s * 0.82, s * 0.82))

        # Trend line going up
        p.setPen(QPen(c, s * 0.06, cap=Qt.PenCapStyle.RoundCap, join=Qt.PenJoinStyle.RoundJoin))
        points = [
            QPointF(s * 0.25, s * 0.70),
            QPointF(s * 0.40, s * 0.55),
            QPointF(s * 0.55, s * 0.45),
            QPointF(s * 0.72, s * 0.28),
        ]
        for i in range(len(points) - 1):
            p.drawLine(points[i], points[i + 1])

        # Arrow tip on trend
        p.drawLine(points[-1], QPointF(s * 0.65, s * 0.30))
        p.drawLine(points[-1], QPointF(s * 0.72, s * 0.38))

    return _create_icon(size, draw, color)
