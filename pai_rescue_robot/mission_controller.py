import rclpy
from rclpy.node import Node

from std_msgs.msg import String, Bool
from geometry_msgs.msg import Twist


class MissionController(Node):

    def __init__(self):

        super().__init__('mission_controller')

        self.pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.state_pub = self.create_publisher(
            String,
            '/mission_state',
            10
        )

        self.sign_sub = self.create_subscription(
            String,
            '/detected_sign',
            self.sign_callback,
            10
        )

        self.obstacle_sub = self.create_subscription(
            Bool,
            '/obstacle_detected',
            self.obstacle_callback,
            10
        )

        self.goal_reached = False
        self.obstacle_detected = False

        self.action = 'FORWARD'
        self.action_end_time = None

        self.timer = self.create_timer(
            0.1,
            self.control_callback
        )

        self.get_logger().info(
            'MISSION CONTROLLER STARTED'
        )

    def publish_state(self, state):

        msg = String()
        msg.data = state
        self.state_pub.publish(msg)

    def publish_twist(self, linear, angular):

        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        self.pub.publish(msg)

    def get_current_time(self):

        return self.get_clock().now().nanoseconds / 1e9

    def start_timed_action(self, action, duration):

        self.action = action
        self.action_end_time = self.get_current_time() + duration

        self.get_logger().info(
            f'ACTION STARTED: {action}'
        )

    def control_callback(self):

        if self.goal_reached:
            self.publish_state('GOAL')
            self.publish_twist(0.0, 0.0)
            return

        if self.obstacle_detected:
            self.publish_state('EMERGENCY_STOP')
            self.publish_twist(0.0, 0.0)
            return

        now = self.get_current_time()

        if (
            self.action_end_time is not None
            and now >= self.action_end_time
        ):
            self.get_logger().info(
                f'ACTION FINISHED: {self.action}'
            )

            self.action = 'FORWARD'
            self.action_end_time = None

        self.publish_state(self.action)

        if self.action == 'TURN_LEFT':
            self.publish_twist(0.0, 0.8)

        elif self.action == 'TURN_RIGHT':
            self.publish_twist(0.0, -0.8)

        elif self.action == 'STOP_WAIT':
            self.publish_twist(0.0, 0.0)

        else:
            self.publish_twist(0.2, 0.0)

    def obstacle_callback(self, msg):

        previous_state = self.obstacle_detected
        self.obstacle_detected = msg.data

        if self.obstacle_detected:

            self.publish_twist(0.0, 0.0)

            if not previous_state:
                self.get_logger().warn(
                    'EMERGENCY STOP: OBSTACLE DETECTED'
                )

        elif previous_state:

            self.get_logger().info(
                'OBSTACLE CLEARED'
            )

    def sign_callback(self, msg):

        label = msg.data

        if self.goal_reached:
            return

        if self.obstacle_detected:
            self.publish_twist(0.0, 0.0)

            self.get_logger().warn(
                'SIGN ACTION BLOCKED BY OBSTACLE'
            )
            return

        self.get_logger().info(
            f'ACTION FOR: {label}'
        )

        if label == 'LEFT':

            self.start_timed_action(
                'TURN_LEFT',
                2.0
            )

        elif label == 'RIGHT':

            self.start_timed_action(
                'TURN_RIGHT',
                2.0
            )

        elif label == 'STOP':

            self.start_timed_action(
                'STOP_WAIT',
                3.0
            )

        elif label == 'GOAL':

            self.goal_reached = True
            self.action = 'GOAL'
            self.action_end_time = None

            self.publish_twist(0.0, 0.0)

            self.get_logger().info(
                'MISSION COMPLETE'
            )


def main(args=None):

    rclpy.init(args=args)

    node = MissionController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_twist(0.0, 0.0)
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
