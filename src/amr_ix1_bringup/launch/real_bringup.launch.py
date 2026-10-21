"""Bringup for the AMR-IX1 outside Gazebo.

Starts robot_state_publisher, the ros2_control controller manager (mock or real hardware),
the three controllers and the cmd_vel stamper.

    ros2 launch amr_ix1_bringup real_bringup.launch.py hardware:=mock
    ros2 launch amr_ix1_bringup real_bringup.launch.py hardware:=real
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_description = get_package_share_directory('amr_ix1_description')
    pkg_bringup = get_package_share_directory('amr_ix1_bringup')

    urdf_file = os.path.join(pkg_description, 'urdf', 'amr_ix1.urdf.xacro')
    default_controllers = os.path.join(pkg_bringup, 'config', 'controllers_real.yaml')

    hardware = DeclareLaunchArgument(
        'hardware', default_value='mock',
        description='Hardware variant of the URDF: mock | real')
    controllers_file = DeclareLaunchArgument(
        'controllers_file', default_value=default_controllers,
        description='Controller manager parameters file')

    robot_description = ParameterValue(
        Command(['xacro ', urdf_file, ' hardware:=', LaunchConfiguration('hardware')]),
        value_type=str)

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description, 'use_sim_time': False}],
    )

    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        output='screen',
        parameters=[
            {'robot_description': robot_description},
            LaunchConfiguration('controllers_file'),
        ],
    )

    def spawner(name):
        return Node(
            package='controller_manager',
            executable='spawner',
            name=f'{name}_spawner',
            output='screen',
            arguments=[name, '--controller-manager', '/controller_manager',
                       '--controller-manager-timeout', '30'],
        )

    twist_stamper = Node(
        package='twist_stamper',
        executable='twist_stamper',
        name='twist_stamper',
        remappings=[
            ('cmd_vel_in', '/cmd_vel'),
            ('cmd_vel_out', '/diff_drive_controller/cmd_vel'),
        ],
        parameters=[{'frame_id': 'base_footprint', 'use_sim_time': False}],
        output='screen',
    )

    return LaunchDescription([
        hardware,
        controllers_file,
        robot_state_publisher,
        controller_manager,
        spawner('joint_state_broadcaster'),
        spawner('diff_drive_controller'),
        spawner('cam_stand_controller'),
        twist_stamper,
    ])
