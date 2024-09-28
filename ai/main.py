import pyrealsense2 as rs
import numpy as np
import cv2
from inference_sdk import InferenceHTTPClient
import base64

# Roboflow API Client setup
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="oIHfAk7TnTpKzXx6bald"  # Replace with your API key
)

# Configure RealSense camera
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)  # Color stream
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)   # Depth stream

# Align depth to color
align_to = rs.stream.color
align = rs.align(align_to)

# Start streaming from RealSense camera
pipeline.start(config)

try:
    while True:
        # Wait for a new set of frames
        frames = pipeline.wait_for_frames()

        # Align the depth frame to the color frame
        aligned_frames = align.process(frames)

        # Get aligned color and depth frames
        color_frame = aligned_frames.get_color_frame()
        depth_frame = aligned_frames.get_depth_frame()

        if not color_frame or not depth_frame:
            continue

        # Convert color frame to numpy array (RGB image)
        color_image = np.asanyarray(color_frame.get_data())

        # Convert the image to JPEG format
        ret, jpeg_image = cv2.imencode('.jpg', color_image)

        if not ret:
            print("Failed to convert image to JPEG")
            continue

        # Encode the image to base64
        image_base64 = base64.b64encode(jpeg_image.tobytes()).decode('utf-8')

        # Send the image to Roboflow for inference
        result = CLIENT.infer(image_base64, model_id="clubs-heads/1")  # Replace with your model ID

        # Extract detection results
        for prediction in result['predictions']:
            x1 = int(prediction['x'] - prediction['width'] / 2)
            y1 = int(prediction['y'] - prediction['height'] / 2)
            x2 = int(prediction['x'] + prediction['width'] / 2)
            y2 = int(prediction['y'] + prediction['height'] / 2)

            # Draw the bounding box on the RGB image
            cv2.rectangle(color_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(color_image, f'{prediction["class"]}: {prediction["confidence"]:.2f}', 
                        (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

            # Get the depth value at the center of the bounding box
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            depth = depth_frame.get_distance(cx, cy)  # Depth in meters

            # Print the detected 3D position of the golf club head
            print(f'Golf Club Head Position (x, y, z): ({cx}, {cy}, {depth:.2f} m)')

        # Show the image with detections using OpenCV
        cv2.imshow('RealSense with Roboflow Detection', color_image)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Stop streaming and clean up
    pipeline.stop()
    cv2.destroyAllWindows()
