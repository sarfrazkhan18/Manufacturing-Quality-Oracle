"""
FastAPI Server for Manufacturing Quality Oracle
Provides REST API for quality inspection and monitoring
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import uvicorn
import numpy as np
import cv2
from datetime import datetime

from ..config import settings
from ..vision import DefectDetector, ImageProcessor
from ..quality import SupplierQualityPredictor, CustomerFeedbackIntegration
from ..reflection import PerformanceAnalyzer

# Create FastAPI app
app = FastAPI(
    title="Manufacturing Quality Oracle API",
    description="AI-powered quality assurance system",
    version=settings.app.version
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize components
detector = DefectDetector()
processor = ImageProcessor()
supplier_predictor = SupplierQualityPredictor()
feedback_integration = CustomerFeedbackIntegration()
performance_analyzer = PerformanceAnalyzer()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app.name,
        "version": settings.app.version,
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/inspect")
async def inspect_image(file: UploadFile = File(...)):
    """
    Inspect uploaded image for defects

    Args:
        file: Image file

    Returns:
        Inspection results with detected defects
    """
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Preprocess
        processed = processor.preprocess_for_detection(image)

        # Detect defects
        detections = detector.detect(processed)

        # Format response
        results = {
            "timestamp": datetime.now().isoformat(),
            "image_shape": image.shape,
            "defects_detected": len(detections),
            "defects": [d.to_dict() for d in detections]
        }

        return JSONResponse(content=results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics")
async def get_metrics():
    """Get system performance metrics"""
    try:
        metrics = {
            "detector": detector.get_metrics(),
            "performance": performance_analyzer.calculate_metrics(),
            "timestamp": datetime.now().isoformat()
        }

        return JSONResponse(content=metrics)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/suppliers")
async def get_suppliers():
    """Get supplier quality rankings"""
    try:
        rankings = supplier_predictor.get_supplier_ranking()

        return JSONResponse(content={
            "suppliers": rankings,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/feedback")
async def submit_feedback(
    customer_id: str,
    product_id: str,
    feedback_text: str,
    rating: Optional[int] = None
):
    """
    Submit customer feedback

    Args:
        customer_id: Customer identifier
        product_id: Product identifier
        feedback_text: Feedback text
        rating: Optional rating (1-5)

    Returns:
        Feedback processing results
    """
    try:
        feedback = feedback_integration.record_feedback(
            customer_id=customer_id,
            product_id=product_id,
            feedback_text=feedback_text,
            rating=rating
        )

        return JSONResponse(content=feedback)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/feedback/trends")
async def get_feedback_trends(days: int = 30):
    """Get customer feedback trends"""
    try:
        trends = feedback_integration.analyze_feedback_trends(days=days)

        return JSONResponse(content=trends)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def start_server():
    """Start the API server"""
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.app.debug,
        log_level=settings.app.log_level.lower()
    )


if __name__ == "__main__":
    start_server()
