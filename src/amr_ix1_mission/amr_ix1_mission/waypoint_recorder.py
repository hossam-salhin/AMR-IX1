#!/usr/bin/env python3

import math
import threading

import rclpy
from rclpy.node import Node
from tf2_ros import Buffer, TransformListener


class WaypointRecorder(Node):
    def __init__(self):
        super().__init__('waypoint_recorder')

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

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
    print('Move the robot to the desired station, then press ENTER.')
    print('Type q + ENTER to quit.\n')

    try:
        while rclpy.ok():
            name = input('Station name: ').strip()

            if name.lower() == 'q':
                break

            if not name:
                print('Station name cannot be empty.\n')
                continue

            try:
                x, y, yaw = node.get_current_pose()

                print(f'\n{name}:')
                print(f'  x   = {x:.6f}')
                print(f'  y   = {y:.6f}')
                print(f'  yaw = {yaw:.6f} rad ({math.degrees(yaw):.2f} deg)')
                print()

            except Exception as exc:
                print(f'Could not read robot pose: {exc}\n')

    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        spin_thread.join(timeout=1.0)


if __name__ == '__main__':
    main()
