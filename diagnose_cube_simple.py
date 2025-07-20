#!/usr/bin/env python3
"""
Simple GAN cube diagnostic - focuses on identifying the actual protocol your cube uses.
"""

import sys
import os
import asyncio
import time
from bleak import BleakScanner, BleakClient

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Known GAN characteristics to try
CHARS_TO_TEST = [
    ("Gen2_State", "28be4cb6-cd67-11e9-a32f-2a2ae2dbcce4"),
    ("Gen3_State", "8653000b-43e6-47b7-9cb0-5fc21d4ae340"),
    ("Gen4_State", "0000fff6-0000-1000-8000-00805f9b34fb")
]

def _log(msg: str):
    """Enhanced logging with timestamps."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def analyze_packet_patterns(data: bytes):
    """Analyze packet for common patterns."""
    _log(f"📦 Packet: {len(data)} bytes - {data.hex()}")
    
    # Check if this might be plaintext (low entropy, readable patterns)
    if len(data) >= 3:
        # Look for common move patterns if this were plaintext
        if data[0] in [0x00, 0x01, 0x02, 0x03, 0x04, 0x05]:  # Low values might be move indices
            _log(f"    🤔 Low first byte (0x{data[0]:02x}) - might be plaintext move")
        
        # Check for Gen3 magic byte
        if data[0] == 0x55:
            _log(f"    ✅ Gen3 magic byte detected!")
            if data[1] == 0x01:
                _log(f"    🔄 Move packet signature!")
        
        # Check entropy
        unique_bytes = len(set(data))
        entropy = unique_bytes / len(data) if len(data) > 0 else 0
        _log(f"    📊 Entropy: {entropy:.2f} ({unique_bytes}/{len(data)} unique)")
        
        if entropy > 0.8:
            _log(f"    🔐 High entropy - likely encrypted")
        elif entropy < 0.4:
            _log(f"    📝 Low entropy - might be plaintext or simple pattern")

async def test_characteristic(device, char_name, char_uuid):
    """Test a specific characteristic."""
    _log(f"🧪 Testing {char_name} ({char_uuid})...")
    
    packet_count = 0
    
    async def notification_handler(_, data: bytes):
        nonlocal packet_count
        packet_count += 1
        _log(f"\n📡 [{char_name}] Packet #{packet_count}")
        analyze_packet_patterns(data)
    
    try:
        client = BleakClient(device)
        await client.connect()
        _log(f"🔗 Connected to test {char_name}")
        
        # Try to start notifications
        await client.start_notify(char_uuid, notification_handler)
        _log(f"✅ {char_name} notifications started!")
        
        # Wait for some packets
        _log("📡 Waiting for packets... move your cube!")
        await asyncio.sleep(10)  # Wait 10 seconds for packets
        
        await client.stop_notify(char_uuid)
        await client.disconnect()
        
        if packet_count > 0:
            _log(f"✅ {char_name} received {packet_count} packets - THIS IS THE ACTIVE CHARACTERISTIC!")
            return True
        else:
            _log(f"❌ {char_name} received no packets")
            return False
            
    except Exception as e:
        _log(f"❌ {char_name} failed: {e}")
        return False

async def main():
    """Main diagnostic function."""
    print("🔬 Simple GAN Cube Protocol Diagnostic")
    print("=" * 50)
    print("This tool will test each known characteristic to find which one your cube uses.")
    print("Move your cube when prompted to generate packets!")
    print()
    
    # Find cube
    _log("🔍 Scanning for GAN cubes...")
    devices = await BleakScanner.discover(timeout=10)
    
    gan_device = None
    for device in devices:
        if device.name and "GAN" in device.name.upper():
            gan_device = device
            break
    
    if not gan_device:
        _log("❌ No GAN cube found")
        return
    
    _log(f"✅ Found cube: {gan_device.name} [{gan_device.address}]")
    
    # Test each characteristic
    working_chars = []
    
    for char_name, char_uuid in CHARS_TO_TEST:
        _log(f"\n{'='*30}")
        if await test_characteristic(gan_device, char_name, char_uuid):
            working_chars.append((char_name, char_uuid))
    
    # Summary
    _log(f"\n{'='*50}")
    _log("🎯 DIAGNOSTIC RESULTS:")
    
    if working_chars:
        for char_name, char_uuid in working_chars:
            _log(f"✅ Working characteristic: {char_name} ({char_uuid})")
        
        # If we found the working characteristic, do extended monitoring
        if len(working_chars) == 1:
            char_name, char_uuid = working_chars[0]
            _log(f"\n🔍 Extended monitoring of {char_name}...")
            _log("Move your cube in different ways to see packet patterns!")
            
            packet_count = 0
            
            async def extended_handler(_, data: bytes):
                nonlocal packet_count
                packet_count += 1
                _log(f"\n📡 Extended Packet #{packet_count}")
                analyze_packet_patterns(data)
            
            try:
                client = BleakClient(gan_device)
                await client.connect()
                await client.start_notify(char_uuid, extended_handler)
                
                _log("📡 Extended monitoring active - press Ctrl+C to stop")
                await asyncio.Event().wait()  # Wait indefinitely
                
            except KeyboardInterrupt:
                _log("🛑 Stopping extended monitoring...")
            except Exception as e:
                _log(f"❌ Extended monitoring error: {e}")
            finally:
                try:
                    await client.disconnect()
                except:
                    pass
    else:
        _log("❌ No working characteristics found!")
        _log("Your cube might use a different protocol or have connection issues.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
