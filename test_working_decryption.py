#!/usr/bin/env python3
"""
Test the working decryption method we discovered for your GAN356 i Carry 2.
This should now properly decrypt packets and detect moves!
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

# Global state
_key_iv = None
_move_count = 0

def _log(msg: str):
    """Enhanced logging with timestamps."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def get_bit_word(data: bytes, bit_offset: int, bit_length: int, little_endian: bool = False) -> int:
    """Extract bit word from byte array, matching JavaScript implementation."""
    byte_offset = bit_offset // 8
    bit_shift = bit_offset % 8
    
    # Calculate how many bytes we need
    bytes_needed = ((bit_length + bit_shift + 7) // 8)
    
    if byte_offset + bytes_needed > len(data):
        return 0
    
    # Extract bytes and convert to integer
    value = 0
    for i in range(bytes_needed):
        if byte_offset + i < len(data):
            if little_endian:
                value |= data[byte_offset + i] << (i * 8)
            else:
                value = (value << 8) | data[byte_offset + i]
    
    # Apply bit shift and mask
    if not little_endian:
        value >>= (bytes_needed * 8 - bit_shift - bit_length)
    else:
        value >>= bit_shift
    
    # Apply bit mask
    mask = (1 << bit_length) - 1
    return value & mask

def analyze_decrypted_packet(data: bytes) -> None:
    """Analyze decrypted packet using Gen3 protocol from JavaScript implementation."""
    global _move_count
    
    _log(f"🔓 Decrypted packet: {len(data)} bytes - {data.hex()}")
    
    if len(data) < 10:  # Need at least 10 bytes for Gen3 protocol
        _log(f"   ⚠️  Packet too short for Gen3 protocol")
        return
    
    # Parse using Gen3 protocol (matching JavaScript)
    magic = get_bit_word(data, 0, 8)  # Byte 0
    event_type = get_bit_word(data, 8, 8)  # Byte 1
    data_length = get_bit_word(data, 16, 8)  # Byte 2
    
    _log(f"   Magic: 0x{magic:02x}, EventType: 0x{event_type:02x}, DataLen: {data_length}")
    
    # Check for Gen3 move packet (magic=0x55, eventType=0x01)
    if magic == 0x55 and event_type == 0x01 and data_length > 0:
        _log(f"   ✅ Valid Gen3 move packet detected!")
        
        # Parse move data (matching JavaScript bit positions)
        cube_timestamp = get_bit_word(data, 24, 32, True)  # Little endian timestamp
        serial = get_bit_word(data, 56, 16, True)  # Little endian serial
        
        direction = get_bit_word(data, 72, 2)  # 2 bits for direction
        face_bits = get_bit_word(data, 74, 6)  # 6 bits for face
        
        # Map face bits to face index (from JavaScript)
        face_map = [2, 32, 8, 1, 16, 4]  # Maps to URFDLB
        try:
            face_index = face_map.index(face_bits)
            face_char = "URFDLB"[face_index]
            direction_char = " '"[direction] if direction < 2 else "?"
            move_name = face_char + direction_char
            
            _move_count += 1
            _log(f"🔄 MOVE DETECTED: {move_name} (serial: {serial}, timestamp: {cube_timestamp}, count: {_move_count})")
            
        except ValueError:
            _log(f"   ❌ Unknown face bits: 0x{face_bits:02x}")
    
    elif magic == 0x55 and event_type == 0x02:
        _log(f"   📊 Gen3 state/facelets packet detected!")
        # Could parse cube state here if needed
        
    elif magic == 0x55:
        _log(f"   ℹ️  Gen3 packet (other type): type=0x{event_type:02x}")
    else:
        _log(f"   ❓ Non-Gen3 packet (magic: 0x{magic:02x})")

async def notification_handler(_, data: bytes) -> None:
    """Notification handler with working decryption."""
    global _key_iv
    
    _log(f"📡 Notification received: {len(data)} bytes")
    
    if not _key_iv:
        _log("❌ No encryption key available")
        return
    
    try:
        from gan_decrypt import decrypt_packet
        decrypted = decrypt_packet(data, _key_iv[0], _key_iv[1])
        analyze_decrypted_packet(decrypted)
    except Exception as e:
        _log(f"❌ Decryption failed: {e}")

async def find_and_connect_cube():
    """Find and connect to GAN cube with working decryption."""
    global _key_iv
    
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
    
    # Derive encryption key using the WORKING method we discovered
    try:
        from gan_decrypt import derive_key_iv
        _key_iv = derive_key_iv(gan_device.address)
        _log(f"🔑 Key derived using corrected method: {_key_iv[0].hex()[:16]}...")
    except Exception as e:
        _log(f"❌ Key derivation failed: {e}")
        return
    
    # Connect and start notifications
    try:
        client = BleakClient(gan_device)
        await client.connect()
        _log("🔗 Connected successfully!")
        
        await client.start_notify(STATE_CHAR_UUID, notification_handler)
        _log("📡 Notifications started with WORKING decryption - move your cube!")
        
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
    print("🎉 Working GAN Cube Move Detector")
    print("=" * 50)
    print("Using the CORRECT decryption method we discovered:")
    print("- GAN Standard base key")
    print("- Salt from FIRST 12 characters of UUID")
    print("- Gen3 protocol parsing")
    print()
    print("Move your cube to see REAL move detection!")
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
