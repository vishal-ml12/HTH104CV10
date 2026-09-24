import React, { useState } from 'react';

export default function YieldLossMassBalance({ optimization, onMassChange }) {
  const [customMass, setCustomMass] = useState(optimization?.input_mass_kg || 100.0);

  if (!optimization) return null;

  const yieldPct = optimization.recycling_yield || 70.0;
  const recoverableKg = ((customMass * yieldPct) / 100.0).toFixed(2);
  const wasteLossKg = (customMass - recoverableKg).toFixed(2);
  const lossBreakdown = optimization.yield_loss_breakdown || {
    baseline_potential: 88.0,
    mechanical_handling_loss: 3.5,
    contamination_rejection_loss: 14.3,
    net_estimated_yield: yieldPct,
  };

  const handleQuickMass = (m) => {
    setCustomMass(m);
    if (onMassChange) onMassChange(m);
  };

  const handleInputMass = (e) => {
    const val = parseFloat(e.target.value) || 0;
    setCustomMass(val);
    if (onMassChange) onMassChange(val);
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <span>Yield-Loss Analysis &amp; Mass Balance Estimation</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Transparent breakdown of recovery potential vs processing losses
          </p>
        </div>

        {/* Mass selector */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-lg">
          <span className="text-[11px] font-bold text-slate-400 px-1.5 uppercase">Batch Mass:</span>
          {[50, 100, 250, 500].map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => handleQuickMass(m)}
              className={`px-2 py-0.5 text-xs font-semibold rounded transition-all ${
                customMass === m ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              {m}kg
            </button>
          ))}
          <div className="flex items-center pl-1 border-l border-slate-200">
            <input
              type="number"
              min="1"
              max="10000"
              value={customMass}
              onChange={handleInputMass}
              className="w-14 text-xs font-mono bg-white border border-slate-300 rounded px-1.5 py-0.5 text-right font-bold text-slate-900"
            />
            <span className="text-[11px] font-mono text-slate-500 ml-1">kg</span>
          </div>
        </div>
      </div>

      {/* Recoverable vs Loss Mass Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            Gross Input Mass
          </span>
          <p className="text-2xl font-extrabold text-slate-900 mt-1">
            {customMass.toFixed(1)} <span className="text-sm font-normal text-slate-500">kg</span>
          </p>
          <span className="text-[11px] text-slate-500 mt-0.5 block">Total batch material</span>
        </div>

        <div className="bg-emerald-50/60 p-4 rounded-xl border border-emerald-200">
          <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider block">
            Estimated Recoverable Recyclate
          </span>
          <p className="text-2xl font-extrabold text-emerald-700 mt-1">
            {recoverableKg} <span className="text-sm font-normal text-emerald-600">kg</span>
          </p>
          <span className="text-[11px] text-emerald-800 font-medium mt-0.5 block">
            Net output ({yieldPct}% yield)
          </span>
        </div>

        <div className="bg-rose-50/60 p-4 rounded-xl border border-rose-200">
          <span className="text-[10px] font-bold text-rose-700 uppercase tracking-wider block">
            Estimated Process Waste / Rejects
          </span>
          <p className="text-2xl font-extrabold text-rose-700 mt-1">
            {wasteLossKg} <span className="text-sm font-normal text-rose-600">kg</span>
          </p>
          <span className="text-[11px] text-rose-800 font-medium mt-0.5 block">
            Purge + handling dropoff ({(100 - yieldPct).toFixed(1)}%)
          </span>
        </div>
      </div>

      {/* Mass Distribution Progress Meter */}
      <div>
        <div className="flex items-center justify-between text-xs font-semibold text-slate-600 mb-1.5">
          <span>Mass Balance Output Ratio</span>
          <span className="font-mono text-emerald-700">{yieldPct}% Recoverable • {(100 - yieldPct).toFixed(1)}% Rejection</span>
        </div>
        <div className="h-3 w-full bg-rose-200 rounded-full overflow-hidden flex">
          <div
            className="h-full bg-emerald-500 transition-all duration-500"
            style={{ width: `${yieldPct}%` }}
            title={`Recoverable Mass: ${recoverableKg} kg (${yieldPct}%)`}
          />
          <div
            className="h-full bg-rose-400 transition-all duration-500"
            style={{ width: `${100 - yieldPct}%` }}
            title={`Process Waste: ${wasteLossKg} kg (${(100 - yieldPct).toFixed(1)}%)`}
          />
        </div>
      </div>

      {/* Transparent Yield-Loss Waterfall Formula */}
      <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-3">
        <span className="text-xs font-bold text-slate-700 block uppercase tracking-wider">
          Configurable Yield Deduction Formula
        </span>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
          <div className="bg-white p-2.5 rounded-lg border border-slate-200">
            <span className="text-[10px] font-bold text-slate-400 uppercase block">Baseline Potential</span>
            <span className="text-sm font-bold text-slate-800">{lossBreakdown.baseline_potential}%</span>
            <span className="text-[10px] text-slate-400 block mt-0.5">Polymer theoretical</span>
          </div>

          <div className="bg-white p-2.5 rounded-lg border border-slate-200 text-rose-600">
            <span className="text-[10px] font-bold text-slate-400 uppercase block">Handling Loss</span>
            <span className="text-sm font-bold">- {lossBreakdown.mechanical_handling_loss}%</span>
            <span className="text-[10px] text-slate-400 block mt-0.5">Mechanical / dust</span>
          </div>

          <div className="bg-white p-2.5 rounded-lg border border-slate-200 text-amber-600">
            <span className="text-[10px] font-bold text-slate-400 uppercase block">Contamination Penalty</span>
            <span className="text-sm font-bold">- {lossBreakdown.contamination_rejection_loss}%</span>
            <span className="text-[10px] text-slate-400 block mt-0.5">Wash purge / rejects</span>
          </div>

          <div className="bg-white p-2.5 rounded-lg border-2 border-emerald-500 text-emerald-700">
            <span className="text-[10px] font-bold text-emerald-600 uppercase block">Net Yield</span>
            <span className="text-sm font-extrabold">= {lossBreakdown.net_estimated_yield}%</span>
            <span className="text-[10px] text-emerald-600 block mt-0.5">Estimated output</span>
          </div>
        </div>

        <p className="text-[11px] text-slate-400 text-center italic">
          Formula: Net Yield = max(0, Baseline Potential - Handling Loss - (Contamination% × 0.95))
        </p>
      </div>
    </div>
  );
}
