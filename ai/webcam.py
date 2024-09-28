import numpy as np
import cv2
from ultralytics import YOLO

# Load the trained YOLOv8 model
model = YOLO('C:/Users/c1leu/OneDrive/Documents/GitHub/hack-the-hill-foresight/runs/detect/train/weights/best.pt')  # Replace with your YOLOv8 model path

# Configure the webcam (0 is the default camera, change it if you have multiple cameras)
cap = cv2.VideoCapture(0)

# Set desired resolution and FPS
desired_width = 1280  # You can adjust this value
desired_height = 720  # You can adjust this value
desired_fps = 60      # You can adjust this value

# Set camera resolution and FPS
cap.set(cv2.CAP_PROP_FRAME_WIDTH, desired_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, desired_height)
cap.set(cv2.CAP_PROP_FPS, desired_fps)

# Check if the webcam is opened correctly
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Define the codec and create VideoWriter object to save the output video
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec
out = cv2.VideoWriter('output.avi', fourcc, 30.0, (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))  # Output video file

try:
    while True:
        # Capture frame-by-frame from the webcam
        ret, frame = cap.read()

        if not ret:
            print("Failed to grab frame")
            break

        # Perform YOLOv8 detection on the webcam frame
        results = model(frame)

        # Iterate through the detected objects in results
        for result in results:
            boxes = result.boxes  # YOLOv8 boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())  # Get the coordinates of the bounding box
                label = model.names[int(box.cls.item())]  # Get label as string using model.names
                confidence = box.conf.item()  # Convert confidence to float
                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f'{label} {confidence:.2f}', (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

        # Show the frame with detections
        cv2.imshow('YOLOv8 Real-Time Detection with Webcam', frame)

        # Write the frame to the video file
        out.write(frame)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # When everything is done, release the capture and video writer
    cap.release()
    out.release()  # Release the video writer
    cv2.destroyAllWindows()  # Close OpenCV windows
