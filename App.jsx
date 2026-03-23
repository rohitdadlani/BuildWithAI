import React, { useState, useEffect } from 'react';
import DashcamStream from './DashcamStream';
import PassengerScreen from './PassengerScreen';

function App() {
  const [analysis, setAnalysis] = useState(null);

  useEffect(() => {
    // Listen for the analysis results coming back from the Python WS Server
    const connectWS = () => {
      const ws = new WebSocket('ws://localhost:8080');
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.event === 'analysis_result') {
            setAnalysis(data.analysis);
            console.log("Analysis received:", data.analysis);
          }
        } catch (err) {
          console.error("Failed to parse WS message:", err);
        }
      };

      ws.onclose = () => {
        console.log('Main App WS disconnected. Retrying in 3s...');
        setTimeout(connectWS, 3000);
      };

      ws.onerror = (err) => {
        console.error('Main App WS error:', err);
      };
    };

    connectWS();
  }, []);

  const isRerouting = analysis?.gesture_detected !== 'none' && analysis?.confidence > 0.85;

  return (
    <div style={{ 
      display: 'flex', 
      height: '100vh', 
      backgroundColor: '#000', 
      columnGap: '1px',
      overflow: 'hidden'
    }}>
      {/* LEFT: The Dashcam / Operator View */}
      <div style={{ 
        width: '450px', 
        borderRight: '1px solid #333', 
        padding: '24px', 
        backgroundColor: '#111',
        overflowY: 'auto'
      }}>
        <DashcamStream />
        
        {analysis && (
          <div style={{ 
            marginTop: '24px', 
            color: '#9ca3af', 
            fontSize: '13px', 
            backgroundColor: '#1a1a1a',
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid #262626'
          }}>
            <strong style={{ color: '#fff', display: 'block', marginBottom: '8px' }}>🚀 EdgeOps Telemetry:</strong>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{JSON.stringify(analysis, null, 2)}</pre>
          </div>
        )}
      </div>

      {/* RIGHT: The Luxury Passenger Experience */}
      <div style={{ flex: 1 }}>
        <PassengerScreen 
          avatarBase64={analysis?.image_base64} 
          statusMessage={analysis?.message} 
          isRerouting={isRerouting} 
        />
      </div>
    </div>
  );
}

export default App;
