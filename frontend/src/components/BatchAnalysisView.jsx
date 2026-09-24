import React, { useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function BatchAnalysisView({ onBatchCompleted }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [batchMass, setBatchMass] = useState(500.0);
  const [loading, setLoading] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFilesSelect = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    // Filter valid images
    const valid = files.filter((f) => f.type.startsWith('image/'));
    if (valid.length === 0) {
      setError('Please select valid image files (PNG, JPG, WEBP).');
      return;
    }

    setError(null);
    setSelectedFiles(valid);
    setBatchResult(null);
  };

  const handleRunBatch = async (e) => {
    e.preventDefault();
    if (selectedFiles.length === 0) {
      setError('Please select at least one image file for batch analysis.');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    selectedFiles.forEach((file) => {
      formData.append('files', file);
    });
    formData.append('input_mass_kg', batchMass);

    try {
      const res = await fetch(`${API_BASE_URL}/api/batch-analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error (HTTP ${res.status})`);
      }

      const data = await res.json();
      setBatchResult(data);
      if (onBatchCompleted) onBatchCompleted();
    } catch (err) {
      console.error('Batch analysis failed:', err);
      setError(err.message || 'Batch analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  const summary = batchResult?.batch_summary;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
      <div className="border-b border-slate-100 pb-3">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <span>Multi-Stream Batch Analysis &amp; High-Throughput Yield Engine</span>
          <span className="text-xs bg-indigo-100 text-indigo-800 font-semibold px-2 py-0.5 rounded-full font-mono">
            Batch Mode
          </span>
        </h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Process multiple stream capture frames simultaneously to evaluate facility-level mass balance
        </p>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
          {error}
        </div>
      )}

      {/* Upload & Parameters Form */}
      <form onSubmit={handleRunBatch} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
          <div className="md:col-span-2 border-2 border-dashed border-slate-300 rounded-xl p-4 text-center hover:border-slate-400 transition-colors">
            <input
              type="file"
              id="batchFileInput"
              multiple
              accept="image/*"
              onChange={handleFilesSelect}
              className="hidden"
            />
            <label
              htmlFor="batchFileInput"
              className="cursor-pointer block text-xs font-medium text-slate-600 space-y-1"
            >
              <span className="text-xl block">📁</span>
              <span className="font-bold text-slate-800 block">
                {selectedFiles.length > 0
                  ? `${selectedFiles.length} files selected`
                  : 'Click or drop multiple waste images here'}
              </span>
              <span className="text-[11px] text-slate-400 block">
                Select multiple JPG, PNG, or WEBP images
              </span>
            </label>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
            <label className="text-[11px] font-bold uppercase text-slate-500 block">
              Total Input Batch Mass
            </label>
            <div className="flex items-center gap-1.5">
              <input
                type="number"
                min="10"
                max="100000"
                value={batchMass}
                onChange={(e) => setBatchMass(parseFloat(e.target.value) || 100)}
                className="w-full text-sm font-bold font-mono bg-white border border-slate-300 rounded-lg px-2.5 py-1.5"
              />
              <span className="text-xs font-mono font-bold text-slate-600">kg</span>
            </div>
            <span className="text-[10px] text-slate-400 block">
              Distributed evenly across all uploaded images
            </span>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || selectedFiles.length === 0}
          className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-bold py-2.5 px-4 rounded-xl shadow-sm text-xs flex items-center justify-center gap-2 transition-all"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              Processing {selectedFiles.length} Batch Images...
            </>
          ) : (
            `Run Batch Optimization (${selectedFiles.length} Images • ${batchMass} kg)`
          )}
        </button>
      </form>

      {/* Batch Results Summary */}
      {summary && (
        <div className="space-y-4 pt-2 border-t border-slate-100">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
            Batch Optimization Summary ({batchResult.batch_size} Images)
          </h4>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <span className="text-[10px] font-bold text-slate-400 uppercase block">Objects Detected</span>
              <span className="text-xl font-extrabold text-slate-900 mt-0.5 block">{summary.total_objects_detected}</span>
            </div>

            <div className="bg-emerald-50/70 p-3 rounded-lg border border-emerald-200">
              <span className="text-[10px] font-bold text-emerald-700 uppercase block">Total Recoverable</span>
              <span className="text-xl font-extrabold text-emerald-700 mt-0.5 block">
                {summary.total_recoverable_kg} <span className="text-xs font-normal">kg</span>
              </span>
            </div>

            <div className="bg-rose-50/70 p-3 rounded-lg border border-rose-200">
              <span className="text-[10px] font-bold text-rose-700 uppercase block">Total Process Loss</span>
              <span className="text-xl font-extrabold text-rose-700 mt-0.5 block">
                {summary.total_waste_loss_kg} <span className="text-xs font-normal">kg</span>
              </span>
            </div>

            <div className="bg-indigo-50/70 p-3 rounded-lg border border-indigo-200">
              <span className="text-[10px] font-bold text-indigo-700 uppercase block">Average Yield</span>
              <span className="text-xl font-extrabold text-indigo-700 mt-0.5 block">
                {summary.average_recycling_yield}%
              </span>
            </div>
          </div>

          {/* Per-session breakdown table */}
          {batchResult.sessions?.length > 0 && (
            <div className="overflow-x-auto mt-3">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="bg-slate-100 text-slate-700 uppercase text-[10px]">
                  <tr>
                    <th className="p-2.5">File</th>
                    <th className="p-2.5">Material</th>
                    <th className="p-2.5">Objects</th>
                    <th className="p-2.5">Yield</th>
                    <th className="p-2.5">Recoverable</th>
                    <th className="p-2.5">Loss</th>
                    <th className="p-2.5">Processing Route</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {batchResult.sessions.map((s, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="p-2.5 font-mono text-[11px] font-semibold text-slate-800">{s.filename}</td>
                      <td className="p-2.5 capitalize font-medium">{s.primary_material}</td>
                      <td className="p-2.5 font-bold">{s.total_objects}</td>
                      <td className="p-2.5 font-bold text-emerald-600">{s.recycling_yield}%</td>
                      <td className="p-2.5 font-mono text-emerald-700">{s.recoverable_mass_kg} kg</td>
                      <td className="p-2.5 font-mono text-rose-600">{s.waste_loss_kg} kg</td>
                      <td className="p-2.5 text-[11px] font-semibold text-slate-700">{s.recommendation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
