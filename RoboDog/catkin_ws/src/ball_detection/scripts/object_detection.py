#!/usr/bin/env python3

import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2

# Initialize YOLO model
model = YOLO('yolov8n.pt')  # Use a suitable YOLOv8 model variant

# Initialize ROS node
rospy.init_node('ball_detection_node', anonymous=True)

# Publishers
ball_position_pub = rospy.Publisher('/ball_position', Float32MultiArray, queue_size=10)

# Image bridge
bridge = CvBridge()

# Webcam index
webcam_index = 2  # Change if using an external webcam

# Function to process the webcam feed
def process_webcam():
    # Open webcam
    cap = cv2.VideoCapture(webcam_index)

    if not cap.isOpened():
        rospy.logerr("Could not open webcam.")
        return

    rospy.loginfo("Ball detection node started. Press Ctrl+C to stop.")

    while not rospy.is_shutdown():
        ret, frame = cap.read()
        if not ret:
            rospy.logerr("Failed to capture frame from webcam.")
            break

        # Detect objects in the frame using YOLOv8
        results = model(frame)
        detections = results[0].boxes.xywh  # Get detections in xywh format (center_x, center_y, width, height)

        # Find the tennis ball (if detected)
        for box in detections:
            x, y, w, h = box[:4].tolist()  # Extract bounding box data
            # Publish ball position (normalized coordinates)
            ball_position = Float32MultiArray(data=[x, y, w, h])
            ball_position_pub.publish(ball_position)
            rospy.loginfo(f"Ball detected at: x={x}, y={y}, w={w}, h={h}")
            break  # Only consider the first detection

        # Annotate and display the frame (for debugging)
        annotated_frame = results[0].plot()
        cv2.imshow("Ball Detection", annotated_frame)

        # Quit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    try:
        process_webcam()
    except rospy.ROSInterruptException:
        pass
