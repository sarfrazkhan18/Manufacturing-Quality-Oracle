"""
Dataset management for quality inspection system
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
import shutil
from datetime import datetime
from loguru import logger
import cv2
import numpy as np

from ..config import settings


class DatasetManager:
    """
    Manager for organizing and maintaining defect detection datasets
    """

    def __init__(self, dataset_root: Optional[Path] = None):
        """
        Initialize dataset manager

        Args:
            dataset_root: Root directory for datasets
        """
        self.dataset_root = dataset_root or settings.DATA_DIR / "datasets"
        self.dataset_root.mkdir(parents=True, exist_ok=True)

        # Dataset structure
        self.images_dir = self.dataset_root / "images"
        self.labels_dir = self.dataset_root / "labels"
        self.archive_dir = self.dataset_root / "archive"

        # Create directories
        for split in ["train", "valid", "test"]:
            (self.images_dir / split).mkdir(parents=True, exist_ok=True)
            (self.labels_dir / split).mkdir(parents=True, exist_ok=True)

        self.archive_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Dataset manager initialized at {self.dataset_root}")

    def add_sample(
        self,
        image: np.ndarray,
        annotations: List[Dict],
        split: str = "train",
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add new sample to dataset

        Args:
            image: Image as numpy array
            annotations: List of annotation dictionaries
            split: Dataset split (train/valid/test)
            metadata: Optional metadata

        Returns:
            True if successful
        """
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            image_name = f"defect_{timestamp}.jpg"

            # Save image
            image_path = self.images_dir / split / image_name
            cv2.imwrite(str(image_path), image)

            # Save annotations in YOLO format
            label_path = self.labels_dir / split / f"defect_{timestamp}.txt"
            self._save_yolo_annotations(label_path, annotations, image.shape)

            # Save metadata
            if metadata:
                metadata_path = label_path.with_suffix('.json')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)

            logger.info(f"Added sample to {split} set: {image_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add sample: {e}")
            return False

    def _save_yolo_annotations(
        self,
        label_path: Path,
        annotations: List[Dict],
        image_shape: Tuple
    ):
        """Save annotations in YOLO format"""
        height, width = image_shape[:2]

        with open(label_path, 'w') as f:
            for ann in annotations:
                # YOLO format: class_id x_center y_center width height (normalized)
                class_id = ann.get("class_id", 0)
                bbox = ann.get("bbox", [0, 0, 0, 0])  # [x1, y1, x2, y2]

                # Convert to YOLO format
                x_center = ((bbox[0] + bbox[2]) / 2) / width
                y_center = ((bbox[1] + bbox[3]) / 2) / height
                w = (bbox[2] - bbox[0]) / width
                h = (bbox[3] - bbox[1]) / height

                f.write(f"{class_id} {x_center} {y_center} {w} {h}\n")

    def get_dataset_stats(self) -> Dict:
        """
        Get dataset statistics

        Returns:
            Dictionary with dataset statistics
        """
        stats = {
            "splits": {},
            "total_images": 0,
            "defect_types": {}
        }

        for split in ["train", "valid", "test"]:
            image_dir = self.images_dir / split
            label_dir = self.labels_dir / split

            image_count = len(list(image_dir.glob("*.jpg"))) + len(list(image_dir.glob("*.png")))
            label_count = len(list(label_dir.glob("*.txt")))

            stats["splits"][split] = {
                "images": image_count,
                "labels": label_count
            }

            stats["total_images"] += image_count

        logger.info(f"Dataset stats: {stats}")
        return stats

    def create_yaml_config(self, class_names: List[str]) -> Path:
        """
        Create dataset.yaml for YOLO training

        Args:
            class_names: List of class names

        Returns:
            Path to created yaml file
        """
        yaml_content = f"""# Manufacturing Quality Oracle Dataset
path: {self.dataset_root}
train: images/train
val: images/valid
test: images/test

# Number of classes
nc: {len(class_names)}

# Class names
names: {class_names}
"""

        yaml_path = self.dataset_root / "dataset.yaml"
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)

        logger.info(f"Created dataset.yaml at {yaml_path}")
        return yaml_path

    def split_dataset(
        self,
        train_ratio: float = 0.7,
        valid_ratio: float = 0.2,
        test_ratio: float = 0.1
    ):
        """
        Split dataset into train/valid/test

        Args:
            train_ratio: Training set ratio
            valid_ratio: Validation set ratio
            test_ratio: Test set ratio
        """
        assert abs(train_ratio + valid_ratio + test_ratio - 1.0) < 0.01, \
            "Ratios must sum to 1.0"

        # Get all images from train directory (assuming unsplit initially)
        all_images = list((self.images_dir / "train").glob("*.jpg"))
        all_images.extend(list((self.images_dir / "train").glob("*.png")))

        # Shuffle
        np.random.shuffle(all_images)

        # Calculate split indices
        n = len(all_images)
        train_end = int(n * train_ratio)
        valid_end = train_end + int(n * valid_ratio)

        # Split
        train_images = all_images[:train_end]
        valid_images = all_images[train_end:valid_end]
        test_images = all_images[valid_end:]

        # Move files
        self._move_files(valid_images, "train", "valid")
        self._move_files(test_images, "train", "test")

        logger.info(
            f"Dataset split: train={len(train_images)}, "
            f"valid={len(valid_images)}, test={len(test_images)}"
        )

    def _move_files(self, files: List[Path], from_split: str, to_split: str):
        """Move files between splits"""
        for image_path in files:
            # Move image
            dest_image = self.images_dir / to_split / image_path.name
            shutil.move(str(image_path), str(dest_image))

            # Move label
            label_name = image_path.stem + ".txt"
            label_path = self.labels_dir / from_split / label_name
            if label_path.exists():
                dest_label = self.labels_dir / to_split / label_name
                shutil.move(str(label_path), str(dest_label))

    def archive_old_data(self, days: int = 90):
        """
        Archive data older than specified days

        Args:
            days: Number of days
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        archived_count = 0

        for split in ["train", "valid", "test"]:
            image_dir = self.images_dir / split

            for image_path in image_dir.iterdir():
                if image_path.stat().st_mtime < cutoff_time:
                    # Create archive subdirectory
                    archive_split = self.archive_dir / split
                    archive_split.mkdir(parents=True, exist_ok=True)

                    # Move image
                    shutil.move(str(image_path), str(archive_split / image_path.name))

                    # Move label
                    label_path = self.labels_dir / split / f"{image_path.stem}.txt"
                    if label_path.exists():
                        shutil.move(str(label_path), str(archive_split / label_path.name))

                    archived_count += 1

        logger.info(f"Archived {archived_count} samples older than {days} days")

    def export_for_training(self, output_path: Path) -> Path:
        """
        Export dataset in format ready for training

        Args:
            output_path: Output directory path

        Returns:
            Path to exported dataset
        """
        output_path.mkdir(parents=True, exist_ok=True)

        # Copy dataset structure
        shutil.copytree(self.images_dir, output_path / "images", dirs_exist_ok=True)
        shutil.copytree(self.labels_dir, output_path / "labels", dirs_exist_ok=True)

        # Copy yaml config if exists
        yaml_path = self.dataset_root / "dataset.yaml"
        if yaml_path.exists():
            shutil.copy(yaml_path, output_path / "dataset.yaml")

        logger.info(f"Exported dataset to {output_path}")
        return output_path
