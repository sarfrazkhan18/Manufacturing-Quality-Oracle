"""
Image preprocessing and enhancement for defect detection
"""

from typing import Tuple, Optional
import numpy as np
import cv2
from loguru import logger


class ImageProcessor:
    """
    Image preprocessing and enhancement utilities
    """

    @staticmethod
    def normalize_lighting(image: np.ndarray, method: str = "clahe") -> np.ndarray:
        """
        Normalize lighting conditions in image

        Args:
            image: Input image (BGR format)
            method: Normalization method ('clahe', 'histogram', 'gamma')

        Returns:
            Normalized image
        """
        if method == "clahe":
            # CLAHE (Contrast Limited Adaptive Histogram Equalization)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)

            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)

            lab = cv2.merge([l, a, b])
            normalized = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        elif method == "histogram":
            # Histogram equalization
            ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
            y, cr, cb = cv2.split(ycrcb)

            y = cv2.equalizeHist(y)

            ycrcb = cv2.merge([y, cr, cb])
            normalized = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)

        elif method == "gamma":
            # Gamma correction
            gamma = ImageProcessor._estimate_gamma(image)
            normalized = ImageProcessor.adjust_gamma(image, gamma)

        else:
            logger.warning(f"Unknown normalization method: {method}")
            normalized = image

        return normalized

    @staticmethod
    def _estimate_gamma(image: np.ndarray) -> float:
        """Estimate optimal gamma value for image"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray) / 255.0

        # Target brightness is 0.5
        if mean_brightness < 0.1:
            return 0.5
        elif mean_brightness > 0.9:
            return 2.0
        else:
            return 1.0 / np.log(0.5) * np.log(mean_brightness)

    @staticmethod
    def adjust_gamma(image: np.ndarray, gamma: float = 1.0) -> np.ndarray:
        """
        Adjust image gamma

        Args:
            image: Input image
            gamma: Gamma value (>1 brightens, <1 darkens)

        Returns:
            Gamma-corrected image
        """
        inv_gamma = 1.0 / gamma
        table = np.array([
            ((i / 255.0) ** inv_gamma) * 255
            for i in range(256)
        ]).astype("uint8")

        return cv2.LUT(image, table)

    @staticmethod
    def reduce_noise(
        image: np.ndarray,
        method: str = "bilateral",
        strength: int = 5
    ) -> np.ndarray:
        """
        Reduce image noise while preserving edges

        Args:
            image: Input image
            method: Denoising method ('bilateral', 'gaussian', 'median', 'nlm')
            strength: Denoising strength (1-10)

        Returns:
            Denoised image
        """
        if method == "bilateral":
            return cv2.bilateralFilter(image, d=9, sigmaColor=strength*15, sigmaSpace=strength*15)

        elif method == "gaussian":
            kernel_size = strength * 2 + 1
            return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)

        elif method == "median":
            kernel_size = strength * 2 + 1
            return cv2.medianBlur(image, kernel_size)

        elif method == "nlm":
            # Non-local means denoising
            return cv2.fastNlMeansDenoisingColored(
                image,
                None,
                h=strength*2,
                hColor=strength*2,
                templateWindowSize=7,
                searchWindowSize=21
            )

        else:
            logger.warning(f"Unknown denoising method: {method}")
            return image

    @staticmethod
    def enhance_edges(image: np.ndarray, strength: float = 1.0) -> np.ndarray:
        """
        Enhance edges in image for better defect detection

        Args:
            image: Input image
            strength: Enhancement strength (0-2)

        Returns:
            Edge-enhanced image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply Laplacian filter
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian = np.uint8(np.abs(laplacian))

        # Blend with original
        enhanced = cv2.addWeighted(
            image,
            1.0,
            cv2.cvtColor(laplacian, cv2.COLOR_GRAY2BGR),
            strength,
            0
        )

        return enhanced

    @staticmethod
    def correct_perspective(
        image: np.ndarray,
        src_points: np.ndarray,
        dst_size: Tuple[int, int]
    ) -> np.ndarray:
        """
        Correct perspective distortion

        Args:
            image: Input image
            src_points: Source quadrilateral points (4x2 array)
            dst_size: Destination size (width, height)

        Returns:
            Perspective-corrected image
        """
        dst_points = np.array([
            [0, 0],
            [dst_size[0] - 1, 0],
            [dst_size[0] - 1, dst_size[1] - 1],
            [0, dst_size[1] - 1]
        ], dtype=np.float32)

        matrix = cv2.getPerspectiveTransform(src_points.astype(np.float32), dst_points)
        corrected = cv2.warpPerspective(image, matrix, dst_size)

        return corrected

    @staticmethod
    def segment_foreground(
        image: np.ndarray,
        method: str = "grabcut"
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Segment foreground (part) from background

        Args:
            image: Input image
            method: Segmentation method ('grabcut', 'threshold')

        Returns:
            Tuple of (mask, segmented_image)
        """
        if method == "grabcut":
            # Initialize mask
            mask = np.zeros(image.shape[:2], np.uint8)

            # Define rectangle around assumed foreground
            height, width = image.shape[:2]
            rect = (10, 10, width - 20, height - 20)

            # GrabCut parameters
            bgd_model = np.zeros((1, 65), np.float64)
            fgd_model = np.zeros((1, 65), np.float64)

            # Apply GrabCut
            cv2.grabCut(
                image,
                mask,
                rect,
                bgd_model,
                fgd_model,
                5,
                cv2.GC_INIT_WITH_RECT
            )

            # Create binary mask
            mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')

            # Apply mask
            segmented = image * mask2[:, :, np.newaxis]

            return mask2, segmented

        elif method == "threshold":
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Otsu's thresholding
            _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Apply mask
            segmented = cv2.bitwise_and(image, image, mask=mask)

            return mask, segmented

        else:
            logger.warning(f"Unknown segmentation method: {method}")
            return np.ones(image.shape[:2], np.uint8), image

    @staticmethod
    def preprocess_for_detection(
        image: np.ndarray,
        normalize_lighting: bool = True,
        reduce_noise: bool = True,
        enhance_edges: bool = False
    ) -> np.ndarray:
        """
        Complete preprocessing pipeline for defect detection

        Args:
            image: Input image
            normalize_lighting: Whether to normalize lighting
            reduce_noise: Whether to reduce noise
            enhance_edges: Whether to enhance edges

        Returns:
            Preprocessed image
        """
        processed = image.copy()

        if normalize_lighting:
            processed = ImageProcessor.normalize_lighting(processed, method="clahe")

        if reduce_noise:
            processed = ImageProcessor.reduce_noise(processed, method="bilateral", strength=3)

        if enhance_edges:
            processed = ImageProcessor.enhance_edges(processed, strength=0.5)

        logger.debug("Image preprocessing completed")

        return processed

    @staticmethod
    def resize_for_model(
        image: np.ndarray,
        target_size: Tuple[int, int] = (640, 640),
        keep_aspect_ratio: bool = True
    ) -> Tuple[np.ndarray, Tuple[float, float]]:
        """
        Resize image for model input

        Args:
            image: Input image
            target_size: Target size (width, height)
            keep_aspect_ratio: Whether to maintain aspect ratio

        Returns:
            Tuple of (resized_image, (scale_x, scale_y))
        """
        h, w = image.shape[:2]
        target_w, target_h = target_size

        if keep_aspect_ratio:
            # Calculate scale
            scale = min(target_w / w, target_h / h)
            new_w, new_h = int(w * scale), int(h * scale)

            # Resize
            resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

            # Create padded image
            padded = np.zeros((target_h, target_w, 3), dtype=np.uint8)
            x_offset = (target_w - new_w) // 2
            y_offset = (target_h - new_h) // 2
            padded[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

            return padded, (scale, scale)

        else:
            # Direct resize
            resized = cv2.resize(image, target_size, interpolation=cv2.INTER_LINEAR)
            scale_x = target_w / w
            scale_y = target_h / h

            return resized, (scale_x, scale_y)

    @staticmethod
    def create_thumbnail(image: np.ndarray, max_size: int = 256) -> np.ndarray:
        """
        Create thumbnail of image

        Args:
            image: Input image
            max_size: Maximum dimension size

        Returns:
            Thumbnail image
        """
        h, w = image.shape[:2]
        scale = min(max_size / w, max_size / h)

        new_w, new_h = int(w * scale), int(h * scale)
        thumbnail = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

        return thumbnail
