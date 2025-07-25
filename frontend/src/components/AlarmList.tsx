// SPDX-License-Identifier: LicenseRef-CubeAlarm-Custom-Attribution
// Copyright (c) 2025 Paul Shapiro
import React from 'react';
import { Alarm } from '../App';
import './AlarmList.css';

interface AlarmListProps {
  alarms: Alarm[];
  onToggle: (id: string, enabled: boolean) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onEdit: (alarm: Alarm) => void;
}

const AlarmList: React.FC<AlarmListProps> = ({ alarms, onToggle, onDelete, onEdit }) => {
  const formatTime = (time: string) => {
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  const formatDays = (days: string[]) => {
    if (days.length === 7) return 'Every day';
    if (days.length === 5 && !days.includes('saturday') && !days.includes('sunday')) {
      return 'Weekdays';
    }
    if (days.length === 2 && days.includes('saturday') && days.includes('sunday')) {
      return 'Weekends';
    }
    
    const dayAbbr = {
      monday: 'Mon',
      tuesday: 'Tue',
      wednesday: 'Wed',
      thursday: 'Thu',
      friday: 'Fri',
      saturday: 'Sat',
      sunday: 'Sun'
    };
    
    return days.map(day => dayAbbr[day as keyof typeof dayAbbr]).join(', ');
  };

  const handleToggle = (id: string) => {
    const alarm = alarms.find(a => a.id === id);
    if (alarm) {
      onToggle(id, !alarm.enabled);
    }
  };

  if (alarms.length === 0) {
    return (
      <div className="alarm-list-empty">
        <p>No alarms set</p>
        <p>Click "Add Alarm" to create your first alarm</p>
      </div>
    );
  }

  return (
    <div className="alarm-list">
      {alarms.map((alarm) => (
        <div 
          key={alarm.id} 
          className={`alarm-item ${alarm.enabled ? 'enabled' : 'disabled'} ${alarm.is_active ? 'active' : ''}`}
        >
          <div className="alarm-main">
            <div className="alarm-time">
              {formatTime(alarm.time)}
            </div>
            <div className="alarm-details">
              <div className="alarm-label">{alarm.label}</div>
              <div className="alarm-days">{formatDays(alarm.days)}</div>
              {alarm.requires_cube_solve && (
                <div className="cube-required">
                  🧩 Requires cube solve
                </div>
              )}
            </div>
          </div>
          
          <div className="alarm-controls">
            <button
              className={`toggle-btn ${alarm.enabled ? 'enabled' : 'disabled'}`}
              onClick={() => handleToggle(alarm.id)}
              title={alarm.enabled ? 'Disable alarm' : 'Enable alarm'}
            >
              {alarm.enabled ? '🔔' : '🔕'}
            </button>
            
            <button
              className="delete-btn"
              onClick={() => onDelete(alarm.id)}
              title="Delete alarm"
            >
              🗑️
            </button>
          </div>
          
          {alarm.is_active && (
            <div className="alarm-active-indicator">
              <span className="pulse">🚨</span>
              RINGING
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default AlarmList;
