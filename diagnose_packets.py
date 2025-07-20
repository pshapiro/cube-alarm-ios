#!/usr/bin/env python3
"""
Diagnostic script to analyze your GAN cube's packet structure.
This will help us understand the encryption and packet format.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def analyze_packet(raw_data: bytes, key: bytes, iv: bytes):
    """Analyze a raw packet with different decryption approaches."""
    print(f"\n🔍 Analyzing packet: {len(raw_data)} bytes")
    print(f"   Raw: {raw_data.hex()}")
    
    # Try different decryption approaches
    from Crypto.Cipher import AES
    
    # Approach 1: Original method
    try:
        from gan_decrypt import decrypt_packet
        decrypted1 = decrypt_packet(raw_data, key, iv)
        print(f"   Method 1: {decrypted1.hex()}")
        print(f"   Type: 0x{decrypted1[0]:02x}, Byte3: 0x{decrypted1[3]:02x if len(decrypted1) > 3 else 0:02x}")
    except Exception as e:
        print(f"   Method 1 failed: {e}")
    
    # Approach 2: Try different key/IV combinations
    try:
        # Test with different template indices
        from gan_decrypt import _get_key_templates
        templates = _get_key_templates()
        
        for i, (key_tpl, iv_tpl) in enumerate([(templates[0], templates[1]), (templates[2], templates[3])]):
            # Recreate key/IV with different template
            mac_bytes = key[:6]  # Use first 6 bytes as mock MAC
            test_key = bytes((key_tpl[j] + mac_bytes[5-j]) % 255 for j in range(16))
            test_iv = bytes((iv_tpl[j] + mac_bytes[5-j]) % 255 for j in range(16))
            
            decrypted = decrypt_packet(raw_data, test_key, test_iv)
            print(f"   Template {i}: {decrypted.hex()[:32]}")
            print(f"   Type: 0x{decrypted[0]:02x}, Byte3: 0x{decrypted[3]:02x if len(decrypted) > 3 else 0:02x}")
    except Exception as e:
        print(f"   Template test failed: {e}")

def main():
    """Main diagnostic function."""
    print("🔬 GAN Cube Packet Diagnostic Tool")
    print("=" * 50)
    
    # Sample packets from your cube (from the test output)
    sample_packets = [
        "e6196cc8084af93f586ba0305515b4ee7f5"[:38],  # 19-byte packet (truncate to valid hex)
        "9b6ccb0a151023af7f69b82f7a0c2e407f5"[:38],  # 19-byte packet  
        "7fa340a2c5849963de11bef48231dfa67f5"[:38],  # 19-byte packet
        "47b3a3e59e26f8a48eba8945dc43cfc8",         # 16-byte packet
    ]
    
    # Your cube's MAC for key derivation (from the UUID we saw in the logs)
    cube_mac = "8F0ADD69-3FC4-BCC5-9CA7-97FB2869B0B3"
    
    try:
        from gan_decrypt import derive_key_iv
        key, iv = derive_key_iv(cube_mac)
        print(f"🔑 Derived key: {key.hex()}")
        print(f"🔑 Derived IV:  {iv.hex()}")
        
        for i, packet_hex in enumerate(sample_packets):
            packet_bytes = bytes.fromhex(packet_hex)
            print(f"\n📦 Packet {i+1}:")
            analyze_packet(packet_bytes, key, iv)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
