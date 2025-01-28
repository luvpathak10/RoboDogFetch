cmake_minimum_required(VERSION 3.0.2)
project(yolo_ball_tracking)

## Find catkin macros and libraries
find_package(catkin REQUIRED COMPONENTS
  rospy
  sensor_msgs
  std_msgs
  cv_bridge
  image_transport
)

## Declare a catkin package
catkin_package()

## Specify additional locations of header files
include_directories(${catkin_INCLUDE_DIRS})

## Install Python scripts
catkin_install_python(PROGRAMS src/yolo_ball_detection.py
    DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

