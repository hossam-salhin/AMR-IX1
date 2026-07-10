#!/usr/bin/env python3
"""
HELIOS AMR — Core Inspection Mission
======================================
Navigates to 3 real waypoints (captured from a successful Nav2 run),
takes a photo and logs an inspection event at each one.
"""

import os
import csv
import time
from datetime import datetime

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

from nav2_simple_commander.robot_navigator import BasicNavigator


# ──────────────────────────────────────────────────────────────
# WAYPOINTS — real coordinates from your successful factory run
# ──────────────────────────────────────────────────────────────

INITIAL_POSE = {
    'x': 32.7520, 'y': 3.0,
    'z': 0.0, 'w': 1.0   # quaternion facing +X
}

WAYPOINTS = [
    {
        'name': 'Station_1',
        'x': -21.945037841796875, 'y': 15.14472770690918,
        'z': -0.615411894250506, 'w': 0.788205684079355
    },
    {
        'name': 'Station_2',
        'x': -17.29313850402832, 'y': 29.819202423095703,
        'z': 0.9766864726122415, 'w': 0.21467075771109875
    },
    {
        'name': 'Station_3',
        'x': -9.162374496459961, 'y': 26.9901123046875,
        'z': -0.7433757215128377, 'w': 0.6688740813226866
    },
]

CAMERA_TOPIC = '/camera/image'
OUTPUT_DIR = os.path.expanduser('~/ROS2_Master_Journey/AMR_inspection/inspection_logs')


class InspectionMission(Node):
    def __init__(self):
        super().__init__('inspection_mission')
        self.bridge = CvBridge()
        self.latest_image = None

        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT,
                          history=HistoryPolicy.KEEP_LAST)
        self.create_subscription(Image, CAMERA_TOPIC, self.image_callback, qos)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.log_path = os.path.join(OUTPUT_DIR, 'inspection_log.csv')
        with open(self.log_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['waypoint', 'timestamp', 'image_file', 'x', 'y'])

        self.get_logger().info(f'Inspection log: {self.log_path}')

    def image_callback(self, msg):
        self.latest_image = msg

    def capture_at_waypoint(self, wp):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_filename = f"{wp['name']}_{timestamp}.jpg"
        image_path = os.path.join(OUTPUT_DIR, image_filename)

        if self.latest_image is not None:
            cv_image = self.bridge.imgmsg_to_cv2(self.latest_image, desired_encoding='bgr8')
            cv2.imwrite(image_path, cv_image)
            self.get_logger().info(f'📷 Captured: {image_filename}')
        else:
            self.get_logger().warn('No image received — skipping capture')
            image_filename = 'NO_IMAGE'

        with open(self.log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([wp['name'], timestamp, image_filename, wp['x'], wp['y']])

        self.get_logger().info(f"✅ Logged inspection event at {wp['name']}")


def make_pose(navigator, x, y, z, w):
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.z = z
    pose.pose.orientation.w = w
    return pose


def main():
    rclpy.init()
    mission_node = InspectionMission()
    navigator = BasicNavigator()

    initial = make_pose(navigator, INITIAL_POSE['x'], INITIAL_POSE['y'],
                         INITIAL_POSE['z'], INITIAL_POSE['w'])
    navigator.setInitialPose(initial)
    navigator.waitUntilNav2Active()

    for wp in WAYPOINTS:
        goal = make_pose(navigator, wp['x'], wp['y'], wp['z'], wp['w'])
        mission_node.get_logger().info(f"🚗 Navigating to {wp['name']}")
        navigator.goToPose(goal)

        while not navigator.isTaskComplete():
            rclpy.spin_once(mission_node, timeout_sec=0.1)

        result = navigator.getResult()
        mission_node.get_logger().info(f"Arrived at {wp['name']} — result: {result}")

        time.sleep(1.0)
        for _ in range(5):
            rclpy.spin_once(mission_node, timeout_sec=0.2)
        mission_node.capture_at_waypoint(wp)

    mission_node.get_logger().info("🏁 Inspection mission complete.")
    navigator.lifecycleShutdown()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
