import sys
import os
import cv2
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFrame,
                             QStackedWidget, QGridLayout, QDoubleSpinBox,
                             QFileDialog, QProgressBar, QMessageBox,
                             QSizePolicy, QSpinBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QMutex, QMutexLocker
from PyQt6.QtGui import QImage, QPixmap, QIcon, QPainter
from PyQt6 import QtCore
from PyQt6.QtSvg import QSvgRenderer

from robot_controller1 import RobotWorker
from vision_engine import VisionEngine

ICONS = {
    "manual":   """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M7 11V7M7 7V3M7 7H3M7 7H11M17 11V7M17 7V3M17 7H13M17 7H21M7 17V21M7 17H3M7 17H11M17 17V21M17 17H13M17 17H21" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
    "shapes":   """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M2 17L12 22L22 17" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M2 12L12 17L22 12" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
    "gcode":    """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M14 2V8H20" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M16 13H8" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M16 17H8" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M10 9H8" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
    "vision":   """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M1 12S5 4 12 4S23 12 23 12S19 20 12 20S1 12 1 12Z" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="12" r="3" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
    "stop":     """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" fill="#ff7b72" stroke="#ff7b72" stroke-width="2"/><rect x="8" y="8" width="8" height="8" fill="white"/></svg>""",
    "square":   """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="4" y="4" width="16" height="16" rx="2" stroke="#58a6ff" stroke-width="2"/></svg>""",
    "triangle": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 4L4 20H20L12 4Z" stroke="#58a6ff" stroke-width="2" stroke-linejoin="round"/></svg>""",
    "circle":   """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="8" stroke="#58a6ff" stroke-width="2"/></svg>""",
    "folder":   """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M22 19C22 19.5304 21.7893 20.0391 21.4142 20.4142C21.0391 20.7893 20.5304 21 20 21H4C3.46957 21 2.96086 20.7893 2.58579 20.4142C2.21071 20.0391 2 19.5304 2 19V5C2 4.46957 2.21071 3.96086 2.58579 3.58579C2.96086 3.21071 3.46957 3 4 3H9L11 5H20C20.5304 5 21.0391 5.21071 21.4142 5.58579C21.7893 5.96086 22 6.46957 22 7V19Z" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
    "play":     """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M5 3L19 12L5 21V3Z" fill="#ffffff"/></svg>""",
    "scan":     """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 7V5C3 3.89543 3.89543 3 5 3H7M17 3H19C20.1046 3 21 3.89543 21 5V7M21 17V19C21 20.1046 20.1046 21 19 21H17M7 21H5C3.89543 21 3 20.1046 3 19V17M8 12H16" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
    "home":     """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="9 22 9 12 15 12 15 22" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
}


def get_svg_icon(name, color="#8b949e"):
    svg_str = ICONS.get(name, "").replace("#8b949e", color)
    renderer = QSvgRenderer(svg_str.encode())
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


# =============================================================================
# HILO DE CÁMARA — captura y procesamiento sincronizados
# =============================================================================

class CameraThread(QThread):
    """
    Hilo de UI que consume frames ya sincronizados del VisionEngine.
    La camara y el procesamiento corren en el grabber interno del VisionEngine.
    Este hilo solo llama detect_shapes() a ~30fps para actualizar la UI,
    siempre usando el frame mas reciente.
    """

    change_pixmap_signal = pyqtSignal(np.ndarray)
    detection_signal     = pyqtSignal(dict)

    TARGET_MS = 33   # ~30 fps para la UI

    def __init__(self, engine: VisionEngine):
        super().__init__()
        self.engine = engine

    def run(self):
        while not self.isInterruptionRequested():
            t_start = cv2.getTickCount()

            # detect_shapes() sin argumento usa el frame mas reciente del grabber
            shapes, frame = self.engine.detect_shapes()
            if frame is not None:
                self.change_pixmap_signal.emit(frame)
                self.detection_signal.emit(shapes)

            t_elapsed_ms = (cv2.getTickCount() - t_start) / cv2.getTickFrequency() * 1000
            remaining_ms = int(self.TARGET_MS - t_elapsed_ms)
            if remaining_ms > 0:
                QThread.msleep(remaining_ms)


# =============================================================================
# VENTANA PRINCIPAL
# =============================================================================

class Lite6App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lite 6 Pro — Control Engine")
        self.setMinimumSize(1400, 900)

        self.ip_address = "172.23.254.151"

        self.detected_shapes: dict = {}
        self.current_shapes:  dict = {}
        self._scanning = False

        qss_path = os.path.join(os.path.dirname(__file__), "styles.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.robot_thread = QThread()
        self.worker = RobotWorker(self.ip_address)
        self.worker.moveToThread(self.robot_thread)
        self.robot_thread.start()

        self.init_sidebar()
        self.init_content_area()

        self.worker.status_updated.connect(self.update_conn_status)
        self.worker.pos_updated.connect(self.update_telemetry)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished.connect(self._on_worker_finished)

        self.switch_page(0)

    # =========================================================================
    # SIDEBAR
    # =========================================================================

    def init_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(280)

        sl = QVBoxLayout(self.sidebar)
        sl.setContentsMargins(24, 32, 24, 24)
        sl.setSpacing(8)

        t = QLabel("LITE 6 PRO")
        t.setObjectName("BrandTitle")
        sl.addWidget(t)
        s = QLabel("ROBOTICS INTELLIGENCE")
        s.setObjectName("BrandSubtitle")
        sl.addWidget(s)
        sl.addSpacing(36)

        nav = QLabel("NAVIGATION")
        nav.setObjectName("SidebarSection")
        sl.addWidget(nav)
        sl.addSpacing(6)

        self.btn_manual = self.create_nav_btn("Manual Control",   0, "manual")
        self.btn_shapes = self.create_nav_btn("Geometric Shapes", 1, "shapes")
        self.btn_gcode  = self.create_nav_btn("G-Code Engine",    2, "gcode")
        self.btn_vision = self.create_nav_btn("Computer Vision",  3, "vision")
        for btn in [self.btn_manual, self.btn_shapes, self.btn_gcode, self.btn_vision]:
            sl.addWidget(btn)

        sl.addStretch()

        sys_lbl = QLabel("SYSTEM")
        sys_lbl.setObjectName("SidebarSection")
        sl.addWidget(sys_lbl)
        sl.addSpacing(6)

        self.conn_label = QLabel("● DISCONNECTED")
        self.conn_label.setObjectName("StatusLabel")
        self.conn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sl.addWidget(self.conn_label)
        sl.addSpacing(8)

        self.btn_connect = QPushButton("CONNECT ROBOT")
        self.btn_connect.setObjectName("ConnectBtn")
        self.btn_connect.clicked.connect(self.connect_robot)
        sl.addWidget(self.btn_connect)

        self.btn_estop = QPushButton("  EMERGENCY STOP")
        self.btn_estop.setIcon(get_svg_icon("stop"))
        self.btn_estop.setObjectName("EmergencyStop")
        self.btn_estop.clicked.connect(self.emergency_stop)
        sl.addWidget(self.btn_estop)

        self.main_layout.addWidget(self.sidebar)

    def create_nav_btn(self, text, index, icon_name):
        btn = QPushButton(f"  {text}")
        btn.setIcon(get_svg_icon(icon_name))
        btn.setIconSize(QtCore.QSize(20, 20))
        btn.setObjectName("NavButton")
        btn.setCheckable(True)
        btn.setMinimumHeight(50)
        btn.clicked.connect(lambda: self.switch_page(index))
        return btn

    def switch_page(self, index):
        self.content_stack.setCurrentIndex(index)
        buttons    = [self.btn_manual, self.btn_shapes, self.btn_gcode, self.btn_vision]
        icon_names = ["manual", "shapes", "gcode", "vision"]
        for i, b in enumerate(buttons):
            active = (i == index)
            b.setChecked(active)
            b.setIcon(get_svg_icon(icon_names[i], "#ffffff" if active else "#8b949e"))

    # =========================================================================
    # ÁREA DE CONTENIDO
    # =========================================================================

    def init_content_area(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.telemetry_bar = QFrame()
        self.telemetry_bar.setObjectName("TelemetryBar")
        self.telemetry_bar.setFixedHeight(80)
        tl = QHBoxLayout(self.telemetry_bar)
        tl.setContentsMargins(40, 0, 40, 0)
        tl.setSpacing(40)

        self.w_x,     self.lbl_x     = self.create_stat_widget("X-AXIS",      "0.00 mm")
        self.w_y,     self.lbl_y     = self.create_stat_widget("Y-AXIS",      "0.00 mm")
        self.w_z,     self.lbl_z     = self.create_stat_widget("Z-AXIS",      "0.00 mm")
        self.w_state, self.lbl_state = self.create_stat_widget("ROBOT STATE", "IDLE")

        for w in [self.w_x, self.w_y, self.w_z]:
            tl.addWidget(w)
        tl.addStretch()
        tl.addWidget(self.w_state)
        layout.addWidget(self.telemetry_bar)

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.create_manual_page())
        self.content_stack.addWidget(self.create_shapes_page())
        self.content_stack.addWidget(self.create_gcode_page())
        self.content_stack.addWidget(self.create_vision_page())
        layout.addWidget(self.content_stack)

        self.main_layout.addWidget(container, 1)

    def create_stat_widget(self, label, value):
        w    = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setSpacing(2)
        vbox.setContentsMargins(0, 0, 0, 0)
        l = QLabel(label)
        l.setStyleSheet("color:#484f58;font-size:10px;font-weight:800;letter-spacing:1px;")
        vbox.addWidget(l)
        val = QLabel(value)
        val.setStyleSheet("color:#ffffff;font-size:18px;font-weight:700;font-family:'JetBrains Mono',monospace;")
        vbox.addWidget(val)
        return w, val

    def page_header(self, title, subtitle):
        header = QVBoxLayout()
        header.setSpacing(4)
        t = QLabel(title)
        t.setObjectName("PageTitle")
        header.addWidget(t)
        s = QLabel(subtitle)
        s.setObjectName("PageSubtitle")
        header.addWidget(s)
        sep = QFrame()
        sep.setObjectName("Separator")
        header.addWidget(sep)
        return header

    def make_page_wrapper(self):
        page  = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(48, 40, 48, 40)
        outer.setSpacing(24)
        return page, outer

    # ── Manual ────────────────────────────────────────────────────────────────

    def create_manual_page(self):
        page, layout = self.make_page_wrapper()
        layout.addLayout(self.page_header("Manual Manipulation", "Direct Cartesian positioning"))
        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(32, 28, 32, 28)
        grid = QGridLayout()
        self.spn_x = self._make_spinbox(-500, 500)
        self.spn_y = self._make_spinbox(-500, 500)
        self.spn_z = self._make_spinbox(50, 450)
        grid.addWidget(self._field_label("X Position"), 0, 0)
        grid.addWidget(self.spn_x, 0, 1)
        grid.addWidget(self._field_label("Y Position"), 1, 0)
        grid.addWidget(self.spn_y, 1, 1)
        grid.addWidget(self._field_label("Z Position"), 2, 0)
        grid.addWidget(self.spn_z, 2, 1)
        cl.addLayout(grid)
        btn_move = QPushButton("  Execute Movement")
        btn_move.setIcon(get_svg_icon("play", "#ffffff"))
        btn_move.setObjectName("PrimaryAction")
        btn_move.setMinimumHeight(52)
        btn_move.clicked.connect(
            lambda: self.worker.move_to(self.spn_x.value(), self.spn_y.value(), self.spn_z.value())
        )
        cl.addWidget(btn_move)
        btn_home = QPushButton("  Go Home")
        btn_home.setIcon(get_svg_icon("home", "#ffffff"))
        btn_home.setObjectName("PrimaryAction")
        btn_home.setMinimumHeight(52)
        btn_home.clicked.connect(self.worker.go_home)
        cl.addWidget(btn_home)
        layout.addWidget(card)
        layout.addStretch()
        return page

    # ── Shapes ────────────────────────────────────────────────────────────────

    def create_shapes_page(self):
        page, layout = self.make_page_wrapper()
        layout.addLayout(self.page_header("Geometric Synthesis", "Preset trajectories — regresa a HOME al terminar"))
        cards_layout = QHBoxLayout()
        for name, icon_key, func in [
            ("SQUARE",   "square",   self.worker.draw_square),
            ("TRIANGLE", "triangle", self.worker.draw_triangle),
            ("CIRCLE",   "circle",   self.worker.draw_circle),
        ]:
            card = QFrame()
            card.setObjectName("ShapeCard")
            vbox = QVBoxLayout(card)
            vbox.setContentsMargins(28, 32, 28, 28)
            icon_lbl = QLabel()
            icon_lbl.setPixmap(get_svg_icon(icon_key, "#58a6ff").pixmap(64, 64))
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(icon_lbl)
            title = QLabel(name)
            title.setObjectName("ShapeTitle")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(title)
            btn = QPushButton(f"Draw {name.title()}")
            btn.setObjectName("PrimaryAction")
            btn.setMinimumHeight(46)
            btn.clicked.connect(func)
            vbox.addWidget(btn)
            cards_layout.addWidget(card)
        layout.addLayout(cards_layout)
        layout.addStretch()
        return page

    # ── G-Code ────────────────────────────────────────────────────────────────

    def create_gcode_page(self):
        page, layout = self.make_page_wrapper()
        layout.addLayout(self.page_header("G-Code Processing Hub", "Load and execute G-Code files"))
        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout(card)
        self.btn_load_gcode = QPushButton("  Select G-Code File")
        self.btn_load_gcode.setIcon(get_svg_icon("folder", "#c9d1d9"))
        self.btn_load_gcode.setMinimumHeight(52)
        self.btn_load_gcode.clicked.connect(self.load_gcode_file)
        cl.addWidget(self.btn_load_gcode)
        self.gcode_progress = QProgressBar()
        cl.addWidget(self.gcode_progress)
        self.btn_run_gcode = QPushButton("  Run Sequence")
        self.btn_run_gcode.setIcon(get_svg_icon("play", "#ffffff"))
        self.btn_run_gcode.setObjectName("PrimaryAction")
        self.btn_run_gcode.setMinimumHeight(52)
        self.btn_run_gcode.clicked.connect(self.run_gcode)
        cl.addWidget(self.btn_run_gcode)
        layout.addWidget(card)
        layout.addStretch()
        return page

    # ── Vision ────────────────────────────────────────────────────────────────

    def create_vision_page(self):
        page, layout = self.make_page_wrapper()
        layout.addLayout(self.page_header(
            "Computer Vision Engine",
            "C920 forward-facing — sincronizado — validación con bajada"
        ))

        container = QHBoxLayout()

        cam_card = QFrame()
        cam_card.setObjectName("Card")
        cam_layout = QVBoxLayout(cam_card)
        self.cam_view = QLabel("Conectando a la cámara…")
        self.cam_view.setMinimumSize(720, 520)
        self.cam_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cam_layout.addWidget(self.cam_view)
        self.lbl_scan_overlay = QLabel("")
        self.lbl_scan_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_scan_overlay.setStyleSheet(
            "color:#58a6ff;font-size:22px;font-weight:700;background:transparent;"
        )
        cam_layout.addWidget(self.lbl_scan_overlay)
        container.addWidget(cam_card, 3)

        ctrl_card = QFrame()
        ctrl_card.setObjectName("Card")
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_layout.setSpacing(10)

        det_label = QLabel("DETECTED")
        det_label.setStyleSheet("color:#484f58;font-size:10px;font-weight:800;letter-spacing:1px;")
        ctrl_layout.addWidget(det_label)

        self.lbl_det_triangle = QLabel("▲ Triangle  —")
        self.lbl_det_square   = QLabel("■ Square    —")
        self.lbl_det_circle   = QLabel("● Circle    —")
        for lbl in [self.lbl_det_triangle, self.lbl_det_square, self.lbl_det_circle]:
            lbl.setStyleSheet("color:#8b949e;font-size:11px;font-family:monospace;")
            ctrl_layout.addWidget(lbl)

        ctrl_layout.addSpacing(10)

        cal_label = QLabel("CALIBRACIÓN")
        cal_label.setStyleSheet("color:#484f58;font-size:10px;font-weight:800;letter-spacing:1px;")
        ctrl_layout.addWidget(cal_label)

        info = QLabel("C920 @ 0.496 mm/px (calculado)")
        info.setStyleSheet("color:#3fb950;font-size:10px;font-family:monospace;")
        ctrl_layout.addWidget(info)

        row_ocy = QHBoxLayout()
        row_ocy.addWidget(QLabel("Cruz abajo:"))
        self.spn_offset_cy = QSpinBox()
        self.spn_offset_cy.setRange(-240, 240)
        self.spn_offset_cy.setSingleStep(5)
        self.spn_offset_cy.setValue(60)
        self.spn_offset_cy.setSuffix(" px")
        self.spn_offset_cy.valueChanged.connect(self._apply_calibration)
        row_ocy.addWidget(self.spn_offset_cy)
        ctrl_layout.addLayout(row_ocy)

        row_ocx = QHBoxLayout()
        row_ocx.addWidget(QLabel("Cruz lateral:"))
        self.spn_offset_cx = QSpinBox()
        self.spn_offset_cx.setRange(-320, 320)
        self.spn_offset_cx.setSingleStep(5)
        self.spn_offset_cx.setValue(0)
        self.spn_offset_cx.setSuffix(" px")
        self.spn_offset_cx.valueChanged.connect(self._apply_calibration)
        row_ocx.addWidget(self.spn_offset_cx)
        ctrl_layout.addLayout(row_ocx)

        row_xp = QHBoxLayout()
        row_xp.addWidget(QLabel("X apuntado:"))
        self.spn_x_point = QDoubleSpinBox()
        self.spn_x_point.setRange(100, 500)
        self.spn_x_point.setDecimals(0)
        self.spn_x_point.setSingleStep(10)
        self.spn_x_point.setValue(200)
        self.spn_x_point.setSuffix(" mm")
        self.spn_x_point.valueChanged.connect(self._apply_calibration)
        row_xp.addWidget(self.spn_x_point)
        ctrl_layout.addLayout(row_xp)

        row_zp = QHBoxLayout()
        row_zp.addWidget(QLabel("Z apuntado:"))
        self.spn_z_point = QDoubleSpinBox()
        self.spn_z_point.setRange(50, 450)
        self.spn_z_point.setDecimals(0)
        self.spn_z_point.setSingleStep(5)
        self.spn_z_point.setValue(163)
        self.spn_z_point.setSuffix(" mm")
        self.spn_z_point.valueChanged.connect(self._apply_calibration)
        row_zp.addWidget(self.spn_z_point)
        ctrl_layout.addLayout(row_zp)

        # ── Bajada de validación ──────────────────────────────────────────────
        row_vdrop = QHBoxLayout()
        row_vdrop.addWidget(QLabel("Bajada validar:"))
        self.spn_validate_drop = QDoubleSpinBox()
        self.spn_validate_drop.setRange(5, 80)
        self.spn_validate_drop.setDecimals(0)
        self.spn_validate_drop.setSingleStep(5)
        self.spn_validate_drop.setValue(20)
        self.spn_validate_drop.setSuffix(" mm")
        self.spn_validate_drop.setToolTip(
            "Cuántos mm baja el brazo al validar cada figura.\n"
            "20mm es un movimiento visible pero seguro."
        )
        self.spn_validate_drop.valueChanged.connect(self._apply_calibration)
        row_vdrop.addWidget(self.spn_validate_drop)
        ctrl_layout.addLayout(row_vdrop)

        ctrl_layout.addSpacing(12)

        self.btn_detect_seq = QPushButton("  Scan & Execute")
        self.btn_detect_seq.setIcon(get_svg_icon("scan", "#ffffff"))
        self.btn_detect_seq.setObjectName("PrimaryAction")
        self.btn_detect_seq.setMinimumHeight(52)
        self.btn_detect_seq.clicked.connect(self.start_scan_then_execute)
        ctrl_layout.addWidget(self.btn_detect_seq)

        self.lbl_scan_countdown = QLabel("")
        self.lbl_scan_countdown.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_scan_countdown.setStyleSheet("color:#58a6ff;font-size:13px;font-weight:700;")
        ctrl_layout.addWidget(self.lbl_scan_countdown)

        ctrl_layout.addStretch()
        container.addWidget(ctrl_card, 1)
        layout.addLayout(container)

        # VisionEngine abre la camara automaticamente (autodeteccion)
        # y arranca el grabber interno sincronizado
        try:
            self.vision_engine = VisionEngine(
                camera_index=None,    # autodetecta índice 0-10
                offset_cx=self.spn_offset_cx.value(),
                offset_cy=self.spn_offset_cy.value()
            )
        except RuntimeError as e:
            QMessageBox.critical(self, "Error de camara", str(e))
            return

        # CameraThread solo consume frames del grabber — no abre la camara
        self.cam_thread = CameraThread(self.vision_engine)
        self.cam_thread.change_pixmap_signal.connect(self.update_image)
        self.cam_thread.detection_signal.connect(self.handle_detections)
        self.cam_thread.start()

        return page

    # =========================================================================
    # CALIBRACIÓN EN VIVO
    # =========================================================================

    def _apply_calibration(self):
        if hasattr(self, "vision_engine"):
            self.vision_engine.offset_cx = self.spn_offset_cx.value()
            self.vision_engine.offset_cy = self.spn_offset_cy.value()
        self.worker.X_POINT          = self.spn_x_point.value()
        self.worker.Z_POINT          = self.spn_z_point.value()
        self.worker.Z_VALIDATE_DROP  = self.spn_validate_drop.value()

    # =========================================================================
    # LÓGICA DE VISIÓN
    # =========================================================================

    def handle_detections(self, shapes: dict):
        for key, value in shapes.items():
            if value is not None:
                self.detected_shapes[key] = value
        self.current_shapes = dict(self.detected_shapes)

        def fmt(name, lbl, symbol):
            v = self.current_shapes.get(name)
            if v:
                lbl.setText(f"{symbol}  Y{v[0]:+.0f} Z{v[1]:+.0f}mm")
                lbl.setStyleSheet("color:#3fb950;font-size:11px;font-family:monospace;")
            else:
                lbl.setText(f"{symbol}  —")
                lbl.setStyleSheet("color:#8b949e;font-size:11px;font-family:monospace;")

        fmt("triangle", self.lbl_det_triangle, "▲ Triangle")
        fmt("square",   self.lbl_det_square,   "■ Square  ")
        fmt("circle",   self.lbl_det_circle,   "● Circle  ")

    def update_image(self, cv_img):
        self.cam_view.setPixmap(self.convert_cv_qt(cv_img))

    def start_scan_then_execute(self):
        if not self.worker.is_connected:
            self.show_error("Conecta el robot primero.")
            return
        if self._scanning:
            return

        SCAN_SECONDS = 4

        self.detected_shapes = {}
        self.current_shapes  = {}
        self._scanning       = True
        self._scan_remaining = SCAN_SECONDS

        self.btn_detect_seq.setEnabled(False)
        txt = f"Escaneando… {SCAN_SECONDS}s"
        self.lbl_scan_countdown.setText(txt)
        self.lbl_scan_overlay.setText(f"◉ {txt}")

        for lbl in [self.lbl_det_triangle, self.lbl_det_square, self.lbl_det_circle]:
            lbl.setText("—")
            lbl.setStyleSheet("color:#8b949e;font-size:11px;font-family:monospace;")

        self._scan_timer = QTimer()
        self._scan_timer.setInterval(1000)
        self._scan_timer.timeout.connect(self._scan_tick)
        self._scan_timer.start()

    def _scan_tick(self):
        self._scan_remaining -= 1
        if self._scan_remaining > 0:
            txt = f"Escaneando… {self._scan_remaining}s"
            self.lbl_scan_countdown.setText(txt)
            self.lbl_scan_overlay.setText(f"◉ {txt}")
        else:
            self._scan_timer.stop()
            self._scanning = False
            self.lbl_scan_countdown.setText("")
            self.lbl_scan_overlay.setText("")
            self.btn_detect_seq.setEnabled(True)
            self._execute_vision_sequence()

    def _execute_vision_sequence(self):
        required = ["triangle", "square", "circle"]
        missing  = [s for s in required if s not in self.current_shapes]
        if missing:
            self.show_error(
                f"No se detectaron: {', '.join(missing)}.\n"
                "Asegúrate de que las figuras estén visibles y vuelve a escanear."
            )
            return
        self.lbl_state.setText("VISION SEQ")
        self.worker.run_vision_sequence(dict(self.current_shapes))

    def _on_worker_finished(self):
        self.lbl_state.setText("IDLE")

    # =========================================================================
    # EMERGENCY STOP
    # =========================================================================

    def emergency_stop(self):
        try:
            if self.worker.arm and self.worker.is_connected:
                self.worker.arm.emergency_stop()
        except Exception as e:
            print(f"[E-STOP] {e}")
        if hasattr(self, "cam_thread") and self.cam_thread.isRunning():
            self.cam_thread.requestInterruption()
        self.lbl_state.setText("E-STOP")
        self.conn_label.setText("● E-STOP")
        self.worker.is_connected = False
        QMessageBox.warning(self, "Emergency Stop", "Robot detenido. Reconecta para continuar.")

    # =========================================================================
    # SLOTS AUXILIARES
    # =========================================================================

    def convert_cv_qt(self, cv_img):
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        q_img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(q_img.scaled(720, 520, Qt.AspectRatioMode.KeepAspectRatio))

    def load_gcode_file(self):
        self.gcode_file, _ = QFileDialog.getOpenFileName(
            self, "Open G-Code", "", "G-Code Files (*.ngc *.gcode *.txt)"
        )
        if self.gcode_file:
            self.btn_load_gcode.setText(f"  Loaded: {os.path.basename(self.gcode_file)}")

    def run_gcode(self):
        if hasattr(self, "gcode_file"):
            self.worker.run_gcode(self.gcode_file)

    def _make_spinbox(self, minv, maxv):
        s = QDoubleSpinBox()
        s.setRange(minv, maxv)
        s.setDecimals(2)
        s.setMinimumHeight(44)
        return s

    def _field_label(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("FieldLabel")
        return lbl

    def connect_robot(self):
        self.btn_connect.setEnabled(False)
        self.conn_label.setText("● CONNECTING…")
        QTimer.singleShot(100, self.worker.connect)

    def update_conn_status(self, status: str):
        self.lbl_state.setText(status)
        if status == "CONNECTED":
            self.conn_label.setText("● CONNECTED")
            self.btn_connect.setHidden(True)
        else:
            self.btn_connect.setEnabled(True)

    def update_progress(self, value: int):
        self.gcode_progress.setValue(value)

    def update_telemetry(self, pos: list):
        self.lbl_x.setText(f"{pos[0]:.2f} mm")
        self.lbl_y.setText(f"{pos[1]:.2f} mm")
        self.lbl_z.setText(f"{pos[2]:.2f} mm")

    def show_error(self, message: str):
        QMessageBox.critical(self, "System Error", message)
        self.btn_connect.setEnabled(True)


    def closeEvent(self, event):
        """Libera la camara al cerrar la ventana."""
        if hasattr(self, 'cam_thread') and self.cam_thread.isRunning():
            self.cam_thread.requestInterruption()
            self.cam_thread.wait(1000)
        if hasattr(self, 'vision_engine'):
            self.vision_engine.release()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Lite6App()
    window.show()
    sys.exit(app.exec())