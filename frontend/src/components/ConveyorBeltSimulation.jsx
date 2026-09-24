import React, { useState, useEffect, useRef } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const MATERIAL_ICONS = {
  plastic: '🍾',
  glass: '🫙',
  metal: '🥫',
  paper: '📦',
  organic: '🍏',
  review: '❓',
  unknown: '❓',
};

const MATERIAL_COLORS = {
  plastic: 'border-blue-500 bg-blue-50 text-blue-700',
  glass: 'border-amber-500 bg-amber-50 text-amber-700',
  metal: 'border-slate-500 bg-slate-100 text-slate-700',
  paper: 'border-yellow-500 bg-yellow-50 text-yellow-700',
  organic: 'border-emerald-500 bg-emerald-50 text-emerald-700',
  review: 'border-rose-500 bg-rose-50 text-rose-700',
  unknown: 'border-slate-400 bg-slate-100 text-slate-600',
};

const STREAM_STYLES = {
  plastic: { border: 'border-blue-500', bg: 'bg-blue-500/20', text: 'text-blue-700', badge: 'bg-blue-600 text-white' },
  glass: { border: 'border-amber-500', bg: 'bg-amber-500/20', text: 'text-amber-700', badge: 'bg-amber-600 text-white' },
  metal: { border: 'border-slate-500', bg: 'bg-slate-500/20', text: 'text-slate-700', badge: 'bg-slate-700 text-white' },
  paper: { border: 'border-yellow-500', bg: 'bg-yellow-500/20', text: 'text-yellow-800', badge: 'bg-yellow-600 text-white' },
  organic: { border: 'border-emerald-500', bg: 'bg-emerald-500/20', text: 'text-emerald-700', badge: 'bg-emerald-600 text-white' },
  review: { border: 'border-rose-500', bg: 'bg-rose-500/25', text: 'text-rose-700', badge: 'bg-rose-600 text-white' },
};

export default function ConveyorBeltSimulation({ onSessionSaved }) {
  // Mode: 'live' (real-time virtual conveyor) vs 'video' (recorded video stream analysis)
  const [activeMode, setActiveMode] = useState('live');

  // Live simulation telemetry state
  const [telemetry, setTelemetry] = useState(null);
  const [simState, setSimState] = useState('RUNNING');
  const [simSpeed, setSimSpeed] = useState(1.0);
  const [loadingAction, setLoadingAction] = useState(false);

  // Video stream upload state
  const [videoFile, setVideoFile] = useState(null);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState(null);
  const [videoInputMass, setVideoInputMass] = useState(100.0);
  const [analyzingVideo, setAnalyzingVideo] = useState(false);
  const [videoResult, setVideoResult] = useState(null);
  const [videoError, setVideoError] = useState(null);
  const [selectedFrameIdx, setSelectedFrameIdx] = useState(0);
  const [hoveredObjectId, setHoveredObjectId] = useState(null);

  const eventLogEndRef = useRef(null);

  // Fetch telemetry snapshot
  const fetchTelemetry = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/conveyor/telemetry`);
      if (res.ok) {
        const data = await res.json();
        setTelemetry(data);
        setSimState(data.simulation_state);
        setSimSpeed(data.conveyor_speed);
      }
    } catch (err) {
      console.error('Failed to fetch conveyor telemetry:', err);
    }
  };

  // Step simulation every 700ms when activeMode is 'live' and running
  useEffect(() => {
    fetchTelemetry();

    if (activeMode !== 'live' || simState !== 'RUNNING') return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/conveyor/step`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ delta_time: 1.0 }),
        });
        if (res.ok) {
          const data = await res.json();
          setTelemetry(data);
          setSimState(data.simulation_state);
          setSimSpeed(data.conveyor_speed);
        }
      } catch (err) {
        console.error('Conveyor step error:', err);
      }
    }, 700);

    return () => clearInterval(interval);
  }, [activeMode, simState]);

  // Auto-scroll event logs
  useEffect(() => {
    if (eventLogEndRef.current) {
      eventLogEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [telemetry?.diverter_event_logs]);

  // Simulation controls
  const handleControl = async (action, speed = 1.0) => {
    try {
      setLoadingAction(true);
      const res = await fetch(`${API_BASE_URL}/api/conveyor/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, speed }),
      });
      if (res.ok) {
        const data = await res.json();
        setTelemetry(data);
        setSimState(data.simulation_state);
        setSimSpeed(data.conveyor_speed);
      }
    } catch (err) {
      console.error(`Conveyor control error (${action}):`, err);
    } finally {
      setLoadingAction(false);
    }
  };

  // Video file upload handler
  const handleVideoFileChange = (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('video/') && !/\.(mp4|webm|avi|mov|mkv)$/i.test(file.name)) {
      setVideoError('Please select a valid video file (.mp4, .webm, .avi, .mov).');
      setVideoFile(null);
      setVideoPreviewUrl(null);
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setVideoError('Selected video exceeds 50MB file size limit.');
      setVideoFile(null);
      setVideoPreviewUrl(null);
      return;
    }

    if (file.size === 0) {
      setVideoError('Selected video file is empty (0 bytes).');
      setVideoFile(null);
      setVideoPreviewUrl(null);
      return;
    }

    setVideoError(null);
    setVideoFile(file);
    setVideoPreviewUrl(URL.createObjectURL(file));
    setVideoResult(null);
    setSelectedFrameIdx(0);
  };

  // Video analysis submit
  const handleAnalyzeVideo = async (e) => {
    if (e) e.preventDefault();
    if (!videoFile) {
      setVideoError('Please choose a video file first.');
      return;
    }

    setAnalyzingVideo(true);
    setVideoError(null);

    const formData = new FormData();
    formData.append('file', videoFile);
    formData.append('input_mass_kg', videoInputMass);

    try {
      const res = await fetch(`${API_BASE_URL}/api/video/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        let msg = `Video analysis failed (HTTP ${res.status})`;
        try {
          const errData = await res.json();
          if (errData && errData.detail) msg = errData.detail;
        } catch {
          // ignore
        }
        throw new Error(msg);
      }

      const data = await res.json();
      setVideoResult(data);
      setSelectedFrameIdx(0);
      if (onSessionSaved) onSessionSaved();
    } catch (err) {
      console.error('Video analysis failed:', err);
      setVideoError(err.message || 'Error processing video stream.');
    } finally {
      setAnalyzingVideo(false);
    }
  };

  const streamCounters = telemetry?.stream_counters || {
    plastic: 0,
    glass: 0,
    metal: 0,
    paper: 0,
    organic: 0,
    review: 0,
  };

  const activeItems = telemetry?.active_belt_items || [];
  const currentObj = telemetry?.current_inspected_object || {};

  // For video keyframe inspector
  const currentKeyframe = videoResult?.conveyor_timeline?.[selectedFrameIdx] || null;

  return (
    <div className="space-y-8">
      {/* Top Banner / Mode Toggle */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl">🏭</span>
            <h2 className="text-xl font-extrabold text-slate-900">
              Virtual Conveyor Belt &amp; Video Stream Simulation
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Continuous multi-waste sorting: Infeed ➔ AI Optical Sensor ➔ Object Tracking ➔ Contamination ➔ 6 Diverter Lanes
          </p>
        </div>

        {/* Model Architecture & Mode Badges */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            AI MODEL: REAL_YOLO (ONNX)
          </span>

          {/* Mode Selector */}
          <div className="flex items-center bg-slate-100 p-1 rounded-lg">
            <button
              type="button"
              onClick={() => setActiveMode('live')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center gap-1.5 ${
                activeMode === 'live'
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <span>🔄</span>
              <span>Live Virtual Conveyor</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveMode('video')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center gap-1.5 ${
                activeMode === 'video'
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <span>🎥</span>
              <span>Video Stream Analysis</span>
            </button>
          </div>
        </div>
      </div>

      {/* Industrial Software Simulation Notice */}
      <div className="p-3.5 bg-slate-900 text-slate-200 rounded-xl text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-sm border border-slate-800">
        <div className="flex items-center gap-2">
          <span className="text-amber-400 font-bold">⚙️ SOFTWARE SORTING SIMULATION:</span>
          <span>
            Modeling automated optical sorting facilities with continuous 1.2 m/s belt dynamics, optical laser scanning, and pneumatic ejection triggers.
          </span>
        </div>
        <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] text-slate-400 font-mono self-start sm:self-auto shrink-0">
          PLC / MODBUS / MQTT READY
        </span>
      </div>

      {/* ================================================================= */}
      {/* MODE 1: LIVE VIRTUAL CONVEYOR SIMULATION                          */}
      {/* ================================================================= */}
      {activeMode === 'live' && (
        <div className="space-y-6">
          {/* Conveyor Architecture Diagram Banner */}
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center font-mono text-xs text-slate-400 space-y-1 shadow-inner select-none">
            <div className="text-cyan-400 font-bold tracking-wider">AI OPTICAL CAMERA</div>
            <div className="text-slate-600">↓</div>
            <div className="text-slate-200 font-bold tracking-widest text-[13px]">
              ========================================================================
              <br />
              SOFTWARE-SIMULATED CONVEYOR BELT (VIRTUAL OPTICAL SORTING)
              <br />
              ========================================================================
            </div>
            <div className="flex justify-around text-[11px] pt-1 font-semibold">
              <span className="text-blue-400">Plastic (● → Air Jet)</span>
              <span className="text-amber-400">Glass (● → Paddle)</span>
              <span className="text-slate-300">Metal (● → Eddy)</span>
              <span className="text-yellow-400">Paper (● → Vacuum)</span>
              <span className="text-emerald-400">Organic (● → Bio)</span>
              <span className="text-rose-400">Manual Review (● → QC)</span>
            </div>
          </div>

          {/* Controls & Counter Stats Bar */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 items-center">
            {/* Simulation Controls */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-2 lg:col-span-2">
              {simState === 'RUNNING' ? (
                <button
                  type="button"
                  onClick={() => handleControl('pause')}
                  disabled={loadingAction}
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs rounded-lg transition-colors flex items-center gap-1.5 shadow-sm"
                >
                  <span>⏸️</span>
                  <span>Pause Belt</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => handleControl('start')}
                  disabled={loadingAction}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-lg transition-colors flex items-center gap-1.5 shadow-sm"
                >
                  <span>▶️</span>
                  <span>Start Belt</span>
                </button>
              )}

              <button
                type="button"
                onClick={() => handleControl('reset')}
                disabled={loadingAction}
                className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-lg transition-colors"
              >
                🔄 Reset
              </button>

              <div className="h-6 w-px bg-slate-200 mx-1" />

              <span className="text-xs font-semibold text-slate-500">Speed:</span>
              {[0.5, 1.0, 2.0].map((spd) => (
                <button
                  key={spd}
                  type="button"
                  onClick={() => handleControl('set_speed', spd)}
                  className={`px-2.5 py-1 text-xs rounded font-bold transition-all ${
                    simSpeed === spd
                      ? 'bg-slate-900 text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {spd}x
                </button>
              ))}

              <div className="ml-auto flex items-center gap-1.5">
                <span
                  className={`w-2.5 h-2.5 rounded-full ${
                    simState === 'RUNNING' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
                  }`}
                />
                <span className="text-xs font-bold text-slate-700">{simState}</span>
              </div>
            </div>

            {/* Total Processed Stat Card */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  Total Objects Processed
                </span>
                <p className="text-2xl font-black text-slate-900 mt-0.5">
                  {telemetry?.total_objects_processed || 0}
                </p>
              </div>
              <span className="text-3xl">📦</span>
            </div>

            {/* Simulated Belt Speed */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  Conveyor Velocity
                </span>
                <p className="text-xl font-bold text-indigo-600 mt-0.5 font-mono">
                  {(1.2 * simSpeed).toFixed(1)} m/s
                </p>
              </div>
              <span className="text-xs bg-indigo-50 text-indigo-700 font-bold px-2 py-1 rounded">
                30 FPS CAM
              </span>
            </div>
          </div>

          {/* 6 Virtual Sorting Lanes Counter Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-blue-50/70 border border-blue-200 p-3 rounded-xl flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-blue-700 uppercase">Plastic Lane</span>
                <p className="text-xl font-black text-blue-900 mt-0.5">{streamCounters.plastic}</p>
                <span className="text-[9px] text-blue-500 font-mono">Air Jet Ejector</span>
              </div>
              <span className="text-2xl">🍾</span>
            </div>

            <div className="bg-amber-50/70 border border-amber-200 p-3 rounded-xl flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-amber-700 uppercase">Glass Lane</span>
                <p className="text-xl font-black text-amber-900 mt-0.5">{streamCounters.glass}</p>
                <span className="text-[9px] text-amber-500 font-mono">Mechanical Paddle</span>
              </div>
              <span className="text-2xl">🫙</span>
            </div>

            <div className="bg-slate-100 border border-slate-300 p-3 rounded-xl flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-slate-700 uppercase">Metal Lane</span>
                <p className="text-xl font-black text-slate-900 mt-0.5">{streamCounters.metal}</p>
                <span className="text-[9px] text-slate-500 font-mono">Eddy Current</span>
              </div>
              <span className="text-2xl">🥫</span>
            </div>

            <div className="bg-yellow-50/70 border border-yellow-200 p-3 rounded-xl flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-yellow-700 uppercase">Paper Lane</span>
                <p className="text-xl font-black text-yellow-900 mt-0.5">{streamCounters.paper}</p>
                <span className="text-[9px] text-yellow-500 font-mono">Vacuum Diverter</span>
              </div>
              <span className="text-2xl">📦</span>
            </div>

            <div className="bg-emerald-50/70 border border-emerald-200 p-3 rounded-xl flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-emerald-700 uppercase">Organic Lane</span>
                <p className="text-xl font-black text-emerald-900 mt-0.5">{streamCounters.organic}</p>
                <span className="text-[9px] text-emerald-500 font-mono">Bio Recovery</span>
              </div>
              <span className="text-2xl">🍏</span>
            </div>

            <div className="bg-rose-50/70 border border-rose-200 p-3 rounded-xl flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-rose-700 uppercase">Manual QC</span>
                <p className="text-xl font-black text-rose-900 mt-0.5">{streamCounters.review}</p>
                <span className="text-[9px] text-rose-500 font-mono">QC Conveyor</span>
              </div>
              <span className="text-2xl">❓</span>
            </div>
          </div>

          {/* MAIN VIRTUAL CONVEYOR BELT VISUALIZER */}
          <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 shadow-xl space-y-4">
            {/* Stage Indicators */}
            <div className="grid grid-cols-4 text-center text-xs font-mono font-bold border-b border-slate-800 pb-3">
              <div className="text-slate-400">
                <span>STAGE 1: MIXED INFEED</span>
                <span className="block text-[10px] text-slate-500 font-sans">0% — 25%</span>
              </div>
              <div className="text-cyan-400">
                <span>STAGE 2: AI OPTICAL SCAN</span>
                <span className="block text-[10px] text-slate-500 font-sans">25% — 55%</span>
              </div>
              <div className="text-amber-400">
                <span>STAGE 3: DIVERTER DECISION</span>
                <span className="block text-[10px] text-slate-500 font-sans">Trigger @ 65%</span>
              </div>
              <div className="text-emerald-400">
                <span>STAGE 4: 6 SORTING LANES</span>
                <span className="block text-[10px] text-slate-500 font-sans">90% — 100%</span>
              </div>
            </div>

            {/* Interactive Belt Viewport */}
            <div className="relative w-full h-44 rounded-xl overflow-hidden border-2 border-slate-700 bg-slate-900 shadow-inner">
              {/* Conveyor Belt Textured Surface with CSS Animation */}
              <div
                className={`absolute inset-0 conveyor-belt-surface opacity-60 ${
                  simState === 'PAUSED' ? 'paused' : ''
                }`}
              />

              {/* Optical Inspection Scanning Line at 25% */}
              <div className="absolute top-0 bottom-0 left-[25%] w-0.5 bg-cyan-400 shadow-[0_0_12px_#22d3ee] z-10 flex flex-col justify-between items-center py-1">
                <span className="bg-cyan-950 text-cyan-300 text-[9px] font-mono font-bold px-1 rounded border border-cyan-500/40">
                  CAMERA
                </span>
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                <span className="text-[9px] text-cyan-300 font-mono">X=25</span>
              </div>

              {/* Diverter Trigger Line at 65% */}
              <div className="absolute top-0 bottom-0 left-[65%] w-0.5 bg-amber-400 shadow-[0_0_12px_#f59e0b] z-10 flex flex-col justify-between items-center py-1">
                <span className="bg-amber-950 text-amber-300 text-[9px] font-mono font-bold px-1 rounded border border-amber-500/40">
                  DIVERTER
                </span>
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                <span className="text-[9px] text-amber-300 font-mono">X=65</span>
              </div>

              {/* 6 Destination Chutes at right edge (90%-100%) */}
              <div className="absolute top-0 bottom-0 right-0 w-[14%] bg-slate-900/90 border-l border-slate-700 z-10 p-1 flex flex-col justify-around text-[9px] font-mono">
                <div className="text-blue-400 flex items-center justify-between">
                  <span>AIR JET</span>
                  <span>1</span>
                </div>
                <div className="text-amber-400 flex items-center justify-between">
                  <span>PADDLE</span>
                  <span>2</span>
                </div>
                <div className="text-slate-300 flex items-center justify-between">
                  <span>EDDY</span>
                  <span>3</span>
                </div>
                <div className="text-yellow-400 flex items-center justify-between">
                  <span>VACUUM</span>
                  <span>4</span>
                </div>
                <div className="text-emerald-400 flex items-center justify-between">
                  <span>BIO</span>
                  <span>5</span>
                </div>
                <div className="text-rose-400 flex items-center justify-between">
                  <span>QC</span>
                  <span>6</span>
                </div>
              </div>

              {/* Moving Waste Objects on Belt */}
              {activeItems.map((item) => {
                const icon = MATERIAL_ICONS[item.material] || '📦';
                const isInspected = item.x >= 25 && item.x <= 75;

                return (
                  <div
                    key={item.object_id}
                    className={`absolute top-1/2 -translate-y-1/2 transition-all duration-300 z-20 flex flex-col items-center cursor-pointer`}
                    style={{ left: `${Math.min(90, item.x)}%` }}
                  >
                    {/* Floating Item Card */}
                    <div
                      className={`px-2 py-1 rounded-lg border shadow-lg bg-white flex items-center gap-1.5 transition-transform ${
                        isInspected ? 'scale-110 ring-2 ring-cyan-400 shadow-cyan-500/20' : 'scale-95'
                      }`}
                    >
                      <span className="text-base">{icon}</span>
                      <div className="leading-tight text-left">
                        <div className="text-[10px] font-bold text-slate-900 capitalize">
                          {item.material}
                        </div>
                        <div className="text-[9px] font-mono text-slate-500">
                          {Math.round(item.confidence * 100)}% conf
                        </div>
                      </div>
                    </div>

                    {/* Stage Sub-tag */}
                    <span className="mt-1 text-[8px] font-mono font-bold text-slate-300 bg-slate-900/80 px-1 rounded">
                      {item.object_id}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Conveyor Legend Bar */}
            <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-cyan-400" /> Optical Sorter (X=25)
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-amber-400" /> Pneumatic Diverter (X=65)
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" /> 6 Lane Diverters (X=95)
                </span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">
                Items dynamically advance based on selected belt velocity multiplier.
              </span>
            </div>
          </div>

          {/* Current Inspected Object & Real-time Diverter Event Console */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
            {/* Active Inspected Object Card */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                <div>
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <span>🔍</span> Current Inspected Object Telemetry
                  </h3>
                  <p className="text-xs text-slate-500">
                    Real-time optical sensor readings as item passes scanning laser
                  </p>
                </div>
                {currentObj.object_id && (
                  <span className="px-2.5 py-1 bg-indigo-50 text-indigo-700 font-mono text-xs font-bold rounded-lg border border-indigo-200">
                    {currentObj.object_id}
                  </span>
                )}
              </div>

              {currentObj.object_id ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Material</span>
                      <p className="text-sm font-bold text-slate-800 capitalize mt-0.5">
                        {currentObj.material}
                      </p>
                    </div>

                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Confidence</span>
                      <p className="text-sm font-bold text-indigo-600 mt-0.5">
                        {Math.round(currentObj.confidence * 100)}%
                      </p>
                    </div>

                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Contamination</span>
                      <p className="text-sm font-bold text-amber-600 mt-0.5">
                        {currentObj.contamination_score}%
                      </p>
                    </div>

                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Est. Yield</span>
                      <p className="text-sm font-bold text-emerald-600 mt-0.5">
                        {currentObj.recycling_yield}%
                      </p>
                    </div>
                  </div>

                  {/* Destination Chute & Route */}
                  <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-500">Target Sorting Lane:</span>
                      <span className="font-bold text-slate-900">{currentObj.lane_name}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-500">Diverter Actuator:</span>
                      <span className="font-mono text-indigo-600 font-bold">{currentObj.diverter_bin}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-500">Processing Route:</span>
                      <span className="px-2 py-0.5 bg-white text-slate-800 font-mono font-bold rounded border text-[10px]">
                        {currentObj.processing_route}
                      </span>
                    </div>
                  </div>

                  {/* Operational Recommendation */}
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs space-y-1">
                    <span className="font-bold text-emerald-900">
                      💡 Route Recommendation: {currentObj.recommendation}
                    </span>
                    <p className="text-emerald-700 text-[11px]">{currentObj.recommendation_reason}</p>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-slate-400 text-xs">
                  Awaiting next waste object to pass optical camera sensor...
                </div>
              )}
            </div>

            {/* Real-time Diverter Event Log Console */}
            <div className="bg-slate-950 p-6 rounded-xl border border-slate-800 shadow-sm space-y-3 flex flex-col h-[380px]">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                  <h3 className="text-sm font-bold text-slate-100 font-mono">
                    REAL-TIME CONVEYOR DIVERTER LOG
                  </h3>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">20 EVENTS BUFFER</span>
              </div>

              {/* Event Log Output */}
              <div className="flex-1 overflow-y-auto space-y-1.5 font-mono text-xs text-slate-300 pr-2">
                {telemetry?.diverter_event_logs && telemetry.diverter_event_logs.length > 0 ? (
                  telemetry.diverter_event_logs.map((logMsg, idx) => (
                    <div
                      key={idx}
                      className="p-1.5 rounded bg-slate-900/60 border border-slate-800/80 leading-relaxed text-[11px]"
                    >
                      <span className="text-cyan-400 font-bold">{logMsg.slice(0, 8)}</span>{' '}
                      <span className="text-slate-200">{logMsg.slice(8)}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-slate-500 text-center py-10 text-xs">
                    Initializing real-time event logs...
                  </div>
                )}
                <div ref={eventLogEndRef} />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ================================================================= */}
      {/* MODE 2: RECORDED VIDEO STREAM ANALYSIS                            */}
      {/* ================================================================= */}
      {activeMode === 'video' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-5">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Recorded Video Stream Analysis</h3>
              <p className="text-xs text-slate-500 mt-1">
                Upload a conveyor video (.mp4, .webm, .avi, .mov). The CV engine samples frames at 2 FPS, detects waste items via YOLO11n ONNX, tracks unique physical objects across frames with persistent IDs, and calculates aggregated yield.
              </p>
            </div>

            {videoError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
                {videoError}
              </div>
            )}

            <form onSubmit={handleAnalyzeVideo} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start">
                <div className="md:col-span-2 space-y-3">
                  <label className="block text-xs font-bold text-slate-700">
                    Select Conveyor Video File
                  </label>
                  <input
                    type="file"
                    accept="video/*,.mp4,.webm,.avi,.mov"
                    onChange={handleVideoFileChange}
                    className="w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-900 file:text-white hover:file:bg-slate-800 cursor-pointer border border-slate-200 rounded-lg p-1.5"
                  />

                  {/* Video Player Preview if uploaded */}
                  {videoPreviewUrl && (
                    <div className="mt-2 rounded-xl overflow-hidden border border-slate-200 bg-black">
                      <video
                        src={videoPreviewUrl}
                        controls
                        className="w-full max-h-56 object-contain"
                      />
                    </div>
                  )}
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">
                      Conveyor Batch Input Mass (kg)
                    </label>
                    <input
                      type="number"
                      min="1"
                      step="1"
                      value={videoInputMass}
                      onChange={(e) => setVideoInputMass(parseFloat(e.target.value) || 100.0)}
                      className="w-full text-xs border border-slate-200 rounded-lg p-2.5 font-mono text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-900"
                    />
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                    <span className="font-bold text-slate-800">⚡ Adaptive Keyframe Sampling</span>
                    <p className="text-slate-500 text-[11px]">
                      Videos are sampled at 2 FPS keyframes to balance real-time tracking accuracy with low CPU starvation.
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                <span className="text-[11px] text-slate-400">
                  Supported formats: MP4, WEBM, AVI, MOV (Max 50MB)
                </span>
                <button
                  type="submit"
                  disabled={!videoFile || analyzingVideo}
                  className="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-400 text-white font-bold text-xs rounded-lg transition-colors flex items-center gap-2 shadow-sm"
                >
                  {analyzingVideo ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Sampling Frames &amp; Tracking Objects...</span>
                    </>
                  ) : (
                    <>
                      <span>🚀</span>
                      <span>Run Video Stream Analysis</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Video Analysis Result Display */}
          {videoResult && (
            <div className="space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">
                    Sampled Keyframes
                  </span>
                  <p className="text-2xl font-black text-slate-900 mt-0.5">
                    {videoResult.total_frames_sampled}
                  </p>
                  <span className="text-[10px] text-slate-500 font-mono">
                    {videoResult.video_metadata?.duration_seconds}s video @ 2 FPS
                  </span>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">
                    Unique Objects Tracked
                  </span>
                  <p className="text-2xl font-black text-indigo-600 mt-0.5">
                    {videoResult.unique_objects_count}
                  </p>
                  <span className="text-[10px] text-slate-500">Persistent IDs across frames</span>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">
                    Recoverable Mass
                  </span>
                  <p className="text-2xl font-black text-teal-600 mt-0.5 font-mono">
                    {videoResult.optimization?.recoverable_mass_kg} kg
                  </p>
                  <span className="text-[10px] text-slate-500">
                    Out of {videoResult.optimization?.input_mass_kg} kg
                  </span>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">
                    Batch Recycling Yield
                  </span>
                  <p className="text-2xl font-black text-emerald-600 mt-0.5">
                    {videoResult.optimization?.recycling_yield}%
                  </p>
                  <span className="text-[10px] text-slate-500">
                    Quality: {videoResult.optimization?.quality_score}/100
                  </span>
                </div>
              </div>

              {/* Material Distribution Breakdown Bar */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Material Stream Distribution across Video
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                  {Object.entries(videoResult.virtual_sorting?.streams || {}).map(([sKey, sVal]) => (
                    <div
                      key={sKey}
                      className="p-2.5 rounded-lg border border-slate-200 bg-slate-50 flex items-center justify-between text-xs"
                    >
                      <div>
                        <span className="font-bold capitalize text-slate-800">{sKey}</span>
                        <p className="text-slate-500 font-mono text-[11px]">{sVal.count} items ({sVal.percentage}%)</p>
                      </div>
                      <span className="text-lg">{MATERIAL_ICONS[sKey] || '📦'}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Interactive Frame-by-Frame Inspector & Overlay */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
                {/* Left: Frame Selector Reel */}
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center justify-between">
                    <span>🎞️ Keyframe Selector</span>
                    <span className="text-[10px] text-slate-400 font-normal">
                      Click frame to inspect
                    </span>
                  </h4>
                  <div className="max-h-[460px] overflow-y-auto space-y-2 pr-1">
                    {videoResult.conveyor_timeline?.map((fItem, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => setSelectedFrameIdx(idx)}
                        className={`w-full text-left p-2.5 rounded-lg border transition-all flex items-center justify-between text-xs ${
                          selectedFrameIdx === idx
                            ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                            : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
                        }`}
                      >
                        <div>
                          <div className="font-mono font-bold">
                            Frame #{fItem.frame_index} ({fItem.timestamp}s)
                          </div>
                          <div className={`text-[10px] ${selectedFrameIdx === idx ? 'text-slate-300' : 'text-slate-500'}`}>
                            {fItem.active_objects_count} active object(s)
                          </div>
                        </div>
                        <span className="text-xs">➔</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Right: Selected Keyframe Image with Bounding Box Overlays */}
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm lg:col-span-2 space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">
                        Frame #{currentKeyframe?.frame_index || 0} Optical Vision Overlay ({currentKeyframe?.timestamp}s)
                      </h4>
                      <p className="text-xs text-slate-500">
                        Computer vision detections and tracked physical IDs
                      </p>
                    </div>
                    <span className="px-2 py-0.5 bg-indigo-50 text-indigo-700 font-mono text-xs font-bold rounded border border-indigo-200">
                      {currentKeyframe?.objects?.length || 0} Objects Detected
                    </span>
                  </div>

                  {/* Frame Image Container with Bounding Boxes */}
                  <div className="relative rounded-xl overflow-hidden border border-slate-800 bg-slate-950 flex items-center justify-center min-h-[260px] max-h-[420px]">
                    {currentKeyframe?.image_base64 ? (
                      <img
                        src={currentKeyframe.image_base64}
                        alt="Current sampled conveyor frame"
                        className="w-full h-auto max-h-[420px] object-contain block select-none"
                      />
                    ) : (
                      <div className="p-10 text-slate-500 text-xs">No image data for frame</div>
                    )}

                    {/* Bounding Box Overlays */}
                    {currentKeyframe?.objects?.map((obj) => {
                      const streamKey = (obj.stream || 'review').toLowerCase();
                      const style = STREAM_STYLES[streamKey] || STREAM_STYLES.review;
                      const norm = obj.bbox?.normalized || { x: 10, y: 10, width: 30, height: 30 };
                      const isHovered = hoveredObjectId === obj.object_id;

                      return (
                        <div
                          key={obj.object_id}
                          onMouseEnter={() => setHoveredObjectId(obj.object_id)}
                          onMouseLeave={() => setHoveredObjectId(null)}
                          className={`absolute border-2 rounded transition-all cursor-pointer ${
                            style.border
                          } ${style.bg} ${isHovered ? 'ring-2 ring-white scale-105 z-30' : 'z-20'}`}
                          style={{
                            left: `${norm.x}%`,
                            top: `${norm.y}%`,
                            width: `${norm.width}%`,
                            height: `${norm.height}%`,
                          }}
                        >
                          <span
                            className={`absolute -top-5 left-0 px-1.5 py-0.2 rounded text-[9px] font-mono font-bold whitespace-nowrap shadow-sm ${style.badge}`}
                          >
                            {obj.object_id} | {obj.material} ({Math.round(obj.confidence * 100)}%)
                          </span>
                        </div>
                      );
                    })}
                  </div>

                  {/* Tracked Objects Legend in Frame */}
                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    {currentKeyframe?.objects?.map((obj) => (
                      <div
                        key={obj.object_id}
                        onMouseEnter={() => setHoveredObjectId(obj.object_id)}
                        onMouseLeave={() => setHoveredObjectId(null)}
                        className={`px-2.5 py-1 rounded-lg border text-xs font-mono font-bold cursor-pointer transition-all ${
                          hoveredObjectId === obj.object_id
                            ? 'bg-slate-900 text-white shadow-sm'
                            : 'bg-slate-50 text-slate-700 border-slate-200'
                        }`}
                      >
                        {obj.object_id}: {obj.material.toUpperCase()} ({Math.round(obj.confidence * 100)}%) ➔ {obj.stream} lane
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Video Diverter Event Log */}
              <div className="bg-slate-950 p-6 rounded-xl border border-slate-800 text-slate-200 shadow-sm space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <h4 className="text-xs font-bold font-mono text-cyan-400">
                    CONVEYOR DIVERTER EXECUTION LOG
                  </h4>
                  <span className="text-[10px] text-slate-400 font-mono">
                    PERSISTED IN MYSQL DATABASE
                  </span>
                </div>
                <div className="max-h-60 overflow-y-auto space-y-1 font-mono text-[11px] text-slate-300 pr-1">
                  {videoResult.event_logs?.map((log, idx) => (
                    <div key={idx} className="p-1 rounded bg-slate-900/60 border border-slate-800">
                      {log}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
