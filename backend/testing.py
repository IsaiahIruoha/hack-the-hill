import torch
import cv2
from ultralytics import YOLO

# Load YOLOv8x model (extra-large pre-trained)
model = YOLO('yolov8x.pt')

# Capture video from webcam or RealSense (for now, we use webcam)
cap = cv2.VideoCapture(0)  # Change '0' to the RealSense video index if needed

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run YOLOv8 model on the current frame
    results = model(frame)

    # Results visualization (draw bounding boxes on the frame)
    annotated_frame = results[0].plot()

    # Display the frame with detected objects
    cv2.imshow('YOLOv8 Detection', annotated_frame)

    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture and close windows
cap.release()
cv2.destroyAllWindows()
