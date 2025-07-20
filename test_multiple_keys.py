#!/usr/bin/env python3
"""
Test multiple encryption keys to find the correct one for your cube.
Based on JavaScript GAN_ENCRYPTION_KEYS array.
"""

import sys
import os
import asyncio
import time
from bleak import BleakScanner, BleakClient

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# GAN Gen3 Service and Characteristic UUIDs
SERVICE_UUID = "8653000a-43e6-47b7-9cb0-5fc21d4ae340"
STATE_CHAR_UUID = "8653000b-43e6-47b7-9cb0-5fc21d4ae340"

# Multiple encryption keys from JavaScript implementation
ENCRYPTION_KEYS = [
    {   # Key used by GAN Gen2, Gen3 and Gen4 cubes
        'name': 'GAN Standard',
        'key': [0x01, 0x02, 0x42, 0x28, 0x31, 0x91, 0x16, 0x07, 0x20, 0x05, 0x18, 0x54, 0x42, 0x11, 0x12, 0x53],
        'iv': [0x11, 0x03, 0x32, 0x28, 0x21, 0x01, 0x76, 0x27, 0x20, 0x95, 0x78, 0x14, 0x32, 0x12, 0x02, 0x43]
    },
    {   # Key used by MoYu AI 2023
        'name': 'MoYu AI 2023',
        'key': [0x05, 0x12, 0x02, 0x45, 0x02, 0x01, 0x29, 0x56, 0x12, 0x78, 0x12, 0x76, 0x81, 0x01, 0x08, 0x03],
        'iv': [0x01, 0x44, 0x28, 0x06, 0x86, 0x21, 0x22, 0x28, 0x51, 0x05, 0x08, 0x31, 0x82, 0x02, 0x21, 0x06]
    }
]

# Global state
_current_keys = []
_cube_address = None

def _log(msg: str):
    """Enhanced logging with timestamps."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def derive_key_iv_with_salt(base_key: list, base_iv: list, mac_address: str) -> tuple:
    """Derive key/IV with salt from MAC address."""
    # Extract MAC bytes as salt (handle both MAC and UUID formats)
    mac_clean = mac_address.replace(':', '').replace('-', '').upper()
    
    if len(mac_clean) == 12:
        # Traditional MAC address format
        salt = bytes.fromhex(mac_clean)
    elif len(mac_clean) == 32:
        # UUID format from macOS BLE - use last 12 hex chars (6 bytes)
        salt = bytes.fromhex(mac_clean[-12:])
    else:
        raise ValueError(f"Invalid MAC/UUID format: {mac_address}")
    
    # Apply salt to first 6 bytes of key and IV
    key = bytearray(base_key)
    iv = bytearray(base_iv)
    
    for i in range(6):
        key[i] = (base_key[i] + salt[i]) % 0xFF
        iv[i] = (base_iv[i] + salt[i]) % 0xFF
    
    return bytes(key), bytes(iv)

def decrypt_with_key(data: bytes, key: bytes, iv: bytes) -> bytes:
    """Decrypt using dual-chunk approach."""
    from Crypto.Cipher import AES
    
    if len(data) < 16:
        return data
    
    # Create a copy to decrypt in-place
    result = bytearray(data)
    
    # Decrypt 16-byte chunk at start (offset 0)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    chunk = cipher.decrypt(result[0:16])
    result[0:16] = chunk
    
    # Decrypt 16-byte chunk at end (offset length-16) if length > 16
    if len(result) > 16:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        end_offset = len(result) - 16
        chunk = cipher.decrypt(result[end_offset:end_offset + 16])
        result[end_offset:end_offset + 16] = chunk
    
    return bytes(result)

def analyze_decrypted_packet(data: bytes, key_name: str) -> bool:
    """Analyze decrypted packet and return True if it looks like valid Gen3."""
    if len(data) < 10:
        return False
    
    magic = data[0]
    event_type = data[1]
    data_length = data[2]
    
    _log(f"   [{key_name}] Magic: 0x{magic:02x}, EventType: 0x{event_type:02x}, DataLen: {data_length}")
    
    # Check for Gen3 protocol signature
    if magic == 0x55:
        _log(f"   ✅ [{key_name}] VALID Gen3 packet detected!")
        if event_type == 0x01:
            _log(f"   🔄 [{key_name}] MOVE packet detected!")
        return True
    
    return False

async def notification_handler(_, data: bytes) -> None:
    """Test multiple keys on each notification."""
    global _current_keys, _cube_address
    
    _log(f"📡 Testing {len(data)}-byte packet with {len(_current_keys)} keys...")
    
    found_valid = False
    for key_info in _current_keys:
        try:
            key, iv = derive_key_iv_with_salt(key_info['key'], key_info['iv'], _cube_address)
            decrypted = decrypt_with_key(data, key, iv)
            
            if analyze_decrypted_packet(decrypted, key_info['name']):
                found_valid = True
                _log(f"🎉 FOUND WORKING KEY: {key_info['name']}")
                _log(f"   Decrypted: {decrypted.hex()}")
                
        except Exception as e:
            _log(f"   ❌ [{key_info['name']}] Error: {e}")
    
    if not found_valid:
        _log(f"   ❌ No valid keys found for this packet")

async def find_and_connect_cube():
    """Find and connect to GAN cube."""
    global _current_keys, _cube_address
    
    _log("🔍 Scanning for GAN cubes...")
    devices = await BleakScanner.discover(timeout=10)
    
    # Find GAN cube
    gan_device = None
    for device in devices:
        if device.name and "GAN" in device.name.upper():
            gan_device = device
            break
    
    if not gan_device:
        _log("❌ No GAN cube found")
        return None
    
    _log(f"✅ Found cube: {gan_device.name} [{gan_device.address}]")
    _cube_address = gan_device.address
    
    # Prepare all encryption keys
    _current_keys = ENCRYPTION_KEYS
    _log(f"🔑 Testing {len(_current_keys)} encryption keys:")
    for key_info in _current_keys:
        _log(f"   - {key_info['name']}")
    
    # Connect and start notifications
    try:
        client = BleakClient(gan_device)
        await client.connect()
        _log("🔗 Connected successfully!")
        
        await client.start_notify(STATE_CHAR_UUID, notification_handler)
        _log("📡 Notifications started - move your cube!")
        
        # Keep connection alive
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            _log("🛑 Stopping...")
        finally:
            await client.disconnect()
            
    except Exception as e:
        _log(f"❌ Connection failed: {e}")

def main():
    """Main function."""
    print("🔍 Multi-Key GAN Cube Diagnostic Tool")
    print("=" * 50)
    print("This tool tests multiple encryption keys to find the correct one for your cube.")
    print("Move your cube to see which key produces valid Gen3 packets!")
    print("Press Ctrl+C to stop.")
    print()
    
    try:
        asyncio.run(find_and_connect_cube())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
