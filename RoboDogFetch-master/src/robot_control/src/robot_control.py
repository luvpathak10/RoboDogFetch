#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
import cv2
import sys
import math
import ctypes
from geometry_msgs.msg import PoseStamped,PoseArray
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image
#sys.path.append('./arm64')
import amd64.robot_interface as sdk
#import platform

#if platform.machine() == 'x86_64':
 #   sys.path.append('./amd64')  # For laptops or desktops
#elif platform.machine() == 'aarch64':
 #   sys.path.append('./arm64')  # For Raspberry Pi or other ARM devices

class RobotControl:
    def __init__(self):
        rospy.init_node('robot_control')

        #subscribe to the target position getting from object detection node
         # Subscribe to the planned path and the camera feed
        self.path_sub = rospy.Subscriber('/planned_path', PoseArray, self.path_callback)
        self.image_sub = rospy.Subscriber('/camera/image_raw', Image, self.image_callback)

        #Initialize UDP and command interface for robot control
        HIGHLEVEL = 0xee
        self.udp = sdk.UDP(HIGHLEVEL, 8080, "192.168.123.161", 8082)
        self.cmd = sdk.HighCmd()
        self.state = sdk.HighState()
        self.udp.InitCmdData(self.cmd)
        
        #variable to store path and current state
        ###self.motion_time = 0
        ###self.target_distance = None
        ###self.target_position_x = None
        ###self.target_position_y = None

        self.path = None
        self.current_target_idx = 0

        self.bridge = CvBridge()

        #Estimate robot's position (initialize to origin)
        self.robot_position = [0, 0]
        self.robot_yaw = 0 #heading angle(in radian)

        #setup optical flow tracking or visual markers (if using visual markers)
        self.prev_frame = None
        self.prev_points = None
        rospy.loginfo('Robot control node initialized')

    def path_callback(self, data):
        """Receive planned path."""
        self.path = [(pose.position.x, pose.position.y) for pose in data.poses]
        self.current_target_idx = 0
        rospy.loginfo("Received new path to follow.")
    
    #function to process camera feed and estimate robot position    
    def image_callback(self, data):
        try:
            current_frame = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            rospy.logerr(f"Error converting image: {e}")
            return

    
    def update_robot_pose(self, current_frame):
        if self.prev_frame is not None:
            #convert to grayscale for better tracking
            prev_gray = cv2.cvtColor(self.prev_frame, cv2.COLOR_BGR2GRAY)
            current_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

            #Detect and track feature points using optical flow (LK method)
            feature_params = dict(maxCorners=100, qualityLevel=0.3, minDistance=7, blockSize=7)
            lk_params = dict(winSize=(15, 15), maxLevel=2, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

            if self.prev_points is None:
                #detect initial points to track
                self.prev_points = cv2.goodFeaturesToTrack(prev_gray, mask= None, **feature_params)
            #calculate optical flow to track movement
            next_points, status, err = cv2.calcOpticalFLowPyrLK(prev_gray, current_gray, self.prev_points, None, **lk_params)

            #Estimate the translation and rotation(change in position) using matched point
            if next_points is not None:
                #calculate the displacement of the points
                movement_vector = np.mean(next_points - self.prev_points, axis=0)

                #update the estimated robot's posotion based on vector
                self.robot_position[0] += movement_vector[0] * 0.1
                self.robot_position[1] += movement_vector[1] * 0.1
                # Estimate rotation based on the angle of the points (optional for yaw)
                # self.robot_yaw += calculate_yaw_change(self.prev_points, next_points)

            # Store current frame and points for the next iteration
            self.prev_frame = current_frame
            self.prev_points = next_points
        else:
            # Set the initial frame
            self.prev_frame = current_frame


    def target_callback(self, data):
        # Receive the target position from the object detection node
        self.target_position_x = data.pose.position.x
        self.target_position_y = data.pose.position.y
        self.target_distance = data.pose.position.z

        rospy.loginfo(f"Target detected at X: {self.target_position_x}, Y: {self.target_position_y}, Distance: {self.target_distance}")

#Stand up process: mode7 -> mode5 -> mode6.
#Fall recovery: fall -> mode7 -> mode8.
#When no command is given to the robot dog, the robot dog can be in mode0 (idle state).

    def calculate_yaw_error(self, current_x, current_y, target_x, target_y):
        target_angle = np.arctan2(target_y - current_y, target_x - current_x)
        yar_error = target_angle - self.robot_yaw
        return yaw_error * 0.5 #gain factor for smoother control

    def move_towards_target(self, target_x, target_y):

        distance_threshold = 1.5
        
        current_x, current_y = self.robot_position  # Use visual-based position estimate
        distance = ((target_x - current_x) ** 2 + (target_y - current_y) ** 2) ** 0.5

        #move forward if target is still away
        if distance > distance_threshold:
            rospy.loginfo('Iffffffffffffffffff')
            self.cmd.velocity = [0.2, 0] #forward speed
            self.footRaisedHeight = 0.1 
            #self.cmd.rotateSpeed = self.calculate_yaw_error(current_x, current_y, target_x, target_y)

            #set the mode of walking
            self.cmd.mode = 2 #walk continously
            self.cmd.euler[0] = 0.0 #Roll
            self.cmd.euler[1] = 0.0 # Pitch
            self.cmd.euler[2] = 0.0 # Yaw
          
        else:
            #stop if close enough to the target
            self.cmd.mode = 0 # force stand
            self.cmd.velocity = [0 , 0]
            self.cmd.yawSpeed = 0.0
            self.current_target_idx += 1
            rospy.loginfo('Elseeeeeeeeeeeeeeeee')
            #rospy.loginfo("Target reached!!!!")
        
        self.udp.SetSend(self.cmd)
        self.udp.Send()

    
    def control_loop(self):
        rate = rospy.Rate(10) 
        while not rospy.is_shutdown():
            if self.path and self.current_target_idx < len(self.path):
                target_x, target_y = self.path[self.current_target_idx]
                self.move_towards_target(target_x, target_y)

            else:
                #stop robot
                self.cmd.mode = 0 # force stand
                self.cmd.velocity = [0 , 0]
                self.cmd.yawSpeed = 0.0
                self.udp.SetSend(self.cmd)
                self.udp.Send()

            
            rate.sleep()

    def walk(self):
        self.cmd.mode = 2     # 0:idle, default stand      1:forced stand     2:walk continuously
        self.gaitType = 1
        self.cmd.velocity = [0.2, 0]
        self.cmd.yawSpeed = 0.0
        self.cmd.footRaiseHeight = 0.1
        #self.rangeObstacle
        # Adjust the Euler angles for the body posture rpy can be used in mode 1
        self.cmd.euler[0] = 0.0  # Roll (no change)
        self.cmd.euler[1] = 2.0  # Pitch (tilt upward slightly)
        self.cmd.euler[2] = 0.0  # Yaw (no change)  can be used in mode 3
        #self.cmd.bodyHeight = 0.2  # Raise body height slightly

        self.udp.SetSend(self.cmd)
        self.udp.Send()

if __name__ == '__main__':
    try:
        robot_control = RobotControl()
        robot_control.control_loop()
    except rospy.ROSInterruptException:
        pass
  