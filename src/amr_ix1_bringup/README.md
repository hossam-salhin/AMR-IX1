# amr_ix1_bringup

Starts the AMR-IX1 outside Gazebo: `robot_state_publisher`, `ros2_control` (mock or real hardware),
`joint_state_broadcaster`, `diff_drive_controller`, `cam_stand_controller` and `twist_stamper`.

```bash
ros2 launch amr_ix1_bringup real_bringup.launch.py hardware:=mock   # loop-back, no robot
ros2 launch amr_ix1_bringup real_bringup.launch.py hardware:=real   # needs amr_ix1_hardware (not written yet)
```

Quick check with `hardware:=mock`:

```bash
ros2 control list_hardware_components
ros2 control list_controllers                       # 3 controllers active
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2}}"
ros2 topic echo /diff_drive_controller/odom --field pose.pose.position.x
ros2 topic echo /diff_drive_controller/odom --field twist.twist.linear.x
ros2 run tf2_ros tf2_echo odom base_footprint
```

Notes:
- `config/controllers_real.yaml` has the same values as the simulation file except `use_sim_time: false`.
  The wheel radius/separation and the limits are the previous design values and must be updated.
- If the odometry stays at zero with the mock hardware, the mock may not integrate wheel positions;
  see the discussion in the engineering log before changing the controller configuration.
