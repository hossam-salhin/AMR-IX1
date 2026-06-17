import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    # ── Package paths ──────────────────────────────────────────
    pkg_description = get_package_share_directory('amr_ix1_description')
    pkg_gazebo      = get_package_share_directory('amr_ix1_gazebo')
    pkg_ros_gz_sim  = get_package_share_directory('ros_gz_sim')

    # ── Resource path for Ignition ─────────────────────────────
    ros2_share_dir = os.path.dirname(pkg_description)

    # ── File paths ─────────────────────────────────────────────
    urdf_file      = os.path.join(pkg_description, 'urdf', 'amr_ix1.urdf.xacro')
    world_file     = os.path.join(pkg_gazebo, 'worlds', 'amr_ix1_empty.sdf')
    controllers_file = os.path.join(pkg_gazebo, 'config', 'controllers.yaml')

    # ── Launch arguments ───────────────────────────────────────
    use_sim_time = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='true',
        description='Use simulation clock'
    )

    # ── Robot description ──────────────────────────────────────
    robot_description = ParameterValue(
        Command(['xacro ', urdf_file]),
        value_type=str
    )

    # ── Environment ────────────────────────────────────────────
    set_ign_resource_path = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=ros2_share_dir
    )

    # ── Nodes ──────────────────────────────────────────────────

    # 1. Ignition Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_file}'}.items(),
    )

    # 2. Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }]
    )

    # 3. Spawn robot
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_amr_ix1',
        output='screen',
        arguments=[
            '-name', 'amr_ix1',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.35',
        ]
    )

    # 4. ROS-Gazebo Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        output='screen',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
            '/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V',
            '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            '/lidar@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
            '/joint_states@sensor_msgs/msg/JointState[ignition.msgs.Model',
            '/imu@sensor_msgs/msg/Imu[ignition.msgs.IMU',
            '/camera/image@sensor_msgs/msg/Image[ignition.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo',
            '/thermal/image@sensor_msgs/msg/Image[ignition.msgs.Image',
        ]
    )

    # 5. Joint State Broadcaster — delayed to let Gazebo load first
    joint_state_broadcaster = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='controller_manager',
                executable='spawner',
                name='joint_state_broadcaster_spawner',
                output='screen',
                arguments=['joint_state_broadcaster'],
            )
        ]
    )

    # 6. Diff Drive Controller — delayed after joint state broadcaster
    diff_drive_controller = TimerAction(
        period=7.0,
        actions=[
            Node(
                package='controller_manager',
                executable='spawner',
                name='diff_drive_controller_spawner',
                output='screen',
                arguments=['diff_drive_controller'],
            )
        ]
    )

    # 7. RViz
    rviz_config = os.path.join(pkg_description, 'rviz', 'amr_ix1.rviz')
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]
    )

    return LaunchDescription([
        set_ign_resource_path,
        use_sim_time,
        robot_state_publisher,
        gazebo,
        spawn_robot,
        bridge,
        joint_state_broadcaster,
        diff_drive_controller,
        rviz,
    ])
