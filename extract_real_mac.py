#!/usr/bin/env python3
"""
Extract real MAC address from BLE advertisement data, matching JavaScript implementation.
This is the missing piece - we need the real MAC from manufacturer data, not the UUID!
"""

import sys
import os
import asyncio
import time
from bleak import BleakScanner

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def _log(msg: str):
    """Enhanced logging with timestamps."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def extract_mac_from_manufacturer_data(manufacturer_data: dict) -> str:
    """Extract MAC address from manufacturer data, matching JavaScript implementation."""
    
    # GAN Company Identifier Codes (from JavaScript GAN_CIC_LIST)
    # Array(256).fill(undefined).map((_v, i) => (i << 8) | 0x01)
    gan_cic_list = [(i << 8) | 0x01 for i in range(256)]
    
    _log(f"📊 Manufacturer data keys: {list(manufacturer_data.keys())}")
    
    # Look for GAN company identifier in manufacturer data
    for cic in gan_cic_list:
        if cic in manufacturer_data:
            data = manufacturer_data[cic]
            _log(f"✅ Found GAN CIC {cic:04x} with {len(data)} bytes: {data.hex()}")
            
            # Extract MAC from last 6 bytes (matching JavaScript)
            if len(data) >= 6:
                # JavaScript: getUint8(dataView.byteLength - i) for i in 1..6
                mac_bytes = []
                for i in range(1, 7):  # 1 to 6
                    mac_bytes.append(data[len(data) - i])
                
                mac_address = ":".join(f"{b:02X}" for b in mac_bytes)
                _log(f"🔑 Extracted MAC: {mac_address}")
                return mac_address
            else:
                _log(f"❌ Data too short for MAC extraction: {len(data)} bytes")
    
    _log(f"❌ No GAN company identifier found in manufacturer data")
    return None

async def scan_and_extract_mac():
    """Scan for GAN cubes and extract real MAC addresses."""
    _log("🔍 Scanning for GAN cubes to extract real MAC addresses...")
    
    def detection_callback(device, advertisement_data):
        if device.name and "GAN" in device.name.upper():
            _log(f"\n📡 Found GAN device: {device.name} [{device.address}]")
            _log(f"   Advertisement data: {advertisement_data}")
            
            if advertisement_data.manufacturer_data:
                _log(f"   Manufacturer data available!")
                real_mac = extract_mac_from_manufacturer_data(advertisement_data.manufacturer_data)
                
                if real_mac:
                    _log(f"🎉 SUCCESS! Real MAC extracted: {real_mac}")
                    _log(f"   Device UUID: {device.address}")
                    _log(f"   Real MAC:    {real_mac}")
                    
                    # Test key derivation with real MAC
                    try:
                        from gan_decrypt import derive_key_iv
                        key, iv = derive_key_iv(real_mac)  # Use real MAC instead of UUID
                        _log(f"🔑 Key derived with real MAC: {key.hex()[:16]}...")
                        return real_mac
                    except Exception as e:
                        _log(f"❌ Key derivation test failed: {e}")
                else:
                    _log(f"❌ Could not extract MAC from manufacturer data")
            else:
                _log(f"❌ No manufacturer data in advertisement")
    
    # Scan for devices
    scanner = BleakScanner(detection_callback=detection_callback)
    await scanner.start()
    
    _log("📡 Scanning... move your cube or turn it on/off to trigger advertisements")
    _log("Press Ctrl+C to stop")
    
    try:
        await asyncio.Event().wait()  # Wait indefinitely
    except KeyboardInterrupt:
        _log("🛑 Stopping scan...")
    finally:
        await scanner.stop()

def main():
    """Main function."""
    print("🔍 Real MAC Address Extractor")
    print("=" * 50)
    print("This tool extracts the REAL MAC address from BLE advertisement data,")
    print("matching the JavaScript implementation exactly.")
    print("This is the missing piece for correct key derivation!")
    print()
    
    try:
        asyncio.run(scan_and_extract_mac())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
