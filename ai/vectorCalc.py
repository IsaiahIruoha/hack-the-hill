# import pyrealsense2 as rs  # Commented out for now as we don't need RealSense
import numpy as np
import time
import random

# Initialize variables
positions = []
velocities = []
timestamps = []

# Configure depth stream (Commented out for now)
# pipeline = rs.pipeline()
# config = rs.config()
# config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 90)  # High frame rate for motion capture

# Start streaming (Commented out for now)
# pipeline.start(config)

# Function to simulate more realistic movement of the club head
def generate_realistic_dummy_positions():
    """
    Simulate more realistic 3D positions for the club head.
    Introduce random variation and higher resolution in movements.
    """
    position_data = []
    current_position = np.array([0.0, 0.0, 0.0])  # Start at origin
    speed = 0.1  # Starting speed

    for i in range(50):  # Simulate 50 frames of motion (about 1 second at 60 FPS)
        # Simulate movement along the x-axis with some variation in y and z
        delta_x = speed + random.uniform(-0.01, 0.01)  # Main direction of motion
        delta_y = random.uniform(-0.01, 0.01)  # Slight vertical variation
        delta_z = random.uniform(-0.01, 0.01)  # Slight depth variation

        # Update the current position with noise
        current_position += np.array([delta_x, delta_y, delta_z])
        position_data.append(current_position.copy())

        # Gradually increase speed to simulate acceleration
        speed += 0.02  # Simulate acceleration

    return position_data

# Generate realistic dummy positions for testing purposes
dummy_positions = generate_realistic_dummy_positions()

# Uncomment this function and implement later for detecting club head from depth frames
# def detect_club_head(depth_frame):
#     """
#     Detect the club head in the depth frame.
#     This is a placeholder function and needs to be implemented based on your detection method.
#     """
#     # Convert depth frame to numpy array
#     depth_image = np.asanyarray(depth_frame.get_data())
    
#     # Preprocess the image (e.g., thresholding, noise reduction)
#     # ...

#     # Detect contours or blobs representing the club head
#     # ...

#     # Return the 3D coordinates (x, y, z) of the club head
#     # For example purposes, return None
#     return None

try:
    for i, club_head_position in enumerate(dummy_positions):
        # Use a dummy timestamp (simulating 1/60th of a second between each frame, 60 FPS)
        current_time = time.time() + i * (1/60)  # Simulate 60 FPS time steps
        positions.append(club_head_position)
        timestamps.append(current_time)

        # Calculate velocity if we have at least two positions
        if len(positions) >= 2:
            delta_pos = np.array(positions[-1]) - np.array(positions[-2])
            delta_time = timestamps[-1] - timestamps[-2]
            velocity = delta_pos / delta_time
            velocities.append(velocity)

            # Calculate acceleration if we have at least two velocities
            if len(velocities) >= 2:
                delta_vel = velocities[-1] - velocities[-2]
                acceleration = delta_vel / delta_time

                # Output the velocity and acceleration vectors
                print(f"Position: {positions[-1]}")
                print(f"Velocity Vector: {velocity}")
                print(f"Acceleration Vector: {acceleration}")

except Exception as e:
    print(f"An error occurred: {e}")

# Stop streaming (Commented out for now)
# finally:
#     pipeline.stop()
