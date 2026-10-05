import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class ThermalVisualizer(Node):
    def __init__(self):
        super().__init__('thermal_visualizer')

        self.declare_parameter('display_min_c', 10.0)
        self.declare_parameter('display_max_c', 70.0)

        self.display_min_c = float(
            self.get_parameter('display_min_c').value
        )
        self.display_max_c = float(
            self.get_parameter('display_max_c').value
        )

        if self.display_max_c <= self.display_min_c:
            self.get_logger().error(
                'display_max_c must be greater than display_min_c. '
                'Using 10.0 to 70.0 C.'
            )
            self.display_min_c = 10.0
            self.display_max_c = 70.0

        self.bridge = CvBridge()

        self.image_sub = self.create_subscription(
            Image,
            '/thermal/image',
            self.image_callback,
            10,
        )

        self.image_pub = self.create_publisher(
            Image,
            '/thermal/image_color',
            10,
        )

        self.legend_pub = self.create_publisher(
            Image,
            '/thermal/legend',
            10,
        )

        self.create_timer(1.0, self.publish_legend)

        self.get_logger().info(
            'Thermal visualizer started | '
            f'Display range: {self.display_min_c:.1f} to '
            f'{self.display_max_c:.1f} C'
        )

    def thermal_to_celsius(self, image):
        """
        Convert the simulated 8-bit thermal image to Celsius.

        Current Ignition Fortress thermal configuration:
            temperature_K = pixel * 3.0

        Therefore:
            temperature_C = pixel * 3.0 - 273.15
        """
        return image.astype(np.float32) * 3.0 - 273.15

    def colorize(self, temp_c):
        """
        Convert absolute temperature to an Ironbow-like BGR image.

        The display range is independent of the physical sensor range.
        """
        normalized = (
            (temp_c - self.display_min_c)
            / (self.display_max_c - self.display_min_c)
        )

        normalized = np.clip(normalized, 0.0, 1.0)

        palette = np.array(
            [
                [35, 0, 45],
                [55, 0, 75],
                [80, 0, 110],
                [110, 0, 150],
                [150, 0, 190],
                [190, 0, 230],
                [230, 0, 255],
                [0, 0, 255],
                [0, 40, 255],
                [0, 80, 255],
                [0, 120, 255],
                [0, 170, 255],
                [0, 220, 255],
                [0, 255, 255],
                [120, 255, 255],
                [220, 255, 255],
                [255, 255, 255],
            ],
            dtype=np.float32,
        )

        positions = np.linspace(0.0, 1.0, len(palette))

        indices = normalized * (len(palette) - 1)
        lower = np.floor(indices).astype(np.int32)
        upper = np.clip(lower + 1, 0, len(palette) - 1)

        fraction = (indices - lower)[..., None]

        color = (
            palette[lower] * (1.0 - fraction)
            + palette[upper] * fraction
        )

        return np.clip(color, 0, 255).astype(np.uint8)

    def image_callback(self, msg):
        try:
            thermal_image = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding='mono8',
            )

            temp_c = self.thermal_to_celsius(thermal_image)
            color_image = self.colorize(temp_c)

            output_msg = self.bridge.cv2_to_imgmsg(
                color_image,
                encoding='bgr8',
            )

            output_msg.header = msg.header
            self.image_pub.publish(output_msg)

        except Exception as exc:
            self.get_logger().error(
                f'Failed to process thermal image: {exc}'
            )

    def publish_legend(self):
        width = 700
        height = 100

        legend = np.zeros((height, width, 3), dtype=np.uint8)

        gradient = np.linspace(
            0.0,
            1.0,
            width,
            dtype=np.float32,
        )

        temp_c = (
            self.display_min_c
            + gradient
            * (self.display_max_c - self.display_min_c)
        )

        gradient_image = np.tile(
            temp_c,
            (height, 1),
        )

        legend[:, :, :] = self.colorize(gradient_image)

        font = cv2.FONT_HERSHEY_SIMPLEX

        # Temperature labels every 5 C across the display range.
        label_count = 13
        label_step = (
            self.display_max_c - self.display_min_c
        ) / (label_count - 1)

        for i in range(label_count):
            temperature = (
                self.display_min_c + i * label_step
            )

            x = int(
                i * (width - 1) / (label_count - 1)
            )

            label = f'{temperature:.0f} C'

            text_size = cv2.getTextSize(
                label,
                font,
                0.42,
                1,
            )[0]

            if i == 0:
                text_x = 2
            elif i == label_count - 1:
                text_x = width - text_size[0] - 2
            else:
                text_x = x - text_size[0] // 2

            cv2.putText(
                legend,
                label,
                (text_x, 90),
                font,
                0.42,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        try:
            legend_msg = self.bridge.cv2_to_imgmsg(
                legend,
                encoding='bgr8',
            )
            self.legend_pub.publish(legend_msg)

        except Exception as exc:
            self.get_logger().error(
                f'Failed to publish thermal legend: {exc}'
            )


def main(args=None):
    rclpy.init(args=args)

    node = ThermalVisualizer()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
