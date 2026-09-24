import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const STREAM_ICONS = {
  plastic: '🥤',
  glass: '🍾',
  metal: '🥫',
  paper: '📦',
  organic: '🍃',
  review: '🔍',
};

export default function TrendsAnalyticsView() {
  const [trends, setTrends] = useState(null);
  const [streamStats, setStreamStats] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [resTrends, resStreams] = await Promise.all([
        fetch(`${API_BASE_URL}/api/analytics/trends`),
        fetch(`${API_BASE_URL}/api/analytics/streams`),
      ]);

      if (resTrends.ok) {
        const dataTrends = await resTrends.json();
        setTrends(dataTrends);
      }
      if (resStreams.ok) {
        const dataStreams = await resStreams.json();
        setStreamStats(dataStreams.streams || {});
      }
    } catch (err) {
      console.error('Error fetching analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const contamData = trends?.contamination_trend || [];
  const qualityData = trends?.quality_trend || [];
  const yieldData = trends?.yield_trend || [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <span>Historical Stream Analytics &amp; Process Trends</span>
            <span className="text-xs bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5 rounded-full font-mono">
              Live Diagnostics
            </span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Temporal trends in visual contamination, purity index, and recycling recovery yield
          </p>
        </div>

        <button
          type="button"
          onClick={fetchData}
          disabled={loading}
          className="text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-lg font-semibold transition-colors flex items-center gap-1.5"
        >
          <svg className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh Trends
        </button>
      </div>

      {/* 3 Metric Trend Strips */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Contamination Trend */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-700 uppercase">Contamination Trend</span>
            <span className="text-xs font-bold text-amber-600 font-mono">
              {contamData.length > 0 ? `${contamData[contamData.length - 1]}% latest` : '—'}
            </span>
          </div>
          <div className="h-20 flex items-end gap-1 pt-2">
            {contamData.slice(-15).map((val, idx) => (
              <div
                key={idx}
                className="flex-1 bg-amber-400 hover:bg-amber-500 rounded-t transition-all group relative"
                style={{ height: `${Math.max(8, Math.min(100, (val / 50) * 100))}%` }}
              >
                <div className="hidden group-hover:block absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-1.5 py-0.5 bg-slate-900 text-white text-[10px] rounded pointer-events-none whitespace-nowrap z-10 font-mono">
                  {val}%
                </div>
              </div>
            ))}
          </div>
          <span className="text-[10px] text-slate-400 block text-right">Last {Math.min(15, contamData.length)} runs</span>
        </div>

        {/* Quality Score Trend */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-700 uppercase">Quality Score Trend</span>
            <span className="text-xs font-bold text-indigo-600 font-mono">
              {qualityData.length > 0 ? `${qualityData[qualityData.length - 1]}/100 latest` : '—'}
            </span>
          </div>
          <div className="h-20 flex items-end gap-1 pt-2">
            {qualityData.slice(-15).map((val, idx) => (
              <div
                key={idx}
                className="flex-1 bg-indigo-400 hover:bg-indigo-500 rounded-t transition-all group relative"
                style={{ height: `${Math.max(8, Math.min(100, val))}%` }}
              >
                <div className="hidden group-hover:block absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-1.5 py-0.5 bg-slate-900 text-white text-[10px] rounded pointer-events-none whitespace-nowrap z-10 font-mono">
                  {val}/100
                </div>
              </div>
            ))}
          </div>
          <span className="text-[10px] text-slate-400 block text-right">Last {Math.min(15, qualityData.length)} runs</span>
        </div>

        {/* Yield Trend */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-700 uppercase">Recycling Yield Trend</span>
            <span className="text-xs font-bold text-emerald-600 font-mono">
              {yieldData.length > 0 ? `${yieldData[yieldData.length - 1]}% latest` : '—'}
            </span>
          </div>
          <div className="h-20 flex items-end gap-1 pt-2">
            {yieldData.slice(-15).map((val, idx) => (
              <div
                key={idx}
                className="flex-1 bg-emerald-500 hover:bg-emerald-600 rounded-t transition-all group relative"
                style={{ height: `${Math.max(8, Math.min(100, val))}%` }}
              >
                <div className="hidden group-hover:block absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-1.5 py-0.5 bg-slate-900 text-white text-[10px] rounded pointer-events-none whitespace-nowrap z-10 font-mono">
                  {val}%
                </div>
              </div>
            ))}
          </div>
          <span className="text-[10px] text-slate-400 block text-right">Last {Math.min(15, yieldData.length)} runs</span>
        </div>
      </div>

      {/* Stream Comparison Analytics */}
      {streamStats && (
        <div className="space-y-3 pt-2 border-t border-slate-100">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600">
            Material Stream Comparative Analytics
          </h4>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {Object.entries(streamStats).map(([sKey, sStat]) => (
              <div key={sKey} className="p-3 rounded-xl border border-slate-200 bg-slate-50/50 space-y-1.5 text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="text-lg">{STREAM_ICONS[sKey] || '📦'}</span>
                  <span className="font-bold text-slate-900 capitalize">{sKey}</span>
                </div>
                <div className="text-[11px] text-slate-500 space-y-0.5">
                  <div>Yield: <strong className="text-emerald-700 font-mono">{sStat.avg_yield}%</strong></div>
                  <div>Contam: <strong className="text-amber-700 font-mono">{sStat.avg_contamination}%</strong></div>
                  <div>Purity: <strong className="text-indigo-700 font-mono">{sStat.avg_quality}/100</strong></div>
                  <div>Items: <strong className="text-slate-800 font-mono">{sStat.total_items}</strong></div>
                  <div className="truncate text-[10px] text-slate-400" title={sStat.dominant_contamination_category}>
                    Top: {sStat.dominant_contamination_category}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
