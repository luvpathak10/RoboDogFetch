cmake_minimum_required(VERSION 3.0.2)
project(ball_detection)

# Find required packages
find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  sensor_msgs
  cv_bridge
)

# Declare a catkin package
catkin_package()

# Install Python scripts
catkin_install_python(PROGRAMS
  scripts/ball_detection_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

