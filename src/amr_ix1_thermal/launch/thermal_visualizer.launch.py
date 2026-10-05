from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    thermal_visualizer = Node(
        package='amr_ix1_thermal',
        executable='thermal_visualizer',
        name='thermal_visualizer',
        output='screen',
    )

    return LaunchDescription([
        thermal_visualizer,
    ])
