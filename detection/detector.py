"""
YOLOv8 inference wrapper for the AI Product Shelf Monitoring System.

This module loads a trained YOLOv8 model (Ultralytics) once per process and
exposes a simple `detect()` method that Flask routes call. Keeping the model
load out of request handlers avoids reloading weights on every request.

Usage:
    from detection.detector import get_detector
    detector = get_detector(current_app.config)
    result = detector.detect(image_path)
"""
import os
import threading

_detector_lock = threading.Lock()
_detector_instance = None


class ShelfDetector:
    def __init__(self, model_path, confidence_threshold=0.4):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self._model = None

    def _load_model(self):
        if self._model is None:
            # Imported lazily so the rest of the app works even before
            # ultralytics/torch are installed (e.g. during early development).
            from ultralytics import YOLO

            if not os.path.exists(self.model_path):
                raise FileNotFoundError(
                    f"YOLO model weights not found at '{self.model_path}'. "
                    "Place your trained best.pt there or set YOLO_MODEL_PATH."
                )
            self._model = YOLO(self.model_path)
        return self._model

    def detect(self, image_path):
        """
        Runs inference on a single image.

        Returns a dict:
        {
            "detections": [
                {"class_label": str, "confidence": float, "box": [x1, y1, x2, y2]},
                ...
            ],
            "image_width": int,
            "image_height": int,
        }
        """
        model = self._load_model()
        results = model.predict(
            source=image_path,
            conf=self.confidence_threshold,
            verbose=False,
        )

        detections = []
        result = results[0]
        height, width = result.orig_shape

        for box in result.boxes:
            cls_id = int(box.cls[0])
            class_label = model.names[cls_id]
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            detections.append(
                {
                    "class_label": class_label,
                    "confidence": confidence,
                    "box": [x1, y1, x2, y2],
                }
            )

        return {
            "detections": detections,
            "image_width": width,
            "image_height": height,
        }

    def annotate(self, image_path, detections, output_path):
        """Draws bounding boxes + labels on the image and saves it to output_path."""
        import cv2

        image = cv2.imread(image_path)
        for det in detections:
            x1, y1, x2, y2 = det["box"]
            label = f"{det['class_label']} {det['confidence']:.2f}"
            cv2.rectangle(image, (x1, y1), (x2, y2), (46, 204, 113), 2)
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(image, (x1, y1 - text_h - 8), (x1 + text_w + 4, y1), (46, 204, 113), -1)
            cv2.putText(
                image, label, (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA,
            )
        cv2.imwrite(output_path, image)
        return output_path


def get_detector(app_config):
    """Returns a process-wide singleton ShelfDetector, built from Flask app config."""
    global _detector_instance
    with _detector_lock:
        if _detector_instance is None:
            _detector_instance = ShelfDetector(
                model_path=app_config["YOLO_MODEL_PATH"],
                confidence_threshold=app_config["YOLO_CONFIDENCE_THRESHOLD"],
            )
        return _detector_instance
