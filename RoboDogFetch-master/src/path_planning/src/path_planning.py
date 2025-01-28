#!/usr/bin/env python3

import rospy
import numpy as np
from geometry_msgs.msg import PoseArray, Twist, Point, PoseStamped
from visualization_msgs.msg import Marker, MarkerArray
import math
from std_msgs.msg import String
import heapq  # Import for A* algorithm

class PathPlanner:
    def __init__(self):
        rospy.init_node('path_planner', anonymous=True)

        # Subscribers
        rospy.Subscriber("/target_position", PoseStamped, self.target_pose_callback)
        rospy.Subscriber("/target_command", String, self.command_callback)

        # Subscriber to detected objects (from object detection node)
        self.objects_sub = rospy.Subscriber("/detected_objects", PoseArray, self.objects_callback)

        # Publisher for velocity commands
        self.vel_pub = rospy.Publisher("/cmd_vel", Twist, queue_size=10)
      
        # RViz marker publishers
        self.marker_pub = rospy.Publisher("/visualization_marker", Marker, queue_size=10)
        self.path_marker_pub = rospy.Publisher("/visualization_marker_array", MarkerArray, queue_size=10)

        # Define goal position (relative to the robot or in fixed coordinates)
        self.goal = np.array([5.0, 5.0])

        # Simulated robot position (since no odometry is available)
        self.robot_position = np.array([0.0, 0.0])
        self.robot_orientation = 0.0  # Simulated orientation in radians (0 is along the x-axis)

        # Start position for A* algorithm
        self.start = (0, 0)  # Initial robot position in grid coordinates

        # Store detected obstacles
        self.obstacles = []

        # Initialize grid
        self.grid = self.create_grid()

        self.rate = rospy.Rate(10)

        # Publish the grid in RViz
        rospy.Timer(rospy.Duration(1.0), self.publish_grid)

    def target_pose_callback(self, data):
        # Receive target position from topic
        x = data.pose.position.x
        y = data.pose.position.y
        z = data.pose.position.z  # Not used in grid planning, but useful for info
        
        # Convert camera coordinates to grid coordinates
        self.goal = self.camera_coords_to_grid(x, y, z)

        # Once we have the goal, visualize the target
        if self.goal:
            rospy.loginfo(f"Target selected at {self.goal}")

            # Update start position in grid
            self.start = (int(self.robot_position[0] / 10), int(self.robot_position[1] / 10))

            # Perform A* pathfinding if the goal is valid
            path = self.astar(self.start, self.goal)
            if path:
                self.publish_path(path)
            else:
                rospy.logwarn("No path found!")

    def camera_coords_to_grid(self, x, y, z):
        # Convert pixel coordinates from camera frame to grid coordinates
        grid_x = int(x / 10)  # Simplified conversion example
        grid_y = int(y / 10)
        return (grid_x, grid_y)

    def command_callback(self, data):
        command = data.data
        rospy.loginfo(f"Received command: {command}")
        # Implement command logic if necessary

    def objects_callback(self, msg):
        """Callback for detected objects"""
        self.obstacles = []
        for pose in msg.poses:
            obstacle_pos = np.array([pose.position.x, pose.position.y])
            self.obstacles.append(obstacle_pos)

        # Publish detected obstacles as markers in RViz
        self.publish_obstacles()

    def publish_robot_marker(self):
        """Publish a marker for the robot's current position."""
        marker = Marker()
        marker.header.frame_id = "map"
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        marker.pose.position.x = self.robot_position[0]
        marker.pose.position.y = self.robot_position[1]
        marker.pose.position.z = 0.1
        marker.pose.orientation.w = 1.0
        marker.scale.x = 0.2
        marker.scale.y = 0.2
        marker.scale.z = 0.2
        marker.color.a = 1.0
        marker.color.r = 0.0
        marker.color.g = 1.0
        marker.color.b = 0.0

        self.marker_pub.publish(marker)

    def publish_goal_marker(self):
        """Publish a marker for the goal position."""
        marker = Marker()
        marker.header.frame_id = "map"
        marker.type = Marker.CYLINDER
        marker.action = Marker.ADD
        marker.pose.position.x = self.goal[0]
        marker.pose.position.y = self.goal[1]
        marker.pose.position.z = 0.1
        marker.pose.orientation.w = 1.0
        marker.scale.x = 0.3
        marker.scale.y = 0.3
        marker.scale.z = 0.1
        marker.color.a = 1.0
        marker.color.r = 1.0
        marker.color.g = 0.0
        marker.color.b = 0.0

        self.marker_pub.publish(marker)

    def publish_obstacles(self):
        """Publish markers for the detected obstacles."""
        marker_array = MarkerArray()
        for i, obstacle in enumerate(self.obstacles):
            marker = Marker()
            marker.header.frame_id = "map"
            marker.type = Marker.CUBE
            marker.action = Marker.ADD
            marker.pose.position.x = obstacle[0]
            marker.pose.position.y = obstacle[1]
            marker.pose.position.z = 0.1
            marker.scale.x = 0.3
            marker.scale.y = 0.3
            marker.scale.z = 0.3
            marker.color.a = 1.0
            marker.color.r = 0.0
            marker.color.g = 0.0
            marker.color.b = 1.0
            marker.id = i
            marker_array.markers.append(marker)

        self.path_marker_pub.publish(marker_array)

    def publish_path(self, path_points):
        """Publish the planned path as a line strip in RViz."""
        marker = Marker()
        marker.header.frame_id = "map"
        marker.type = Marker.LINE_STRIP
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0
        marker.scale.x = 0.05
        marker.color.a = 1.0
        marker.color.r = 0.0
        marker.color.g = 1.0
        marker.color.b = 0.0

        for point in path_points:
            p = Point()
            p.x = point[0]
            p.y = point[1]
            p.z = 0.0
            marker.points.append(p)

        self.marker_pub.publish(marker)

    def calculate_repulsive_force(self, obstacle_pos, influence_radius=1.0):
        """
        Calculate a repulsive force away from a given obstacle based on its distance.
        The influence radius defines how close an obstacle has to be to influence the robot.
        """
        to_obstacle = obstacle_pos - self.robot_position
        distance_to_obstacle = np.linalg.norm(to_obstacle)

        if distance_to_obstacle < influence_radius:
            repulsive_strength = 1.0 / (distance_to_obstacle ** 2)
            repulsive_force = -repulsive_strength * (to_obstacle / distance_to_obstacle)
            return repulsive_force
        else:
            return np.zeros(2)

    def calculate_combined_vector(self):
        """Calculate the combined attractive and repulsive forces for obstacle avoidance."""
        to_goal = self.goal - self.robot_position
        goal_distance = np.linalg.norm(to_goal)

        if goal_distance > 0:
            attractive_force = to_goal / goal_distance
        else:
            attractive_force = np.zeros(2)

        total_repulsive_force = np.zeros(2)

        for obstacle in self.obstacles:
            repulsive_force = self.calculate_repulsive_force(obstacle)
            total_repulsive_force += repulsive_force

        combined_force = attractive_force + total_repulsive_force
        return combined_force

    def plan_path(self):
        """Main path planning loop with obstacle avoidance."""
        while not rospy.is_shutdown():
            combined_vector = self.calculate_combined_vector()
            combined_direction = math.atan2(combined_vector[1], combined_vector[0])

            to_goal = self.goal - self.robot_position
            goal_distance = np.linalg.norm(to_goal)
            goal_distance = 2
            if goal_distance < 0.5:  # Goal reached
                rospy.loginfo("Goal reached!")
                self.stop_robot()
                return

            self.robot_position += 0.1 * np.array([math.cos(combined_direction), math.sin(combined_direction)])

            self.publish_robot_marker()
            self.publish_goal_marker()

            self.rate.sleep()

    def stop_robot(self):
        """Stop the robot by publishing zero velocity."""
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = 0.0
        self.vel_pub.publish(twist)

    def create_grid(self):
        # Create a static or dynamic grid representing the environment
        grid = [[0 for _ in range(50)] for _ in range(50)]  # Simple 50x50 grid
        return grid

    def heuristic(self, node, goal):
        return math.sqrt((node[0] - goal[0])**2 + (node[1] - goal[1])**2)

    def get_neighbors(self, node):
        neighbors = []
        x, y = node
        for nx, ny in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
            if 0 <= nx < len(self.grid) and 0 <= ny < len(self.grid[0]) and self.grid[nx][ny] == 0:
                neighbors.append((nx, ny))
        return neighbors

    def cost(self, current, neighbor):
        return 1  # Uniform cost for simplicity

    def astar(self, start, goal):
        open_list = []
        heapq.heappush(open_list, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}

        while open_list:
            current = heapq.heappop(open_list)[1]

            if current == goal:
                return self.reconstruct_path(came_from, current)

            for neighbor in self.get_neighbors(current):
                tentative_g_score = g_score[current] + self.cost(current, neighbor)

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    heapq.heappush(open_list, (f_score[neighbor], neighbor))

        return None

    def reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return path[::-1]

    def publish_grid(self, event=None):
        marker_array = MarkerArray()
        marker_id = 0
        for i in range(len(self.grid)):
            for j in range(len(self.grid[i])):
                marker = Marker()
                marker.header.frame_id = "map"
                marker.type = Marker.CUBE
                marker.action = Marker.ADD
                marker.id = marker_id
                marker_id += 1
                marker.scale.x = 0.1
                marker.scale.y = 0.1
                marker.scale.z = 0.05
                marker.color.a = 1.0
                marker.pose.position.x = i * 0.1
                marker.pose.position.y = j * 0.1
                marker.pose.position.z = 0.0

                if self.grid[i][j] == 1:
                    marker.color.r = 1.0
                    marker.color.g = 0.0
                    marker.color.b = 0.0  # Red for obstacles
                else:
                    marker.color.r = 0.0
                    marker.color.g = 1.0
                    marker.color.b = 0.0  # Green for free space

                marker_array.markers.append(marker)

        # Now publish the entire marker array at once
        self.marker_pub.publish(marker_array)



if __name__ == '__main__':
    try:
        path_planner = PathPlanner()
        path_planner.plan_path()
    except rospy.ROSInterruptException:
        pass
