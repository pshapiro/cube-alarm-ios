#!/usr/bin/env python3
"""
GAN Cube Worker class for integration with alarm server.
Provides a clean interface for cube events and connection management.
"""

import asyncio
import os
import threading
import time
from typing import Optional, Callable, List

# Import the working ble_worker functions directly
from ble_worker import run, add_move_callback, add_solve_callback
from gan_decrypt import CubeMove, SolvedEvent

class GanCubeWorker:
    """Simple wrapper around the working ble_worker.py."""
    
    def __init__(self):
        self.on_move: Optional[Callable] = None
        self.on_solved: Optional[Callable] = None
        self.on_connected: Optional[Callable] = None
        
        self.running = False
        self._thread = None
        self._socketio = None
    
    def _log(self, message: str):
        """Log with timestamp."""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        print(f"[{timestamp}] {message}")
    
    def start(self, socketio_ref=None):
        """Start the cube worker using the working ble_worker.py."""
        if self.running:
            return
        
        self.running = True
        self._socketio = socketio_ref
        
        # Set up callbacks for the working ble_worker
        if self.on_move:
            add_move_callback(self._move_wrapper)
        
        if self.on_solved:
            add_solve_callback(self._solved_wrapper)
        
        # Start the working ble_worker in a thread
        self._thread = threading.Thread(target=self._run_ble_worker, daemon=True)
        self._thread.start()
        
        self._log("🚀 Started GAN cube worker using working ble_worker.py")
    
    def stop(self):
        """Stop the cube worker."""
        self.running = False
        self._log("🛑 Stopping GAN cube worker...")
        if self._thread:
            self._thread.join(timeout=5.0)
    
    def force_solved_state(self):
        """Force cube state to solved (like official GAN app reset button)."""
        try:
            self._log("🔄 Manually resetting cube state to solved")
            if self.on_solved:
                solved_event = SolvedEvent(serial=0, timestamp=time.time())
                self.on_solved(solved_event)
                self._log("✅ Successfully triggered solved event")
            else:
                self._log("⚠️ Warning: on_solved callback not set")
                # Still return success since this isn't a critical error
        except Exception as e:
            self._log(f"❌ Error forcing solved state: {e}")
            raise  # Re-raise the exception so the API can return a proper error
    
    def is_connected(self) -> bool:
        """Check if cube is connected."""
        return self.running
    
    def is_solved(self) -> bool:
        """Check if cube is currently solved (placeholder - could track state)."""
        # This could be enhanced to track actual cube state
        return False
    
    def _run_ble_worker(self):
        """Run the working ble_worker.py."""
        try:
            # Use the working ble_worker.py directly
            run(self._socketio)
        except Exception as e:
            self._log(f"❌ BLE worker error: {e}")
    
    def _move_wrapper(self, move_dict):
        """Wrapper for move callbacks - converts dict to CubeMove object."""
        try:
            if self.on_move:
                # Convert dictionary to CubeMove object
                move_obj = CubeMove(
                    face=move_dict.get('face', 0),
                    direction=move_dict.get('direction', 0),
                    move=move_dict.get('move', ''),
                    serial=move_dict.get('serial', 0),
                    local_timestamp=move_dict.get('local_timestamp'),
                    cube_timestamp=move_dict.get('cube_timestamp')
                )
                self.on_move(move_obj)
        except Exception as e:
            self._log(f"❌ Error in move callback: {e}")
            self._log(f"❌ Move dict: {move_dict}")
    
    def _solved_wrapper(self):
        """Wrapper for solved callbacks."""
        try:
            if self.on_solved:
                # Create a SolvedEvent object like the original implementation
                solved_event = SolvedEvent(serial=0, timestamp=time.time())
                self.on_solved(solved_event)
        except Exception as e:
            self._log(f"❌ Error in solved callback: {e}")
    
    def run_sync(self, socketio_ref=None):
        """Run the cube worker (blocking) - interface expected by alarm_server.py."""
        try:
            # Set socketio reference if provided
            if socketio_ref:
                self._socketio = socketio_ref
            
            # Start the cube worker using the working ble_worker.py
            self.start(self._socketio)
            
            # Keep the thread alive
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self._log("🛑 BLE loop cancelled")
            self.stop()
        except Exception as e:
            self._log(f"💥 Worker error: {e}")
            self.stop()

if __name__ == "__main__":
    worker = GanCubeWorker()
    
    # Set up event handlers for testing
    def on_move(move: CubeMove):
        direction_str = "'" if move.direction == 1 else ""
        print(f"🔄 Move: {move.face}{direction_str} (serial: {move.serial})")
    
    def on_solved(solved_event: SolvedEvent):
        print(f"🎉 Cube solved! (serial: {solved_event.serial})")
    
    def on_connected(connected: bool):
        status = 'connected' if connected else 'disconnected'
        print(f"📱 Cube {status}")
    
    worker.on_move = on_move
    worker.on_solved = on_solved
    worker.on_connected = on_connected
    
    worker.run_sync()
