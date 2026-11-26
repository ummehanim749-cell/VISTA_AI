
import json
from memory import TemporalMemory

def main():
    memory = TemporalMemory()

    with open("tracking_data.json", "r") as file:
        data = json.load(file)

    print("\n===== VISTA AI INTEGRATION =====")

    memory.process_frames(data)

    print("Total frames:", len(data))

    summary = memory.get_summary()

    print("\n===== TEMPORAL MEMORY RESULTS =====")

    for track_id, details in summary.items():
        print("\nTrack ID:", track_id)
        print("Frames detected:", details["frames_detected"])
        print("Horizontal movement:", details["movement_x"])
        print("Vertical movement:", details["movement_y"])

    print("\n===== TRACK GAP ANALYSIS =====")
    gaps = memory.detect_missing_frames()
    for track_id, frames in gaps.items():

        print(f"Track {track_id}: {len(frames)} missing frames")
    print("\nINTEGRATION TEST COMPLETED!")

if __name__ == "__main__":
    main()
