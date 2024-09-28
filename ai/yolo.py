import pyrealsense2 as rs
import numpy as np
import cv2
from ultralytics import YOLO

# Load the trained YOLOv8 model
model = YOLO('C:/Users/c1leu/OneDrive/Documents/GitHub/hack-the-hill-foresight/runs/detect/train/weights/best.pt')  # Replace with your YOLOv8 model path

# Configure RealSense camera
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)  # Color stream
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)   # Depth stream

# Start streaming from RealSense camera
pipeline.start(config)

# Define the codec and create VideoWriter object to save the output video
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec
out = cv2.VideoWriter('output.avi', fourcc, 30.0, (640, 480))  # Output video file

try:
    while True:
        # Capture frames from the RealSense camera
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()

        if not color_frame:
            continue

        # Convert image to numpy array
        color_image = np.asanyarray(color_frame.get_data())

        # Perform YOLOv8 detection on the RGB image
        results = model(color_image)

        # Iterate through the detected objects in results
        for result in results:
            boxes = result.boxes  # YOLOv8 boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())  # Get the coordinates of the bounding box
                label = model.names[int(box.cls.item())]  # Get label as string using model.names
                confidence = box.conf.item()  # Convert confidence to float
                # Draw bounding box
                cv2.rectangle(color_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(color_image, f'{label} {confidence:.2f}', (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

        # Show the image with detections (optional)
        cv2.imshow('YOLOv8 Real-Time Detection with RealSense', color_image)

        # Write the frame to the video file
        out.write(color_image)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Stop streaming and clean up
    pipeline.stop()
    out.release()  # Release the video writer
    cv2.destroyAllWindows()  # Close OpenCV windows
