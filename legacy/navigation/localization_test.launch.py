import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, SetRemap
from launch.actions import TimerAction, ExecuteProcess, IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource



def generate_launch_description():
    
    nav_pkg = get_package_share_directory("amr_ix1_navigation")
    map_file = os.path.join(nav_pkg, 'maps', 'factory_map.yaml')
    amcl_params = os.path.join(nav_pkg, 'config', 'amcl.yaml')
    
    lifecycle_nodes = ['map_server','amcl' ]

    map_server = Node(
                package='nav2_map_server',
                executable='map_server',
                name='map_server',
                output='screen',
                parameters=[{"yaml_filename":map_file,
                             "use_sim_time":True
                             }],
    )
    
    amcl_node = Node(
                package='nav2_amcl',
                executable='amcl',
                name='amcl',
                output='screen',
                parameters=[amcl_params ],
    )
    
    lifecycle_manager = Node(
                package='nav2_lifecycle_manager',
                executable='lifecycle_manager',
                name='lifecycle_manager_localization',
                output='screen',
                parameters=[{'use_sim_time': True},
                            {'autostart': True},
                            {'node_names': lifecycle_nodes}])
    
    deactivate_map_server = TimerAction(
        period=4.0,
        actions=[ExecuteProcess(
            cmd=['ros2', 'lifecycle', 'set', '/map_server', 'deactivate'],
            output='screen'
        )]
    )
    
    activate_map_server = TimerAction(
        period=6.0,
        actions=[ExecuteProcess(
            cmd=['ros2', 'lifecycle', 'set', '/map_server', 'activate'],
            output='screen'
        )]
    )
    
   
    
    ld= LaunchDescription()
    ld.add_action(map_server)
    ld.add_action(amcl_node)
    ld.add_action(lifecycle_manager)
    ld.add_action(deactivate_map_server)
    ld.add_action(activate_map_server)

    return ld
