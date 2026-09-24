import React from 'react';

const ROUTE_CONFIG = {
  DIRECT_RECYCLING: {
    label: 'Direct Mechanical Reprocessing',
    badge: 'bg-emerald-100 text-emerald-800 border-emerald-300',
    icon: '✨',
    color: 'emerald',
  },
  PRE_PROCESSING_WASHING: {
    label: 'Automated Pre-Processing & Wash-Line Route',
    badge: 'bg-blue-100 text-blue-800 border-blue-300',
    icon: '🧼',
    color: 'blue',
  },
  SECONDARY_PROCESSING_SHREDDING: {
    label: 'Secondary Granulation & Sink-Float Separation',
    badge: 'bg-amber-100 text-amber-800 border-amber-300',
    icon: '⚙️',
    color: 'amber',
  },
  DOWNGRADE_RDF: {
    label: 'Downgrade to Refuse-Derived Fuel (RDF) / Downcycling',
    badge: 'bg-purple-100 text-purple-800 border-purple-300',
    icon: '🔥',
    color: 'purple',
  },
  MANUAL_REVIEW_FLAGGED: {
    label: 'Manual Verification Conveyor Diversion',
    badge: 'bg-rose-100 text-rose-800 border-rose-300',
    icon: '🔍',
    color: 'rose',
  },
};

export default function ExplainableRecommendation({ optimization, _primaryMaterial }) {
  if (!optimization) return null;

  const routeKey = optimization.processing_route || 'PRE_PROCESSING_WASHING';
  const routeCfg = ROUTE_CONFIG[routeKey] || ROUTE_CONFIG.PRE_PROCESSING_WASHING;
  const explain = optimization.explainability || {
    recommendation: optimization.recommendation,
    reason: `Contamination = ${optimization.contamination_percentage}%, Quality = ${optimization.quality_score}/100, Estimated Yield = ${optimization.recycling_yield}%`,
    technical_justification: optimization.recommendation_reason,
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
      {/* Title & Route Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2.5">
          <span className="text-2xl">{routeCfg.icon}</span>
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              Smart Processing Route
            </span>
            <h3 className="text-base font-bold text-slate-900 leading-tight">
              {routeCfg.label}
            </h3>
          </div>
        </div>

        <span className={`px-3 py-1 rounded-full text-xs font-bold border ${routeCfg.badge} self-start sm:self-auto`}>
          {routeKey}
        </span>
      </div>

      {/* Main Explainability Card: Recommendation + Reason */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block">
            Operation Recommendation
          </span>
          <p className="text-lg font-extrabold text-slate-900 mt-0.5">
            &ldquo;{explain.recommendation}&rdquo;
          </p>
        </div>

        <div className="border-t border-slate-200/70 pt-2.5">
          <span className="text-xs font-bold text-slate-600 block mb-1">
            because:
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-1.5">
            <div className="bg-white px-3 py-2 rounded-lg border border-slate-200">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Contamination</span>
              <span className="text-sm font-extrabold text-amber-600">
                {optimization.contamination_percentage}%
              </span>
            </div>
            <div className="bg-white px-3 py-2 rounded-lg border border-slate-200">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Quality Score</span>
              <span className="text-sm font-extrabold text-indigo-600">
                {optimization.quality_score} / 100
              </span>
            </div>
            <div className="bg-white px-3 py-2 rounded-lg border border-slate-200">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Estimated Yield</span>
              <span className="text-sm font-extrabold text-emerald-600">
                {optimization.recycling_yield}%
              </span>
            </div>
          </div>
        </div>

        {/* Technical Rationale */}
        <div className="bg-white p-3 rounded-lg border border-slate-200 text-xs text-slate-600 leading-relaxed">
          <span className="font-bold text-slate-800 block mb-0.5">Technical Justification:</span>
          <p>{explain.technical_justification || optimization.recommendation_reason}</p>
        </div>
      </div>

      {/* Prototype Notice */}
      <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
        <span>ℹ️</span>
        <span>
          Decision logic is transparent and deterministic based on stream purity, edge frequency heuristics, and material thresholds.
        </span>
      </div>
    </div>
  );
}
