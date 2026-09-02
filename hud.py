import sys
import math
import random
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont, QRadialGradient, QLinearGradient

class StarkExpoHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.angle_fast = 0.0
        self.angle_slow = 0.0
        self.angle_reverse = 0.0
        self.wave_phase = 0.0
        
        self.metrics = {
            "CPU": 0, "RAM": 0, "TEMP": 0, "VOLTAGE": 1.2
        }
        
        self.initUI()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_telemetry)
        self.timer.start(16)
        
    def initUI(self):
        self.setWindowTitle("STARK EXPO - JARVIS CORE")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(1200, 800)
        
        screen_geo = QApplication.primaryScreen().availableGeometry()
        bx = (screen_geo.width() - self.width()) // 2
        by = (screen_geo.height() - self.height()) // 2
        self.move(bx, by)
        
    def update_telemetry(self):
        self.angle_fast += 2.5
        self.angle_slow += 0.7
        self.angle_reverse -= 1.6
        self.wave_phase += 0.18
        
        self.metrics["CPU"] = int(48 + math.sin(self.wave_phase * 0.1) * 12 + random.randint(-1, 1))
        self.metrics["RAM"] = int(76 + math.cos(self.wave_phase * 0.05) * 2)
        self.metrics["TEMP"] = int(64 + math.sin(self.wave_phase * 0.08) * 3)
        self.metrics["VOLTAGE"] = 1.22 + math.sin(self.wave_phase * 0.2) * 0.02
        
        self.repaint()

    def draw_3d_orbital_ring(self, painter, cx, cy, radius, rot_angle, tilt_x_base, tilt_y_base, stroke_width, color, is_dashed=False):
        painter.setPen(QPen(color, stroke_width, Qt.PenStyle.SolidLine if not is_dashed else Qt.PenStyle.DashLine))
        
        rad_tilt_x = math.radians(tilt_x_base + math.sin(math.radians(rot_angle)) * 28)
        rad_tilt_y = math.radians(tilt_y_base + math.cos(math.radians(rot_angle)) * 38)
        rad_spin = math.radians(rot_angle)
        
        total_points = 140
        points = []
        
        for i in range(total_points + 1):
            theta = math.radians(i * (360 / total_points))
            x2d = math.cos(theta) * radius
            y2d = math.sin(theta) * radius
            
            xr = x2d * math.cos(rad_spin) - y2d * math.sin(rad_spin)
            yr = x2d * math.sin(rad_spin) + y2d * math.cos(rad_spin)
            
            z_depth = math.sin(theta + rad_spin) * math.sin(rad_tilt_x)
            depth_scale = 1.0 + (z_depth * 0.15) 
            
            xp = xr * math.cos(rad_tilt_y) * depth_scale
            yp = (yr * math.cos(rad_tilt_x) + xp * math.sin(rad_tilt_x)) * depth_scale
            
            points.append(QPointF(xp + cx, yp + cy))
            
        prev_p = points[0]
        for p in points[1:]:
            painter.drawLine(prev_p, p)
            prev_p = p

    def draw_circular_gauge(self, painter, cx, cy, radius, value, max_value, label):
        painter.setPen(QPen(QColor(0, 240, 255, 30), 2))
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)
        
        span_angle = int(-(value / max_value) * 360 * 16)
        painter.setPen(QPen(QColor(0, 240, 255, 180), 3))
        painter.drawArc(cx - radius, cy - radius, radius * 2, radius * 2, 90 * 16, span_angle)
        
        painter.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255, 220))
        painter.drawText(cx - 16, cy + 3, f"{value}%")
        
        painter.setFont(QFont("Arial", 7, QFont.Weight.Black))
        painter.setPen(QColor(0, 240, 255, 160))
        painter.drawText(cx - 12, cy + 14, label)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        painter.fillRect(0, 0, w, h, QColor(10, 16, 26, 225))
        cx, cy = int(w * 0.5), int(h * 0.5)
        
        flash_seed = random.random()
        base_flash = 160 + int(math.sin(self.wave_phase * 2.5) * 45)
        if flash_seed > 0.94:
            base_flash = min(255, base_flash + 65)
        elif flash_seed < 0.04:
            base_flash = max(70, base_flash - 60)
            
        # --- 1. RADIAL GLOW ---
        deep_glow = QRadialGradient(QPointF(cx, cy), 420)
        deep_glow.setColorAt(0.0, QColor(0, 242, 255, int(base_flash * 0.35)))
        deep_glow.setColorAt(0.3, QColor(0, 130, 220, int(base_flash * 0.15)))
        deep_glow.setColorAt(0.6, QColor(0, 40, 90, 8))
        deep_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(deep_glow))
        painter.drawEllipse(cx - 420, cy - 420, 840, 840)
        
        # --- 2. PROJECTION PLATFORMS ---
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(0, 240, 255, 90), 2))
        painter.drawRoundedRect(cx - 90, cy - 300, 180, 10, 2, 2)
        painter.drawRoundedRect(cx - 90, cy + 290, 180, 10, 2, 2)
        
        vert_grad = QLinearGradient(QPointF(cx, cy - 290), QPointF(cx, cy + 290))
        vert_grad.setColorAt(0.0, QColor(0, 240, 255, 0))
        vert_grad.setColorAt(0.5, QColor(0, 240, 255, int(base_flash * 0.2)))
        vert_grad.setColorAt(1.0, QColor(0, 240, 255, 0))
        painter.setPen(QPen(QBrush(vert_grad), 1.5, Qt.PenStyle.DashLine))
        painter.drawLine(cx, cy - 290, cx, cy + 290)
        
        # --- 3. 3D ORBITAL ROTATION FIELD ---
        self.draw_3d_orbital_ring(painter, cx, cy, 240, self.angle_slow, 45, 20, 6.0, QColor(0, 240, 255, base_flash))
        self.draw_3d_orbital_ring(painter, cx, cy, 210, self.angle_fast, -35, 55, 5.0, QColor(0, 210, 255, int(base_flash * 0.85)))
        self.draw_3d_orbital_ring(painter, cx, cy, 180, self.angle_reverse, 60, -15, 3.5, QColor(0, 240, 255, int(base_flash * 0.7)), is_dashed=True)
        self.draw_3d_orbital_ring(painter, cx, cy, 130, self.angle_slow * 1.5, 15, 70, 4.0, QColor(0, 240, 255, int(base_flash * 0.8)))

        # --- 4. CENTRAL HUB CORE ---
        painter.setPen(QPen(QColor(0, 240, 255, 150), 3))
        painter.setBrush(QBrush(QColor(2, 16, 35, 245)))
        painter.drawEllipse(cx - 75, cy - 75, 150, 150)
        
        singularity = QRadialGradient(QPointF(cx, cy), 65)
        singularity.setColorAt(0.0, QColor(255, 255, 255, min(255, base_flash + 20)))
        singularity.setColorAt(0.3, QColor(0, 242, 255, base_flash))
        singularity.setColorAt(0.7, QColor(0, 80, 180, 70))
        singularity.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(singularity))
        painter.drawEllipse(cx - 65, cy - 65, 130, 130)
        
        # --- 5. CENTERED JARVIS TEXT (FIXED FLOATS TO INTS) ---
        text_font = QFont("Arial", 14, QFont.Weight.Black)
        painter.setFont(text_font)
        box_w, box_h = 140, 40
        box_x = cx - (box_w // 2)
        box_y = cy - (box_h // 2)
        
        # Explicit integer coordinates for drawText parameters
        painter.setPen(QColor(0, 10, 25, 240))
        painter.drawText(box_x + 2, box_y + 2, box_w, box_h, Qt.AlignmentFlag.AlignCenter, "JARVIS")
        painter.setPen(QColor(255, 255, 255, 255))
        painter.drawText(box_x, box_y, box_w, box_h, Qt.AlignmentFlag.AlignCenter, "JARVIS")
        
        # --- 6. FLOATING PARTICLES ---
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(24):
            rad_orbit = 280 + int(math.sin(self.wave_phase * 0.1 + i) * 25)
            px = int(cx + math.cos(self.angle_slow * 0.22 + i * 0.4) * rad_orbit)
            py = int(cy + math.sin(self.angle_fast * 0.11 + i * 0.35) * (rad_orbit // 2.1))
            
            part_opacity = 40 + int(math.sin(self.angle_fast * 0.4 + i) * 110)
            final_opacity = max(0, min(255, int(part_opacity * (base_flash / 200.0))))
            painter.setBrush(QBrush(QColor(0, 240, 255, final_opacity)))
            painter.drawEllipse(px - 1, py - 1, 3, 3)

        # --- 7. PERIPHERALS ---
        self.draw_circular_gauge(painter, cx - 240, cy - 280, 34, self.metrics["CPU"], 100, "CPU")
        self.draw_circular_gauge(painter, cx - 100, cy - 335, 34, self.metrics["RAM"], 100, "RAM")
        self.draw_circular_gauge(painter, cx + 100, cy - 335, 34, self.metrics["TEMP"], 120, "TEMP")
        
        painter.setFont(QFont("Arial", 16, QFont.Weight.Black))
        painter.setPen(QColor(255, 255, 255, 235))
        painter.drawText(60, 90, "STARK EXPO 2010")
        
        painter.setFont(QFont("Courier New", 9, QFont.Weight.Bold))
        painter.setPen(QColor(0, 240, 255, 170))
        painter.drawText(60, 115, "POWER PLATFORM ARCHITECTURE // ONLINE // SYSTEM_READY")
        
        painter.setPen(QPen(QColor(0, 240, 255, 45), 1))
        painter.drawLine(50, 60, 50, h - 100)
        painter.drawLine(50, h - 100, w - 50, h - 100)
        
        graph_sx, graph_sy = w - 420, h - 180
        painter.setPen(QPen(QColor(0, 240, 255, 35), 1))
        for gi in range(4):
            painter.drawLine(graph_sx, graph_sy + (gi * 20), graph_sx + 360, graph_sy + (gi * 20))
            
        painter.setPen(QPen(QColor(0, 255, 160, 220), 1.5))
        prev_x, prev_y = graph_sx, graph_sy + 30
        for gx in range(0, 360, 4):
            gy = graph_sy + 30 + int(math.sin(gx * 0.07 + self.wave_phase) * 16 * math.cos(gx * 0.03))
            painter.drawLine(prev_x, prev_y, graph_sx + gx, gy)
            prev_x, prev_y = graph_sx + gx, gy
            
        painter.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        painter.setPen(QColor(0, 240, 255, 140))
        painter.drawText(graph_sx, graph_sy - 12, "CORE HARMONIC BALANCER FEEDBACK")

        log_x = w - 300
        painter.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        painter.setPen(QColor(255, 255, 255, 190))
        painter.drawText(log_x, 100, "SYSTEM DIAGNOSTICS:")
        
        logs = [
            ("NODE_DELTA_LOCK", "SUCCESS"),
            ("BUS_BANDWIDTH", "MAXIMAL"),
            ("VOLTAGE_REG", f"{self.metrics['VOLTAGE']:.3f}V"),
            ("SECTOR_ARRAY", "CLEAR"),
            ("SUBSYS_SYNC", "STABLE")
        ]
        
        ly = 135
        for l_title, l_stat in logs:
            painter.setFont(QFont("Courier New", 9))
            painter.setPen(QColor(0, 240, 255, 140))
            painter.drawText(log_x, ly, l_title)
            painter.setPen(QColor(255, 255, 255, 220))
            painter.drawText(log_x + 150, ly, l_stat)
            ly += 30

if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = StarkExpoHUD()
    hud.show()
    
    hud.raise_()
    hud.activateWindow()
    
    sys.exit(app.exec())