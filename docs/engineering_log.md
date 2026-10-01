# AMR-IX1 Engineering Log

## 2026-09-23 — Session 1

### Goal
Reorganize the repository structure without affecting the working ROS 2 simulation and navigation system.

### What we changed
- Moved obsolete navigation and world files into `legacy/`.
- Renamed navigation map files to clearer project-specific names.
- Moved analysis scripts into `scripts/analysis/`.
- Updated Gazebo and Navigation launch files to use the current project world and map.
- Updated the global costmap inflation configuration used during navigation testing.
- Removed an inactive `use_astar` configuration entry from the active planner configuration.

### Validation
- ROS 2 workspace built successfully.
- Gazebo launched successfully.
- AMR spawned correctly.
- Navigation launched successfully.
- Main AMR-IX1 map loaded successfully.
- Repository working tree was clean after the changes.

### Git
Commit:
`18a80cc — chore(repo): reorganize project structure`

Pushed successfully to GitHub.

### Decision
The repository cleanup is complete. Future navigation experiments will be developed separately from this cleanup commit.

### Next Step
Continue navigation validation and investigate remaining navigation behavior, particularly goal orientation and performance on the main inspection map.


## 2026-09-25 — session 2 (Navigation Goal Orientation Validation)

### Goal
Validate the final navigation pose after investigating the incorrect final yaw behavior.

### Runtime Test Configuration
The following parameters were changed temporarily at runtime from the terminal and were NOT yet committed to the YAML configuration:

- `GridBased.use_final_approach_orientation = false`
- `general_goal_checker.xy_goal_tolerance = 0.10 m`
- `general_goal_checker.yaw_goal_tolerance = 0.10 rad`

### Test Map
The navigation test was performed using `testing_map.yaml` instead of the main inspection map.

This map was selected as a lighter validation environment to maintain more stable RTF while investigating and validating the final goal orientation behavior.

The main inspection map remains the primary project map and was not replaced by the testing map.

### Gazebo Test Environment
The navigation validation was run in the dedicated warehouse test environment.

The Gazebo launch configuration was updated to:
- Use the project `models` directory for Gazebo model resources.
- Launch `tugbot_warehouse.sdf`.
- Spawn the AMR at the corresponding warehouse test starting pose.

These launch changes are part of the validation environment used during the navigation orientation investigation.

### Test Goal
RViz `/goal_pose`:

- x = 21.884 m
- y = -28.465 m
- yaw = 0.89°

### Settling
A 1-second settling delay was added to the test script before reading the final `map -> base_link` transform.

### Final Result
- Nav2 status: `SUCCEEDED`
- Position error: **0.089 m (89 mm)**
- Yaw error: **5.39°**
- XY tolerance: 0.10 m (100 mm)
- Yaw tolerance: 0.10 rad (~5.73°)

Both final errors were within the temporary runtime tolerances.

### A/B Test Finding
With `GridBased.use_final_approach_orientation = true`, the final path orientation caused a large final yaw error of approximately **52.89°**.

With the parameter set to `false` at runtime, the same goal produced a final yaw error of **5.39°** after the 1-second settling period.

### Decision
The runtime test supports keeping `GridBased.use_final_approach_orientation = false` for the next navigation validation.

The YAML configuration has NOT been changed yet. The runtime parameter changes should be made persistent only after the navigation behavior is fully validated.

### Next Step
Before making persistent configuration changes, continue controlled navigation validation and then update the YAML and commit the validated configuration.

## 2026-09-26 — Session 3 (Navigation Goal Orientation & Tolerance Validation)

### Objective

Finalize the navigation goal orientation behavior and validate practical position/yaw goal tolerances.

### Goal Orientation Investigation

The previous configuration used:

```yaml
use_final_approach_orientation: true
```

A controlled A/B test was performed using the same navigation goal.

#### Result with `use_final_approach_orientation = true`

- Position error: approximately `0.128 m`
- Yaw error: approximately `53.35°`
- Nav2 result: `SUCCEEDED`

Inspection of the final planned path showed that the path orientation near the goal differed significantly from the requested goal orientation.

#### Result with `use_final_approach_orientation = false`

Using the same goal:

- Position error: approximately `0.128 m`
- Yaw error: approximately `8.42°`
- Nav2 result: `SUCCEEDED`

The large final yaw error observed with the previous configuration was strongly associated with `use_final_approach_orientation = true`.

### Second Goal Validation

A second goal with a different requested orientation was tested to verify that the behavior was not specific to the first goal.

Target:

- Position: approximately `(20.5, -28.0)`
- Yaw: `90°`

Final measured pose:

- Position: approximately `(20.534, -28.174)`
- Yaw: approximately `95.63°`

Results:

- Position error: approximately `0.177 m`
- Yaw error: approximately `5.63°`

The robot successfully reached the second goal with a final orientation close to the requested orientation.

### Persistent Configuration Changes

Based on the controlled tests, the planner configuration was changed from:

```yaml
use_final_approach_orientation: true
```

to:

```yaml
use_final_approach_orientation: false
```

The goal checker tolerances were then reduced.

Previous values:

```yaml
xy_goal_tolerance: 0.15
yaw_goal_tolerance: 0.15
```

Validated values:

```yaml
xy_goal_tolerance: 0.10
yaw_goal_tolerance: 0.10
```

### Final Tolerance Validation

The same navigation goal was tested after restarting the navigation stack with the new persistent configuration.

Final action result:

- Nav2 result: `SUCCEEDED`
- Position error: `0.104 m`
- Yaw error: `3.95°`

A subsequent stable TF measurement after the robot had completely stopped showed:

- Position: approximately `(21.768, -28.426)`
- Yaw: approximately `-2.76°`
- Position error: approximately `0.123 m`
- Yaw error: approximately `3.65°`

The difference between the action-result measurement and the later TF measurement is due to the measurements being taken at different times after the navigation action completed.

### Final Validated Configuration

```yaml
general_goal_checker:
  plugin: "nav2_controller::SimpleGoalChecker"
  xy_goal_tolerance: 0.10
  yaw_goal_tolerance: 0.10
  stateful: true
```

Planner:

```yaml
use_final_approach_orientation: false
```

### Decision

The validated configuration will be kept as the current navigation baseline.

Further reduction of goal tolerances is not justified at this stage because the observed positional error can still vary around the 10 cm target. Additional tuning can be considered later if improved localization or control accuracy is required.

### Engineering Conclusion

The final goal orientation issue was investigated using controlled navigation tests and an A/B comparison of the planner's final approach orientation behavior.

Disabling `use_final_approach_orientation` reduced the observed final yaw error from approximately `53°` to single-digit degrees across multiple goals while maintaining comparable positional accuracy.

The goal checker tolerances were subsequently reduced to:

- `0.10 m` XY tolerance
- `0.10 rad` yaw tolerance (~`5.7°`)

The navigation goal orientation and tolerance configuration is now considered validated for the current simulation baseline.


## 2026-09-28 — Session 4 (Dynamic Obstacle Replanning Investigation)

### Objective

Investigate Nav2 behavior when previously unknown obstacles block a corridor entrance and determine how dynamic LiDAR observations affect the global and local costmaps and path replanning.

### Test Setup

- Navigation stack: Nav2
- Global planner: SmacPlanner2D
- Local controller: Regulated Pure Pursuit
- LiDAR topic: `/lidar`
- Obstacle type: two simulated cubes placed near a corridor entrance
- A small gap was intentionally left between the two cubes
- Robot footprint:
  `[[0.42,0.51],[0.42,-0.51],[-0.42,-0.51],[-0.42,0.51]]`

### Relevant Costmap Configuration

Global costmap:
- `rolling_window: false`
- Plugins:
  - `static_layer`
  - `obstacle_layer`
  - `inflation_layer`
- Obstacle source: `/lidar`
- `clearing: true`

Local costmap:
- `rolling_window: true`
- Configured width/height: `5 m × 5 m`
- Obstacle source: `/lidar`
- `clearing: true`
- `inflation_radius: 0.45 m`

> Note: During the live investigation, the local costmap was temporarily expanded to `7 m × 7 m` using runtime parameters to test whether a larger observation window would eliminate the path switching. The larger window did not resolve the behavior. The persistent configuration was kept at `5 m × 5 m`.

### Observations

1. When the robot was far from the obstacle pair, the global costmap contained obstacle inflation and Nav2 was able to plan toward the corridor.

2. As the robot moved toward the obstacle pair, the observed obstacle/inflation representation in the global costmap changed depending on the robot pose and LiDAR visibility.

3. When the robot approached the obstacle pair from another direction, parts of the previously visible inflation disappeared from the global costmap.

4. The local costmap showed the obstacle currently visible within the LiDAR observation area, but the complete inflated representation was not always visible around the obstacle pair.

5. With the goal placed inside the blocked corridor, the global path repeatedly switched between the left and right sides of the obstacle pair.

6. In some runs, the robot remained almost stationary because the path changed repeatedly before meaningful movement could occur.

7. In another run, the robot eventually committed to one side, but continued replanning as it approached the obstacles.

8. The global planner publishes `/plan` at approximately `0.93 Hz` under normal conditions, corresponding to roughly one plan per `1.07 s`.

9. During the problematic run, large gaps appeared in `/plan` publication, with observed intervals reaching approximately `3.55 s`, `5.68 s`, and `7.70 s`.

10. Increasing the local costmap from `3 m × 3 m` to `7 m × 7 m` during runtime did not eliminate the path-switching behavior.

### Current Interpretation

The behavior is reproducible and is associated with dynamic obstacle observations from the LiDAR being incorporated into the global costmap while obstacle clearing/raytracing changes the observed obstacle representation as the robot moves.

The global planner subsequently replans using the changing costmap and may select different candidate paths around the obstacle pair.

However, the exact root cause of the repeated left/right path switching has **not yet been isolated**. In particular, it has not yet been conclusively determined whether the dominant factor is:

- LiDAR clearing/raytracing,
- obstacle persistence in the global costmap,
- planner replanning behavior,
- the narrow gap between the obstacles,
- or interaction between the planner, controller, and behavior tree.

The local costmap was persistently changed from 3 m × 3 m to 5 m × 5 m for the current navigation configuration. This change did not resolve the observed path-switching behavior.

### Result

**Status: Investigation ongoing / root cause not yet isolated.**

The dynamic obstacle test is considered a reproducible limitation/failure case and will be investigated separately from the previously validated navigation baseline.

## 2026-09-29 — session 5 (Dynamic Obstacle Replanning Investigation)

### Goal
Investigate the repeated left/right path oscillation observed when Nav2 encounters dynamic obstacles blocking a corridor entrance.

### What We Changed

- Tested dynamic obstacle avoidance using two simulated cubes placed near the corridor entrance.
- Increased local costmap `width` and `height` at runtime up to `8 × 8`.
- Increased `observation_persistence` for both local and global obstacle layers at runtime.
- Tested obstacle-layer `clearing` behavior.
- Increased SmacPlanner2D `cost_travel_multiplier` from `2.0` to `5.0`.
- Verified the global costmap using the full `/global_costmap/costmap_raw` data instead of the truncated default ROS 2 topic output.

### Validation

The global costmap was confirmed to contain actual lethal and inflated obstacle cells:

- Total cells: `937,791`
- Lethal cells (`254`): `20,491`
- Inscribed cells (`253`): `151,377`
- Free cells (`0`): `332,616`
- Costed cells (`1–252`): `433,307`

This confirms that LiDAR obstacle marking and costmap obstacle representation are working.

However, the dynamic navigation behavior remained unchanged.

Observed behavior:

1. The planner initially generates a path around one side of the obstacle.
2. As the robot approaches that route, the path becomes blocked.
3. Nav2 replans toward the opposite side.
4. The new path may pass through or very close to the inflated region on the opposite side.
5. As the robot approaches the new route, the planner changes the path again.
6. The robot repeatedly switches between the two sides, producing left/right path oscillation.
7. In some attempts, the robot nearly stopped or interacted physically with the simulated obstacle.
8. RPP also reported collision detection during some attempts.

Increasing local costmap size, obstacle persistence, and SmacPlanner2D cost weighting did not resolve the behavior.

### Problems / Findings

- The issue is not simply caused by missing obstacle marking.
- Lethal obstacle cells (`254`) are present in the global costmap.
- Increasing `observation_persistence` only made obstacle information remain visible for longer; it did not prevent the planner from selecting the opposite inflated region.
- Increasing the local costmap size did not change the oscillation.
- Increasing `cost_travel_multiplier` from `2.0` to `5.0` did not produce a meaningful improvement.
- The remaining problem appears to involve the interaction between dynamic costmap updates, global replanning, inflated costs, and controller/recovery behavior.

### Decision

Stop parameter tuning for this issue temporarily.

The current evidence is sufficient to investigate the underlying Nav2 planning/replanning behavior instead of continuing to modify costmap parameters blindly.

A deeper analysis will be performed before making further configuration changes.

### Next Step

Analyze the dynamic-obstacle behavior with an external ROS2/Nav2 review and identify the highest-probability root causes and the minimum number of targeted experiments required to resolve the issue.

## 2026-10-01 — session 6 (Dynamic Obstacle Replanning Stabilization)

### Goal

Continue the dynamic-obstacle navigation investigation from the previous sessions and identify a practical, stable configuration for global replanning around the simulated obstacle pair.

The objective was not to find mathematically optimal Nav2 parameters, but to obtain a sufficiently stable engineering configuration that can be validated further during the remaining simulation work and later adapted to the real robot.

### Previous Investigation Summary

The dynamic-obstacle scenario consists of two simulated cubes positioned near a corridor entrance.

The previously observed behavior was:

1. The global planner initially selected one side of the obstacle pair.
2. As the robot approached, LiDAR visibility and obstacle representation changed.
3. The inflated obstacle regions in the global costmap changed with the robot pose.
4. The planner could select the opposite side.
5. Repeated replanning sometimes caused left/right path switching.
6. In some runs the robot remained almost stationary while the planner/controller repeatedly reacted to the changing path.
7. Increasing the local costmap size, obstacle persistence, and `cost_travel_multiplier` did not resolve the behavior.
8. The exact problem was therefore considered to involve the interaction between obstacle observation, costmap updates, global replanning, and controller behavior.

### Experiment 6A — Raytrace Range

The effect of `raytrace_max_range` was investigated separately for the global and local costmaps.

The initial baseline was:

* Global costmap: `raytrace_max_range = 3.0 m`
* Local costmap: `raytrace_max_range = 3.0 m`

The value was then changed to:

* Global costmap: `raytrace_max_range = 2.7 m`
* Local costmap: `raytrace_max_range = 3.0 m`

`obstacle_max_range` was explicitly set to `2.5 m` for both costmaps. This matches the previously observed/default effective value and was not intended as an additional behavioral change.

### Experiment 6A Results

The global-only `2.7 m` configuration produced noticeably more stable behavior than the previous `3.0 m` configuration.

Two independent runs were performed.

Observed behavior:

1. The robot approached the obstacle pair.
2. Obstacle inflation appeared in the global costmap.
3. The planner changed to the alternative entrance.
4. The robot was able to continue toward the new route instead of repeatedly switching between both sides.
5. A second goal was sent farther away.
6. After reaching that goal, the original goal was sent again.
7. When the robot approached the obstacle pair again, the inflation representation was initially absent or had cleared.
8. The obstacles were then detected and represented again.
9. The planner selected the alternative route quickly.
10. The same general behavior was observed in both runs.

The global-only `2.7 m` configuration therefore appeared more stable than `3.0 m` in this scenario.

### Decision from Experiment 6A

Keep the following configuration as the current working navigation configuration:

```yaml
# local costmap
raytrace_max_range: 3.0

# global costmap
raytrace_max_range: 2.7
```

No further raytrace tuning was performed after this point.

The value `2.7 m` is considered a practical simulation configuration rather than a theoretically optimal or hardware-final value. Real LiDAR behavior, sensor noise, latency, obstacle geometry, and robot motion may require further adjustment during hardware integration.

---

### Experiment 6B — Distance-Based Global Replanning

The next suspected contributor was the frequency of global replanning.

The baseline behavior tree used:

```xml
<RateController hz="1.0">
```

which caused global planning to be triggered periodically.

A custom navigation behavior tree was introduced using:

```xml
<DistanceController distance="0.75">
```

The intention was to reduce excessive reactions to small costmap changes while still allowing the planner to reconsider the route after the robot had moved a meaningful distance.

### Custom Behavior Tree

The current custom BT contains the following navigation pipeline:

```text
DistanceController (0.75 m)
        ↓
ComputePathToPose
        ↓
SmoothPath (simple_smoother)
        ↓
FollowPath
```

The recovery section retains:

* Global/local costmap clearing
* Spin recovery
* Wait recovery
* BackUp recovery

The smoothed path is passed to `FollowPath` through:

```text
{smoothed_path}
```

rather than directly using the raw planner path.

### Experiment 6B Results

Two independent runs were performed using the combined working configuration.

Observed behavior:

1. The obstacle inflation became significantly more stable.
2. The global path no longer changed continuously in response to small changes in the costmap.
3. After selecting a route, the robot continued following that route for a meaningful distance.
4. Replanning occurred after the robot progressed along the current route rather than continuously.
5. When a genuinely better route became available, a new path was generated and the robot changed to it.
6. The previous left/right oscillation was substantially reduced.
7. The same general behavior was observed in two separate runs.

This represents a significant improvement over the previous repeated path-switching behavior.

### Current Working Configuration

The current navigation configuration for this dynamic-obstacle scenario is:

```text
Global costmap:
    obstacle_max_range: 2.5 m
    raytrace_max_range: 2.7 m
    inflation_radius: 2.5 m
    cost_scaling_factor: 1.5

Local costmap:
    obstacle_max_range: 2.5 m
    raytrace_max_range: 3.0 m
    inflation_radius: 0.45 m
    cost_scaling_factor: 2.0

Global replanning:
    DistanceController distance: 0.75 m

Path processing:
    SimpleSmoother

Planner:
    SmacPlanner2D
    cost_travel_multiplier: 2.0
```

The persistent local costmap configuration remains:

```text
5 m × 5 m
```

The previously tested `7 m × 7 m` and `8 m × 8 m` local costmap sizes were runtime experiments and did not resolve the path-switching behavior.

### Engineering Interpretation

The results support the following interpretation:

The original instability was not caused by a single missing obstacle or an inability of SmacPlanner2D to find an alternative route.

Instead, the behavior was strongly associated with the interaction between:

* LiDAR obstacle observation and clearing,
* changing obstacle/inflation representation,
* global costmap updates,
* frequent global replanning,
* and controller execution of continuously changing paths.

Reducing the global raytrace range from `3.0 m` to `2.7 m` produced a more stable global obstacle representation in the tested scenario.

Replacing periodic replanning with distance-based replanning then reduced the sensitivity of the navigation behavior to small intermediate costmap changes.

The addition of path smoothing is part of the current custom BT configuration and was tested together with the distance-based replanning configuration. Therefore, the current results do not isolate the individual contribution of `DistanceController` and `SmoothPath`.

### Decision

The current configuration is accepted as the **working simulation configuration** for the dynamic-obstacle scenario.

No further parameter optimization will be performed for this issue unless a new reproducible navigation problem appears.

The goal is not to exhaustively optimize every Nav2 parameter in simulation. Future problems will be treated as separate engineering issues and investigated only when they produce an observable failure or regression.

### Important Limitation

This configuration is not considered final hardware tuning.

The real AMR may exhibit different behavior due to:

* LiDAR measurement noise,
* sensor update rate,
* processing latency,
* wheel slip,
* odometry drift,
* real obstacle geometry,
* motor/controller response,
* floor friction,
* and differences between simulated and physical dynamics.

The current values should therefore be treated as the **validated simulation baseline**, to be revalidated and adjusted during hardware integration if required.

### Status

**Dynamic obstacle replanning investigation: Working simulation configuration established.**

The previous repeated left/right path oscillation has been substantially reduced in two independent runs using the current configuration.

Further investigation is deferred unless the behavior regresses or a new related failure is observed.
