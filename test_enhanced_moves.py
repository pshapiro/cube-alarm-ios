#!/usr/bin/env python3
"""
Test enhanced GAN cube backend with specific move detection and solve state.
"""

import sys
import os
import asyncio
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.enhanced_gan_cube import EnhancedGANCube

def main():
    """Test enhanced cube functionality."""
    print("🎯 Enhanced GAN Cube Move Detection Test")
    print("=" * 50)
    print("Features being tested:")
    print("✅ Specific move detection (U, R, F, D, L, B with prime notation)")
    print("✅ Solved state detection")
    print("✅ Move counting and timing")
    print("✅ Real MAC address extraction and decryption")
    print()
    print("Expected improvements:")
    print("🔄 Should show moves like 'U', 'R'', 'F', etc. (not just 'Move1', 'Move2')")
    print("🎉 Should detect when cube reaches solved state")
    print("📊 Should track move count and timing accurately")
    print()
    print("Move your cube to test enhanced detection!")
    print("Press Ctrl+C to stop.")
    print()

    cube = EnhancedGANCube()
    
    def on_move(move):
        """Handle move events."""
        state = cube.get_cube_state()
        print(f"🔄 MOVE: {move.move} | Serial: {move.serial} | Total: {state.move_count} | Solved: {'🎉 YES' if state.is_solved else '❌ NO'}")
        
        if move.face and move.direction:
            print(f"   📝 Details: Face={move.face}, Direction='{move.direction}', Time={move.timestamp:.2f}")
    
    def on_solve():
        """Handle solve events."""
        print()
        print("🎉" * 20)
        print("🎉 CUBE SOLVED! ALARM WOULD BE DISMISSED! 🎉")
        print("🎉" * 20)
        print()
    
    cube.set_move_callback(on_move)
    cube.set_solve_callback(on_solve)
    
    try:
        asyncio.run(cube.run())
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
        print()
        
        # Show final statistics
        state = cube.get_cube_state()
        conn_state = cube.state
        
        print("📊 Final Statistics:")
        print(f"   Connected: {conn_state.connected}")
        print(f"   Device: {conn_state.device_name}")
        print(f"   MAC: {conn_state.mac_address}")
        print(f"   Total Moves: {state.move_count}")
        print(f"   Final State: {'🎉 SOLVED' if state.is_solved else '❌ NOT SOLVED'}")
        if state.last_move:
            print(f"   Last Move: {state.last_move.move}")
        print()
        print("✅ Enhanced cube backend test complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
