import React, { useState, useEffect } from 'react';
import CameraCapture from './components/CameraCapture';
import BoundingBoxOverlay from './components/BoundingBoxOverlay';
import VirtualSortingDashboard from './components/VirtualSortingDashboard';
import ReviewQueuePanel from './components/ReviewQueuePanel';
import ExplainableRecommendation from './components/ExplainableRecommendation';
import YieldLossMassBalance from './components/YieldLossMassBalance';
import StreamWiseTable from './components/StreamWiseTable';
import BatchAnalysisView from './components/BatchAnalysisView';
import TrendsAnalyticsView from './components/TrendsAnalyticsView';
import ConveyorBeltSimulation from './components/ConveyorBeltSimulation';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function App() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [activeTab, setActiveTab] = useState('optimize'); // 'optimize' | 'batch' | 'trends' | 'conveyor'

  const [inputMode, setInputMode] = useState('upload'); // 'upload' | 'camera'
  const [selectedFile, setSelectedFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [inputMassKg, setInputMassKg] = useState(100.0);
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analyzedFileName, setAnalyzedFileName] = useState('');
  const [statistics, setStatistics] = useState(null);
  const [recentResults, setRecentResults] = useState([]);
  const [reviewQueue, setReviewQueue] = useState([]);
  const [error, setError] = useState(null);
  const [selectedSessionId, setSelectedSessionId] = useState(null);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/health`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setHealthStatus(data);
    } catch (err) {
      console.error('Health check failed:', err);
      setHealthStatus({ status: 'error', service: 'Backend unreachable' });
    }
  };

  const fetchStatistics = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/statistics`);
      if (res.ok) {
        const data = await res.json();
        setStatistics(data);
      }
    } catch (err) {
      console.error('Error fetching statistics:', err);
    }
  };

  const fetchRecentResults = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/results`);
      if (res.ok) {
        const data = await res.json();
        setRecentResults(data);
      }
    } catch (err) {
      console.error('Error fetching results:', err);
    }
  };

  const fetchReviewQueue = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/review-queue`);
      if (res.ok) {
        const data = await res.json();
        setReviewQueue(data);
      }
    } catch (err) {
      console.error('Error fetching review queue:', err);
    }
  };

  // Initialize data on mount
  useEffect(() => {
    checkHealth();
    fetchStatistics();
    fetchRecentResults();
    fetchReviewQueue();
  }, []);

  const handleFileChange = (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setError('Please select a valid image file (PNG, JPG, WEBP).');
      setSelectedFile(null);
      setImagePreview(null);
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setError('Selected image exceeds the 15MB file size limit.');
      setSelectedFile(null);
      setImagePreview(null);
      return;
    }

    if (file.size === 0) {
      setError('Selected image file is empty (0 bytes). Please choose a valid image.');
      setSelectedFile(null);
      setImagePreview(null);
      return;
    }

    setError(null);
    setSelectedFile(file);
    setImagePreview(URL.createObjectURL(file));
    setAnalysisResult(null);
    setAnalyzedFileName('');
    setSelectedSessionId(null);
  };

  const handleCameraCapture = (file) => {
    setError(null);
    setSelectedFile(file);
    setImagePreview(URL.createObjectURL(file));
    setAnalysisResult(null);
    setAnalyzedFileName('');
    setSelectedSessionId(null);
    setInputMode('upload');
  };

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();

    if (!selectedFile) {
      setError('Please select an image file or capture a photo first.');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('input_mass_kg', inputMassKg);

    try {
      const res = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        let errorMsg = `Server error (HTTP ${res.status})`;
        try {
          const errData = await res.json();
          if (errData && errData.detail) {
            errorMsg = errData.detail;
          }
        } catch {
          // Ignore JSON parsing errors
        }
        throw new Error(errorMsg);
      }

      const data = await res.json();
      if (!data || !data.success || !data.analysis) {
        throw new Error('Received malformed response from analysis server.');
      }

      setAnalysisResult(data);
      setSelectedSessionId(data.session_id);
      setAnalyzedFileName(selectedFile.name);

      // Refresh database tables & statistics
      await Promise.all([fetchStatistics(), fetchRecentResults(), fetchReviewQueue()]);
    } catch (err) {
      console.error('Analysis failed:', err);
      setError(err.message || 'Analysis failed. Please check backend connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleReclassify = async (objectDbId, newMaterial) => {
    const res = await fetch(`${API_BASE_URL}/api/review-queue/${objectDbId}/reclassify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        new_material: newMaterial,
        notes: 'Operator verified material stream via dashboard action',
      }),
    });

    if (!res.ok) {
      throw new Error(`Failed to reclassify object #${objectDbId}`);
    }

    await Promise.all([fetchReviewQueue(), fetchStatistics(), fetchRecentResults()]);
  };

  const handleInspectSession = async (sessionId) => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`);
      if (!res.ok) throw new Error('Session not found');
      const data = await res.json();

      const sessionRec = data.session;
      const detectedObjs = data.detected_objects || [];
      const streamRecs = data.stream_analyses || [];

      // Rebuild stream_analyses dictionary
      const streamsAnalysisMap = {};
      streamRecs.forEach((sr) => {
        streamsAnalysisMap[sr.stream_name] = {
          stream_name: sr.stream_name,
          item_count: sr.item_count,
          stream_share_pct: sr.stream_share_pct,
          contamination_category: sr.contamination_category,
          contamination_level: sr.contamination_level,
          contamination_percentage: sr.contamination_percentage,
          quality_score: sr.quality_score,
          estimated_yield: sr.estimated_yield,
          yield_loss_handling: sr.yield_loss_handling,
          yield_loss_contamination: sr.yield_loss_contamination,
          recoverable_mass_kg: sr.recoverable_mass_kg,
          waste_loss_kg: sr.waste_loss_kg,
          processing_route: sr.processing_route,
          recommendation: sr.recommendation,
          recommendation_reason: sr.recommendation_reason,
        };
      });

      const reconstructedAnalysis = {
        success: true,
        session_id: sessionRec.session_id,
        mode: sessionRec.mode || 'REAL_YOLO',
        analysis: {
          materials: [{ name: sessionRec.material, confidence: sessionRec.confidence }],
          contamination: {
            level: sessionRec.contamination_level,
            percentage: sessionRec.contamination_percentage,
          },
          quality_score: sessionRec.quality_score,
          recycling_yield: sessionRec.recycling_yield,
          recommendation: sessionRec.recommendation,
          recommendation_reason: sessionRec.recommendation_reason,
          processing_route: sessionRec.processing_route,
          detected_objects: detectedObjs.map((obj) => ({
            object_id: obj.object_id,
            material: obj.material,
            confidence: obj.confidence,
            stream: obj.stream,
            status: obj.status,
            contamination_score: obj.contamination_score,
            contamination_category: obj.contamination_category,
            bbox: {
              x: obj.box_x,
              y: obj.box_y,
              width: obj.box_width,
              height: obj.box_height,
              normalized: {
                x: obj.box_x,
                y: obj.box_y,
                width: obj.box_width,
                height: obj.box_height,
              },
            },
          })),
          virtual_sorting: {
            total_objects: sessionRec.total_objects,
            streams: {
              plastic: { count: sessionRec.plastic_count, percentage: sessionRec.total_objects > 0 ? Math.round((sessionRec.plastic_count / sessionRec.total_objects) * 100) : 0, diverter_bin: 'Bin 1 - Air Jet Ejector' },
              glass: { count: sessionRec.glass_count, percentage: sessionRec.total_objects > 0 ? Math.round((sessionRec.glass_count / sessionRec.total_objects) * 100) : 0, diverter_bin: 'Bin 2 - Mechanical Paddle' },
              metal: { count: sessionRec.metal_count, percentage: sessionRec.total_objects > 0 ? Math.round((sessionRec.metal_count / sessionRec.total_objects) * 100) : 0, diverter_bin: 'Bin 3 - Eddy Current / Magnetic Separator' },
              paper: { count: sessionRec.paper_count, percentage: sessionRec.total_objects > 0 ? Math.round((sessionRec.paper_count / sessionRec.total_objects) * 100) : 0, diverter_bin: 'Bin 4 - Vacuum Suction Diverter' },
              organic: { count: sessionRec.organic_count, percentage: sessionRec.total_objects > 0 ? Math.round((sessionRec.organic_count / sessionRec.total_objects) * 100) : 0, diverter_bin: 'Bin 5 - Biological Recovery Bin' },
              review: { count: sessionRec.review_count, percentage: sessionRec.total_objects > 0 ? Math.round((sessionRec.review_count / sessionRec.total_objects) * 100) : 0, diverter_bin: 'Manual Verification Conveyor' },
            },
            diverter_events: [
              `[Loaded from MySQL] Session ${sessionRec.session_id} - ${sessionRec.total_objects} objects stored.`,
            ],
          },
          streams_analysis: streamsAnalysisMap,
          optimization: {
            primary_material: sessionRec.material,
            confidence: sessionRec.confidence,
            total_objects: sessionRec.total_objects,
            input_mass_kg: sessionRec.input_mass_kg || 100.0,
            recoverable_mass_kg: sessionRec.recoverable_mass_kg || ((100.0 * sessionRec.recycling_yield) / 100.0),
            waste_loss_kg: sessionRec.waste_loss_kg || (100.0 - ((100.0 * sessionRec.recycling_yield) / 100.0)),
            contamination_percentage: sessionRec.contamination_percentage,
            quality_score: sessionRec.quality_score,
            recycling_yield: sessionRec.recycling_yield,
            yield_loss_breakdown: {
              baseline_potential: 88.0,
              mechanical_handling_loss: 3.5,
              contamination_rejection_loss: Math.max(0, 88.0 - 3.5 - sessionRec.recycling_yield),
              net_estimated_yield: sessionRec.recycling_yield,
            },
            processing_route: sessionRec.processing_route || 'PRE_PROCESSING_WASHING',
            recommendation: sessionRec.recommendation,
            recommendation_reason: sessionRec.recommendation_reason || `Contamination = ${sessionRec.contamination_percentage}%, Quality = ${sessionRec.quality_score}/100, Yield = ${sessionRec.recycling_yield}%`,
            explainability: {
              recommendation: sessionRec.recommendation,
              reason: `Contamination = ${sessionRec.contamination_percentage}%, Quality = ${sessionRec.quality_score}/100, Estimated Yield = ${sessionRec.recycling_yield}%`,
              technical_justification: sessionRec.recommendation_reason || 'Verified historical session record.',
            },
          },
        },
      };

      setAnalysisResult(reconstructedAnalysis);
      setSelectedSessionId(sessionRec.session_id);
      setAnalyzedFileName(sessionRec.image_name || `Session ${sessionId}`);
      setActiveTab('optimize'); // Switch to view result
    } catch (err) {
      console.error('Failed to load session:', err);
      setError(`Failed to inspect session ${sessionId}: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const detectedObjects = analysisResult?.analysis?.detected_objects || [];
  const virtualSorting = analysisResult?.analysis?.virtual_sorting;
  const streamsAnalysis = analysisResult?.analysis?.streams_analysis || {};
  const optimization = analysisResult?.analysis?.optimization;
  const currentMode = analysisResult?.mode || 'REAL_YOLO';

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 p-4 md:p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header & Status Bar */}
        <header className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-slate-200 pb-5 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl">♻️</span>
              <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-slate-900">
                Multi-Waste-Stream Recycling Yield Optimizer
              </h1>
            </div>
            <p className="text-sm text-slate-500 mt-1">
              Phase 3: Video Stream &amp; Conveyor Belt Virtual Sorting Simulation
            </p>

          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Model Architecture Badge */}
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                currentMode === 'REAL_YOLO'
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                  : 'bg-amber-100 text-amber-800 border border-amber-300'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  currentMode === 'REAL_YOLO' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
                }`}
              />
              {currentMode === 'REAL_YOLO' ? 'REAL_YOLO (ONNX YOLO11n)' : 'DEMO_FALLBACK'}
            </span>

            {/* Backend Connectivity Status */}
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${
                healthStatus?.status === 'ok'
                  ? 'bg-slate-100 text-slate-700 border border-slate-300'
                  : 'bg-rose-100 text-rose-800 border border-rose-300'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  healthStatus?.status === 'ok' ? 'bg-emerald-500' : 'bg-rose-500'
                }`}
              />
              {healthStatus?.status === 'ok' ? 'API 200 OK' : 'Offline'}
            </span>
          </div>
        </header>

        {/* Prototype Scientific Honesty Disclaimer Banner */}
        <div className="p-3.5 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 flex items-start gap-2.5 shadow-sm">
          <span className="text-base leading-none">ℹ️</span>
          <div className="leading-relaxed">
            <strong>Prototype Optics &amp; Estimation Notice:</strong> The system analyzes surface visual characteristics
            via standard RGB optics. It does not claim hidden sub-surface chemical impurities can be detected without NIR spectroscopy.
            Quality scores and recycling yields are estimated algorithmic predictions for optimization modeling, not certified industrial recovery rates.
          </div>
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-rose-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-rose-500 hover:text-rose-800 font-bold ml-4 text-base"
            >
              &times;
            </button>
          </div>
        )}

        {/* Top Aggregate Metrics Bar */}
        {statistics && (
          <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Total Runs</span>
              <p className="text-xl font-extrabold text-slate-900 mt-0.5">{statistics.total_analyses}</p>
            </div>
            <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Objects Detected</span>
              <p className="text-xl font-extrabold text-indigo-600 mt-0.5">{statistics.total_objects_detected}</p>
            </div>
            <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Avg Contamination</span>
              <p className="text-xl font-extrabold text-amber-600 mt-0.5">{statistics.average_contamination}%</p>
            </div>
            <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Avg Quality Purity</span>
              <p className="text-xl font-extrabold text-purple-600 mt-0.5">{statistics.average_quality_score}/100</p>
            </div>
            <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Avg Recovery Yield</span>
              <p className="text-xl font-extrabold text-emerald-600 mt-0.5">{statistics.average_recycling_yield}%</p>
            </div>
            <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Total Recovered</span>
              <p className="text-xl font-extrabold text-teal-600 mt-0.5 font-mono">{statistics.total_recoverable_kg} kg</p>
            </div>
          </section>
        )}

        {/* Phase 2 Main Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-200 pb-1">
          <button
            type="button"
            onClick={() => setActiveTab('optimize')}
            className={`px-4 py-2 font-bold text-xs rounded-lg transition-all flex items-center gap-2 ${
              activeTab === 'optimize'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <span>🔬</span>
            <span>Stream Optimization &amp; Yield Engine</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('batch')}
            className={`px-4 py-2 font-bold text-xs rounded-lg transition-all flex items-center gap-2 ${
              activeTab === 'batch'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <span>📦</span>
            <span>Batch Analysis Mode</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('trends')}
            className={`px-4 py-2 font-bold text-xs rounded-lg transition-all flex items-center gap-2 ${
              activeTab === 'trends'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <span>📈</span>
            <span>Historical Stream Analytics &amp; Trends</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('conveyor')}
            className={`px-4 py-2 font-bold text-xs rounded-lg transition-all flex items-center gap-2 ${
              activeTab === 'conveyor'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            <span>🏭</span>
            <span>Conveyor Belt Simulation</span>
          </button>
        </div>


        {/* TAB 1: Stream Optimization & Virtual Sorting View */}
        {activeTab === 'optimize' && (
          <div className="space-y-8">
            {/* Input & Vision Pipeline Visualizer */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
              
              {/* Left Column: Image Ingestion (Upload & Camera) */}
              <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-5">
                <div>
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold text-slate-900">Mixed-Waste Input Source</h2>
                    <div className="flex items-center bg-slate-100 p-1 rounded-lg">
                      <button
                        type="button"
                        onClick={() => setInputMode('upload')}
                        className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                          inputMode === 'upload' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'
                        }`}
                      >
                        📁 File Upload
                      </button>
                      <button
                        type="button"
                        onClick={() => setInputMode('camera')}
                        className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                          inputMode === 'camera' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900'
                        }`}
                      >
                        📷 Live Camera
                      </button>
                    </div>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Provide a mixed-waste photo. The engine will segment objects, separate streams, and optimize yield.
                  </p>
                </div>

                {inputMode === 'camera' ? (
                  <CameraCapture
                    onCapture={handleCameraCapture}
                    onCancel={() => setInputMode('upload')}
                  />
                ) : (
                  <form onSubmit={handleAnalyze} className="space-y-4">
                    <div className="border-2 border-dashed border-slate-300 hover:border-slate-400 rounded-xl p-6 text-center transition-colors">
                      <input
                        type="file"
                        id="wasteImageInput"
                        accept="image/png,image/jpeg,image/webp,image/bmp,image/gif"
                        onChange={handleFileChange}
                        className="hidden"
                      />
                      <label
                        htmlFor="wasteImageInput"
                        className="cursor-pointer block text-sm text-slate-600 font-medium"
                      >
                        {selectedFile ? (
                          <div>
                            <span className="text-emerald-700 font-bold block">{selectedFile.name}</span>
                            <span className="text-xs text-slate-400">
                              ({(selectedFile.size / 1024).toFixed(1)} KB) • Click to select a different image
                            </span>
                          </div>
                        ) : (
                          <div className="space-y-1">
                            <span className="text-2xl block">📤</span>
                            <span className="font-semibold text-slate-700 block">Click to upload mixed waste photo</span>
                            <span className="text-xs text-slate-400 block">Supports PNG, JPG, WEBP (Up to 15MB)</span>
                          </div>
                        )}
                      </label>
                    </div>

                    {/* Batch Mass Parameter Input */}
                    <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 flex items-center justify-between gap-3">
                      <div>
                        <span className="text-xs font-bold text-slate-700 block">Batch Input Mass:</span>
                        <span className="text-[11px] text-slate-400">Used for mass balance recovery estimation</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <input
                          type="number"
                          min="1"
                          max="10000"
                          value={inputMassKg}
                          onChange={(e) => setInputMassKg(parseFloat(e.target.value) || 100)}
                          className="w-20 text-xs font-mono font-bold bg-white border border-slate-300 rounded px-2 py-1 text-right text-slate-900"
                        />
                        <span className="text-xs font-mono font-bold text-slate-500">kg</span>
                      </div>
                    </div>

                    {imagePreview && (
                      <div className="space-y-2">
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">
                          Sample Image Preview
                        </span>
                        <div className="relative rounded-lg overflow-hidden border border-slate-200 bg-slate-100 flex items-center justify-center max-h-56 p-2">
                          <img
                            src={imagePreview}
                            alt="Selected waste preview"
                            className="max-h-52 w-auto object-contain rounded"
                          />
                        </div>
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={loading || !selectedFile}
                      className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-xl shadow-sm transition-all text-sm flex items-center justify-center gap-2"
                    >
                      {loading ? (
                        <>
                          <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                          </svg>
                          Analyzing Contamination &amp; Optimizing Yield...
                        </>
                      ) : (
                        'Run Virtual Sorting & Stream Optimization'
                      )}
                    </button>
                  </form>
                )}
              </section>

              {/* Right Column: Multi-Object Detection Bounding Boxes & Heatmap */}
              <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-5">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-slate-900">Vision Segmentation &amp; Heatmap</h2>
                    <p className="text-xs text-slate-500">
                      Bounding boxes, material classification, and surface contamination intensity
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {analyzedFileName && (
                      <span className="text-[11px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono truncate max-w-[140px]" title={analyzedFileName}>
                        {analyzedFileName}
                      </span>
                    )}
                    {selectedSessionId && (
                      <span className="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md font-mono font-bold">
                        {selectedSessionId}
                      </span>
                    )}
                  </div>
                </div>

                {imagePreview && detectedObjects.length > 0 ? (
                  <BoundingBoxOverlay
                    imageSrc={imagePreview}
                    detectedObjects={detectedObjects}
                    _sessionData={analysisResult}
                  />
                ) : imagePreview && !analysisResult ? (
                  <div className="p-8 text-center border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
                    <span className="text-3xl block mb-2">🎯</span>
                    <p className="text-sm font-semibold text-slate-700">Image Loaded</p>
                    <p className="text-xs text-slate-500 mt-1">
                      Click &quot;Run Virtual Sorting &amp; Stream Optimization&quot; to execute the Phase 2 pipeline.
                    </p>
                  </div>
                ) : (
                  <div className="p-12 text-center border border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400 text-xs">
                    <span className="text-3xl block mb-2 opacity-50">📷</span>
                    Upload or capture a waste image to see multi-object bounding boxes, contamination heatmaps, and yield metrics.
                  </div>
                )}
              </section>
            </div>

            {/* Phase 2: Explainable Recommendation Banner */}
            {optimization && (
              <section>
                <ExplainableRecommendation
                  optimization={optimization}
                  primaryMaterial={optimization.primary_material}
                />
              </section>
            )}

            {/* Phase 2: Yield-Loss Breakdown & Mass Balance Panel */}
            {optimization && (
              <section>
                <YieldLossMassBalance
                  optimization={optimization}
                  onMassChange={(m) => setInputMassKg(m)}
                />
              </section>
            )}

            {/* Phase 2: Stream-Wise Contamination Analysis Table */}
            {Object.keys(streamsAnalysis).length > 0 && (
              <section>
                <StreamWiseTable streamsAnalysis={streamsAnalysis} />
              </section>
            )}

            {/* Virtual Sorting Engine Pipeline (6 Stream Bins & Diverter Simulation) */}
            {virtualSorting && (
              <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-4">
                  <div>
                    <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
                      <span>Virtual Sorting Engine</span>
                      <span className="text-xs font-mono font-semibold bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full">
                        Active Simulation
                      </span>
                    </h2>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Mixed-waste stream separated into 6 distinct virtual recycling streams
                    </p>
                  </div>

                  {/* Summary badges */}
                  {optimization && (
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">Est. Yield</span>
                        <span className="text-base font-extrabold text-emerald-600">
                          {optimization.recycling_yield}%
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">Quality Score</span>
                        <span className="text-base font-extrabold text-indigo-600">
                          {optimization.quality_score}/100
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                <VirtualSortingDashboard
                  virtualSorting={virtualSorting}
                  _detectedObjects={detectedObjects}
                />
              </section>
            )}

            {/* Human Review Queue Section */}
            <section>
              <ReviewQueuePanel
                reviewItems={reviewQueue}
                onReclassify={handleReclassify}
                onRefresh={fetchReviewQueue}
              />
            </section>

            {/* Stored Analysis History (MySQL) */}
            <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Stored Analysis Sessions (MySQL)</h2>
                  <p className="text-xs text-slate-500">Live persistence records from waste_analysis and stream_analyses tables</p>
                </div>
                <button
                  onClick={() => {
                    fetchRecentResults();
                    fetchStatistics();
                    fetchReviewQueue();
                  }}
                  className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-lg font-medium transition-colors"
                >
                  Refresh History
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-600">
                  <thead className="bg-slate-100 text-slate-700 uppercase font-semibold">
                    <tr>
                      <th className="p-3">Session ID</th>
                      <th className="p-3">Primary</th>
                      <th className="p-3">Contam</th>
                      <th className="p-3">Quality</th>
                      <th className="p-3">Yield</th>
                      <th className="p-3">Recoverable</th>
                      <th className="p-3">Route</th>
                      <th className="p-3">Created</th>
                      <th className="p-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {recentResults.length > 0 ? (
                      recentResults.map((row) => (
                        <tr
                          key={row.id}
                          className={`hover:bg-slate-50 ${selectedSessionId === row.session_id ? 'bg-indigo-50/50' : ''}`}
                        >
                          <td className="p-3 font-mono font-bold text-slate-900">{row.session_id}</td>
                          <td className="p-3 capitalize font-semibold">{row.material}</td>
                          <td className="p-3 font-bold text-amber-700">{row.contamination_percentage}%</td>
                          <td className="p-3 text-purple-700 font-bold">{row.quality_score}/100</td>
                          <td className="p-3 text-emerald-700 font-bold">{row.recycling_yield}%</td>
                          <td className="p-3 font-mono text-teal-700 font-bold">
                            {row.recoverable_mass_kg ? `${row.recoverable_mass_kg} kg` : '—'}
                          </td>
                          <td className="p-3">
                            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-100 text-slate-800 font-semibold">
                              {row.processing_route || 'PRE_PROCESSING'}
                            </span>
                          </td>
                          <td className="p-3 text-slate-400">
                            {new Date(row.created_at).toLocaleTimeString()}
                          </td>
                          <td className="p-3 text-right">
                            <button
                              type="button"
                              onClick={() => handleInspectSession(row.session_id)}
                              className="text-xs bg-indigo-50 hover:bg-indigo-100 text-indigo-700 px-2 py-1 rounded font-semibold transition-colors"
                            >
                              Inspect
                            </button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="9" className="p-4 text-center text-slate-400">
                          No records found in database.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}

        {/* TAB 2: Batch Analysis Mode */}
        {activeTab === 'batch' && (
          <BatchAnalysisView
            onBatchCompleted={() => {
              fetchStatistics();
              fetchRecentResults();
            }}
          />
        )}

        {/* TAB 3: Historical Trends & Stream Analytics */}
        {activeTab === 'trends' && (
          <TrendsAnalyticsView />
        )}

        {/* TAB 4: Conveyor Belt Simulation */}
        {activeTab === 'conveyor' && (
          <ConveyorBeltSimulation
            onSessionSaved={() => {
              fetchStatistics();
              fetchRecentResults();
            }}
          />
        )}

      </div>
    </div>
  );
}

