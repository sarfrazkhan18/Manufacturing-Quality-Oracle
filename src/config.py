"""
Configuration management for Manufacturing Quality Oracle
"""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data")
MODEL_DIR = BASE_DIR / os.getenv("MODEL_DIR", "models")
LOG_DIR = BASE_DIR / os.getenv("LOG_DIR", "logs")
BACKUP_DIR = BASE_DIR / os.getenv("BACKUP_DIR", "backups")
REPORT_DIR = BASE_DIR / os.getenv("REPORT_OUTPUT_DIR", "reports")

# Create directories if they don't exist
for directory in [DATA_DIR, MODEL_DIR, LOG_DIR, BACKUP_DIR, REPORT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class AppConfig(BaseModel):
    """Application configuration"""
    name: str = Field(default_factory=lambda: os.getenv("APP_NAME", "Manufacturing Quality Oracle"))
    version: str = Field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))
    environment: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "production"))
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


class RoboflowConfig(BaseModel):
    """Roboflow API configuration"""
    api_key: str = Field(default_factory=lambda: os.getenv("ROBOFLOW_API_KEY", ""))
    workspace: str = Field(default_factory=lambda: os.getenv("ROBOFLOW_WORKSPACE", ""))
    project: str = Field(default_factory=lambda: os.getenv("ROBOFLOW_PROJECT", "defect-detection"))


class ModelConfig(BaseModel):
    """AI model configuration"""
    yolo_model_path: Path = Field(default_factory=lambda: Path(os.getenv("YOLO_MODEL_PATH", "./models/yolov8n.pt")))
    custom_model_path: Path = Field(default_factory=lambda: Path(os.getenv("CUSTOM_MODEL_PATH", "./models/custom_defect_detector.pt")))
    confidence_threshold: float = Field(default_factory=lambda: float(os.getenv("CONFIDENCE_THRESHOLD", "0.5")))
    iou_threshold: float = Field(default_factory=lambda: float(os.getenv("IOU_THRESHOLD", "0.45")))
    model_version: str = Field(default_factory=lambda: os.getenv("MODEL_VERSION", "v1.0"))


class ReflectionConfig(BaseModel):
    """Reflection agent configuration"""
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = Field(default_factory=lambda: os.getenv("REFLECTION_MODEL", "gpt-4"))
    temperature: float = Field(default_factory=lambda: float(os.getenv("REFLECTION_TEMPERATURE", "0.7")))


class CameraConfig(BaseModel):
    """Camera configuration"""
    resolution_width: int = Field(default_factory=lambda: int(os.getenv("CAMERA_RESOLUTION_WIDTH", "1920")))
    resolution_height: int = Field(default_factory=lambda: int(os.getenv("CAMERA_RESOLUTION_HEIGHT", "1080")))
    fps: int = Field(default_factory=lambda: int(os.getenv("CAMERA_FPS", "30")))
    buffer_size: int = Field(default_factory=lambda: int(os.getenv("CAMERA_BUFFER_SIZE", "10")))
    camera_ids: List[int] = Field(default_factory=lambda: [int(x) for x in os.getenv("CAMERA_IDS", "0").split(",")])


class EdgeConfig(BaseModel):
    """Edge device configuration"""
    device_type: str = Field(default_factory=lambda: os.getenv("EDGE_DEVICE_TYPE", "generic"))
    compute_threads: int = Field(default_factory=lambda: int(os.getenv("EDGE_COMPUTE_THREADS", "4")))
    gpu_acceleration: bool = Field(default_factory=lambda: os.getenv("GPU_ACCELERATION", "true").lower() == "true")
    tensorrt_optimization: bool = Field(default_factory=lambda: os.getenv("TENSORRT_OPTIMIZATION", "true").lower() == "true")


class DatabaseConfig(BaseModel):
    """Database configuration"""
    host: str = Field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = Field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    name: str = Field(default_factory=lambda: os.getenv("DB_NAME", "quality_oracle"))
    user: str = Field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    password: str = Field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisConfig(BaseModel):
    """Redis cache configuration"""
    host: str = Field(default_factory=lambda: os.getenv("REDIS_HOST", "localhost"))
    port: int = Field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))
    db: int = Field(default_factory=lambda: int(os.getenv("REDIS_DB", "0")))
    password: Optional[str] = Field(default_factory=lambda: os.getenv("REDIS_PASSWORD", None))


class IntegrationConfig(BaseModel):
    """Integration configuration for MES/ERP"""
    mes_api_url: str = Field(default_factory=lambda: os.getenv("MES_API_URL", ""))
    mes_api_key: str = Field(default_factory=lambda: os.getenv("MES_API_KEY", ""))
    erp_api_url: str = Field(default_factory=lambda: os.getenv("ERP_API_URL", ""))
    erp_api_key: str = Field(default_factory=lambda: os.getenv("ERP_API_KEY", ""))

    opcua_server_url: str = Field(default_factory=lambda: os.getenv("OPCUA_SERVER_URL", "opc.tcp://localhost:4840"))
    opcua_username: Optional[str] = Field(default_factory=lambda: os.getenv("OPCUA_USERNAME", None))
    opcua_password: Optional[str] = Field(default_factory=lambda: os.getenv("OPCUA_PASSWORD", None))

    mqtt_broker_host: str = Field(default_factory=lambda: os.getenv("MQTT_BROKER_HOST", "localhost"))
    mqtt_broker_port: int = Field(default_factory=lambda: int(os.getenv("MQTT_BROKER_PORT", "1883")))
    mqtt_topic_prefix: str = Field(default_factory=lambda: os.getenv("MQTT_TOPIC_PREFIX", "quality/oracle"))

    plc_ip: str = Field(default_factory=lambda: os.getenv("PLC_IP_ADDRESS", "192.168.1.100"))
    plc_port: int = Field(default_factory=lambda: int(os.getenv("PLC_PORT", "502")))


class QualityThresholds(BaseModel):
    """Quality threshold configuration"""
    defect_rate_threshold: float = Field(default_factory=lambda: float(os.getenv("DEFECT_RATE_THRESHOLD", "0.05")))
    critical_defect_threshold: float = Field(default_factory=lambda: float(os.getenv("CRITICAL_DEFECT_THRESHOLD", "0.01")))
    process_deviation_threshold: float = Field(default_factory=lambda: float(os.getenv("PROCESS_DEVIATION_THRESHOLD", "2.0")))
    supplier_min_score: float = Field(default_factory=lambda: float(os.getenv("SUPPLIER_MIN_SCORE", "70.0")))


class Settings(BaseModel):
    """Global settings"""
    app: AppConfig = Field(default_factory=AppConfig)
    roboflow: RoboflowConfig = Field(default_factory=RoboflowConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    reflection: ReflectionConfig = Field(default_factory=ReflectionConfig)
    camera: CameraConfig = Field(default_factory=CameraConfig)
    edge: EdgeConfig = Field(default_factory=EdgeConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    integration: IntegrationConfig = Field(default_factory=IntegrationConfig)
    thresholds: QualityThresholds = Field(default_factory=QualityThresholds)


# Global settings instance
settings = Settings()
