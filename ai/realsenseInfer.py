import pyrealsense2 as rs
import numpy as np
import cv2
import time
import math
import roboflow

# Initialize the Roboflow client
rf = roboflow.Roboflow(api_key="Glf7m6FSWucqx20RPu76")

# Get the project and model from the Roboflow workspace
project = rf.workspace().project("clubs-heads")
local_inference_server_address = "http://localhost:9001/"
version_number = 1

# Point to the local inference server instead of the remote one
model = project.version(version_number=version_number, local=local_inference_server_address).model

# Function to calculate Euclidean distance between two points
def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

# Function to draw bounding boxes and display speed, along with positions
def draw_bounding_boxes(frame, result, prev_box, prev_time, depth_frame):
    predictions = result['predictions']
    speed = 0  # Default speed

    if predictions:
        prediction = predictions[0]  # Assuming we're only tracking the first detected object
        x = int(prediction['x'])
        y = int(prediction['y'])
        width = int(prediction['width'])
        height = int(prediction['height'])
        confidence = prediction['confidence']
        class_name = prediction['class']

        # Define the bounding box
        top_left = (x - width // 2, y - height // 2)
        bottom_right = (x + width // 2, y + height // 2)

        # Draw bounding box and label
        cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)
        cv2.putText(frame, f"{class_name}: {confidence:.2f}", (x - width // 2, y - height // 2 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Print bounding box position
        print(f"Bounding Box - Class: {class_name}, Confidence: {confidence:.2f}, Top Left: {top_left}, Bottom Right: {bottom_right}")

        # Get the center of the bounding box and its depth
        cx = (x - width // 2 + x + width // 2) // 2
        cy = (y - height // 2 + y + height // 2) // 2
        depth = depth_frame.get_distance(cx, cy)  # Depth in meters

        # Print detected object's position in 3D space (x, y, depth)
        print(f"Object Position - Center (x, y): ({cx}, {cy}), Depth: {depth:.2f} meters")

        # Calculate speed if we have a previous bounding box
        if prev_box is not None:
            prev_x, prev_y = prev_box
            current_time = time.time()
            time_diff = current_time - prev_time

            # Calculate distance moved between frames and speed
            distance = calculate_distance(prev_x, prev_y, x, y)
            speed = distance / time_diff  # Speed = distance / time

            # Print speed
            print(f"Speed: {speed:.2f} px/s")

            # Update the previous bounding box and time
            prev_box = (x, y)
            prev_time = current_time
        else:
            # Set the initial previous bounding box and time
            prev_box = (x, y)
            prev_time = time.time()

    return frame, prev_box, prev_time

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

# Initialize variables for tracking speed
prev_box = None  # To store previous bounding box center
prev_time = time.time()  # To store previous frame time

# Set frame rate limit (adjust according to your processing speed)
frame_rate = 60  # Set the frame rate (in frames per second)
prev_time_frame = 0

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

        # Limit the frame rate
        time_elapsed = time.time() - prev_time_frame
        if time_elapsed > 1. / frame_rate:
            prev_time_frame = time.time()

            # Send the frame to the local inference server and get results
            result = model.predict(color_image).json()  # Use the Roboflow SDK for local inference

            # Draw bounding boxes around detected objects and calculate speed
            color_image, prev_box, prev_time = draw_bounding_boxes(color_image, result, prev_box, prev_time, depth_frame)

        # Show the image with detections using OpenCV
        cv2.imshow('RealSense with Roboflow Detection', color_image)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Stop streaming and clean up
    pipeline.stop()
    cv2.destroyAllWindows()
