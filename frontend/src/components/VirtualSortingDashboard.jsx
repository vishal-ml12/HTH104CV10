import React from 'react';

const STREAM_CONFIG = [
  {
    key: 'plastic',
    name: 'Plastic Stream',
    bin: 'Bin 1 - Air Jet Ejector',
    color: 'border-blue-300 bg-blue-50/60 text-blue-900',
    barColor: 'bg-blue-500',
    badge: 'bg-blue-600 text-white',
    icon: '🥤',
    spec: 'PET Bottles, HDPE, Rigid Polymers',
  },
  {
    key: 'glass',
    name: 'Glass Stream',
    bin: 'Bin 2 - Mechanical Paddle',
    color: 'border-amber-300 bg-amber-50/60 text-amber-900',
    barColor: 'bg-amber-500',
    badge: 'bg-amber-600 text-white',
    icon: '🍾',
    spec: 'Container Glass, Bottles, Cullet',
  },
  {
    key: 'metal',
    name: 'Metal Stream',
    bin: 'Bin 3 - Eddy Current / Magnetic Separator',
    color: 'border-slate-300 bg-slate-50/60 text-slate-900',
    barColor: 'bg-slate-600',
    badge: 'bg-slate-700 text-white',
    icon: '🥫',
    spec: 'Aluminum, Tinplate, Ferrous Scrap',
  },
  {
    key: 'paper',
    name: 'Paper/Cardboard Stream',
    bin: 'Bin 4 - Vacuum Suction Diverter',
    color: 'border-yellow-300 bg-yellow-50/60 text-yellow-900',
    barColor: 'bg-yellow-500',
    badge: 'bg-yellow-600 text-white',
    icon: '📦',
    spec: 'Cardboard, Kraft, Fiberboard',
  },
  {
    key: 'organic',
    name: 'Organic Stream',
    bin: 'Bin 5 - Biological Recovery Bin',
    color: 'border-emerald-300 bg-emerald-50/60 text-emerald-900',
    barColor: 'bg-emerald-500',
    badge: 'bg-emerald-600 text-white',
    icon: '🍃',
    spec: 'Compostables, Residues, Food Waste',
  },
  {
    key: 'review',
    name: 'Human Review Queue',
    bin: 'Manual Verification Conveyor',
    color: 'border-rose-300 bg-rose-50/60 text-rose-900',
    barColor: 'bg-rose-500',
    badge: 'bg-rose-600 text-white',
    icon: '🔍',
    spec: 'Low Confidence (<50%), Ambiguous, Mixed',
  },
];

export default function VirtualSortingDashboard({ virtualSorting, _detectedObjects = [] }) {
  const streams = virtualSorting?.streams || {};
  const logs = virtualSorting?.diverter_events || [];

  return (
    <div className="space-y-6">
      {/* Simulation Disclaimer Alert */}
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-xs flex items-start gap-3 shadow-sm">
        <span className="text-lg leading-none">⚠️</span>
        <div>
          <span className="font-bold uppercase tracking-wider block text-amber-800">
            Software Virtual Sorting Simulation Notice
          </span>
          <p className="mt-0.5 text-amber-700 leading-relaxed">
            The Virtual Sorting Engine is a software-based sorting simulation modeling multi-stream
            pneumatic/robotic optical diversion behavior. It operates purely in software for process modeling
            and yield optimization, and does not actuate physical hardware.
          </p>
        </div>
      </div>

      {/* 6 Material Stream Bins Grid */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>Virtual Material Stream Bins</span>
              <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full font-mono font-normal">
                6 Diverter Streams
              </span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Automated routing based on multi-object neural classification &amp; confidence thresholds
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {STREAM_CONFIG.map((cfg) => {
            const streamData = streams[cfg.key] || { count: 0, percentage: 0, items: [] };
            const count = streamData.count || 0;
            const pct = streamData.percentage || 0;
            const items = streamData.items || [];

            return (
              <div
                key={cfg.key}
                className={`p-4 rounded-xl border ${cfg.color} shadow-sm flex flex-col justify-between transition-all`}
              >
                <div>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">{cfg.icon}</span>
                      <div>
                        <h4 className="font-bold text-sm leading-tight text-slate-900">{cfg.name}</h4>
                        <span className="text-[11px] text-slate-500 font-mono block mt-0.5">
                          {cfg.bin}
                        </span>
                      </div>
                    </div>
                    <span className="text-xl font-extrabold text-slate-900">{count}</span>
                  </div>

                  <p className="text-[11px] text-slate-500 mt-2">{cfg.spec}</p>

                  {/* Progress Bar */}
                  <div className="mt-3">
                    <div className="flex items-center justify-between text-[11px] font-semibold text-slate-600 mb-1">
                      <span>Stream Allocation</span>
                      <span className="font-mono">{pct}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-200/80 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${cfg.barColor}`}
                        style={{ width: `${pct}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                {/* Items routed to this bin */}
                <div className="mt-3 pt-2.5 border-t border-slate-200/60">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Routed Objects
                  </span>
                  {items.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {items.map((it) => (
                        <span
                          key={it.object_id}
                          className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded ${cfg.badge}`}
                          title={`${it.material} - ${(it.confidence * 100).toFixed(0)}% confidence`}
                        >
                          {it.object_id} ({(it.confidence * 100).toFixed(0)}%)
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-[11px] text-slate-400 italic">No objects diverted to this bin</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Diverter Event Logs Console */}
      <div className="bg-slate-900 rounded-xl p-4 border border-slate-800 text-slate-200 space-y-2">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400">
              Virtual Diverter Event Simulation Log
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-500">
            {logs.length} actuation event{logs.length === 1 ? '' : 's'}
          </span>
        </div>

        <div className="font-mono text-xs max-h-36 overflow-y-auto space-y-1 pr-1 text-slate-300">
          {logs.length > 0 ? (
            logs.map((log, idx) => (
              <div key={idx} className="flex items-start gap-2 hover:bg-slate-800/50 p-0.5 rounded">
                <span className="text-slate-600 select-none">&gt;</span>
                <span>{log}</span>
              </div>
            ))
          ) : (
            <div className="text-slate-500 italic py-2">
              Waiting for waste sample analysis to simulate virtual diversion stream...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
