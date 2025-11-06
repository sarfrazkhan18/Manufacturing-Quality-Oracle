"""
OPC UA Client for industrial protocol communication
"""

from typing import Optional, Any
from loguru import logger

try:
    from opcua import Client as OPCUAClientBase
    from opcua import ua
    OPCUA_AVAILABLE = True
except ImportError:
    OPCUA_AVAILABLE = False
    logger.warning("opcua package not installed. OPC UA functionality disabled.")

from ..config import settings


class OPCUAClient:
    """
    OPC UA client for industrial communication
    """

    def __init__(
        self,
        server_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize OPC UA client

        Args:
            server_url: OPC UA server URL
            username: Optional username
            password: Optional password
        """
        self.server_url = server_url or settings.integration.opcua_server_url
        self.username = username or settings.integration.opcua_username
        self.password = password or settings.integration.opcua_password

        self.client: Optional[OPCUAClientBase] = None
        self.connected = False

        if not OPCUA_AVAILABLE:
            logger.error("OPC UA client cannot be initialized: opcua package not installed")

        logger.info(f"OPC UA client initialized for {self.server_url}")

    def connect(self) -> bool:
        """
        Connect to OPC UA server

        Returns:
            True if connected successfully
        """
        if not OPCUA_AVAILABLE:
            return False

        try:
            self.client = OPCUAClientBase(self.server_url)

            if self.username and self.password:
                self.client.set_user(self.username)
                self.client.set_password(self.password)

            self.client.connect()
            self.connected = True

            logger.info(f"Connected to OPC UA server: {self.server_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to OPC UA server: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from OPC UA server"""
        if self.client and self.connected:
            try:
                self.client.disconnect()
                self.connected = False
                logger.info("Disconnected from OPC UA server")
            except Exception as e:
                logger.error(f"Error disconnecting from OPC UA server: {e}")

    def read_value(self, node_id: str) -> Optional[Any]:
        """
        Read value from OPC UA node

        Args:
            node_id: Node identifier

        Returns:
            Node value or None
        """
        if not self.connected:
            logger.warning("Not connected to OPC UA server")
            return None

        try:
            node = self.client.get_node(node_id)
            value = node.get_value()

            logger.debug(f"Read OPC UA node {node_id}: {value}")
            return value

        except Exception as e:
            logger.error(f"Error reading OPC UA node {node_id}: {e}")
            return None

    def write_value(self, node_id: str, value: Any) -> bool:
        """
        Write value to OPC UA node

        Args:
            node_id: Node identifier
            value: Value to write

        Returns:
            True if successful
        """
        if not self.connected:
            logger.warning("Not connected to OPC UA server")
            return False

        try:
            node = self.client.get_node(node_id)
            node.set_value(value)

            logger.debug(f"Wrote OPC UA node {node_id}: {value}")
            return True

        except Exception as e:
            logger.error(f"Error writing OPC UA node {node_id}: {e}")
            return False

    def write_quality_status(
        self,
        station_id: str,
        status: str,
        defect_count: int = 0
    ) -> bool:
        """
        Write quality status to OPC UA server

        Args:
            station_id: Station identifier
            status: Status string ("OK", "DEFECT", "WARNING")
            defect_count: Number of defects

        Returns:
            True if successful
        """
        status_node = f"ns=2;s=Station.{station_id}.QualityStatus"
        count_node = f"ns=2;s=Station.{station_id}.DefectCount"

        status_written = self.write_value(status_node, status)
        count_written = self.write_value(count_node, defect_count)

        return status_written and count_written
