#!/usr/bin/env python3

import rospy
from std_msgs.msg import Float32MultiArray
import sys
import math

import sys
sys.path.append('/home/luv/catkin_ws/src/unitree_legged_sdk/lib/python/arm64')  # Correct path to the module
import robot_interface as sdk


# Global variable to store ball position
ball_position = None

def ball_position_callback(data):
    """
    Callback function to update the ball position.
    """
    global ball_position
    ball_position = data.data  # [x, y, w, h]

def go1_control_node():
    """
    Main control loop for the Unitree Go1 robot.
    """
    global ball_position

    # Initialize the ROS node
    rospy.init_node('go1_control_node', anonymous=True)
    
    # Subscribe to the ball position topic
    rospy.Subscriber('/ball_position', Float32MultiArray, ball_position_callback)

    # Initialize Unitree Go1 SDK
    HIGHLEVEL = 0xee
    udp = sdk.UDP(HIGHLEVEL, 8080, "192.168.123.161", 8082)  # Adjust IP and port as per your setup
    cmd = sdk.HighCmd()
    state = sdk.HighState()
    udp.InitCmdData(cmd)

    rospy.loginfo("Unitree Go1 control node started. Listening for ball position...")
    rate = rospy.Rate(10)  # Control loop at 10 Hz

    while not rospy.is_shutdown():
        if ball_position:
            x, y, w, h = ball_position
            rospy.loginfo(f"Ball detected at: x={x}, y={y}, w={w}, h={h}")

            # Control logic to approach the ball
            cmd.mode = 2  # Walking mode
            cmd.gaitType = 1  # Trot gait
            cmd.footRaiseHeight = 0.1  # Set foot height
            cmd.bodyHeight = 0.0  # Neutral body height

            # Normalize x-coordinate and calculate velocity
            x_normalized = (x - 320) / 320  # Assuming 640x480 frame resolution
            forward_velocity = 0.3  # Forward speed (m/s)
            lateral_velocity = -x_normalized * 0.1  # Lateral correction speed
            yaw_rate = -x_normalized * 0.3  # Adjust robot's yaw towards the ball

            # Set velocity commands
            cmd.velocity[0] = forward_velocity  # Forward
            cmd.velocity[1] = lateral_velocity  # Lateral
            cmd.velocity[2] = 0  # No vertical movement
            cmd.yawSpeed = yaw_rate

            udp.SetSend(cmd)
            udp.Send()
        else:
            rospy.loginfo("No ball detected. Stopping robot.")
            
            # Stop the robot
            cmd.mode = 0  # Idle mode
            cmd.velocity = [0, 0, 0]
            cmd.yawSpeed = 0
            udp.SetSend(cmd)
            udp.Send()

        # Receive feedback from the robot
        udp.Recv()
        udp.GetRecv(state)
        rate.sleep()

if __name__ == '__main__':
    try:
        go1_control_node()
    except rospy.ROSInterruptException:
        pass

