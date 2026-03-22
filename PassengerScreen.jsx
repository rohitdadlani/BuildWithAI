import React, { useState, useEffect } from 'react';

const PassengerScreen = ({ avatarBase64, statusMessage, isRerouting }) => {
  const [eta, setEta] = useState(150); // 2 minutes 30 seconds = 150 seconds
  const [showAnalysis, setShowAnalysis] = useState(false);

  // Animated text sequence block
  useEffect(() => {
    if (isRerouting) {
      setShowAnalysis(true);
      const timer = setTimeout(() => {
        setShowAnalysis(false);
      }, 2500); // Show "Analyzing situation..." for 2.5s before the final status message
      return () => clearTimeout(timer);
    } else {
      setShowAnalysis(false);
    }
  }, [isRerouting, statusMessage]);

  // ETA Countdown logic: counts from 2:30 to 0:00 over 30 seconds
  // This means 150 simulated seconds drops to 0 in 30 real seconds.
  // 150 / 30 = 5 ETA seconds per 1 real second tick.
  useEffect(() => {
    let intervalId;
    if (isRerouting && eta > 0) {
      intervalId = setInterval(() => {
        setEta((prev) => Math.max(0, prev - 5)); // decrease by 5 simulated seconds
      }, 1000);
    }
    
    // Auto-reset the ETA if we stop rerouting for repeated demo usage
    if (!isRerouting) {
      setEta(150);
    }
    
    return () => clearInterval(intervalId);
  }, [isRerouting, eta]);

  const formatETA = (totalSeconds) => {
    const m = Math.floor(totalSeconds / 60);
    const s = totalSeconds % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  // Determine styling based on state
  const isPulsing = isRerouting && !showAnalysis;
  const borderStyle = isPulsing ? '0 0 50px rgba(59, 130, 246, 0.15) inset' : 'none';

  return (
    <div style={{
      width: '100%',
      height: '100vh',
      backgroundColor: '#0a0a0a',
      color: '#e5e5e5',
      fontFamily: "'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      boxSizing: 'border-box',
      overflow: 'hidden',
      padding: '40px',
      transition: 'box-shadow 1s ease-in-out, border 1s ease-in-out',
      boxShadow: borderStyle,
      border: isPulsing ? '1px solid rgba(59, 130, 246, 0.4)' : '1px solid transparent',
      position: 'relative'
    }}>
      {/* CSS Keyframes injected for pulsing borders and fade transitions */}
      <style>
        {`
          @keyframes pulse-border {
            0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.2) inset; }
            50% { box-shadow: 0 0 40px 10px rgba(59, 130, 246, 0.2) inset; }
            100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.2) inset; }
          }
          .pulse-active {
            animation: pulse-border 3s ease-in-out infinite;
          }
          @keyframes glow {
            0% { opacity: 0.5; text-shadow: 0 0 10px rgba(96, 165, 250, 0); }
            50% { opacity: 1; text-shadow: 0 0 20px rgba(96, 165, 250, 0.5); }
            100% { opacity: 0.5; text-shadow: 0 0 10px rgba(96, 165, 250, 0); }
          }
          .glow-text {
            animation: glow 1.5s ease-in-out infinite;
          }
           @keyframes fade-in {
            0% { opacity: 0; transform: translateY(15px); }
            100% { opacity: 1; transform: translateY(0); }
          }
          .fade-in {
            animation: fade-in 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
          }
        `}
      </style>

      {/* Top Header / ETA Bar */}
      <div style={{
        position: 'absolute',
        top: '40px',
        left: '40px',
        right: '40px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        paddingBottom: '20px'
      }}>
        <div style={{ fontSize: '22px', fontWeight: '300', letterSpacing: '4px', textTransform: 'uppercase' }}>
          Rocket<strong style={{ fontWeight: '700' }}>Ride</strong>
        </div>
        
        {isRerouting && (
          <div className="fade-in" style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '16px' 
          }}>
             <div style={{
              fontSize: '14px',
              textTransform: 'uppercase',
              color: '#9ca3af',
              letterSpacing: '1.5px',
              fontWeight: '500'
            }}>Est. Arrival</div>
            <div style={{
              fontSize: '36px',
              fontWeight: '200',
              color: '#60a5fa',
              fontVariantNumeric: 'tabular-nums'
            }}>
              {formatETA(eta)}
            </div>
          </div>
        )}
      </div>

      {/* Center Content Wrapper */}
      <div className={isPulsing ? 'pulse-active' : ''} style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        flex: 1,
        width: '100%',
        maxWidth: '900px',
        textAlign: 'center'
      }}>

        {/* Dynamic Avatar Display */}
        {avatarBase64 ? (
          <div className="fade-in" style={{
            width: '240px',
            height: '240px',
            borderRadius: '50%',
            overflow: 'hidden',
            marginBottom: '48px',
            background: '#1a1a1a',
            border: '4px solid #262626',
            boxShadow: '0 20px 50px rgba(0,0,0,0.6)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'border 0.5s',
            borderColor: isRerouting ? '#3b82f6' : '#262626'
          }}>
            {/* Some platforms output base64 with data prefix, some without. */}
            {/* If it lacks the prefix, we prepend it for the img src. */}
            <img 
              src={avatarBase64.startsWith('data:') ? avatarBase64 : `data:image/jpeg;base64,${avatarBase64}`} 
              alt="AI AV System Avatar" 
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          </div>
        ) : (
          <div className="fade-in" style={{
            width: '240px',
            height: '240px',
            borderRadius: '50%',
            marginBottom: '48px',
            background: 'linear-gradient(135deg, #1f2937, #111827)',
            border: '4px solid #374151',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 20px 50px rgba(0,0,0,0.6)'
          }}>
             <span style={{ fontSize: '80px', filter: 'grayscale(0.5)' }}>🤖</span>
          </div>
        )}

        {/* Status Messaging Area */}
        <div style={{ minHeight: '140px', width: '100%' }}>
          {isRerouting ? (
            showAnalysis ? (
              <h2 className="glow-text" style={{ 
                fontSize: '44px', 
                fontWeight: '300', 
                color: '#60a5fa',
                margin: 0,
                letterSpacing: '1px'
              }}>
                Analyzing scenario...
              </h2>
            ) : (
              <div className="fade-in">
                <h2 style={{ 
                  fontSize: '48px', 
                  fontWeight: '400', 
                  color: '#ffffff',
                  margin: '0 0 20px 0',
                  lineHeight: '1.2',
                  letterSpacing: '0.5px'
                }}>
                  Course Corrected
                </h2>
                <p style={{ 
                  fontSize: '28px', 
                  color: '#9ca3af', 
                  margin: '0 auto',
                  maxWidth: '750px',
                  lineHeight: '1.4',
                  fontWeight: '300'
                }}>
                  {statusMessage || "We are rerouting to dynamically avoid a delay in your ride."}
                </p>
              </div>
            )
          ) : (
            <div className="fade-in">
              <h2 style={{ 
                fontSize: '48px', 
                fontWeight: '300', 
                color: '#ffffff',
                margin: '0 0 20px 0',
                letterSpacing: '0.5px'
              }}>
                Enjoy your ride.
              </h2>
              <p style={{ 
                fontSize: '28px', 
                color: '#6b7280', 
                margin: '0 auto',
                fontWeight: '300',
                maxWidth: '750px'
              }}>
                {statusMessage || "Cruising smoothly to your destination."}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PassengerScreen;
