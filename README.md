# AMR-IX1 — Autonomous Mobile Inspection Robot

![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)
![License](https://img.shields.io/badge/License-Apache_2.0-green)
![Status](https://img.shields.io/badge/Status-In_Development-orange)

## Overview

AMR-IX1 is a 4-wheel skid-steer autonomous mobile robot designed for industrial inspection and predictive maintenance tasks. This repository contains the complete ROS2 software stack including robot description, simulation, navigation, and inspection behaviors.

## Robot Specifications

| Parameter | Value |
|-----------|-------|
| Drive Type | 4-Wheel Skid-Steer |
| Wheel Diameter | 150mm |
| Primary Sensor | RPLiDAR A2 |
| Vision | RGB Camera + Thermal Camera |
| IMU | ICM-20948 |
| Compute | Raspberry Pi 5 / NVIDIA Jetson Orin Nano |
| MCU | ESP32 |
| ROS2 Distribution | Humble Hawksbill |

## Package Structure
AMR_inspection/

└── src/

└── amr_ix1_description/     # URDF, meshes, and visualization

## Development Roadmap

- [x] Robot URDF/Xacro description
- [x] RViz visualization
- [x] TF tree validation
- [ ] Gazebo simulation
- [ ] Differential drive controller
- [ ] LiDAR integration
- [ ] Camera integration
- [ ] SLAM
- [ ] Nav2 autonomous navigation
- [ ] Inspection behaviors

## Quick Start

```bash
# Clone the repository
git clone <your-repo-url>
cd AMR_inspection

# Build
colcon build --symlink-install
source install/setup.bash

# Visualize in RViz
ros2 launch amr_ix1_description display.launch.py
```

## Author

Hossam — Mechatronics Engineering Student
