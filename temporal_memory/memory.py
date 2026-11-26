
import json
from collections import defaultdict


class TemporalMemory:
    def __init__(self):
        self.track_history = defaultdict(list)
        self.frame_history = []

    def load_data(self, file_path):
        with open(file_path, "r") as file:
            data = json.load(file)

        return data

    def process_frames(self, data):
        self.track_history.clear()
        self.frame_history.clear()

        for frame in data:
            frame_id = frame["frame_id"]
            timestamp = frame["timestamp"]

            self.frame_history.append(frame_id)

            for person in frame["tracks"]:
                track_id = person["track_id"]
                bbox = person["bbox"]

                x1, y1, x2, y2 = bbox

                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2

                self.track_history[track_id].append({
                    "frame_id": frame_id,
                    "timestamp": timestamp,
                    "center": (center_x, center_y),
                    "confidence": person["confidence"]
                })

    def get_summary(self):
        summary = {}

        for track_id, history in self.track_history.items():
            first = history[0]
            last = history[-1]

            start_x, start_y = first["center"]
            end_x, end_y = last["center"]

            movement_x = end_x - start_x
            movement_y = end_y - start_y

            summary[track_id] = {
                "frames_detected": len(history),
                "first_frame": first["frame_id"],
                "last_frame": last["frame_id"],
                "movement_x": movement_x,
                "movement_y": movement_y,
                "average_confidence": sum(
                    item["confidence"] for item in history
                ) / len(history)
            }

        return summary

    def detect_missing_frames(self):
        missing = {}

        for track_id, history in self.track_history.items():
            detected_frames = {
                item["frame_id"] for item in history
            }

            gaps = [
                frame for frame in self.frame_history
                if frame not in detected_frames
            ]

            missing[track_id] = gaps

        return missing
