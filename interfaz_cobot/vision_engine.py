import cv2
import numpy as np
import threading
import time


class VisionEngine:
    """
    Motor de visión — Logitech C920, forward-facing.

    DETECCIÓN AUTOMÁTICA DE CÁMARA
    ────────────────────────────────
    camera_index=None  → prueba índices 0-10 y usa el primero que funcione.
    camera_index=N     → fuerza ese índice específico.

    SINCRONIZACIÓN CÁMARA ↔ PROCESAMIENTO
    ──────────────────────────────────────
    Un hilo grabber consume el buffer de OpenCV continuamente.
    detect_shapes() siempre trabaja con el frame más reciente — sin desfase.

    pixel_to_mm (calculado con FOV C920 70.4°×43.3°):
      @ 1280×720 → 0.496 mm/px
      @ 640×480  → 0.868 mm/px

    Ejes (forward-facing):
      Px derecha   → robot +Y
      Px izquierda → robot -Y
      Px arriba    → robot +Z
      Px abajo     → robot -Z
    """

    PX_TO_MM = {
        (1280, 720): 0.496,
        (640,  480): 0.868,
        (960,  540): 0.661,
    }
    DEFAULT_PX_TO_MM = 0.496

    def __init__(self, camera_index=None, offset_cx: int = 0, offset_cy: int = 60):
        self.offset_cx     = offset_cx
        self.offset_cy     = offset_cy
        self._pixel_to_mm  = self.DEFAULT_PX_TO_MM
        self.frame_cx      = 640
        self.frame_cy      = 360
        self._lock         = threading.Lock()
        self._latest_frame = None
        self._running      = True
        self.camera_index  = None
        self._cap          = None

        # Abrir cámara
        self._cap = self._open_camera(camera_index)

        if self._cap is None:
            print("[VisionEngine] ⚠️  No se encontró ninguna cámara disponible.")
            return

        # Intentar resolución alta
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self._cap.set(cv2.CAP_PROP_FPS, 30)

        w   = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h   = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self._cap.get(cv2.CAP_PROP_FPS)
        print(f"[VisionEngine] Índice {self.camera_index} → {w}×{h} @ {fps:.0f}fps")

        # Iniciar grabber
        self._grabber = threading.Thread(target=self._grab_loop, daemon=True)
        self._grabber.start()

        # Esperar primer frame (máx 3s)
        deadline = time.time() + 3.0
        while self._latest_frame is None and time.time() < deadline:
            time.sleep(0.03)

        if self._latest_frame is None:
            print("[VisionEngine] ⚠️  La cámara abrió pero no entrega frames.")

    # ── Búsqueda de cámara ────────────────────────────────────────────────────

    def _open_camera(self, forced_index):
        # C920 confirmada en /dev/video3 — si se pasa None usa ese por defecto
        if forced_index is None:
            forced_index = 3
        candidates = [forced_index, 0]   # intenta 3 primero, 0 como fallback
        for idx in candidates:
            try:
                cap = cv2.VideoCapture(idx)
                if not cap.isOpened():
                    cap.release()
                    continue
                ok, frame = cap.read()
                if ok and frame is not None and frame.size > 0:
                    self.camera_index = idx
                    print(f"[VisionEngine] Cámara encontrada en índice {idx}")
                    return cap
                cap.release()
            except Exception:
                continue
        return None

    # ── Hilo grabber ──────────────────────────────────────────────────────────

    def _grab_loop(self):
        while self._running and self._cap is not None:
            ret, frame = self._cap.read()
            if ret and frame is not None:
                with self._lock:
                    self._latest_frame = frame

    # ── API pública ───────────────────────────────────────────────────────────

    def is_ready(self) -> bool:
        with self._lock:
            return self._latest_frame is not None

    def get_latest_frame(self):
        with self._lock:
            f = self._latest_frame
        return None if f is None else f.copy()

    def detect_shapes(self, frame=None):
        """
        Detecta cuadrado, triángulo y círculo.

        frame=None → usa el frame más reciente del grabber (sincronizado).
        frame=img  → procesa ese frame directamente.

        Retorna:
            results  : {"triangle": (dy_mm, dz_mm)|None, "square": ..., "circle": ...}
            annotated: frame BGR anotado  (None si no hay frame disponible)
        """
        empty = {"triangle": None, "square": None, "circle": None}

        if frame is None:
            with self._lock:
                raw = self._latest_frame
            if raw is None:
                return empty, None
            frame = raw.copy()
        else:
            frame = frame.copy()

        h, w = frame.shape[:2]
        self._pixel_to_mm = self.PX_TO_MM.get((w, h), self.DEFAULT_PX_TO_MM)
        self.frame_cx = w // 2 + self.offset_cx
        self.frame_cy = h // 2 + self.offset_cy

        results = dict(empty)

        gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged   = cv2.Canny(blurred, 50, 150)

        contours, _ = cv2.findContours(
            edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 500:
                continue

            peri   = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            M      = cv2.moments(cnt)
            if M["m00"] == 0:
                continue

            cx_px = int(M["m10"] / M["m00"])
            cy_px = int(M["m01"] / M["m00"])

            dy_mm = (cx_px - self.frame_cx) * self._pixel_to_mm
            dz_mm = (self.frame_cy - cy_px) * self._pixel_to_mm

            label = None
            color = (255, 255, 255)

            if len(approx) == 3:
                if results["triangle"] is None:
                    results["triangle"] = (dy_mm, dz_mm)
                label, color = "Triangle", (0, 220, 80)

            elif len(approx) == 4:
                xr, yr, wr, hr = cv2.boundingRect(approx)
                ar = wr / float(hr)
                if 0.90 <= ar <= 1.10:
                    if results["square"] is None:
                        results["square"] = (dy_mm, dz_mm)
                    label, color = "Square", (255, 140, 0)

            elif len(approx) > 6:
                circularity = (4 * np.pi * area) / (peri ** 2)
                if circularity > 0.78:
                    if results["circle"] is None:
                        results["circle"] = (dy_mm, dz_mm)
                    label, color = "Circle", (60, 100, 255)

            if label:
                cv2.drawContours(frame, [cnt], -1, color, 2)
                cv2.putText(
                    frame,
                    f"{label}  Y{dy_mm:+.0f} Z{dz_mm:+.0f}mm",
                    (cx_px, cy_px - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1
                )
                cv2.circle(frame, (cx_px, cy_px), 5, (0, 255, 255), -1)

        # Cruz del centro óptico
        cv2.drawMarker(frame, (self.frame_cx, self.frame_cy),
                       (0, 255, 255), cv2.MARKER_CROSS, 28, 2)
        cv2.putText(
            frame,
            f"AIM  {self._pixel_to_mm:.3f}mm/px",
            (self.frame_cx + 16, self.frame_cy + 6),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1
        )

        return results, frame

    def calibrate(self, pixel_distance: float, real_mm: float):
        if pixel_distance > 0:
            val    = real_mm / pixel_distance
            factor = val / self._pixel_to_mm
            self.PX_TO_MM         = {k: v * factor for k, v in self.PX_TO_MM.items()}
            self.DEFAULT_PX_TO_MM = val
            print(f"[VisionEngine] Calibrado manual: {val:.4f} mm/px")

    def release(self):
        self._running = False
        if hasattr(self, "_grabber"):
            self._grabber.join(timeout=1.0)
        if self._cap is not None:
            self._cap.release()