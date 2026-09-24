import React from 'react';

const STREAM_ICONS = {
  plastic: '🥤',
  glass: '🍾',
  metal: '🥫',
  paper: '📦',
  organic: '🍃',
  review: '🔍',
};

const CATEGORY_LABELS = {
  organic_residue: 'Organic / Bio Residue',
  label_adhesive: 'Label / Adhesive Residue',
  cross_polymer: 'Cross-Polymer Mix',
  soil_dust: 'Particulate / Dust',
  none: 'Clean Stream',
};

const SEVERITY_BADGES = {
  low: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  medium: 'bg-amber-100 text-amber-800 border-amber-200',
  high: 'bg-rose-100 text-rose-800 border-rose-200',
  critical: 'bg-purple-100 text-purple-800 border-purple-200',
};

export default function StreamWiseTable({ streamsAnalysis = {} }) {
  const streamKeys = ['plastic', 'glass', 'metal', 'paper', 'organic', 'review'];

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <span>Stream-Wise Contamination &amp; Quality Analysis</span>
            <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full font-mono font-normal">
              Post-Virtual Separation
            </span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Individual contamination inspection, purity assessment, and recovery estimation per stream
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-600">
          <thead className="bg-slate-100 text-slate-700 uppercase font-semibold text-[11px]">
            <tr>
              <th className="p-3">Stream</th>
              <th className="p-3">Objects</th>
              <th className="p-3">Dominant Contaminant</th>
              <th className="p-3">Contamination</th>
              <th className="p-3">Quality Score</th>
              <th className="p-3">Est. Yield</th>
              <th className="p-3">Recoverable</th>
              <th className="p-3">Processing Route</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {streamKeys.map((sKey) => {
              const data = streamsAnalysis[sKey] || {
                stream_name: sKey,
                item_count: 0,
                stream_share_pct: 0,
                contamination_category: 'none',
                contamination_level: 'low',
                contamination_percentage: 0,
                quality_score: 100,
                estimated_yield: 80,
                recoverable_mass_kg: 0,
                processing_route: 'IDLE',
                recommendation: 'Idle',
                recommendation_reason: 'No material',
              };

              const isActive = data.item_count > 0;
              const sevBadge = SEVERITY_BADGES[data.contamination_level] || SEVERITY_BADGES.low;
              const catLabel = CATEGORY_LABELS[data.contamination_category] || data.contamination_category;

              return (
                <tr
                  key={sKey}
                  className={`hover:bg-slate-50 transition-colors ${
                    isActive ? 'bg-white font-medium' : 'bg-slate-50/40 opacity-70'
                  }`}
                >
                  <td className="p-3 flex items-center gap-2">
                    <span className="text-base">{STREAM_ICONS[sKey] || '📦'}</span>
                    <div>
                      <span className="font-bold text-slate-900 capitalize block">
                        {data.stream_name} Stream
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {data.stream_share_pct}% share
                      </span>
                    </div>
                  </td>

                  <td className="p-3">
                    <span className={`font-mono font-bold ${isActive ? 'text-slate-900 text-sm' : 'text-slate-400'}`}>
                      {data.item_count}
                    </span>
                  </td>

                  <td className="p-3">
                    <span className="font-medium text-slate-700 capitalize">
                      {isActive ? catLabel : '—'}
                    </span>
                  </td>

                  <td className="p-3">
                    {isActive ? (
                      <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${sevBadge}`}>
                        {data.contamination_percentage}% ({data.contamination_level})
                      </span>
                    ) : (
                      <span className="text-slate-400">0.0%</span>
                    )}
                  </td>

                  <td className="p-3">
                    <span className="font-bold text-indigo-600">
                      {isActive ? `${data.quality_score} / 100` : '—'}
                    </span>
                  </td>

                  <td className="p-3">
                    <span className="font-bold text-emerald-600">
                      {isActive ? `${data.estimated_yield}%` : '—'}
                    </span>
                  </td>

                  <td className="p-3">
                    <span className="font-mono text-slate-700">
                      {isActive ? `${data.recoverable_mass_kg} kg` : '0 kg'}
                    </span>
                  </td>

                  <td className="p-3">
                    {isActive ? (
                      <div>
                        <span className="font-semibold text-slate-900 block text-[11px]">
                          {data.recommendation}
                        </span>
                        <span className="text-[10px] text-slate-400 block line-clamp-1" title={data.recommendation_reason}>
                          {data.recommendation_reason}
                        </span>
                      </div>
                    ) : (
                      <span className="text-slate-400 italic">Stream Idle</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
