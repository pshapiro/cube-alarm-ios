#!/usr/bin/env python3
"""
Simple test script for the enhanced GAN cube implementation.
Run this to test your cube connection and see the enhanced features in action.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Test the original simple approach first
if __name__ == "__main__":
    print("🚀 Testing Enhanced GAN Cube Implementation")
    print("=" * 50)
    
    print("📋 Enhanced Features Added:")
    print("  ✅ Serial number tracking for move ordering")
    print("  ✅ Missed move detection & recovery") 
    print("  ✅ Move buffering to handle BLE packet loss")
    print("  ✅ Full cube state tracking for reliable solve detection")
    print("  ✅ Battery & hardware monitoring")
    print("  ✅ Robust connection handling with retry logic")
    print("  ✅ Enhanced logging with timestamps")
    print()
    
    print("🔍 Looking for your GAN356 i Carry 2...")
    print("💡 Make sure your cube is:")
    print("  • Powered on (shake it to wake up)")
    print("  • Within Bluetooth range (~10 feet)")
    print("  • Not connected to other apps/devices")
    print()
    
    try:
        # Import the enhanced BLE worker
        import ble_worker
        
        print("🎯 Starting enhanced cube monitoring...")
        print("🔄 Move your cube to see enhanced move tracking!")
        print("🎉 Solve your cube to test solve detection!")
        print("⏹️  Press Ctrl+C to stop")
        print()
        
        # This will use all the enhanced features automatically
        ble_worker.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("💡 Make sure you're in the cube-alarm directory")
        print("💡 Try: cd /Users/paulshapiro/Documents/Development/rubiks_alarm/cube-alarm")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Check that all dependencies are installed: pip install -r requirements.txt")
        print("💡 Make sure Bluetooth is enabled on your Mac")
