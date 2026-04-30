import time
import os
import sys
import re
import math
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

sys.path.append(os.path.join(os.path.dirname(__file__), 'xArm-Python-SDK'))

try:
    from xarm.wrapper import XArmAPI
except ImportError:
    XArmAPI = None


class RobotWorker(QObject):

    finished         = pyqtSignal()
    status_updated   = pyqtSignal(str)
    pos_updated      = pyqtSignal(list)
    progress_updated = pyqtSignal(int)
    error_occurred   = pyqtSignal(str)

    def __init__(self, ip: str):
        super().__init__()
        self.ip  = ip
        self.arm = None
        self.is_connected = False

        # ── HOME ──────────────────────────────────────────────────────────────
        self.HOME_X = 200.0
        self.HOME_Y = 0.0
        self.HOME_Z = 150.0

        # ── DIBUJO ────────────────────────────────────────────────────────────
        self.X_BASE = 200.0
        self.Y_BASE = 0.0
        self.Z_UP   = 150.0
        self.Z_DRAW = 95.0

        # ── ORIENTACIÓN EN GRADOS ─────────────────────────────────────────────
        self.ROLL  = 180.0
        self.PITCH = 0.0
        self.YAW   = 0.0

        # ── VISIÓN FORWARD-FACING ─────────────────────────────────────────────
        self.X_POINT = 200.0   # X fijo de apuntado
        self.Z_POINT = 163.0   # Z base de apuntado (altura donde ves las figuras)
        self.Z_MIN   = 50.0    # Z mínimo permitido

        # Cuánto baja el brazo al validar cada figura (mm)
        # Se baja desde target_z hacia abajo esta cantidad para "confirmar"
        self.Z_VALIDATE_DROP = 30.0

        # Delta mínimo para filtrar ruido
        self.MIN_DELTA_MM = 4.0

    # =========================================================================
    # CONEXIÓN
    # =========================================================================

    @pyqtSlot()
    def connect(self):
        if not XArmAPI:
            self.error_occurred.emit("SDK de xArm no encontrado.")
            return False
        try:
            self.arm = XArmAPI(self.ip)
            self.arm.clean_error()
            self.arm.motion_enable(enable=True)
            self.arm.set_mode(0)
            self.arm.set_state(state=0)
            self.is_connected = True
            self.status_updated.emit("CONNECTED")
            return True
        except Exception as e:
            self.error_occurred.emit(f"Error de conexión: {str(e)}")
            return False

    def disconnect(self):
        if self.arm:
            self.arm.disconnect()
            self.is_connected = False

    # =========================================================================
    # MOVIMIENTO
    # =========================================================================

    def _get_current_position(self):
        if not self.is_connected:
            return None
        code, pos = self.arm.get_position()
        if code == 0 and pos:
            return pos
        self.error_occurred.emit(f"No se pudo leer posición (código {code})")
        return None

    def check_collision(self, x, y, z):
        if x ** 2 + y ** 2 < 80 ** 2:
            return True, "Demasiado cerca de la base."
        if z < self.Z_MIN:
            return True, f"Z demasiado bajo (mínimo {self.Z_MIN} mm)."
        return False, ""

    def move_to(self, x, y, z, wait=True, mvline=False):
        if not self.is_connected:
            return False

        z = max(self.Z_MIN, z)   # clamp siempre

        collision, msg = self.check_collision(x, y, z)
        if collision:
            self.error_occurred.emit(f"COLISIÓN EVITADA: {msg}")
            return False

        speed = 50 if mvline else 80
        code  = self.arm.set_position(
            x=x, y=y, z=z,
            roll=self.ROLL, pitch=self.PITCH, yaw=self.YAW,
            speed=speed, wait=wait, mvline=mvline,
            is_radian=False
        )

        if code == 0:
            self.pos_updated.emit([x, y, z])
            return True

        if code == 9:
            self.error_occurred.emit(
                f"Posición inalcanzable (code=9): X={x:.1f} Y={y:.1f} Z={z:.1f}\n"
                "Ajusta X_POINT/Z_POINT en el panel de calibración."
            )
        else:
            self.error_occurred.emit(f"Error del Robot: Código {code}")
        return False

    def go_home(self):
        self.status_updated.emit("Regresando a HOME...")
        self.move_to(self.HOME_X, self.HOME_Y, self.HOME_Z, wait=True)
        self.status_updated.emit("HOME")

    # =========================================================================
    # FIGURAS GEOMÉTRICAS
    # =========================================================================

    @pyqtSlot()
    def draw_square(self, side=50):
        if not self.is_connected: return
        self.status_updated.emit("Dibujando Cuadrado...")
        self.move_to(self.X_BASE,        self.Y_BASE,        self.Z_UP)
        self.move_to(self.X_BASE,        self.Y_BASE,        self.Z_DRAW)
        self.move_to(self.X_BASE + side, self.Y_BASE,        self.Z_DRAW, mvline=True)
        self.move_to(self.X_BASE + side, self.Y_BASE + side, self.Z_DRAW, mvline=True)
        self.move_to(self.X_BASE,        self.Y_BASE + side, self.Z_DRAW, mvline=True)
        self.move_to(self.X_BASE,        self.Y_BASE,        self.Z_DRAW, mvline=True)
        self.move_to(self.X_BASE,        self.Y_BASE,        self.Z_UP)
        self.go_home()
        self.finished.emit()

    @pyqtSlot()
    def draw_triangle(self, side=50):
        if not self.is_connected: return
        self.status_updated.emit("Dibujando Triángulo...")
        h = side * 0.866
        self.move_to(self.X_BASE,              self.Y_BASE,     self.Z_UP)
        self.move_to(self.X_BASE,              self.Y_BASE,     self.Z_DRAW)
        self.move_to(self.X_BASE + side,       self.Y_BASE,     self.Z_DRAW, mvline=True)
        self.move_to(self.X_BASE + (side / 2), self.Y_BASE + h, self.Z_DRAW, mvline=True)
        self.move_to(self.X_BASE,              self.Y_BASE,     self.Z_DRAW, mvline=True)
        self.move_to(self.X_BASE,              self.Y_BASE,     self.Z_UP)
        self.go_home()
        self.finished.emit()

    @pyqtSlot()
    def draw_circle(self, diameter=50):
        if not self.is_connected: return
        self.status_updated.emit("Dibujando Círculo...")
        r  = diameter / 2
        cx = self.X_BASE + r
        cy = self.Y_BASE
        self.move_to(cx + r, cy, self.Z_UP)
        self.move_to(cx + r, cy, self.Z_DRAW)
        for deg in range(0, 360, 10):
            rad = math.radians(deg)
            self.move_to(cx + r * math.cos(rad), cy + r * math.sin(rad),
                         self.Z_DRAW, mvline=True)
        self.move_to(cx + r, cy, self.Z_DRAW, mvline=True)
        self.move_to(cx + r, cy, self.Z_UP)
        self.go_home()
        self.finished.emit()

    # =========================================================================
    # G-CODE
    # =========================================================================

    @pyqtSlot(str)
    def run_gcode(self, filepath: str, scale: float = 0.5):
        if not self.is_connected or not os.path.exists(filepath):
            return
        with open(filepath, 'r') as f:
            lines = f.readlines()
        total = len(lines)
        self.status_updated.emit("Ejecutando G-Code...")
        curr_x, curr_y = 0.0, 0.0
        for i, line in enumerate(lines):
            found_x = re.search(r'X([-+]?\d*\.?\d+)', line)
            found_y = re.search(r'Y([-+]?\d*\.?\d+)', line)
            if found_x or found_y:
                if found_x: curr_x = float(found_x.group(1))
                if found_y: curr_y = float(found_y.group(1))
                self.move_to(self.X_BASE + curr_x * scale,
                             self.Y_BASE + curr_y * scale,
                             self.Z_DRAW, mvline=True)
            self.progress_updated.emit(int((i / total) * 100))
        self.go_home()
        self.finished.emit()

    # =========================================================================
    # SECUENCIA DE VISIÓN
    # =========================================================================

    @pyqtSlot(dict)
    def run_vision_sequence(self, current_shapes: dict):
        """
        Para cada figura [triángulo → cuadrado → círculo]:

          1. Va a la posición de apuntado base (X_POINT, Y=0, Z_POINT).
          2. Aplica delta Y y Z de la detección.
          3. BAJA Z_VALIDATE_DROP mm para validar visualmente la figura.
          4. Pausa 1.2s en la posición de validación.
          5. Sube de vuelta a target_z (posición de apuntado de esa figura).
          6. Regresa a la base de apuntado.

        Al terminar todas → HOME.
        """
        if not self.is_connected or not current_shapes:
            self.error_occurred.emit("Robot desconectado o sin detecciones.")
            return

        sequence = ["triangle", "square", "circle"]
        self.status_updated.emit("Visión: Iniciando secuencia...")

        # Ir a posición de apuntado base
        ok = self.move_to(self.X_POINT, self.HOME_Y, self.Z_POINT, wait=True)
        if not ok:
            self.error_occurred.emit(
                f"No se pudo llegar a la posición base "
                f"(X={self.X_POINT}, Y=0, Z={self.Z_POINT}).\n"
                "Verifica los valores en el panel de calibración."
            )
            return

        for shape_name in sequence:
            delta = current_shapes.get(shape_name)
            if delta is None:
                self.status_updated.emit(f"  → {shape_name}: no detectado, saltando.")
                continue

            dy_mm, dz_mm = delta

            # ── Posición de apuntado para esta figura ──────────────────────────
            target_x = self.X_POINT
            target_y = max(-340.0, min(340.0, self.HOME_Y + dy_mm))
            target_z = max(self.Z_MIN, min(self.Z_POINT, self.Z_POINT + dz_mm))

            self.status_updated.emit(
                f"  → Apuntando {shape_name}  Y={target_y:+.1f}  Z={target_z:.1f} mm"
            )

            ok = self.move_to(target_x, target_y, target_z, wait=True, mvline=True)
            if not ok:
                self.status_updated.emit(f"  → {shape_name}: inalcanzable, saltando.")
                self.move_to(self.X_POINT, self.HOME_Y, self.Z_POINT, wait=True)
                continue

            # ── BAJADA DE VALIDACIÓN ───────────────────────────────────────────
            # Baja Z_VALIDATE_DROP mm desde la posición de apuntado
            # para "confirmar" visualmente la figura detectada.
            validate_z = max(self.Z_MIN, target_z - self.Z_VALIDATE_DROP)

            self.status_updated.emit(
                f"  → Validando {shape_name}  bajando a Z={validate_z:.1f} mm"
            )
            self.move_to(target_x, target_y, validate_z, wait=True, mvline=True)

            # Pausa en la posición de validación
            time.sleep(1.2)

            # Subir de vuelta a la posición de apuntado antes de moverse
            self.move_to(target_x, target_y, target_z, wait=True, mvline=True)

            # Regresar a posición de apuntado base
            self.move_to(self.X_POINT, self.HOME_Y, self.Z_POINT, wait=True)

        # ── HOME ───────────────────────────────────────────────────────────────
        self.go_home()
        self.status_updated.emit("Secuencia Completada ✓")
        self.finished.emit()