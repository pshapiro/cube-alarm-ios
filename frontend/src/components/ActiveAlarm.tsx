// SPDX-License-Identifier: LicenseRef-CubeAlarm-Custom-Attribution
// Copyright (c) 2025 Paul Shapiro
import React, { useEffect, useState, useRef } from 'react';
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
  cubeMoves: string[];
}

const ActiveAlarm: React.FC<ActiveAlarmProps> = ({
  alarm,
  cubeState,
  onStop,
  cubeSolved,
  cubeMoves
}) => {
  console.log('🚨 ActiveAlarm: Component rendered with cubeSolved =', cubeSolved, 'alarm =', alarm.label);
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [audioContext, setAudioContext] = useState<AudioContext | null>(null);
  const [alarmStartTime] = useState(Date.now());
  const isPlayingRef = useRef(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Create audio context for alarm sound
  useEffect(() => {
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    setAudioContext(ctx);
    return () => {
      ctx.close();
    };
  }, []);

  // Play alarm sound
  const playAlarmSound = () => {
    if (!audioContext || isPlayingRef.current) return;
    
    isPlayingRef.current = true;
    
    const playBeep = () => {
      // Check if we should stop playing
      if (!isPlayingRef.current || cubeSolved) {
        console.log('🔇 Stopping beep due to:', !isPlayingRef.current ? 'not playing' : 'cube solved');
        return;
      }
      
      if (!audioContext) return;
      
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
      
      // Schedule next beep
      timeoutRef.current = setTimeout(playBeep, 1500);
    };
    
    playBeep();
  };

  // Stop alarm sound
  const stopAlarmSound = () => {
    isPlayingRef.current = false;
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  };

  // Frontend alarm sound disabled - Pi handles alarm audio
  useEffect(() => {
    console.log('🔊 ActiveAlarm: Frontend alarm sound disabled - Pi handles audio');
    // No frontend alarm sound - Pi backend plays alarm locally
    return () => {
      // Cleanup only
      stopAlarmSound();
    };
  }, [audioContext]);

  // Stop alarm when cube is solved, but only after 5-second minimum to prevent immediate stops
  useEffect(() => {
    console.log('🔊 ActiveAlarm: cubeSolved changed to:', cubeSolved);
    if (cubeSolved && alarm.requires_cube_solve) {
      const alarmAge = Date.now() - alarmStartTime;
      if (alarmAge >= 5000) { // 5 second minimum
        console.log('🛑 ActiveAlarm: Stopping alarm due to cube solved after', alarmAge, 'ms');
        onStop();
      } else {
        console.log('🕒 ActiveAlarm: Cube solved but alarm too new (', alarmAge, 'ms) - ignoring');
      }
    }
  }, [cubeSolved, onStop, alarm.requires_cube_solve, alarmStartTime]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAlarmSound();
    };
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeElapsed(prev => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // TEMPORARILY DISABLED: Auto-stop logic for testing
  // useEffect(() => {
  //   // Auto-stop if cube is solved and required
  //   // But only after alarm has been active for at least 5 seconds to prevent immediate stops
  //   if (alarm.requires_cube_solve && cubeSolved) {
  //     const timeActive = Date.now() - alarmStartTime;
  //     if (timeActive >= 5000) { // 5 second minimum active time
  //       console.log('🎯 ActiveAlarm: Auto-stopping alarm - cube solved after', timeActive, 'ms');
  //       onStop();
  //     } else {
  //       console.log('🕒 ActiveAlarm: Cube solved but alarm too new (', timeActive, 'ms) - waiting...');
  //     }
  //   }
  // }, [alarm.requires_cube_solve, cubeSolved, onStop, alarmStartTime]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatAlarmTime = (time: string | undefined) => {
    if (!time || typeof time !== 'string') {
      return 'Unknown Time';
    }
    const parts = time.split(':');
    if (parts.length !== 2) {
      return time; // Return as-is if not in expected format
    }
    const [hours, minutes] = parts;
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
