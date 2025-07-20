"""
Enhanced GAN Cube Protocol Driver
Implements robust move tracking, serial number handling, and missed move recovery
based on the gan-web-bluetooth JavaScript implementation.
"""

from __future__ import annotations
import asyncio
import time
from typing import List, Dict, Optional, Callable, Any
from collections import deque
from dataclasses import dataclass
from abc import ABC, abstractmethod

try:
    from .gan_decrypt import (
        CubeMove, CubeEvent, MoveEvent, FaceletsEvent, BatteryEvent, HardwareEvent,
        CubeState, parse_move_enhanced, parse_facelets_event, parse_battery_event,
        parse_hardware_event, decrypt_packet
    )
except ImportError:
    from gan_decrypt import (
        CubeMove, CubeEvent, MoveEvent, FaceletsEvent, BatteryEvent, HardwareEvent,
        CubeState, parse_move_enhanced, parse_facelets_event, parse_battery_event,
        parse_hardware_event, decrypt_packet
    )


class GanProtocolDriver(ABC):
    """Base class for GAN cube protocol drivers."""
    
    @abstractmethod
    async def handle_state_event(self, raw_connection: 'GanCubeRawConnection', 
                                event_message: bytes) -> List[CubeEvent]:
        """Handle binary event messages from cube device."""
        pass
    
    @abstractmethod
    def create_command_message(self, command: Dict[str, Any]) -> Optional[bytes]:
        """Create binary command message for cube device."""
        pass


class GanGen3ProtocolDriver(GanProtocolDriver):
    """
    Driver implementation for GAN Gen3 protocol, supported cubes:
    - GAN356 i Carry 2
    """
    
    def __init__(self):
        self.serial = -1
        self.last_serial = -1
        self.last_local_timestamp: Optional[float] = None
        self.move_buffer: deque[CubeEvent] = deque(maxlen=100)  # FIFO buffer for moves
        
    def create_command_message(self, command: Dict[str, Any]) -> Optional[bytes]:
        """Create binary command message for cube device."""
        cmd_type = command.get("type")
        
        if cmd_type == "REQUEST_HARDWARE":
            return bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        elif cmd_type == "REQUEST_FACELETS":
            return bytes([0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        elif cmd_type == "REQUEST_BATTERY":
            return bytes([0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        elif cmd_type == "REQUEST_RESET":
            return bytes([0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        
        return None
    
    async def request_move_history(self, conn: 'GanCubeRawConnection', 
                                  serial: int, count: int) -> None:
        """Private cube command for requesting move history."""
        # Create move history request command
        cmd = bytes([0x05, serial, count, 0x00, 0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        await conn.send_command_message(cmd)
    
    def is_serial_in_range(self, start: int, end: int, serial: int, 
                          closed_start: bool = False, closed_end: bool = False) -> bool:
        """
        Check if circular serial number (modulo 256) fits into (start,end) serial number range.
        By default range is open, set closed_start / closed_end to make it closed.
        """
        # Handle circular serial numbers (0-255)
        if start <= end:
            if closed_start and closed_end:
                return start <= serial <= end
            elif closed_start:
                return start <= serial < end
            elif closed_end:
                return start < serial <= end
            else:
                return start < serial < end
        else:  # Wrap around case
            if closed_start and closed_end:
                return serial >= start or serial <= end
            elif closed_start:
                return serial >= start or serial < end
            elif closed_end:
                return serial > start or serial <= end
            else:
                return serial > start or serial < end
    
    def inject_missed_move_to_buffer(self, move_event: CubeEvent) -> None:
        """Used to inject missed moves to FIFO buffer."""
        self.move_buffer.append(move_event)
    
    async def evict_move_buffer(self, conn: Optional['GanCubeRawConnection'] = None) -> List[CubeEvent]:
        """
        Evict move events from FIFO buffer until missing move event detected.
        In case of missing move, and if connection is provided, submit request for move history to fill gap in buffer.
        """
        events = []
        
        while self.move_buffer:
            event = self.move_buffer[0]
            
            if isinstance(event, MoveEvent):
                expected_serial = (self.last_serial + 1) % 256
                
                if event.move.serial == expected_serial:
                    # Move is in sequence, evict it
                    self.move_buffer.popleft()
                    events.append(event)
                    self.last_serial = event.move.serial
                    self.last_local_timestamp = event.move.local_timestamp
                else:
                    # Missing move detected
                    if conn and self.is_serial_in_range(self.last_serial, event.move.serial, expected_serial):
                        # Request missing moves
                        missing_count = (event.move.serial - expected_serial) % 256
                        await self.request_move_history(conn, expected_serial, missing_count)
                    break
            else:
                # Non-move event, just evict
                self.move_buffer.popleft()
                events.append(event)
        
        return events
    
    async def check_if_move_missed(self, conn: 'GanCubeRawConnection') -> None:
        """Used in response to periodic facelets event to check if any moves missed."""
        if self.last_local_timestamp and time.time() - self.last_local_timestamp > 5.0:
            # No moves for 5 seconds, request recent move history
            await self.request_move_history(conn, (self.last_serial + 1) % 256, 10)
    
    async def handle_state_event(self, conn: 'GanCubeRawConnection', 
                                event_message: bytes) -> List[CubeEvent]:
        """Handle binary event messages from cube device."""
        events = []
        
        if len(event_message) < 16:
            return events
        
        # Log packet details for debugging
        packet_type = event_message[0] if len(event_message) > 0 else 0
        
        try:
            # Import here to avoid circular imports
            try:
                from .gan_decrypt import is_move_packet
            except ImportError:
                from gan_decrypt import is_move_packet
            
            # First attempt to parse as Gen3 facelets event (may be >16 bytes)
            facelets_evt = parse_facelets_event(event_message)
            if facelets_evt:
                events.append(facelets_evt)
                await self.check_if_move_missed(conn)

            if is_move_packet(event_message):
                print(f"🔄 Detected move packet")
                move = parse_move_enhanced(event_message)
                move_event = MoveEvent(move)
                
                # Add to buffer for ordering
                self.move_buffer.append(move_event)

                # Always emit the move immediately so callers get timely updates
                events.append(move_event)
                
                # Additionally evict any subsequently ordered moves (fills gaps)
                ordered_events = await self.evict_move_buffer(conn)
                events.extend(ordered_events)
                
            # Ignore 19-byte 0x02 status/telemetry frames – they're not moves
            elif len(event_message) == 19 and packet_type == 0x02:
                pass  # Silently ignore status frames
            
            elif len(event_message) == 16:
                # 16-byte packets are typically command responses or status
                pass  # Silently ignore most 16-byte status packets
                
                # Try to parse as different event types
                if packet_type == 0x03:  # Facelets state event
                    facelets_event = parse_facelets_event(event_message)
                    if facelets_event:
                        events.append(facelets_event)
                        await self.check_if_move_missed(conn)
                        
                elif packet_type == 0x04:  # Battery event
                    battery_event = parse_battery_event(event_message)
                    if battery_event:
                        events.append(battery_event)
                        
                elif packet_type == 0x05:  # Hardware event
                    hardware_event = parse_hardware_event(event_message)
                    if hardware_event:
                        events.append(hardware_event)
                        
            else:
                print(f"❓ Unknown packet type: len={len(event_message)}, type=0x{packet_type:02x}")

        except Exception as e:
            print(f"❌ Error parsing event: {e}")
            print(f"   Packet: {event_message.hex()}")
        
        return events


@dataclass
class GanCubeRawConnection:
    """Raw connection interface for internal use."""
    
    send_command_message: Callable[[bytes], Any]
    disconnect: Callable[[], Any]


class GanCubeConnection:
    """
    Connection object representing connection API and state.
    Enhanced with robust move tracking and state management.
    """
    
    def __init__(self, device_name: str, device_mac: str, 
                 raw_connection: GanCubeRawConnection,
                 protocol_driver: GanProtocolDriver):
        self.device_name = device_name
        self.device_mac = device_mac
        self._raw_connection = raw_connection
        self._protocol_driver = protocol_driver
        self._event_callbacks: List[Callable[[CubeEvent], None]] = []
        self._cube_state = CubeState.solved()
        self._move_count = 0
        self._last_solved_move_count = 0
        
    def add_event_callback(self, callback: Callable[[CubeEvent], None]) -> None:
        """Add callback for cube events."""
        self._event_callbacks.append(callback)
    
    def remove_event_callback(self, callback: Callable[[CubeEvent], None]) -> None:
        """Remove event callback."""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)
    
    async def handle_notification(self, data: bytes, key: bytes, iv: bytes) -> None:
        """Handle BLE notification with enhanced processing."""
        try:
            # Decrypt the packet
            decrypted = decrypt_packet(data, key, iv)
            
            # Process through protocol driver
            events = await self._protocol_driver.handle_state_event(self._raw_connection, decrypted)
            
            # Handle each event
            for event in events:
                await self._process_event(event)
                
                # Notify callbacks
                for callback in self._event_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            callback(event)
                    except Exception as e:
                        print(f"Error in event callback: {e}")
                        
        except Exception as e:
            print(f"Error handling notification: {e}")
    
    async def _process_event(self, event: CubeEvent) -> None:
        """Process individual cube events."""
        if isinstance(event, MoveEvent):
            self._move_count += 1
            # Apply move to cube state (simplified - full implementation would track actual state)
            # For now, just check if we're back to solved based on move count
            if self._move_count > self._last_solved_move_count and self._cube_state.is_solved():
                # Potential solve - in real implementation, would verify actual cube state
                pass
                
        elif isinstance(event, FaceletsEvent):
            self._cube_state = event.state
            if event.state.is_solved():
                self._last_solved_move_count = self._move_count
    
    def is_solved(self) -> bool:
        """Check if cube is currently solved."""
        return self._cube_state.is_solved()
    
    def get_move_count(self) -> int:
        """Get total move count."""
        return self._move_count
    
    async def send_cube_command(self, command: Dict[str, Any]) -> None:
        """Send command to the cube."""
        cmd_message = self._protocol_driver.create_command_message(command)
        if cmd_message:
            await self._raw_connection.send_command_message(cmd_message)
    
    async def disconnect(self) -> None:
        """Close this connection."""
        await self._raw_connection.disconnect()
    
    async def request_battery_level(self) -> None:
        """Request current battery level."""
        await self.send_cube_command({"type": "REQUEST_BATTERY"})
    
    async def request_hardware_info(self) -> None:
        """Request hardware information."""
        await self.send_cube_command({"type": "REQUEST_HARDWARE"})
    
    async def reset_cube_state(self) -> None:
        """Reset cube to solved state."""
        await self.send_cube_command({"type": "REQUEST_RESET"})
        self._cube_state = CubeState.solved()
        self._move_count = 0
        self._last_solved_move_count = 0
