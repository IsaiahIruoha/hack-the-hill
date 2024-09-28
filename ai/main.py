import pyrealsense2 as rs
import numpy as np
import cv2

# Initialize RealSense pipeline
pipeline = rs.pipeline()
config = rs.config()

# Configure the pipeline to stream both depth and color frames
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start streaming
pipeline.start(config)

try:
    while True:
        # Wait for frames
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        
        # Convert color frame to numpy array for OpenCV processing
        color_image = np.asanyarray(color_frame.get_data())

        # Convert depth frame to numpy array for OpenCV processing
        depth_image = np.asanyarray(depth_frame.get_data())
        
        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
        
        # Stack both images horizontally
        images = np.hstack((color_image, depth_colormap))
        
        # Show images
        cv2.imshow('RealSense RGB and Depth', images)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
finally:
    # Stop streaming
    pipeline.stop()
    cv2.destroyAllWindows()
