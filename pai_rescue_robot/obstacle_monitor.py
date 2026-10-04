#!/usr/bin/env python3

import math
import statistics

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, Float32


class ObstacleMonitor(Node):

    def __init__(self):

        super().__init__('obstacle_monitor')

        self.declare_parameter('stop_distance', 0.50)
        self.declare_parameter('clear_distance', 0.60)
        self.declare_parameter('minimum_near_points', 3)
        self.declare_parameter('detect_frames', 3)
        self.declare_parameter('clear_frames', 5)

        self.stop_distance = float(
            self.get_parameter('stop_distance').value
        )

        self.clear_distance = float(
            self.get_parameter('clear_distance').value
        )

        self.minimum_near_points = int(
            self.get_parameter('minimum_near_points').value
        )

        self.detect_frames = int(
            self.get_parameter('detect_frames').value
        )

        self.clear_frames = int(
            self.get_parameter('clear_frames').value
        )

        self.front_angle = math.radians(17.0)

        self.obstacle_pub = self.create_publisher(
            Bool,
            '/obstacle_detected',
            10
        )

        self.distance_pub = self.create_publisher(
            Float32,
            '/obstacle_distance',
            10
        )

        self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )

        self.obstacle_detected = False
        self.detect_count = 0
        self.clear_count = 0
        self.last_logged_state = None

        self.get_logger().info(
            'OBSTACLE MONITOR STARTED: '
            f'stop={self.stop_distance:.2f} m, '
            f'clear={self.clear_distance:.2f} m, '
            f'points={self.minimum_near_points}, '
            f'detect_frames={self.detect_frames}, '
            f'clear_frames={self.clear_frames}'
        )

    def representative_distance(self, valid_ranges):

        if not valid_ranges:
            return float('inf')

        nearest = sorted(valid_ranges)[
            :self.minimum_near_points
        ]

        return float(
            statistics.median(nearest)
        )

    def scan_callback(self, msg):

        valid_ranges = []

        for index, distance in enumerate(msg.ranges):

            angle = (
                msg.angle_min
                + index * msg.angle_increment
            )

            if abs(angle) > self.front_angle:
                continue

            if not math.isfinite(distance):
                continue

            if distance < msg.range_min:
                continue

            if distance > msg.range_max:
                continue

            valid_ranges.append(
                float(distance)
            )

        distance = self.representative_distance(
            valid_ranges
        )

        stop_points = sum(
            value <= self.stop_distance
            for value in valid_ranges
        )

        clear_points = sum(
            value <= self.clear_distance
            for value in valid_ranges
        )

        obstacle_candidate = (
            stop_points
            >= self.minimum_near_points
        )

        clear_candidate = (
            clear_points
            < self.minimum_near_points
        )

        if not self.obstacle_detected:

            if obstacle_candidate:
                self.detect_count += 1
            else:
                self.detect_count = 0

            self.clear_count = 0

            if self.detect_count >= self.detect_frames:
                self.obstacle_detected = True
                self.detect_count = 0

        else:

            if clear_candidate:
                self.clear_count += 1
            else:
                self.clear_count = 0

            self.detect_count = 0

            if self.clear_count >= self.clear_frames:
                self.obstacle_detected = False
                self.clear_count = 0

        obstacle_msg = Bool()
        obstacle_msg.data = self.obstacle_detected
        self.obstacle_pub.publish(obstacle_msg)

        distance_msg = Float32()
        distance_msg.data = distance
        self.distance_pub.publish(distance_msg)

        if self.obstacle_detected != self.last_logged_state:

            if self.obstacle_detected:
                self.get_logger().warn(
                    'OBSTACLE DETECTED: '
                    f'{distance:.2f} m, '
                    f'near_points={stop_points}'
                )
            else:
                self.get_logger().info(
                    'PATH CLEAR: '
                    f'{distance:.2f} m'
                )

            self.last_logged_state = (
                self.obstacle_detected
            )


def main(args=None):

    rclpy.init(args=args)

    node = ObstacleMonitor()

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
