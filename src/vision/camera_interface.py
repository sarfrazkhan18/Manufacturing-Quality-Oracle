"""
Industrial Camera Interface for high-resolution capture
"""

import time
from typing import Optional, List, Tuple
import threading
from queue import Queue
import numpy as np
import cv2
from loguru import logger

from ..config import settings


class CameraInterface:
    """
    Interface for industrial cameras with buffering and preprocessing
    """

    def __init__(
        self,
        camera_id: int = 0,
        resolution: Optional[Tuple[int, int]] = None,
        fps: Optional[int] = None,
        buffer_size: Optional[int] = None
    ):
        """
        Initialize camera interface

        Args:
            camera_id: Camera device ID
            resolution: (width, height) tuple
            fps: Frames per second
            buffer_size: Frame buffer size
        """
        self.camera_id = camera_id
        self.resolution = resolution or (
            settings.camera.resolution_width,
            settings.camera.resolution_height
        )
        self.fps = fps or settings.camera.fps
        self.buffer_size = buffer_size or settings.camera.buffer_size

        # Camera capture object
        self.cap: Optional[cv2.VideoCapture] = None

        # Frame buffer
        self.frame_buffer = Queue(maxsize=self.buffer_size)

        # Thread control
        self.capture_thread: Optional[threading.Thread] = None
        self.is_running = False

        # Statistics
        self.frames_captured = 0
        self.frames_dropped = 0

        logger.info(
            f"Camera interface initialized: ID={camera_id}, "
            f"Resolution={self.resolution}, FPS={self.fps}"
        )

    def start(self) -> bool:
        """
        Start camera capture

        Returns:
            True if started successfully
        """
        try:
            # Open camera
            self.cap = cv2.VideoCapture(self.camera_id)

            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.camera_id}")
                return False

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

            # Set buffer size
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Verify settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))

            logger.info(
                f"Camera settings: {actual_width}x{actual_height} @ {actual_fps}fps"
            )

            # Start capture thread
            self.is_running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()

            logger.info(f"Camera {self.camera_id} started successfully")
            return True

        except Exception as e:
            logger.error(f"Error starting camera: {e}")
            return False

    def stop(self):
        """Stop camera capture"""
        self.is_running = False

        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)

        if self.cap:
            self.cap.release()

        logger.info(f"Camera {self.camera_id} stopped")

    def _capture_loop(self):
        """Internal capture loop running in separate thread"""
        logger.info("Capture thread started")

        while self.is_running:
            ret, frame = self.cap.read()

            if not ret:
                logger.warning("Failed to read frame from camera")
                time.sleep(0.1)
                continue

            # Add frame to buffer
            try:
                if self.frame_buffer.full():
                    # Remove oldest frame
                    self.frame_buffer.get_nowait()
                    self.frames_dropped += 1

                self.frame_buffer.put_nowait(frame)
                self.frames_captured += 1

            except Exception as e:
                logger.error(f"Error adding frame to buffer: {e}")

        logger.info("Capture thread stopped")

    def get_frame(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Get latest frame from buffer

        Args:
            timeout: Timeout in seconds

        Returns:
            Frame as numpy array or None
        """
        try:
            frame = self.frame_buffer.get(timeout=timeout)
            return frame
        except:
            return None

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        Get the most recent frame, clearing buffer

        Returns:
            Latest frame or None
        """
        latest_frame = None

        # Drain buffer to get latest
        while not self.frame_buffer.empty():
            try:
                latest_frame = self.frame_buffer.get_nowait()
            except:
                break

        return latest_frame

    def is_active(self) -> bool:
        """Check if camera is active"""
        return self.is_running and self.cap is not None and self.cap.isOpened()

    def get_stats(self) -> dict:
        """Get camera statistics"""
        return {
            "camera_id": self.camera_id,
            "is_active": self.is_active(),
            "frames_captured": self.frames_captured,
            "frames_dropped": self.frames_dropped,
            "buffer_size": self.frame_buffer.qsize(),
            "resolution": self.resolution,
            "fps": self.fps
        }


class MultiCameraManager:
    """
    Manager for multiple industrial cameras
    """

    def __init__(self, camera_ids: Optional[List[int]] = None):
        """
        Initialize multi-camera manager

        Args:
            camera_ids: List of camera IDs to manage
        """
        self.camera_ids = camera_ids or settings.camera.camera_ids
        self.cameras: dict[int, CameraInterface] = {}

        logger.info(f"Multi-camera manager initialized with cameras: {self.camera_ids}")

    def start_all(self) -> dict[int, bool]:
        """
        Start all cameras

        Returns:
            Dictionary mapping camera ID to success status
        """
        results = {}

        for camera_id in self.camera_ids:
            camera = CameraInterface(camera_id=camera_id)
            success = camera.start()
            results[camera_id] = success

            if success:
                self.cameras[camera_id] = camera
            else:
                logger.error(f"Failed to start camera {camera_id}")

        logger.info(
            f"Started {len(self.cameras)}/{len(self.camera_ids)} cameras successfully"
        )

        return results

    def stop_all(self):
        """Stop all cameras"""
        for camera_id, camera in self.cameras.items():
            camera.stop()
            logger.info(f"Stopped camera {camera_id}")

        self.cameras.clear()

    def get_frame(self, camera_id: int) -> Optional[np.ndarray]:
        """Get frame from specific camera"""
        camera = self.cameras.get(camera_id)
        if camera:
            return camera.get_frame()
        return None

    def get_all_frames(self) -> dict[int, np.ndarray]:
        """
        Get frames from all active cameras

        Returns:
            Dictionary mapping camera ID to frame
        """
        frames = {}

        for camera_id, camera in self.cameras.items():
            frame = camera.get_latest_frame()
            if frame is not None:
                frames[camera_id] = frame

        return frames

    def get_stats(self) -> dict[int, dict]:
        """Get statistics for all cameras"""
        return {
            camera_id: camera.get_stats()
            for camera_id, camera in self.cameras.items()
        }
