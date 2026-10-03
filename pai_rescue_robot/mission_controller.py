import time

import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from geometry_msgs.msg import Twist


class MissionController(Node):

    def __init__(self):

        super().__init__('mission_controller')

        self.pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.sub = self.create_subscription(
            String,
            '/detected_sign',
            self.sign_callback,
            10
        )

        self.goal_reached = False

        self.get_logger().info(
            "MISSION CONTROLLER STARTED"
        )

        self.timer = self.create_timer(
            0.2,
            self.forward_callback
        )

    def publish_twist(self, linear, angular):

        msg = Twist()

        msg.linear.x = linear
        msg.angular.z = angular

        self.pub.publish(msg)

    def forward_callback(self):

        if self.goal_reached:
            return

        self.publish_twist(0.2, 0.0)

    def sign_callback(self, msg):

        label = msg.data

        self.get_logger().info(
            f"ACTION FOR: {label}"
        )

        if label == 'LEFT':

            self.publish_twist(0.0, 0.8)
            time.sleep(2.0)

        elif label == 'RIGHT':

            self.publish_twist(0.0, -0.8)
            time.sleep(2.0)

        elif label == 'STOP':

            self.publish_twist(0.0, 0.0)
            time.sleep(3.0)

        elif label == 'GOAL':

            self.goal_reached = True

            self.publish_twist(0.0, 0.0)

            self.get_logger().info(
                'MISSION COMPLETE'
            )


def main():

    rclpy.init()

    node = MissionController()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
