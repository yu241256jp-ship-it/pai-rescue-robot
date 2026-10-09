import math

import rclpy
from rclpy.node import Node

from gazebo_msgs.srv import DeleteEntity, SpawnEntity
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool, String


class VideoDemoManager(Node):

    def __init__(self):

        super().__init__('video_demo_manager')

        self.spawn_client = self.create_client(
            SpawnEntity,
            '/spawn_entity'
        )

        self.delete_client = self.create_client(
            DeleteEntity,
            '/delete_entity'
        )

        self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        self.create_subscription(
            String,
            '/detected_sign',
            self.sign_callback,
            10
        )

        self.create_subscription(
            Bool,
            '/obstacle_detected',
            self.obstacle_callback,
            10
        )

        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_yaw = 0.0
        self.odom_received = False

        self.stage = 'WAIT_FOR_SERVICES'
        self.current_model = None
        self.pending_action = None
        self.action_time = None
        self.initial_spawn_requested = False
        self.obstacle_detected = False

        self.timer = self.create_timer(
            0.1,
            self.timer_callback
        )

        self.get_logger().info(
            'VIDEO DEMO MANAGER STARTED'
        )

    def odom_callback(self, msg):

        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y

        q = msg.pose.pose.orientation

        siny = 2.0 * (
            q.w * q.z
            + q.x * q.y
        )

        cosy = 1.0 - 2.0 * (
            q.y * q.y
            + q.z * q.z
        )

        self.robot_yaw = math.atan2(
            siny,
            cosy
        )

        self.odom_received = True

    def get_time(self):

        return (
            self.get_clock().now().nanoseconds
            / 1e9
        )

    def create_sign_sdf(self, name, color):

        red, green, blue = color

        return f"""<?xml version='1.0'?>
<sdf version='1.6'>
  <model name='{name}'>
    <static>true</static>
    <link name='link'>
      <visual name='visual'>
        <geometry>
          <box>
            <size>0.08 0.50 0.50</size>
          </box>
        </geometry>
        <material>
          <ambient>{red} {green} {blue} 1</ambient>
          <diffuse>{red} {green} {blue} 1</diffuse>
          <emissive>{red} {green} {blue} 1</emissive>
        </material>
      </visual>
    </link>
  </model>
</sdf>
"""

    def create_obstacle_sdf(self, name):

        return f"""<?xml version='1.0'?>
<sdf version='1.6'>
  <model name='{name}'>
    <static>true</static>
    <link name='link'>
      <collision name='collision'>
        <geometry>
          <box>
            <size>0.15 0.90 0.70</size>
          </box>
        </geometry>
      </collision>
      <visual name='visual'>
        <geometry>
          <box>
            <size>0.15 0.90 0.70</size>
          </box>
        </geometry>
        <material>
          <ambient>0.35 0.35 0.35 1</ambient>
          <diffuse>0.45 0.45 0.45 1</diffuse>
        </material>
      </visual>
    </link>
  </model>
</sdf>
"""

    def spawn_sign(
        self,
        name,
        color,
        distance
    ):

        x = (
            self.robot_x
            + distance * math.cos(self.robot_yaw)
        )

        y = (
            self.robot_y
            + distance * math.sin(self.robot_yaw)
        )

        request = SpawnEntity.Request()
        request.name = name
        request.xml = self.create_sign_sdf(
            name,
            color
        )
        request.robot_namespace = ''

        request.initial_pose.position.x = x
        request.initial_pose.position.y = y
        request.initial_pose.position.z = 0.45

        request.initial_pose.orientation.z = math.sin(
            self.robot_yaw / 2.0
        )

        request.initial_pose.orientation.w = math.cos(
            self.robot_yaw / 2.0
        )

        request.reference_frame = 'world'

        future = self.spawn_client.call_async(
            request
        )

        future.add_done_callback(
            lambda result: self.spawn_finished(
                result,
                name
            )
        )

        self.current_model = name

        self.get_logger().info(
            f'SPAWN REQUEST: {name}, '
            f'x={x:.2f}, y={y:.2f}'
        )

    def spawn_lidar_obstacle(self, distance):

        name = 'video_lidar_obstacle'

        x = (
            self.robot_x
            + distance * math.cos(self.robot_yaw)
        )

        y = (
            self.robot_y
            + distance * math.sin(self.robot_yaw)
        )

        request = SpawnEntity.Request()
        request.name = name
        request.xml = self.create_obstacle_sdf(name)
        request.robot_namespace = ''

        request.initial_pose.position.x = x
        request.initial_pose.position.y = y
        request.initial_pose.position.z = 0.35

        request.initial_pose.orientation.z = math.sin(
            self.robot_yaw / 2.0
        )

        request.initial_pose.orientation.w = math.cos(
            self.robot_yaw / 2.0
        )

        request.reference_frame = 'world'

        future = self.spawn_client.call_async(request)

        future.add_done_callback(
            lambda result: self.spawn_finished(
                result,
                name
            )
        )

        self.current_model = name

        self.get_logger().info(
            f'LIDAR OBSTACLE SPAWN REQUEST: '
            f'x={x:.2f}, y={y:.2f}'
        )

    def spawn_finished(self, future, name):

        try:
            response = future.result()

            if response.success:
                self.get_logger().info(
                    f'SIGN SPAWNED: {name}'
                )
            else:
                self.get_logger().error(
                    f'SPAWN FAILED: '
                    f'{response.status_message}'
                )

        except Exception as error:

            self.get_logger().error(
                f'SPAWN ERROR: {error}'
            )

    def delete_current_sign(self):

        if self.current_model is None:
            return

        name = self.current_model

        request = DeleteEntity.Request()
        request.name = name

        future = self.delete_client.call_async(
            request
        )

        future.add_done_callback(
            lambda result: self.delete_finished(
                result,
                name
            )
        )

        self.current_model = None

    def delete_finished(self, future, name):

        try:
            response = future.result()

            if response.success:
                self.get_logger().info(
                    f'SIGN DELETED: {name}'
                )
            else:
                self.get_logger().warn(
                    f'DELETE FAILED: '
                    f'{response.status_message}'
                )

        except Exception as error:

            self.get_logger().error(
                f'DELETE ERROR: {error}'
            )

    def schedule(self, action, delay):

        self.pending_action = action
        self.action_time = (
            self.get_time()
            + delay
        )

        self.get_logger().info(
            f'SCHEDULED: {action} '
            f'in {delay:.1f} seconds'
        )

    def obstacle_callback(self, msg):

        previous = self.obstacle_detected
        self.obstacle_detected = msg.data

        if (
            self.stage == 'LIDAR_OBSTACLE_ACTIVE'
            and self.obstacle_detected
            and not previous
        ):
            self.get_logger().warn(
                'LIDAR OBSTACLE DETECTED: EMERGENCY STOP'
            )

            self.stage = 'LIDAR_EMERGENCY_STOP'

            self.schedule(
                'DELETE_LIDAR_OBSTACLE',
                3.0
            )

        elif (
            self.stage == 'WAITING_LIDAR_CLEAR'
            and not self.obstacle_detected
            and previous
        ):
            self.get_logger().info(
                'LIDAR AREA CLEARED: RESUME MISSION'
            )

            self.stage = 'GREEN_PENDING'

            self.schedule(
                'SPAWN_GREEN',
                1.0
            )

    def sign_callback(self, msg):

        label = msg.data

        if (
            self.stage == 'BLUE_ACTIVE'
            and label == 'LEFT'
        ):
            self.get_logger().info(
                'BLUE DETECTED: LEFT TURN'
            )

            self.delete_current_sign()
            self.stage = 'LEFT_TURNING'

            self.schedule(
                'SPAWN_YELLOW',
                2.6
            )

        elif (
            self.stage == 'YELLOW_ACTIVE'
            and label == 'RIGHT'
        ):
            self.get_logger().info(
                'YELLOW DETECTED: RIGHT TURN'
            )

            self.delete_current_sign()
            self.stage = 'RIGHT_TURNING'

            self.schedule(
                'SPAWN_RED',
                2.6
            )

        elif (
            self.stage == 'RED_ACTIVE'
            and label == 'STOP'
        ):
            self.get_logger().info(
                'RED DETECTED: STOP'
            )

            self.stage = 'STOPPING'

            self.schedule(
                'DELETE_RED',
                2.2
            )

        elif (
            self.stage == 'GREEN_ACTIVE'
            and label == 'GOAL'
        ):
            self.get_logger().info(
                'GREEN DETECTED: GOAL'
            )

            self.delete_current_sign()
            self.stage = 'COMPLETE'

            self.get_logger().info(
                'VIDEO DEMO COMPLETE'
            )

    def timer_callback(self):

        services_ready = (
            self.spawn_client.service_is_ready()
            and self.delete_client.service_is_ready()
        )

        if (
            not self.initial_spawn_requested
            and self.odom_received
            and services_ready
        ):
            self.initial_spawn_requested = True
            self.stage = 'BLUE_ACTIVE'

            self.spawn_sign(
                'video_blue_sign',
                (0.0, 0.0, 1.0),
                3.00
            )

            return

        if (
            self.pending_action is None
            or self.action_time is None
        ):
            return

        if self.get_time() < self.action_time:
            return

        action = self.pending_action
        self.pending_action = None
        self.action_time = None

        if action == 'SPAWN_YELLOW':

            self.stage = 'YELLOW_ACTIVE'

            self.spawn_sign(
                'video_yellow_sign',
                (1.0, 1.0, 0.0),
                6.50
            )

        elif action == 'SPAWN_RED':

            self.stage = 'RED_ACTIVE'

            self.spawn_sign(
                'video_red_sign',
                (1.0, 0.0, 0.0),
                6.50
            )

        elif action == 'DELETE_RED':

            self.delete_current_sign()
            self.stage = 'LIDAR_OBSTACLE_PENDING'

            self.schedule(
                'SPAWN_LIDAR_OBSTACLE',
                1.2
            )

        elif action == 'SPAWN_LIDAR_OBSTACLE':

            self.stage = 'LIDAR_OBSTACLE_ACTIVE'

            self.spawn_lidar_obstacle(
                3.00
            )

        elif action == 'DELETE_LIDAR_OBSTACLE':

            self.delete_current_sign()
            self.stage = 'WAITING_LIDAR_CLEAR'

            self.get_logger().info(
                'LIDAR OBSTACLE REMOVED'
            )

        elif action == 'SPAWN_GREEN':

            self.stage = 'GREEN_ACTIVE'

            self.spawn_sign(
                'video_green_sign',
                (0.0, 1.0, 0.0),
                6.50
            )


def main(args=None):

    rclpy.init(args=args)

    node = VideoDemoManager()

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
