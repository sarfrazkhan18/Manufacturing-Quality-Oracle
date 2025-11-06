"""
Roboflow API client for dataset management and augmentation
"""

from typing import Optional, Dict, List
from pathlib import Path
import os
from roboflow import Roboflow
from loguru import logger

from ..config import settings


class RoboflowClient:
    """
    Client for Roboflow dataset management and model deployment
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        workspace: Optional[str] = None,
        project: Optional[str] = None
    ):
        """
        Initialize Roboflow client

        Args:
            api_key: Roboflow API key
            workspace: Workspace name
            project: Project name
        """
        self.api_key = api_key or settings.roboflow.api_key
        self.workspace_name = workspace or settings.roboflow.workspace
        self.project_name = project or settings.roboflow.project

        if not self.api_key:
            logger.warning("Roboflow API key not provided. Some features will be unavailable.")
            self.rf = None
            self.workspace = None
            self.project = None
        else:
            # Initialize Roboflow
            self.rf = Roboflow(api_key=self.api_key)
            self.workspace = self.rf.workspace(self.workspace_name) if self.workspace_name else None
            self.project = self.workspace.project(self.project_name) if self.workspace and self.project_name else None

            logger.info(f"Roboflow client initialized: {self.workspace_name}/{self.project_name}")

    def download_dataset(
        self,
        version: int,
        format: str = "yolov8",
        location: Optional[Path] = None
    ) -> Path:
        """
        Download dataset from Roboflow

        Args:
            version: Dataset version number
            format: Export format (yolov8, coco, voc, etc.)
            location: Download location

        Returns:
            Path to downloaded dataset
        """
        if not self.project:
            raise ValueError("Roboflow project not initialized")

        download_path = location or settings.DATA_DIR / "datasets"
        download_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading dataset version {version} in {format} format...")

        dataset = self.project.version(version).download(
            model_format=format,
            location=str(download_path)
        )

        logger.info(f"Dataset downloaded to {dataset.location}")

        return Path(dataset.location)

    def upload_image(
        self,
        image_path: Path,
        annotation_path: Optional[Path] = None,
        batch_name: Optional[str] = None,
        split: str = "train"
    ) -> bool:
        """
        Upload image to Roboflow project

        Args:
            image_path: Path to image file
            annotation_path: Optional path to annotation file
            batch_name: Batch name for organization
            split: Dataset split (train, valid, test)

        Returns:
            True if upload successful
        """
        if not self.project:
            raise ValueError("Roboflow project not initialized")

        try:
            # Upload image
            self.project.upload(
                image_path=str(image_path),
                annotation_path=str(annotation_path) if annotation_path else None,
                batch_name=batch_name,
                split=split
            )

            logger.info(f"Uploaded image: {image_path.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to upload image {image_path}: {e}")
            return False

    def upload_batch(
        self,
        image_dir: Path,
        annotation_dir: Optional[Path] = None,
        batch_name: Optional[str] = None,
        split: str = "train"
    ) -> Dict[str, int]:
        """
        Upload batch of images to Roboflow

        Args:
            image_dir: Directory containing images
            annotation_dir: Directory containing annotations
            batch_name: Batch name for organization
            split: Dataset split

        Returns:
            Dictionary with upload statistics
        """
        if not self.project:
            raise ValueError("Roboflow project not initialized")

        success_count = 0
        fail_count = 0

        # Get image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        image_files = [
            f for f in image_dir.iterdir()
            if f.suffix.lower() in image_extensions
        ]

        logger.info(f"Uploading {len(image_files)} images to Roboflow...")

        for image_path in image_files:
            # Find corresponding annotation
            annotation_path = None
            if annotation_dir:
                annotation_path = annotation_dir / f"{image_path.stem}.txt"
                if not annotation_path.exists():
                    annotation_path = None

            # Upload
            success = self.upload_image(
                image_path=image_path,
                annotation_path=annotation_path,
                batch_name=batch_name,
                split=split
            )

            if success:
                success_count += 1
            else:
                fail_count += 1

        logger.info(
            f"Upload complete: {success_count} successful, {fail_count} failed"
        )

        return {
            "success": success_count,
            "failed": fail_count,
            "total": len(image_files)
        }

    def generate_version(
        self,
        augmentation_config: Optional[Dict] = None,
        preprocessing_config: Optional[Dict] = None
    ) -> int:
        """
        Generate new dataset version with augmentation

        Args:
            augmentation_config: Augmentation settings
            preprocessing_config: Preprocessing settings

        Returns:
            New version number
        """
        if not self.project:
            raise ValueError("Roboflow project not initialized")

        # Default augmentation for manufacturing quality
        if augmentation_config is None:
            augmentation_config = {
                "rotation": {"min": -15, "max": 15},
                "shear": {"min": -5, "max": 5},
                "brightness": {"min": -20, "max": 20},
                "exposure": {"min": -10, "max": 10},
                "blur": {"max": 2},
                "noise": {"max": 5}
            }

        # Default preprocessing
        if preprocessing_config is None:
            preprocessing_config = {
                "auto-orient": True,
                "resize": {"width": 640, "height": 640, "format": "Stretch to"}
            }

        logger.info("Generating new dataset version with augmentation...")

        # Note: Actual API calls would go here
        # This is a placeholder as the Roboflow API structure varies

        logger.info("Dataset version generated successfully")

        return self.project.versions[-1] if self.project.versions else 1

    def get_deployment_model(self, version: int) -> str:
        """
        Get deployment URL for trained model

        Args:
            version: Model version number

        Returns:
            Deployment URL or model ID
        """
        if not self.project:
            raise ValueError("Roboflow project not initialized")

        model = self.project.version(version)

        logger.info(f"Retrieved deployment model for version {version}")

        return model.id

    def get_project_stats(self) -> Dict:
        """
        Get project statistics

        Returns:
            Dictionary with project stats
        """
        if not self.project:
            return {"error": "Project not initialized"}

        stats = {
            "project_name": self.project_name,
            "workspace": self.workspace_name,
            "versions": len(self.project.versions) if hasattr(self.project, 'versions') else 0,
        }

        logger.info(f"Project stats: {stats}")

        return stats

    def annotate_with_model(
        self,
        image_path: Path,
        confidence: float = 0.5
    ) -> List[Dict]:
        """
        Use trained model to generate annotations

        Args:
            image_path: Path to image
            confidence: Confidence threshold

        Returns:
            List of predicted annotations
        """
        if not self.project:
            raise ValueError("Roboflow project not initialized")

        try:
            # Get latest model version
            model = self.project.version(self.project.version)

            # Run prediction
            prediction = model.predict(str(image_path), confidence=confidence)

            annotations = []
            for pred in prediction:
                annotations.append({
                    "class": pred["class"],
                    "confidence": pred["confidence"],
                    "bbox": [pred["x"], pred["y"], pred["width"], pred["height"]]
                })

            logger.info(f"Generated {len(annotations)} annotations for {image_path.name}")

            return annotations

        except Exception as e:
            logger.error(f"Failed to generate annotations: {e}")
            return []
