import React, { useState } from 'react';
import { Alarm } from '../App';
import './AlarmForm.css';

interface AlarmFormProps {
  onSubmit?: (alarm: Partial<Alarm>) => void;
  onSave?: (alarmData: Omit<Alarm, "id">) => Promise<void>;
  onCancel: () => void;
  alarm?: Alarm; // For editing existing alarms
}

const AlarmForm: React.FC<AlarmFormProps> = ({ onSubmit, onSave, onCancel, alarm }) => {
  const [formData, setFormData] = useState({
    time: alarm?.time || '07:00',
    label: alarm?.label || '',
    days: alarm?.days || ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
    enabled: alarm?.enabled ?? true,
    requires_cube_solve: alarm?.requires_cube_solve ?? true
  });

  const dayOptions = [
    { key: 'monday', label: 'Monday' },
    { key: 'tuesday', label: 'Tuesday' },
    { key: 'wednesday', label: 'Wednesday' },
    { key: 'thursday', label: 'Thursday' },
    { key: 'friday', label: 'Friday' },
    { key: 'saturday', label: 'Saturday' },
    { key: 'sunday', label: 'Sunday' }
  ];

  const handleDayToggle = (day: string) => {
    setFormData(prev => ({
      ...prev,
      days: prev.days.includes(day)
        ? prev.days.filter(d => d !== day)
        : [...prev.days, day]
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.label.trim()) {
      alert('Please enter a label for the alarm');
      return;
    }
    
    if (formData.days.length === 0) {
      alert('Please select at least one day');
      return;
    }

    // Use onSave if available (for editing), otherwise use onSubmit (for creating)
    if (onSave) {
      onSave(formData);
    } else if (onSubmit) {
      onSubmit(formData);
    }
  };

  const selectAllDays = () => {
    setFormData(prev => ({
      ...prev,
      days: dayOptions.map(d => d.key)
    }));
  };

  const selectWeekdays = () => {
    setFormData(prev => ({
      ...prev,
      days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    }));
  };

  const selectWeekends = () => {
    setFormData(prev => ({
      ...prev,
      days: ['saturday', 'sunday']
    }));
  };

  const clearDays = () => {
    setFormData(prev => ({
      ...prev,
      days: []
    }));
  };

  return (
    <div className="alarm-form-overlay">
      <div className="alarm-form-container">
        <div className="alarm-form-header">
          <h2>{alarm ? 'Edit Alarm' : 'Add New Alarm'}</h2>
          <button className="close-btn" onClick={onCancel}>×</button>
        </div>

        <form onSubmit={handleSubmit} className="alarm-form">
          <div className="form-group">
            <label htmlFor="time">Time</label>
            <input
              type="time"
              id="time"
              value={formData.time}
              onChange={(e) => setFormData(prev => ({ ...prev, time: e.target.value }))}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="label">Label</label>
            <input
              type="text"
              id="label"
              placeholder="e.g., Wake up, Meeting, etc."
              value={formData.label}
              onChange={(e) => setFormData(prev => ({ ...prev, label: e.target.value }))}
              required
            />
          </div>

          <div className="form-group">
            <label>Days</label>
            <div className="day-presets">
              <button type="button" onClick={selectAllDays}>All Days</button>
              <button type="button" onClick={selectWeekdays}>Weekdays</button>
              <button type="button" onClick={selectWeekends}>Weekends</button>
              <button type="button" onClick={clearDays}>Clear</button>
            </div>
            <div className="day-checkboxes">
              {dayOptions.map(day => (
                <label key={day.key} className="day-checkbox">
                  <input
                    type="checkbox"
                    checked={formData.days.includes(day.key)}
                    onChange={() => handleDayToggle(day.key)}
                  />
                  <span>{day.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.requires_cube_solve}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  requires_cube_solve: e.target.checked 
                }))}
              />
              <span>Require cube solve to stop alarm</span>
            </label>
            <div className="checkbox-help">
              When enabled, you must solve the Rubik's cube to stop the alarm
            </div>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.enabled}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  enabled: e.target.checked 
                }))}
              />
              <span>Enable alarm</span>
            </label>
          </div>

          <div className="form-actions">
            <button type="button" onClick={onCancel} className="cancel-btn">
              Cancel
            </button>
            <button type="submit" className="submit-btn">
              {alarm ? 'Update Alarm' : 'Create Alarm'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AlarmForm;
