import cv2
import numpy as np

import rclpy
from rclpy.node import Node

from cv_bridge import CvBridge

from sensor_msgs.msg import Image
from std_msgs.msg import String


class SignDetector(Node):

    def __init__(self):
        super().__init__('sign_detector')

        self.bridge = CvBridge()

        self.sub = self.create_subscription(
            Image,
            '/front_camera/image_raw',
            self.image_callback,
            10
        )

        self.pub = self.create_publisher(
            String,
            '/detected_sign',
            10
        )

        self.last_label = ""

        self.get_logger().info("SIGN DETECTOR STARTED")

    def image_callback(self, msg):

        frame = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding='bgr8'
        )

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        blue = cv2.inRange(
            hsv,
            (100, 100, 50),
            (130, 255, 255)
        )

        yellow = cv2.inRange(
            hsv,
            (20, 100, 100),
            (35, 255, 255)
        )

        red1 = cv2.inRange(
            hsv,
            (0, 100, 100),
            (10, 255, 255)
        )

        red2 = cv2.inRange(
            hsv,
            (160, 100, 100),
            (180, 255, 255)
        )

        red = cv2.bitwise_or(red1, red2)

        green = cv2.inRange(
            hsv,
            (40, 50, 50),
            (90, 255, 255)
        )

        scores = {
            "LEFT": int(np.sum(blue)),
            "RIGHT": int(np.sum(yellow)),
            "STOP": int(np.sum(red)),
            "GOAL": int(np.sum(green))
        }

        label = max(scores, key=scores.get)

        if scores[label] < 50000:
            return

        if label != self.last_label:

            self.last_label = label

            msg_out = String()
            msg_out.data = label

            self.pub.publish(msg_out)

            self.get_logger().info(
                f"DETECTED: {label}"
            )


def main():
    rclpy.init()

    node = SignDetector()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
