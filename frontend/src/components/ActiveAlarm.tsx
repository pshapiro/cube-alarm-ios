import React, { useEffect, useState } from 'react';
import { Alarm } from '../App';
import './ActiveAlarm.css';

interface CubeState {
  connected: boolean;
  solved: boolean;
  lastMove: string;
}

interface ActiveAlarmProps {
  alarm: Alarm;
  cubeState: CubeState;
  onStop: () => Promise<void>;
  cubeSolved: boolean;
}

const ActiveAlarm: React.FC<ActiveAlarmProps> = ({ 
  alarm, 
  cubeState, 
  onStop, 
  cubeSolved 
}) => {
  const [timeElapsed, setTimeElapsed] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeElapsed(prev => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Auto-stop if cube is solved and required
    if (alarm.requires_cube_solve && cubeSolved) {
      onStop();
    }
  }, [alarm.requires_cube_solve, cubeSolved, onStop]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatAlarmTime = (time: string) => {
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  return (
    <div className="active-alarm-overlay">
      <div className="active-alarm-container">
        <div className="alarm-icon">
          <span className="alarm-emoji">🚨</span>
        </div>
        
        <div className="alarm-info">
          <h1 className="alarm-title">{alarm.label}</h1>
          <div className="alarm-time">{formatAlarmTime(alarm.time)}</div>
          <div className="alarm-elapsed">
            Ringing for {formatTime(timeElapsed)}
          </div>
        </div>

        {alarm.requires_cube_solve ? (
          <div className="cube-solve-section">
            <div className="cube-instruction">
              <span className="cube-icon">🧩</span>
              <p>Solve the Rubik's cube to stop this alarm</p>
            </div>
            
            <div className={`cube-status ${cubeSolved ? 'solved' : 'scrambled'}`}>
              {cubeSolved ? (
                <>
                  <span className="status-icon">✅</span>
                  <span>Cube solved! Stopping alarm...</span>
                </>
              ) : (
                <>
                  <span className="status-icon">🔄</span>
                  <span>Cube is scrambled - keep solving!</span>
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="manual-stop-section">
            <button className="stop-alarm-btn" onClick={onStop}>
              Stop Alarm
            </button>
          </div>
        )}

        {alarm.requires_cube_solve && (
          <div className="emergency-stop">
            <button className="emergency-stop-btn" onClick={onStop}>
              Emergency Stop
            </button>
            <p className="emergency-note">
              Use only in emergencies - defeats the purpose of the cube alarm!
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActiveAlarm;
