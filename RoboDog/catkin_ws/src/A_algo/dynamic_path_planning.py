#!/usr/bin/env python3

import rospy
from std_msgs.msg import Float32MultiArray
from sensor_msgs.msg import Range
from geometry_msgs.msg import Twist
import numpy as np
import cv2
from ultralytics import YOLO
import heapq

# Constants
GRID_SIZE = (10, 10)
grid = np.zeros(GRID_SIZE, dtype=int)  # 0 = free, 1 = obstacle, 2 = ball, 3 = robot
robot_position = [0, 0]
grid[robot_position[0]][robot_position[1]] = 3
ball_position = None
obstacle_positions = []

# Initialize YOLO model for ball detection
model = YOLO('/path/to/your/yolo_ball_model.pt')  # Replace with your trained YOLOv8 model
cap = cv2.VideoCapture(1)  # External webcam index (adjust as needed)

# A* Path Planning
def heuristic(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def a_star(grid, start, goal):
    rows, cols = grid.shape
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    open_set = []
    heapq.heappush(open_set, (0, start))
    g_cost = {start: 0}
    f_cost = {start: heuristic(start, goal)}
    parent = {start: None}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            return reconstruct_path(parent, current)

        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)

            if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols and grid[neighbor[0]][neighbor[1]] != 1:
                tentative_g_cost = g_cost[current] + 1

                if neighbor not in g_cost or tentative_g_cost < g_cost[neighbor]:
                    g_cost[neighbor] = tentative_g_cost
                    f_cost[neighbor] = tentative_g_cost + heuristic(neighbor, goal)
                    parent[neighbor] = current
                    heapq.heappush(open_set, (f_cost[neighbor], neighbor))

    return None

def reconstruct_path(parent, current):
    path = []
    while current is not None:
        path.append(current)
        current = parent[current]
    return path[::-1]

# ROS Callbacks
def ultrasonic_callback(data):
    global obstacle_positions
    if data.range < 0.3:  # Obstacle detected within 30 cm
        rospy.loginfo("Obstacle detected at %.2f meters!" % data.range)
        obstacle_positions.append(data.range)  # Convert to grid and update

# Robot Movement
cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)

def move_robot(linear, angular):
    cmd = Twist()
    cmd.linear.x = linear
    cmd.angular.z = angular
    cmd_vel_pub.publish(cmd)

# Ball Detection
def detect_ball():
    global ball_position
    ret, frame = cap.read()
    if not ret:
        rospy.logerr("Failed to capture frame from webcam.")
        return

    results = model(frame)
    detections = results[0].boxes.xywh
    confidences = results[0].boxes.conf

    for box, conf in zip(detections, confidences):
        if conf > 0.8:  # Confidence threshold
            x, y, w, h = box[:4].tolist()
            grid_x = int(x / frame.shape[1] * GRID_SIZE[0])
            grid_y = int(y / frame.shape[0] * GRID_SIZE[1])
            grid[grid == 2] = 0  # Clear old ball position
            ball_position = (grid_x, grid_y)
            grid[grid_x][grid_y] = 2
            break

    # Annotate and display frame
    annotated_frame = results[0].plot()
    cv2.imshow("Ball Detection", annotated_frame)
    cv2.waitKey(1)

# Main Navigation Loop
def main():
    rospy.init_node("dynamic_navigation", anonymous=True)
    rospy.Subscriber("/ultrasonic_data", Range, ultrasonic_callback)

    rate = rospy.Rate(10)  # 10 Hz loop rate

    while not rospy.is_shutdown():
        detect_ball()  # Update ball position dynamically

        if ball_position:
            rospy.loginfo(f"Ball detected at: {ball_position}")

            # Plan path
            path = a_star(grid, tuple(robot_position), ball_position)
            if path:
                rospy.loginfo(f"Path: {path}")
                for step in path[1:]:  # Skip the first step (robot's current position)
                    move_robot(0.2, 0)  # Move forward
                    rospy.sleep(0.5)
            else:
                rospy.logwarn("No path to ball found!")

        rate.sleep()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass

