"""
Week 1: Data Collection Script
Automated image capture for metal surface defect dataset
"""

import cv2
import os
from pathlib import Path
from datetime import datetime
import json
from loguru import logger

class DataCollectionTool:
    """Tool for systematic data collection"""

    def __init__(self, output_dir: str = "data/raw_images"):
        """
        Initialize data collection tool

        Args:
            output_dir: Directory to save collected images
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for each defect type
        self.defect_types = ["scratch", "dent", "crack", "rust", "paint_defect", "good"]
        for defect_type in self.defect_types:
            (self.output_dir / defect_type).mkdir(exist_ok=True)

        # Metadata tracking
        self.metadata = []
        self.image_count = {dt: 0 for dt in self.defect_types}

        logger.info(f"Data collection tool initialized: {self.output_dir}")

    def capture_session(self, camera_id: int = 0, defect_type: str = "scratch"):
        """
        Start interactive capture session

        Args:
            camera_id: Camera device ID
            defect_type: Type of defect being captured
        """
        if defect_type not in self.defect_types:
            logger.error(f"Unknown defect type: {defect_type}")
            return

        # Open camera
        cap = cv2.VideoCapture(camera_id)

        if not cap.isOpened():
            logger.error(f"Failed to open camera {camera_id}")
            return

        # Set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

        logger.info(f"Starting capture session for: {defect_type}")
        logger.info("Controls:")
        logger.info("  SPACE - Capture image")
        logger.info("  S - Change severity (low/medium/high)")
        logger.info("  Q - Quit session")

        severity = "medium"
        captured_count = 0

        while True:
            ret, frame = cap.read()

            if not ret:
                logger.error("Failed to read frame")
                break

            # Display frame with info
            display_frame = frame.copy()
            cv2.putText(
                display_frame,
                f"Type: {defect_type} | Severity: {severity} | Count: {captured_count}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
            cv2.putText(
                display_frame,
                "SPACE=Capture | S=Severity | Q=Quit",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.imshow("Data Collection", display_frame)

            key = cv2.waitKey(1) & 0xFF

            # Capture image
            if key == ord(' '):
                self._save_image(frame, defect_type, severity)
                captured_count += 1
                logger.info(f"Captured image #{captured_count}")

            # Change severity
            elif key == ord('s'):
                severities = ["low", "medium", "high"]
                current_idx = severities.index(severity)
                severity = severities[(current_idx + 1) % 3]
                logger.info(f"Severity changed to: {severity}")

            # Quit
            elif key == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        logger.info(f"Capture session complete: {captured_count} images")

    def _save_image(self, image, defect_type: str, severity: str):
        """Save captured image with metadata"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{defect_type}_{severity}_{timestamp}.jpg"

        # Save image
        filepath = self.output_dir / defect_type / filename
        cv2.imwrite(str(filepath), image)

        # Save metadata
        metadata_entry = {
            "filename": filename,
            "filepath": str(filepath),
            "defect_type": defect_type,
            "severity": severity,
            "timestamp": datetime.now().isoformat(),
            "resolution": f"{image.shape[1]}x{image.shape[0]}"
        }
        self.metadata.append(metadata_entry)
        self.image_count[defect_type] += 1

    def batch_import(self, source_dir: Path, defect_type: str):
        """
        Import existing images from directory

        Args:
            source_dir: Directory containing images
            defect_type: Defect type for these images
        """
        source_path = Path(source_dir)

        if not source_path.exists():
            logger.error(f"Source directory not found: {source_dir}")
            return

        # Supported formats
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}

        imported = 0
        for image_file in source_path.iterdir():
            if image_file.suffix.lower() in image_extensions:
                # Read image
                img = cv2.imread(str(image_file))

                if img is not None:
                    # Save with new naming
                    self._save_image(img, defect_type, "medium")
                    imported += 1

        logger.info(f"Imported {imported} images from {source_dir}")

    def generate_report(self):
        """Generate data collection report"""
        report = {
            "collection_date": datetime.now().isoformat(),
            "total_images": sum(self.image_count.values()),
            "by_defect_type": self.image_count,
            "images": self.metadata
        }

        # Save report
        report_path = self.output_dir / "collection_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("DATA COLLECTION REPORT")
        logger.info("="*60)
        logger.info(f"Total Images: {report['total_images']}")
        logger.info("\nBy Defect Type:")
        for defect_type, count in self.image_count.items():
            percentage = (count / report['total_images'] * 100) if report['total_images'] > 0 else 0
            logger.info(f"  {defect_type:15s}: {count:4d} ({percentage:5.1f}%)")
        logger.info("="*60)
        logger.info(f"Report saved to: {report_path}")

        return report

    def check_quality(self):
        """Check quality of collected images"""
        logger.info("Checking image quality...")

        issues = []

        for defect_type in self.defect_types:
            type_dir = self.output_dir / defect_type

            for image_path in type_dir.glob("*.jpg"):
                img = cv2.imread(str(image_path))

                if img is None:
                    issues.append(f"Cannot read: {image_path}")
                    continue

                # Check resolution
                if img.shape[0] < 720 or img.shape[1] < 1280:
                    issues.append(f"Low resolution: {image_path}")

                # Check if too dark
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                mean_brightness = gray.mean()

                if mean_brightness < 30:
                    issues.append(f"Too dark: {image_path}")
                elif mean_brightness > 225:
                    issues.append(f"Too bright: {image_path}")

                # Check if blurry (using Laplacian variance)
                laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                if laplacian_var < 100:
                    issues.append(f"Blurry: {image_path}")

        if issues:
            logger.warning(f"Found {len(issues)} quality issues:")
            for issue in issues[:10]:  # Show first 10
                logger.warning(f"  - {issue}")
        else:
            logger.info("✓ All images passed quality check")

        return issues


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Week 1: Data Collection Tool")
    parser.add_argument("--mode", choices=["capture", "import", "report", "check"],
                       default="capture", help="Operation mode")
    parser.add_argument("--camera", type=int, default=0, help="Camera ID")
    parser.add_argument("--defect-type", type=str, default="scratch",
                       choices=["scratch", "dent", "crack", "rust", "paint_defect", "good"],
                       help="Defect type")
    parser.add_argument("--source-dir", type=str, help="Source directory for import")
    parser.add_argument("--output-dir", type=str, default="data/raw_images",
                       help="Output directory")

    args = parser.parse_args()

    # Initialize tool
    tool = DataCollectionTool(output_dir=args.output_dir)

    # Execute mode
    if args.mode == "capture":
        tool.capture_session(camera_id=args.camera, defect_type=args.defect_type)

    elif args.mode == "import":
        if not args.source_dir:
            logger.error("--source-dir required for import mode")
            return
        tool.batch_import(args.source_dir, args.defect_type)

    elif args.mode == "report":
        tool.generate_report()

    elif args.mode == "check":
        tool.check_quality()

    # Always generate final report
    tool.generate_report()


if __name__ == "__main__":
    main()
