import React, { useState } from 'react';

const RECLASSIFY_OPTIONS = [
  { material: 'plastic', label: 'Plastic (Bin 1)', color: 'bg-blue-600 hover:bg-blue-700 text-white' },
  { material: 'glass', label: 'Glass (Bin 2)', color: 'bg-amber-600 hover:bg-amber-700 text-white' },
  { material: 'metal', label: 'Metal (Bin 3)', color: 'bg-slate-700 hover:bg-slate-800 text-white' },
  { material: 'paper', label: 'Paper (Bin 4)', color: 'bg-yellow-600 hover:bg-yellow-700 text-white' },
  { material: 'organic', label: 'Organic (Bin 5)', color: 'bg-emerald-600 hover:bg-emerald-700 text-white' },
];

export default function ReviewQueuePanel({
  reviewItems = [],
  onReclassify,
  onRefresh,
  loading = false,
}) {
  const [processingId, setProcessingId] = useState(null);
  const [successNote, setSuccessNote] = useState(null);

  const handleAction = async (itemId, newMaterial) => {
    setProcessingId(itemId);
    setSuccessNote(null);
    try {
      await onReclassify(itemId, newMaterial);
      setSuccessNote(`Item #${itemId} reclassified as ${newMaterial.toUpperCase()} and routed to designated bin.`);
      setTimeout(() => setSuccessNote(null), 4000);
    } catch (err) {
      console.error('Reclassification error:', err);
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center font-bold text-lg">
            🔍
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              Human Review &amp; Ambiguity Queue
              {reviewItems.length > 0 && (
                <span className="bg-rose-500 text-white text-xs px-2 py-0.5 rounded-full font-mono font-bold">
                  {reviewItems.length} Pending
                </span>
              )}
            </h3>
            <p className="text-xs text-slate-500">
              Objects with &lt;50% confidence or multi-layer composite waste requiring human operator sign-off
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5"
        >
          <svg
            className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh Queue
        </button>
      </div>

      {successNote && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center gap-2 animate-fadeIn">
          <span>✓</span>
          <span>{successNote}</span>
        </div>
      )}

      {reviewItems.length === 0 ? (
        <div className="p-8 text-center border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
          <div className="text-2xl mb-2">🎉</div>
          <p className="text-sm font-semibold text-slate-800">Human Review Queue is Clear</p>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
            All detected waste objects in recent runs satisfied model certainty thresholds and were autonomously
            diverted to their respective virtual recycling streams.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {reviewItems.map((item) => (
            <div
              key={item.id}
              className="p-4 rounded-xl border border-rose-200 bg-rose-50/30 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-slate-900 text-sm">
                    {item.object_id} (DB #{item.id})
                  </span>
                  <span className="text-xs bg-rose-100 text-rose-800 font-semibold px-2 py-0.5 rounded">
                    Needs Verification
                  </span>
                  <span className="text-xs font-mono text-slate-400">
                    Session: {item.session_id}
                  </span>
                </div>
                <div className="text-xs text-slate-600 flex items-center gap-3">
                  <span>
                    Model Prediction: <strong className="capitalize">{item.material}</strong>
                  </span>
                  <span>
                    Confidence: <strong>{(item.confidence * 100).toFixed(1)}%</strong>
                  </span>
                  <span>
                    BBox: ({item.box_x.toFixed(0)}, {item.box_y.toFixed(0)}, {item.box_width.toFixed(0)}×{item.box_height.toFixed(0)})
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-1.5 shrink-0">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mr-1">
                  Reclassify to:
                </span>
                {RECLASSIFY_OPTIONS.map((opt) => (
                  <button
                    key={opt.material}
                    type="button"
                    disabled={processingId === item.id}
                    onClick={() => handleAction(item.id, opt.material)}
                    className={`text-xs px-2.5 py-1.5 rounded-lg font-semibold transition-all shadow-sm disabled:opacity-50 ${opt.color}`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
