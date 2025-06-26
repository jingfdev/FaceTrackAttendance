import cv2
import numpy as np
import os
from typing import List, Tuple, Optional

class FaceDetector:
    def __init__(self):
        """Initialize the face detector with OpenCV's Haar Cascade and DNN face detection"""
        # Load the pre-trained Haar Cascade face detection model
        cascade_path = '/home/runner/workspace/.pythonlibs/lib/python3.11/site-packages/cv2/data/haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Try to load DNN face detection model for better accuracy
        try:
            # Download and load DNN face detection model
            self.net = cv2.dnn.readNetFromTensorflow('opencv_face_detector_uint8.pb', 'opencv_face_detector.pbtxt')
            self.use_dnn = True
            print("Loaded DNN face detection model")
        except Exception as e:
            print(f"DNN model not available, using Haar Cascade: {e}")
            self.net = None
            self.use_dnn = False
        
        # Initialize the face recognizer if available
        self.has_face_recognizer = False
        self.face_recognizer = None
        print("Using histogram-based face comparison (OpenCV face module not required)")
        
    def detect_faces_in_image(self, image_path: str) -> bool:
        """
        Detect faces in an image file using DNN or Haar Cascade
        
        Args:
            image_path: Path to the image file
            
        Returns:
            bool: True if at least one face is detected, False otherwise
        """
        try:
            # Read the image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image from {image_path}")
            
            # Try DNN face detection first if available
            if self.use_dnn and self.net is not None:
                try:
                    h, w = image.shape[:2]
                    blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300), [104, 117, 123])
                    self.net.setInput(blob)
                    detections = self.net.forward()
                    
                    # Check for face detections with confidence > 0.5
                    for i in range(detections.shape[2]):
                        confidence = detections[0, 0, i, 2]
                        if confidence > 0.5:
                            return True
                except Exception as e:
                    print(f"DNN detection failed: {e}, falling back to Haar Cascade")
            
            # Fallback to Haar Cascade
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces with multiple scale factors for better detection
            for scale_factor in [1.1, 1.2, 1.3]:
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=scale_factor,
                    minNeighbors=5,
                    minSize=(30, 30),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                if len(faces) > 0:
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error detecting faces in {image_path}: {str(e)}")
            return False
    
    def extract_face_features(self, image_path: str) -> Optional[np.ndarray]:
        """
        Extract face features from an image for recognition
        
        Args:
            image_path: Path to the image file
            
        Returns:
            numpy.ndarray: Face region as grayscale array, or None if no face found
        """
        try:
            # Read the image
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            if len(faces) == 0:
                return None
            
            # Take the first (largest) face
            x, y, w, h = faces[0]
            face_region = gray[y:y+h, x:x+w]
            
            # Resize to standard size for comparison
            face_region = cv2.resize(face_region, (100, 100))
            
            return face_region
            
        except Exception as e:
            print(f"Error extracting face features from {image_path}: {str(e)}")
            return None
    
    def compare_faces(self, image1_path: str, image2_path: str) -> float:
        """
        Compare two face images and return similarity score
        
        Args:
            image1_path: Path to first image
            image2_path: Path to second image
            
        Returns:
            float: Similarity score between 0.0 and 1.0 (higher means more similar)
        """
        try:
            # Extract face features from both images
            face1 = self.extract_face_features(image1_path)
            face2 = self.extract_face_features(image2_path)
            
            if face1 is None or face2 is None:
                return 0.0
            
            # Calculate histogram comparison
            hist1 = cv2.calcHist([face1], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([face2], [0], None, [256], [0, 256])
            
            # Use correlation method for comparison
            correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            # Also use template matching for additional comparison
            result = cv2.matchTemplate(face1, face2, cv2.TM_CCOEFF_NORMED)
            template_score = float(np.max(result))
            
            # Combine both scores (weighted average)
            combined_score = (float(correlation) * 0.6) + (template_score * 0.4)
            
            # Ensure score is between 0 and 1
            return max(0.0, min(1.0, combined_score))
            
        except Exception as e:
            print(f"Error comparing faces: {str(e)}")
            return 0.0
    
    def detect_faces_in_frame(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in a video frame
        
        Args:
            frame: OpenCV frame (numpy array)
            
        Returns:
            List of tuples: Each tuple contains (x, y, width, height) of detected face
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces with multiple scale factors for better detection
            faces = []
            for scale_factor in [1.1, 1.2, 1.3]:
                detected = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=scale_factor,
                    minNeighbors=5,
                    minSize=(50, 50),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                if len(detected) > 0:
                    faces = detected
                    break
            
            return [(x, y, w, h) for x, y, w, h in faces]
            
        except Exception as e:
            print(f"Error detecting faces in frame: {str(e)}")
            return []
    
    def detect_and_recognize_in_image(self, image_path: str) -> dict:
        """
        Detect faces and return detailed information including coordinates
        
        Args:
            image_path: Path to the image file
            
        Returns:
            dict: Detection results with face coordinates and recognition info
        """
        try:
            # Read the image
            image = cv2.imread(image_path)
            if image is None:
                return {'success': False, 'error': 'Could not read image'}
            
            # Detect faces and get coordinates
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(50, 50),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            if len(faces) == 0:
                return {'success': False, 'error': 'No faces detected'}
            
            # Return face coordinates for drawing bounding boxes
            face_data = []
            for (x, y, w, h) in faces:
                face_data.append({
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h)
                })
            
            return {
                'success': True,
                'faces': face_data,
                'total_faces': len(faces)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def draw_face_rectangles(self, frame: np.ndarray, faces: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """
        Draw rectangles around detected faces
        
        Args:
            frame: OpenCV frame
            faces: List of face coordinates
            
        Returns:
            numpy.ndarray: Frame with rectangles drawn around faces
        """
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        
        return frame
