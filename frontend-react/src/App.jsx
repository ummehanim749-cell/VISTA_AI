
import { useEffect, useState } from "react";
import axios from "axios";
import {
  LayoutDashboard, Video, ScanEye, Activity,
  Brain, MessageSquare, Settings, Bell,
  RefreshCw, Users, AlertTriangle, Upload,
  Server, Wifi, WifiOff
} from "lucide-react";

const API = "https://fancy-bars-roll.loca.lt";
const pages = [
  ["Overview", LayoutDashboard],
  ["Video Analysis", Video],
  ["Object Tracking", ScanEye],
  ["Event Monitoring", Activity],
  ["Temporal Memory", Brain],
  ["Ask VISTA AI", MessageSquare],
  ["Settings", Settings]
];

export default function App() {
  const [page, setPage] = useState("Overview");
  const [health, setHealth] = useState("Checking");
  const [tracking, setTracking] = useState(null);
  const [events, setEvents] = useState(null);
  const [video, setVideo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [uploadStatus, setUploadStatus] = useState("");
  async function uploadVideo() {
  if (!video) {
    setUploadStatus("Please select a video first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", video);

  try {
    setUploadStatus("Uploading video...");
    const response = await axios.post(
      `${API}/upload-video`,
      formData
    );
    setUploadStatus(response.data.message);
  } catch (err) {
    setUploadStatus("Video upload failed.");
  }
}
  async function refreshData() {
    setLoading(true);
    setError("");

    try {
      const [h, t, e] = await Promise.all([
        axios.get(`${API}/health`),
        axios.get(`${API}/tracking`),
        axios.get(`${API}/events`)
      ]);

      setHealth("Online");
      setTracking(t.data);
      setEvents(e.data);
    } catch (err) {
      setHealth("Offline");
      setError("Cannot connect to FastAPI. Check that the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshData();
  }, []);

  const eventList = Array.isArray(events)
    ? events
    : Array.isArray(events?.events) ? events.events : [];

  const frames = Array.isArray(tracking)
    ? tracking
    : tracking?.data || tracking?.results || [];

  const detectionCount = frames.reduce(
    (total, frame) => total + (frame.tracks?.length || 0), 0
  );

  function content() {
    if (page === "Video Analysis") {
      return <section className="panel">
        <h2>Video Analysis Workspace</h2>
        <label className="upload-area">
          <Upload size={34}/>
          <h3>Select a video</h3>
          <p>Choose an MP4 or other video file</p>
          <input type="file" accept="video/*" hidden
            onChange={e => setVideo(e.target.files?.[0] || null)}/>
        </label>
        {video && <>
          <p>Selected: {video.name}</p>
          <video className="video" controls src={URL.createObjectURL(video)}/>
          <p className="muted">Local preview only. Backend video processing is not connected yet.</p>
        </>}
        <button
  className="upload-btn"
  onClick={uploadVideo}
  disabled={!video || loading}
>
  Upload Video
</button>

<p className="muted">{uploadStatus}</p>
      </section>;
    }

    if (page === "Object Tracking") {
      return <section className="panel">
        <h2>Object Tracking Results</h2>
        <p className="muted">Data retrieved from the tracking API.</p>
        <pre className="json-view">{JSON.stringify(tracking, null, 2) || "No data"}</pre>
      </section>;
    }

    if (page === "Event Monitoring") {
      return <section className="panel">
        <h2>Event Monitoring</h2>
        {eventList.length ? eventList.map((event, i) =>
          <div className="event-row" key={i}>
            <AlertTriangle/>
            <span>{event.event_type || event.type || JSON.stringify(event)}</span>
          </div>
        ) : <p className="muted">No event records available.</p>}
      </section>;
    }

    if (page === "Temporal Memory") {
      return <section className="panel">
        <h2>Temporal Memory</h2>
        <p>Memory module integration is the next development step.</p>
      </section>;
    }

    if (page === "Ask VISTA AI") {
      return <section className="panel">
        <h2>Ask VISTA AI</h2>
        <p>Question-answering API integration is the next development step.</p>
      </section>;
    }

    if (page === "Settings") {
      return <section className="panel">
        <h2>System Settings</h2>
        <p>Backend URL: {API}</p>
        <p>Backend status: {health}</p>
        <button className="action-btn" onClick={refreshData}>
          Test connection
        </button>
      </section>;
    }

    return <>
      <div className="stats-grid">
        <Stat icon={Users} label="Tracked detections" value={detectionCount}/>
        <Stat icon={Activity} label="Detected events" value={eventList.length}/>
        <Stat icon={Server} label="Backend status" value={health}/>
        <Stat icon={Video} label="Video selected" value={video ? "Yes" : "No"}/>
      </div>

      <div className="content-grid">
        <section className="panel">
          <h2>System Overview</h2>
          <p className="muted">VISTA AI backend connection</p>
          <p>{health === "Online" ? "● Backend connected" : "● Backend disconnected"}</p>
          {loading && <p>Loading data...</p>}
          {error && <p className="error">{error}</p>}
          <button className="action-btn" onClick={refreshData}>
            <RefreshCw size={16}/> Refresh data
          </button>
        </section>

        <section className="panel">
          <h2>Recent Events</h2>
          {eventList.slice(0, 5).map((event, i) =>
            <div className="event-row" key={i}>
              <AlertTriangle size={17}/>
              {event.event_type || event.type || "Detected event"}
            </div>
          )}
          {!eventList.length && <p className="muted">No events loaded.</p>}
        </section>
      </div>
    </>;
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand">
        <ScanEye size={30}/>
        <div><h2>VISTA AI</h2><small>VISUAL INTELLIGENCE</small></div>
      </div>

      <p className="nav-label">WORKSPACE</p>
      <nav>
        {pages.map(([name, Icon]) =>
          <button key={name}
            className={`nav-item ${page === name ? "active" : ""}`}
            onClick={() => setPage(name)}>
            <Icon size={19}/>{name}
          </button>
        )}
      </nav>

      <div className="sidebar-footer">
        {health === "Online" ? <Wifi size={16}/> : <WifiOff size={16}/>}
        Backend {health}
      </div>
    </aside>

    <main className="main-area">
      <header className="topbar">
        <div>
          <small>VISTA AI / WORKSPACE</small>
          <h1>{page}</h1>
        </div>
        <div className="top-actions">
          <span>{health}</span>
          <button className="icon-btn" onClick={refreshData}>
            <RefreshCw/>
          </button>
          <Bell/>
        </div>
      </header>
      <div className="page-content">{content()}</div>
    </main>
  </div>;
}

function Stat({ icon: Icon, label, value }) {
  return <section className="stat-card">
    <Icon size={25}/>
    <p>{label}</p>
    <h2>{value}</h2>
  </section>;
}
