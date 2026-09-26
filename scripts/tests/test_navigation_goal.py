#!/usr/bin/env python3

import math
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from tf2_ros import Buffer, TransformListener


class NavigationGoalTest(Node):

    def __init__(self):
        super().__init__('navigation_goal_test')

        self.action_client = ActionClient(
            self,
            NavigateToPose,
            '/navigate_to_pose'
        )

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Goal copied from RViz /goal_pose
        self.goal_x = 21.883745193481445
        self.goal_y = -28.46511459350586

        # RViz goal quaternion
        self.goal_z = 0.007747706251893465
        self.goal_w = 0.9999699860734993

        self.send_goal()

    def quaternion_to_yaw(self, z, w):
        return math.atan2(
            2.0 * w * z,
            1.0 - 2.0 * z * z
        )

    def send_goal(self):
        self.get_logger().info('Waiting for Nav2 action server...')

        if not self.action_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error('Nav2 action server not available.')
            rclpy.shutdown()
            return

        goal_msg = NavigateToPose.Goal()

        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()

        goal_msg.pose.pose.position.x = self.goal_x
        goal_msg.pose.pose.position.y = self.goal_y
        goal_msg.pose.pose.position.z = 0.0

        goal_msg.pose.pose.orientation.z = self.goal_z
        goal_msg.pose.pose.orientation.w = self.goal_w

        goal_yaw = self.quaternion_to_yaw(
            self.goal_z,
            self.goal_w
        )

        self.get_logger().info(
            f'Goal: x={self.goal_x:.3f}, '
            f'y={self.goal_y:.3f}, '
            f'yaw={math.degrees(goal_yaw):.2f} deg'
        )

        future = self.action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )

        future.add_done_callback(self.goal_response_callback)

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback

        self.get_logger().info(
            f'Distance remaining: '
            f'{feedback.distance_remaining:.3f} m'
        )

    def goal_response_callback(self, future):
        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().error('Goal was rejected.')
            rclpy.shutdown()
            return

        self.get_logger().info('Goal accepted.')

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.goal_result_callback)

    def goal_result_callback(self, future):
        result = future.result()
        status = result.status

        self.get_logger().info(
            f'Nav2 finished with status: {status}'
        )
        self.get_logger().info('Waiting 1.0 second for robot to settle...')
        time.sleep(1.0)

        self.get_logger().info(
            'Reading final map -> base_link transform...'
        )
        

        try:
            transform = self.tf_buffer.lookup_transform(
                'map',
                'base_link',
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=3.0)
            )

            x = transform.transform.translation.x
            y = transform.transform.translation.y

            z = transform.transform.rotation.z
            w = transform.transform.rotation.w

            actual_yaw = self.quaternion_to_yaw(z, w)
            goal_yaw = self.quaternion_to_yaw(
                self.goal_z,
                self.goal_w
            )

            dx = x - self.goal_x
            dy = y - self.goal_y

            position_error = math.sqrt(
                dx * dx + dy * dy
            )

            yaw_error = math.atan2(
                math.sin(actual_yaw - goal_yaw),
                math.cos(actual_yaw - goal_yaw)
            )

            self.get_logger().info('========== FINAL RESULT ==========')

            self.get_logger().info(
                f'Goal pose:   '
                f'x={self.goal_x:.3f}, '
                f'y={self.goal_y:.3f}, '
                f'yaw={math.degrees(goal_yaw):.2f} deg'
            )

            self.get_logger().info(
                f'Actual pose: '
                f'x={x:.3f}, '
                f'y={y:.3f}, '
                f'yaw={math.degrees(actual_yaw):.2f} deg'
            )

            self.get_logger().info(
                f'Position error: {position_error:.3f} m'
            )

            self.get_logger().info(
                f'Yaw error: '
                f'{math.degrees(abs(yaw_error)):.2f} deg'
            )

            self.get_logger().info(
                '================================='
            )

        except Exception as e:
            self.get_logger().error(
                f'Failed to read final TF: {e}'
            )

        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)

    node = NavigationGoalTest()

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
