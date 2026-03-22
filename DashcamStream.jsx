import React, { useEffect, useRef, useState, useCallback } from 'react';

const DashcamStream = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState('');
  
  // Connect to the webcam on mount
  useEffect(() => {
    let intervalId;
    
    // Step 1: Access webcam via getUserMedia
    const initWebcam = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } }
        });
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        
        // Step 2: Establish WS and start streaming frames
        connectWebSocket();
        
      } catch (err) {
        console.error("Camera error:", err);
        setError('Could not access webcam: ' + err.message);
      }
    };
    
    const connectWebSocket = () => {
      const ws = new WebSocket('ws://localhost:8080');
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsStreaming(true);
        setError('');
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsStreaming(false);
      };
      
      ws.onerror = (err) => {
        console.error('WebSocket Error:', err);
        setIsStreaming(false);
        setError('WebSocket error connecting to ws://localhost:8080');
      };
      
      wsRef.current = ws;
      
      // Send frames every 500ms
      intervalId = setInterval(captureAndSendFrame, 500);
    };
    
    // Captures the current frame as base64 JPEG and sends over WS
    const captureAndSendFrame = () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && videoRef.current) {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        
        // Ensure video is playing and has dimensions
        if (video.readyState === video.HAVE_ENOUGH_DATA && video.videoWidth > 0 && video.videoHeight > 0) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          const ctx = canvas.getContext('2d');
          
          // Draw video frame to canvas
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          
          // Convert to base64 JPEG
          const base64Jpeg = canvas.toDataURL('image/jpeg', 0.8);
          
          // Send over WS
          wsRef.current.send(JSON.stringify({
            event: 'dashcam_frame',
            format: 'jpeg',
            timestamp: Date.now(),
            data: base64Jpeg
          }));
        }
      }
    };

    initWebcam();
    
    return () => {
      // Cleanup on unmount
      if (intervalId) {
        clearInterval(intervalId);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = videoRef.current.srcObject.getTracks();
        tracks.forEach(track => track.stop());
      }
    };
  }, []);

  // Step 5: Simulate Incident via Special Flag Frame
  const handleSimulateIncident = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && videoRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      
      let base64Jpeg = null;
      if (video.videoWidth > 0 && video.videoHeight > 0) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        base64Jpeg = canvas.toDataURL('image/jpeg', 0.8);
      }
      
      const incidentPayload = {
        event: 'incident_flag',
        incident: true,
        location: '995 Market St, SF',
        timestamp: Date.now(),
        data: base64Jpeg
      };
      
      console.log('Sending incident flag:', incidentPayload);
      wsRef.current.send(JSON.stringify(incidentPayload));
      
      alert('SIMULATED INCIDENT TRIGGERED!\n\nPayload sent to ws://localhost:8080 with { "incident": true, "location": "995 Market St, SF" }');
    } else {
      alert('Cannot send incident: WebSocket is disconnected.');
    }
  }, []);

  return (
    <div style={{
      maxWidth: '640px',
      margin: '0 auto',
      fontFamily: 'Inter, system-ui, sans-serif',
      padding: '20px',
      backgroundColor: '#1E1E1E',
      color: '#ffffff',
      borderRadius: '12px',
      boxShadow: '0 8px 16px rgba(0,0,0,0.5)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h2 style={{ margin: 0, fontSize: '24px' }}>RocketRide Dashcam</h2>
        
        {/* Step 4: Status Indicator */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '8px', 
          padding: '6px 12px',
          backgroundColor: isStreaming ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          border: `1px solid ${isStreaming ? '#22c55e' : '#ef4444'}`,
          borderRadius: '20px',
          fontWeight: '500'
        }}>
          <div style={{ 
            width: '10px', 
            height: '10px', 
            borderRadius: '50%', 
            backgroundColor: isStreaming ? '#22c55e' : '#ef4444',
            boxShadow: isStreaming ? '0 0 8px #22c55e' : 'none'
          }} />
          {isStreaming ? 'Streaming' : 'Disconnected'}
        </div>
      </div>
      
      {error && (
        <div style={{ 
          backgroundColor: '#ef444420', 
          color: '#ef4444', 
          padding: '12px', 
          borderRadius: '8px', 
          marginBottom: '16px',
          border: '1px solid #ef444450'
        }}>
          ⚠️ {error}
        </div>
      )}
      
      {/* Step 3: Live Preview window */}
      <div style={{ 
        position: 'relative', 
        width: '100%', 
        aspectRatio: '4/3', 
        backgroundColor: '#000', 
        borderRadius: '8px', 
        overflow: 'hidden',
        border: '1px solid #333'
      }}>
        <video 
          ref={videoRef}
          autoPlay 
          playsInline 
          muted
          style={{ 
            width: '100%', 
            height: '100%', 
            objectFit: 'cover'
          }}
        />
        {/* Offscreen canvas used for grabbing frames */}
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </div>

      <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'center' }}>
        {/* Step 5: Simulate Incident Button */}
        <button 
          onClick={handleSimulateIncident}
          disabled={!isStreaming}
          style={{
            backgroundColor: '#dc2626',
            color: 'white',
            border: 'none',
            padding: '16px 32px',
            fontSize: '18px',
            fontWeight: 'bold',
            borderRadius: '8px',
            cursor: isStreaming ? 'pointer' : 'not-allowed',
            opacity: isStreaming ? 1 : 0.6,
            boxShadow: isStreaming ? '0 4px 12px rgba(220, 38, 38, 0.4)' : 'none',
            transition: 'all 0.2s',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            width: '100%',
            justifyContent: 'center'
          }}
        >
          <span style={{ fontSize: '24px' }}>🚨</span> SIMULATE INCIDENT
        </button>
      </div>
    </div>
  );
};

export default DashcamStream;
