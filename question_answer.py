
import json
import os

class VISTAQuestionAnswer:

    def __init__(self, json_path="tracking_data.json"):
        self.json_path = json_path
        self.data = []

        with open(json_path, "r") as file:
            self.data = json.load(file)

        self.tracks = {}

        for frame in self.data:
            for obj in frame.get("tracks", []):
                track_id = obj["track_id"]

                if track_id not in self.tracks:
                    self.tracks[track_id] = []

                self.tracks[track_id].append({
                    "frame_id": frame["frame_id"],
                    "timestamp": frame["timestamp"],
                    "class_name": obj["class_name"],
                    "confidence": obj["confidence"],
                    "bbox": obj["bbox"]
                })

    def answer(self, question):

        q = question.lower()

        if "how many frames" in q:
            return f"Total frames processed: {len(self.data)}"

        if "how many people" in q:
            count = sum(
                1 for track in self.tracks.values()
                if track[0]["class_name"] == "person"
            )
            return f"Unique person tracks detected: {count}"

        if "how many objects" in q or "how many tracks" in q:
            return f"Total unique tracks detected: {len(self.tracks)}"

        if "which person moved the most" in q or "moved the most" in q:

            movements = {}

            for track_id, history in self.tracks.items():
                if len(history) < 2:
                    continue

                first = history[0]["bbox"]
                last = history[-1]["bbox"]

                start_x = (first[0] + first[2]) / 2
                start_y = (first[1] + first[3]) / 2

                end_x = (last[0] + last[2]) / 2
                end_y = (last[1] + last[3]) / 2

                distance = (
                    (end_x - start_x) ** 2 +
                    (end_y - start_y) ** 2
                ) ** 0.5

                movements[track_id] = distance

            if not movements:
                return "Not enough tracking data to calculate movement."

            best = max(movements, key=movements.get)

            return (
                f"Track ID {best} moved the most. "
                f"Estimated displacement: {movements[best]:.2f} pixels."
            )

        
        if "disappear" in q or "last seen" in q:
            if not self.tracks:
                return "No tracking data available."

            results = []

            for track_id, history in self.tracks.items():
                last = history[-1]
                results.append(
                    f"Track {track_id}: last detected at "
                    f"{last['timestamp']} seconds"
                )

            return "\n".join(results)

        if "which objects" in q or "what objects" in q:
            classes = sorted(set(
                item["class_name"]
                for history in self.tracks.values()
                for item in history
            ))
            return "Detected objects: " + ", ".join(classes)

        
        
        # FALL / COLLAPSE-LIKE MOVEMENT ANALYSIS
        if "collapse" in q or "fall" in q:
            fall_results = []

            for track_id, history in self.tracks.items():
                if len(history) < 2:
                    continue

                # Only analyse people
                if history[-1]["class_name"] != "person":
                    continue

                for i in range(1, len(history)):
                    previous = history[i - 1]["bbox"]
                    current = history[i]["bbox"]

                    prev_width = previous[2] - previous[0]
                    prev_height = previous[3] - previous[1]

                    curr_width = current[2] - current[0]
                    curr_height = current[3] - current[1]

                    if prev_height <= 0 or curr_height <= 0:
                        continue

                    prev_ratio = prev_width / prev_height
                    curr_ratio = curr_width / curr_height

                    height_drop = (
                        prev_height - curr_height
                    ) / prev_height

                    if curr_ratio > 1.3 and height_drop > 0.25:
                        fall_results.append(track_id)
                        break

            if fall_results:
                return (
                    "Possible fall-like movement detected for "
                    f"person track IDs: {fall_results}. "
                    "Please verify using the video."
                )

            return "No clear fall-like movement detected in the tracking data."

        # UNUSUAL MOVEMENT ANALYSIS
        if "anomaly" in q or "unusual movement" in q:
            unusual_tracks = []

            for track_id, history in self.tracks.items():
                if len(history) < 2:
                    continue

                for i in range(1, len(history)):
                    previous = history[i - 1]["bbox"]
                    current = history[i]["bbox"]

                    prev_cx = (previous[0] + previous[2]) / 2
                    prev_cy = (previous[1] + previous[3]) / 2

                    curr_cx = (current[0] + current[2]) / 2
                    curr_cy = (current[1] + current[3]) / 2

                    movement = (
                        (curr_cx - prev_cx) ** 2
                        + (curr_cy - prev_cy) ** 2
                    ) ** 0.5

                    box_size = (
                        (previous[2] - previous[0]) ** 2
                        + (previous[3] - previous[1]) ** 2
                    ) ** 0.5

                    if box_size > 0 and movement > 2.5 * box_size:
                        unusual_tracks.append(track_id)
                        break

            if unusual_tracks:
                return (
                    "Unusually large movement detected for "
                    f"track IDs: {unusual_tracks}. "
                    "Please verify the video."
                )

            return "No unusually large movement detected in the tracking data."
        
        # ==========================================
        # VISTA AI - SMART VIDEO QUERY MODULE
        # ==========================================

        # Prepare track information
        track_info = []

        for track_id, history in self.tracks.items():
            if not history:
                continue

            latest = history[-1]
            class_name = latest.get("class_name", "unknown")

            track_info.append({
                "id": track_id,
                "class": class_name,
                "history": history,
                "first": history[0].get("timestamp", 0),
                "last": latest.get("timestamp", 0),
                "confidence": latest.get("confidence", 0)
            })

        # Count objects by class
        class_counts = {}

        for track in track_info:
            name = track["class"]
            class_counts[name] = class_counts.get(name, 0) + 1

        # Calculate movement speed
        movement_data = []

        for track in track_info:
            history = track["history"]

            if len(history) < 2:
                continue

            total_distance = 0
            total_time = 0

            for i in range(1, len(history)):
                old = history[i - 1]
                new = history[i]

                old_box = old["bbox"]
                new_box = new["bbox"]

                old_x = (old_box[0] + old_box[2]) / 2
                old_y = (old_box[1] + old_box[3]) / 2

                new_x = (new_box[0] + new_box[2]) / 2
                new_y = (new_box[1] + new_box[3]) / 2

                distance = (
                    (new_x - old_x) ** 2 +
                    (new_y - old_y) ** 2
                ) ** 0.5

                time_gap = (
                    new.get("timestamp", 0) -
                    old.get("timestamp", 0)
                )

                if time_gap > 0:
                    total_distance += distance
                    total_time += time_gap

            if total_time > 0:
                movement_data.append({
                    "id": track["id"],
                    "class": track["class"],
                    "speed": total_distance / total_time,
                    "distance": total_distance,
                    "duration": total_time
                })

        # PEOPLE QUESTIONS
        if any(word in q for word in [
            "who appeared", "first person", "people appeared"
        ]):
            people = [
                t for t in track_info
                if t["class"] == "person"
            ]

            if not people:
                return "No person tracks found."

            first = min(people, key=lambda x: x["first"])

            return f"Person Track ID {first['id']} appeared first."

        # OBJECT COUNT QUESTIONS
        for name, count in class_counts.items():
            if (
                f"how many {name}" in q
                or f"number of {name}" in q
            ):
                return f"Detected {count} unique {name} track(s)."

        # TOTAL UNIQUE TRACKS
        if any(word in q for word in [
            "unique tracks", "total tracks", "track count"
        ]):
            return f"Total unique tracked objects: {len(track_info)}"

        # SLOWEST MOVING OBJECT / PERSON
        if any(word in q for word in [
            "moving slow", "slowest", "slowly"
        ]):
            candidates = [
                m for m in movement_data
                if m["class"] == "person"
            ]

            if not candidates:
                return "Insufficient timestamped person tracking data."

            slowest = min(candidates, key=lambda x: x["speed"])

            return (
                f"Slowest person: Track ID {slowest['id']}. "
                f"Estimated speed: {slowest['speed']:.2f} pixels/second."
            )

        # FASTEST MOVING PERSON
        if any(word in q for word in [
            "moving fast", "fastest", "fast moving"
        ]):
            candidates = [
                m for m in movement_data
                if m["class"] == "person"
            ]

            if not candidates:
                return "Insufficient timestamped person tracking data."

            fastest = max(candidates, key=lambda x: x["speed"])

            return (
                f"Fastest person: Track ID {fastest['id']}. "
                f"Estimated speed: {fastest['speed']:.2f} pixels/second."
            )

        # STATIONARY PERSON
        if any(word in q for word in [
            "stationary", "standing still", "not moving"
        ]):
            candidates = [
                m for m in movement_data
                if m["class"] == "person"
            ]

            stationary = [
                m for m in candidates
                if m["speed"] <= 5
            ]

            if stationary:
                ids = [str(m["id"]) for m in stationary]
                return "Possibly stationary person track IDs: " + ", ".join(ids)

            return "No person met the stationary movement threshold."

        # PERSON / OBJECT VISIBILITY DURATION
        if any(word in q for word in [
            "how long", "visible duration", "duration"
        ]):
            people = [
                t for t in track_info
                if t["class"] == "person"
            ]

            if not people:
                return "No person tracking data available."

            results = []

            for person in people:
                duration = person["last"] - person["first"]

                results.append(
                    f"Track {person['id']}: {duration:.2f} seconds"
                )

            return "Visibility duration: " + "; ".join(results)

        # FIRST AND LAST APPEARANCE
        if "appeared first" in q or "first detected" in q:
            if not track_info:
                return "No tracking data available."

            first = min(track_info, key=lambda x: x["first"])

            return (
                f"First detected: {first['class']} "
                f"(Track ID {first['id']}) at {first['first']:.2f} seconds."
            )

        if ("last appeared" in q or
            "most recently detected" in q or
            "detected most recently" in q or
            "which object was detected most recently" in q or
            "which object was last detected" in q or
            "last detected" in q or
            "detected last" in q or
            "which object appeared last" in q):
            if not track_info:
                return "No tracking data available."

            last = max(track_info, key=lambda x: x["last"])

            return (
                f"Most recently detected: {last['class']} "
                f"(Track ID {last['id']}) at {last['last']:.2f} seconds."
            )

        # DETECTION CONFIDENCE
        if "confidence" in q:
            if not track_info:
                return "No confidence data available."

            avg = sum(t["confidence"] for t in track_info) / len(track_info)

            return f"Average latest detection confidence: {avg:.3f}"

        # TRACK ID QUESTIONS
        if "track id" in q or "track number" in q:
            for track in track_info:
                if str(track["id"]) in q:
                    return (
                        f"Track ID {track['id']} is a "
                        f"{track['class']}. "
                        f"Observed in {len(track['history'])} frames."
                    )

            return "Please provide a valid Track ID from this video."

        # VIDEO TIME RANGE
        if "video duration" in q or "how long is the video" in q:
            timestamps = [
                frame.get("timestamp", 0)
                for frame in self.data
            ]

            if timestamps:
                return (
                    f"Available tracking timestamps span "
                    f"{max(timestamps) - min(timestamps):.2f} seconds."
                )

            return "Video timestamps are unavailable."

        return (
            "I can answer questions about people, objects, "
            "tracking IDs, movement and video frames. "
            "Please try another question."
        )


if __name__ == "__main__":

    print("\n===== VISTA AI QUESTION ANSWERING =====")

    if not os.path.exists("tracking_data.json"):
        print("Error: tracking_data.json not found!")
    else:
        qa = VISTAQuestionAnswer()

        print("Question Answering System Ready!")

        while True:
            question = input("\nAsk about your video (type exit to stop): ")

            if question.lower() == "exit":
                print("VISTA AI stopped.")
                break

            print("\nVISTA AI:", qa.answer(question))
