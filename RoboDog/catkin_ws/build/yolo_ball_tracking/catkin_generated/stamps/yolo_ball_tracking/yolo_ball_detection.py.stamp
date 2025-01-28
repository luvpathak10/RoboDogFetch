import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from ultralytics import YOLO

class YOLOBallDetector:
    def __init__(self):
        # Initialize ROS and YOLO
        self.bridge = CvBridge()
        self.model = YOLO("yolov8n.pt")  # Pretrained YOLOv8 model
        rospy.init_node('yolo_ball_tracking', anonymous=True)

        # Subscribe to the webcam topic
        rospy.Subscriber("/webcam/image_raw", Image, self.image_callback)

        # Publisher for ball position
        self.pub = rospy.Publisher('/ball_position', String, queue_size=10)

    def image_callback(self, data):
        rospy.loginfo("Image received")
        try:
            # Convert ROS image to OpenCV format
            frame = self.bridge.imgmsg_to_cv2(data, "bgr8")

            # Perform YOLOv8 detection
            results = self.model.predict(source=frame, conf=0.5, show=True)  # `show=True` for visualization

            # Process detected objects
            for result in results:
                for box in result.boxes.xyxy:  # Bounding box coordinates
                    x1, y1, x2, y2 = map(int, box)
                    cx = int((x1 + x2) / 2)  # Center x-coordinate
                    cy = int((y1 + y2) / 2)  # Center y-coordinate

                    # Publish ball position
                    self.pub.publish(f"x={cx}, y={cy}")
                    rospy.loginfo(f"Ball detected at: x={cx}, y={cy}")

        except Exception as e:
            rospy.logerr(f"Error in image_callback: {e}")

    def run(self):
        rospy.spin()

if __name__ == '__main__':
    detector = YOLOBallDetector()
    detector.run()


