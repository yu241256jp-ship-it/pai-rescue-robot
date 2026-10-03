from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():

    pkg_dir = get_package_share_directory(
        'pai_rescue_robot'
    )

    sim_launch = os.path.join(
        pkg_dir,
        'launch',
        'mvp_simulation.launch.py'
    )

    return LaunchDescription([

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                sim_launch
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
        )

    ])
