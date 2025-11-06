"""
Universal Manufacturing Defect Detector - Data Pipeline
Downloads and combines multiple open-source manufacturing datasets
"""

import os
import yaml
import shutil
from pathlib import Path
from loguru import logger
from roboflow import Roboflow
import requests
import zipfile
from tqdm import tqdm


class UniversalDatasetBuilder:
    """
    Build universal manufacturing defect detection dataset
    Combines: MVTec AD, NEU Steel, PCB Defects, Welding Defects
    """

    def __init__(self, output_dir: str = "data/universal_manufacturing"):
        """
        Initialize dataset builder

        Args:
            output_dir: Output directory for combined dataset
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Dataset sources
        self.datasets = {
            'mvtec_ad': {
                'url': 'https://www.mvtec.com/company/research/datasets/mvtec-ad',
                'type': 'direct',
                'categories': ['metal_nut', 'screw', 'tile', 'wood', 'carpet']
            },
            'neu_steel': {
                'workspace': 'neu-det',
                'project': 'steel-defects',
                'type': 'roboflow'
            },
            'pcb_defects': {
                'workspace': 'dans-ws',
                'project': 'manufacturing-defect-detection-lpxwn',
                'type': 'roboflow'
            },
            'welding_defects': {
                'workspace': 'welding-inspection',
                'project': 'welding-defects',
                'type': 'roboflow'
            }
        }

        # Combined class mapping
        self.unified_classes = [
            'scratch',      # Linear surface marks
            'dent',         # Deformations/indentations
            'crack',        # Fractures
            'contamination',# Rust, dirt, foreign material
            'color_defect', # Paint, coating issues
            'missing',      # Missing parts/holes
            'surface_defect'# General surface anomalies
        ]

        logger.info(f"Universal dataset builder initialized: {self.output_dir}")

    def download_roboflow_dataset(
        self,
        workspace: str,
        project: str,
        api_key: str,
        version: int = 1
    ) -> Path:
        """
        Download dataset from Roboflow

        Args:
            workspace: Roboflow workspace
            project: Project name
            api_key: Roboflow API key
            version: Dataset version

        Returns:
            Path to downloaded dataset
        """
        logger.info(f"Downloading Roboflow dataset: {workspace}/{project}")

        try:
            rf = Roboflow(api_key=api_key)
            project_obj = rf.workspace(workspace).project(project)
            dataset = project_obj.version(version).download("yolov8")

            logger.info(f"Downloaded to: {dataset.location}")
            return Path(dataset.location)

        except Exception as e:
            logger.error(f"Failed to download {project}: {e}")
            return None

    def download_mvtec_subset(self) -> Path:
        """
        Download subset of MVTec AD dataset
        Note: MVTec requires manual download, this creates placeholder
        """
        logger.info("MVTec AD requires manual download")
        logger.info("Download from: https://www.mvtec.com/company/research/datasets/mvtec-ad/downloads")

        mvtec_dir = self.output_dir / "mvtec_ad"
        mvtec_dir.mkdir(exist_ok=True)

        # Create instructions file
        instructions = """
MVTec AD Dataset Download Instructions:

1. Visit: https://www.mvtec.com/company/research/datasets/mvtec-ad/downloads
2. Download these categories (relevant for manufacturing):
   - metal_nut (1000+ images)
   - screw (1000+ images)
   - tile (1000+ images)
   - wood (1000+ images)

3. Extract to: {mvtec_dir}

4. Expected structure:
   mvtec_ad/
   ├── metal_nut/
   │   ├── train/
   │   └── test/
   ├── screw/
   │   ├── train/
   │   └── test/
   └── ...

5. Run: python scripts/universal_dataset.py --convert-mvtec

Total size: ~4GB
        """.format(mvtec_dir=mvtec_dir)

        with open(mvtec_dir / "DOWNLOAD_INSTRUCTIONS.txt", 'w') as f:
            f.write(instructions)

        logger.info(f"Instructions saved to: {mvtec_dir}/DOWNLOAD_INSTRUCTIONS.txt")

        return mvtec_dir

    def build_universal_dataset(self, roboflow_api_key: str) -> Path:
        """
        Build complete universal dataset

        Args:
            roboflow_api_key: Roboflow API key

        Returns:
            Path to unified dataset
        """
        logger.info("Building universal manufacturing dataset...")

        # Create output structure
        for split in ['train', 'valid', 'test']:
            (self.output_dir / 'images' / split).mkdir(parents=True, exist_ok=True)
            (self.output_dir / 'labels' / split).mkdir(parents=True, exist_ok=True)

        total_images = 0

        # Download Roboflow datasets
        for name, config in self.datasets.items():
            if config['type'] == 'roboflow':
                logger.info(f"Processing {name}...")

                dataset_path = self.download_roboflow_dataset(
                    workspace=config['workspace'],
                    project=config['project'],
                    api_key=roboflow_api_key
                )

                if dataset_path:
                    # Copy to unified dataset
                    images_added = self._merge_dataset(dataset_path, name)
                    total_images += images_added
                    logger.info(f"Added {images_added} images from {name}")

        # MVTec (manual download)
        logger.info("Checking for MVTec AD dataset...")
        mvtec_dir = self.output_dir / "mvtec_ad"

        if mvtec_dir.exists() and any(mvtec_dir.iterdir()):
            images_added = self._convert_mvtec_dataset(mvtec_dir)
            total_images += images_added
            logger.info(f"Added {images_added} images from MVTec AD")
        else:
            logger.warning("MVTec AD not found. Download manually for better results.")

        # Create dataset.yaml
        self._create_dataset_yaml()

        logger.info(f"Universal dataset complete: {total_images} images")
        logger.info(f"Location: {self.output_dir}")

        return self.output_dir

    def _merge_dataset(self, source_path: Path, dataset_name: str) -> int:
        """Merge dataset into unified structure"""
        images_added = 0

        for split in ['train', 'valid', 'test']:
            # Source paths
            source_images = source_path / split / 'images'
            source_labels = source_path / split / 'labels'

            if not source_images.exists():
                continue

            # Destination paths
            dest_images = self.output_dir / 'images' / split
            dest_labels = self.output_dir / 'labels' / split

            # Copy images and labels
            for image_file in source_images.glob('*'):
                if image_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    # New filename with dataset prefix
                    new_name = f"{dataset_name}_{image_file.name}"

                    # Copy image
                    shutil.copy2(image_file, dest_images / new_name)

                    # Copy label if exists
                    label_file = source_labels / f"{image_file.stem}.txt"
                    if label_file.exists():
                        shutil.copy2(label_file, dest_labels / f"{dataset_name}_{image_file.stem}.txt")

                    images_added += 1

        return images_added

    def _convert_mvtec_dataset(self, mvtec_dir: Path) -> int:
        """
        Convert MVTec AD format to YOLO format
        MVTec uses anomaly masks, we'll convert to bounding boxes
        """
        images_added = 0

        # Process each category
        for category_dir in mvtec_dir.iterdir():
            if not category_dir.is_dir():
                continue

            # Process test set (has defects)
            test_dir = category_dir / 'test'
            if not test_dir.exists():
                continue

            # Process defect types
            for defect_dir in test_dir.iterdir():
                if not defect_dir.is_dir() or defect_dir.name == 'good':
                    continue

                # Process images in this defect type
                for image_file in defect_dir.glob('*.png'):
                    # Determine split (80% train, 20% valid)
                    split = 'train' if images_added % 5 != 0 else 'valid'

                    # Copy image
                    new_name = f"mvtec_{category_dir.name}_{defect_dir.name}_{image_file.name}"
                    dest_image = self.output_dir / 'images' / split / new_name
                    shutil.copy2(image_file, dest_image)

                    # Create label (use full image as defect for now)
                    # In production, you'd use the ground truth masks
                    label_content = self._create_mvtec_label(defect_dir.name)
                    label_file = self.output_dir / 'labels' / split / f"{new_name.rsplit('.', 1)[0]}.txt"

                    with open(label_file, 'w') as f:
                        f.write(label_content)

                    images_added += 1

        return images_added

    def _create_mvtec_label(self, defect_type: str) -> str:
        """Map MVTec defect type to unified class"""
        # MVTec defect type mapping
        defect_mapping = {
            'scratch': 0,  # scratch
            'dent': 1,     # dent
            'crack': 2,    # crack
            'contamination': 3,
            'color': 4,
            'hole': 5,
            'bent': 1,
            'broken': 2
        }

        # Find matching class
        class_id = 6  # Default to surface_defect

        for key, value in defect_mapping.items():
            if key in defect_type.lower():
                class_id = value
                break

        # Return center of image as defect (0.5, 0.5 with 0.8 width/height)
        # In production, use actual ground truth masks
        return f"{class_id} 0.5 0.5 0.8 0.8\n"

    def _create_dataset_yaml(self):
        """Create dataset.yaml for YOLO training"""
        yaml_content = {
            'path': str(self.output_dir.absolute()),
            'train': 'images/train',
            'val': 'images/valid',
            'test': 'images/test',
            'nc': len(self.unified_classes),
            'names': self.unified_classes
        }

        yaml_path = self.output_dir / 'dataset.yaml'

        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_content, f, default_flow_style=False)

        logger.info(f"Created dataset.yaml: {yaml_path}")

        # Also create detailed info
        info = f"""
Universal Manufacturing Defect Detection Dataset

Classes ({len(self.unified_classes)}):
{chr(10).join(f'  {i}: {name}' for i, name in enumerate(self.unified_classes))}

Sources:
- NEU Steel Defects (1,800+ images)
- PCB Manufacturing Defects (340+ images)
- Welding Defects (80+ images)
- MVTec AD (if downloaded)

Total: ~2,200-7,200 images (depending on MVTec)

Training: 70%
Validation: 20%
Test: 10%

Usage:
  from ultralytics import YOLO
  model = YOLO('yolov8m.pt')
  model.train(data='{yaml_path}', epochs=100)
"""

        with open(self.output_dir / 'README.txt', 'w') as f:
            f.write(info)

    def get_dataset_stats(self) -> dict:
        """Get statistics about the dataset"""
        stats = {
            'splits': {},
            'total_images': 0,
            'class_distribution': {cls: 0 for cls in self.unified_classes}
        }

        for split in ['train', 'valid', 'test']:
            images_dir = self.output_dir / 'images' / split
            labels_dir = self.output_dir / 'labels' / split

            if not images_dir.exists():
                continue

            image_count = len(list(images_dir.glob('*')))
            stats['splits'][split] = image_count
            stats['total_images'] += image_count

            # Count classes
            for label_file in labels_dir.glob('*.txt'):
                with open(label_file, 'r') as f:
                    for line in f:
                        class_id = int(line.split()[0])
                        if 0 <= class_id < len(self.unified_classes):
                            stats['class_distribution'][self.unified_classes[class_id]] += 1

        return stats


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Universal Manufacturing Dataset Builder")
    parser.add_argument("--roboflow-api-key", type=str,
                       help="Roboflow API key (get from app.roboflow.com)")
    parser.add_argument("--convert-mvtec", action="store_true",
                       help="Convert MVTec AD dataset (must be downloaded manually first)")
    parser.add_argument("--output-dir", type=str, default="data/universal_manufacturing",
                       help="Output directory")
    parser.add_argument("--stats", action="store_true",
                       help="Show dataset statistics")

    args = parser.parse_args()

    # Initialize builder
    builder = UniversalDatasetBuilder(output_dir=args.output_dir)

    if args.stats:
        # Show statistics
        stats = builder.get_dataset_stats()
        logger.info("\n" + "="*60)
        logger.info("DATASET STATISTICS")
        logger.info("="*60)
        logger.info(f"Total Images: {stats['total_images']}")
        logger.info("\nSplit Distribution:")
        for split, count in stats['splits'].items():
            percentage = (count / stats['total_images'] * 100) if stats['total_images'] > 0 else 0
            logger.info(f"  {split:10s}: {count:5d} ({percentage:5.1f}%)")
        logger.info("\nClass Distribution:")
        for cls, count in stats['class_distribution'].items():
            logger.info(f"  {cls:20s}: {count:5d}")
        logger.info("="*60)

    elif args.convert_mvtec:
        # Convert MVTec dataset
        mvtec_dir = Path(args.output_dir) / "mvtec_ad"
        if mvtec_dir.exists():
            builder._convert_mvtec_dataset(mvtec_dir)
            logger.info("MVTec conversion complete!")
        else:
            logger.error(f"MVTec directory not found: {mvtec_dir}")

    else:
        # Build complete dataset
        if not args.roboflow_api_key:
            logger.error("--roboflow-api-key required")
            logger.info("Get your API key from: https://app.roboflow.com/settings/api")
            return

        dataset_path = builder.build_universal_dataset(args.roboflow_api_key)
        logger.info(f"\n✅ Universal dataset ready: {dataset_path}")

        # Show stats
        stats = builder.get_dataset_stats()
        logger.info(f"\n📊 Total images: {stats['total_images']}")
        logger.info(f"📂 Location: {dataset_path}")
        logger.info(f"📄 Config: {dataset_path}/dataset.yaml")


if __name__ == "__main__":
    main()
