import cv2
import numpy as np
import time
from collections import deque
from detector import ClothDetector

class TryOnServer:

    def __init__(
        self,
        # cloth_path: str,
        # camera_id: int = 0,
        # target_fps: int = 30,
        # display_width: int = 1280,
        # display_height: int = 720,
        device: str
    ):

        # self.cloth_path = cloth_path
        # self.camera_id = camera_id
        # self.target_fps = target_fps
        # self.display_width = display_width
        # self.display_height = display_height
        
        # Initialize detector
        # print(f"Initializing ClothDetector on {device}...")
        self.detector = ClothDetector(device=device, debug=True)
        # print("ClothDetector initialized successfully!")
        
        # # Load cloth image
        # print(f"Loading cloth image from: {cloth_path}")
        # self.cloth_image = cv2.imread(cloth_path)
        # if self.cloth_image is None:
        #     raise ValueError(f"Could not load cloth image: {cloth_path}")
        
        # print(f"Loaded garment: {self.cloth_image.shape}")
        
        # # Pre-detect cloth keypoints
        # print("Detecting cloth keypoints...")
        # self.cloth_keypoints, self.cloth_mask = self.detector.detect_cloth_keypoints(
        #     self.cloth_image
        # )
        # print("Cloth keypoints detected!")
        
        # Performance tracking
        self.fps_history = deque(maxlen=30)
        self.frame_times = deque(maxlen=100)
        
        # UI state
        self.show_original = False
        self.show_keypoints = False
        self.paused = False
        
        # Camera
        self.cap = None
        
    # def _init_camera(self) -> bool:
    #     """Initialize camera capture."""
    #     self.cap = cv2.VideoCapture(self.camera_id)
        
    #     if not self.cap.isOpened():
    #         print(f"Error: Could not open camera {self.camera_id}")
    #         return False
        
    #     # Set camera properties
    #     self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    #     self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    #     self.cap.set(cv2.CAP_PROP_FPS, 30)
        
    #     # Get actual camera properties
    #     actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    #     actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    #     actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        
    #     print(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")
    #     return True
    
    def _draw_ui(
        self,
        frame: np.ndarray,
        # fps: float,
        # processing_time: float
    ) -> np.ndarray:
        """Draw UI overlay on frame."""
        overlay = frame.copy()
        
        # Semi-transparent panel
        panel_height = 120
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], panel_height), 
                     (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Status text
        y_offset = 30
        line_height = 25
        
        # texts = [
        #     f"FPS: {fps:.1f}",
        #     f"Processing: {processing_time*1000:.1f}ms",
        #     f"Mode: {'ORIGINAL' if self.show_original else 'TRY-ON'}" + 
        #     (" | PAUSED" if self.paused else "")
        # ]
        
        # for i, text in enumerate(texts):
        #     cv2.putText(frame, text, (10, y_offset + i * line_height),
        #                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # # Controls
        # controls_y = frame.shape[0] - 100
        # control_texts = [
        #     "SPACE: Original/Try-on",
        #     "K: Show keypoints",
        #     "P: Pause",
        #     "S: Screenshot",
        #     "Q: Quit"
        # ]
        
        # for i, text in enumerate(control_texts):
        #     cv2.putText(frame, text, (10, controls_y + i * 20),
        #                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def _process_frame(self, frame: np.ndarray, cloth_image):
        """Process a single frame."""
        start_time = time.time()
        
        if self.show_original:
            result = frame
            detected_mask = None
            landmarks = None
        else:
            # Detect person's cloth mask and pose
            detected_mask, landmarks = self.detector.detect_cloth_mask(frame)
            
            # Apply cloth overlay
            result = self.detector.apply_cloth_overlay(
                frame,
                cloth_image,
                detected_mask,
                landmarks
            )
            
            # Optionally show keypoints
            if self.show_keypoints and landmarks is not None:
                result = self.detector.visualize_human_keypoints(
                    result,
                    landmarks,
                    self.cloth_keypoints
                )
        
        processing_time = time.time() - start_time
        return result, processing_time
    
    # def change_garment(self, new_cloth_path: str) -> bool:
    #     """Change the garment being tried on."""
    #     new_cloth = cv2.imread(new_cloth_path)
    #     if new_cloth is None:
    #         print(f"Could not load new garment: {new_cloth_path}")
    #         return False
        
    #     self.cloth_image = new_cloth
    #     self.cloth_keypoints, self.cloth_mask = self.detector.detect_cloth_keypoints(
    #         new_cloth
    #     )
    #     self.cloth_path = new_cloth_path
        
    #     print(f"Changed garment to: {new_cloth_path}")
    #     return True
    
    def run(self, frame, cloth):
        """Run the real-time try-on loop."""
        import time as time_module
        print(f"\n[{time_module.strftime('%H:%M:%S')}] TryOnServer.run() called")
        print(f"  Frame shape: {frame.shape if frame is not None else 'None'}")
        print(f"  Cloth shape: {cloth.shape if cloth is not None else 'None'}")

        frame_count = 0
        last_frame = None

        try:
            loop_start = time.time()
            
            # # Capture frame
            # if not self.paused:
            #     ret, frame = self.cap.read()
            #     if not ret:
            #         print("Error: Could not read frame")
            #         break
            #     last_frame = frame
            # else:
            #     frame = last_frame.copy() if last_frame is not None else None
            #     if frame is None:
            #         continue

            # # Load cloth image
            # print(f"Loading cloth image from: {cl}")
            # self.cloth_image = cv2.imread(cloth_path)
            # if self.cloth_image is None:
            #     raise ValueError(f"Could not load cloth image: {cloth_path}")
            self.cloth_image = cloth

            
            # print(f"Loaded garment: {self.cloth_image.shape}")
            
            # Pre-detect cloth keypoints
            # print("Detecting cloth keypoints...")
            self.cloth_keypoints, self.cloth_mask = self.detector.detect_cloth_keypoints(
                self.cloth_image
            )
            # print("Cloth keypoints detected!")
            
            # Process frame
            print(f"  Starting _process_frame...")
            result, proc_time = self._process_frame(frame, cloth)
            print(f"  _process_frame completed in {proc_time*1000:.1f}ms")
            print(f"  Result shape: {result.shape if result is not None else 'None'}")
            self.frame_times.append(proc_time)
            
            # # Calculate FPS
            # loop_time = time.time() - loop_start
            # current_fps = 1.0 / loop_time if loop_time > 0 else 0
            # self.fps_history.append(current_fps)
            # avg_fps = np.mean(self.fps_history)
            
            # # Draw UI
            display_frame = self._draw_ui(
                result,
                # avg_fps,
                # proc_time
            )

            # Try to show window (may fail if running headless/server)
            try:
                cv2.imshow('Virtual Try-On', display_frame)
            except Exception as imshow_error:
                # Ignore display errors when running as server (headless mode)
                print(f"  [INFO] cv2.imshow failed (expected in server mode): {imshow_error}")

            # Save with timestamp to verify updates
            import os
            import time as time_module
            save_path = os.path.join(os.path.dirname(__file__), 'saved_frame.png')
            success = cv2.imwrite(save_path, display_frame)
            timestamp = time_module.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] Saved frame to: {save_path} - Success: {success}")

            return display_frame
            
            # Handle keyboard input
            # key = cv2.waitKey(1) & 0xFF
            
            # if key == ord('q') or key == 27:  # Q or ESC
            #     break
            # elif key == ord(' '):  # SPACE
            #     self.show_original = not self.show_original
            #     print(f"Mode: {'ORIGINAL' if self.show_original else 'TRY-ON'}")
            # elif key == ord('k'):  # K
            #     self.show_keypoints = not self.show_keypoints
            #     print(f"Keypoints overlay: {'ON' if self.show_keypoints else 'OFF'}")
            # elif key == ord('p'):  # P
            #     self.paused = not self.paused
            #     print(f"{'PAUSED' if self.paused else 'RESUMED'}")
            # elif key == ord('s'):  # S - Screenshot
            #     timestamp = time.strftime("%Y%m%d_%H%M%S")
            #     filename = f"tryon_screenshot_{timestamp}.png"
            #     cv2.imwrite(filename, result)
            #     print(f"Screenshot saved: {filename}")
            
            # frame_count += 1
            
            # # Maintain target FPS
            # target_frame_time = 1.0 / self.target_fps
            # sleep_time = target_frame_time - (time.time() - loop_start)
            # if sleep_time > 0:
            #     time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        except Exception as e:
            print(f"\n[ERROR] Exception in TryOnServer.run(): {e}")
            import traceback
            traceback.print_exc()
            return frame  # Return original frame on error
        
        # finally:
        #     # Cleanup
        #     if self.cap is not None:
        #         self.cap.release()
        #     cv2.destroyAllWindows()
        #     self.detector.cleanup()
            
        #     # Print statistics
        #     print("\n" + "="*60)
        #     print("Session Statistics")
        #     print("="*60)
        #     print(f"Total frames processed: {frame_count}")
        #     if self.frame_times:
        #         print(f"Average processing time: {np.mean(self.frame_times)*1000:.1f}ms")
        #         print(f"Average FPS: {np.mean(self.fps_history):.1f}")
        #     print("="*60)


if __name__ == '__main__':
    # Configuration
    cloth_path = 'shirt.png'
    camera_id = 0
    target_fps = 30
    display_width = 1280
    display_height = 720
    device = 'cpu'  # or 'cpu'
    
    # Verify garment exists
    import os
    if not os.path.exists(cloth_path):
        print(f"Error: Garment image not found: {cloth_path}")
        exit(1)
    
    # Initialize and run
    tryon = TryOnServer(
        cloth_path=cloth_path,
        camera_id=camera_id,
        target_fps=target_fps,
        display_width=display_width,
        display_height=display_height,
        device=device
    )
    
    tryon.run()