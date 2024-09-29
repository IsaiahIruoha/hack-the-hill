from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
        return 0
    return sum(values) / len(values)

# Function to track the club face movement in 3D space using depth information
def track_club_movement(result, prev_position, prev_time, depth_frame):
    predictions = result['predictions']
    
    # Initialize avg_speed and avg_launch_angle to default values
    avg_speed = 0  
    avg_launch_angle = 0  
    speed = 0  # Default speed
    launch_angle = 0  # Default launch angle
    top_3d = None
    bottom_3d = None

    if predictions:
        prediction = predictions[0]  # Assuming we're only tracking the first detected object (club face)
        x = int(prediction['x'])
        y = int(prediction['y'])
        width = int(prediction['width'])
        height = int(prediction['height'])

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
        launch_angle_history.append(launch_angle)
        if len(launch_angle_history) > HISTORY_LENGTH:
            launch_angle_history.pop(0)
        avg_launch_angle = moving_average(launch_angle_history)

        # If there's a previous position, calculate speed and movement
        if prev_position is not None:
            prev_x, prev_y, prev_z = prev_position['x'], prev_position['y'], prev_position['z']
            current_time = time.time()
            time_diff = current_time - prev_time

            # Calculate the distance moved in 3D space
            distance_moved = calculate_distance_3d(prev_x, prev_y, prev_z, cx, (top_y + bottom_y) / 2, (top_depth + bottom_depth) / 2)
            speed = distance_moved / time_diff if time_diff > 0 else 0

            # Add speed to history and calculate moving average
            speed_history.append(speed)
            if len(speed_history) > HISTORY_LENGTH:
                speed_history.pop(0)
            avg_speed = moving_average(speed_history)

            # Safety check: Ensure speed is within reasonable bounds
            if avg_speed > MAX_SPEED:
                avg_speed = 0  # Reset speed if it's abnormally high

            # Update the previous position and time
            prev_position = {"x": int(cx), "y": int((top_y + bottom_y) / 2), "z": float((top_depth + bottom_depth) / 2)}
            prev_time = current_time
        else:
            # Set the initial position and time if this is the first detection
            prev_position = {"x": int(cx), "y": int((top_y + bottom_y) / 2), "z": float((top_depth + bottom_depth) / 2)}
            prev_time = time.time()

    return top_3d, bottom_3d, avg_speed, avg_launch_angle, prev_position, prev_time

# WebSocket endpoint for streaming RealSense video
@app.websocket("/ws/video")
async def video_stream(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            # Wait for a new set of frames
            frames = pipeline.wait_for_frames()

            # Align the depth frame to the RGB frame
            aligned_frames = align.process(frames)

            # Get RGB frame
            color_frame = aligned_frames.get_color_frame()

            if not color_frame:
                continue

            # Convert RGB frame to numpy array
            color_image = np.asanyarray(color_frame.get_data())

            # Encode frame as JPEG and send as base64 string over WebSocket
            _, jpeg_frame = cv2.imencode('.jpg', color_image)
            jpeg_base64 = base64.b64encode(jpeg_frame).decode('utf-8')
            await websocket.send_text(jpeg_base64)

    except WebSocketDisconnect:
        print("WebSocket connection closed")

    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()

# REST API to get club face data
@app.get("/club-face")
async def get_club_face():
    global prev_position, prev_time

    # Wait for a new set of frames
    frames = pipeline.wait_for_frames()

    # Align the depth frame to the RGB frame
    aligned_frames = align.process(frames)

    # Get RGB and depth frames
    color_frame = aligned_frames.get_color_frame()
    depth_frame = aligned_frames.get_depth_frame()

    if not color_frame or not depth_frame:
        return JSONResponse(content={"error": "No frames available"}, status_code=500)

    # Convert RGB frame to numpy array
    color_image = np.asanyarray(color_frame.get_data())

    # Send the frame to the local inference server and get results
    result = model.predict(color_image).json()  # Use the Roboflow SDK for local inference

    # Track the club face movement in 3D space
    top_3d, bottom_3d, avg_speed, avg_launch_angle, prev_position, prev_time = track_club_movement(
        result, prev_position, prev_time, depth_frame)

    # Log the values for debugging
    print(f"Top Position: {top_3d}, Bottom Position: {bottom_3d}, Speed: {avg_speed}, Launch Angle: {avg_launch_angle}")

    # Return the results as JSON
    return {
        "speed": avg_speed,
        "launch_angle": avg_launch_angle
    }
