"""
MQTT Publisher for IoT and real-time data streaming
"""

from typing import Dict, Optional
import json
from datetime import datetime
from loguru import logger

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logger.warning("paho-mqtt package not installed. MQTT functionality disabled.")

from ..config import settings


class MQTTPublisher:
    """
    MQTT publisher for quality data streaming
    """

    def __init__(
        self,
        broker_host: Optional[str] = None,
        broker_port: Optional[int] = None,
        topic_prefix: Optional[str] = None
    ):
        """
        Initialize MQTT publisher

        Args:
            broker_host: MQTT broker host
            broker_port: MQTT broker port
            topic_prefix: Topic prefix for all messages
        """
        self.broker_host = broker_host or settings.integration.mqtt_broker_host
        self.broker_port = broker_port or settings.integration.mqtt_broker_port
        self.topic_prefix = topic_prefix or settings.integration.mqtt_topic_prefix

        self.client: Optional[mqtt.Client] = None
        self.connected = False

        if not MQTT_AVAILABLE:
            logger.error("MQTT publisher cannot be initialized: paho-mqtt package not installed")

        logger.info(f"MQTT publisher initialized for {self.broker_host}:{self.broker_port}")

    def connect(self) -> bool:
        """
        Connect to MQTT broker

        Returns:
            True if connected successfully
        """
        if not MQTT_AVAILABLE:
            return False

        try:
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect

            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()

            logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for successful connection"""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback for disconnection"""
        self.connected = False
        logger.info("Disconnected from MQTT broker")

    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client and self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")

    def publish_detection(self, detection: Dict) -> bool:
        """
        Publish defect detection event

        Args:
            detection: Detection data

        Returns:
            True if published successfully
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False

        topic = f"{self.topic_prefix}/detection"

        payload = {
            "timestamp": datetime.now().isoformat(),
            "type": "defect_detection",
            "data": detection
        }

        return self._publish(topic, payload)

    def publish_quality_metrics(self, metrics: Dict) -> bool:
        """
        Publish quality metrics

        Args:
            metrics: Quality metrics data

        Returns:
            True if published successfully
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False

        topic = f"{self.topic_prefix}/metrics"

        payload = {
            "timestamp": datetime.now().isoformat(),
            "type": "quality_metrics",
            "data": metrics
        }

        return self._publish(topic, payload)

    def publish_alert(self, alert: Dict) -> bool:
        """
        Publish quality alert

        Args:
            alert: Alert data

        Returns:
            True if published successfully
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker")
            return False

        topic = f"{self.topic_prefix}/alerts"

        payload = {
            "timestamp": datetime.now().isoformat(),
            "type": "quality_alert",
            "data": alert
        }

        return self._publish(topic, payload)

    def _publish(self, topic: str, payload: Dict) -> bool:
        """
        Publish message to topic

        Args:
            topic: MQTT topic
            payload: Message payload

        Returns:
            True if published successfully
        """
        try:
            result = self.client.publish(
                topic,
                json.dumps(payload),
                qos=2
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {topic}")
                return True
            else:
                logger.error(f"Failed to publish to {topic}: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"Error publishing to MQTT: {e}")
            return False
