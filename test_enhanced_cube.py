#!/usr/bin/env python3
"""
Test script for the enhanced GAN cube implementation.
This demonstrates the new features and robustness improvements.
"""

import sys
import os
import time

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def on_cube_solved():
    """Callback when cube is solved - this is where you'd stop your alarm."""
    print("🎉 CUBE SOLVED! This would stop the alarm.")
    print(f"⏰ Solved at: {time.strftime('%H:%M:%S')}")
    
    # In your alarm app, you would:
    # - Stop the alarm sound
    # - Show success message
    # - Log the solve time
    # - Reset for next alarm

def on_cube_move(move_data):
    """Callback for each cube move - shows enhanced move tracking."""
    print(f"🔄 Move: {move_data['move']} (Serial: {move_data.get('serial', 'N/A')})")
    
    # Enhanced data available:
    # - move_data['face']: Face index (0-5)
    # - move_data['direction']: 0=CW, 1=CCW  
    # - move_data['serial']: Serial number for ordering
    # - move_data['local_timestamp']: Host timestamp
    # - move_data['cube_timestamp']: Cube internal timestamp

def main():
    """Main test function."""
    print("🚀 Testing Enhanced GAN Cube Implementation")
    print("=" * 50)
    
    print("📋 Enhanced Features:")
    print("  ✅ Serial number tracking")
    print("  ✅ Missed move detection & recovery") 
    print("  ✅ Move buffering for BLE reliability")
    print("  ✅ Full cube state tracking")
    print("  ✅ Battery & hardware monitoring")
    print("  ✅ Robust connection handling")
    print()
    
    print("🔍 Looking for your GAN356 i Carry 2...")
    print("💡 Make sure your cube is:")
    print("  • Powered on (shake it)")
    print("  • Within Bluetooth range")
    print("  • Not connected to other devices")
    print()
    
    try:
        # Import here to avoid module issues
        from ble_worker import run, add_solve_callback, add_move_callback
        
        # Add callbacks for enhanced functionality
        add_solve_callback(on_cube_solved)
        add_move_callback(on_cube_move)
        
        # Start the enhanced BLE worker
        # This will now handle all the robust features automatically
        run()
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("💡 Make sure you're in the cube-alarm directory")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Try: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
