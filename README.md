# AMR-IX1 — Autonomous Mobile Inspection Robot

![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)
![Gazebo](https://img.shields.io/badge/Gazebo-Fortress-orange)
![Status](https://img.shields.io/badge/Status-Simulation%20Validated%20%7C%20Hardware%20In%20Progress-yellow)
![License](https://img.shields.io/badge/License-Apache%202.0-green)

## Overview

**AMR-IX1** is a 4-wheel skid-steer Autonomous Mobile Robot (AMR) designed for **industrial inspection and predictive-maintenance applications**.

The project is being developed as a complete robotics system, covering:

- Robot description and mechanical integration
- ROS 2 simulation
- Sensor simulation
- SLAM and localization
- Autonomous navigation
- Inspection missions
- RGB and thermal data acquisition
- Inspection data logging
- Low-level motor control and physical robot integration

The software stack is being validated in simulation first, while the physical robot, motor firmware, and real sensor integration are currently under development.

---

## Current Status

| Area | Status |
|---|---|
| Robot URDF/Xacro | ✅ Verified |
| RViz visualization | ✅ Verified |
| Gazebo Fortress simulation | ✅ Verified |
| `ros2_control` simulation | ✅ Verified |
| LiDAR simulation | ✅ Verified |
| IMU simulation | ✅ Verified |
| RGB camera simulation | ✅ Verified |
| Thermal camera simulation | ✅ Verified |
| TF tree | ✅ Verified |
| SLAM Toolbox | ✅ Verified |
| AMCL localization | ✅ Verified |
| Nav2 autonomous navigation | ✅ Verified |
| Autonomous waypoint mission | ✅ Verified |
| RGB image capture | ✅ Verified |
| Thermal image capture | ✅ Verified |
| Inspection CSV logging | ✅ Verified |
| Camera stand joint control | ✅ Functionally verified in simulation |
| Physical robot assembly | 🔄 In progress |
| Motor controller firmware | 🔄 In progress |
| Physical sensor integration | ⏳ Planned |
| Real robot ROS 2 deployment | ⏳ Planned |
| Physical autonomous inspection | ⏳ Planned |

### Simulation milestone

A complete simulated inspection workflow has been demonstrated:

**Robot → Sensors → SLAM/Localization → Nav2 → Waypoints → RGB/Thermal Images → Inspection Log**

The current simulation includes a 3-waypoint inspection mission with successful navigation, image capture, and CSV logging.

---

## Key Capabilities

### Autonomous Navigation

The navigation stack currently includes:

- Nav2
- AMCL
- SmacPlanner2D
- Regulated Pure Pursuit
- Global and local costmaps
- Obstacle and inflation layers
- Goal checking and recovery behaviors

The navigation system has been tested through autonomous multi-waypoint missions in the simulated factory environment.

### SLAM and Localization

The project uses:

- SLAM Toolbox for mapping
- AMCL for map-based localization
- TF2 for coordinate-frame management
- LiDAR-based environmental perception

The simulated TF chain has been validated across the robot and sensor frames.

### Autonomous Inspection

The inspection workflow is designed around predefined factory waypoints.

At each inspection point, the system can acquire:

- RGB images
- Thermal images
- Timestamped inspection information

The collected information is recorded in an inspection CSV log for later analysis.

### Thermal Perception

AMR-IX1 includes a simulated thermal camera pipeline.

The simulation currently provides:

- Raw thermal image data
- Temperature conversion
- Absolute display range
- False-color thermal visualization
- Thermal legend
- Thermal properties for selected Gazebo environment models

The physical thermal camera has **not yet been selected**. The current implementation is therefore a simulation and software-integration pipeline rather than a representation of a finalized physical sensor.

---

## System Architecture

```text
                    AMR-IX1
                       │
                       ▼
              ┌──────────────────┐
              │ Robot Description │
              │   URDF / Xacro   │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Gazebo Fortress  │
              │   Simulation     │
              └────────┬─────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       LiDAR          IMU       RGB/Thermal
          │            │            │
          └────────────┼────────────┘
                       ▼
              ┌──────────────────┐
              │   ROS 2 Topics   │
              │   TF / Sensors   │
              └────────┬─────────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
        ┌───────────┐     ┌────────────┐
        │ SLAM /    │     │   AMCL     │
        │ Mapping   │     │ Localization│
        └─────┬─────┘     └──────┬─────┘
              │                  │
              └────────┬─────────┘
                       ▼
              ┌──────────────────┐
              │      Nav2        │
              │ Planning + Control│
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Inspection Mission│
              └────────┬─────────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       RGB/Thermal Data     Inspection Log
```

---

## Hardware

The physical hardware architecture is still being finalized. The following represents the current target configuration rather than a claim that every component has already been finalized or integrated.

| Component           | Current Specification / Status                      |
| ------------------- | --------------------------------------------------- |
| Drive configuration | 4-wheel skid-steer                                  |
| Wheel size          | Targeting 8-inch wheels                             |
| Drive motors        | Hoverboard wheel/motor option under evaluation      |
| LiDAR               | RPLIDAR C1                                          |
| IMU                 | To be selected based on availability and evaluation |
| RGB camera          | Physical model TBD                                  |
| Thermal camera      | Physical model TBD                                  |
| MCU                 | ESP32                                               |
| Primary compute     | NVIDIA Jetson Orin Nano — current target            |
| Alternative compute | Raspberry Pi 5 — under evaluation                   |

### Wheel and Motor Selection

The current mechanical direction is toward approximately **8-inch wheels**, with hoverboard wheel/motor assemblies being evaluated as a possible drive solution.

The final motor and wheel configuration will be selected after practical testing of:

* Motor performance
* Controller compatibility
* Torque requirements
* Power requirements
* Low-level control feasibility
* Mechanical integration

### Compute Platform

The **NVIDIA Jetson Orin Nano** is currently the primary target compute platform.

A **Raspberry Pi 5** remains under evaluation.

The final platform will be selected after the low-level firmware is developed and the actual compute, power, and software requirements are validated on the physical robot.

### LiDAR

The planned physical LiDAR is the **RPLIDAR C1**.

The C1 provides 360° scanning and is supported by SLAMTEC's ROS/ROS2 ecosystem, making it suitable for the project's mapping, localization, and navigation pipeline.

---

## Software Stack

| Component           | Technology               |
| ------------------- | ------------------------ |
| Operating System    | Ubuntu 22.04             |
| Robotics Middleware | ROS 2 Humble             |
| Simulation          | Ignition Gazebo Fortress |
| Visualization       | RViz2                    |
| Navigation          | Nav2                     |
| SLAM                | SLAM Toolbox             |
| Localization        | AMCL                     |
| Robot Control       | `ros2_control`           |
| Robot Description   | URDF / Xacro             |
| Main Languages      | C++ / Python             |
| Version Control     | Git / GitHub             |

---

## ROS 2 Packages

The repository is currently organized into the following main packages:

### `amr_ix1_description`

Contains the robot model and visualization resources:

* URDF/Xacro
* Meshes
* Robot TF structure
* RViz configuration
* Camera stand and sensor mounting definitions

Launch:

```bash
ros2 launch amr_ix1_description display.launch.py
```

### `amr_ix1_gazebo`

Contains the Gazebo simulation environment:

* Gazebo world
* Robot spawning
* Simulated sensors
* `ros2_control` integration
* Environment models
* Thermal properties
* Simulation bridges

Launch:

```bash
ros2 launch amr_ix1_gazebo gazebo.launch.py
```

### `amr_ix1_slam`

Contains the mapping configuration and SLAM integration.

Main technology:

* SLAM Toolbox

Launch:

```bash
ros2 launch amr_ix1_slam slam.launch.py
```

### `amr_ix1_navigation`

Contains the autonomous navigation stack:

* Nav2 configuration
* AMCL
* Costmaps
* Planner
* Controller
* Behavior Trees
* Maps
* Inspection mission logic

Launch:

```bash
ros2 launch amr_ix1_navigation navigation.launch.py
```

### `amr_ix1_thermal`

Contains the thermal image processing and visualization pipeline:

* Raw thermal image subscription
* Temperature conversion
* False-color visualization
* Thermal legend
* Thermal display publishing

Launch:

```bash
ros2 launch amr_ix1_thermal thermal_visualizer.launch.py
```

---

## Simulation Workflow

The current development workflow follows this pipeline:

```text
Robot Description
       │
       ▼
Gazebo Fortress
       │
       ▼
Simulated Sensors
       │
       ├── LiDAR
       ├── IMU
       ├── RGB Camera
       └── Thermal Camera
       │
       ▼
SLAM Toolbox
       │
       ▼
Map
       │
       ▼
AMCL Localization
       │
       ▼
Nav2
       │
       ▼
Autonomous Waypoints
       │
       ▼
Inspection Mission
       │
       ├── RGB Images
       ├── Thermal Images
       └── inspection_log.csv
```

---

## Thermal Camera Simulation

The current simulated thermal sensor uses:

* Resolution: `160 × 120`
* Image format: `L8` / `mono8`
* Update rate: `5 Hz`
* Horizontal FOV: `0.9599 rad`
* Near clip: `0.1 m`
* Far clip: `30 m`
* Simulated physical temperature range: approximately `-50°C` to `400°C`
* Thermal resolution: `3 K/pixel`

The raw thermal image is converted using:

```text
Temperature (°C) = pixel × 3.0 − 273.15
```

The visualization currently uses an absolute display range of:

```text
10°C → 70°C
```

Selected Gazebo environment models also have thermal properties for simulation.

For the complete implementation and modification procedure, see:

[`docs/thermal_camera.md`](docs/thermal_camera.md)

---

## Quick Start

### Requirements

The current development environment is:

* Ubuntu 22.04
* ROS 2 Humble
* Ignition Gazebo Fortress
* `colcon`
* Git

### Clone

```bash
git clone https://github.com/hossam-salhin/AMR-IX1.git
cd AMR-IX1
```

### Build

```bash
colcon build --symlink-install
```

### Source

```bash
source install/setup.bash
```

### Launch the robot visualization

```bash
ros2 launch amr_ix1_description display.launch.py
```

### Launch the Gazebo simulation

```bash
ros2 launch amr_ix1_gazebo gazebo.launch.py
```

The remaining components can then be launched according to the required workflow:

```bash
ros2 launch amr_ix1_slam slam.launch.py
```

```bash
ros2 launch amr_ix1_navigation navigation.launch.py
```

```bash
ros2 launch amr_ix1_thermal thermal_visualizer.launch.py
```

> The exact launch order and runtime configuration may evolve as the physical robot integration progresses.

---

## Repository Structure

```text
AMR_inspection/
├── README.md
├── docs/
│   ├── engineering_log.md
│   └── thermal_camera.md
│
├── src/
│   ├── amr_ix1_description/
│   │   ├── launch/
│   │   ├── meshes/
│   │   ├── rviz/
│   │   └── urdf/
│   │
│   ├── amr_ix1_gazebo/
│   │   ├── config/
│   │   ├── launch/
│   │   ├── models/
│   │   └── worlds/
│   │
│   ├── amr_ix1_navigation/
│   │   ├── behavior_trees/
│   │   ├── config/
│   │   ├── launch/
│   │   └── maps/
│   │
│   ├── amr_ix1_slam/
│   │   ├── config/
│   │   ├── launch/
│   │   └── maps/
│   │
│   └── amr_ix1_thermal/
│       ├── amr_ix1_thermal/
│       ├── launch/
│       ├── resource/
│       └── test/
│
└── ...
```

---

## Documentation

The project documentation is separated according to purpose.

### Engineering Log

[`docs/engineering_log.md`](docs/engineering_log.md)

Contains the development history, experiments, measurements, failures, decisions, and verification results.

The engineering log is intended to answer:

> **What happened during development, why did we make a decision, and what evidence supported it?**

### Thermal Camera Guide

[`docs/thermal_camera.md`](docs/thermal_camera.md)

Contains the reusable technical reference for:

* Thermal sensor configuration
* Raw thermal data
* Temperature conversion
* Visualization
* Gazebo thermal properties
* Local Gazebo models
* Launch integration
* Verification
* Troubleshooting
* Future thermal development

The thermal guide is intended to answer:

> **How do I configure, modify, or reproduce the thermal camera system?**

---

## Known Limitations

The following limitations are currently known and intentionally documented.

### Physical Robot

The physical robot is still under development.

Real-world integration of the following systems is not yet complete:

* Motor control
* Low-level firmware
* LiDAR
* IMU
* RGB camera
* Thermal camera
* Onboard compute
* Complete ROS 2 deployment

### Odometry

Odometry drift has been observed in simulation and remains an area for further improvement.

An EKF-based sensor-fusion baseline has not yet been finalized.

### Navigation

The navigation stack is functionally validated in simulation, but additional tuning is expected during physical deployment.

In particular:

* Real-world odometry will require validation.
* Costmap parameters will require physical tuning.
* Final orientation behavior may require additional tuning.
* Dynamic obstacle behavior requires further investigation.

### Thermal Perception

The current thermal camera is simulated.

The physical thermal camera model, calibration, radiometric capabilities, and real-world temperature accuracy have not yet been finalized.

### Compute

The final onboard compute platform has not yet been locked.

Jetson Orin Nano is the current target, while Raspberry Pi 5 remains under evaluation.

---

## Development Roadmap

### Phase 1 — Simulation and Software Validation

* [x] Robot URDF/Xacro
* [x] RViz visualization
* [x] TF validation
* [x] Gazebo simulation
* [x] `ros2_control` simulation
* [x] LiDAR simulation
* [x] IMU simulation
* [x] RGB camera simulation
* [x] Thermal camera simulation
* [x] SLAM
* [x] AMCL localization
* [x] Nav2 autonomous navigation
* [x] Multi-waypoint inspection mission
* [x] RGB image capture
* [x] Thermal image capture
* [x] Inspection CSV logging
* [x] Camera stand joint control verification

### Phase 2 — Physical Robot Integration

* [ ] Complete mechanical assembly
* [ ] Finalize wheel and motor configuration
* [ ] Develop motor-control firmware
* [ ] Validate motor controllers
* [ ] Finalize onboard compute platform
* [ ] Integrate RPLIDAR C1
* [ ] Select and integrate IMU
* [ ] Select and integrate RGB camera
* [ ] Select and integrate thermal camera
* [ ] Transfer ROS 2 stack to onboard computer
* [ ] Validate motor commands
* [ ] Validate odometry
* [ ] Validate TF
* [ ] Validate sensor drivers
* [ ] Perform physical SLAM
* [ ] Perform physical localization
* [ ] Tune Nav2 on the real robot
* [ ] Run physical autonomous inspection missions

### Phase 3 — Inspection and Predictive Maintenance

* [ ] Collect real inspection datasets
* [ ] Integrate real thermal data
* [ ] Develop thermal anomaly analysis
* [ ] Improve inspection data management
* [ ] Connect inspection results to predictive-maintenance workflows
* [ ] Perform extended autonomous testing
* [ ] Evaluate system reliability in realistic industrial environments

---

## Engineering Development Method

AMR-IX1 is developed using an evidence-driven engineering workflow:

```text
Problem
   ↓
Evidence
   ↓
Hypothesis
   ↓
Controlled Experiment
   ↓
Result
   ↓
Decision
   ↓
Documentation
```

Changes are validated experimentally whenever possible rather than being accepted only because they appear theoretically correct.

This approach is especially important for:

* Navigation tuning
* Sensor behavior
* Gazebo simulation
* Robot control
* Hardware selection
* Physical integration

---

## Project Documentation Philosophy

The repository separates **current project information** from **development history**.

### README

The README answers:

> What is AMR-IX1 and how does the system currently work?

### Engineering Log

The engineering log answers:

> What did we try, what happened, and why did we make each engineering decision?

### Technical Guides

Technical guides answer:

> How can a specific subsystem be configured, reproduced, or modified?

This separation is intended to keep the repository useful both as an engineering record and as a professional robotics portfolio.

---

## Author

**Hossam Ahmed Salhin**

Mechatronics Engineering Student
Nahda University, Egypt

* GitHub: [hossam-salhin](https://github.com/hossam-salhin)
* Email: [hossamsalhinahmed@gmail.com](mailto:hossamsalhinahmed@gmail.com)

---

## License

This project is licensed under the **Apache License 2.0**.

See the `LICENSE` file for details.
