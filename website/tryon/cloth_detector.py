import cv2
import numpy as np
from PIL import Image
import torch
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
import mediapipe as mp


class ClothDetector:
    
    def __init__(self, device='cuda'):

        if device == "cuda" and torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"

        local_path = "mattmdjaga/segformer_b2_clothes"

        self.processor = SegformerImageProcessor.from_pretrained(local_path)
        self.model = SegformerForSemanticSegmentation.from_pretrained(local_path)
        self.model.to(self.device).eval()

        mp_pose = mp.solutions.pose
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1,
        )
        self.mp_pose = mp_pose

        self.upper_clothes_class = 4


    def detect_cloth_mask(self, frame):
        h, w = frame.shape[:2]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)

        inputs = self.processor(images=pil, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            with torch.cuda.amp.autocast(enabled=(self.device == "cuda")):
                outputs = self.model(**inputs)
                logits = outputs.logits

        upsampled = torch.nn.functional.interpolate(
            logits,
            size=(h, w),
            mode="bilinear",
            align_corners=False,
        )

        pred = upsampled.argmax(1).squeeze(0).cpu().numpy()

        cloth_mask = (pred == self.upper_clothes_class).astype(np.uint8) * 255

        pose_results = self.pose.process(rgb)
        landmarks = pose_results.pose_landmarks if pose_results.pose_landmarks else None

        cloth_mask = self.refine_mask(cloth_mask)

        return cloth_mask, landmarks

    def refine_mask(self, mask):
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        mask = cv2.GaussianBlur(mask, (21, 21), 0)

        return mask

    def cleanup(self):
        if hasattr(self, "pose"):
            self.pose.close()
