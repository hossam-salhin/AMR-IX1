#!/usr/bin/env python3

import math
import threading
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from tf2_ros import Buffer, TransformListener

CAMERA_JOINT = 'cam_stand_joint'
CAMERA_CONTROLLER_TOPIC = '/cam_stand_controller/joint_trajectory'
CAMERA_MIN_PITCH = -0.7854
CAMERA_MAX_PITCH = 0.2
CAMERA_COMMAND_DURATION = 2.0
CAMERA_TOLERANCE = 0.01


class WaypointRecorder(Node):
    def __init__(self):
        super().__init__('waypoint_recorder')

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.latest_camera_pitch = None

        self.camera_state_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.camera_state_callback,
            10
        )

        self.camera_command_pub = self.create_publisher(
            JointTrajectory,
            CAMERA_CONTROLLER_TOPIC,
            10
        )

    def camera_state_callback(self, msg):
        if CAMERA_JOINT not in msg.name:
            return

        index = msg.name.index(CAMERA_JOINT)

        if index < len(msg.position):
            self.latest_camera_pitch = float(msg.position[index])

    def get_camera_pitch(self, timeout_sec=3.0):
        start = time.monotonic()

        while time.monotonic() - start < timeout_sec:
            if self.latest_camera_pitch is not None:
                return self.latest_camera_pitch

            time.sleep(0.05)

        raise RuntimeError(
            f'Joint state for {CAMERA_JOINT} is not available'
        )

    def set_camera_pitch(self, pitch, timeout_sec=8.0):
        if not CAMERA_MIN_PITCH <= pitch <= CAMERA_MAX_PITCH:
            raise ValueError(
                f'Camera pitch must be between '
                f'{CAMERA_MIN_PITCH:.4f} and {CAMERA_MAX_PITCH:.4f} rad'
            )

        start = time.monotonic()

        while (
            self.camera_command_pub.get_subscription_count() == 0
            and time.monotonic() - start < 3.0
        ):
            time.sleep(0.05)

        if self.camera_command_pub.get_subscription_count() == 0:
            raise RuntimeError(
                f'No subscriber found on {CAMERA_CONTROLLER_TOPIC}'
            )

        trajectory = JointTrajectory()
        trajectory.joint_names = [CAMERA_JOINT]

        point = JointTrajectoryPoint()
        point.positions = [pitch]
        point.time_from_start = rclpy.duration.Duration(
            seconds=CAMERA_COMMAND_DURATION
        ).to_msg()

        trajectory.points = [point]
        self.camera_command_pub.publish(trajectory)

        start = time.monotonic()

        while time.monotonic() - start < timeout_sec:
            if (
                self.latest_camera_pitch is not None
                and abs(self.latest_camera_pitch - pitch) <= CAMERA_TOLERANCE
            ):
                return self.latest_camera_pitch

            time.sleep(0.05)

        raise RuntimeError(
            f'Camera stand did not reach target {pitch:.4f} rad '
            f'within {timeout_sec:.1f} s'
        )

    def get_current_pose(self):
        if not self.tf_buffer.can_transform(
            'map',
            'base_footprint',
            rclpy.time.Time(),
            timeout=rclpy.duration.Duration(seconds=2.0)
        ):
            raise RuntimeError('TF map -> base_footprint is not available')

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


def main():
    rclpy.init()

    node = WaypointRecorder()

    spin_thread = threading.Thread(
        target=rclpy.spin,
        args=(node,),
        daemon=True
    )
    spin_thread.start()

    print('\nAMR-IX1 Waypoint Recorder')
    print('Frame: map -> base_footprint')
    print(
        f'Camera stand joint: {CAMERA_JOINT} '
        f'[{CAMERA_MIN_PITCH:.4f}, {CAMERA_MAX_PITCH:.4f}] rad'
    )
    print('Move the robot to the desired station.')
    print('The recorder will set and save the camera pitch for that station.')
    print('Type q + ENTER at the station-name prompt to quit.\n')

    try:
        while rclpy.ok():
            name = input('Station name: ').strip()

            if name.lower() == 'q':
                break

            if not name:
                print('Station name cannot be empty.\n')
                continue

            try:
                current_pitch = node.get_camera_pitch()

                print(
                    f'Current camera pitch: '
                    f'{math.degrees(current_pitch):.2f} deg '
                    f'({current_pitch:.6f} rad)'
                )

                pitch_text = input(
                    'Camera pitch in degrees (blank = keep current): '
                ).strip()

                if pitch_text:
                    target_pitch = math.radians(float(pitch_text))
                    actual_pitch = node.set_camera_pitch(target_pitch)
                else:
                    actual_pitch = current_pitch

                x, y, yaw = node.get_current_pose()

                print(f'\n{name}:')
                print(f'  x            = {x:.6f}')
                print(f'  y            = {y:.6f}')
                print(
                    f'  yaw          = {yaw:.6f} rad '
                    f'({math.degrees(yaw):.2f} deg)'
                )
                print(
                    f'  camera_pitch = {actual_pitch:.6f} rad '
                    f'({math.degrees(actual_pitch):.2f} deg)'
                )

                print('\nYAML:')
                print(f'  {name}:')
                print(f'    x: {x:.6f}')
                print(f'    y: {y:.6f}')
                print(f'    yaw: {yaw:.6f}')
                print(f'    camera_pitch: {actual_pitch:.6f}')
                print()

            except ValueError as exc:
                print(f'Invalid camera pitch: {exc}\n')
            except Exception as exc:
                print(f'Could not record waypoint: {exc}\n')

    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        spin_thread.join(timeout=1.0)


if __name__ == '__main__':
    main()