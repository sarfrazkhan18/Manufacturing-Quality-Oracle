"""
PLC (Programmable Logic Controller) Connector
Uses Modbus TCP for PLC communication
"""

from typing import Optional
from loguru import logger

try:
    from pymodbus.client import ModbusTcpClient
    from pymodbus.exceptions import ModbusException
    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False
    logger.warning("pymodbus package not installed. PLC functionality disabled.")

from ..config import settings


class PLCConnector:
    """
    Connector for PLC communication via Modbus TCP
    """

    def __init__(
        self,
        ip_address: Optional[str] = None,
        port: Optional[int] = None,
        unit_id: int = 1
    ):
        """
        Initialize PLC connector

        Args:
            ip_address: PLC IP address
            port: Modbus TCP port
            unit_id: Modbus unit ID
        """
        self.ip_address = ip_address or settings.integration.plc_ip
        self.port = port or settings.integration.plc_port
        self.unit_id = unit_id

        self.client: Optional[ModbusTcpClient] = None
        self.connected = False

        if not MODBUS_AVAILABLE:
            logger.error("PLC connector cannot be initialized: pymodbus package not installed")

        logger.info(f"PLC connector initialized for {self.ip_address}:{self.port}")

    def connect(self) -> bool:
        """
        Connect to PLC

        Returns:
            True if connected successfully
        """
        if not MODBUS_AVAILABLE:
            return False

        try:
            self.client = ModbusTcpClient(
                host=self.ip_address,
                port=self.port,
                timeout=5
            )

            self.connected = self.client.connect()

            if self.connected:
                logger.info(f"Connected to PLC at {self.ip_address}:{self.port}")
            else:
                logger.error("Failed to connect to PLC")

            return self.connected

        except Exception as e:
            logger.error(f"Error connecting to PLC: {e}")
            return False

    def disconnect(self):
        """Disconnect from PLC"""
        if self.client and self.connected:
            try:
                self.client.close()
                self.connected = False
                logger.info("Disconnected from PLC")
            except Exception as e:
                logger.error(f"Error disconnecting from PLC: {e}")

    def trigger_reject_mechanism(self, part_id: str) -> bool:
        """
        Trigger reject mechanism for defective part

        Args:
            part_id: Part identifier

        Returns:
            True if successful
        """
        if not self.connected:
            logger.warning("Not connected to PLC")
            return False

        try:
            # Write to reject coil (address 0)
            # This would be configured based on actual PLC programming
            result = self.client.write_coil(
                address=0,
                value=True,
                unit=self.unit_id
            )

            if result.isError():
                logger.error(f"Error triggering reject mechanism: {result}")
                return False

            logger.info(f"Triggered reject mechanism for part {part_id}")
            return True

        except Exception as e:
            logger.error(f"Error triggering reject mechanism: {e}")
            return False

    def update_quality_counter(self, counter_type: str, value: int) -> bool:
        """
        Update quality counter in PLC

        Args:
            counter_type: Counter type ("pass", "fail", "total")
            value: Counter value

        Returns:
            True if successful
        """
        if not self.connected:
            logger.warning("Not connected to PLC")
            return False

        # Map counter types to register addresses
        address_map = {
            "pass": 100,
            "fail": 101,
            "total": 102
        }

        address = address_map.get(counter_type)
        if address is None:
            logger.error(f"Unknown counter type: {counter_type}")
            return False

        try:
            result = self.client.write_register(
                address=address,
                value=value,
                unit=self.unit_id
            )

            if result.isError():
                logger.error(f"Error updating counter: {result}")
                return False

            logger.debug(f"Updated {counter_type} counter to {value}")
            return True

        except Exception as e:
            logger.error(f"Error updating quality counter: {e}")
            return False

    def read_sensor_value(self, sensor_address: int) -> Optional[int]:
        """
        Read sensor value from PLC

        Args:
            sensor_address: Sensor register address

        Returns:
            Sensor value or None
        """
        if not self.connected:
            logger.warning("Not connected to PLC")
            return None

        try:
            result = self.client.read_holding_registers(
                address=sensor_address,
                count=1,
                unit=self.unit_id
            )

            if result.isError():
                logger.error(f"Error reading sensor: {result}")
                return None

            value = result.registers[0]
            logger.debug(f"Read sensor at address {sensor_address}: {value}")

            return value

        except Exception as e:
            logger.error(f"Error reading sensor value: {e}")
            return None
