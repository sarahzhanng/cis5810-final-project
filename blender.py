import cv2
import numpy as np
import mediapipe as mp


class GarmentBlender:

    
    def __init__(self):
        """Initialize blender"""
        self.mp_pose = mp.solutions.pose
    
    def blend(self, frame, garment, cloth_mask, landmarks=None):
        h, w = frame.shape[:2]
        
        if landmarks is not None:
            warped_garment = self.improved_warp_with_pose(garment, cloth_mask, landmarks, (h, w))
        else:
            warped_garment = self.warp_to_mask_shape(garment, cloth_mask, (h, w))
        
        result = self.mask_based_replacement(frame, warped_garment, cloth_mask)
        
        return result
    
    def improved_warp_with_pose(self, garment, mask, landmarks, target_size):
        h, w = target_size
        landmarks_list = landmarks.landmark
        
        try:
            l_shoulder = landmarks_list[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            r_shoulder = landmarks_list[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            l_hip = landmarks_list[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            r_hip = landmarks_list[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            l_elbow = landmarks_list[self.mp_pose.PoseLandmark.LEFT_ELBOW.value]
            r_elbow = landmarks_list[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value]
            
            neck = landmarks_list[self.mp_pose.PoseLandmark.NOSE.value]
            
            neck_pt = np.array([neck.x * w, neck.y * h + 50])
            ls_pt = np.array([l_shoulder.x * w, l_shoulder.y * h])
            rs_pt = np.array([r_shoulder.x * w, r_shoulder.y * h])
            lh_pt = np.array([l_hip.x * w, l_hip.y * h])
            rh_pt = np.array([r_hip.x * w, r_hip.y * h])
            le_pt = np.array([l_elbow.x * w, l_elbow.y * h])
            re_pt = np.array([r_elbow.x * w, r_elbow.y * h])
            
        except Exception as e:
            print(f"Pose detection failed: {e}, using mask-based warping")
            return self.warp_to_mask_shape(garment, mask, target_size)
        
        gh, gw = garment.shape[:2]
        src_points = np.float32([
            [gw * 0.5, gh * 0.05],
            [gw * 0.3, gh * 0.08],
            [gw * 0.7, gh * 0.08],
            
            [gw * 0.15, gh * 0.12],
            [gw * 0.85, gh * 0.12],
            
            [gw * 0.25, gh * 0.30],
            [gw * 0.5, gh * 0.30],
            [gw * 0.75, gh * 0.30],
            
            [gw * 0.2, gh * 0.60],
            [gw * 0.5, gh * 0.60],
            [gw * 0.8, gh * 0.60],
            
            [gw * 0.05, gh * 0.25],
            [gw * 0.95, gh * 0.25],
        ])
        
        center_x = (ls_pt[0] + rs_pt[0]) / 2
        center_hip_x = (lh_pt[0] + rh_pt[0]) / 2
        center_hip_y = (lh_pt[1] + rh_pt[1]) / 2
        
        dst_points = np.float32([
            neck_pt,                          # Center neck
            (neck_pt + ls_pt) / 2,           # Left collar
            (neck_pt + rs_pt) / 2,           # Right collar
            
            ls_pt,                            # Left shoulder
            rs_pt,                            # Right shoulder
            
            (ls_pt + lh_pt) / 2,             # Left mid-torso
            [center_x, (ls_pt[1] + lh_pt[1]) / 2],  # Center mid-torso
            (rs_pt + rh_pt) / 2,             # Right mid-torso
            
            lh_pt,                            # Left hip
            [center_hip_x, center_hip_y],    # Center hip
            rh_pt,                            # Right hip
            
            le_pt,                            # Left sleeve
            re_pt,                            # Right sleeve
        ])
        
        warped = self.tps_warp(garment, src_points, dst_points, (h, w))
        
        return warped
    
    def tps_warp(self, image, src_points, dst_points, output_shape):
        h, w = output_shape
        
        subdiv = cv2.Subdiv2D((-1, -1, w+2, h+2))
        for point in dst_points:
            px = float(np.clip(point[0], -1, w+1))
            py = float(np.clip(point[1], -1, h+1))
            if np.isfinite(px) and np.isfinite(py):
                try:
                    subdiv.insert((px, py))
                except:
                    pass
        
        triangles = subdiv.getTriangleList()
        
        output = np.zeros((h, w, 3), dtype=np.uint8)
        
        for t in triangles:
            pt1 = (int(t[0]), int(t[1]))
            pt2 = (int(t[2]), int(t[3]))
            pt3 = (int(t[4]), int(t[5]))
            
            if (0 <= pt1[0] < w and 0 <= pt1[1] < h and
                0 <= pt2[0] < w and 0 <= pt2[1] < h and
                0 <= pt3[0] < w and 0 <= pt3[1] < h):
                
                triangle_dst = np.array([pt1, pt2, pt3], dtype=np.float32)
                
                center = triangle_dst.mean(axis=0)
                
                distances = np.linalg.norm(dst_points - center, axis=1)
                closest_idx = np.argmin(distances)
                
                src_center = src_points[closest_idx]
                
                gh, gw = image.shape[:2]
                scale_x = gw / w
                scale_y = gh / h
                
                triangle_src = np.array([
                    [pt1[0] * scale_x, pt1[1] * scale_y],
                    [pt2[0] * scale_x, pt2[1] * scale_y],
                    [pt3[0] * scale_x, pt3[1] * scale_y]
                ], dtype=np.float32)
                
                self.warp_triangle(image, output, triangle_src, triangle_dst)
        
        return output
    
    def warp_triangle(self, src, dst, src_tri, dst_tri):

        src_rect = cv2.boundingRect(src_tri)
        dst_rect = cv2.boundingRect(dst_tri)
        
        src_tri_cropped = []
        dst_tri_cropped = []
        
        for i in range(3):
            src_tri_cropped.append(((src_tri[i][0] - src_rect[0]), (src_tri[i][1] - src_rect[1])))
            dst_tri_cropped.append(((dst_tri[i][0] - dst_rect[0]), (dst_tri[i][1] - dst_rect[1])))
        
        src_cropped = src[src_rect[1]:src_rect[1] + src_rect[3], 
                          src_rect[0]:src_rect[0] + src_rect[2]]
        
        if src_cropped.size == 0:
            return
        
        warp_mat = cv2.getAffineTransform(
            np.float32(src_tri_cropped), 
            np.float32(dst_tri_cropped)
        )
        
        dst_cropped = cv2.warpAffine(
            src_cropped, warp_mat, 
            (dst_rect[2], dst_rect[3]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT_101
        )

        mask = np.zeros((dst_rect[3], dst_rect[2], 3), dtype=np.float32)
        cv2.fillConvexPoly(mask, np.int32(dst_tri_cropped), (1.0, 1.0, 1.0))
        
        try:
            y1, y2 = dst_rect[1], dst_rect[1] + dst_rect[3]
            x1, x2 = dst_rect[0], dst_rect[0] + dst_rect[2]
            
            if (y1 >= 0 and y2 <= dst.shape[0] and x1 >= 0 and x2 <= dst.shape[1] and
                mask.shape[0] == dst_cropped.shape[0] and mask.shape[1] == dst_cropped.shape[1]):
                dst[y1:y2, x1:x2] = dst[y1:y2, x1:x2] * (1 - mask) + dst_cropped * mask
        except:
            pass
    
    def warp_to_mask_shape(self, garment, mask, target_size):
        h, w = target_size

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return np.zeros((h, w, 3), dtype=np.uint8)
        
        main_contour = max(contours, key=cv2.contourArea)
        
        x, y, box_w, box_h = cv2.boundingRect(main_contour)
        
        if box_w > 0 and box_h > 0:
            margin = 1.1
            new_w = int(box_w * margin)
            new_h = int(box_h * margin)
            
            garment_resized = cv2.resize(garment, (new_w, new_h), 
                                        interpolation=cv2.INTER_LANCZOS4)
            
            warped = np.zeros((h, w, 3), dtype=np.uint8)
            
            offset_x = x - (new_w - box_w) // 2
            offset_y = y - (new_h - box_h) // 2
            
            y1 = max(0, offset_y)
            y2 = min(h, offset_y + new_h)
            x1 = max(0, offset_x)
            x2 = min(w, offset_x + new_w)
            
            gy1 = max(0, -offset_y)
            gy2 = gy1 + (y2 - y1)
            gx1 = max(0, -offset_x)
            gx2 = gx1 + (x2 - x1)
            
            if gy2 > gy1 and gx2 > gx1:
                warped[y1:y2, x1:x2] = garment_resized[gy1:gy2, gx1:gx2]
            
            return warped
        
        return np.zeros((h, w, 3), dtype=np.uint8)
    
    def mask_based_replacement(self, background, foreground, mask):
        if mask.shape[:2] != background.shape[:2]:
            mask = cv2.resize(mask, (background.shape[1], background.shape[0]))
        
        blend_mask = self.create_smooth_mask(mask)

        bg = background.astype(np.float32)
        fg = foreground.astype(np.float32)
        
        fg_adjusted = self.match_lighting(bg, fg, blend_mask)
        
        result = bg * (1 - blend_mask) + fg_adjusted * blend_mask
        
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        return result
    
    def create_smooth_mask(self, mask):

        smooth = mask.astype(np.float32) / 255.0
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
        inner = cv2.erode(mask, kernel, iterations=2)
        inner = inner.astype(np.float32) / 255.0
        
        outer = cv2.dilate(mask, kernel, iterations=2)
        outer = outer.astype(np.float32) / 255.0
        
        smooth = cv2.GaussianBlur(smooth, (31, 31), 10)
        
        smooth = np.maximum(smooth, inner)
        
        dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
        dist = cv2.normalize(dist, None, 0, 1, cv2.NORM_MINMAX)
        dist = cv2.GaussianBlur(dist, (15, 15), 0)
        
        smooth = smooth * 0.6 + dist * 0.4
        
        smooth = np.clip(smooth, 0, 1)
        
        smooth = np.stack([smooth] * 3, axis=2)
        
        return smooth
    
    def match_lighting(self, background, foreground, mask):
        
        mask_binary = (mask[:,:,0] > 0.5).astype(np.uint8)
        
        if mask_binary.sum() == 0:
            return foreground
        
        bg_mean = cv2.mean(background.astype(np.uint8), mask=mask_binary)[:3]
        
        fg_mean = cv2.mean(foreground.astype(np.uint8), mask=mask_binary)[:3]
        
        ratio = np.array(bg_mean) / (np.array(fg_mean) + 1e-6)
        
        ratio = np.clip(ratio, 0.7, 1.3)
        
        adjusted = foreground * ratio
        
        bg_gray = cv2.cvtColor(background.astype(np.uint8), cv2.COLOR_BGR2GRAY)
        bg_light = cv2.GaussianBlur(bg_gray, (51, 51), 0).astype(np.float32) / 255.0
        bg_light = np.stack([bg_light] * 3, axis=2)
        
        adjusted = adjusted * (0.8 + bg_light * 0.2)
        
        adjusted = np.clip(adjusted, 0, 255)
        
        return adjusted