import cv2
import numpy as np

class VisionEngine:
    def __init__(self):
        # Camera intrinsic/extrinsic calibration would go here
        # For now, we assume a simple mapping or pixel-to-mm ratio
        self.pixel_to_mm = 0.5 
        self.offset_x = 0
        self.offset_y = 0

    def detect_shapes(self, frame):
        """
        Detects Square, Triangle, and Circle in the frame.
        Returns a dictionary of found shapes with their centroids in mm.
        """
        results = {"triangle": None, "square": None, "circle": None}
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 150)
        
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 500: continue # Filter noise
            
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            M = cv2.moments(cnt)
            if M["m00"] == 0: continue
            
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            
            # Convert to Robot Coordinates (Conceptual)
            rx = cx * self.pixel_to_mm + self.offset_x
            ry = cy * self.pixel_to_mm + self.offset_y
            
            if len(approx) == 3:
                results["triangle"] = (rx, ry)
                cv2.drawContours(frame, [cnt], -1, (0, 255, 0), 2)
                cv2.putText(frame, "Triangle", (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
            elif len(approx) == 4:
                # Check for squareness (aspect ratio)
                (x, y, w, h) = cv2.boundingRect(approx)
                ar = w / float(h)
                if 0.95 <= ar <= 1.05:
                    results["square"] = (rx, ry)
                    cv2.drawContours(frame, [cnt], -1, (255, 0, 0), 2)
                    cv2.putText(frame, "Square", (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            elif len(approx) > 6:
                circularity = (4 * np.pi * area) / (peri**2)
                if circularity > 0.8:
                    results["circle"] = (rx, ry)
                    cv2.drawContours(frame, [cnt], -1, (0, 0, 255), 2)
                    cv2.putText(frame, "Circle", (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                    
        return results, frame
