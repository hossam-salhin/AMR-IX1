#!/usr/bin/env python3

import csv
import math
import os
import time
import threading
from datetime import datetime

import cv2
import rclpy
import yaml
from cv_bridge import CvBridge
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.duration import Duration
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import Image
from tf2_ros import Buffer, TransformListener


class InspectionMission(Node):
    def __init__(self):
        super().__init__('inspection_mission')

        self.bridge = CvBridge()

        self.latest_rgb = None
        self.latest_thermal = None
        self.rgb_time = None
        self.thermal_time = None

        self.create_subscription(
            Image,
            '/camera/image',
            self.rgb_callback,
            10
        )

        self.create_subscription(
            Image,
            '/thermal/image',
            self.thermal_callback,
            10
        )

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def rgb_callback(self, msg):
        self.latest_rgb = msg
        self.rgb_time = self.get_clock().now()

    def thermal_callback(self, msg):
        self.latest_thermal = msg
        self.thermal_time = self.get_clock().now()

    def get_robot_pose(self, timeout_sec=3.0):
        start = time.monotonic()

        while time.monotonic() - start < timeout_sec:
            if self.tf_buffer.can_transform(
                'map',
                'base_footprint',
                rclpy.time.Time()
            ):
                transform = self.tf_buffer.lookup_transform(
                    'map',
                    'base_footprint',
                    rclpy.time.Time()
                )

                x = transform.transform.translation.x
                y = transform.transform.translation.y

                q = transform.transform.rotation
                yaw = math.atan2(
                    2.0 * (q.w * q.z + q.x * q.y),
                    1.0 - 2.0 * (q.y * q.y + q.z * q.z)
                )

                return x, y, yaw

        raise RuntimeError(
            "TF map -> base_footprint not available within timeout"
        )

    @staticmethod
    def calculate_pose_error(
        target_x,
        target_y,
        target_yaw,
        actual_x,
        actual_y,
        actual_yaw
    ):
        dx = actual_x - target_x
        dy = actual_y - target_y

        position_error = math.hypot(dx, dy)

        yaw_error = math.atan2(
            math.sin(actual_yaw - target_yaw),
            math.cos(actual_yaw - target_yaw)
        )

        yaw_error_deg = math.degrees(abs(yaw_error))

        return position_error, abs(yaw_error), yaw_error_deg

    def wait_for_images(self, timeout_sec=5.0):
        start = time.monotonic()

        initial_rgb = self.rgb_time
        initial_thermal = self.thermal_time

        while time.monotonic() - start < timeout_sec:
            time.sleep(0.05)

            rgb_fresh = (
                self.latest_rgb is not None
                and self.rgb_time != initial_rgb
            )

            thermal_fresh = (
                self.latest_thermal is not None
                and self.thermal_time != initial_thermal
            )

            if rgb_fresh and thermal_fresh:
                return True

        return False

    def save_images(self, output_dir, station_name):
        if self.latest_rgb is None or self.latest_thermal is None:
            return False, 'Missing image frame'

        try:
            rgb = self.bridge.imgmsg_to_cv2(
                self.latest_rgb,
                desired_encoding='bgr8'
            )

            thermal = self.bridge.imgmsg_to_cv2(
                self.latest_thermal,
                desired_encoding='passthrough'
            )

            rgb_path = os.path.join(
                output_dir,
                f'{station_name}_rgb.png'
            )

            thermal_path = os.path.join(
                output_dir,
                f'{station_name}_thermal.png'
            )

            if not cv2.imwrite(rgb_path, rgb):
                return False, 'Failed to save RGB image'

            if not cv2.imwrite(thermal_path, thermal):
                return False, 'Failed to save thermal image'

            return True, ''

        except Exception as exc:
            return False, str(exc)

    def make_pose(self, x, y, yaw):
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()

        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0

        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)

        return pose


def load_waypoints():
    package_root = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    yaml_path = os.path.join(
        package_root,
        'config',
        'inspection_waypoints.yaml'
    )

    with open(yaml_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

    return data['stations']


def main():
    rclpy.init()

    mission = InspectionMission()
    navigator = BasicNavigator()

    executor = MultiThreadedExecutor()
    executor.add_node(mission)

    executor_thread = threading.Thread(
        target=executor.spin,
        daemon=True
    )
    executor_thread.start()

    stations = load_waypoints()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    output_dir = os.path.expanduser(
        os.path.join(
            '~/ROS2_Master_Journey/AMR_inspection',
            'inspection_runs',
            timestamp
        )
    )

    os.makedirs(output_dir, exist_ok=True)

    csv_path = os.path.join(
        output_dir,
        'inspection_log.csv'
    )

    with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow([
            'station',
            'target_x',
            'target_y',
            'target_yaw',
            'camera_pitch',
            'actual_x',
            'actual_y',
            'actual_yaw',
            'position_error_m',
            'yaw_error_rad',
            'yaw_error_deg',
            'navigation_result',
            'capture_result',
            'timestamp'
        ])

        navigator.waitUntilNav2Active()

        mission.get_logger().info(
            f'Starting inspection mission: {timestamp}'
        )

        for station_name, station in stations.items():
            target_x = float(station['x'])
            target_y = float(station['y'])
            target_yaw = float(station['yaw'])
            camera_pitch = float(station.get('camera_pitch', 0.0))

            mission.get_logger().info(
                f'Navigating to {station_name}'
            )

            goal = mission.make_pose(
                target_x,
                target_y,
                target_yaw
            )

            navigator.goToPose(goal)

            while not navigator.isTaskComplete():
                time.sleep(0.1)

            result = navigator.getResult()

            if result != TaskResult.SUCCEEDED:
                mission.get_logger().error(
                    f'{station_name}: navigation failed'
                )

                writer.writerow([
                    station_name,
                    target_x,
                    target_y,
                    target_yaw,
                    camera_pitch,
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    str(result),
                    'not_attempted',
                    datetime.now().isoformat()
                ])
                csv_file.flush()
                continue

            mission.get_logger().info(
                f'{station_name}: navigation succeeded'
            )

            # Experimental post-SUCCEEDED pose stability check.
            # Only Station 1 and Station 5 are measured.
            if station_name in ('station_1', 'station_5'):
                mission.get_logger().info(
                    f'{station_name}: starting post-SUCCEEDED TF stability check'
                )

                samples = []

                for sample_idx in range(4):
                    try:
                        sample_x, sample_y, sample_yaw = mission.get_robot_pose()

                        samples.append(
                            (sample_x, sample_y, sample_yaw)
                        )

                        mission.get_logger().info(
                            f'{station_name}: '
                            f'TF sample {sample_idx}: '
                            f'({sample_x:.3f}, {sample_y:.3f}, '
                            f'{math.degrees(sample_yaw):.2f} deg)'
                        )

                        if sample_idx < 3:
                            time.sleep(1.0)

                    except Exception as exc:
                        mission.get_logger().warning(
                            f'{station_name}: '
                            f'could not read TF sample {sample_idx}: {exc}'
                        )

                if len(samples) >= 2:
                    first_x, first_y, first_yaw = samples[0]
                    last_x, last_y, last_yaw = samples[-1]

                    delta_position = math.hypot(
                        last_x - first_x,
                        last_y - first_y
                    )

                    delta_yaw = math.atan2(
                        math.sin(last_yaw - first_yaw),
                        math.cos(last_yaw - first_yaw)
                    )

                    mission.get_logger().info(
                        f'{station_name}: post-SUCCEEDED change over '
                        f'{len(samples)} samples: '
                        f'delta_position={delta_position:.4f} m, '
                        f'delta_yaw={math.degrees(delta_yaw):.3f} deg'
                    )

            try:
                actual_x, actual_y, actual_yaw = mission.get_robot_pose()

                position_error_m, yaw_error_rad, yaw_error_deg = (
                    mission.calculate_pose_error(
                        target_x,
                        target_y,
                        target_yaw,
                        actual_x,
                        actual_y,
                        actual_yaw
                    )
                )

                mission.get_logger().info(
                    f'{station_name}: '
                    f'target=({target_x:.3f}, {target_y:.3f}, '
                    f'{math.degrees(target_yaw):.2f} deg), '
                    f'actual=({actual_x:.3f}, {actual_y:.3f}, '
                    f'{math.degrees(actual_yaw):.2f} deg), '
                    f'position_error={position_error_m:.3f} m, '
                    f'yaw_error={yaw_error_deg:.2f} deg'
                )

            except Exception as exc:
                mission.get_logger().warning(
                    f'Could not read actual pose: {exc}'
                )
                actual_x = actual_y = actual_yaw = ''
                position_error_m = yaw_error_rad = yaw_error_deg = ''

            capture_ok = mission.wait_for_images(timeout_sec=5.0)

            if capture_ok:
                capture_result, capture_error = mission.save_images(
                    output_dir,
                    station_name
                )

                if capture_result:
                    capture_status = 'saved'
                    mission.get_logger().info(
                        f'{station_name}: RGB + thermal saved'
                    )
                else:
                    capture_status = f'failed: {capture_error}'
                    mission.get_logger().error(
                        f'{station_name}: capture failed: {capture_error}'
                    )
            else:
                capture_status = 'timeout'
                mission.get_logger().error(
                    f'{station_name}: image capture timeout'
                )

            writer.writerow([
                station_name,
                target_x,
                target_y,
                target_yaw,
                camera_pitch,
                actual_x,
                actual_y,
                actual_yaw,
                position_error_m,
                yaw_error_rad,
                yaw_error_deg,
                'SUCCEEDED',
                capture_status,
                datetime.now().isoformat()
            ])

            csv_file.flush()

    mission.get_logger().info(
        f'Inspection mission finished. Results: {output_dir}'
    )

    mission.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
