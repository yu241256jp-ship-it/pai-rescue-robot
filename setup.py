from setuptools import setup, find_packages
from glob import glob

package_name = 'pai_rescue_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
        (
            'share/' + package_name + '/launch',
            glob('launch/*.py')
        ),
        (
            'share/' + package_name + '/urdf',
            glob('urdf/*')
        ),
        (
            'share/' + package_name + '/worlds',
            glob('worlds/*')
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='ubuntu@todo.todo',
    description='PAI MVP Robot',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'sign_detector = pai_rescue_robot.sign_detector:main',
            'mission_controller = pai_rescue_robot.mission_controller:main',
            'obstacle_monitor = pai_rescue_robot.obstacle_monitor:main',
            'mission_logger = pai_rescue_robot.mission_logger:main',
            'video_demo_manager = pai_rescue_robot.video_demo_manager:main',
        ],
    },
)
