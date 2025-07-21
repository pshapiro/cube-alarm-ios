#!/usr/bin/env python3
"""
Raspberry Pi Audio Handler for Alarm Clock
Handles local audio playback on Raspberry Pi with fallback options.
"""

import os
import subprocess
import threading
import time
import logging
from typing import Optional, Dict
import platform

logger = logging.getLogger(__name__)

class PiAudioManager:
    """Manages audio playback on Raspberry Pi with multiple fallback options."""
    
    def __init__(self):
        self.active_alarms: Dict[str, threading.Thread] = {}
        self.is_pi = self._detect_raspberry_pi()
        self.audio_method = self._detect_audio_method()
        
        logger.info(f"🔊 Audio Manager initialized - Platform: {'Pi' if self.is_pi else platform.system()}, Method: {self.audio_method}")
    
    def _detect_raspberry_pi(self) -> bool:
        """Detect if running on Raspberry Pi."""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                return 'Raspberry Pi' in f.read()
        except:
            return False
    
    def _detect_audio_method(self) -> str:
        """Detect best available audio method."""
        methods = []
        
        # Check for pygame (preferred for Pi)
        try:
            import pygame
            methods.append('pygame')
        except ImportError:
            pass
        
        # Check for system audio commands
        if self._command_exists('aplay'):
            methods.append('aplay')
        if self._command_exists('paplay'):
            methods.append('paplay')
        if self._command_exists('speaker-test'):
            methods.append('speaker-test')
        if self._command_exists('afplay'):  # macOS
            methods.append('afplay')
        
        # Return best method
        if 'pygame' in methods:
            return 'pygame'
        elif 'aplay' in methods:
            return 'aplay'
        elif 'paplay' in methods:
            return 'paplay'
        elif 'afplay' in methods:
            return 'afplay'
        elif 'speaker-test' in methods:
            return 'speaker-test'
        else:
            return 'none'
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        try:
            subprocess.run(['which', command], check=True, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def start_alarm_sound(self, alarm_id: str, alarm_label: str = "Alarm") -> bool:
        """Start playing alarm sound for given alarm ID."""
        if alarm_id in self.active_alarms:
            logger.warning(f"⚠️ Alarm sound already playing for {alarm_id}")
            return True
        
        logger.info(f"🔊 Starting alarm sound for: {alarm_label} (ID: {alarm_id})")
        
        # Create and start alarm thread
        alarm_thread = threading.Thread(
            target=self._alarm_sound_loop,
            args=(alarm_id, alarm_label),
            daemon=True
        )
        alarm_thread.start()
        
        self.active_alarms[alarm_id] = alarm_thread
        return True
    
    def stop_alarm_sound(self, alarm_id: str) -> bool:
        """Stop playing alarm sound for given alarm ID."""
        if alarm_id not in self.active_alarms:
            logger.warning(f"⚠️ No alarm sound playing for {alarm_id}")
            return True
        
        logger.info(f"🔇 Stopping alarm sound for ID: {alarm_id}")
        
        # Remove from active alarms (this will stop the loop)
        thread = self.active_alarms.pop(alarm_id, None)
        
        # Wait briefly for thread to finish
        if thread and thread.is_alive():
            thread.join(timeout=2)
        
        return True
    
    def stop_all_alarms(self):
        """Stop all active alarm sounds."""
        logger.info("🔇 Stopping all alarm sounds")
        alarm_ids = list(self.active_alarms.keys())
        for alarm_id in alarm_ids:
            self.stop_alarm_sound(alarm_id)
    
    def _alarm_sound_loop(self, alarm_id: str, alarm_label: str):
        """Main alarm sound loop - runs until alarm is stopped."""
        logger.info(f"🎵 Starting alarm sound loop for: {alarm_label}")
        
        try:
            while alarm_id in self.active_alarms:
                success = self._play_alarm_sound_once()
                if not success:
                    logger.error(f"❌ Failed to play alarm sound for {alarm_label}")
                    break
                
                # Wait between beeps (check for stop every 0.1s)
                for _ in range(10):  # 1 second total, checking every 0.1s
                    if alarm_id not in self.active_alarms:
                        break
                    time.sleep(0.1)
        
        except Exception as e:
            logger.error(f"❌ Error in alarm sound loop for {alarm_label}: {e}")
        
        finally:
            logger.info(f"🔇 Alarm sound loop ended for: {alarm_label}")
    
    def _play_alarm_sound_once(self) -> bool:
        """Play alarm sound once using the best available method."""
        try:
            if self.audio_method == 'pygame':
                return self._play_pygame()
            elif self.audio_method == 'aplay':
                return self._play_aplay()
            elif self.audio_method == 'paplay':
                return self._play_paplay()
            elif self.audio_method == 'afplay':
                return self._play_afplay()
            elif self.audio_method == 'speaker-test':
                return self._play_speaker_test()
            else:
                logger.error("❌ No audio method available")
                return False
        
        except Exception as e:
            logger.error(f"❌ Error playing alarm sound: {e}")
            return False
    
    def _play_pygame(self) -> bool:
        """Play alarm sound using pygame."""
        try:
            import pygame
            
            # Initialize pygame mixer if not already done
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            
            # Check for custom alarm sound file
            sound_file = os.environ.get('ALARM_SOUND_FILE', 'sounds/alarm.wav')
            if os.path.exists(sound_file):
                sound = pygame.mixer.Sound(sound_file)
                sound.play()
                # Wait for sound to finish
                while pygame.mixer.get_busy():
                    time.sleep(0.1)
            else:
                # Generate beep sound programmatically
                self._generate_beep_pygame()
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Pygame audio error: {e}")
            return False
    
    def _generate_beep_pygame(self):
        """Generate a beep sound using pygame."""
        try:
            import pygame
            import numpy as np
            
            # Generate a 800Hz sine wave for 1 second
            sample_rate = 22050
            duration = 1.0
            frequency = 800
            
            frames = int(duration * sample_rate)
            arr = np.zeros((frames, 2), dtype=np.int16)
            
            for i in range(frames):
                wave = int(16383 * np.sin(2 * np.pi * frequency * i / sample_rate))
                arr[i][0] = wave  # Left channel
                arr[i][1] = wave  # Right channel
            
            sound = pygame.sndarray.make_sound(arr)
            sound.play()
            
            # Wait for sound to finish
            while pygame.mixer.get_busy():
                time.sleep(0.1)
        
        except Exception as e:
            logger.error(f"❌ Error generating beep: {e}")
    
    def _play_aplay(self) -> bool:
        """Play alarm sound using aplay (ALSA)."""
        try:
            sound_file = os.environ.get('ALARM_SOUND_FILE', 'sounds/alarm.wav')
            if os.path.exists(sound_file):
                subprocess.run(['aplay', sound_file], check=True, 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Use speaker-test as fallback
                return self._play_speaker_test()
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _play_paplay(self) -> bool:
        """Play alarm sound using paplay (PulseAudio)."""
        try:
            sound_file = os.environ.get('ALARM_SOUND_FILE', 'sounds/alarm.wav')
            if os.path.exists(sound_file):
                subprocess.run(['paplay', sound_file], check=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Use speaker-test as fallback
                return self._play_speaker_test()
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _play_afplay(self) -> bool:
        """Play alarm sound using afplay (macOS)."""
        try:
            # Try multiple system sounds on macOS
            sound_paths = [
                '/System/Library/Sounds/Alarm.aiff',
                '/System/Library/Sounds/Glass.aiff', 
                '/System/Library/Sounds/Ping.aiff',
                '/System/Library/Sounds/Sosumi.aiff'
            ]
            
            for sound_path in sound_paths:
                if os.path.exists(sound_path):
                    subprocess.run(['afplay', sound_path], 
                                 check=True, timeout=5,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True
            
            # If no system sounds found, generate a beep
            subprocess.run(['say', 'alarm'], check=True, timeout=3,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
    
    def _play_speaker_test(self) -> bool:
        """Play alarm sound using speaker-test (fallback)."""
        try:
            subprocess.run(['speaker-test', '-t', 'sine', '-f', '800', '-l', '1'], 
                         check=True, timeout=3,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
    
    def test_audio(self) -> bool:
        """Test audio output."""
        logger.info(f"🔊 Testing audio output using method: {self.audio_method}")
        return self._play_alarm_sound_once()

# Global audio manager instance
_audio_manager: Optional[PiAudioManager] = None

def get_audio_manager() -> PiAudioManager:
    """Get global audio manager instance."""
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = PiAudioManager()
    return _audio_manager

# Convenience functions
def start_alarm_sound(alarm_id: str, alarm_label: str = "Alarm") -> bool:
    """Start playing alarm sound."""
    return get_audio_manager().start_alarm_sound(alarm_id, alarm_label)

def stop_alarm_sound(alarm_id: str) -> bool:
    """Stop playing alarm sound."""
    return get_audio_manager().stop_alarm_sound(alarm_id)

def stop_all_alarms():
    """Stop all alarm sounds."""
    get_audio_manager().stop_all_alarms()

def test_audio() -> bool:
    """Test audio output."""
    return get_audio_manager().test_audio()

if __name__ == "__main__":
    # Test the audio system
    logging.basicConfig(level=logging.INFO)
    
    print("🔊 Testing Pi Audio Manager...")
    
    # Test audio
    if test_audio():
        print("✅ Audio test successful!")
    else:
        print("❌ Audio test failed!")
    
    # Test alarm sound
    print("🚨 Testing alarm sound (3 seconds)...")
    start_alarm_sound("test", "Test Alarm")
    time.sleep(3)
    stop_alarm_sound("test")
    
    print("🎉 Audio manager test complete!")
