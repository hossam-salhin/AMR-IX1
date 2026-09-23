import math
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path, OccupancyGrid

class PathClearance(Node):
    def __init__(self):
        super().__init__('path_clearance')
        self.path = None
        self.costmap = None

        self.create_subscription(Path, '/plan', self.path_cb, 10)

        qos = rclpy.qos.QoSProfile(
            depth=1,
            reliability=rclpy.qos.ReliabilityPolicy.RELIABLE,
            durability=rclpy.qos.DurabilityPolicy.TRANSIENT_LOCAL
        )

        self.create_subscription(
            OccupancyGrid,
            '/global_costmap/costmap',
            self.map_cb,
            qos
        )

    def path_cb(self, msg):
        self.path = msg
        self.measure()

    def map_cb(self, msg):
        self.costmap = msg
        self.measure()

    def measure(self):
        if self.path is None or self.costmap is None:
            return

        info = self.costmap.info
        data = self.costmap.data

        obstacles = []

        for my in range(info.height):
            for mx in range(info.width):
                if data[my * info.width + mx] >= 254:
                    x = info.origin.position.x + (mx + 0.5) * info.resolution
                    y = info.origin.position.y + (my + 0.5) * info.resolution
                    obstacles.append((x, y))

        if not obstacles:
            print("No lethal obstacle cells found.")
            return

        clearances = []

        for pose in self.path.poses:
            x = pose.pose.position.x
            y = pose.pose.position.y

            min_d = min(
                math.hypot(x - ox, y - oy)
                for ox, oy in obstacles
            )

            clearances.append(min_d)

        print("\n===== PATH CLEARANCE =====")
        print(f"PATH CELLS : {len(clearances)}")
        print(f"MIN        : {min(clearances):.3f} m")
        print(f"AVG        : {sum(clearances)/len(clearances):.3f} m")
        print(f"MAX        : {max(clearances):.3f} m")
        print("==========================")

        self.path = None

def main():
    rclpy.init()
    node = PathClearance()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
