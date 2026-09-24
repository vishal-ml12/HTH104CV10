import React, { useState } from 'react';

const STREAM_STYLES = {
  plastic: {
    border: 'border-blue-500',
    bg: 'bg-blue-500/15',
    text: 'text-blue-700',
    badge: 'bg-blue-600 text-white',
    ring: 'ring-blue-400',
    name: 'Plastic',
  },
  glass: {
    border: 'border-amber-500',
    bg: 'bg-amber-500/15',
    text: 'text-amber-700',
    badge: 'bg-amber-600 text-white',
    ring: 'ring-amber-400',
    name: 'Glass',
  },
  metal: {
    border: 'border-slate-500',
    bg: 'bg-slate-500/15',
    text: 'text-slate-700',
    badge: 'bg-slate-700 text-white',
    ring: 'ring-slate-400',
    name: 'Metal',
  },
  paper: {
    border: 'border-yellow-500',
    bg: 'bg-yellow-500/15',
    text: 'text-yellow-800',
    badge: 'bg-yellow-600 text-white',
    ring: 'ring-yellow-400',
    name: 'Paper/Cardboard',
  },
  organic: {
    border: 'border-emerald-500',
    bg: 'bg-emerald-500/15',
    text: 'text-emerald-700',
    badge: 'bg-emerald-600 text-white',
    ring: 'ring-emerald-400',
    name: 'Organic',
  },
  review: {
    border: 'border-rose-500',
    bg: 'bg-rose-500/20',
    text: 'text-rose-700',
    badge: 'bg-rose-600 text-white',
    ring: 'ring-rose-400',
    name: 'Review Queue',
  },
};

export default function BoundingBoxOverlay({ imageSrc, detectedObjects = [], _sessionData }) {
  const [activeObjId, setActiveObjId] = useState(null);
  const [overlayMode, setOverlayMode] = useState('stream'); // 'stream' | 'heatmap'

  if (!imageSrc) return null;

  return (
    <div className="space-y-4">
      {/* Mode Switcher */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-slate-500 font-medium">Overlay Visualization Mode:</span>
        <div className="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs font-semibold">
          <button
            type="button"
            onClick={() => setOverlayMode('stream')}
            className={`px-2.5 py-1 rounded-md transition-all ${
              overlayMode === 'stream' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            🎨 Stream Bins
          </button>
          <button
            type="button"
            onClick={() => setOverlayMode('heatmap')}
            className={`px-2.5 py-1 rounded-md transition-all ${
              overlayMode === 'heatmap' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            🔥 Contamination Heatmap
          </button>
        </div>
      </div>

      {/* Visualizer Canvas Container */}
      <div className="relative rounded-xl overflow-hidden border-2 border-slate-200 bg-slate-950 flex items-center justify-center shadow-inner group">
        <img
          src={imageSrc}
          alt="Analyzed waste stream"
          className="w-full h-auto max-h-[460px] object-contain block select-none"
        />

        {/* Bounding Box / Heatmap Overlays */}
        {detectedObjects.map((obj) => {
          const streamKey = (obj.stream || 'review').toLowerCase();
          const style = STREAM_STYLES[streamKey] || STREAM_STYLES.review;
          const norm = obj.bbox?.normalized || { x: 0, y: 0, width: 100, height: 100 };
          const isHovered = activeObjId === obj.object_id;

          const contamScore = obj.contamination_score || 10.0;
          const contamCategory = obj.contamination_category || 'none';

          // Heatmap styling based on score
          const isHeatmap = overlayMode === 'heatmap';
          let heatBg = 'bg-emerald-500/20 border-emerald-400';
          let heatBadge = 'bg-emerald-600 text-white';
          if (contamScore >= 35.0) {
            heatBg = 'bg-rose-500/40 border-rose-500 backdrop-blur-[1px]';
            heatBadge = 'bg-rose-600 text-white';
          } else if (contamScore >= 15.0) {
            heatBg = 'bg-amber-500/30 border-amber-400';
            heatBadge = 'bg-amber-600 text-white';
          }

          // Clamping to stay inside frame safely
          const left = Math.max(0, Math.min(100, norm.x));
          const top = Math.max(0, Math.min(100, norm.y));
          const width = Math.max(2, Math.min(100 - left, norm.width));
          const height = Math.max(2, Math.min(100 - top, norm.height));

          return (
            <div
              key={obj.object_id}
              onMouseEnter={() => setActiveObjId(obj.object_id)}
              onMouseLeave={() => setActiveObjId(null)}
              className={`absolute border-2 transition-all duration-150 cursor-pointer pointer-events-auto ${
                isHeatmap ? heatBg : `${style.border} ${style.bg}`
              } ${isHovered ? 'ring-4 ring-indigo-400 z-30' : 'z-20'}`}
              style={{
                left: `${left}%`,
                top: `${top}%`,
                width: `${width}%`,
                height: `${height}%`,
              }}
            >
              {/* Top-Left Identifier Badge */}
              <div className="absolute top-0 left-0 -translate-y-full transform flex items-center gap-1 shadow-md whitespace-nowrap pointer-events-none">
                {isHeatmap ? (
                  <span className={`text-[11px] font-bold px-1.5 py-0.5 rounded-t font-mono ${heatBadge}`}>
                    {obj.object_id}: {contamScore}% Contam ({contamCategory})
                  </span>
                ) : (
                  <>
                    <span className={`text-[11px] font-bold px-1.5 py-0.5 rounded-t font-mono ${style.badge}`}>
                      {obj.object_id}: {obj.material?.toUpperCase()} ({(obj.confidence * 100).toFixed(0)}%)
                    </span>
                    <span className="text-[10px] bg-slate-900/90 text-slate-200 px-1.5 py-0.5 rounded-t hidden sm:inline-block">
                      ➔ {obj.stream?.toUpperCase()} STREAM
                    </span>
                  </>
                )}
              </div>

              {/* Center crosshair on hover */}
              {isHovered && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="w-2 h-2 rounded-full bg-white shadow-lg animate-ping"></div>
                </div>
              )}
            </div>
          );
        })}

        {/* Legend Overlay at bottom */}
        <div className="absolute bottom-2 left-2 right-2 bg-slate-900/85 backdrop-blur-sm border border-slate-700/80 rounded-lg px-3 py-1.5 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-200">
          {overlayMode === 'heatmap' ? (
            <div className="flex items-center gap-3">
              <span className="font-semibold text-white">Contamination Intensity:</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-emerald-500"></span>Low (&lt;15%)</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-amber-500"></span>Medium (15-35%)</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-rose-500"></span>High (&gt;35%)</span>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <span className="font-semibold text-white">Virtual Streams:</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500"></span>Plastic</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500"></span>Glass</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-slate-400"></span>Metal</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500"></span>Paper</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500"></span>Organic</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500"></span>Review</span>
            </div>
          )}
          <span className="text-[11px] text-slate-400 font-mono">
            {detectedObjects.length} object{detectedObjects.length === 1 ? '' : 's'} segmented
          </span>
        </div>
      </div>

      {/* Detected Objects Table */}
      {detectedObjects.length > 0 && (
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-3 space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-600 px-1">
            <span>Detected Multi-Object Segmentations ({detectedObjects.length})</span>
            <span className="text-slate-400">Hover item to highlight in viewer</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
            {detectedObjects.map((obj) => {
              const streamKey = (obj.stream || 'review').toLowerCase();
              const style = STREAM_STYLES[streamKey] || STREAM_STYLES.review;
              const isHovered = activeObjId === obj.object_id;

              return (
                <div
                  key={obj.object_id}
                  onMouseEnter={() => setActiveObjId(obj.object_id)}
                  onMouseLeave={() => setActiveObjId(null)}
                  className={`p-2.5 rounded-lg border text-xs transition-all cursor-pointer ${
                    isHovered
                      ? 'border-indigo-500 bg-indigo-50/50 shadow-sm'
                      : 'border-slate-200 bg-white hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-slate-900">{obj.object_id}</span>
                    <span className={`px-2 py-0.5 rounded-full font-semibold text-[10px] ${style.badge}`}>
                      {style.name} Stream
                    </span>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-slate-600">
                    <span className="capitalize font-medium">{obj.material}</span>
                    <span className="font-mono text-slate-500">{(obj.confidence * 100).toFixed(1)}% conf</span>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-100">
                    <span>Contamination:</span>
                    <span className="font-bold text-amber-700">
                      {obj.contamination_score || 0}% ({obj.contamination_category || 'none'})
                    </span>
                  </div>
                  {obj.status === 'pending_review' && (
                    <div className="mt-1 text-[10px] text-rose-600 font-medium">
                      ⚠️ Low confidence / Flagged for review
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
