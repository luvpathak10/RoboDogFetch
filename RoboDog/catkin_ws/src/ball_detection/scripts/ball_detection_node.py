#!/usr/bin/env python3

import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2

# Initialize YOLO model
model = YOLO('/home/luv/catkin_ws/src/ball_detection/models/best.pt')  # Correct path to the model

# Initialize ROS node
rospy.init_node('ball_detection_node', anonymous=True)

# Publishers
ball_position_pub = rospy.Publisher('/ball_position', Float32MultiArray, queue_size=10)

# Image bridge
bridge = CvBridge()

# Webcam index
webcam_index = rospy.get_param("~webcam_index", 2)  # Default to 0, parameterized

# Function to process the webcam feed
def process_webcam():
    # Open webcam
    cap = cv2.VideoCapture(webcam_index)

    if not cap.isOpened():
        rospy.logerr("Could not open webcam.")
        return

    rospy.loginfo("Ball detection node started. Press Ctrl+C to stop.")
    rate = rospy.Rate(60)  # 10 Hz

    while not rospy.is_shutdown():
        ret, frame = cap.read()
        if not ret:
            rospy.logerr("Failed to capture frame from webcam.")
            break

        # Detect objects in the frame using YOLOv8
        results = model(frame)
        detections = results[0].boxes.xywh
        confidences = results[0].boxes.conf  # Confidence scores

        ball_detected = False
        for box, conf in zip(detections, confidences):
            if conf > 0.8:  # Confidence threshold
                x, y, w, h = box[:4].tolist()

                # Normalize coordinates
                height, width, _ = frame.shape
                x /= width
                y /= height
                w /= width
                h /= height

                # Publish ball position (normalized coordinates)
                ball_position = Float32MultiArray(data=[x, y, w, h])
                ball_position_pub.publish(ball_position)
                rospy.loginfo(f"Ball detected at: x={x:.3f}, y={y:.3f}, w={w:.3f}, h={h:.3f}, confidence={conf:.2f}")
                ball_detected = True
                break  # Only consider the first detection

        if not ball_detected:
            rospy.logwarn("No ball detected.")

        # Annotate and display the frame (for debugging)
        annotated_frame = results[0].plot()
        cv2.imshow("Ball Detection", annotated_frame)

        # Quit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        rate.sleep()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    try:
        process_webcam()
    except rospy.ROSInterruptException:
        pass

