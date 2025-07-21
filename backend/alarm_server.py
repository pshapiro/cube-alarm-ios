#!/usr/bin/env python3
"""
Alarm Clock Server with WebSocket support for GAN Cube integration.
Provides REST API for alarm management and WebSocket for real-time updates.
"""

import asyncio
import json
import logging
from datetime import datetime, time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import threading


from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import schedule

from cube_worker import GanCubeWorker
from gan_decrypt import CubeMove, SolvedEvent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global cube worker instance
cube_worker = None

@dataclass
class Alarm:
    """Represents an alarm clock entry."""
    id: str
    time: str  # Format: "HH:MM"
    days: List[str]  # ["monday", "tuesday", etc.]
    enabled: bool
    label: str
    requires_cube_solve: bool = True
    is_active: bool = False  # Currently ringing
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

class AlarmManager:
    """Manages alarm scheduling and triggering."""
    
    def __init__(self):
        self.alarms: Dict[str, Alarm] = {}
        self.active_alarms: Set[str] = set()
        self.cube_solved = False
        self.cube_connected = False
        self.last_cube_state = ""
        
    def add_alarm(self, alarm: Alarm) -> bool:
        """Add a new alarm."""
        self.alarms[alarm.id] = alarm
        if alarm.enabled:
            self._schedule_alarm(alarm)
        return True
    
    def update_alarm(self, alarm_id: str, updates: dict) -> bool:
        """Update an existing alarm."""
        if alarm_id not in self.alarms:
            return False
        
        alarm = self.alarms[alarm_id]
        
        # Update fields
        for key, value in updates.items():
            if hasattr(alarm, key):
                setattr(alarm, key, value)
        
        # Reschedule if needed
        if alarm.enabled:
            self._schedule_alarm(alarm)
        else:
            self._unschedule_alarm(alarm)
        
        return True
    
    def delete_alarm(self, alarm_id: str) -> bool:
        """Delete an alarm."""
        if alarm_id not in self.alarms:
            return False
        
        self._unschedule_alarm(self.alarms[alarm_id])
        del self.alarms[alarm_id]
        return True
    
    def get_alarms(self) -> List[Dict]:
        """Get all alarms."""
        return [asdict(alarm) for alarm in self.alarms.values()]
    
    def trigger_alarm(self, alarm_id: str):
        """Trigger an alarm."""
        if alarm_id not in self.alarms:
            return
        
        alarm = self.alarms[alarm_id]
        alarm.is_active = True
        self.active_alarms.add(alarm_id)
        
        logger.info(f"🚨 Alarm triggered: {alarm.label} at {alarm.time}")
        
        # Emit to all connected clients
        socketio.emit('alarm_triggered', {
            'alarm': asdict(alarm),
            'timestamp': datetime.now().isoformat()
        })
    
    def stop_alarm(self, alarm_id: str, solved_by_cube: bool = False):
        """Stop an active alarm."""
        if alarm_id not in self.alarms:
            return False
        
        alarm = self.alarms[alarm_id]
        if not alarm.is_active:
            return False
        
        alarm.is_active = False
        self.active_alarms.discard(alarm_id)
        
        logger.info(f"⏰ Alarm stopped: {alarm.label} {'by cube solve' if solved_by_cube else 'manually'}")
        
        # Emit to all connected clients
        socketio.emit('alarm_stopped', {
            'alarm': asdict(alarm),
            'solved_by_cube': solved_by_cube,
            'timestamp': datetime.now().isoformat()
        })
        
        return True
    
    def on_cube_solved(self):
        """Handle cube solved event."""
        self.cube_solved = True
        logger.info("🎉 Cube solved! Checking for active alarms...")
        logger.info(f"🔍 DEBUG: Active alarms: {list(self.active_alarms)}")
        
        # Stop all active alarms that require cube solve
        for alarm_id in list(self.active_alarms):
            alarm = self.alarms[alarm_id]
            logger.info(f"🔍 DEBUG: Checking alarm {alarm_id}: requires_cube_solve={alarm.requires_cube_solve}")
            if alarm.requires_cube_solve:
                logger.info(f"🚨 DEBUG: Stopping alarm {alarm_id} due to cube solved")
                self.stop_alarm(alarm_id, solved_by_cube=True)
        
        # Emit cube state update
        socketio.emit('cube_solved', {
            'timestamp': datetime.now().isoformat()
        })
    
    def on_cube_move(self, move: CubeMove):
        """Handle cube move event."""
        self.cube_solved = False
        
        # Emit cube move update
        socketio.emit('cube_move', {
            'face': move.face,
            'direction': move.direction,
            'timestamp': datetime.now().isoformat()
        })
    
    def on_cube_connected(self, connected: bool):
        """Handle cube connection status."""
        self.cube_connected = connected
        logger.info(f"📱 Cube {'connected' if connected else 'disconnected'}")
        
        socketio.emit('cube_connected', {
            'connected': connected,
            'timestamp': datetime.now().isoformat()
        })
    
    def _schedule_alarm(self, alarm: Alarm):
        """Schedule an alarm with the scheduler."""
        # Clear existing schedule for this alarm
        self._unschedule_alarm(alarm)
        
        # Schedule for each day
        for day in alarm.days:
            getattr(schedule.every(), day.lower()).at(alarm.time).do(
                self.trigger_alarm, alarm.id
            ).tag(alarm.id)
    
    def _unschedule_alarm(self, alarm: Alarm):
        """Remove alarm from scheduler."""
        schedule.clear(alarm.id)

# Global instances
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
alarm_manager = AlarmManager()

# REST API Routes
@app.route('/api/alarms', methods=['GET'])
def get_alarms():
    """Get all alarms."""
    return jsonify(alarm_manager.get_alarms())

@app.route('/api/alarms', methods=['POST'])
def create_alarm():
    """Create a new alarm."""
    data = request.json
    
    # Generate ID if not provided
    if 'id' not in data:
        data['id'] = f"alarm_{datetime.now().timestamp()}"
    
    try:
        alarm = Alarm(**data)
        success = alarm_manager.add_alarm(alarm)
        
        if success:
            socketio.emit('alarm_created', asdict(alarm))
            return jsonify(asdict(alarm)), 201
        else:
            return jsonify({'error': 'Failed to create alarm'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/alarms/<alarm_id>', methods=['PUT'])
def update_alarm(alarm_id):
    """Update an existing alarm."""
    data = request.json
    success = alarm_manager.update_alarm(alarm_id, data)
    
    if success:
        alarm = alarm_manager.alarms[alarm_id]
        socketio.emit('alarm_updated', asdict(alarm))
        return jsonify(asdict(alarm))
    else:
        return jsonify({'error': 'Alarm not found'}), 404

@app.route('/api/alarms/<alarm_id>', methods=['DELETE'])
def delete_alarm(alarm_id):
    """Delete an alarm."""
    success = alarm_manager.delete_alarm(alarm_id)
    
    if success:
        socketio.emit('alarm_deleted', {'id': alarm_id})
        return '', 204
    else:
        return jsonify({'error': 'Alarm not found'}), 404

@app.route('/api/alarms/<alarm_id>/stop', methods=['POST'])
def stop_alarm(alarm_id):
    """Manually stop an active alarm."""
    success = alarm_manager.stop_alarm(alarm_id, solved_by_cube=False)
    
    if success:
        return jsonify({'message': 'Alarm stopped'})
    else:
        return jsonify({'error': 'Alarm not found or not active'}), 404

@app.route('/api/cube/status', methods=['GET'])
def get_cube_status():
    """Get current cube connection and solved status."""
    return jsonify({
        'connected': alarm_manager.cube_connected,
        'solved': alarm_manager.cube_solved
    })

@app.route('/api/cube/reset', methods=['POST'])
def reset_cube_state():
    """Reset cube state to solved (like official GAN app)."""
    try:
        logger.info("🔄 Reset cube state requested")
        if cube_worker:
            logger.info(f"📱 Cube worker available: {type(cube_worker)}")
            # Force cube state to solved
            cube_worker.force_solved_state()
            socketio.emit('cube_solved')
            logger.info("✅ Cube state reset successful")
            return jsonify({'success': True, 'message': 'Cube state reset to solved'})
        else:
            logger.error("❌ Cube worker not available")
            return jsonify({'error': 'Cube worker not available'}), 500
    except Exception as e:
        logger.error(f"❌ Error resetting cube state: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status."""
    return jsonify({
        'cube_connected': alarm_manager.cube_connected,
        'cube_solved': alarm_manager.cube_solved,
        'active_alarms': len(alarm_manager.active_alarms),
        'total_alarms': len(alarm_manager.alarms),
        'timestamp': datetime.now().isoformat()
    })

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info("Client connected")
    emit('status', {
        'cube_connected': alarm_manager.cube_connected,
        'cube_solved': alarm_manager.cube_solved,
        'active_alarms': len(alarm_manager.active_alarms),
        'alarms': alarm_manager.get_alarms()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info("Client disconnected")

# Cube Worker Integration

def run_cube_worker():
    """Run the cube worker in a separate thread."""
    global cube_worker
    cube_worker = GanCubeWorker()
    
    # Import BLE worker functions to register callbacks directly
    from ble_worker import add_solve_callback, add_move_callback, add_connection_callback, run
    
    # Set up event callbacks directly with BLE worker (bypass cube worker)
    def on_move_direct(move_dict):
        """Direct callback from BLE worker to alarm manager."""
        try:
            # Convert dict to CubeMove object like cube worker does
            move_obj = CubeMove(
                face=move_dict.get('face', 0),
                direction=move_dict.get('direction', 0),
                move=move_dict.get('move', ''),
                serial=move_dict.get('serial', 0),
                local_timestamp=move_dict.get('local_timestamp'),
                cube_timestamp=move_dict.get('cube_timestamp')
            )
            alarm_manager.on_cube_move(move_obj)
        except Exception as e:
            logger.error(f"❌ Error in direct move callback: {e}")
        
    def on_solved_direct():
        """Direct callback from BLE worker to alarm manager."""
        try:
            logger.info("🎯 DEBUG: Received solved event DIRECTLY from BLE worker!")
            alarm_manager.on_cube_solved()
        except Exception as e:
            logger.error(f"❌ Error in direct solved callback: {e}")
    
    def on_connected_direct(connected: bool):
        """Direct callback from BLE worker to alarm manager for connection status."""
        try:
            logger.info(f"🎯 DEBUG: Received connection event DIRECTLY from BLE worker: {connected}")
            alarm_manager.on_cube_connected(connected)
        except Exception as e:
            logger.error(f"❌ Error in direct connection callback: {e}")
    
    # Register callbacks DIRECTLY with BLE worker
    logger.info("🎯 DEBUG: Registering callbacks DIRECTLY with BLE worker")
    add_move_callback(on_move_direct)
    add_solve_callback(on_solved_direct)
    add_connection_callback(on_connected_direct)
    
    # Set up cube worker callbacks for compatibility
    def on_move(move: CubeMove):
        alarm_manager.on_cube_move(move)
        
    def on_solved(solved_event: SolvedEvent):
        logger.info(f"🎯 DEBUG: Received solved event in alarm server: {solved_event}")
        alarm_manager.on_cube_solved()
        
    def on_connected(connected: bool):
        alarm_manager.on_cube_connected(connected)
    
    # Set callbacks on cube worker for compatibility
    cube_worker.on_move = on_move
    cube_worker.on_solved = on_solved
    cube_worker.on_connected = on_connected
    
    # Run BLE worker directly instead of through cube worker
    logger.info("🎯 DEBUG: Starting BLE worker directly")
    try:
        run(socketio)  # Run BLE worker directly with socketio
        logger.info("🎯 DEBUG: BLE worker completed")
    except Exception as e:
        logger.error(f"BLE worker error: {e}")
        import traceback
        logger.error(f"BLE worker traceback: {traceback.format_exc()}")

def run_scheduler():
    """Run the alarm scheduler in a separate thread."""
    while True:
        schedule.run_pending()
        threading.Event().wait(1)

if __name__ == '__main__':
    # Start cube worker thread
    cube_thread = threading.Thread(target=run_cube_worker, daemon=True)
    cube_thread.start()
    
    # Start scheduler thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("🚀 Starting Rubik's Cube Alarm Server...")
    logger.info("📱 Cube worker started")
    logger.info("⏰ Scheduler started")
    logger.info("🌐 API server starting on http://localhost:5001")
    
    # Run Flask-SocketIO server
    socketio.run(app, host='0.0.0.0', port=5001, debug=False)
