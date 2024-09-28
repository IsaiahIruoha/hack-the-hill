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

# Function to draw bounding boxes and display speed
def draw_bounding_boxes(frame, result, prev_box, prev_time):
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

        # Calculate speed if we have a previous bounding box
        if prev_box is not None:
            prev_x, prev_y = prev_box
            current_time = time.time()
            time_diff = current_time - prev_time

            # Calculate distance moved between frames and speed
            distance = calculate_distance(prev_x, prev_y, x, y)
            speed = distance / time_diff  # Speed = distance / time

            # Update the previous bounding box and time
            prev_box = (x, y)
            prev_time = current_time
        else:
            # Set the initial previous bounding box and time
            prev_box = (x, y)
            prev_time = time.time()

    # Display speed on the frame (top right corner)
    cv2.putText(frame, f"Speed: {speed:.2f} px/s", (frame.shape[1] - 150, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    return frame, prev_box, prev_time

# Initialize webcam feed
cap = cv2.VideoCapture(0)  # 0 is the default webcam

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Optionally reduce the resolution for faster processing
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Height

# Initialize variables for tracking speed
prev_box = None  # To store previous bounding box center
prev_time = time.time()  # To store previous frame time

# Set frame rate limit (adjust according to your processing speed)
frame_rate = 60  # Set the frame rate (in frames per second)
prev_time_frame = 0

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    if not ret:
        print("Failed to grab frame")
        break

    # Limit the frame rate
    time_elapsed = time.time() - prev_time_frame
    if time_elapsed > 1. / frame_rate:
        prev_time_frame = time.time()

        # Send the frame to the local inference server and get results
        result = model.predict(frame).json()  # Use the Roboflow SDK for local inference

        # Draw bounding boxes around detected objects and calculate speed
        frame, prev_box, prev_time = draw_bounding_boxes(frame, result, prev_box, prev_time)

    # Display the resulting frame in a window
    cv2.imshow('Webcam Feed', frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture when everything is done
cap.release()
cv2.destroyAllWindows()