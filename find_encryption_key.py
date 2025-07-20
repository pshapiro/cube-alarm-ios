#!/usr/bin/env python3
"""
Alternative encryption key finder for GAN356 i Carry 2.
Since we confirmed the cube is Gen3 but uses non-standard encryption,
this tool tries various alternative approaches to find the correct key.
"""

import sys
import os
import asyncio
import time
from bleak import BleakScanner, BleakClient
from Crypto.Cipher import AES

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# GAN Gen3 Service and Characteristic UUIDs
SERVICE_UUID = "8653000a-43e6-47b7-9cb0-5fc21d4ae340"
STATE_CHAR_UUID = "8653000b-43e6-47b7-9cb0-5fc21d4ae340"

# Alternative encryption approaches to try
ALTERNATIVE_APPROACHES = [
    {
        'name': 'No Salt (Base Key Only)',
        'description': 'Use base key without MAC salt modification',
        'apply_salt': False
    },
    {
        'name': 'Reversed Salt Order',
        'description': 'Apply salt in reverse byte order',
        'apply_salt': True,
        'reverse_salt': True
    },
    {
        'name': 'Full Key Salt (16 bytes)',
        'description': 'Apply salt to all 16 bytes instead of just first 6',
        'apply_salt': True,
        'full_key_salt': True
    },
    {
        'name': 'XOR Salt Instead of Add',
        'description': 'XOR salt with key instead of adding',
        'apply_salt': True,
        'use_xor': True
    },
    {
        'name': 'Different Salt Source',
        'description': 'Use first 12 chars of UUID instead of last 12',
        'apply_salt': True,
        'use_first_uuid_chars': True
    },
    {
        'name': 'ECB Mode Instead of CBC',
        'description': 'Try AES-ECB instead of AES-CBC',
        'apply_salt': True,
        'use_ecb': True
    }
]

# Base keys to try with each approach
BASE_KEYS = [
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

def _log(msg: str):
    """Enhanced logging with timestamps."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def derive_key_iv_alternative(base_key: bytes, base_iv: bytes, mac_address: str, approach: dict) -> tuple:
    """Derive key/IV using alternative approach."""
    
    # Extract salt from MAC/UUID
    mac_clean = mac_address.replace(':', '').replace('-', '').upper()
    
    if len(mac_clean) == 32:  # UUID format
        if approach.get('use_first_uuid_chars', False):
            salt = bytes.fromhex(mac_clean[:12])  # First 12 chars instead of last 12
        else:
            salt = bytes.fromhex(mac_clean[-12:])  # Last 12 chars (standard)
    elif len(mac_clean) == 12:  # MAC format
        salt = bytes.fromhex(mac_clean)
    else:
        raise ValueError(f"Invalid MAC/UUID format: {mac_address}")
    
    # Apply salt reversal if requested
    if approach.get('reverse_salt', False):
        salt = salt[::-1]  # Reverse byte order
    
    # Start with base key and IV
    key = bytearray(base_key)
    iv = bytearray(base_iv)
    
    if approach.get('apply_salt', True):
        # Determine how many bytes to modify
        bytes_to_modify = 16 if approach.get('full_key_salt', False) else 6
        
        for i in range(min(bytes_to_modify, len(salt))):
            if approach.get('use_xor', False):
                # XOR instead of add
                key[i] = base_key[i] ^ salt[i % len(salt)]
                iv[i] = base_iv[i] ^ salt[i % len(salt)]
            else:
                # Standard add with modulo
                key[i] = (base_key[i] + salt[i % len(salt)]) % 0xFF
                iv[i] = (base_iv[i] + salt[i % len(salt)]) % 0xFF
    
    return bytes(key), bytes(iv)

def decrypt_with_approach(data: bytes, key: bytes, iv: bytes, approach: dict) -> bytes:
    """Decrypt using specified approach."""
    if len(data) < 16:
        return data
    
    result = bytearray(data)
    
    if approach.get('use_ecb', False):
        # Try AES-ECB mode
        cipher = AES.new(key, AES.MODE_ECB)
        # Decrypt in 16-byte blocks
        for i in range(0, len(result), 16):
            block_end = min(i + 16, len(result))
            if block_end - i == 16:  # Only decrypt full blocks
                block = cipher.decrypt(result[i:block_end])
                result[i:block_end] = block
    else:
        # Standard dual-chunk CBC approach
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

def analyze_decrypted_result(data: bytes, base_key_name: str, approach_name: str) -> bool:
    """Analyze decrypted result for Gen3 protocol signatures."""
    if len(data) < 3:
        return False
    
    magic = data[0]
    event_type = data[1]
    data_length = data[2]
    
    # Check for Gen3 protocol signature
    if magic == 0x55:
        _log(f"    🎉 [{base_key_name} + {approach_name}] FOUND VALID Gen3 MAGIC BYTE!")
        if event_type == 0x01:
            _log(f"    🔄 [{base_key_name} + {approach_name}] MOVE packet detected!")
        elif event_type == 0x02:
            _log(f"    📊 [{base_key_name} + {approach_name}] State packet detected!")
        _log(f"    📦 [{base_key_name} + {approach_name}] Full decrypted: {data.hex()}")
        return True
    
    # Also check for other potentially valid patterns
    if magic in [0x00, 0x01, 0x02] and event_type in [0x00, 0x01, 0x02] and data_length < 50:
        _log(f"    🤔 [{base_key_name} + {approach_name}] Possible valid pattern: magic=0x{magic:02x}, type=0x{event_type:02x}, len={data_length}")
        return False
    
    return False

async def test_all_approaches():
    """Test all alternative encryption approaches."""
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
    
    # Collect some sample packets first
    sample_packets = []
    
    async def packet_collector(_, data: bytes):
        if len(sample_packets) < 5:  # Collect 5 sample packets
            sample_packets.append(data)
            _log(f"📦 Collected sample packet {len(sample_packets)}: {len(data)} bytes")
    
    # Connect and collect packets
    try:
        client = BleakClient(gan_device)
        await client.connect()
        _log("🔗 Connected - collecting sample packets...")
        
        await client.start_notify(STATE_CHAR_UUID, packet_collector)
        
        # Wait for packets
        while len(sample_packets) < 5:
            await asyncio.sleep(0.5)
        
        await client.stop_notify(STATE_CHAR_UUID)
        await client.disconnect()
        
    except Exception as e:
        _log(f"❌ Packet collection failed: {e}")
        return
    
    _log(f"✅ Collected {len(sample_packets)} sample packets")
    
    # Now test all combinations
    _log("\n🧪 Testing all encryption approaches...")
    
    found_working_approach = False
    
    for base_key_info in BASE_KEYS:
        for approach in ALTERNATIVE_APPROACHES:
            approach_name = f"{base_key_info['name']} + {approach['name']}"
            _log(f"\n🔬 Testing: {approach_name}")
            _log(f"    Description: {approach['description']}")
            
            try:
                # Derive key/IV using this approach
                key, iv = derive_key_iv_alternative(
                    base_key_info['key'], 
                    base_key_info['iv'], 
                    gan_device.address, 
                    approach
                )
                
                _log(f"    🔑 Key: {key.hex()[:16]}...")
                _log(f"    🔑 IV:  {iv.hex()[:16]}...")
                
                # Test on all sample packets
                valid_packets = 0
                for i, packet in enumerate(sample_packets):
                    try:
                        decrypted = decrypt_with_approach(packet, key, iv, approach)
                        if analyze_decrypted_result(decrypted, base_key_info['name'], approach['name']):
                            valid_packets += 1
                    except Exception as e:
                        _log(f"    ❌ Packet {i+1} decryption error: {e}")
                
                if valid_packets > 0:
                    _log(f"    ✅ SUCCESS! {valid_packets}/{len(sample_packets)} packets decrypted successfully!")
                    found_working_approach = True
                    
                    # Save the working approach
                    _log(f"\n🎉 WORKING ENCRYPTION FOUND!")
                    _log(f"Base Key: {base_key_info['name']}")
                    _log(f"Approach: {approach['name']}")
                    _log(f"Description: {approach['description']}")
                    break
                else:
                    _log(f"    ❌ No valid packets found with this approach")
                    
            except Exception as e:
                _log(f"    ❌ Approach failed: {e}")
        
        if found_working_approach:
            break
    
    if not found_working_approach:
        _log("\n❌ No working encryption approach found with current methods")
        _log("Your cube may use a completely custom encryption scheme")

def main():
    """Main function."""
    print("🔍 Alternative Encryption Key Finder")
    print("=" * 50)
    print("Testing various alternative encryption approaches for your Gen3 cube...")
    print("This will try different key derivation methods, salt applications, and cipher modes.")
    print()
    
    try:
        asyncio.run(test_all_approaches())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
