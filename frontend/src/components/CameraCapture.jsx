import React, { useRef, useState, useEffect } from 'react';

export default function CameraCapture({ onCapture, onCancel }) {
  const videoRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [cameraError, setCameraError] = useState(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let activeStream = null;

    async function initCamera() {
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error('Camera access is not supported by your browser environment.');
        }

        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: false,
        });

        activeStream = mediaStream;
        setStream(mediaStream);

        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
          videoRef.current.onloadedmetadata = () => {
            videoRef.current.play().catch(console.error);
            setIsReady(true);
          };
        }
      } catch (err) {
        console.error('Camera initialization error:', err);
        setCameraError(err.message || 'Unable to access camera device. Please verify permissions.');
      }
    }

    initCamera();

    return () => {
      if (activeStream) {
        activeStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const handleCapture = () => {
    if (!videoRef.current || !isReady) return;

    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (blob) {
          const file = new File([blob], `camera_snapshot_${Date.now()}.jpg`, { type: 'image/jpeg' });
          if (stream) {
            stream.getTracks().forEach((track) => track.stop());
          }
          onCapture(file);
        }
      },
      'image/jpeg',
      0.92
    );
  };

  return (
    <div className="bg-slate-900 rounded-xl p-4 text-white space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse"></span>
          <span className="text-sm font-semibold tracking-wide">Live Camera Stream</span>
        </div>
        <button
          type="button"
          onClick={onCancel}
          className="text-xs text-slate-400 hover:text-white px-2 py-1 rounded hover:bg-slate-800"
        >
          Cancel
        </button>
      </div>

      {cameraError ? (
        <div className="p-4 bg-rose-950/80 border border-rose-800 text-rose-200 rounded-lg text-sm">
          <p className="font-semibold mb-1">Camera Device Unavailable</p>
          <p className="text-xs text-rose-300">{cameraError}</p>
          <button
            type="button"
            onClick={onCancel}
            className="mt-3 bg-rose-800 hover:bg-rose-700 text-white text-xs px-3 py-1.5 rounded transition-colors"
          >
            Use File Upload Instead
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="relative aspect-video bg-black rounded-lg overflow-hidden flex items-center justify-center border border-slate-700">
            <video
              ref={videoRef}
              playsInline
              muted
              className="w-full h-full object-contain"
            />
            {!isReady && (
              <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 text-xs text-slate-300">
                Initializing camera feed...
              </div>
            )}
            {/* Viewfinder crosshairs */}
            <div className="absolute inset-6 border border-emerald-500/30 rounded pointer-events-none flex items-center justify-center">
              <div className="w-8 h-8 border-t-2 border-l-2 border-emerald-400 absolute top-0 left-0"></div>
              <div className="w-8 h-8 border-t-2 border-r-2 border-emerald-400 absolute top-0 right-0"></div>
              <div className="w-8 h-8 border-b-2 border-l-2 border-emerald-400 absolute bottom-0 left-0"></div>
              <div className="w-8 h-8 border-b-2 border-r-2 border-emerald-400 absolute bottom-0 right-0"></div>
              <span className="text-[10px] text-emerald-400/70 font-mono tracking-widest uppercase">
                Align mixed waste in frame
              </span>
            </div>
          </div>

          <div className="flex items-center justify-center gap-3 pt-1">
            <button
              type="button"
              onClick={handleCapture}
              disabled={!isReady}
              className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-semibold py-2 px-6 rounded-lg text-sm flex items-center gap-2 shadow-lg shadow-emerald-900/30 transition-all"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9" strokeWidth="2"></circle>
                <circle cx="12" cy="12" r="3" fill="currentColor"></circle>
              </svg>
              Capture Frame for Sorting
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
