
import cv2
import json
import sys

from pathlib import Path
from collections import Counter
from ultralytics import YOLO
from temporal_memory.memory import TemporalMemory


# Supported media formats
IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_FORMATS = {".mp4", ".avi", ".mov", ".mkv"}


def process_media(media_path):

    media_path = Path(media_path)

    if not media_path.exists():
        raise FileNotFoundError("Media file not found!")

    # Load pretrained YOLO model
    model = YOLO("yolo11n.pt")

    all_frames = []

    # IMAGE PROCESSING
    if media_path.suffix.lower() in IMAGE_FORMATS:

        results = model.predict(
            source=str(media_path),
            verbose=False
        )

        result = results[0]
        tracks = []

        if result.boxes is not None:
            for i, box in enumerate(result.boxes):

                class_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                bbox = box.xyxy[0].tolist()

                tracks.append({
                    "track_id": i + 1,
                    "class_id": class_id,
                    "class_name": model.names[class_id],
                    "confidence": confidence,
                    "bbox": bbox
                })

        all_frames.append({
            "video_id": media_path.name,
            "frame_id": 1,
            "timestamp": 0.0,
            "tracks": tracks
        })

    # VIDEO PROCESSING
    elif media_path.suffix.lower() in VIDEO_FORMATS:

        cap = cv2.VideoCapture(str(media_path))

        if not cap.isOpened():
            raise ValueError("Unable to open video!")

        fps = cap.get(cv2.CAP_PROP_FPS)

        if fps <= 0:
            fps = 30

        frame_id = 0

        while True:

            success, frame = cap.read()

            if not success:
                break

            frame_id += 1

            # Detect and track objects
            results = model.track(
                frame,
                persist=True,
                tracker="bytetrack.yaml",
                verbose=False
            )

            result = results[0]
            tracks = []
            boxes = result.boxes

            if boxes is not None:

                ids = boxes.id

                for i, box in enumerate(boxes):

                    class_id = int(box.cls[0].item())
                    confidence = float(box.conf[0].item())
                    bbox = box.xyxy[0].tolist()

                    if ids is not None:
                        track_id = int(ids[i].item())
                    else:
                        track_id = f"untracked_{frame_id}_{i}"

                    tracks.append({
                        "track_id": track_id,
                        "class_id": class_id,
                        "class_name": model.names[class_id],
                        "confidence": confidence,
                        "bbox": bbox
                    })

            all_frames.append({
                "video_id": media_path.name,
                "frame_id": frame_id,
                "timestamp": frame_id / fps,
                "tracks": tracks
            })

        cap.release()

    else:
        raise ValueError("Unsupported image or video format!")

    return all_frames


def main():

    if len(sys.argv) < 2:
        print("Usage: python media_processor.py <media_path>")
        return

    media_path = sys.argv[1]

    print("\n===== VISTA AI MEDIA ANALYSIS =====")

    # Automatically process uploaded media
    data = process_media(media_path)

    # Save generated tracking information
    output_path = Path("temporal_memory/generated_tracking.json")

    with open(output_path, "w") as file:
        json.dump(data, file, indent=4)

    # Count detected objects
    object_counts = Counter()

    for frame in data:
        for track in frame["tracks"]:
            object_counts[track["class_name"]] += 1

    print("\nDetected objects across frames:")

    for name, count in object_counts.items():
        print(name, ":", count)

    print("\nTotal frames processed:", len(data))

    # Run temporal memory for videos
    if len(data) > 1:

        memory = TemporalMemory()
        memory.process_frames(data)

        print("\n===== TEMPORAL MEMORY =====")

        for track_id, details in memory.get_summary().items():

            print("\nTrack ID:", track_id)
            print("Frames detected:", details["frames_detected"])
            print("Horizontal movement:", details["movement_x"])
            print("Vertical movement:", details["movement_y"])

        print("\nMissing detections:")
        print(memory.detect_missing_frames())

    print("\nGenerated JSON:", output_path)
    print("\nVista AI analysis completed!")


if __name__ == "__main__":
    main()
