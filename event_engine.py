
import json
import os
from collections import defaultdict

INPUT_FILE = "tracking_data.json"
OUTPUT_FILE = "events.json"

# Initial demo thresholds. These need validation on real videos.
FAST_MOVEMENT_THRESHOLD = 180  # pixels per second
CROWD_THRESHOLD = 8             # people in one frame
EVENT_COOLDOWN = 2.0
CROWD_COOLDOWN = 5.0            # seconds between repeated alerts


def load_tracking_data(filename):
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("frames", "data", "results"):
            if isinstance(data.get(key), list):
                return data[key]

    raise ValueError("Could not find a list of video frames in tracking_data.json")


def get_center(bbox):
    if not isinstance(bbox, (list, tuple)) or len(bbox) < 4:
        return None

    x1, y1, x2, y2 = map(float, bbox[:4])
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def detect_events(frames):
    events = []
    track_history = defaultdict(list)
    last_alert_time = {}
    last_crowd_alert_time = -999

    for frame in frames:
        timestamp = float(frame.get("timestamp", 0))
        frame_id = frame.get("frame_id", -1)
        tracks = frame.get("tracks", [])

        people_count = 0

        for track in tracks:
            track_id = track.get("track_id")
            class_name = str(track.get("class_name", "unknown")).lower()

            if class_name == "person":
                people_count += 1

            center = get_center(track.get("bbox"))
            if center is None or track_id is None:
                continue

            track_history[track_id].append({
                "timestamp": timestamp,
                "frame_id": frame_id,
                "center": center,
                "class_name": class_name
            })

        
        # Crowd density alert with cooldown
        if people_count >= CROWD_THRESHOLD:
            if timestamp - last_crowd_alert_time >= CROWD_COOLDOWN:
                events.append({
                    "event_type": "high_crowd_density",
                    "timestamp": timestamp,
                    "frame_id": frame_id,
                    "people_count": people_count,
                    "description": (
                        f"{people_count} people detected in one frame. "
                        "Review this area for possible crowding."
                    ),
                    "severity": "medium"
                })

                last_crowd_alert_time = timestamp

    # Movement analysis for each tracked object
    for track_id, observations in track_history.items():
        if len(observations) < 3:
            continue
        observations.sort(key=lambda item: item["timestamp"])

        for previous, current in zip(observations, observations[1:]):
            time_gap = current["timestamp"] - previous["timestamp"]

            if time_gap <= 0:
                continue

            x1, y1 = previous["center"]
            x2, y2 = current["center"]

            distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            speed = distance / time_gap

            if current["class_name"] == "person" and speed >= FAST_MOVEMENT_THRESHOLD:
                event_time = current["timestamp"]
                last_time = last_alert_time.get(track_id, -999)

                if event_time - last_time >= EVENT_COOLDOWN:
                    events.append({
                        "event_type": "sudden_movement",
                        "timestamp": event_time,
                        "frame_id": current["frame_id"],
                        "track_id": track_id,
                        "object": current["class_name"],
                        "estimated_speed_pixels_per_second": round(speed, 2),
                        "description": (
                            f"{current['class_name']} with Track ID {track_id} "
                            "showed rapid movement."
                        ),
                        "severity": "medium"
                    })

                    last_alert_time[track_id] = event_time

    events.sort(key=lambda event: event["timestamp"])
    return events


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: {INPUT_FILE} not found.")
        print("Place this script in your main VISTA_AI folder.")
        return

    frames = load_tracking_data(INPUT_FILE)
    events = detect_events(frames)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(events, file, indent=4)

    print("\n========== VISTA AI EVENT ENGINE ==========")
    print(f"Frames processed: {len(frames)}")
    print(f"Events generated: {len(events)}")
    print(f"Output saved to: {OUTPUT_FILE}")

    for event in events[:15]:
        print(
            f"\n[{event['event_type']}] "
            f"Time: {event['timestamp']:.2f}s"
        )
        print(event["description"])

    if not events:
        print("No events detected with the current thresholds.")

    print("\nEVENT ENGINE TEST COMPLETED!")


if __name__ == "__main__":
    main()
