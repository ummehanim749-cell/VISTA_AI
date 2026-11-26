import gradio as gr
import requests

def analyze_video(video_path):
    if video_path is None:
        return (
            "Please upload a video first.",
            None, None, None, None
        )

    try:
        tracking_response = requests.get(
            "http://127.0.0.1:8000/tracking",
            timeout=30
        )
        events_response = requests.get(
            "http://127.0.0.1:8000/events",
            timeout=30
        )

        tracking_response.raise_for_status()
        events_response.raise_for_status()

        tracking_data = tracking_response.json()
        events_data = events_response.json()

        anomaly_data = [
            event for event in events_data
            if event.get("event_type") == "sudden_movement"
        ]

        return (
            "Backend connected! Tracking and event data loaded.",
            video_path,
            tracking_data,
            events_data,
            anomaly_data
        )

    except requests.RequestException as error:
        return (
            f"Backend connection failed: {error}",
            None, None, None, None
        )


with gr.Blocks(
    theme=gr.themes.Soft(),
    title="VISTA-AI"
) as demo:

    gr.Markdown("""
    # VISTA-AI
    ### Visual Intelligence, Spatial Tracking & Analysis
    Open-World Video Intelligence Dashboard
    """)

    gr.Markdown("## 1. Upload CCTV Video")

    video_input = gr.Video(
        label="Select Video",
        sources=["upload"],
        format="mp4"
    )

    analyze_button = gr.Button(
        "Analyze Video",
        variant="primary"
    )

    status = gr.Textbox(
        label="Processing Status",
        interactive=False
    )

    gr.Markdown("## 2. Annotated Video")

    annotated_video = gr.Video(
        label="AI Processed Video",
        interactive=False
    )

    gr.Markdown("## 3. Object Tracking")

    tracking_results = gr.JSON(
        label="Tracking JSON"
    )

    gr.Markdown("## 4. Event Timeline")

    event_results = gr.JSON(
        label="Event Analysis"
    )

    gr.Markdown("## 5. Anomaly Analysis & Evidence")

    anomaly_results = gr.JSON(
        label="Reasoning and Evidence"
    )

    analyze_button.click(
        fn=analyze_video,
        inputs=video_input,
        outputs=[
            status,
            annotated_video,
            tracking_results,
            event_results,
            anomaly_results
        ]
    )

if __name__ == "__main__":
    demo.launch()