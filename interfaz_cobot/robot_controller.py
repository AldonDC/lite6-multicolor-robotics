import time
import os
import sys
import re
from PyQt6.QtCore import QObject, pyqtSignal

# Add SDK path
sys.path.append(os.path.join(os.path.dirname(__file__), 'xArm-Python-SDK'))

try:
    from xarm.wrapper import XArmAPI
except ImportError:
    XArmAPI = None

class RobotWorker(QObject):
    finished = pyqtSignal()
    status_updated = pyqtSignal(str)
    pos_updated = pyqtSignal(list)
    progress_updated = pyqtSignal(int)
    error_occurred = pyqtSignal(str)

    def __init__(self, ip):
        super().__init__()
        self.ip = ip
        self.arm = None
        self.is_connected = False
        
        # Calibration constants (based on your scripts)
        self.X_BASE = 95.6
        self.Y_BASE = 321.1
        self.Z_UP = 150.0
        self.Z_DRAW = 98.0 # Default draw height
        self.ROLL = -178.9
        self.PITCH = 3.5
        self.YAW = 112.2

    def connect(self):
        if not XArmAPI:
            self.error_occurred.emit("SDK not found")
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
            self.error_occurred.emit(f"Connection failed: {str(e)}")
            return False

    def check_collision(self, x, y, z):
        """Simple safety check to avoid hitting the base or table too hard."""
        # Forbidden Cylinder near base: Radius < 100mm
        dist_sq = x**2 + y**2
        if dist_sq < 100**2:
            return True, "Target too close to base (Radius < 100mm)"
        if z < 0:
            return True, "Target below table level (Z < 0)"
        return False, ""

    def move_to(self, x, y, z, wait=True):
        collision, msg = self.check_collision(x, y, z)
        if collision:
            self.error_occurred.emit(f"COLLISION PREVENTED: {msg}")
            return False
        
        code = self.arm.set_position(x=x, y=y, z=z, roll=self.ROLL, 
                                     pitch=self.PITCH, yaw=self.YAW, 
                                     speed=100, wait=wait, is_radian=False)
        if code == 0:
            self.pos_updated.emit([x, y, z])
            return True
        else:
            self.error_occurred.emit(f"Robot Error: {code}")
            return False

    def draw_square(self, side=50):
        self.status_updated.emit("Drawing Square...")
        # Start at Base
        res = self.move_to(self.X_BASE, self.Y_BASE, self.Z_DRAW)
        if not res: return
        
        self.move_to(self.X_BASE - side, self.Y_BASE, self.Z_DRAW)
        self.move_to(self.X_BASE - side, self.Y_BASE - side, self.Z_DRAW)
        self.move_to(self.X_BASE, self.Y_BASE - side, self.Z_DRAW)
        self.move_to(self.X_BASE, self.Y_BASE, self.Z_DRAW)
        
        self.move_to(self.X_BASE, self.Y_BASE, self.Z_UP)
        self.status_updated.emit("Square Finished")
        self.finished.emit()

    def draw_triangle(self, side=50):
        self.status_updated.emit("Drawing Triangle...")
        h = side * 0.866 # sqrt(3)/2
        self.move_to(self.X_BASE, self.Y_BASE, self.Z_DRAW)
        self.move_to(self.X_BASE - side, self.Y_BASE, self.Z_DRAW)
        self.move_to(self.X_BASE - side/2, self.Y_BASE - h, self.Z_DRAW)
        self.move_to(self.X_BASE, self.Y_BASE, self.Z_DRAW)
        
        self.move_to(self.X_BASE, self.Y_BASE, self.Z_UP)
        self.status_updated.emit("Triangle Finished")
        self.finished.emit()

    def draw_circle(self, diameter=50):
        self.status_updated.emit("Drawing Circle...")
        import math
        r = diameter / 2
        cx, cy = self.X_BASE - r, self.Y_BASE - r
        
        # Move to start
        self.move_to(cx + r, cy, self.Z_DRAW)
        
        for i in range(0, 361, 10):
            rad = math.radians(i)
            tx = cx + r * math.cos(rad)
            ty = cy + r * math.sin(rad)
            self.move_to(tx, ty, self.Z_DRAW, wait=True)
            
        self.move_to(cx + r, cy, self.Z_UP)
        self.status_updated.emit("Circle Finished")
        self.finished.emit()

    def run_gcode(self, filepath, scale=0.5):
        if not os.path.exists(filepath):
            self.error_occurred.emit("File not found")
            return

        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        total = len(lines)
        self.status_updated.emit("Running G-Code...")
        
        curr_x, curr_y = 0.0, 0.0
        for i, line in enumerate(lines):
            found_x = re.search(r'X([-+]?\d*\.\d+|\d+)', line)
            found_y = re.search(r'Y([-+]?\d*\.\d+|\d+)', line)
            
            if found_x or found_y:
                if found_x: curr_x = float(found_x.group(1))
                if found_y: curr_y = float(found_y.group(1))
                
                real_x = self.X_BASE - (curr_x * scale)
                real_y = self.Y_BASE - (curr_y * scale)
                self.move_to(real_x, real_y, self.Z_DRAW)
            
            self.progress_updated.emit(int((i/total)*100))
        
        self.move_to(self.X_BASE, self.Y_BASE, self.Z_UP)
        self.finished.emit()

    def run_vision_sequence(self, current_shapes):
        if not self.is_connected:
            return
            
        sequence = ["triangle", "square", "circle"]
        self.status_updated.emit("Vision Sequence: Auto-Navigating...")
        
        for shape_type in sequence:
            pos = current_shapes.get(shape_type)
            if pos:
                rx, ry = pos
                self.move_to(rx, ry, self.Z_UP)
                self.move_to(rx, ry, 110.0) # Move slightly above to "point"
                time.sleep(2)
                self.move_to(rx, ry, self.Z_UP)
            
        self.status_updated.emit("Vision Sequence Completed")
        self.finished.emit()

    def disconnect(self):
        if self.arm:
            self.arm.disconnect()
            self.is_connected = False
            self.status_updated.emit("DISCONNECTED")
