#!/usr/bin/env python3
"""
Comprehensive GAN cube diagnostic tool to identify cube type and protocol.
Tests multiple approaches: Gen2, Gen3, Gen4, and raw packet analysis.
"""

import sys
import os
import asyncio
import time
from bleak import BleakScanner, BleakClient

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# All known GAN service UUIDs
SERVICES = {
    'Gen2': "6e400001-b5a3-f393-e0a9-e50e24dc4179",
    'Gen3': "8653000a-43e6-47b7-9cb0-5fc21d4ae340", 
    'Gen4': "00000010-0000-fff7-fff6-fff5fff4fff0"
}

CHARACTERISTICS = {
    'Gen2_State': "28be4cb6-cd67-11e9-a32f-2a2ae2dbcce4",
    'Gen3_State': "8653000b-43e6-47b7-9cb0-5fc21d4ae340",
    'Gen4_State': "0000fff6-0000-1000-8000-00805f9b34fb"
}

def _log(msg: str):
    """Enhanced logging with timestamps."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def analyze_raw_packet(data: bytes, source: str = ""):
    """Analyze raw packet for patterns."""
    _log(f"📦 [{source}] Raw packet: {len(data)} bytes")
    _log(f"    Hex: {data.hex()}")
    
    if len(data) >= 3:
        _log(f"    First 3 bytes: 0x{data[0]:02x} 0x{data[1]:02x} 0x{data[2]:02x}")
        
        # Check for known protocol signatures
        if data[0] == 0x55:
            _log(f"    ✅ Gen3 magic byte detected!")
            if data[1] == 0x01:
                _log(f"    🔄 Move packet signature!")
        elif data[0] in [0x00, 0x01, 0x02]:  # Common Gen2 patterns
            _log(f"    🤔 Possible Gen2 pattern")
        
        # Look for repeated patterns (might indicate encryption)
        if len(set(data)) < len(data) * 0.3:  # Low entropy might mean repeating patterns
            _log(f"    🔄 Low entropy - possible repeating pattern")
    
    # Check if data looks encrypted (high entropy)
    if len(data) > 8:
        unique_bytes = len(set(data))
        entropy_ratio = unique_bytes / len(data)
        _log(f"    📊 Entropy: {entropy_ratio:.2f} ({unique_bytes}/{len(data)} unique bytes)")
        
        if entropy_ratio > 0.8:
            _log(f"    🔐 High entropy - likely encrypted")
        elif entropy_ratio < 0.3:
            _log(f"    📝 Low entropy - might be plaintext or pattern")

def try_decrypt_approaches(data: bytes, mac_address: str):
    """Try different decryption approaches."""
    from Crypto.Cipher import AES
    
    # Standard keys from JavaScript
    keys_to_try = [
        {
            'name': 'GAN Standard',
            'key': bytes([0x01, 0x02, 0x42, 0x28, 0x31, 0x91, 0x16, 0x07, 0x20, 0x05, 0x18, 0x54, 0x42, 0x11, 0x12, 0x53]),
            'iv': bytes([0x11, 0x03, 0x32, 0x28, 0x21, 0x01, 0x76, 0x27, 0x20, 0x95, 0x78, 0x14, 0x32, 0x12, 0x02, 0x43])
        },
        {
            'name': 'MoYu AI 2023',
            'key': bytes([0x05, 0x12, 0x02, 0x45, 0x02, 0x01, 0x29, 0x56, 0x12, 0x78, 0x12, 0x76, 0x81, 0x01, 0x08, 0x03]),
            'iv': bytes([0x01, 0x44, 0x28, 0x06, 0x86, 0x21, 0x22, 0x28, 0x51, 0x05, 0x08, 0x31, 0x82, 0x02, 0x21, 0x06])
        }
    ]
    
    # Extract salt from MAC/UUID
    mac_clean = mac_address.replace(':', '').replace('-', '').upper()
    if len(mac_clean) == 32:  # UUID format
        salt = bytes.fromhex(mac_clean[-12:])
    elif len(mac_clean) == 12:  # MAC format
        salt = bytes.fromhex(mac_clean)
    else:
        _log(f"    ❌ Cannot extract salt from: {mac_address}")
        return
    
    _log(f"    🧂 Using salt: {salt.hex()}")
    
    for key_info in keys_to_try:
        try:
            # Apply salt to key and IV
            key = bytearray(key_info['key'])
            iv = bytearray(key_info['iv'])
            
            for i in range(6):
                key[i] = (key_info['key'][i] + salt[i]) % 0xFF
                iv[i] = (key_info['iv'][i] + salt[i]) % 0xFF
            
            # Try dual-chunk decryption (JavaScript approach)
            if len(data) >= 16:
                result = bytearray(data)
                
                # Decrypt first 16 bytes
                cipher = AES.new(bytes(key), AES.MODE_CBC, bytes(iv))
                chunk = cipher.decrypt(result[0:16])
                result[0:16] = chunk
                
                # Decrypt last 16 bytes if packet > 16 bytes
                if len(result) > 16:
                    cipher = AES.new(bytes(key), AES.MODE_CBC, bytes(iv))
                    end_offset = len(result) - 16
                    chunk = cipher.decrypt(result[end_offset:end_offset + 16])
                    result[end_offset:end_offset + 16] = chunk
                
                decrypted = bytes(result)
                _log(f"    🔓 [{key_info['name']}] Decrypted: {decrypted.hex()}")
                
                # Check for protocol signatures
                if len(decrypted) >= 3:
                    magic = decrypted[0]
                    event_type = decrypted[1]
                    data_len = decrypted[2]
                    
                    if magic == 0x55:
                        _log(f"    ✅ [{key_info['name']}] VALID Gen3 protocol!")
                        if event_type == 0x01:
                            _log(f"    🔄 [{key_info['name']}] MOVE packet detected!")
                        return True
                    else:
                        _log(f"    ❌ [{key_info['name']}] Magic: 0x{magic:02x} (expected 0x55)")
                        
        except Exception as e:
            _log(f"    ❌ [{key_info['name']}] Decryption error: {e}")
    
    return False

async def test_cube_services(device):
    """Test which services the cube supports."""
    _log(f"🔍 Testing services for {device.name}...")
    
    try:
        client = BleakClient(device)
        await client.connect()
        _log("🔗 Connected for service discovery")
        
        services = await client.get_services()
        _log(f"📋 Found {len(services.services)} services:")
        
        cube_generation = None
        state_char = None
        
        for service in services.services:
            service_uuid = str(service.uuid).lower()
            _log(f"    Service: {service_uuid}")
            
            # Check if this matches known GAN services
            for gen, uuid in SERVICES.items():
                if service_uuid == uuid.lower():
                    _log(f"    ✅ {gen} service detected!")
                    cube_generation = gen
                    
                    # Find the state characteristic
                    for char in service.characteristics:
                        char_uuid = str(char.uuid).lower()
                        expected_char = CHARACTERISTICS.get(f"{gen}_State", "").lower()
                        if char_uuid == expected_char:
                            _log(f"    ✅ {gen} state characteristic found!")
                            state_char = char.uuid
                            break
        
        await client.disconnect()
        return cube_generation, state_char
        
    except Exception as e:
        _log(f"❌ Service discovery failed: {e}")
        return None, None

async def monitor_notifications(device, char_uuid):
    """Monitor notifications and analyze packets."""
    packet_count = 0
    
    async def notification_handler(_, data: bytes):
        nonlocal packet_count
        packet_count += 1
        
        _log(f"\n📡 Packet #{packet_count}")
        analyze_raw_packet(data, "RAW")
        
        # Try decryption approaches
        success = try_decrypt_approaches(data, device.address)
        if success:
            _log(f"🎉 FOUND WORKING DECRYPTION!")
    
    try:
        client = BleakClient(device)
        await client.connect()
        _log("🔗 Connected for monitoring")
        
        await client.start_notify(char_uuid, notification_handler)
        _log("📡 Monitoring started - move your cube!")
        _log("Press Ctrl+C to stop...")
        
        # Monitor for a while
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            _log("🛑 Stopping...")
        finally:
            await client.disconnect()
            
    except Exception as e:
        _log(f"❌ Monitoring failed: {e}")

async def main():
    """Main diagnostic function."""
    print("🔬 Comprehensive GAN Cube Diagnostic Tool")
    print("=" * 60)
    print("This tool will:")
    print("1. Identify your cube's generation (Gen2/Gen3/Gen4)")
    print("2. Test all known encryption keys")
    print("3. Analyze raw packet patterns")
    print("4. Find the correct decryption approach")
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
    
    # Test services to identify generation
    cube_gen, state_char = await test_cube_services(gan_device)
    
    if cube_gen and state_char:
        _log(f"🎯 Identified as {cube_gen} cube")
        _log(f"📡 Using characteristic: {state_char}")
        
        # Monitor notifications
        await monitor_notifications(gan_device, state_char)
    else:
        _log("❌ Could not identify cube generation or find state characteristic")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
