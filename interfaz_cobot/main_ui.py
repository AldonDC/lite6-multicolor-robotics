import sys
import os
import cv2
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFrame,
                             QStackedWidget, QGridLayout, QDoubleSpinBox,
                             QFileDialog, QProgressBar, QMessageBox,
                             QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QImage, QPixmap, QIcon, QPainter
from PyQt6 import QtCore
from PyQt6.QtSvg import QSvgRenderer

from robot_controller import RobotWorker
from vision_engine import VisionEngine

# --- EMBEDDED HIGH-TECH SVG ICONS ---
ICONS = {
    "manual": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M7 11V7M7 7V3M7 7H3M7 7H11M17 11V7M17 7V3M17 7H13M17 7H21M7 17V21M7 17H3M7 17H11M17 17V21M17 17H13M17 17H21" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
    "shapes": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M2 17L12 22L22 17" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M2 12L12 17L22 12" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
    "gcode": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M14 2V8H20" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M16 13H8" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M16 17H8" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M10 9H8" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
    "vision": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M1 12S5 4 12 4S23 12 23 12S19 20 12 20S1 12 1 12Z" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="12" r="3" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
    "connect": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M18.15 15.65L14.65 19.15M13.65 16.65L10.15 20.15M7.15 17.15L3.65 13.65M6.65 11.65L3.15 8.15M11.65 6.65L8.15 3.15M17.15 3.65L13.65 7.15M16.65 13.65L20.15 10.15M19.15 14.65L22.65 11.15" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
    "stop": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" fill="#ff7b72" stroke="#ff7b72" stroke-width="2"/><rect x="8" y="8" width="8" height="8" fill="white"/></svg>""",
    "square": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="4" y="4" width="16" height="16" rx="2" stroke="#58a6ff" stroke-width="2"/></svg>""",
    "triangle": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 4L4 20H20L12 4Z" stroke="#58a6ff" stroke-width="2" stroke-linejoin="round"/></svg>""",
    "circle": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="8" stroke="#58a6ff" stroke-width="2"/></svg>""",
    "folder": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M22 19C22 19.5304 21.7893 20.0391 21.4142 20.4142C21.0391 20.7893 20.5304 21 20 21H4C3.46957 21 2.96086 20.7893 2.58579 20.4142C2.21071 20.0391 2 19.5304 2 19V5C2 4.46957 2.21071 3.96086 2.58579 3.58579C2.96086 3.21071 3.46957 3 4 3H9L11 5H20C20.5304 5 21.0391 5.21071 21.4142 5.58579C21.7893 5.96086 22 6.46957 22 7V19Z" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
    "play": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M5 3L19 12L5 21V3Z" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="#ffffff"/></svg>""",
    "check": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M20 6L9 17L4 12" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
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


class CameraThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    detection_signal = pyqtSignal(dict)

    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    def run(self):
        cap = cv2.VideoCapture(0)
        while not self.isInterruptionRequested():
            ret, cv_img = cap.read()
            if ret:
                shapes, frame = self.engine.detect_shapes(cv_img)
                self.change_pixmap_signal.emit(frame)
                self.detection_signal.emit(shapes)
            QThread.msleep(30)
        cap.release()


class Lite6App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lite 6 Pro — Control Engine")
        self.setMinimumSize(1400, 900)

        self.ip_address = "192.168.1.164"

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

        self.switch_page(0)

    # ========================================================
    # SIDEBAR
    # ========================================================
    def init_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(280)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(24, 32, 24, 24)
        sidebar_layout.setSpacing(8)

        # Brand
        app_title = QLabel("LITE 6 PRO")
        app_title.setObjectName("BrandTitle")
        sidebar_layout.addWidget(app_title)

        subtitle = QLabel("ROBOTICS INTELLIGENCE")
        subtitle.setObjectName("BrandSubtitle")
        sidebar_layout.addWidget(subtitle)

        sidebar_layout.addSpacing(36)

        # Navigation section
        nav_label = QLabel("NAVIGATION")
        nav_label.setObjectName("SidebarSection")
        sidebar_layout.addWidget(nav_label)
        sidebar_layout.addSpacing(6)

        self.btn_manual = self.create_nav_btn("Manual Control", 0, "manual")
        self.btn_shapes = self.create_nav_btn("Geometric Shapes", 1, "shapes")
        self.btn_gcode = self.create_nav_btn("G-Code Engine", 2, "gcode")
        self.btn_vision = self.create_nav_btn("Computer Vision", 3, "vision")

        sidebar_layout.addWidget(self.btn_manual)
        sidebar_layout.addWidget(self.btn_shapes)
        sidebar_layout.addWidget(self.btn_gcode)
        sidebar_layout.addWidget(self.btn_vision)

        sidebar_layout.addStretch()

        # System status section
        sys_label = QLabel("SYSTEM")
        sys_label.setObjectName("SidebarSection")
        sidebar_layout.addWidget(sys_label)
        sidebar_layout.addSpacing(6)

        self.conn_label = QLabel("● DISCONNECTED")
        self.conn_label.setObjectName("StatusLabel")
        self.conn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(self.conn_label)
        sidebar_layout.addSpacing(8)

        self.btn_connect = QPushButton("CONNECT ROBOT")
        self.btn_connect.setObjectName("ConnectBtn")
        self.btn_connect.clicked.connect(self.connect_robot)
        sidebar_layout.addWidget(self.btn_connect)

        self.btn_estop = QPushButton("  EMERGENCY STOP")
        self.btn_estop.setIcon(get_svg_icon("stop"))
        self.btn_estop.setObjectName("EmergencyStop")
        sidebar_layout.addWidget(self.btn_estop)

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
        buttons = [self.btn_manual, self.btn_shapes, self.btn_gcode, self.btn_vision]
        icon_names = ["manual", "shapes", "gcode", "vision"]
        for i, b in enumerate(buttons):
            is_active = (i == index)
            b.setChecked(is_active)
            # Update icon color on active
            color = "#ffffff" if is_active else "#8b949e"
            b.setIcon(get_svg_icon(icon_names[i], color))

    # ========================================================
    # CONTENT
    # ========================================================
    def init_content_area(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Telemetry Bar
        self.telemetry_bar = QFrame()
        self.telemetry_bar.setObjectName("TelemetryBar")
        self.telemetry_bar.setFixedHeight(80)
        self.telemetry_bar.setStyleSheet("""
            QFrame#TelemetryBar {
                background-color: #0d1117;
                border-bottom: 1px solid #21262d;
            }
        """)
        t_layout = QHBoxLayout(self.telemetry_bar)
        t_layout.setContentsMargins(40, 0, 40, 0)
        t_layout.setSpacing(40)

        self.w_x, self.lbl_x = self.create_stat_widget("X-AXIS", "0.00 mm")
        self.w_y, self.lbl_y = self.create_stat_widget("Y-AXIS", "0.00 mm")
        self.w_z, self.lbl_z = self.create_stat_widget("Z-AXIS", "0.00 mm")
        self.w_state, self.lbl_state = self.create_stat_widget("ROBOT STATE", "IDLE")

        t_layout.addWidget(self.w_x)
        t_layout.addWidget(self.w_y)
        t_layout.addWidget(self.w_z)
        t_layout.addStretch()
        t_layout.addWidget(self.w_state)

        layout.addWidget(self.telemetry_bar)

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.create_manual_page())
        self.content_stack.addWidget(self.create_shapes_page())
        self.content_stack.addWidget(self.create_gcode_page())
        self.content_stack.addWidget(self.create_vision_page())
        layout.addWidget(self.content_stack)

        self.main_layout.addWidget(container, 1)

    def create_stat_widget(self, label, value):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        vbox = QVBoxLayout(w)
        vbox.setSpacing(2)
        vbox.setContentsMargins(0, 0, 0, 0)

        l = QLabel(label)
        l.setStyleSheet("background: transparent; color: #484f58; font-size: 10px; font-weight: 800; letter-spacing: 1px;")
        vbox.addWidget(l)

        val = QLabel(value)
        val.setStyleSheet("background: transparent; color: #ffffff; font-size: 18px; font-weight: 700; font-family: 'JetBrains Mono', monospace;")
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
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(48, 40, 48, 40)
        outer.setSpacing(24)
        return page, outer

    # --------- Manual Page ---------
    def create_manual_page(self):
        page, layout = self.make_page_wrapper()
        layout.addLayout(self.page_header(
            "Manual Manipulation",
            "Direct Cartesian positioning — send the end-effector to absolute coordinates"
        ))

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(20)

        section = QLabel("Target Coordinates (mm)")
        section.setObjectName("SectionTitle")
        card_layout.addWidget(section)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(18)
        grid.setColumnStretch(1, 1)

        self.spn_x = self._make_spinbox(-500, 500)
        self.spn_y = self._make_spinbox(-500, 500)
        self.spn_z = self._make_spinbox(0, 300)

        grid.addWidget(self._field_label("X Position"), 0, 0)
        grid.addWidget(self.spn_x, 0, 1)
        grid.addWidget(self._field_label("Y Position"), 1, 0)
        grid.addWidget(self.spn_y, 1, 1)
        grid.addWidget(self._field_label("Z Position"), 2, 0)
        grid.addWidget(self.spn_z, 2, 1)

        card_layout.addLayout(grid)
        card_layout.addSpacing(8)

        btn_move = QPushButton("  Execute Movement")
        btn_move.setIcon(get_svg_icon("play", "#ffffff"))
        btn_move.setIconSize(QtCore.QSize(18, 18))
        btn_move.setObjectName("PrimaryAction")
        btn_move.setMinimumHeight(52)
        btn_move.clicked.connect(
            lambda: self.worker.move_to(self.spn_x.value(), self.spn_y.value(), self.spn_z.value())
        )
        card_layout.addWidget(btn_move)

        layout.addWidget(card)
        layout.addStretch()
        return page

    def _make_spinbox(self, minv, maxv):
        s = QDoubleSpinBox()
        s.setRange(minv, maxv)
        s.setDecimals(2)
        s.setSingleStep(1.0)
        s.setMinimumHeight(44)
        s.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return s

    def _field_label(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("FieldLabel")
        lbl.setMinimumWidth(140)
        return lbl

    # --------- Shapes Page ---------
    def create_shapes_page(self):
        page, layout = self.make_page_wrapper()
        layout.addLayout(self.page_header(
            "Geometric Synthesis",
            "Preset trajectories — 5cm scale shapes drawn in the XY plane"
        ))

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        shapes_data = [
            ("SQUARE", "square", "4 linear segments", self.worker.draw_square),
            ("TRIANGLE", "triangle", "3 linear segments", self.worker.draw_triangle),
            ("CIRCLE", "circle", "Smooth arc trajectory", self.worker.draw_circle),
        ]

        for name, icon_key, hint, func in shapes_data:
            card = QFrame()
            card.setObjectName("ShapeCard")
            vbox = QVBoxLayout(card)
            vbox.setContentsMargins(28, 32, 28, 28)
            vbox.setSpacing(14)
            vbox.setAlignment(Qt.AlignmentFlag.AlignTop)

            icon_pix = get_svg_icon(icon_key, "#58a6ff").pixmap(64, 64)
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon_pix)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setStyleSheet("padding: 12px 0;")
            vbox.addWidget(icon_lbl)

            title = QLabel(name)
            title.setObjectName("ShapeTitle")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(title)

            hint_lbl = QLabel(hint)
            hint_lbl.setObjectName("ShapeHint")
            hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(hint_lbl)

            vbox.addSpacing(8)

            btn = QPushButton(f"Draw {name.title()}")
            btn.setObjectName("PrimaryAction")
            btn.setMinimumHeight(46)
            btn.clicked.connect(func)
            vbox.addWidget(btn)

            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)
        layout.addStretch()
        return page

    # --------- G-Code Page ---------
    def create_gcode_page(self):
        page, layout = self.make_page_wrapper()
        layout.addLayout(self.page_header(
            "G-Code Processing Hub",
            "Load and execute G-Code files — real-time progress feedback"
        ))

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(20)

        section = QLabel("File Selection")
        section.setObjectName("SectionTitle")
        card_layout.addWidget(section)

        self.btn_load_gcode = QPushButton("  Select G-Code File")
        self.btn_load_gcode.setIcon(get_svg_icon("folder", "#c9d1d9"))
        self.btn_load_gcode.setIconSize(QtCore.QSize(20, 20))
        self.btn_load_gcode.setMinimumHeight(52)
        self.btn_load_gcode.clicked.connect(self.load_gcode_file)
        card_layout.addWidget(self.btn_load_gcode)

        card_layout.addSpacing(8)

        prog_section = QLabel("Execution Progress")
        prog_section.setObjectName("SectionTitle")
        card_layout.addWidget(prog_section)

        self.gcode_progress = QProgressBar()
        self.gcode_progress.setMinimumHeight(28)
        card_layout.addWidget(self.gcode_progress)

        card_layout.addSpacing(8)

        self.btn_run_gcode = QPushButton("  Run Sequence")
        self.btn_run_gcode.setIcon(get_svg_icon("play", "#ffffff"))
        self.btn_run_gcode.setIconSize(QtCore.QSize(18, 18))
        self.btn_run_gcode.setObjectName("PrimaryAction")
        self.btn_run_gcode.setMinimumHeight(52)
        self.btn_run_gcode.clicked.connect(self.run_gcode)
        card_layout.addWidget(self.btn_run_gcode)

        layout.addWidget(card)
        layout.addStretch()
        return page

    def load_gcode_file(self):
        self.gcode_file, _ = QFileDialog.getOpenFileName(
            self, "Open G-Code", "", "G-Code Files (*.ngc *.gcode *.txt)"
        )
        if self.gcode_file:
            self.btn_load_gcode.setText(f"  Loaded: {os.path.basename(self.gcode_file)}")
            self.btn_load_gcode.setIcon(get_svg_icon("check", "#3fb950"))

    def run_gcode(self):
        if hasattr(self, 'gcode_file'):
            self.worker.run_gcode(self.gcode_file)

    # --------- Vision Page ---------
    def create_vision_page(self):
        page, layout = self.make_page_wrapper()
        layout.addLayout(self.page_header(
            "Computer Vision Engine",
            "Live detection — identify geometric shapes and sequence them automatically"
        ))

        container = QHBoxLayout()
        container.setSpacing(20)

        # Camera card
        cam_card = QFrame()
        cam_card.setObjectName("Card")
        cam_layout = QVBoxLayout(cam_card)
        cam_layout.setContentsMargins(20, 20, 20, 20)
        cam_layout.setSpacing(12)

        cam_title = QLabel("Live Camera Feed")
        cam_title.setObjectName("SectionTitle")
        cam_layout.addWidget(cam_title)

        self.cam_view = QLabel("Connecting to camera…")
        self.cam_view.setMinimumSize(720, 520)
        self.cam_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cam_view.setStyleSheet(
            "background-color: #05070a; border: 1px solid #21262d; "
            "border-radius: 12px; color: #8b949e; font-size: 14px;"
        )
        cam_layout.addWidget(self.cam_view)

        container.addWidget(cam_card, 3)

        # Control card
        ctrl_card = QFrame()
        ctrl_card.setObjectName("Card")
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(24, 24, 24, 24)
        ctrl_layout.setSpacing(16)
        ctrl_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        ctrl_title = QLabel("Detection Control")
        ctrl_title.setObjectName("SectionTitle")
        ctrl_layout.addWidget(ctrl_title)

        hint = QLabel(
            "Point the camera at the workspace. Detected shapes will be queued "
            "and executed by the robot in sequence."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("background: transparent; color: #8b949e; font-size: 12px; line-height: 1.5;")
        ctrl_layout.addWidget(hint)

        ctrl_layout.addSpacing(8)

        self.btn_detect_seq = QPushButton("  Auto-Detect Sequence")
        self.btn_detect_seq.setIcon(get_svg_icon("vision", "#ffffff"))
        self.btn_detect_seq.setIconSize(QtCore.QSize(20, 20))
        self.btn_detect_seq.setObjectName("PrimaryAction")
        self.btn_detect_seq.setMinimumHeight(52)
        self.btn_detect_seq.clicked.connect(self.run_vision_sequence)
        ctrl_layout.addWidget(self.btn_detect_seq)

        ctrl_layout.addStretch()
        container.addWidget(ctrl_card, 1)

        layout.addLayout(container)

        self.vision_engine = VisionEngine()
        self.cam_thread = CameraThread(self.vision_engine)
        self.cam_thread.change_pixmap_signal.connect(self.update_image)
        self.cam_thread.detection_signal.connect(self.handle_detections)
        self.cam_thread.start()

        return page

    def handle_detections(self, shapes):
        self.current_shapes = shapes

    def run_vision_sequence(self):
        if not self.worker.is_connected:
            self.show_error("Please connect the robot first.")
            return
        self.worker.run_vision_sequence(self.current_shapes)

    def update_image(self, cv_img):
        qt_img = self.convert_cv_qt(cv_img)
        self.cam_view.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        # Add tech overlay
        h, w, _ = cv_img.shape
        cv2.putText(cv_img, "LITE 6 - VISION ENGINE", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.line(cv_img, (w//2 - 20, h//2), (w//2 + 20, h//2), (0, 255, 0), 1)
        cv2.line(cv_img, (w//2, h//2 - 20), (w//2, h//2 + 20), (0, 255, 0), 1)
        
        # Rounded rectangle overlay (simulated HUD corners)
        length = 40
        thickness = 2
        color = (139, 148, 158) # #8b949e
        cv2.line(cv_img, (20, 20), (20 + length, 20), color, thickness)
        cv2.line(cv_img, (20, 20), (20, 20 + length), color, thickness)
        
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(q_img.scaled(720, 520, Qt.AspectRatioMode.KeepAspectRatio))

    # ========================================================
    # ROBOT STATE
    # ========================================================
    def connect_robot(self):
        self.btn_connect.setEnabled(False)
        self.conn_label.setText("● CONNECTING…")
        QTimer.singleShot(100, self.worker.connect)

    def update_conn_status(self, status):
        self.lbl_state.setText(status)
        if status == "CONNECTED":
            self.lbl_state.setStyleSheet("background: transparent; color: #3fb950; font-size: 18px; font-weight: 700;")
            self.conn_label.setText("● CONNECTED")
            self.conn_label.setObjectName("StatusLabelConnected")
            self.conn_label.setStyleSheet("")
            self.conn_label.style().unpolish(self.conn_label)
            self.conn_label.style().polish(self.conn_label)
            self.btn_connect.setHidden(True)
        else:
            self.lbl_state.setStyleSheet("background: transparent; color: #ff7b72; font-size: 18px; font-weight: 700;")
            self.conn_label.setText(f"● {status}")
            self.btn_connect.setEnabled(True)

    def update_progress(self, value):
        self.gcode_progress.setValue(value)

    def update_telemetry(self, pos):
        self.lbl_x.setText(f"{pos[0]:.2f} mm")
        self.lbl_y.setText(f"{pos[1]:.2f} mm")
        self.lbl_z.setText(f"{pos[2]:.2f} mm")

    def show_error(self, message):
        self.lbl_state.setText("ERROR")
        self.lbl_state.setStyleSheet("background: transparent; color: #ff7b72; font-size: 18px; font-weight: 700;")
        QMessageBox.critical(self, "System Error", message)
        self.btn_connect.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Lite6App()
    window.show()
    sys.exit(app.exec())
