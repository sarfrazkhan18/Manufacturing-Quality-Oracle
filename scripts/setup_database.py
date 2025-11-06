"""
Database setup script for Manufacturing Quality Oracle
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from loguru import logger

from src.config import settings

# Create base
Base = declarative_base()


# Define database models
class Inspection(Base):
    """Inspection record"""
    __tablename__ = 'inspections'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    camera_id = Column(Integer)
    image_path = Column(String)
    defects_detected = Column(Integer, default=0)
    results = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)


class Defect(Base):
    """Defect record"""
    __tablename__ = 'defects'

    id = Column(Integer, primary_key=True)
    inspection_id = Column(Integer)
    defect_type = Column(String)
    confidence = Column(Float)
    severity = Column(String)
    bbox_x1 = Column(Integer)
    bbox_y1 = Column(Integer)
    bbox_x2 = Column(Integer)
    bbox_y2 = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)


class Supplier(Base):
    """Supplier record"""
    __tablename__ = 'suppliers'

    id = Column(Integer, primary_key=True)
    supplier_id = Column(String, unique=True)
    name = Column(String)
    quality_score = Column(Float)
    risk_level = Column(String)
    total_deliveries = Column(Integer, default=0)
    defect_rate = Column(Float, default=0.0)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class CustomerFeedback(Base):
    """Customer feedback record"""
    __tablename__ = 'customer_feedback'

    id = Column(Integer, primary_key=True)
    customer_id = Column(String)
    product_id = Column(String)
    feedback_text = Column(String)
    rating = Column(Integer)
    sentiment = Column(String)
    sentiment_score = Column(Float)
    action_taken = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)


class ProcessMetric(Base):
    """Process monitoring metric"""
    __tablename__ = 'process_metrics'

    id = Column(Integer, primary_key=True)
    metric_name = Column(String)
    value = Column(Float)
    baseline_mean = Column(Float)
    baseline_std = Column(Float)
    z_score = Column(Float)
    is_deviation = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.now)


def setup_database():
    """Setup database tables"""
    logger.info("Setting up database...")

    # Create engine
    engine = create_engine(settings.database.url)

    # Create all tables
    Base.metadata.create_all(engine)

    logger.info("Database tables created successfully!")

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Verify tables
    inspector = engine.dialect.get_table_names(engine.connect())
    logger.info(f"Created tables: {inspector}")

    session.close()

    return True


if __name__ == "__main__":
    try:
        setup_database()
        logger.info("Database setup complete!")
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)
