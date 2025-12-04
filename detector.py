import cv2
import numpy as np
from PIL import Image
import torch
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
import mediapipe as mp
import traceback


class ClothDetector:
    def __init__(self, device='cuda', debug=True):
        self.debug = debug
        self.device = "cuda" if device == "cuda" and torch.cuda.is_available() else "cpu"
        self._log(f"Using device: {self.device}")

        local_path = "../segformer_b2_clothes"
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

    def _log(self, msg):
        if self.debug:
            print(f"[DEBUG] {msg}")

    def detect_cloth_mask(self, frame):
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
        self._log(f"detect_cloth_mask: mask shape = {cloth_mask.shape}, non-zero = {np.count_nonzero(cloth_mask)}")

        return cloth_mask, landmarks

    def refine_mask(self, mask):
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        return cv2.GaussianBlur(mask, (11, 11), 0)

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
            'left_shoulder': get_point(mp_pose.PoseLandmark.LEFT_SHOULDER),
            'right_shoulder': get_point(mp_pose.PoseLandmark.RIGHT_SHOULDER),
            'left_hip': get_point(mp_pose.PoseLandmark.LEFT_HIP),
            'right_hip': get_point(mp_pose.PoseLandmark.RIGHT_HIP),
            'left_elbow': get_point(mp_pose.PoseLandmark.LEFT_ELBOW),
            'right_elbow': get_point(mp_pose.PoseLandmark.RIGHT_ELBOW),
            'left_wrist': get_point(mp_pose.PoseLandmark.LEFT_WRIST),
            'right_wrist': get_point(mp_pose.PoseLandmark.RIGHT_WRIST),
        }
        
        keypoints['left_elbow_vis'] = get_visibility(mp_pose.PoseLandmark.LEFT_ELBOW)
        keypoints['right_elbow_vis'] = get_visibility(mp_pose.PoseLandmark.RIGHT_ELBOW)
        keypoints['left_wrist_vis'] = get_visibility(mp_pose.PoseLandmark.LEFT_WRIST)
        keypoints['right_wrist_vis'] = get_visibility(mp_pose.PoseLandmark.RIGHT_WRIST)
        
        keypoints['neck'] = (keypoints['left_shoulder'] + keypoints['right_shoulder']) / 2
        keypoints['waist_center'] = (keypoints['left_hip'] + keypoints['right_hip']) / 2
        
        keypoints['left_sleeve_end'], keypoints['right_sleeve_end'] = \
            self._estimate_human_sleeve_ends(keypoints, cloth_keypoints)
        
        self._log(f"get_human_keypoints: Found {len(keypoints)} keypoints")
        return keypoints

    def _estimate_human_sleeve_ends(self, human_kp, cloth_kp):
        left_shoulder = human_kp['left_shoulder']
        right_shoulder = human_kp['right_shoulder']
        left_elbow = human_kp['left_elbow']
        right_elbow = human_kp['right_elbow']
        left_wrist = human_kp['left_wrist']
        right_wrist = human_kp['right_wrist']
        
        sleeve_ratio = 0.5
        
        if cloth_kp is not None:
            cloth_shoulder_width = np.linalg.norm(
                cloth_kp.get('right_shoulder', np.array([0, 0])) - 
                cloth_kp.get('left_shoulder', np.array([0, 0]))
            )
            
            if cloth_shoulder_width > 0:
                left_sleeve_len = np.linalg.norm(
                    cloth_kp.get('left_sleeve_end', cloth_kp.get('left_shoulder', np.array([0, 0]))) -
                    cloth_kp.get('left_shoulder', np.array([0, 0]))
                )
                right_sleeve_len = np.linalg.norm(
                    cloth_kp.get('right_sleeve_end', cloth_kp.get('right_shoulder', np.array([0, 0]))) -
                    cloth_kp.get('right_shoulder', np.array([0, 0]))
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

    def extract_cloth_mask_from_image(self, cloth_image):
        self._log(f"extract_cloth_mask_from_image: shape = {cloth_image.shape}")
        h, w = cloth_image.shape[:2]
        
        gray = cv2.cvtColor(cloth_image, cv2.COLOR_BGR2GRAY)
        
        border_pixels = np.concatenate([
            cloth_image[0, :],
            cloth_image[-1, :],
            cloth_image[:, 0],
            cloth_image[:, -1]
        ])
        avg_border = np.mean(border_pixels)
        self._log(f"Average border value: {avg_border:.1f}")
        
        if avg_border > 200:
            self._log("Using white background threshold")
            _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        elif avg_border < 50:
            self._log("Using dark background threshold")
            _, mask = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)
        else:
            self._log("Using flood fill for complex background")
            mask = np.ones((h, w), dtype=np.uint8) * 255
            flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
            
            for seed in [(0, 0), (w-1, 0), (0, h-1), (w-1, h-1)]:
                cv2.floodFill(gray, flood_mask, seed, 128, 30, 30)
            
            mask = (flood_mask[1:-1, 1:-1] == 0).astype(np.uint8) * 255
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self._log(f"Found {len(contours)} contours")
        
        if contours:
            largest = max(contours, key=cv2.contourArea)
            self._log(f"Largest contour area: {cv2.contourArea(largest)}")
            mask = np.zeros_like(mask)
            cv2.drawContours(mask, [largest], -1, 255, -1)
        
        return mask

    def detect_cloth_keypoints(self, cloth_image):
        self._log("detect_cloth_keypoints: Starting")
        h, w = cloth_image.shape[:2]
        
        cloth_mask = self.extract_cloth_mask_from_image(cloth_image)
        
        contours, _ = cv2.findContours(cloth_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            self._log("detect_cloth_keypoints: No contours found!")
            return None, cloth_mask
        
        contour = max(contours, key=cv2.contourArea)
        contour = contour.squeeze()
        
        self._log(f"detect_cloth_keypoints: contour shape = {contour.shape}")
        
        if len(contour.shape) == 1:
            self._log("detect_cloth_keypoints: Contour is 1D, returning None")
            return None, cloth_mask
        
        x_min, y_min = contour.min(axis=0)
        x_max, y_max = contour.max(axis=0)
        cloth_width = x_max - x_min
        cloth_height = y_max - y_min
        center_x = (x_min + x_max) / 2
        
        self._log(f"Cloth bounds: ({x_min}, {y_min}) to ({x_max}, {y_max}), size: {cloth_width}x{cloth_height}")
        
        keypoints = {}
        
        # 1. Find neckline
        top_region = contour[contour[:, 1] < y_min + cloth_height * 0.15]
        self._log(f"Top region points: {len(top_region)}")
        if len(top_region) > 0:
            top_center = top_region[np.argmin(np.abs(top_region[:, 0] - center_x))]
            keypoints['neck'] = top_center.astype(float)
        
        # 2. Find shoulders
        top_30 = contour[contour[:, 1] < y_min + cloth_height * 0.25]
        self._log(f"Top 25% points: {len(top_30)}")
        if len(top_30) > 0:
            sorted_by_x = top_30[np.argsort(top_30[:, 0])]
            
            left_candidates = sorted_by_x[:max(1, len(sorted_by_x)//4)]
            left_shoulder = left_candidates[np.argmin(left_candidates[:, 1])]
            keypoints['left_shoulder'] = left_shoulder.astype(float)
            
            right_candidates = sorted_by_x[-max(1, len(sorted_by_x)//4):]
            right_shoulder = right_candidates[np.argmin(right_candidates[:, 1])]
            keypoints['right_shoulder'] = right_shoulder.astype(float)
        
        # 3. Find sleeve ends
        left_sleeve_end = contour[np.argmin(contour[:, 0])].astype(float)
        right_sleeve_end = contour[np.argmax(contour[:, 0])].astype(float)
        keypoints['left_sleeve_end'] = left_sleeve_end
        keypoints['right_sleeve_end'] = right_sleeve_end
        
        # 4. Find armpits
        left_side = contour[contour[:, 0] < center_x]
        right_side = contour[contour[:, 0] >= center_x]
        
        if len(left_side) > 0:
            left_middle = left_side[
                (left_side[:, 1] > y_min + cloth_height * 0.2) & 
                (left_side[:, 1] < y_min + cloth_height * 0.6)
            ]
            if len(left_middle) > 0:
                left_armpit = left_middle[np.argmax(left_middle[:, 0])]
                keypoints['left_armpit'] = left_armpit.astype(float)
        
        if len(right_side) > 0:
            right_middle = right_side[
                (right_side[:, 1] > y_min + cloth_height * 0.2) & 
                (right_side[:, 1] < y_min + cloth_height * 0.6)
            ]
            if len(right_middle) > 0:
                right_armpit = right_middle[np.argmin(right_middle[:, 0])]
                keypoints['right_armpit'] = right_armpit.astype(float)
        
        # 5. Find bottom hem
        bottom_region = contour[contour[:, 1] > y_min + cloth_height * 0.85]
        self._log(f"Bottom region points: {len(bottom_region)}")
        if len(bottom_region) > 0:
            left_bottom = bottom_region[np.argmin(bottom_region[:, 0])]
            keypoints['left_bottom'] = left_bottom.astype(float)
            
            right_bottom = bottom_region[np.argmax(bottom_region[:, 0])]
            keypoints['right_bottom'] = right_bottom.astype(float)
            
            center_bottom = bottom_region[np.argmax(bottom_region[:, 1])]
            keypoints['bottom_center'] = center_bottom.astype(float)
        
        self._log(f"detect_cloth_keypoints: Found {len(keypoints)} keypoints: {list(keypoints.keys())}")
        return keypoints, cloth_mask

    def warp_cloth_to_body(self, cloth_image, cloth_mask, cloth_keypoints, human_keypoints, frame_shape):
        self._log("warp_cloth_to_body: Starting")
        h, w = frame_shape[:2]
        
        # Check if we need to flip left/right (mirroring issue)
        # Cloth: left shoulder should be on left side of image (lower x)
        # Human facing camera: their left shoulder is on RIGHT side of image (higher x)
        cloth_left_x = cloth_keypoints.get('left_shoulder', np.array([0, 0]))[0]
        cloth_right_x = cloth_keypoints.get('right_shoulder', np.array([0, 0]))[0]
        human_left_x = human_keypoints.get('left_shoulder', np.array([0, 0]))[0]
        human_right_x = human_keypoints.get('right_shoulder', np.array([0, 0]))[0]
        
        # Determine if mirroring is needed
        cloth_left_is_left = cloth_left_x < cloth_right_x  # True if cloth left shoulder is on left
        human_left_is_left = human_left_x < human_right_x  # True if human left shoulder is on left (back view)
        
        need_mirror = cloth_left_is_left != human_left_is_left
        self._log(f"Cloth left_x={cloth_left_x:.1f}, right_x={cloth_right_x:.1f}")
        self._log(f"Human left_x={human_left_x:.1f}, right_x={human_right_x:.1f}")
        self._log(f"Need mirror: {need_mirror}")
        
        src_pts = []
        dst_pts = []
        
        # If mirroring needed, swap left/right mappings
        if need_mirror:
            point_pairs = [
                ('left_shoulder', 'right_shoulder'),   # cloth left -> human right
                ('right_shoulder', 'left_shoulder'),   # cloth right -> human left
                ('left_bottom', 'right_hip'),
                ('right_bottom', 'left_hip'),
                ('left_sleeve_end', 'right_sleeve_end'),
                ('right_sleeve_end', 'left_sleeve_end'),
            ]
        else:
            point_pairs = [
                ('left_shoulder', 'left_shoulder'),
                ('right_shoulder', 'right_shoulder'),
                ('left_bottom', 'left_hip'),
                ('right_bottom', 'right_hip'),
                ('left_sleeve_end', 'left_sleeve_end'),
                ('right_sleeve_end', 'right_sleeve_end'),
            ]
        
        for cloth_key, human_key in point_pairs:
            if cloth_key in cloth_keypoints and human_key in human_keypoints:
                src_pt = cloth_keypoints[cloth_key].copy()
                dst_pt = human_keypoints[human_key].copy()
                
                if 'hip' in human_key:
                    dst_pt = dst_pt + np.array([0, 30])
                
                src_pts.append(src_pt)
                dst_pts.append(dst_pt)
                self._log(f"  Mapping {cloth_key} -> {human_key}: {src_pt} -> {dst_pt}")
        
        # Add armpit points (also swap if mirroring)
        if need_mirror:
            if 'left_armpit' in cloth_keypoints:
                src_pts.append(cloth_keypoints['left_armpit'].copy())
                armpit_pos = (human_keypoints['right_shoulder'] + human_keypoints['right_hip']) / 2
                armpit_pos[0] = human_keypoints['right_shoulder'][0]
                dst_pts.append(armpit_pos)
            
            if 'right_armpit' in cloth_keypoints:
                src_pts.append(cloth_keypoints['right_armpit'].copy())
                armpit_pos = (human_keypoints['left_shoulder'] + human_keypoints['left_hip']) / 2
                armpit_pos[0] = human_keypoints['left_shoulder'][0]
                dst_pts.append(armpit_pos)
        else:
            if 'left_armpit' in cloth_keypoints:
                src_pts.append(cloth_keypoints['left_armpit'].copy())
                armpit_pos = (human_keypoints['left_shoulder'] + human_keypoints['left_hip']) / 2
                armpit_pos[0] = human_keypoints['left_shoulder'][0]
                dst_pts.append(armpit_pos)
            
            if 'right_armpit' in cloth_keypoints:
                src_pts.append(cloth_keypoints['right_armpit'].copy())
                armpit_pos = (human_keypoints['right_shoulder'] + human_keypoints['right_hip']) / 2
                armpit_pos[0] = human_keypoints['right_shoulder'][0]
                dst_pts.append(armpit_pos)
        
        # Add neck point (center, no swap needed)
        if 'neck' in cloth_keypoints and 'neck' in human_keypoints:
            src_pts.append(cloth_keypoints['neck'].copy())
            dst_pts.append(human_keypoints['neck'].copy())
        
        src_pts = np.float32(src_pts)
        dst_pts = np.float32(dst_pts)
        
        self._log(f"warp_cloth_to_body: {len(src_pts)} point pairs")
        
        if len(src_pts) < 3:
            self._log("warp_cloth_to_body: Not enough points!")
            return None, None
        
        # Use TPS (Thin Plate Spline) for smooth warping, fallback to perspective
        if len(src_pts) >= 4:
            self._log("Using TPS warp")
            try:
                # Try TPS first for smoother results
                tps = cv2.createThinPlateSplineShapeTransformer()
                
                # TPS needs points in specific format
                src_pts_tps = src_pts.reshape(1, -1, 2)
                dst_pts_tps = dst_pts.reshape(1, -1, 2)
                
                matches = [cv2.DMatch(i, i, 0) for i in range(len(src_pts))]
                
                tps.estimateTransformation(dst_pts_tps, src_pts_tps, matches)
                
                warped_cloth = tps.warpImage(cloth_image)
                warped_mask = tps.warpImage(cloth_mask)
                
                # Resize if needed
                if warped_cloth.shape[:2] != (h, w):
                    warped_cloth = cv2.resize(warped_cloth, (w, h))
                    warped_mask = cv2.resize(warped_mask, (w, h))
                    
            except Exception as e:
                self._log(f"TPS warp failed: {e}, trying perspective")
                # Fallback to perspective with 4 main points (shoulders + hips)
                try:
                    matrix = cv2.getPerspectiveTransform(src_pts[:4], dst_pts[:4])
                    warped_cloth = cv2.warpPerspective(cloth_image, matrix, (w, h),
                                                       flags=cv2.INTER_LINEAR,
                                                       borderMode=cv2.BORDER_CONSTANT)
                    warped_mask = cv2.warpPerspective(cloth_mask, matrix, (w, h),
                                                      flags=cv2.INTER_LINEAR,
                                                      borderMode=cv2.BORDER_CONSTANT)
                except Exception as e2:
                    self._log(f"Perspective also failed: {e2}, using homography")
                    # Ultimate fallback: find homography
                    matrix, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC)
                    warped_cloth = cv2.warpPerspective(cloth_image, matrix, (w, h))
                    warped_mask = cv2.warpPerspective(cloth_mask, matrix, (w, h))
        else:
            self._log("Using affine warp (3 points)")
            matrix = cv2.getAffineTransform(src_pts[:3], dst_pts[:3])
            warped_cloth = cv2.warpAffine(cloth_image, matrix, (w, h),
                                          flags=cv2.INTER_LINEAR,
                                          borderMode=cv2.BORDER_CONSTANT,
                                          borderValue=(0, 0, 0))
            warped_mask = cv2.warpAffine(cloth_mask, matrix, (w, h),
                                         flags=cv2.INTER_LINEAR,
                                         borderMode=cv2.BORDER_CONSTANT,
                                         borderValue=0)
        
        self._log(f"warp_cloth_to_body: warped_cloth shape = {warped_cloth.shape if warped_cloth is not None else None}")
        self._log(f"warp_cloth_to_body: warped_mask non-zero = {np.count_nonzero(warped_mask) if warped_mask is not None else 0}")
        return warped_cloth, warped_mask

    def _piecewise_affine_warp(self, src_img, src_mask, src_pts, dst_pts, output_size):
        self._log("_piecewise_affine_warp: Starting")
        w, h = output_size
        
        src_h, src_w = src_img.shape[:2]
        
        corners_src = np.float32([
            [0, 0], [src_w-1, 0], [src_w-1, src_h-1], [0, src_h-1]
        ])
        corners_dst = np.float32([
            [0, 0], [w-1, 0], [w-1, h-1], [0, h-1]
        ])
        
        all_src = np.vstack([src_pts, corners_src])
        all_dst = np.vstack([dst_pts, corners_dst])
        
        self._log(f"Total points for triangulation: {len(all_dst)}")
        
        # Triangulate
        rect = (0, 0, w, h)
        subdiv = cv2.Subdiv2D(rect)
        
        valid_points = 0
        for pt in all_dst:
            try:
                # Clamp to valid range
                px = max(0, min(w-1, pt[0]))
                py = max(0, min(h-1, pt[1]))
                subdiv.insert((float(px), float(py)))
                valid_points += 1
            except Exception as e:
                self._log(f"Failed to insert point {pt}: {e}")
        
        self._log(f"Inserted {valid_points} points into Subdiv2D")
        
        triangles = subdiv.getTriangleList()
        self._log(f"Created {len(triangles)} triangles")
        
        warped_img = np.zeros((h, w, 3), dtype=np.uint8)
        warped_mask = np.zeros((h, w), dtype=np.uint8)
        
        valid_triangles = 0
        for tri in triangles:
            dst_tri = np.array([
                [tri[0], tri[1]],
                [tri[2], tri[3]],
                [tri[4], tri[5]]
            ], dtype=np.float32)
            
            if not self._triangle_in_rect(dst_tri, rect):
                continue
            
            # Find corresponding source triangle
            src_tri = []
            for pt in dst_tri:
                dists = np.linalg.norm(all_dst - pt, axis=1)
                idx = np.argmin(dists)
                src_tri.append(all_src[idx])
            src_tri = np.array(src_tri, dtype=np.float32)
            
            try:
                self._warp_triangle(src_img, warped_img, src_tri, dst_tri)
                self._warp_triangle(
                    src_mask[:, :, np.newaxis] if len(src_mask.shape) == 2 else src_mask,
                    warped_mask[:, :, np.newaxis] if len(warped_mask.shape) == 2 else warped_mask,
                    src_tri, dst_tri
                )
                valid_triangles += 1
            except Exception as e:
                pass  # Skip problematic triangles
        
        self._log(f"Warped {valid_triangles} triangles successfully")
        
        if len(warped_mask.shape) == 3:
            warped_mask = warped_mask[:, :, 0]
        
        return warped_img, warped_mask

    def _triangle_in_rect(self, tri, rect):
        x, y, w, h = rect
        for pt in tri:
            if pt[0] < x or pt[0] >= x + w or pt[1] < y or pt[1] >= y + h:
                return False
        return True

    def _warp_triangle(self, src_img, dst_img, src_tri, dst_tri):
        src_rect = cv2.boundingRect(src_tri.astype(np.int32))
        dst_rect = cv2.boundingRect(dst_tri.astype(np.int32))
        
        src_tri_offset = src_tri - np.array([src_rect[0], src_rect[1]])
        dst_tri_offset = dst_tri - np.array([dst_rect[0], dst_rect[1]])
        
        # Check for degenerate triangles
        if cv2.contourArea(src_tri_offset.astype(np.int32)) < 1:
            return
        if cv2.contourArea(dst_tri_offset.astype(np.int32)) < 1:
            return
        
        matrix = cv2.getAffineTransform(
            src_tri_offset.astype(np.float32),
            dst_tri_offset.astype(np.float32)
        )
        
        x, y, w, h = src_rect
        if x < 0 or y < 0 or x + w > src_img.shape[1] or y + h > src_img.shape[0]:
            return
        if w <= 0 or h <= 0:
            return
        
        src_crop = src_img[y:y+h, x:x+w]
        
        dst_w, dst_h = dst_rect[2], dst_rect[3]
        if dst_w <= 0 or dst_h <= 0:
            return
            
        warped = cv2.warpAffine(src_crop, matrix, (dst_w, dst_h),
                                flags=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_REFLECT_101)
        
        mask = np.zeros((dst_h, dst_w), dtype=np.uint8)
        cv2.fillConvexPoly(mask, dst_tri_offset.astype(np.int32), 255)
        
        dx, dy = dst_rect[0], dst_rect[1]
        if dx < 0 or dy < 0 or dx + dst_w > dst_img.shape[1] or dy + dst_h > dst_img.shape[0]:
            return
        
        dst_region = dst_img[dy:dy+dst_h, dx:dx+dst_w]
        
        if len(warped.shape) == 2:
            warped = warped[:, :, np.newaxis]
        if len(dst_region.shape) == 2:
            dst_region = dst_region[:, :, np.newaxis]
        
        mask_3ch = mask[:, :, np.newaxis] / 255.0
        blended = (warped * mask_3ch + dst_region * (1 - mask_3ch)).astype(np.uint8)
        
        if blended.shape[-1] == 1:
            dst_img[dy:dy+dst_h, dx:dx+dst_w] = blended[:, :, 0]
        else:
            dst_img[dy:dy+dst_h, dx:dx+dst_w] = blended

    def apply_cloth_overlay(self, frame, cloth_image, detected_mask, landmarks):
        self._log("=" * 60)
        self._log("apply_cloth_overlay: Starting")
        self._log("=" * 60)
        
        try:
            h, w = frame.shape[:2]
            self._log(f"Frame shape: {frame.shape}")
            self._log(f"Cloth image shape: {cloth_image.shape}")
            self._log(f"Detected mask shape: {detected_mask.shape}")
            
            # Resize cloth to match frame
            self._log("Resizing cloth image to match frame")
            cloth_image = cv2.resize(cloth_image, (w, h), interpolation=cv2.INTER_LINEAR)
            self._log(f"Resized cloth shape: {cloth_image.shape}")

            # Detect cloth keypoints
            self._log("Detecting cloth keypoints...")
            cloth_keypoints, cloth_mask = self.detect_cloth_keypoints(cloth_image)
            
            if cloth_keypoints is None:
                self._log("No cloth keypoints found, using simple overlay")
                return self._simple_overlay(frame, cloth_image, detected_mask)
            
            # Get human keypoints
            self._log("Getting human keypoints...")
            human_keypoints = self.get_human_keypoints(landmarks, frame.shape, cloth_keypoints)
            
            if human_keypoints is None:
                self._log("No human keypoints found, using simple overlay")
                return self._simple_overlay(frame, cloth_image, detected_mask)
            
            # Warp cloth to body
            self._log("Warping cloth to body...")
            warped_cloth, warped_cloth_mask = self.warp_cloth_to_body(
                cloth_image, cloth_mask, cloth_keypoints, human_keypoints, frame.shape
            )
            
            if warped_cloth is None:
                self._log("Warping failed, using simple overlay")
                return self._simple_overlay(frame, cloth_image, detected_mask)
            
            self._log(f"Warped cloth shape: {warped_cloth.shape}")
            self._log(f"Warped mask shape: {warped_cloth_mask.shape}")
            self._log(f"Warped mask non-zero pixels: {np.count_nonzero(warped_cloth_mask)}")
            self._log(f"Detected mask non-zero pixels: {np.count_nonzero(detected_mask)}")
            
            # Save intermediate for debugging
            cv2.imwrite("debug_warped_cloth.jpg", warped_cloth)
            cv2.imwrite("debug_warped_mask.jpg", warped_cloth_mask)
            
            # Combine masks - use detected mask as primary since it's more accurate
            # But only where warped cloth has content
            self._log("Combining masks...")
            
            # Option 1: Use detected mask only (most reliable)
            # combined_mask = detected_mask.copy()
            
            # Option 2: Use warped mask only (follows the warped cloth)
            # combined_mask = warped_cloth_mask.copy()
            
            # Option 3: Use union of both masks for maximum coverage
            # combined_mask = cv2.bitwise_or(detected_mask, warped_cloth_mask)
            
            # Option 4: Use intersection but dilate warped mask first
            warped_mask_dilated = cv2.dilate(warped_cloth_mask, 
                                              cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (30, 30)),
                                              iterations=2)
            combined_mask = cv2.bitwise_and(detected_mask, warped_mask_dilated)
            
            self._log(f"Combined mask non-zero: {np.count_nonzero(combined_mask)}")
            
            # If combined mask is too small, fall back to detected mask
            if np.count_nonzero(combined_mask) < np.count_nonzero(detected_mask) * 0.3:
                self._log("Combined mask too small, using detected mask instead")
                combined_mask = detected_mask.copy()
            
            combined_mask = cv2.GaussianBlur(combined_mask, (15, 15), 0)
            cv2.imwrite("debug_combined_mask.jpg", combined_mask)
            
            # Blend
            self._log("Blending...")
            mask_normalized = combined_mask.astype(np.float32) / 255.0
            mask_3ch = np.stack([mask_normalized] * 3, axis=-1)
            
            result = (warped_cloth * mask_3ch + frame * (1 - mask_3ch)).astype(np.uint8)
            
            self._log("apply_cloth_overlay: Complete!")
            return result
            
        except Exception as e:
            self._log(f"ERROR in apply_cloth_overlay: {e}")
            traceback.print_exc()
            return frame

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
        cloth_full[y:y+h_box, x:x+w_box] = cloth_resized
        
        mask_normalized = cloth_mask.astype(np.float32) / 255.0
        mask_3ch = np.stack([mask_normalized] * 3, axis=-1)
        
        result = (cloth_full * mask_3ch + frame * (1 - mask_3ch)).astype(np.uint8)
        return result

    def visualize_cloth_keypoints(self, cloth_image):
        result = cloth_image.copy()
        keypoints, mask = self.detect_cloth_keypoints(cloth_image)
        
        if keypoints is None:
            return result, mask
        
        colors = {
            'neck': (0, 255, 255),
            'left_shoulder': (0, 255, 0),
            'right_shoulder': (0, 255, 0),
            'left_armpit': (255, 0, 255),
            'right_armpit': (255, 0, 255),
            'left_bottom': (255, 0, 0),
            'right_bottom': (255, 0, 0),
            'bottom_center': (255, 128, 0),
            'left_sleeve_end': (0, 128, 255),
            'right_sleeve_end': (0, 128, 255),
        }
        
        for name, point in keypoints.items():
            pt = tuple(point.astype(int))
            color = colors.get(name, (255, 255, 255))
            cv2.circle(result, pt, 8, color, -1)
            cv2.putText(result, name, (pt[0]+5, pt[1]-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        connections = [
            ('left_shoulder', 'right_shoulder', (0, 255, 0)),
            ('left_shoulder', 'left_sleeve_end', (0, 200, 255)),
            ('right_shoulder', 'right_sleeve_end', (0, 200, 255)),
            ('left_bottom', 'right_bottom', (255, 0, 0)),
        ]
        
        for start, end, color in connections:
            if start in keypoints and end in keypoints:
                cv2.line(result, 
                        tuple(keypoints[start].astype(int)),
                        tuple(keypoints[end].astype(int)),
                        color, 2)
        
        return result, mask

    def visualize_human_keypoints(self, frame, landmarks, cloth_keypoints=None):
        result = frame.copy()
        keypoints = self.get_human_keypoints(landmarks, frame.shape, cloth_keypoints)
        
        if keypoints is None:
            return result
        
        colors = {
            'neck': (0, 255, 255),
            'left_shoulder': (0, 255, 0),
            'right_shoulder': (0, 255, 0),
            'left_hip': (255, 0, 0),
            'right_hip': (255, 0, 0),
            'waist_center': (255, 128, 0),
            'left_elbow': (128, 255, 128),
            'right_elbow': (128, 255, 128),
            'left_wrist': (64, 255, 64),
            'right_wrist': (64, 255, 64),
            'left_sleeve_end': (0, 128, 255),
            'right_sleeve_end': (0, 128, 255),
        }
        
        for name, point in keypoints.items():
            if '_vis' in name:
                continue
            pt = tuple(point.astype(int))
            color = colors.get(name, (255, 255, 255))
            cv2.circle(result, pt, 8, color, -1)
            cv2.putText(result, name, (pt[0]+5, pt[1]-5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        connections = [
            ('left_shoulder', 'left_elbow', (128, 255, 128)),
            ('left_elbow', 'left_wrist', (128, 255, 128)),
            ('right_shoulder', 'right_elbow', (128, 255, 128)),
            ('right_elbow', 'right_wrist', (128, 255, 128)),
            ('left_shoulder', 'right_shoulder', (0, 255, 0)),
            ('left_hip', 'right_hip', (255, 0, 0)),
            ('left_shoulder', 'left_sleeve_end', (0, 128, 255)),
            ('right_shoulder', 'right_sleeve_end', (0, 128, 255)),
        ]
        
        for start, end, color in connections:
            if start in keypoints and end in keypoints:
                pt1 = tuple(keypoints[start].astype(int))
                pt2 = tuple(keypoints[end].astype(int))
                cv2.line(result, pt1, pt2, color, 2)
        
        return result

    def cleanup(self):
        if hasattr(self, "pose"):
            self.pose.close()
