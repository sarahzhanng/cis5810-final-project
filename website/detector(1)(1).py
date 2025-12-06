import cv2
import numpy as np
from PIL import Image
import torch
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
import mediapipe as mp
import traceback


# ======================================================
# Helper: Trim cloth image using alpha channel
# ======================================================
def trim_png_to_content(img):
    if img.shape[2] != 4:
        return img  # no alpha

    alpha = img[:, :, 3]
    coords = cv2.findNonZero(alpha)
    if coords is None:
        return img

    x, y, w, h = cv2.boundingRect(coords)
    return img[y:y+h, x:x+w]


class ClothDetector:
    def __init__(self, device='cuda', debug=True):
        self.debug = debug
        self.device = "cuda" if device == "cuda" and torch.cuda.is_available() else "cpu"
        self._log(f"Using device: {self.device}")

        self.processor = SegformerImageProcessor.from_pretrained("mattmdjaga/segformer_b2_clothes")
        self.model = SegformerForSemanticSegmentation.from_pretrained("mattmdjaga/segformer_b2_clothes")
        self.model.to(self.device).eval()

        mp_pose = mp.solutions.pose
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1,
        )
        self.mp_pose = mp_pose

        self.upper_clothes_class = 4


    def _log(self, msg):
        if self.debug:
            print(f"[DETECTOR] {msg}")


    # ======================================================
    # MASK EXTRACTION (clean + alpha-aware)
    # ======================================================
    def extract_cloth_mask_from_image(self, cloth_image):
        self._log("Extracting cloth mask")

        if cloth_image.shape[2] == 4:  # PNG with alpha
            alpha = cloth_image[:, :, 3]
            mask = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)[1]
        else:  # jpeg fallback
            gray = cv2.cvtColor(cloth_image, cv2.COLOR_BGR2GRAY)
            mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)[1]

        # remove fringe noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        return mask


    # ======================================================
    # HUMAN MASK (body detection)
    # ======================================================
    def detect_cloth_mask(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)

        inputs = self.processor(images=pil, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            logits = self.model(**inputs).logits

        upsampled = torch.nn.functional.interpolate(
            logits, size=frame.shape[:2], mode='bilinear', align_corners=False
        )
        pred = upsampled.argmax(1)[0].cpu().numpy()
        mask = (pred == self.upper_clothes_class).astype(np.uint8) * 255

        pose_results = self.pose.process(rgb)
        landmarks = pose_results.pose_landmarks if pose_results.pose_landmarks else None

        return mask, landmarks


    # ======================================================
    # CLOTH KEYS
    # ======================================================
    def detect_cloth_keypoints(self, cloth_image):
        mask = self.extract_cloth_mask_from_image(cloth_image)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, mask, None

        contour = max(contours, key=cv2.contourArea).squeeze()
        if contour.ndim != 2:
            return None, mask, None

        x_min, y_min = contour.min(axis=0)
        x_max, y_max = contour.max(axis=0)
        w = x_max - x_min
        h = y_max - y_min
        cx = (x_min + x_max) / 2.0

        kp = {}
        # Shoulders from top 25%
        top_pts = contour[(contour[:,1] < y_min + 0.25*h)]
        left = top_pts[np.argmin(top_pts[:,0])]
        right = top_pts[np.argmax(top_pts[:,0])]
        kp['left_shoulder'] = left.astype(float)
        kp['right_shoulder'] = right.astype(float)

        # Sleeve ends from widest points
        kp['left_sleeve_end'] = contour[np.argmin(contour[:,0])].astype(float)
        kp['right_sleeve_end'] = contour[np.argmax(contour[:,0])].astype(float)

        return kp, mask, (x_min, y_min, w, h)


    # ======================================================
    # HUMAN KEYS
    # ======================================================
    def get_human_keypoints(self, landmarks, frame_shape):
        if landmarks is None:
            return None

        h, w = frame_shape[:2]
        mp_pose = self.mp_pose

        def P(i): return np.array([landmarks.landmark[i].x*w, landmarks.landmark[i].y*h])

        kp = {
            'left_shoulder': P(mp_pose.PoseLandmark.LEFT_SHOULDER),
            'right_shoulder': P(mp_pose.PoseLandmark.RIGHT_SHOULDER),
            'left_wrist': P(mp_pose.PoseLandmark.LEFT_WRIST),
            'right_wrist': P(mp_pose.PoseLandmark.RIGHT_WRIST),
        }
        return kp


    # ======================================================
    # MAIN WARP
    # TPS first → piecewise fallback
    # ======================================================
    def warp_cloth_to_body(self, cloth, mask, cloth_kp, human_kp, frame_shape):
        H, W = frame_shape[:2]

        # Read keypoints into TPS format
        src = np.float32([
            cloth_kp['left_shoulder'], 
            cloth_kp['right_shoulder'],
            cloth_kp['left_sleeve_end'],
            cloth_kp['right_sleeve_end'],
        ])
        dst = np.float32([
            human_kp['left_shoulder'],
            human_kp['right_shoulder'],
            human_kp['left_wrist'],
            human_kp['right_wrist'],
        ])

        # Try TPS warp
        try:
            tps = cv2.createThinPlateSplineShapeTransformer()
            matches = [cv2.DMatch(i, i, 0) for i in range(len(src))]
            tps.estimateTransformation(dst.reshape(1,-1,2), src.reshape(1,-1,2), matches)

            warped_cloth = tps.warpImage(cloth, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
            warped_mask = tps.warpImage(mask, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

            warped_cloth = cv2.resize(warped_cloth, (W,H))
            warped_mask = cv2.resize(warped_mask, (W,H))
            return warped_cloth, warped_mask

        except:
            self._log("TPS failed → Piecewise fallback")

        # Piecewise fallback (simple affine)
        M = cv2.getAffineTransform(src[:3], dst[:3])
        warped_cloth = cv2.warpAffine(cloth, M, (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
        warped_mask = cv2.warpAffine(mask, M, (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        return warped_cloth, warped_mask


    # ======================================================
    # FINAL BLENDING
    # ======================================================
    def apply_cloth_overlay(self, frame, cloth_image, detected_mask, landmarks):
        try:
            # Alpha-trim cloth first
            cloth_image = trim_png_to_content(cloth_image)

            # Premultiply alpha (prevents halos!)
            if cloth_image.shape[2] == 4:
                rgb = cloth_image[:, :, :3].astype(np.float32)
                a = cloth_image[:, :, 3:4].astype(np.float32) / 255.0
                cloth_image = (rgb * a).astype(np.uint8)

            cloth_kp, cloth_mask, bbox = self.detect_cloth_keypoints(cloth_image)
            if cloth_kp is None: return frame

            human_kp = self.get_human_keypoints(landmarks, frame.shape)
            if human_kp is None: return frame

            warped_cloth, warped_mask = self.warp_cloth_to_body(
                cloth_image, cloth_mask, cloth_kp, human_kp, frame.shape)

            warped_mask = cv2.GaussianBlur(warped_mask, (21,21), 0)
            m = warped_mask.astype(np.float32)/255.0
            m3 = np.stack([m]*3, -1)

            result = (warped_cloth*m3 + frame*(1-m3)).astype(np.uint8)
            return result

        except Exception as e:
            traceback.print_exc()
            return frame
