from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():

    package_directory = get_package_share_directory(
        'pai_rescue_robot'
    )

    level2_base_launch = os.path.join(
        package_directory,
        'launch',
        'level2_base_simulation.launch.py'
    )

    return LaunchDescription([

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                level2_base_launch
            )
        ),

        Node(
            package='pai_rescue_robot',
            executable='sign_detector',
            output='screen'
        ),

        Node(
            package='pai_rescue_robot',
            executable='mission_controller',
            output='screen'
        ),

        Node(
            package='pai_rescue_robot',
            executable='obstacle_monitor',
            name='obstacle_monitor',
            output='screen',
            parameters=[{
                'stop_distance': 0.50,
                'clear_distance': 0.60,
                'minimum_near_points': 3,
                'detect_frames': 3,
                'clear_frames': 5
            }]
        ),

        Node(
            package='pai_rescue_robot',
            executable='mission_logger',
            name='mission_logger',
            output='screen'
        )

    ])
