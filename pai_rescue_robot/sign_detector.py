from collections import Counter, deque

import cv2
import numpy as np

import rclpy
from rclpy.node import Node

from cv_bridge import CvBridge

from sensor_msgs.msg import Image
from std_msgs.msg import Float32, String


class SignDetector(Node):

    def __init__(self):

        super().__init__('sign_detector')

        self.bridge = CvBridge()

        self.image_sub = self.create_subscription(
            Image,
            '/front_camera/image_raw',
            self.image_callback,
            10
        )

        self.sign_pub = self.create_publisher(
            String,
            '/detected_sign',
            10
        )

        self.confidence_pub = self.create_publisher(
            Float32,
            '/sign_confidence',
            10
        )

        self.history = deque(maxlen=5)
        self.minimum_votes = 3
        self.declare_parameter('minimum_score', 50000)
        self.minimum_score = int(
            self.get_parameter('minimum_score').value
        )

        self.active_label = None
        self.clear_count = 0
        self.clear_frames = 5

        self.get_logger().info(
            'SIGN DETECTOR STARTED: '
            'history=5, minimum_votes=3'
        )

    def create_masks(self, hsv):

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

        return {
            'LEFT': blue,
            'RIGHT': yellow,
            'STOP': red,
            'GOAL': green
        }

    def image_callback(self, msg):

        try:
            frame = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding='bgr8'
            )
        except Exception as error:
            self.get_logger().error(
                f'IMAGE CONVERSION ERROR: {error}'
            )
            return

        hsv = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2HSV
        )

        masks = self.create_masks(hsv)

        scores = {
            label: int(np.sum(mask))
            for label, mask in masks.items()
        }

        best_label = max(
            scores,
            key=scores.get
        )

        best_score = scores[best_label]

        total_score = float(
            255 * frame.shape[0] * frame.shape[1]
        )

        confidence = min(
            1.0,
            best_score / total_score
        )

        confidence_msg = Float32()
        confidence_msg.data = float(confidence)
        self.confidence_pub.publish(confidence_msg)

        if best_score >= self.minimum_score:
            candidate = best_label
        else:
            candidate = 'NONE'

        self.history.append(candidate)

        valid_history = [
            label
            for label in self.history
            if label != 'NONE'
        ]

        stable_label = None
        vote_count = 0

        if valid_history:
            counts = Counter(valid_history)
            stable_label, vote_count = counts.most_common(1)[0]

            if vote_count < self.minimum_votes:
                stable_label = None

        if stable_label is None:

            self.clear_count += 1

            if self.clear_count >= self.clear_frames:

                if self.active_label is not None:
                    self.get_logger().info(
                        'SIGN AREA CLEARED'
                    )

                self.active_label = None

            return

        self.clear_count = 0

        if stable_label == self.active_label:
            return

        self.active_label = stable_label

        sign_msg = String()
        sign_msg.data = stable_label
        self.sign_pub.publish(sign_msg)

        self.get_logger().info(
            f'DETECTED: {stable_label}, '
            f'confidence={confidence:.4f}, '
            f'votes={vote_count}/{len(self.history)}'
        )


def main(args=None):

    rclpy.init(args=args)

    node = SignDetector()

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
