// SPDX-License-Identifier: LicenseRef-CubeAlarm-Custom-Attribution
// Copyright (c) 2025 Paul Shapiro
import React from 'react';
import './CubeStatus.css';

interface CubeStatusProps {
  connected: boolean;
  solved: boolean;
  alarmCount: number;
  lastMove: string;
  onResetCubeState?: () => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onVisualizeCube?: () => void;
}

const CubeStatus: React.FC<CubeStatusProps> = ({ connected, solved, alarmCount, onResetCubeState, onConnect, onDisconnect, onVisualizeCube }) => {
  // Debug logging
  console.log('CubeStatus render:', { connected, solved, hasResetCallback: !!onResetCubeState });
  
  return (
    <div className="cube-status">
      <div className={`status-item ${connected ? 'connected' : 'disconnected'}`}>
        <span className="status-icon">
          {connected ? '📱' : '📵'}
        </span>
        <span className="status-text">
          {connected ? 'Cube Connected' : 'Cube Disconnected'}
        </span>
      </div>
      
      <div className={`status-item ${solved ? 'solved' : 'scrambled'}`}>
        <span className="status-icon">
          {solved ? '✅' : '🧩'}
        </span>
        <span className="status-text">
          {solved ? 'Solved' : 'Scrambled'}
        </span>
      </div>

      {!connected && onConnect && (
        <div className="status-item">
          <button className="reset-cube-btn" onClick={onConnect}>🔌 Connect</button>
        </div>
      )}

      {connected && onDisconnect && (
        <div className="status-item">
          <button className="reset-cube-btn" onClick={onDisconnect}>🔌 Disconnect</button>
        </div>
      )}
      
      {connected && onResetCubeState && (
        <div className="status-item reset-button">
          <button 
            className="reset-cube-btn"
            onClick={onResetCubeState}
            title="Reset cube state to solved (like official GAN app)"
          >
            🔄 Reset State
          </button>
        </div>
      )}

      {connected && onVisualizeCube && (
        <div className="status-item">
          <button className="reset-cube-btn" onClick={onVisualizeCube}>
            👁️ Visualize Cube
          </button>
        </div>
      )}
      
      <div className="status-item">
        <span className="status-icon">⏰</span>
        <span className="status-text">
          {alarmCount} Active Alarms
        </span>
      </div>
    </div>
  );
};

export default CubeStatus;
