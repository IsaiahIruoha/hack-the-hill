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
    # Get the differences in z and y to calculate the angle
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

def track_club_movement(frame, result, prev_position, prev_time, depth_frame):
    predictions = result['predictions']
    
    # Initialize avg_speed and avg_launch_angle to default values
    avg_speed = 0  
    avg_launch_angle = 0  
    speed = 0  # Default speed
    launch_angle = 0  # Default launch angle
    position_3d = None  # To hold the current position of the club face

    if predictions:
        prediction = predictions[0]  # Assuming we're only tracking the first detected object (club face)
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

        # Get the top and bottom of the bounding box
        top_y = y - height // 2
        bottom_y = y + height // 2

        # Get the center of the bounding box
        cx = (x + (x + width)) // 2

        # Ensure cx and cy are within the bounds of the image dimensions
        depth_width = depth_frame.get_width()
        depth_height = depth_frame.get_height()

        # Clamp the coordinates to stay within image bounds
        cx = np.clip(cx, 0, depth_width - 1)
        top_y = np.clip(top_y, 0, depth_height - 1)
        bottom_y = np.clip(bottom_y, 0, depth_height - 1)

        # Get depth values for the top and bottom of the club face
        top_depth = depth_frame.get_distance(cx, top_y)
        bottom_depth = depth_frame.get_distance(cx, bottom_y)

        # 3D position of the club face (average of top and bottom points)
        position_3d = (cx, (top_y + bottom_y) // 2, (top_depth + bottom_depth) / 2)

        # Print the 3D coordinates of the club face
        print(f"Club Face Position - 3D (x, y, z): ({cx}, {(top_y + bottom_y) // 2}, {(top_depth + bottom_depth) / 2:.2f} meters)")

        # Calculate launch angle
        launch_angle = calculate_launch_angle(top_depth, bottom_depth, top_y, bottom_y)

        # Add launch angle to history and calculate moving average
        launch_angle_history.append(launch_angle)
        if len(launch_angle_history) > HISTORY_LENGTH:
            launch_angle_history.pop(0)
        avg_launch_angle = moving_average(launch_angle_history)

        # If there's a previous position, calculate speed and direction of movement
        if prev_position is not None:
            prev_x, prev_y, prev_z = prev_position
            current_time = time.time()
            time_diff = current_time - prev_time

            # Calculate the distance moved in 3D space
            distance_moved = calculate_distance_3d(prev_x, prev_y, prev_z, cx, (top_y + bottom_y) // 2, (top_depth + bottom_depth) / 2)

            # Calculate the speed (distance moved per time unit)
            speed = distance_moved / time_diff if time_diff > 0 else 0

            # Add speed to history and calculate moving average
            speed_history.append(speed)
            if len(speed_history) > HISTORY_LENGTH:
                speed_history.pop(0)
            avg_speed = moving_average(speed_history)

            # Safety check: Ensure speed is within reasonable bounds
            if avg_speed > MAX_SPEED:
                avg_speed = 0  # Reset speed if it's abnormally high

            # Print the speed and movement information
            print(f"Speed: {avg_speed:.2f} m/s, Distance Moved: {distance_moved:.2f} meters")

            # Update the previous position and time
            prev_position = (cx, (top_y + bottom_y) // 2, (top_depth + bottom_depth) / 2)
            prev_time = current_time
        else:
            # Set the initial position and time if this is the first detection
            prev_position = (cx, (top_y + bottom_y) // 2, (top_depth + bottom_depth) / 2)
            prev_time = time.time()

    return frame, prev_position, prev_time, avg_speed, avg_launch_angle


# Configure RealSense camera
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)  # RGB Camera
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)   # Depth Camera

# Align depth to RGB
align_to = rs.stream.color
align = rs.align(align_to)

# Start streaming from RealSense camera
pipeline.start(config)

# Initialize variables for tracking speed and movement
prev_position = None  # To store the previous position of the club face in 3D
prev_time = time.time()  # To store the previous frame time

# Set frame rate limit (adjust according to your processing speed)
frame_rate = 60  # Set the frame rate (in frames per second)
prev_time_frame = 0

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

        # Limit the frame rate
        time_elapsed = time.time() - prev_time_frame
        if time_elapsed > 1. / frame_rate:
            prev_time_frame = time.time()

            # Send the RGB frame to the local inference server and get results
            result = model.predict(color_image).json()  # Use the Roboflow SDK for local inference

            # Track the club face movement in 3D space
            color_image, prev_position, prev_time, avg_speed, avg_launch_angle = track_club_movement(
                color_image, result, prev_position, prev_time, depth_frame)

            # Display moving average speed and launch angle on the screen
            cv2.putText(color_image, f"Speed (Avg): {avg_speed:.2f} m/s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(color_image, f"Launch Angle (Avg): {avg_launch_angle:.2f} degrees", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Show the image with detections and calculations using OpenCV
        cv2.imshow('RealSense with Club Movement Tracking', color_image)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Stop streaming and clean up
    pipeline.stop()
    cv2.destroyAllWindows()
