"""
Week 3-4: YOLOv8 Model Training Script
Train custom defect detection model
"""

import os
from pathlib import Path
from datetime import datetime
import yaml
import json
from ultralytics import YOLO
from loguru import logger
import torch


class ModelTrainer:
    """YOLOv8 model trainer for defect detection"""

    def __init__(self, dataset_path: str, output_dir: str = "models/training"):
        """
        Initialize trainer

        Args:
            dataset_path: Path to dataset.yaml
            output_dir: Output directory for models
        """
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Check CUDA availability
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Training device: {self.device}")

        if self.device == "cuda":
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"CUDA Version: {torch.version.cuda}")

    def create_dataset_yaml(
        self,
        dataset_root: Path,
        classes: list,
        output_path: Path = None
    ):
        """
        Create dataset.yaml for YOLO training

        Args:
            dataset_root: Root directory of dataset
            classes: List of class names
            output_path: Path to save yaml file
        """
        if output_path is None:
            output_path = dataset_root / "dataset.yaml"

        config = {
            "path": str(dataset_root.absolute()),
            "train": "images/train",
            "val": "images/valid",
            "test": "images/test",
            "nc": len(classes),
            "names": classes
        }

        with open(output_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        logger.info(f"Created dataset.yaml: {output_path}")
        return output_path

    def train(
        self,
        model_size: str = "n",  # n, s, m, l, x
        epochs: int = 100,
        batch_size: int = 16,
        img_size: int = 640,
        patience: int = 50,
        pretrained: bool = True,
        resume: bool = False
    ):
        """
        Train YOLOv8 model

        Args:
            model_size: Model size (n=nano, s=small, m=medium, l=large, x=xlarge)
            epochs: Number of training epochs
            batch_size: Batch size
            img_size: Image size
            patience: Early stopping patience
            pretrained: Use pretrained weights
            resume: Resume from last checkpoint
        """
        logger.info("="*60)
        logger.info("STARTING MODEL TRAINING")
        logger.info("="*60)

        # Initialize model
        if resume:
            model_path = self.output_dir / "last.pt"
            if model_path.exists():
                logger.info(f"Resuming from: {model_path}")
                model = YOLO(str(model_path))
            else:
                logger.warning("No checkpoint found, starting fresh")
                model = YOLO(f"yolov8{model_size}.pt" if pretrained else f"yolov8{model_size}.yaml")
        else:
            model = YOLO(f"yolov8{model_size}.pt" if pretrained else f"yolov8{model_size}.yaml")

        logger.info(f"Model: YOLOv8{model_size}")
        logger.info(f"Pretrained: {pretrained}")
        logger.info(f"Dataset: {self.dataset_path}")
        logger.info(f"Epochs: {epochs}")
        logger.info(f"Batch size: {batch_size}")
        logger.info(f"Image size: {img_size}")

        # Training configuration
        train_args = {
            "data": str(self.dataset_path),
            "epochs": epochs,
            "batch": batch_size,
            "imgsz": img_size,
            "patience": patience,
            "save": True,
            "save_period": 10,
            "device": self.device,
            "workers": 8,
            "optimizer": "AdamW",
            "lr0": 0.001,
            "lrf": 0.01,
            "momentum": 0.937,
            "weight_decay": 0.0005,
            "warmup_epochs": 3,
            "warmup_momentum": 0.8,
            "warmup_bias_lr": 0.1,
            "augment": True,
            "hsv_h": 0.015,
            "hsv_s": 0.7,
            "hsv_v": 0.4,
            "degrees": 0.0,
            "translate": 0.1,
            "scale": 0.5,
            "shear": 0.0,
            "perspective": 0.0,
            "flipud": 0.0,
            "fliplr": 0.5,
            "mosaic": 1.0,
            "mixup": 0.0,
            "copy_paste": 0.0,
            "project": str(self.output_dir),
            "name": f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "exist_ok": True,
            "pretrained": pretrained,
            "verbose": True
        }

        # Start training
        logger.info("Starting training...")
        results = model.train(**train_args)

        logger.info("Training complete!")

        # Save training summary
        self._save_training_summary(results, train_args)

        return model, results

    def validate(self, model_path: str, conf_threshold: float = 0.5):
        """
        Validate trained model

        Args:
            model_path: Path to trained model
            conf_threshold: Confidence threshold
        """
        logger.info("="*60)
        logger.info("MODEL VALIDATION")
        logger.info("="*60)

        model = YOLO(model_path)

        # Run validation
        results = model.val(
            data=str(self.dataset_path),
            conf=conf_threshold,
            device=self.device
        )

        # Print metrics
        logger.info("\nValidation Results:")
        logger.info(f"  mAP@0.5: {results.box.map50:.4f}")
        logger.info(f"  mAP@0.5:0.95: {results.box.map:.4f}")
        logger.info(f"  Precision: {results.box.mp:.4f}")
        logger.info(f"  Recall: {results.box.mr:.4f}")

        return results

    def export_model(
        self,
        model_path: str,
        formats: list = ["onnx", "torchscript"]
    ):
        """
        Export model to different formats

        Args:
            model_path: Path to trained model
            formats: Export formats (onnx, torchscript, tflite, etc.)
        """
        logger.info("Exporting model...")

        model = YOLO(model_path)

        for fmt in formats:
            try:
                logger.info(f"Exporting to {fmt}...")
                export_path = model.export(format=fmt)
                logger.info(f"✓ Exported: {export_path}")
            except Exception as e:
                logger.error(f"✗ Failed to export {fmt}: {e}")

    def _save_training_summary(self, results, config):
        """Save training summary"""
        summary = {
            "training_date": datetime.now().isoformat(),
            "config": config,
            "results": {
                "final_map": float(results.box.map) if hasattr(results, 'box') else None,
                "final_map50": float(results.box.map50) if hasattr(results, 'box') else None,
            }
        }

        summary_path = self.output_dir / "training_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Training summary saved: {summary_path}")

    def benchmark_speed(self, model_path: str, img_size: int = 640):
        """
        Benchmark inference speed

        Args:
            model_path: Path to model
            img_size: Image size for inference
        """
        import time
        import numpy as np

        logger.info("Benchmarking inference speed...")

        model = YOLO(model_path)

        # Warmup
        dummy_input = np.random.randint(0, 255, (img_size, img_size, 3), dtype=np.uint8)
        for _ in range(10):
            model.predict(dummy_input, verbose=False)

        # Benchmark
        times = []
        for _ in range(100):
            start = time.time()
            model.predict(dummy_input, verbose=False)
            times.append((time.time() - start) * 1000)  # Convert to ms

        avg_time = np.mean(times)
        std_time = np.std(times)

        logger.info(f"\nInference Speed:")
        logger.info(f"  Average: {avg_time:.2f}ms")
        logger.info(f"  Std Dev: {std_time:.2f}ms")
        logger.info(f"  FPS: {1000/avg_time:.1f}")

        return avg_time


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Week 3-4: Model Training")
    parser.add_argument("--mode", choices=["train", "validate", "export", "benchmark"],
                       default="train", help="Operation mode")
    parser.add_argument("--dataset", type=str, required=True,
                       help="Path to dataset.yaml")
    parser.add_argument("--model-size", type=str, default="n",
                       choices=["n", "s", "m", "l", "x"],
                       help="Model size")
    parser.add_argument("--epochs", type=int, default=100,
                       help="Number of epochs")
    parser.add_argument("--batch", type=int, default=16,
                       help="Batch size")
    parser.add_argument("--img-size", type=int, default=640,
                       help="Image size")
    parser.add_argument("--model-path", type=str,
                       help="Path to trained model (for validate/export/benchmark)")
    parser.add_argument("--resume", action="store_true",
                       help="Resume from last checkpoint")

    args = parser.parse_args()

    # Initialize trainer
    trainer = ModelTrainer(
        dataset_path=args.dataset,
        output_dir="models/training"
    )

    # Execute mode
    if args.mode == "train":
        model, results = trainer.train(
            model_size=args.model_size,
            epochs=args.epochs,
            batch_size=args.batch,
            img_size=args.img_size,
            resume=args.resume
        )

        # Validate after training
        logger.info("\nRunning post-training validation...")
        trainer.validate(model_path=str(trainer.output_dir / "train" / "weights" / "best.pt"))

    elif args.mode == "validate":
        if not args.model_path:
            logger.error("--model-path required for validate mode")
            return
        trainer.validate(model_path=args.model_path)

    elif args.mode == "export":
        if not args.model_path:
            logger.error("--model-path required for export mode")
            return
        trainer.export_model(
            model_path=args.model_path,
            formats=["onnx", "torchscript"]
        )

    elif args.mode == "benchmark":
        if not args.model_path:
            logger.error("--model-path required for benchmark mode")
            return
        trainer.benchmark_speed(model_path=args.model_path, img_size=args.img_size)


if __name__ == "__main__":
    main()
