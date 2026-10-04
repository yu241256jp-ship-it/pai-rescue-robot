import csv
from datetime import datetime
from pathlib import Path

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool, Float32, String


class MissionLogger(Node):

    def __init__(self):

        super().__init__('mission_logger')

        self.mission_state = 'UNKNOWN'
        self.detected_sign = ''
        self.sign_confidence = 0.0
        self.obstacle_detected = False
        self.obstacle_distance = float('inf')
        self.cmd_linear_x = 0.0
        self.cmd_angular_z = 0.0
        self.odom_linear_x = 0.0
        self.odom_angular_z = 0.0

        log_directory = Path.home() / 'pai_ws' / 'logs'
        log_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        timestamp = datetime.now().strftime(
            '%Y%m%d_%H%M%S'
        )

        self.log_path = (
            log_directory
            / f'mission_log_{timestamp}.csv'
        )

        self.log_file = self.log_path.open(
            'w',
            newline='',
            encoding='utf-8'
        )

        self.csv_writer = csv.writer(
            self.log_file
        )

        self.csv_writer.writerow([
            'timestamp',
            'mission_state',
            'detected_sign',
            'sign_confidence',
            'obstacle_detected',
            'obstacle_distance',
            'cmd_linear_x',
            'cmd_angular_z',
            'odom_linear_x',
            'odom_angular_z'
        ])

        self.log_file.flush()

        self.create_subscription(
            String,
            '/mission_state',
            self.mission_state_callback,
            10
        )

        self.create_subscription(
            String,
            '/detected_sign',
            self.detected_sign_callback,
            10
        )

        self.create_subscription(
            Float32,
            '/sign_confidence',
            self.sign_confidence_callback,
            10
        )

        self.create_subscription(
            Bool,
            '/obstacle_detected',
            self.obstacle_detected_callback,
            10
        )

        self.create_subscription(
            Float32,
            '/obstacle_distance',
            self.obstacle_distance_callback,
            10
        )

        self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.timer = self.create_timer(
            0.5,
            self.write_log
        )

        self.get_logger().info(
            f'MISSION LOGGER STARTED: {self.log_path}'
        )

    def mission_state_callback(self, msg):

        self.mission_state = msg.data

    def detected_sign_callback(self, msg):

        self.detected_sign = msg.data

    def sign_confidence_callback(self, msg):

        self.sign_confidence = float(msg.data)

    def obstacle_detected_callback(self, msg):

        self.obstacle_detected = bool(msg.data)

    def obstacle_distance_callback(self, msg):

        self.obstacle_distance = float(msg.data)

    def cmd_vel_callback(self, msg):

        self.cmd_linear_x = float(
            msg.linear.x
        )

        self.cmd_angular_z = float(
            msg.angular.z
        )

    def odom_callback(self, msg):

        self.odom_linear_x = float(
            msg.twist.twist.linear.x
        )

        self.odom_angular_z = float(
            msg.twist.twist.angular.z
        )

    def write_log(self):

        timestamp = datetime.now().isoformat(
            timespec='milliseconds'
        )

        self.csv_writer.writerow([
            timestamp,
            self.mission_state,
            self.detected_sign,
            f'{self.sign_confidence:.6f}',
            self.obstacle_detected,
            f'{self.obstacle_distance:.6f}',
            f'{self.cmd_linear_x:.6f}',
            f'{self.cmd_angular_z:.6f}',
            f'{self.odom_linear_x:.6f}',
            f'{self.odom_angular_z:.6f}'
        ])

        self.log_file.flush()

    def destroy_node(self):

        if not self.log_file.closed:
            self.log_file.flush()
            self.log_file.close()

        super().destroy_node()


def main(args=None):

    rclpy.init(args=args)

    node = MissionLogger()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
