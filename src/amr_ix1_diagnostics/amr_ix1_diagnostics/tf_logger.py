#!/usr/bin/env python3

import math
import os
import time
from datetime import datetime, timezone

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener, TransformException


class TFLogger(Node):
    def __init__(self):
        super().__init__('tf_logger')

        self.declare_parameter('parent_frame', 'map')
        self.declare_parameter('child_frame', 'base_footprint')
        self.declare_parameter('sample_rate_hz', 10.0)
        self.declare_parameter('output_file', '')

        parent_frame = self.get_parameter(
            'parent_frame'
        ).get_parameter_value().string_value

        child_frame = self.get_parameter(
            'child_frame'
        ).get_parameter_value().string_value

        sample_rate_hz = self.get_parameter(
            'sample_rate_hz'
        ).get_parameter_value().double_value

        output_file = self.get_parameter(
            'output_file'
        ).get_parameter_value().string_value

        if sample_rate_hz <= 0.0:
            raise ValueError('sample_rate_hz must be greater than zero')

        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = os.path.expanduser(
                '~/ROS2_Master_Journey/AMR_inspection/tf_logs'
            )
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(
                output_dir, f'tf_trace_{timestamp}.txt'
            )
        else:
            output_file = os.path.abspath(
                os.path.expanduser(output_file)
            )
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

        self.parent_frame = parent_frame
        self.child_frame = child_frame
        self.output_path = output_file

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(
            self.tf_buffer, self
        )

        self.file = open(
            self.output_path, 'w', encoding='utf-8', buffering=1
        )

        self.file.write(
            'record_time_utc,record_time_unix,tf_time_sec,tf_time_nanosec,'
            'parent_frame,child_frame,x_m,y_m,z_m,'
            'roll_rad,pitch_rad,yaw_rad,yaw_deg\n'
        )

        self.timer = self.create_timer(
            1.0 / sample_rate_hz, self.record_transform
        )

        self.get_logger().info(
            f'TF logging started: {parent_frame} -> {child_frame}'
        )
        self.get_logger().info(
            f'Sampling rate: {sample_rate_hz:.2f} Hz'
        )
        self.get_logger().info(
            f'Output file: {self.output_path}'
        )

    @staticmethod
    def quaternion_to_euler(q):
        sinr_cosp = 2.0 * (q.w * q.x + q.y * q.z)
        cosr_cosp = 1.0 - 2.0 * (q.x * q.x + q.y * q.y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2.0 * (q.w * q.y - q.z * q.x)
        pitch = math.asin(
            max(-1.0, min(1.0, sinp))
        )

        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return roll, pitch, yaw

    def record_transform(self):
        record_time = time.time()
        record_time_utc = datetime.now(
            timezone.utc
        ).isoformat(timespec='milliseconds')

        try:
            transform = self.tf_buffer.lookup_transform(
                self.parent_frame,
                self.child_frame,
                Time()
            )

            tf_stamp = transform.header.stamp
            translation = transform.transform.translation
            rotation = transform.transform.rotation

            roll, pitch, yaw = self.quaternion_to_euler(rotation)

            self.file.write(
                f'{record_time_utc},{record_time:.6f},'
                f'{tf_stamp.sec},{tf_stamp.nanosec},'
                f'{self.parent_frame},{self.child_frame},'
                f'{translation.x:.6f},{translation.y:.6f},'
                f'{translation.z:.6f},'
                f'{roll:.6f},{pitch:.6f},{yaw:.6f},'
                f'{math.degrees(yaw):.3f}\n'
            )

        except TransformException as exc:
            self.get_logger().warning(
                f'TF lookup failed: {exc}',
                throttle_duration_sec=5.0
            )

    def destroy_node(self):
        if hasattr(self, 'file') and not self.file.closed:
            self.file.flush()
            self.file.close()

        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = TFLogger()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f'TF Logger error: {exc}')
        raise
    finally:
        if node is not None:
            node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
