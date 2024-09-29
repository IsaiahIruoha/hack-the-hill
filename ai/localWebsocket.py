from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import pyrealsense2 as rs
import numpy as np
import time
import math
import roboflow
import cv2
import base64

# Initialize the FastAPI app
app = FastAPI()

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://www.foresights.ca"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Roboflow client
rf = roboflow.Roboflow(api_key="Glf7m6FSWucqx20RPu76")
project = rf.workspace().project("clubs-heads")
local_inference_server_address = "http://localhost:9001/"
version_number = 1
model = project.version(version_number=version_number, local=local_inference_server_address).model

# RealSense setup
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

# Align depth to RGB
align_to = rs.stream.color
align = rs.align(align_to)

# Start streaming from RealSense camera
pipeline.start(config)

# Variables to store the previous position and time across requests
prev_position = None
prev_time = None

# Define maximum thresholds and history lengths
MAX_SPEED = 150  # max golf swing speed (m/s)
MAX_ANGLE = 90  # max possible launch angle in degrees
HISTORY_LENGTH = 5  # Number of frames to use in the moving average
MAX_TIME_DIFF = 0.5  # Maximum allowable time difference in seconds

# Variables to store history
speed_history = []
launch_angle_history = []

# Function to calculate Euclidean distance between two 3D points
def calculate_distance_3d(x1, y1, z1, x2, y2, z2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)

# Function to calculate launch angle using two points (top and bottom of club)
def calculate_launch_angle(top_z, bottom_z, top_y, bottom_y):
    delta_z = bottom_z - top_z
    delta_y = bottom_y - top_y

    # Calculate the launch angle using arctangent, and ensure it's an absolute value
    launch_angle = abs(math.degrees(math.atan2(delta_z, delta_y)) * 10)

    # Ensure angle is within a reasonable range
    if abs(launch_angle) > MAX_ANGLE:
        return 0
    return launch_angle

# Function to calculate a moving average for a list of values
def moving_average(values):
    if len(values) == 0:
        return None  # Return None to indicate no data
    return sum(values) / len(values)

# Function to track the club face movement in 3D space using depth information
def track_club_movement(result, prev_position, prev_time, depth_frame):
    predictions = result['predictions']

    # Initialize avg_speed and avg_launch_angle to None
    avg_speed = None
    avg_launch_angle = None
    speed = None  # Default speed
    launch_angle = None  # Default launch angle
    top_3d = None
    bottom_3d = None
    bbox = None
    confidence = None

    if predictions:
        prediction = predictions[0]  # Assuming we're only tracking the first detected object (club face)
        x = int(prediction['x'])
        y = int(prediction['y'])
        width = int(prediction['width'])
        height = int(prediction['height'])
        confidence = prediction.get('confidence', 0.0)  # Get confidence score

        # Store the bounding box for drawing later
        bbox = (x, y, width, height)

        # Get the top and bottom of the bounding box (y-coordinates)
        top_y = y  # Top of the club head
        bottom_y = y + height  # Bottom of the club head

        # Get the center x coordinate for both top and bottom
        cx = int((x + (x + width)) // 2)

        # Ensure cx and cy are within the bounds of the image dimensions
        depth_width = depth_frame.get_width()
        depth_height = depth_frame.get_height()
        cx = np.clip(cx, 0, depth_width - 1)
        top_y = np.clip(top_y, 0, depth_height - 1)
        bottom_y = np.clip(bottom_y, 0, depth_height - 1)

        # Get depth values for both the top and bottom points
        top_depth = depth_frame.get_distance(cx, top_y)
        bottom_depth = depth_frame.get_distance(cx, bottom_y)

        # 3D positions of the top and bottom of the club face
        top_3d = {"x": int(cx), "y": int(top_y), "z": float(top_depth)}
        bottom_3d = {"x": int(cx), "y": int(bottom_y), "z": float(bottom_depth)}

        # Calculate launch angle
        launch_angle = calculate_launch_angle(top_depth, bottom_depth, top_y, bottom_y)

        # Add launch angle to history and calculate moving average
        if launch_angle is not None:
            launch_angle_history.append(launch_angle)
            if len(launch_angle_history) > HISTORY_LENGTH:
                launch_angle_history.pop(0)
            avg_launch_angle = moving_average(launch_angle_history)

        # Calculate time difference
        current_time = time.time()
        time_diff = current_time - prev_time if prev_time else 0

        # Only calculate speed if time difference is within an acceptable range
        if prev_position is not None and 0 < time_diff < MAX_TIME_DIFF:
            prev_x, prev_y, prev_z = prev_position['x'], prev_position['y'], prev_position['z']
            # Calculate the distance moved in 3D space
            distance_moved = calculate_distance_3d(
                prev_x, prev_y, prev_z,
                cx, (top_y + bottom_y) / 2, (top_depth + bottom_depth) / 2
            )
            speed = distance_moved / time_diff if time_diff > 0 else 0

            # Add speed to history and calculate moving average
            if speed is not None and speed > 0:
                speed_history.append(speed)
                if len(speed_history) > HISTORY_LENGTH:
                    speed_history.pop(0)
                avg_speed = moving_average(speed_history)

            # Safety check: Ensure speed is within reasonable bounds
            if avg_speed is not None and avg_speed > MAX_SPEED:
                avg_speed = None  # Reset avg_speed if it's abnormally high

        else:
            # Too much time has passed; reset speed history
            speed_history.clear()
            avg_speed = None

        # Update prev_position and prev_time
        prev_position = {
            "x": int(cx),
            "y": int((top_y + bottom_y) / 2),
            "z": float((top_depth + bottom_depth) / 2)
        }
        prev_time = current_time

    else:
        # No detection in this frame
        print("No club head detected in this frame.")
        # Optionally, keep prev_position and prev_time unchanged

    return top_3d, bottom_3d, avg_speed, avg_launch_angle, prev_position, prev_time, bbox, confidence

# WebSocket endpoint for streaming RealSense video and stats
@app.websocket("/ws/video")
async def video_stream(websocket: WebSocket):
    await websocket.accept()

    global prev_position, prev_time

    try:
        while True:
            # Wait for a new set of frames
            frames = pipeline.wait_for_frames()

            # Align the depth frame to the RGB frame
            aligned_frames = align.process(frames)

            # Get RGB and depth frames
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()

            if not color_frame or not depth_frame:
                continue

            # Convert RGB frame to numpy array
            color_image = np.asanyarray(color_frame.get_data())

            # Convert depth frame to numpy array
            depth_image = np.asanyarray(depth_frame.get_data())

            # Apply color map to depth image for visualization
            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

            # Send the frame to the local inference server and get results
            result = model.predict(color_image).json()

            # Track the club face movement in 3D space
            top_3d, bottom_3d, avg_speed, avg_launch_angle, prev_position, prev_time, bbox, confidence = track_club_movement(
                result, prev_position, prev_time, depth_frame)

            # Draw bounding box and label on the color image
            if bbox is not None:
                x, y, width, height = bbox
                # Draw bounding box
                cv2.rectangle(color_image, (x, y), (x + width, y + height), (0, 255, 0), 2)
                # Draw label with confidence score
                label_text = f"Club Head: {confidence:.2f}"
                cv2.putText(color_image, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Draw bounding box and label on the depth image
            if bbox is not None:
                x, y, width, height = bbox
                # Draw bounding box
                cv2.rectangle(depth_colormap, (x, y), (x + width, y + height), (0, 255, 0), 2)
                # Draw label with confidence score
                label_text = f"Club Head: {confidence:.2f}"
                cv2.putText(depth_colormap, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Encode color image as JPEG
            _, jpeg_frame = cv2.imencode('.jpg', color_image)
            jpeg_base64 = base64.b64encode(jpeg_frame).decode('utf-8')

            # Encode depth image as JPEG
            _, depth_jpeg_frame = cv2.imencode('.jpg', depth_colormap)
            depth_jpeg_base64 = base64.b64encode(depth_jpeg_frame).decode('utf-8')

            # Package both video and stats
            message = {
                "image": jpeg_base64,
                "depth_image": depth_jpeg_base64,
                "stats": {
                    "speed": avg_speed,
                    "launch_angle": avg_launch_angle
                }
            }

            await websocket.send_json(message)

    except WebSocketDisconnect:
        print("WebSocket connection closed")

    except Exception as e:
        print(f"WebSocket error: {e}")
        # Optionally, log the traceback for more details
        import traceback
        traceback.print_exc()
        await websocket.close()
