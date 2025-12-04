"""
Main Application
Real-Time Virtual Try-On System

Usage:
    python main.py --garment path/to/shirt.jpg
    python main.py --device cpu
"""

import cv2
import numpy as np
import time
from collections import deque
import argparse

from cloth_detector import ClothDetector
from blender import GarmentBlender


class VirtualTryOnSystem:
    
    def __init__(self, device='cuda'):

        print("\n" + "="*70)
        print("REAL-TIME VIRTUAL TRY-ON SYSTEM")
        print("="*70 + "\n")
        
        self.detector = ClothDetector(device=device)
        self.blender = GarmentBlender()
        
        self.current_garment = None
        self.show_mask = False
        self.show_warped = False
        
        self.fps_history = deque(maxlen=30)
        self.detection_times = deque(maxlen=30)
        self.blend_times = deque(maxlen=30)
        
        print("="*70)
        print("System ready!")
        print("="*70 + "\n")
    
    def load_garment(self, garment_path):
        
        try:
            garment = cv2.imread(garment_path)
            if garment is None:
                raise ValueError(f"Cannot load image from {garment_path}")
            
            self.current_garment = garment
            print(f"Loaded garment: {garment_path}")
            return True
        except Exception as e:
            print(f"Failed to load garment: {e}")
            return False
    
    def process_frame(self, frame):
        
        detect_start = time.time()
        cloth_mask, landmarks = self.detector.detect_cloth_mask(frame)
        detect_time = time.time() - detect_start
        self.detection_times.append(detect_time)
        
        blend_start = time.time()
        if self.current_garment is not None:
            result = self.blender.blend(frame, self.current_garment, cloth_mask, landmarks)
        else:
            result = frame.copy()
        
        blend_time = time.time() - blend_start
        self.blend_times.append(blend_time)
        
        debug_info = {
            'cloth_mask': cloth_mask,
            'landmarks': landmarks,
            'detect_time': detect_time,
            'blend_time': blend_time
        }
        
        return result, debug_info
    
    def draw_ui(self, frame, debug_info):

        h, w = frame.shape[:2]
        
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (400, 140), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
        
        if self.fps_history:
            fps = np.mean(self.fps_history)
            color = (0, 255, 0) if fps > 10 else (0, 165, 255) if fps > 5 else (0, 0, 255)
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        if self.detection_times:
            detect_ms = np.mean(self.detection_times) * 1000
            cv2.putText(frame, f"Detection: {detect_ms:.0f}ms", (10, 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 200, 255), 2)
        
        if self.blend_times:
            blend_ms = np.mean(self.blend_times) * 1000
            cv2.putText(frame, f"Blending: {blend_ms:.0f}ms", (10, 95),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 100), 2)
        
        if self.current_garment is not None:
            status = "Loaded"
            color = (0, 255, 0)
        else:
            status = "None"
            color = (100, 100, 100)
        cv2.putText(frame, f"Garment: {status}", (10, 125),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        cv2.rectangle(frame, (0, h - 30), (w, h), (0, 0, 0), -1)
        controls = "G=Load | M=Mask | S=Save | Q=Quit"
        cv2.putText(frame, controls, (10, h - 8),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def run(self, camera_id=0):

        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            print("Cannot open webcam")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("\nCONTROLS:")
        print("  G - Load garment image")
        print("  M - Toggle mask visualization")
        print("  S - Save current result")
        print("  Q - Quit\n")
        
        print("Starting camera...\n")
        
        try:
            while True:
                frame_start = time.time()
                
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame")
                    continue
                
                frame = cv2.flip(frame, 1)
                
                result, debug_info = self.process_frame(frame)
                
                if self.show_mask:
                    mask_colored = cv2.applyColorMap(debug_info['cloth_mask'], 
                                                     cv2.COLORMAP_JET)
                    result = cv2.addWeighted(result, 0.6, mask_colored, 0.4, 0)
                
                result = self.draw_ui(result, debug_info)
                
                frame_time = time.time() - frame_start
                fps = 1.0 / frame_time if frame_time > 0 else 0
                self.fps_history.append(fps)
                
                cv2.imshow('Virtual Try-On', result)
                
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("\nQuitting...")
                    break
                elif key == ord('g'):
                    print("\nEnter garment image path:")
                    garment_path = input("> ").strip()
                    self.load_garment(garment_path)
                elif key == ord('m'):
                    self.show_mask = not self.show_mask
                    status = "ON" if self.show_mask else "OFF"
                    print(f"Mask visualization: {status}")
                elif key == ord('s'):
                    filename = f"result_{int(time.time())}.jpg"
                    cv2.imwrite(filename, result)
                    print(f"Saved: {filename}")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.detector.cleanup()
            
            self.print_statistics()
    
    def print_statistics(self):
        """Print session statistics"""
        print("\nSession Statistics:")
        if self.fps_history:
            avg_fps = np.mean(self.fps_history)
            min_fps = np.min(self.fps_history)
            max_fps = np.max(self.fps_history)
            print(f"   Average FPS: {avg_fps:.1f}")
            print(f"   Min/Max FPS: {min_fps:.1f} / {max_fps:.1f}")
        
        if self.detection_times:
            avg_detect = np.mean(self.detection_times) * 1000
            print(f"   Average detection time: {avg_detect:.1f}ms")
        
        if self.blend_times:
            avg_blend = np.mean(self.blend_times) * 1000
            print(f"   Average blending time: {avg_blend:.1f}ms")
        
        print()


def main():

    parser = argparse.ArgumentParser(
        description='Real-Time Virtual Try-On with SegFormer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --garment shirt.jpg
  python main.py --device cpu --camera 1
  python main.py --garment shirt.jpg --device cuda
        """
    )
    
    parser.add_argument(
        '--garment', 
        type=str, 
        help='Path to garment image (can also load during runtime with G key)'
    )
    
    parser.add_argument(
        '--device', 
        type=str, 
        default='cuda',
        choices=['cuda', 'cpu'],
        help='Device to run model on (default: cuda)'
    )
    
    parser.add_argument(
        '--camera', 
        type=int, 
        default=0,
        help='Camera device ID (default: 0)'
    )
    
    args = parser.parse_args()
    try:
        system = VirtualTryOnSystem(device=args.device)
    except Exception as e:
        print(f"\nFailed to initialize system: {e}")
        print("\nTroubleshooting:")
        print("  - Ensure all dependencies are installed: pip install -r requirements.txt")
        print("  - Check if CUDA is available if using --device cuda")
        print("  - Try --device cpu if GPU issues persist")
        return
    
    if args.garment:
        system.load_garment(args.garment)
    
    try:
        system.run(camera_id=args.camera)
    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()