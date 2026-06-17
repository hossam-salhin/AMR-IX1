import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    # ── Package path ───────────────────────────────────────────
    pkg_share = get_package_share_directory('amr_ix1_description')

    # ── File paths ─────────────────────────────────────────────
    urdf_file = os.path.join(pkg_share, 'urdf', 'amr_ix1.urdf.xacro')
    rviz_config_file = os.path.join(pkg_share, 'rviz', 'amr_ix1.rviz')

    # ── Launch arguments ───────────────────────────────────────
    use_sim_time = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )

    # ── Robot description via xacro ────────────────────────────
    robot_description = ParameterValue(
        Command(['xacro ', urdf_file]),
        value_type=str
    )

    # ── Nodes ──────────────────────────────────────────────────
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }]
    )

    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
    )

    return LaunchDescription([
        use_sim_time,
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        rviz_node,
    ])
