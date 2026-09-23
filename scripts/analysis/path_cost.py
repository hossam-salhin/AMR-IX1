import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path, OccupancyGrid

class PathCost(Node):
    def __init__(self):
        super().__init__('path_cost')
        self.path = None
        self.costmap = None

        self.create_subscription(
            Path, '/plan', self.path_cb,
            10
        )

        self.create_subscription(
            OccupancyGrid, '/global_costmap/costmap', self.map_cb,
            rclpy.qos.QoSProfile(
                depth=1,
                reliability=rclpy.qos.ReliabilityPolicy.RELIABLE,
                durability=rclpy.qos.DurabilityPolicy.TRANSIENT_LOCAL
            )
        )

    def path_cb(self, msg):
        self.path = msg
        self.try_measure()

    def map_cb(self, msg):
        self.costmap = msg
        self.try_measure()

    def try_measure(self):
        if self.path is None or self.costmap is None:
            return

        info = self.costmap.info
        data = self.costmap.data

        costs = []

        for pose in self.path.poses:
            x = pose.pose.position.x
            y = pose.pose.position.y

            mx = int((x - info.origin.position.x) / info.resolution)
            my = int((y - info.origin.position.y) / info.resolution)

            if 0 <= mx < info.width and 0 <= my < info.height:
                cost = data[my * info.width + mx]

                if cost >= 0:
                    costs.append(cost)

        if not costs:
            return

        zero = sum(c == 0 for c in costs)
        nonzero = sum(c > 0 for c in costs)
        high = sum(c >= 50 for c in costs)
        avg = sum(costs) / len(costs)

        print('\n===== PATH COST RESULT =====')
        print(f'PATH CELLS : {len(costs)}')
        print(f'MIN        : {min(costs)}')
        print(f'MAX        : {max(costs)}')
        print(f'AVG        : {avg:.2f}')
        print(f'ZERO       : {zero}')
        print(f'NONZERO    : {nonzero}')
        print(f'>=50       : {high}')
        print(f'>=90       : {sum(c >= 90 for c in costs)}')
        print('============================')

        self.path = None

def main():
    rclpy.init()
    node = PathCost()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
