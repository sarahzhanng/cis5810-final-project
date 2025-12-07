import cv2
import numpy as np
from PIL import Image
import torch
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
import mediapipe as mp
import traceback


class ClothDetector:
    def __init__(self, device="cuda", debug=True):
        self.debug = debug
        self.device = "cuda" if device == "cuda" and torch.cuda.is_available() else "cpu"
        self._log(f"Using device: {self.device}")

        # SegFormer for HUMAN clothes segmentation
        local_path = "mattmdjaga/segformer_b2_clothes"
        self.processor = SegformerImageProcessor.from_pretrained(local_path)
        self.model = SegformerForSemanticSegmentation.from_pretrained(local_path)
        self.model.to(self.device).eval()

        # MediaPipe pose for body keypoints
        mp_pose = mp.solutions.pose
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1,
        )
        self.mp_pose = mp_pose

        # SegFormer class index for "upper clothes"
        self.upper_clothes_class = 4

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _log(self, msg):
        if self.debug:
            print(f"[DEBUG] {msg}")

    # ------------------------------------------------------------------
    # HUMAN CLOTH MASK (camera frame)
    # ------------------------------------------------------------------
    def detect_cloth_mask(self, frame):
        """Segment the user's upper clothing from the camera frame."""
        self._log(f"detect_cloth_mask: frame shape = {frame.shape}")
        h, w = frame.shape[:2]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)

        inputs = self.processor(images=pil, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            with torch.cuda.amp.autocast(enabled=(self.device == "cuda")):
                logits = self.model(**inputs).logits

        upsampled = torch.nn.functional.interpolate(
            logits, size=(h, w), mode="bilinear", align_corners=False
        )
        pred = upsampled.argmax(1).squeeze(0).cpu().numpy()

        cloth_mask = (pred == self.upper_clothes_class).astype(np.uint8) * 255

        pose_results = self.pose.process(rgb)
        landmarks = pose_results.pose_landmarks if pose_results.pose_landmarks else None
        self._log(f"Pose landmarks detected: {landmarks is not None}")

        cloth_mask = self.refine_mask(cloth_mask)
        cloth_mask = self.enforce_torso_region(cloth_mask)
        self._log(
            f"detect_cloth_mask: mask shape = {cloth_mask.shape}, non-zero = {np.count_nonzero(cloth_mask)}"
        )

        return cloth_mask, landmarks

    def refine_mask(self, mask):
        """Strong cleanup to prevent huge black/white blobs."""
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        return mask

    def enforce_torso_region(self, mask):
        """
        Clean up mask by keeping only the largest connected component.
        NO width restrictions - user wants full coverage.
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return mask

        # Just keep the largest contour, no width restrictions
        largest = max(contours, key=cv2.contourArea)
        clean = np.zeros_like(mask)
        cv2.drawContours(clean, [largest], -1, 255, thickness=cv2.FILLED)
        return clean

    # ------------------------------------------------------------------
    # GARMENT MASK (offline cloth image – remove borders!)
    # ------------------------------------------------------------------
    def extract_cloth_mask_from_image(self, cloth_image):
        """
        Build a mask for the garment in the PNG.
        This version is more robust to transparent / grey borders:
        1) Estimate border color
        2) Mark pixels far from that color as garment
        3) Keep only largest connected component.
        """
        self._log(f"extract_cloth_mask_from_image: shape = {cloth_image.shape}")
        h, w = cloth_image.shape[:2]

        # If alpha channel exists, use it directly
        if cloth_image.shape[2] == 4:
            self._log("Alpha channel found, using it as primary mask")
            alpha = cloth_image[:, :, 3]
            # Use moderate threshold to include garment but exclude transparent borders
            mask = (alpha > 50).astype(np.uint8) * 255
        else:
            # Use border color to infer background
            border = np.concatenate(
                [
                    cloth_image[0, :],
                    cloth_image[-1, :],
                    cloth_image[:, 0],
                    cloth_image[:, -1],
                ]
            ).astype(np.float32)

            bg_color = np.median(border, axis=0)  # (B,G,R)
            self._log(f"Estimated border color (BGR): {bg_color}")

            # Distance in color space from background
            diff = np.linalg.norm(
                cloth_image.astype(np.float32) - bg_color.reshape(1, 1, 3), axis=2
            )

            # Threshold – tune if needed; high = ignore more near-border pixels
            thresh = 20.0
            mask = (diff > thresh).astype(np.uint8) * 255

        # Clean up mask - use smaller kernel to preserve garment edges
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        # Don't use MORPH_OPEN as it erodes the edges too much

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self._log(f"Found {len(contours)} garment contours")
        if contours:
            largest = max(contours, key=cv2.contourArea)
            self._log(f"Largest contour area: {cv2.contourArea(largest)}")
            clean = np.zeros_like(mask)
            cv2.drawContours(clean, [largest], -1, 255, thickness=cv2.FILLED)
            mask = clean

        return mask

    def detect_cloth_keypoints(self, cloth_image):
        """
        Old keypoint logic (neck, shoulders, armpits, hem) but using the
        new, border-aware garment mask.
        """
        self._log("detect_cloth_keypoints: Starting")
        h, w = cloth_image.shape[:2]

        cloth_mask = self.extract_cloth_mask_from_image(cloth_image)

        contours, _ = cv2.findContours(cloth_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            self._log("detect_cloth_keypoints: No contours found!")
            return None, cloth_mask

        contour = max(contours, key=cv2.contourArea).squeeze()
        self._log(f"detect_cloth_keypoints: contour shape = {contour.shape}")

        if len(contour.shape) == 1:
            self._log("detect_cloth_keypoints: Contour is 1D, returning None")
            return None, cloth_mask

        x_min, y_min = contour.min(axis=0)
        x_max, y_max = contour.max(axis=0)
        cloth_width = x_max - x_min
        cloth_height = y_max - y_min
        center_x = (x_min + x_max) / 2

        self._log(
            f"Cloth bounds: ({x_min}, {y_min}) to ({x_max}, {y_max}), size: {cloth_width}x{cloth_height}"
        )

        keypoints = {}

        # 1. Neckline (top center)
        top_region = contour[contour[:, 1] < y_min + cloth_height * 0.15]
        self._log(f"Top region points: {len(top_region)}")
        if len(top_region) > 0:
            top_center = top_region[np.argmin(np.abs(top_region[:, 0] - center_x))]
            keypoints["neck"] = top_center.astype(float)

        # 2. Shoulders
        top_25 = contour[contour[:, 1] < y_min + cloth_height * 0.25]
        self._log(f"Top 25% points: {len(top_25)}")
        if len(top_25) > 0:
            sorted_by_x = top_25[np.argsort(top_25[:, 0])]

            left_candidates = sorted_by_x[: max(1, len(sorted_by_x) // 4)]
            left_shoulder = left_candidates[np.argmin(left_candidates[:, 1])]
            keypoints["left_shoulder"] = left_shoulder.astype(float)

            right_candidates = sorted_by_x[-max(1, len(sorted_by_x) // 4) :]
            right_shoulder = right_candidates[np.argmin(right_candidates[:, 1])]
            keypoints["right_shoulder"] = right_shoulder.astype(float)

        # 3. Sleeve ends (extreme left/right)
        left_sleeve_end = contour[np.argmin(contour[:, 0])].astype(float)
        right_sleeve_end = contour[np.argmax(contour[:, 0])].astype(float)
        keypoints["left_sleeve_end"] = left_sleeve_end
        keypoints["right_sleeve_end"] = right_sleeve_end

        # 4. Armpits
        left_side = contour[contour[:, 0] < center_x]
        right_side = contour[contour[:, 0] >= center_x]

        if len(left_side) > 0:
            left_middle = left_side[
                (left_side[:, 1] > y_min + cloth_height * 0.2)
                & (left_side[:, 1] < y_min + cloth_height * 0.6)
            ]
            if len(left_middle) > 0:
                left_armpit = left_middle[np.argmax(left_middle[:, 0])]
                keypoints["left_armpit"] = left_armpit.astype(float)

        if len(right_side) > 0:
            right_middle = right_side[
                (right_side[:, 1] > y_min + cloth_height * 0.2)
                & (right_side[:, 1] < y_min + cloth_height * 0.6)
            ]
            if len(right_middle) > 0:
                right_armpit = right_middle[np.argmin(right_middle[:, 0])]
                keypoints["right_armpit"] = right_armpit.astype(float)

        # 5. Bottom hem
        bottom_region = contour[contour[:, 1] > y_min + cloth_height * 0.85]
        self._log(f"Bottom region points: {len(bottom_region)}")
        if len(bottom_region) > 0:
            left_bottom = bottom_region[np.argmin(bottom_region[:, 0])]
            keypoints["left_bottom"] = left_bottom.astype(float)

            right_bottom = bottom_region[np.argmax(bottom_region[:, 0])]
            keypoints["right_bottom"] = right_bottom.astype(float)

            center_bottom = bottom_region[np.argmax(bottom_region[:, 1])]
            keypoints["bottom_center"] = center_bottom.astype(float)

        self._log(
            f"detect_cloth_keypoints: Found {len(keypoints)} keypoints: {list(keypoints.keys())}"
        )
        return keypoints, cloth_mask

    # ------------------------------------------------------------------
    # HUMAN KEYPOINTS
    # ------------------------------------------------------------------
    def get_human_keypoints(self, landmarks, frame_shape, cloth_keypoints=None):
        self._log(f"get_human_keypoints: frame_shape = {frame_shape}")
        h, w = frame_shape[:2]

        if landmarks is None:
            self._log("get_human_keypoints: No landmarks!")
            return None

        def get_point(landmark_id):
            lm = landmarks.landmark[landmark_id]
            return np.array([lm.x * w, lm.y * h])

        def get_visibility(landmark_id):
            return landmarks.landmark[landmark_id].visibility

        mp_pose = self.mp_pose

        keypoints = {
            "left_shoulder": get_point(mp_pose.PoseLandmark.LEFT_SHOULDER),
            "right_shoulder": get_point(mp_pose.PoseLandmark.RIGHT_SHOULDER),
            "left_hip": get_point(mp_pose.PoseLandmark.LEFT_HIP),
            "right_hip": get_point(mp_pose.PoseLandmark.RIGHT_HIP),
            "left_elbow": get_point(mp_pose.PoseLandmark.LEFT_ELBOW),
            "right_elbow": get_point(mp_pose.PoseLandmark.RIGHT_ELBOW),
            "left_wrist": get_point(mp_pose.PoseLandmark.LEFT_WRIST),
            "right_wrist": get_point(mp_pose.PoseLandmark.RIGHT_WRIST),
            "left_knee": get_point(mp_pose.PoseLandmark.LEFT_KNEE),
            "right_knee": get_point(mp_pose.PoseLandmark.RIGHT_KNEE),
        }

        keypoints["left_elbow_vis"] = get_visibility(mp_pose.PoseLandmark.LEFT_ELBOW)
        keypoints["right_elbow_vis"] = get_visibility(mp_pose.PoseLandmark.RIGHT_ELBOW)
        keypoints["left_wrist_vis"] = get_visibility(mp_pose.PoseLandmark.LEFT_WRIST)
        keypoints["right_wrist_vis"] = get_visibility(mp_pose.PoseLandmark.RIGHT_WRIST)
        keypoints["left_knee_vis"] = get_visibility(mp_pose.PoseLandmark.LEFT_KNEE)
        keypoints["right_knee_vis"] = get_visibility(mp_pose.PoseLandmark.RIGHT_KNEE)

        keypoints["neck"] = (
            keypoints["left_shoulder"] + keypoints["right_shoulder"]
        ) / 2
        keypoints["waist_center"] = (
            keypoints["left_hip"] + keypoints["right_hip"]
        ) / 2

        keypoints["left_sleeve_end"], keypoints["right_sleeve_end"] = (
            self._estimate_human_sleeve_ends(keypoints, cloth_keypoints)
        )

        self._log(f"get_human_keypoints: Found {len(keypoints)} keypoints")
        return keypoints

    def _estimate_human_sleeve_ends(self, human_kp, cloth_kp):
        left_shoulder = human_kp["left_shoulder"]
        right_shoulder = human_kp["right_shoulder"]
        left_elbow = human_kp["left_elbow"]
        right_elbow = human_kp["right_elbow"]
        left_wrist = human_kp["left_wrist"]
        right_wrist = human_kp["right_wrist"]

        sleeve_ratio = 0.5

        if cloth_kp is not None:
            cloth_shoulder_width = np.linalg.norm(
                cloth_kp.get("right_shoulder", np.array([0, 0]))
                - cloth_kp.get("left_shoulder", np.array([0, 0]))
            )

            if cloth_shoulder_width > 0:
                left_sleeve_len = np.linalg.norm(
                    cloth_kp.get(
                        "left_sleeve_end",
                        cloth_kp.get("left_shoulder", np.array([0, 0])),
                    )
                    - cloth_kp.get("left_shoulder", np.array([0, 0]))
                )
                right_sleeve_len = np.linalg.norm(
                    cloth_kp.get(
                        "right_sleeve_end",
                        cloth_kp.get("right_shoulder", np.array([0, 0])),
                    )
                    - cloth_kp.get("right_shoulder", np.array([0, 0]))
                )

                avg_sleeve_len = (left_sleeve_len + right_sleeve_len) / 2
                ratio = avg_sleeve_len / cloth_shoulder_width

                self._log(f"Sleeve ratio: {ratio:.2f}")

                if ratio < 0.3:
                    sleeve_ratio = 0.2
                elif ratio < 0.6:
                    sleeve_ratio = 0.4
                elif ratio < 1.0:
                    sleeve_ratio = 0.6
                elif ratio < 1.5:
                    sleeve_ratio = 0.8
                else:
                    sleeve_ratio = 1.0

        left_arm_upper = left_elbow - left_shoulder
        left_arm_lower = left_wrist - left_elbow

        right_arm_upper = right_elbow - right_shoulder
        right_arm_lower = right_wrist - right_elbow

        if sleeve_ratio <= 0.5:
            t = sleeve_ratio * 2
            left_sleeve_end = left_shoulder + t * left_arm_upper
            right_sleeve_end = right_shoulder + t * right_arm_upper
        else:
            t = (sleeve_ratio - 0.5) * 2
            left_sleeve_end = left_elbow + t * left_arm_lower
            right_sleeve_end = right_elbow + t * right_arm_lower

        return left_sleeve_end, right_sleeve_end

    # ------------------------------------------------------------------
    # WARP GARMENT onto BODY
    # (old good logic, unchanged except using improved masks)
    # ------------------------------------------------------------------
    def warp_cloth_to_body(
        self, cloth_image, cloth_mask, cloth_keypoints, human_keypoints, frame_shape,
        alpha_mask=None
    ):
        self._log("warp_cloth_to_body: Starting")
        h, w = frame_shape[:2]

        # Check if we need to flip left/right (mirroring issue)
        cloth_left_x = cloth_keypoints.get("left_shoulder", np.array([0, 0]))[0]
        cloth_right_x = cloth_keypoints.get("right_shoulder", np.array([0, 0]))[0]
        human_left_x = human_keypoints.get("left_shoulder", np.array([0, 0]))[0]
        human_right_x = human_keypoints.get("right_shoulder", np.array([0, 0]))[0]

        cloth_left_is_left = cloth_left_x < cloth_right_x
        human_left_is_left = human_left_x < human_right_x

        need_mirror = cloth_left_is_left != human_left_is_left
        self._log(f"Cloth left_x={cloth_left_x:.1f}, right_x={cloth_right_x:.1f}")
        self._log(f"Human left_x={human_left_x:.1f}, right_x={human_right_x:.1f}")
        self._log(f"Need mirror: {need_mirror}")

        src_pts = []
        dst_pts = []

        if need_mirror:
            point_pairs = [
                ("left_shoulder", "right_shoulder"),
                ("right_shoulder", "left_shoulder"),
                ("left_bottom", "right_hip"),
                ("right_bottom", "left_hip"),
                ("left_sleeve_end", "right_sleeve_end"),
                ("right_sleeve_end", "left_sleeve_end"),
                ("neck", "neck"),
                ("bottom_center", "waist_center"),
            ]
        else:
            point_pairs = [
                ("left_shoulder", "left_shoulder"),
                ("right_shoulder", "right_shoulder"),
                ("left_bottom", "left_hip"),
                ("right_bottom", "right_hip"),
                ("left_sleeve_end", "left_sleeve_end"),
                ("right_sleeve_end", "right_sleeve_end"),
                ("neck", "neck"),
                ("bottom_center", "waist_center"),
            ]

        # Calculate vertical shift to move garment UP
        h, w = frame_shape[:2]
        vertical_shift_up = int(h * 0.1)  # Shift up by 10% of frame height

        for cloth_key, human_key in point_pairs:
            if cloth_key in cloth_keypoints and human_key in human_keypoints:
                src_pt = cloth_keypoints[cloth_key].copy()
                dst_pt = human_keypoints[human_key].copy()

                # SHIFT ALL POINTS UP to raise the garment higher on the body
                dst_pt[1] = max(0, dst_pt[1] - vertical_shift_up)

                src_pts.append(src_pt)
                dst_pts.append(dst_pt)
                self._log(f"  Mapping {cloth_key} -> {human_key}: {src_pt} -> {dst_pt}")

        # Armpits (also apply vertical shift)
        if need_mirror:
            if "left_armpit" in cloth_keypoints:
                src_pts.append(cloth_keypoints["left_armpit"].copy())
                armpit_pos = (
                    human_keypoints["right_shoulder"] + human_keypoints["right_hip"]
                ) / 2
                armpit_pos[0] = human_keypoints["right_shoulder"][0]
                armpit_pos[1] = max(0, armpit_pos[1] - vertical_shift_up)
                dst_pts.append(armpit_pos)

            if "right_armpit" in cloth_keypoints:
                src_pts.append(cloth_keypoints["right_armpit"].copy())
                armpit_pos = (
                    human_keypoints["left_shoulder"] + human_keypoints["left_hip"]
                ) / 2
                armpit_pos[0] = human_keypoints["left_shoulder"][0]
                armpit_pos[1] = max(0, armpit_pos[1] - vertical_shift_up)
                dst_pts.append(armpit_pos)
        else:
            if "left_armpit" in cloth_keypoints:
                src_pts.append(cloth_keypoints["left_armpit"].copy())
                armpit_pos = (
                    human_keypoints["left_shoulder"] + human_keypoints["left_hip"]
                ) / 2
                armpit_pos[0] = human_keypoints["left_shoulder"][0]
                armpit_pos[1] = max(0, armpit_pos[1] - vertical_shift_up)
                dst_pts.append(armpit_pos)

            if "right_armpit" in cloth_keypoints:
                src_pts.append(cloth_keypoints["right_armpit"].copy())
                armpit_pos = (
                    human_keypoints["right_shoulder"] + human_keypoints["right_hip"]
                ) / 2
                armpit_pos[0] = human_keypoints["right_shoulder"][0]
                armpit_pos[1] = max(0, armpit_pos[1] - vertical_shift_up)
                dst_pts.append(armpit_pos)

        # Neck and bottom_center already handled in point_pairs above

        src_pts = np.float32(src_pts)
        dst_pts = np.float32(dst_pts)

        self._log(f"warp_cloth_to_body: {len(src_pts)} point pairs")

        if len(src_pts) < 3:
            self._log("warp_cloth_to_body: Not enough points!")
            return None, None, None

        # TPS if possible, else perspective / affine
        if len(src_pts) >= 4:
            self._log("Using TPS warp")
            try:
                tps = cv2.createThinPlateSplineShapeTransformer()
                src_pts_tps = src_pts.reshape(1, -1, 2)
                dst_pts_tps = dst_pts.reshape(1, -1, 2)
                matches = [cv2.DMatch(i, i, 0) for i in range(len(src_pts))]

                tps.estimateTransformation(dst_pts_tps, src_pts_tps, matches)

                warped_cloth = tps.warpImage(cloth_image)
                warped_mask = tps.warpImage(cloth_mask)
                warped_alpha = tps.warpImage(alpha_mask) if alpha_mask is not None else None

                if warped_cloth.shape[:2] != (h, w):
                    warped_cloth = cv2.resize(warped_cloth, (w, h))
                    warped_mask = cv2.resize(warped_mask, (w, h))
                    if warped_alpha is not None:
                        warped_alpha = cv2.resize(warped_alpha, (w, h))
            except Exception as e:
                self._log(f"TPS warp failed: {e}, trying perspective")
                try:
                    matrix = cv2.getPerspectiveTransform(src_pts[:4], dst_pts[:4])
                    warped_cloth = cv2.warpPerspective(
                        cloth_image,
                        matrix,
                        (w, h),
                        flags=cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_CONSTANT,
                    )
                    warped_mask = cv2.warpPerspective(
                        cloth_mask,
                        matrix,
                        (w, h),
                        flags=cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_CONSTANT,
                    )
                    warped_alpha = cv2.warpPerspective(
                        alpha_mask,
                        matrix,
                        (w, h),
                        flags=cv2.INTER_LINEAR,
                        borderMode=cv2.BORDER_CONSTANT,
                    ) if alpha_mask is not None else None
                except Exception as e2:
                    self._log(f"Perspective also failed: {e2}, using homography")
                    matrix, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC)
                    warped_cloth = cv2.warpPerspective(cloth_image, matrix, (w, h))
                    warped_mask = cv2.warpPerspective(cloth_mask, matrix, (w, h))
                    warped_alpha = cv2.warpPerspective(alpha_mask, matrix, (w, h)) if alpha_mask is not None else None
        else:
            self._log("Using affine warp (3 points)")
            matrix = cv2.getAffineTransform(src_pts[:3], dst_pts[:3])
            warped_cloth = cv2.warpAffine(
                cloth_image,
                matrix,
                (w, h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0),
            )
            warped_mask = cv2.warpAffine(
                cloth_mask,
                matrix,
                (w, h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0,
            )
            warped_alpha = cv2.warpAffine(
                alpha_mask,
                matrix,
                (w, h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0,
            ) if alpha_mask is not None else None

        self._log(
            f"warp_cloth_to_body: warped_cloth shape = {warped_cloth.shape if warped_cloth is not None else None}"
        )
        self._log(
            f"warp_cloth_to_body: warped_mask non-zero = {np.count_nonzero(warped_mask) if warped_mask is not None else 0}"
        )
        return warped_cloth, warped_mask, warped_alpha

    # ------------------------------------------------------------------
    # APPLY OVERLAY (warp + blend)
    # ------------------------------------------------------------------
    def apply_cloth_overlay(self, frame, cloth_image, detected_mask, landmarks):
        self._log("=" * 60)
        self._log("apply_cloth_overlay: Starting")
        self._log("=" * 60)

        try:
            h, w = frame.shape[:2]
            self._log(f"Frame shape: {frame.shape}")
            self._log(f"Cloth image shape: {cloth_image.shape}")
            self._log(f"Detected mask shape: {detected_mask.shape}")

            # Handle RGBA by compositing onto black background (preserves garment colors)
            # ALSO save alpha mask to filter later
            if cloth_image.shape[2] == 4:
                self._log("Converting RGBA to BGR by compositing on black background")
                alpha = cloth_image[:, :, 3]
                alpha_normalized = alpha / 255.0
                alpha_3ch = np.stack([alpha_normalized] * 3, axis=-1)
                bgr = cloth_image[:, :, :3]
                # Composite on BLACK background (not white) to avoid white edges
                black_bg = np.zeros_like(bgr)
                cloth_image_bgr = (bgr * alpha_3ch + black_bg * (1 - alpha_3ch)).astype(np.uint8)
                cloth_image_for_keypoints = cloth_image.copy()

                # SAVE original alpha mask - we'll use this after warping
                # Pixels with alpha > 50 are part of the garment (even if dark colored)
                original_alpha_mask = (alpha > 50).astype(np.uint8) * 255
            else:
                cloth_image_bgr = cloth_image.copy()
                cloth_image_for_keypoints = cloth_image.copy()
                original_alpha_mask = None

            # Resize cloth to match frame
            self._log("Resizing cloth image to match frame")
            cloth_image_bgr = cv2.resize(cloth_image_bgr, (w, h), interpolation=cv2.INTER_LINEAR)
            cloth_image_for_keypoints = cv2.resize(cloth_image_for_keypoints, (w, h), interpolation=cv2.INTER_LINEAR)
            if original_alpha_mask is not None:
                original_alpha_mask = cv2.resize(original_alpha_mask, (w, h), interpolation=cv2.INTER_LINEAR)
            self._log(f"Resized cloth shape: {cloth_image_bgr.shape}")

            # Detect cloth keypoints
            self._log("Detecting cloth keypoints...")
            cloth_keypoints, cloth_mask = self.detect_cloth_keypoints(cloth_image_for_keypoints)

            # Debug: save original cloth mask before warping
            import os
            debug_dir = os.path.dirname(__file__)
            cv2.imwrite(os.path.join(debug_dir, "debug_cloth_mask_original.jpg"), cloth_mask)
            self._log(f"Saved original cloth mask, non-zero pixels: {np.count_nonzero(cloth_mask)}")

            # Debug: save cloth with keypoints visualized
            if cloth_keypoints is not None:
                debug_cloth = cloth_image_bgr.copy()
                for name, point in cloth_keypoints.items():
                    pt = tuple(point.astype(int))
                    cv2.circle(debug_cloth, pt, 10, (0, 255, 0), -1)
                    cv2.putText(debug_cloth, name[:4], (pt[0]+5, pt[1]-5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                cv2.imwrite(os.path.join(debug_dir, "debug_cloth_keypoints.jpg"), debug_cloth)
                self._log(f"Cloth keypoints: {list(cloth_keypoints.keys())}")

            if cloth_keypoints is None:
                self._log("No cloth keypoints found, using simple overlay")
                return self._simple_overlay(frame, cloth_image_bgr, detected_mask)

            # Get human keypoints
            self._log("Getting human keypoints...")
            human_keypoints = self.get_human_keypoints(
                landmarks, frame.shape, cloth_keypoints
            )

            if human_keypoints is None:
                self._log("No human keypoints found, using simple overlay")
                return self._simple_overlay(frame, cloth_image_bgr, detected_mask)

            # Warp cloth to body (using BGR version without alpha)
            # Also warp the original alpha mask if available
            self._log("Warping cloth to body...")
            warped_cloth, warped_cloth_mask, warped_alpha_mask = self.warp_cloth_to_body(
                cloth_image_bgr, cloth_mask, cloth_keypoints, human_keypoints, frame.shape,
                original_alpha_mask
            )

            if warped_cloth is None:
                self._log("Warping failed, using simple overlay")
                return self._simple_overlay(frame, cloth_image_bgr, detected_mask)

            self._log(f"Warped cloth shape: {warped_cloth.shape}")
            self._log(f"Warped mask shape: {warped_cloth_mask.shape}")
            self._log(
                f"Warped mask non-zero pixels: {np.count_nonzero(warped_cloth_mask)}"
            )
            self._log(
                f"Detected mask non-zero pixels: {np.count_nonzero(detected_mask)}"
            )

            # Debug: save warped cloth and mask
            import os
            debug_dir = os.path.dirname(__file__)
            cv2.imwrite(os.path.join(debug_dir, "debug_warped_cloth.jpg"), warped_cloth)
            cv2.imwrite(os.path.join(debug_dir, "debug_warped_mask.jpg"), warped_cloth_mask)
            self._log(f"Saved debug images to {debug_dir}")

            # Combine masks FIRST (before alpha filtering to get good coverage)
            self._log("Combining masks...")
            # Dilate warped mask to ensure good coverage
            warped_mask_dilated = cv2.dilate(
                warped_cloth_mask,
                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (50, 50)),
                iterations=3,
            )
            combined_mask = cv2.bitwise_and(detected_mask, warped_mask_dilated)
            self._log(f"Combined mask non-zero: {np.count_nonzero(combined_mask)}")

            # Debug: save dilated warped mask to see coverage
            cv2.imwrite(os.path.join(debug_dir, "debug_warped_mask_dilated.jpg"), warped_mask_dilated)
            cv2.imwrite(os.path.join(debug_dir, "debug_detected_mask.jpg"), detected_mask)

            # NOW filter with alpha mask AFTER dilation to remove black edges
            if warped_alpha_mask is not None:
                self._log("Applying warped alpha mask to remove black edges from combined mask")
                # Dilate alpha mask slightly to be less aggressive
                alpha_dilated = cv2.dilate(
                    warped_alpha_mask,
                    cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
                    iterations=1,
                )
                combined_mask = cv2.bitwise_and(combined_mask, alpha_dilated)
                cv2.imwrite(os.path.join(debug_dir, "debug_warped_alpha_mask.jpg"), warped_alpha_mask)
                cv2.imwrite(os.path.join(debug_dir, "debug_alpha_dilated.jpg"), alpha_dilated)
                self._log(f"After alpha filter, mask non-zero: {np.count_nonzero(combined_mask)}")
            else:
                self._log("No alpha mask available, skipping alpha filtering")

            # Only use fallback if combined mask is REALLY small (less than 10% of detected)
            if np.count_nonzero(combined_mask) < np.count_nonzero(detected_mask) * 0.1:
                self._log("WARNING: Combined mask too small, using detected mask instead")
                combined_mask = detected_mask.copy()
            else:
                self._log(f"Combined mask is {np.count_nonzero(combined_mask) / np.count_nonzero(detected_mask) * 100:.1f}% of detected mask")

            combined_mask = cv2.GaussianBlur(combined_mask, (15, 15), 0)
            cv2.imwrite(os.path.join(debug_dir, "debug_combined_mask.jpg"), combined_mask)

            # Blend using combined mask (alpha filtering already applied earlier)
            self._log("Blending...")
            mask_normalized = combined_mask.astype(np.float32) / 255.0
            mask_3ch = np.stack([mask_normalized] * 3, axis=-1)

            result = (warped_cloth * mask_3ch + frame * (1 - mask_3ch)).astype(
                np.uint8
            )

            # Debug: save final blend mask
            cv2.imwrite(os.path.join(debug_dir, "debug_final_blend_mask.jpg"),
                       (mask_3ch[:,:,0] * 255).astype(np.uint8))

            self._log("apply_cloth_overlay: Complete!")
            return result

        except Exception as e:
            self._log(f"ERROR in apply_cloth_overlay: {e}")
            traceback.print_exc()
            return frame

    # ------------------------------------------------------------------
    # SIMPLE OVERLAY (fallback)
    # ------------------------------------------------------------------
    def _simple_overlay(self, frame, cloth_image, cloth_mask):
        self._log("Using simple overlay fallback")
        h, w = frame.shape[:2]

        coords = cv2.findNonZero(cloth_mask)
        if coords is None:
            self._log("No mask coordinates found!")
            return frame

        x, y, w_box, h_box = cv2.boundingRect(coords)
        self._log(f"Bounding box: ({x}, {y}, {w_box}, {h_box})")

        cloth_resized = cv2.resize(cloth_image, (w_box, h_box))

        cloth_full = np.zeros_like(frame)
        cloth_full[y : y + h_box, x : x + w_box] = cloth_resized

        mask_normalized = cloth_mask.astype(np.float32) / 255.0
        mask_3ch = np.stack([mask_normalized] * 3, axis=-1)

        result = (cloth_full * mask_3ch + frame * (1 - mask_3ch)).astype(np.uint8)
        return result

    # ------------------------------------------------------------------
    # VISUALIZATION HELPERS
    # ------------------------------------------------------------------
    def visualize_cloth_keypoints(self, cloth_image):
        result = cloth_image.copy()
        keypoints, mask = self.detect_cloth_keypoints(cloth_image)

        if keypoints is None:
            return result, mask

        colors = {
            "neck": (0, 255, 255),
            "left_shoulder": (0, 255, 0),
            "right_shoulder": (0, 255, 0),
            "left_armpit": (255, 0, 255),
            "right_armpit": (255, 0, 255),
            "left_bottom": (255, 0, 0),
            "right_bottom": (255, 0, 0),
            "bottom_center": (255, 128, 0),
            "left_sleeve_end": (0, 128, 255),
            "right_sleeve_end": (0, 128, 255),
        }

        for name, point in keypoints.items():
            pt = tuple(point.astype(int))
            color = colors.get(name, (255, 255, 255))
            cv2.circle(result, pt, 8, color, -1)
            cv2.putText(
                result,
                name,
                (pt[0] + 5, pt[1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                color,
                1,
            )

        connections = [
            ("left_shoulder", "right_shoulder", (0, 255, 0)),
            ("left_shoulder", "left_sleeve_end", (0, 200, 255)),
            ("right_shoulder", "right_sleeve_end", (0, 200, 255)),
            ("left_bottom", "right_bottom", (255, 0, 0)),
        ]

        for start, end, color in connections:
            if start in keypoints and end in keypoints:
                cv2.line(
                    result,
                    tuple(keypoints[start].astype(int)),
                    tuple(keypoints[end].astype(int)),
                    color,
                    2,
                )

        return result, mask

    def visualize_human_keypoints(self, frame, landmarks, cloth_keypoints=None):
        result = frame.copy()
        keypoints = self.get_human_keypoints(landmarks, frame.shape, cloth_keypoints)

        if keypoints is None:
            return result

        colors = {
            "neck": (0, 255, 255),
            "left_shoulder": (0, 255, 0),
            "right_shoulder": (0, 255, 0),
            "left_hip": (255, 0, 0),
            "right_hip": (255, 0, 0),
            "waist_center": (255, 128, 0),
            "left_elbow": (128, 255, 128),
            "right_elbow": (128, 255, 128),
            "left_wrist": (64, 255, 64),
            "right_wrist": (64, 255, 64),
            "left_sleeve_end": (0, 128, 255),
            "right_sleeve_end": (0, 128, 255),
        }

        for name, point in keypoints.items():
            if "_vis" in name:
                continue
            pt = tuple(point.astype(int))
            color = colors.get(name, (255, 255, 255))
            cv2.circle(result, pt, 8, color, -1)
            cv2.putText(
                result,
                name,
                (pt[0] + 5, pt[1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                color,
                1,
            )

        connections = [
            ("left_shoulder", "left_elbow", (128, 255, 128)),
            ("left_elbow", "left_wrist", (128, 255, 128)),
            ("right_shoulder", "right_elbow", (128, 255, 128)),
            ("right_elbow", "right_wrist", (128, 255, 128)),
            ("left_shoulder", "right_shoulder", (0, 255, 0)),
            ("left_hip", "right_hip", (255, 0, 0)),
            ("left_shoulder", "left_sleeve_end", (0, 128, 255)),
            ("right_shoulder", "right_sleeve_end", (0, 128, 255)),
        ]

        for start, end, color in connections:
            if start in keypoints and end in keypoints:
                pt1 = tuple(keypoints[start].astype(int))
                pt2 = tuple(keypoints[end].astype(int))
                cv2.line(result, pt1, pt2, color, 2)

        return result

    # ------------------------------------------------------------------
    # CLEANUP
    # ------------------------------------------------------------------
    def cleanup(self):
        if hasattr(self, "pose"):
            self.pose.close()
