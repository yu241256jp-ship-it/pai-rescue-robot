from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    pkg_dir = get_package_share_directory('pai_rescue_robot')

    urdf_file = os.path.join(
        pkg_dir,
        'urdf',
        'rescue_robot.urdf.xacro'
    )

    world_file = os.path.join(
        pkg_dir,
        'worlds',
        'level2_course.world'
    )

    gazebo = ExecuteProcess(
        cmd=[
            'gazebo',
            '--verbose',
            world_file,
            '-s',
            'libgazebo_ros_init.so',
            '-s',
            'libgazebo_ros_factory.so'
        ],
        output='screen'
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[
            {
                'robot_description':
                open(urdf_file).read()
            }
        ],
        output='screen'
    )

    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity',
            'rescue_robot',
            '-file',
            urdf_file
        ],
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_robot
    ])
