"""
Manufacturing Quality Oracle - Main Application Entry Point
"""

import asyncio
import signal
import sys
from pathlib import Path
from loguru import logger

from .config import settings, LOG_DIR
from .vision import DefectDetector, CameraInterface, MultiCameraManager
from .reflection import ReflectionAgent, PerformanceAnalyzer, ImprovementEngine
from .quality import SupplierQualityPredictor, CustomerFeedbackIntegration, ProcessDeviationMonitor
from .integration import MESConnector, MQTTPublisher


class QualityOracle:
    """
    Main application orchestrator for Manufacturing Quality Oracle
    """

    def __init__(self):
        """Initialize the quality oracle system"""

        # Setup logging
        log_file = LOG_DIR / f"quality_oracle_{settings.app.environment}.log"
        logger.add(
            log_file,
            rotation="500 MB",
            retention="30 days",
            level=settings.app.log_level
        )

        logger.info("=" * 60)
        logger.info(f"Manufacturing Quality Oracle v{settings.app.version}")
        logger.info(f"Environment: {settings.app.environment}")
        logger.info("=" * 60)

        # Initialize components
        self.defect_detector = None
        self.camera_manager = None
        self.reflection_agent = None
        self.performance_analyzer = None
        self.improvement_engine = None
        self.supplier_predictor = None
        self.feedback_integration = None
        self.process_monitor = None
        self.mes_connector = None
        self.mqtt_publisher = None

        # Control flag
        self.running = False

    def initialize(self):
        """Initialize all system components"""
        logger.info("Initializing system components...")

        # Computer Vision
        try:
            logger.info("Initializing defect detector...")
            self.defect_detector = DefectDetector()
        except Exception as e:
            logger.error(f"Failed to initialize defect detector: {e}")

        # Camera system
        try:
            logger.info("Initializing camera system...")
            self.camera_manager = MultiCameraManager()
        except Exception as e:
            logger.error(f"Failed to initialize camera system: {e}")

        # Reflection and improvement
        try:
            logger.info("Initializing reflection system...")
            self.reflection_agent = ReflectionAgent()
            self.performance_analyzer = PerformanceAnalyzer()
            self.improvement_engine = ImprovementEngine(
                self.reflection_agent,
                self.performance_analyzer,
                auto_apply=False  # Manual approval for safety
            )
        except Exception as e:
            logger.error(f"Failed to initialize reflection system: {e}")

        # Quality management
        try:
            logger.info("Initializing quality management...")
            self.supplier_predictor = SupplierQualityPredictor()
            self.feedback_integration = CustomerFeedbackIntegration()
            self.process_monitor = ProcessDeviationMonitor()
        except Exception as e:
            logger.error(f"Failed to initialize quality management: {e}")

        # Industrial integration
        try:
            logger.info("Initializing industrial integration...")
            self.mes_connector = MESConnector()
            self.mqtt_publisher = MQTTPublisher()
            self.mqtt_publisher.connect()
        except Exception as e:
            logger.error(f"Failed to initialize industrial integration: {e}")

        logger.info("System initialization complete!")

    async def run(self):
        """Main application loop"""
        self.running = True

        logger.info("Starting Manufacturing Quality Oracle...")

        # Start cameras
        if self.camera_manager:
            logger.info("Starting camera system...")
            self.camera_manager.start_all()

        # Main processing loop
        inspection_count = 0
        improvement_cycle_interval = 100  # Run improvement cycle every 100 inspections

        try:
            while self.running:
                # Get frames from all cameras
                if self.camera_manager:
                    frames = self.camera_manager.get_all_frames()

                    for camera_id, frame in frames.items():
                        # Detect defects
                        if self.defect_detector:
                            detections = self.defect_detector.detect(frame)

                            # Log detections
                            if detections:
                                logger.info(
                                    f"Camera {camera_id}: Detected {len(detections)} defects"
                                )

                                # Send to MES
                                if self.mes_connector:
                                    for detection in detections:
                                        if detection.severity in ["critical", "high"]:
                                            self.mes_connector.send_defect_alert(
                                                detection.to_dict(),
                                                severity=detection.severity
                                            )

                                # Publish via MQTT
                                if self.mqtt_publisher:
                                    for detection in detections:
                                        self.mqtt_publisher.publish_detection(
                                            detection.to_dict()
                                        )

                                # Record for performance analysis
                                if self.performance_analyzer:
                                    for detection in detections:
                                        self.performance_analyzer.record_detection(
                                            detection.to_dict()
                                        )

                        inspection_count += 1

                # Run improvement cycle periodically
                if inspection_count % improvement_cycle_interval == 0 and inspection_count > 0:
                    logger.info("Running improvement cycle...")
                    if self.improvement_engine:
                        try:
                            cycle_result = self.improvement_engine.run_improvement_cycle()
                            logger.info(f"Improvement cycle complete: {cycle_result.get('status')}")
                        except Exception as e:
                            logger.error(f"Error in improvement cycle: {e}")

                # Small delay to prevent CPU overload
                await asyncio.sleep(0.01)

        except KeyboardInterrupt:
            logger.info("Received shutdown signal...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down Manufacturing Quality Oracle...")

        self.running = False

        # Stop cameras
        if self.camera_manager:
            logger.info("Stopping cameras...")
            self.camera_manager.stop_all()

        # Disconnect MQTT
        if self.mqtt_publisher:
            logger.info("Disconnecting MQTT...")
            self.mqtt_publisher.disconnect()

        # Save final metrics
        if self.performance_analyzer:
            logger.info("Saving performance metrics...")
            report = self.performance_analyzer.generate_performance_report()
            logger.info(f"Final metrics: {report.get('overall_metrics')}")

        logger.info("Shutdown complete. Goodbye!")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    sys.exit(0)


def main():
    """Main entry point"""

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and run application
    app = QualityOracle()
    app.initialize()

    # Run async event loop
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
