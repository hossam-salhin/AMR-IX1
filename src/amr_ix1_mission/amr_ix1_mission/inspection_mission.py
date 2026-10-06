#!/usr/bin/env python3

import csv
import math
import os
import time
from datetime import datetime

import cv2
import rclpy
import yaml
from cv_bridge import CvBridge
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.duration import Duration
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

    def get_robot_pose(self):
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

    def wait_for_images(self, timeout_sec=5.0):
        start = time.monotonic()

        initial_rgb = self.rgb_time
        initial_thermal = self.thermal_time

        while time.monotonic() - start < timeout_sec:
            rclpy.spin_once(self, timeout_sec=0.05)

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
                rclpy.spin_once(mission, timeout_sec=0.1)

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
                    str(result),
                    'not_attempted',
                    datetime.now().isoformat()
                ])
                csv_file.flush()
                continue

            mission.get_logger().info(
                f'{station_name}: navigation succeeded'
            )

            try:
                actual_x, actual_y, actual_yaw = mission.get_robot_pose()
            except Exception as exc:
                mission.get_logger().warning(
                    f'Could not read actual pose: {exc}'
                )
                actual_x = actual_y = actual_yaw = ''

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
                'SUCCEEDED',
                capture_status,
                datetime.now().isoformat()
            ])

            csv_file.flush()

    mission.get_logger().info(
        f'Inspection mission finished. Results: {output_dir}'
    )

    navigator.lifecycleShutdown()

    mission.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
