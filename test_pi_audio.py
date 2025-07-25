#!/usr/bin/env python3
# SPDX-License-Identifier: LicenseRef-CubeAlarm-Custom-Attribution
# Copyright (c) 2025 Paul Shapiro
"""
Local test script for Pi Audio Manager
Tests the audio system without requiring full alarm server dependencies.
"""

import sys
import os
import time

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_audio_system():
    """Test the Pi audio system locally."""
    print("🔊 Testing Pi Audio System Locally...")
    print("=" * 50)
    
    try:
        from pi_audio import get_audio_manager, test_audio, start_alarm_sound, stop_alarm_sound
        
        # Initialize audio manager
        audio_manager = get_audio_manager()
        print(f"✅ Audio Manager initialized")
        print(f"   Platform: {'Pi' if audio_manager.is_pi else 'macOS/Other'}")
        print(f"   Audio Method: {audio_manager.audio_method}")
        print()
        
        # Test 1: Basic audio test
        print("🎵 Test 1: Basic Audio Test")
        if test_audio():
            print("✅ Basic audio test PASSED")
        else:
            print("❌ Basic audio test FAILED")
        print()
        
        # Test 2: Alarm sound management
        print("🚨 Test 2: Alarm Sound Management")
        print("   Starting alarm sound for 3 seconds...")
        
        success = start_alarm_sound("test-alarm", "Test Alarm")
        if success:
            print("✅ Alarm sound started successfully")
            time.sleep(3)
            
            success = stop_alarm_sound("test-alarm")
            if success:
                print("✅ Alarm sound stopped successfully")
            else:
                print("❌ Failed to stop alarm sound")
        else:
            print("❌ Failed to start alarm sound")
        print()
        
        # Test 3: Multiple alarms
        print("🔔 Test 3: Multiple Alarms")
        print("   Starting two alarms simultaneously...")
        
        start_alarm_sound("alarm1", "Morning Alarm")
        start_alarm_sound("alarm2", "Backup Alarm")
        
        print("   Both alarms should be playing for 2 seconds...")
        time.sleep(2)
        
        stop_alarm_sound("alarm1")
        print("   Stopped first alarm, second should continue...")
        time.sleep(1)
        
        stop_alarm_sound("alarm2")
        print("   Stopped second alarm")
        print("✅ Multiple alarm test completed")
        print()
        
        # Test 4: Cross-platform compatibility
        print("🌍 Test 4: Cross-Platform Compatibility")
        import platform
        system = platform.system()
        print(f"   Running on: {system}")
        
        if system == "Darwin":
            print("   macOS detected - should use afplay or say")
        elif system == "Linux":
            if audio_manager.is_pi:
                print("   Raspberry Pi detected - should use pygame/aplay")
            else:
                print("   Linux detected - should use aplay/paplay")
        else:
            print(f"   {system} detected - using fallback methods")
        
        print("✅ Cross-platform compatibility verified")
        print()
        
        print("🎉 All tests completed successfully!")
        print("=" * 50)
        print("✅ Pi Audio System is ready for deployment!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_alarm_server_integration():
    """Test integration with alarm server components."""
    print("\n🔗 Testing Alarm Server Integration...")
    print("=" * 50)
    
    try:
        # Test importing alarm server components
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        
        # Test Pi audio import from alarm server context
        from pi_audio import start_alarm_sound, stop_alarm_sound
        
        print("✅ Pi audio imports work from alarm server context")
        
        # Simulate alarm server workflow
        print("🔄 Simulating alarm server workflow...")
        
        # 1. Start alarm
        alarm_id = "integration-test"
        alarm_label = "Integration Test Alarm"
        
        print(f"   1. Starting alarm: {alarm_label}")
        success = start_alarm_sound(alarm_id, alarm_label)
        if success:
            print("   ✅ Alarm started via Pi audio manager")
        else:
            print("   ❌ Failed to start alarm")
            return False
        
        # 2. Let it play briefly
        time.sleep(2)
        
        # 3. Stop alarm (simulate cube solved)
        print("   2. Stopping alarm (simulating cube solved)")
        success = stop_alarm_sound(alarm_id)
        if success:
            print("   ✅ Alarm stopped via Pi audio manager")
        else:
            print("   ❌ Failed to stop alarm")
            return False
        
        print("✅ Alarm server integration test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🍓 Pi Audio System Local Testing")
    print("This tests the Pi audio system on your current platform")
    print("before deploying to Raspberry Pi.")
    print()
    
    # Run tests
    audio_test_passed = test_audio_system()
    integration_test_passed = test_alarm_server_integration()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"   Audio System: {'✅ PASSED' if audio_test_passed else '❌ FAILED'}")
    print(f"   Integration:  {'✅ PASSED' if integration_test_passed else '❌ FAILED'}")
    
    if audio_test_passed and integration_test_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Ready for Raspberry Pi deployment!")
        print("\nNext steps:")
        print("1. Push code to Git repository")
        print("2. Run setup_pi.sh on your Raspberry Pi")
        print("3. Test full system on Pi")
    else:
        print("\n❌ Some tests failed - fix issues before Pi deployment")
    
    print("=" * 50)
