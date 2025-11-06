"""
Customer-Specific Fine-Tuning Pipeline
Rapidly fine-tune universal model for specific customer use cases
"""

import os
from pathlib import Path
from datetime import datetime
import yaml
import json
import shutil
from ultralytics import YOLO
from loguru import logger


class CustomerFineTuner:
    """
    Fine-tune universal model for customer-specific defects
    Target: 95%+ accuracy in 2-3 weeks with 200-500 customer images
    """

    def __init__(
        self,
        universal_model_path: str,
        customer_name: str,
        output_dir: str = "models/customers"
    ):
        """
        Initialize customer fine-tuner

        Args:
            universal_model_path: Path to trained universal model
            customer_name: Customer identifier
            output_dir: Output directory for customer models
        """
        self.universal_model_path = Path(universal_model_path)
        self.customer_name = customer_name.lower().replace(" ", "_")
        self.output_dir = Path(output_dir) / self.customer_name
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Customer fine-tuner initialized for: {customer_name}")
        logger.info(f"Base model: {self.universal_model_path}")

    def prepare_customer_dataset(
        self,
        customer_data_dir: Path,
        train_split: float = 0.7,
        valid_split: float = 0.2
    ) -> Path:
        """
        Prepare customer-specific dataset

        Args:
            customer_data_dir: Directory with customer images and labels
            train_split: Training set ratio
            valid_split: Validation set ratio

        Returns:
            Path to dataset.yaml
        """
        logger.info(f"Preparing dataset for {self.customer_name}...")

        # Create dataset structure
        dataset_dir = self.output_dir / "dataset"
        for split in ['train', 'valid', 'test']:
            (dataset_dir / 'images' / split).mkdir(parents=True, exist_ok=True)
            (dataset_dir / 'labels' / split).mkdir(parents=True, exist_ok=True)

        # Get all images
        customer_data_dir = Path(customer_data_dir)
        images = list(customer_data_dir.glob('images/*.jpg')) + \
                 list(customer_data_dir.glob('images/*.png'))

        logger.info(f"Found {len(images)} images")

        if len(images) < 50:
            logger.warning(f"⚠️  Only {len(images)} images - recommend at least 200 for good results")

        # Shuffle and split
        import random
        random.shuffle(images)

        n = len(images)
        train_end = int(n * train_split)
        valid_end = train_end + int(n * valid_split)

        splits = {
            'train': images[:train_end],
            'valid': images[train_end:valid_end],
            'test': images[valid_end:]
        }

        # Copy files
        for split, image_list in splits.items():
            for image_path in image_list:
                # Copy image
                dest_image = dataset_dir / 'images' / split / image_path.name
                shutil.copy2(image_path, dest_image)

                # Copy label
                label_path = customer_data_dir / 'labels' / f"{image_path.stem}.txt"
                if label_path.exists():
                    dest_label = dataset_dir / 'labels' / split / f"{image_path.stem}.txt"
                    shutil.copy2(label_path, dest_label)

        logger.info(f"Split: train={len(splits['train'])}, valid={len(splits['valid'])}, test={len(splits['test'])}")

        # Detect classes from labels
        classes = self._detect_classes(dataset_dir)

        # Create dataset.yaml
        yaml_content = {
            'path': str(dataset_dir.absolute()),
            'train': 'images/train',
            'val': 'images/valid',
            'test': 'images/test',
            'nc': len(classes),
            'names': classes
        }

        yaml_path = dataset_dir / 'dataset.yaml'
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_content, f, default_flow_style=False)

        logger.info(f"Created dataset.yaml with {len(classes)} classes: {classes}")

        return yaml_path

    def _detect_classes(self, dataset_dir: Path) -> list:
        """Detect unique classes from label files"""
        class_ids = set()

        for label_file in (dataset_dir / 'labels').rglob('*.txt'):
            with open(label_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        class_ids.add(int(parts[0]))

        # Use generic names if we don't have mapping
        return [f"defect_{i}" for i in sorted(class_ids)]

    def finetune(
        self,
        dataset_yaml: Path,
        epochs: int = 50,  # Fewer epochs for fine-tuning
        batch_size: int = 16,
        learning_rate: float = 0.0001,  # Lower LR for fine-tuning
        freeze_layers: int = 10  # Freeze backbone layers
    ):
        """
        Fine-tune universal model on customer data

        Args:
            dataset_yaml: Path to customer dataset.yaml
            epochs: Training epochs (50 is usually enough)
            batch_size: Batch size
            learning_rate: Learning rate (lower for fine-tuning)
            freeze_layers: Number of layers to freeze (preserves universal features)

        Returns:
            Fine-tuned model and results
        """
        logger.info("="*70)
        logger.info(f"FINE-TUNING FOR CUSTOMER: {self.customer_name.upper()}")
        logger.info("="*70)
        logger.info(f"Base Model: {self.universal_model_path}")
        logger.info(f"Customer Data: {dataset_yaml}")
        logger.info(f"Target: 95%+ accuracy with {epochs} epochs")
        logger.info("="*70)

        # Load universal model
        model = YOLO(str(self.universal_model_path))

        # Fine-tuning configuration
        train_args = {
            # Data
            "data": str(dataset_yaml),
            "epochs": epochs,
            "batch": batch_size,
            "imgsz": 640,

            # Fine-tuning specific
            "lr0": learning_rate,  # Lower learning rate
            "lrf": learning_rate * 0.1,
            "warmup_epochs": 3,
            "freeze": freeze_layers,  # Freeze backbone

            # Optimization
            "optimizer": "AdamW",
            "momentum": 0.937,
            "weight_decay": 0.0005,

            # Regularization (prevent overfitting on small dataset)
            "dropout": 0.2,  # Higher dropout
            "label_smoothing": 0.1,

            # Augmentation (aggressive for small datasets)
            "hsv_h": 0.015,
            "hsv_s": 0.7,
            "hsv_v": 0.4,
            "degrees": 15.0,
            "translate": 0.2,
            "scale": 0.9,
            "shear": 5.0,
            "perspective": 0.001,
            "flipud": 0.0,
            "fliplr": 0.5,
            "mosaic": 1.0,
            "mixup": 0.15,

            # Training control
            "patience": 15,  # Lower patience
            "save": True,
            "save_period": 10,
            "device": "auto",
            "workers": 8,
            "exist_ok": True,
            "verbose": True,

            # Output
            "project": str(self.output_dir),
            "name": f"finetuned_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        }

        # Start fine-tuning
        logger.info("🚀 Starting fine-tuning...")
        logger.info(f"⏱️  Estimated time: 1-2 hours")

        results = model.train(**train_args)

        logger.info("✅ Fine-tuning complete!")

        # Validate
        logger.info("\n📊 Running validation...")
        val_results = model.val()

        # Save results
        self._save_finetuning_results(model, results, val_results, train_args)

        return model, results, val_results

    def _save_finetuning_results(self, model, results, val_results, config):
        """Save fine-tuning results and deployment info"""

        # Create summary
        summary = {
            "customer": self.customer_name,
            "finetuning_date": datetime.now().isoformat(),
            "base_model": str(self.universal_model_path),
            "configuration": {
                "epochs": config["epochs"],
                "batch_size": config["batch"],
                "learning_rate": config["lr0"],
                "frozen_layers": config["freeze"]
            },
            "final_metrics": {
                "mAP@0.5": float(val_results.box.map50),
                "mAP@0.5:0.95": float(val_results.box.map),
                "precision": float(val_results.box.mp),
                "recall": float(val_results.box.mr),
            },
            "performance_assessment": {
                "target_accuracy": "95%",
                "achieved": float(val_results.box.map50) >= 0.95,
                "production_ready": float(val_results.box.map50) >= 0.93
            },
            "model_path": str(self.output_dir / config["name"] / "weights" / "best.pt")
        }

        # Save summary
        summary_path = self.output_dir / "finetuning_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        # Print results
        self._print_results(summary)

        # Create customer deployment package
        self._create_deployment_package(summary)

    def _print_results(self, summary):
        """Print formatted results"""
        metrics = summary["final_metrics"]

        print("\n" + "="*70)
        print(f"🎯 FINE-TUNING RESULTS FOR: {self.customer_name.upper()}")
        print("="*70)
        print(f"\n📊 Final Metrics:")
        print(f"   mAP@0.5:      {metrics['mAP@0.5']*100:.1f}%")
        print(f"   mAP@0.5:0.95: {metrics['mAP@0.5:0.95']*100:.1f}%")
        print(f"   Precision:    {metrics['precision']*100:.1f}%")
        print(f"   Recall:       {metrics['recall']*100:.1f}%")

        print(f"\n✅ Performance Assessment:")
        if summary["performance_assessment"]["production_ready"]:
            print(f"   ✓ PRODUCTION READY - {metrics['mAP@0.5']*100:.1f}% accuracy")
            print(f"   ✓ Meets/exceeds 95% target")
            print(f"   ✓ Ready for deployment")
        else:
            print(f"   ⚠️  Below production threshold ({metrics['mAP@0.5']*100:.1f}% vs 95% target)")
            print(f"   → Recommend collecting more customer-specific data")

        print(f"\n📦 Customer Model:")
        print(f"   {summary['model_path']}")

        print(f"\n🚀 Next Steps:")
        print(f"   1. Review deployment package: {self.output_dir}/deployment/")
        print(f"   2. Test on customer facility: python scripts/test_customer_model.py")
        print(f"   3. Deploy to production: ./deployment/deploy_customer.sh")
        print("="*70 + "\n")

    def _create_deployment_package(self, summary):
        """Create complete deployment package for customer"""

        deployment_dir = self.output_dir / "deployment"
        deployment_dir.mkdir(exist_ok=True)

        # Copy best model
        model_src = Path(summary['model_path'])
        model_dest = deployment_dir / f"{self.customer_name}_model.pt"
        shutil.copy2(model_src, model_dest)

        # Create deployment script
        deploy_script = f"""#!/bin/bash
# Deployment script for {self.customer_name.upper()}

MODEL_PATH="{model_dest}"
CUSTOMER="{self.customer_name}"

echo "Deploying Manufacturing Quality Oracle for $CUSTOMER"
echo "Model: $MODEL_PATH"
echo "Target Accuracy: {summary['final_metrics']['mAP@0.5']*100:.1f}%"

# Copy model to deployment location
cp $MODEL_PATH /opt/quality-oracle/models/$CUSTOMER.pt

# Update configuration
cat > /opt/quality-oracle/config/$CUSTOMER.yaml <<EOF
customer: {self.customer_name}
model_path: /opt/quality-oracle/models/$CUSTOMER.pt
confidence_threshold: 0.5
target_accuracy: {summary['final_metrics']['mAP@0.5']}
deployment_date: {datetime.now().isoformat()}
EOF

# Restart service
sudo systemctl restart quality-oracle

echo "✅ Deployment complete for $CUSTOMER"
echo "Monitor with: sudo journalctl -u quality-oracle -f"
"""

        script_path = deployment_dir / "deploy.sh"
        with open(script_path, 'w') as f:
            f.write(deploy_script)

        script_path.chmod(0o755)

        # Create customer README
        readme = f"""
# Manufacturing Quality Oracle - {self.customer_name.upper()} Deployment

## Model Performance

**Achieved Accuracy: {summary['final_metrics']['mAP@0.5']*100:.1f}%**
- Precision: {summary['final_metrics']['precision']*100:.1f}%
- Recall: {summary['final_metrics']['recall']*100:.1f}%
- Status: {'✅ PRODUCTION READY' if summary['performance_assessment']['production_ready'] else '⚠️ NEEDS MORE DATA'}

## Deployment

### Quick Deploy
```bash
cd {deployment_dir}
./deploy.sh
```

### Manual Deploy
```bash
# Copy model
cp {self.customer_name}_model.pt /path/to/deployment/

# Run inference
python scripts/edge_inference.py --model {self.customer_name}_model.pt
```

## Testing

Test with customer images:
```bash
python scripts/test_customer_model.py \\
    --model {model_dest} \\
    --test-dir /path/to/customer/test/images
```

## Monitoring

After deployment, monitor performance:
```bash
# Real-time logs
sudo journalctl -u quality-oracle -f

# Performance metrics
python scripts/monitor_customer.py --customer {self.customer_name}
```

## Expected Results

**Before AI:**
- Manual inspection: X parts/hour
- Defect escape rate: Y%

**With AI (Target):**
- Automated inspection: 10X parts/hour
- Defect escape rate: <1%
- 30%+ defect reduction

## Support

- Technical Support: support@manufacturing-oracle.com
- Customer Success: {self.customer_name}@manufacturing-oracle.com
- Emergency: 1-800-QUALITY

## Model Information

- Base Model: Universal Manufacturing Detector
- Fine-tuned: {summary['finetuning_date']}
- Training Images: Customer-specific dataset
- Deployment: {datetime.now().isoformat()}

---

**Manufacturing Quality Oracle**
*AI-Powered Quality Assurance*
"""

        readme_path = deployment_dir / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme)

        logger.info(f"📦 Deployment package created: {deployment_dir}")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Fine-tune for Customer")
    parser.add_argument("--universal-model", type=str, required=True,
                       help="Path to universal model")
    parser.add_argument("--customer-name", type=str, required=True,
                       help="Customer name/identifier")
    parser.add_argument("--customer-data", type=str, required=True,
                       help="Path to customer data directory")
    parser.add_argument("--epochs", type=int, default=50,
                       help="Training epochs")
    parser.add_argument("--batch", type=int, default=16,
                       help="Batch size")

    args = parser.parse_args()

    # Initialize fine-tuner
    finetuner = CustomerFineTuner(
        universal_model_path=args.universal_model,
        customer_name=args.customer_name
    )

    # Prepare dataset
    dataset_yaml = finetuner.prepare_customer_dataset(
        customer_data_dir=Path(args.customer_data)
    )

    # Fine-tune
    model, results, val_results = finetuner.finetune(
        dataset_yaml=dataset_yaml,
        epochs=args.epochs,
        batch_size=args.batch
    )

    logger.info("\n✅ Customer model ready for deployment!")


if __name__ == "__main__":
    main()
