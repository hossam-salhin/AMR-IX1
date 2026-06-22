import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_nav = get_package_share_directory('amr_ix1_navigation')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')

    map_file = os.path.join(pkg_nav, 'maps', 'factory_map.yaml')
    params_file = os.path.join(pkg_nav, 'config', 'nav2_params.yaml')

    use_sim_time = DeclareLaunchArgument('use_sim_time', default_value='true')

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2_bringup, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'map': map_file,
            'params_file': params_file,
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'autostart': 'true',
        }.items(),
    )

    return LaunchDescription([use_sim_time, nav2])
