#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt

# Initialize grid
GRID_SIZE = (10, 10)  # 10x10 grid
grid = np.zeros(GRID_SIZE, dtype=int)  # 0 = free space, 1 = obstacle, 2 = ball, 3 = robot

# Initial robot position
robot_position = [0, 0]
grid[robot_position[0]][robot_position[1]] = 3  # Mark robot's position on the grid

# Function to update grid with ball position
def update_ball_position(grid, ball_coords):
    grid[grid == 2] = 0  # Clear old ball position
    grid[ball_coords[0]][ball_coords[1]] = 2  # Mark new ball position

# Function to update grid with obstacles
def update_obstacles(grid, obstacle_coords):
    for coord in obstacle_coords:
        grid[coord[0]][coord[1]] = 1  # Mark obstacles

# Visualization function
def visualize_grid(grid):
    plt.imshow(grid, cmap='viridis', origin='upper')
    plt.colorbar(label='Grid Legend: 0-Free, 1-Obstacle, 2-Ball, 3-Robot')
    plt.show()

# Example usage
if __name__ == "__main__":
    # Example ball and obstacle updates
    ball_position = [7, 8]  # Grid coordinates for the ball
    obstacle_positions = [[4, 4], [4, 5], [5, 4]]  # Grid coordinates for obstacles

    update_ball_position(grid, ball_position)
    update_obstacles(grid, obstacle_positions)

    print("Updated Grid:")
    print(grid)

    visualize_grid(grid)

