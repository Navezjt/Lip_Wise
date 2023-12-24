import cv2
import math
import os
import file_check

import mediapipe as mp
import numpy as np

from basicsr.utils.download_util import load_file_from_url

class media_preprocess:

    """
    INDEXES:
        0-477: Landmarks:
        478-479: Bounding box:
            478: Top left corner
            479: height, width
        480-485: Keypoints:
            480: Left eye
            481: Right eye
            482: Nose
            483: Mouth left
            484: Mouth right
            485: Mouth center
    """

    def __init__(self):
        self.npy_directory = file_check.NPY_FILES_DIR
        self.weights_directory = file_check.WEIGHTS_DIR

        self.detector_model_path = os.path.join(file_check.MP_WEIGHTS_DIR, 'blaze_face_short_range.tflite')
        self.landmarker_model_path = os.path.join(file_check.MP_WEIGHTS_DIR, "face_landmarker.task")

    def preprocess_image(self, image_path):

        frame = cv2.imread(image_path)
        # Convert frame to RGB and convert to MediaPipe image
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        
        # Initialize mediapipe
        BaseOptions = mp.tasks.BaseOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        FaceLandmarker = mp.tasks.vision.FaceLandmarker
        FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions

        FaceDetector = mp.tasks.vision.FaceDetector
        FaceDetectorOptions = mp.tasks.vision.FaceDetectorOptions

        # Create a face detector instance with the image mode:
        options_det = FaceDetectorOptions(
            base_options=BaseOptions(model_asset_path=self.detector_model_path),
            min_detection_confidence=0.5,
            running_mode=VisionRunningMode.IMAGE)


        options_lan = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.landmarker_model_path),
            min_face_detection_confidence=0.5,
            running_mode=VisionRunningMode.IMAGE)
        
        video_landmarks = np.zeros((1, 486, 2)).astype(np.float64)
        
        with FaceLandmarker.create_from_options(options_lan) as landmarker,FaceDetector.create_from_options(options_det) as detector:
            # Run face detector and face landmark models in IMAGE mode
            result_landmarker = landmarker.detect(mp_frame)
            result_detection = detector.detect(mp_frame)
        
        # Get data ready to be saved
        if len(result_detection.detections) > 0 and len(result_landmarker.face_landmarks) > 0:
            # Get bounding box
            bbox = result_detection.detections[0].bounding_box
            bbox_np = (np.array([bbox.origin_x, bbox.origin_y, bbox.width, bbox.height]).reshape(2, 2) / [frame.shape[1], frame.shape[0]]).astype(np.float64)

            # Get Keypoints
            kp = result_detection.detections[0].keypoints
            kp_np = np.array([[k.x, k.y] for k in kp]).astype(np.float64)

            # Get landmarks
            landmarks_np = np.array([[i.x, i.y] for i in result_landmarker.face_landmarks[0]]).astype(np.float64)

            # Concatenate landmarks, bbox and keypoints. This is the data that will be saved.
            data = np.vstack((landmarks_np, bbox_np, kp_np)).astype(np.float64)
        else:
            data = np.zeros((486,2)).astype(np.float64)

        video_landmarks[0] = data

        # Save video landmarks
        np.save(os.path.join(self.npy_directory,'video_landmarks.npy'), video_landmarks)

    def preprocess_video(self, video_path):

        video = cv2.VideoCapture(video_path)

        # Get video properties
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"Frames to process: {frame_count}")

        # Initialize mediapipe
        BaseOptions = mp.tasks.BaseOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        FaceLandmarker = mp.tasks.vision.FaceLandmarker
        FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions

        FaceDetector = mp.tasks.vision.FaceDetector
        FaceDetectorOptions = mp.tasks.vision.FaceDetectorOptions

        # Create a face detector instance with the image mode:
        options_det = FaceDetectorOptions(
            base_options=BaseOptions(model_asset_path=self.detector_model_path),
            min_detection_confidence=0.5,
            running_mode=VisionRunningMode.IMAGE)


        options_lan = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self.landmarker_model_path),
            min_face_detection_confidence=0.5,
            running_mode=VisionRunningMode.IMAGE)

        frame_no = 0
        no_face_index = []
        video_landmarks = np.zeros((frame_count, 486, 2)).astype(np.float64)

        with FaceLandmarker.create_from_options(options_lan) as landmarker,FaceDetector.create_from_options(options_det) as detector:
            while video.isOpened():

                ret, frame = video.read()
                
                if not ret:
                    break
                
                # Get frame timestamp
                timestamp = int(video.get(cv2.CAP_PROP_POS_MSEC))

                # Convert frame to RGB and convert to MediaPipe image
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

                # Run face detector and face landmark models in VIDEO mode
                # result_landmarker = landmarker.detect_for_video(mp_frame, timestamp)
                # result_detection = detector.detect_for_video(mp_frame, timestamp)

                # Run face detector and face landmark models in IMAGE mode
                result_landmarker = landmarker.detect(mp_frame)
                result_detection = detector.detect(mp_frame)

                # Get data ready to be saved
                print(f"Frame {frame_no} processing")
                print(f"Face Detected: {len(result_landmarker.face_landmarks) > 0}")
                
                if len(result_detection.detections) > 0 and len(result_landmarker.face_landmarks) > 0:
                    # Get bounding box
                    bbox = result_detection.detections[0].bounding_box
                    bbox_np = (np.array([bbox.origin_x, bbox.origin_y, bbox.width, bbox.height]).reshape(2, 2) / [width, height]).astype(np.float64)

                    # Get Keypoints
                    kp = result_detection.detections[0].keypoints
                    kp_np = np.array([[k.x, k.y] for k in kp]).astype(np.float64)

                    # Get landmarks
                    landmarks_np = np.array([[i.x, i.y] for i in result_landmarker.face_landmarks[0]]).astype(np.float64)

                    # Concatenate landmarks, bbox and keypoints. This is the data that will be saved.
                    data = np.vstack((landmarks_np, bbox_np, kp_np)).astype(np.float64)
                else:
                    data = np.zeros((486,2)).astype(np.float64)
                    no_face_index.append(frame_no)

                # Append data
                print(f"Frame {frame_no} processed")
                video_landmarks[frame_no] = data
            
                # Increment frame number
                frame_no += 1
            # Save video landmarks
            np.save(os.path.join(self.npy_directory,'video_landmarks.npy'), video_landmarks)
            np.savetxt(os.path.join(self.npy_directory,'no_face_index.txt'), np.array(no_face_index), fmt='%d')

            # Release video
            video.release()

    def gen_face_route_index(self):
            """
            Generates and saves the face route index as an npy array.

            The face route index is obtained by sorting the face oval indices in a specific order.

            Returns:
                None
            """
            # Load face mesh model
            mp_face_mesh = mp.solutions.face_mesh
            face_oval = mp_face_mesh.FACEMESH_FACE_OVAL

            index = np.array(list(face_oval))

            # Sort the array
            i = 0
            while i < len(index) - 1:
                # Find the index of the row where the first element is the same as the second element of the current row
                next_index = np.where(index[:, 0] == index[i, 1])[0]
                if next_index.size>0 and next_index[0] != i + 1:
                    # Swap rows
                    index[[i + 1, next_index[0]]] = index[[next_index[0], i + 1]]
                i += 1

            # Save index as npy array
            np.save(os.path.join(self.npy_directory, 'face_route_index.npy'), index)

class FaceHelpers:

    def __init__(self):
        self.video_landmarks_path = os.path.join(file_check.NPY_FILES_DIR,'video_landmarks.npy')
        self.landmarks_all = np.load(self.video_landmarks_path)

    def gen_face_mask(self, img, frame_no=0):
        """
        Generates the face mask using face oval indices from face oval landmarks.

        Args:
            img: Image from which the face mask is to be generated.
            frame_no: The frame number of the image.
        
        Returns:
            The face mask in bool format to be fed in the paste back function or extract_face function.
        """
        index = np.load(os.path.join(self.npy_directory, 'face_route_index.npy'))

        coords = list()
        for source_idx, target_idx in index:
            source = self.landmarks_all[frame_no][source_idx]
            target = self.landmarks_all[frame_no][target_idx]
            coords.append([source[0], source[1]])
            coords.append([target[0], target[1]])

        coords = np.array(coords)
        coords = (coords*[img.shape[1], img.shape[0]]).astype(np.int32)

        mask = np.zeros((img.shape[0], img.shape[1]))
        mask = cv2.fillConvexPoly(mask, coords, 1)
        mask = mask.astype(bool)

        return mask

    def extrtact_face(self, img, frame_no=0):
        """
        Extracts the face from the image (Image with only face and black background).

        Args:
            img: Image from which the face is to be extracted.

        Returns:
            Only The face.
        """
        mask = self.gen_face_mask(img, frame_no)
        face = np.zeros_like(img)
        face[mask] = img[mask]

        return face

    def findEuclideanDistance(self, source_representation, test_representation):
        euclidean_distance = source_representation - test_representation
        euclidean_distance = np.sum(np.multiply(euclidean_distance, euclidean_distance))
        euclidean_distance = np.sqrt(euclidean_distance)
        return euclidean_distance

    #this function is inspired from the deepface repository: https://github.com/serengil/deepface/blob/master/deepface/commons/functions.py
    def alignment_procedure(self, img, frame_no=0):

        left_eye = self.landmarks_all[frame_no][480] # Left eye index is 480
        right_eye = self.landmarks_all[frame_no][481] # Right eye index is 481

        #this function aligns given face in img based on left and right eye coordinates

        #left eye is the eye appearing on the left (right eye of the person)
        #left top point is (0, 0)

        left_eye_x, left_eye_y = left_eye
        right_eye_x, right_eye_y = right_eye

        #-----------------------
        #decide the image is inverse

        center_eyes = (int((left_eye_x + right_eye_x) / 2), int((left_eye_y + right_eye_y) / 2))

        center = (img.shape[1] / 2, img.shape[0] / 2)

        output_size = (img.shape[1], img.shape[0])
        

        #-----------------------
        #find rotation direction

        if left_eye_y > right_eye_y:
            point_3rd = (right_eye_x, left_eye_y)
            direction = -1 #rotate same direction to clock
        else:
            point_3rd = (left_eye_x, right_eye_y)
            direction = 1 #rotate inverse direction of clock

        #-----------------------
        #find length of triangle edges

        a = self.findEuclideanDistance(np.array(left_eye), np.array(point_3rd))
        b = self.findEuclideanDistance(np.array(right_eye), np.array(point_3rd))
        c = self.findEuclideanDistance(np.array(right_eye), np.array(left_eye))

        #-----------------------

        #apply cosine rule

        if b != 0 and c != 0: #this multiplication causes division by zero in cos_a calculation

            cos_a = (b*b + c*c - a*a)/(2*b*c)
            
            #PR15: While mathematically cos_a must be within the closed range [-1.0, 1.0], floating point errors would produce cases violating this
            #In fact, we did come across a case where cos_a took the value 1.0000000169176173, which lead to a NaN from the following np.arccos step
            cos_a = min(1.0, max(-1.0, cos_a))
            
            
            angle = np.arccos(cos_a) #angle in radian
            angle = (angle * 180) / math.pi #radian to degree

            #-----------------------
            #rotate base image

            if direction == -1:
                angle = 90 - angle

            # Get the rotation matrix
            M = cv2.getRotationMatrix2D(center, direction * angle, 1)

            # Perform the affine transformation to rotate the image
            img_rotated = cv2.warpAffine(img, M, output_size)

        return img_rotated, M  #return img and inverse afiine matrix anyway

    def warp_face(self, face, frame_no=0):
        print("Warping and aligning face...")
        face, M = self.alignment_procedure(face, frame_no)
        return face, M
        

    def paste_back(face, background, mask):
        """
        Pastes the face back on the background.

        Args:
            face: Full image with the face.
            background: The background on which the face is to be pasted.

        Returns:
            The background with the face pasted on it.
        """
        background[mask] = face[mask]
        return background