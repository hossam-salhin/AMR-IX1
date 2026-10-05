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

# Session 7 — Final Goal Orientation, Navigation Tuning, and Simulation Baseline
Date: 2026-10-05

## 1. Session Objective

The objective of Session 7 was to investigate the remaining navigation issue where the robot could reach the goal position but sometimes struggled to complete the final goal orientation, especially when a large heading rotation was required.

The investigation followed the established engineering workflow:

Observation → Measurement → Hypothesis → One Experiment → Result → Decision

The goal was not to blindly tune Nav2 parameters, but to determine whether the behavior was caused by navigation configuration, controller behavior, replanning, or simulation physics.

---

## 2. Starting Point

Session 7 started from the clean repository baseline:

e1e84cd — fix(navigation): stabilize dynamic obstacle replanning

The robot was already able to:

- Navigate to predefined goals.
- Use AMCL localization.
- Generate and follow global paths.
- Replan around dynamic obstacles.
- Complete the previously validated 3-waypoint inspection mission.
- Capture RGB/thermal inspection data.
- Generate inspection logs.
- Use the custom navigation behavior tree.
- React to dynamic obstacles using the previously validated DistanceController configuration.

The remaining issue was primarily related to final goal orientation.

---

## 3. Initial Final-Rotation Problem

Observed behavior:

- The robot generally reached the correct goal position.
- Final orientation was sometimes completed successfully.
- In open areas, final orientation was generally achievable.
- In constrained/corridor situations, final rotation could become unstable.
- Large required heading changes were more problematic than smaller rotations.
- The robot could sometimes rotate correctly and sometimes oscillate.
- During problematic runs, the robot could move slightly while attempting to rotate.
- Continuous replanning could then produce a new path and interfere with the final rotation.

The issue was therefore investigated as a navigation/controller/replanning problem rather than immediately assuming a single parameter was responsible.

---

## 4. Progress Checker Experiment

Original configuration:

movement_time_allowance: 5.0

This could cause the controller to declare insufficient progress while the robot was still performing a legitimate final heading adjustment.

Experiment:

movement_time_allowance:
5.0 → 15.0 seconds

Result:

- The robot was given enough time to complete heading adjustment.
- Premature progress failure during final heading adjustment was reduced.
- Open-space goals could complete more reliably.

Decision:

KEEP

Current value:

movement_time_allowance: 15.0

---

## 5. XY Goal Tolerance Investigation

Original value:

xy_goal_tolerance: 0.10 m

The tight XY tolerance increased sensitivity to small physical/simulation movements during final rotation.

Experiments included increasing the tolerance through multiple values.

Observed trend:

- 0.10 m → noticeable oscillation.
- 0.15 m → limited improvement.
- 0.20 m → noticeable improvement.
- 0.25–0.40 m → substantially reduced final-position oscillation.

The current selected value is:

xy_goal_tolerance: 0.25 m

Decision:

KEEP 0.25 m as the current simulation baseline.

This is an engineering trade-off for the current simulation and is not being treated as a universal final hardware value.

---

## 6. RPP Final Approach / Rotation Parameters

The following RPP-related parameters were tested as part of the final-approach investigation:

max_linear_decel:
1.0 → 1.5

approach_velocity_scaling_dist:
0.6 m

min_approach_linear_velocity:
0.05 m/s

rotate_to_heading_min_angle:
0.78 rad ≈ 45 degrees

The changes were tested rather than being added blindly.

Observed result:

- The parameters affected the final approach and final-heading behavior.
- Their effect was visible not only for very large rotations but also for smaller final-angle cases.
- The resulting behavior became more controllable in a number of goal orientations.
- However, the changes did not completely eliminate the large-angle behavior.

Decision:

KEEP the tested configuration as the current simulation baseline.

Current relevant configuration:

max_linear_decel: 1.5
approach_velocity_scaling_dist: 0.6
min_approach_linear_velocity: 0.05
rotate_to_heading_min_angle: 0.78

---

## 7. Final Rotation Evidence

During problematic rotations, /cmd_vel showed that the robot did not always perform a perfectly stationary pure rotation.

Observed command behavior included:

- angular velocity in the positive direction,
- small forward linear velocity,
- angular velocity reduction,
- angular velocity reversal,
- negative rotation,
- later correction back toward the target heading.

This demonstrated that the controller was capable of producing translational motion while the robot was attempting to achieve final orientation.

The goal pose itself remained stable while the path/controller behavior could change during continuous replanning.

---

## 8. Continuous Replanning Observation

During problematic final rotations, the controller repeatedly received new paths.

Typical observation:

Passing new path to controller.

This occurred approximately every 1–1.4 seconds in the continuous-replanning configuration.

This supported the hypothesis that final rotation, small translational drift, and replanning could interact with each other.

However, the evidence was not sufficient to claim that replanning alone was the root cause.

---

## 9. Behavior Tree Experiments

### 9.1 SmoothPath Experiment

A SmoothPath stage was temporarily introduced between path planning and path following.

Conceptually:

ComputePathToPose
→ SmoothPath
→ FollowPath

The smoothed path was stored in a separate blackboard variable and then passed to FollowPath.

Observed problems included:

- repeated SmoothPath processing,
- very high BT activity,
- messages such as:
  "Received a path to smooth.",
- Behavior Tree tick-rate warnings,
- controller loop timing problems,
- Failed to make progress,
- instability during navigation.

The experiment was therefore abandoned.

The current BT does NOT use SmoothPath.

Current structure:

DistanceController
→ ComputePathToPose
→ FollowPath

with the existing recovery structure.

Decision:

REMOVE SmoothPath.

---

## 10. DistanceController Investigation

The DistanceController value used in the custom BT was previously:

distance = 0.75 m

During dynamic-obstacle investigation, this was experimentally reduced.

Tested value:

distance = 0.35 m

Result:

Two independent successful runs showed:

- faster route reaction,
- less time spent approaching the obstacle before replanning,
- safer distance from the simulated obstacle,
- no collision in the tested scenario.

Decision:

KEEP

Current BT value:

DistanceController distance="0.35"

This is considered the practical dynamic-obstacle baseline.

---

## 11. Alternative Behavior Tree Experiment

An installed Nav2 behavior tree was tested that replans only when the goal is updated.

Conceptually:

GoalUpdatedController
→ ComputePathToPose
→ FollowPath

Result:

The alternative BT did not provide a meaningful improvement for the observed final-rotation problem.

The previous custom BT was therefore restored.

Decision:

KEEP the custom BT.

---

## 12. Current Custom Behavior Tree

Current structure:

NavigateRecovery
└── NavigateWithReplanning
    ├── DistanceController distance="0.35"
    │   └── ComputePathToPose
    └── FollowPath
        └── recovery / local costmap clearing

Recovery actions remain available through the existing RecoveryFallback structure.

SmoothPath is NOT part of the current BT.

---

## 13. Large-Angle Rotation Result

After the above experiments:

- Goal position is reached reliably.
- Final rotation works well for many smaller and medium heading changes.
- Rotations up to approximately 110 degrees were observed to behave acceptably.
- Larger final rotations can still produce oscillation/drift in Gazebo.

The remaining behavior appears strongly related to the simulated skid-steer robot's physical response during rotation.

Possible contributing factors include:

- wheel-ground friction,
- skid-steer lateral slip,
- Gazebo contact dynamics,
- wheel inertia,
- collision/contact behavior,
- small translational drift during rotation.

This has NOT been proven to be exclusively a Gazebo physics issue.

It is therefore documented as the current engineering hypothesis rather than a confirmed root cause.

---

## 14. Engineering Decision

The team decided to STOP further parameter tuning of the large-angle final-rotation behavior in simulation at this stage.

Reason:

The robot already demonstrates the required navigation functionality, while the remaining issue is strongly coupled to simulated skid-steer dynamics.

The real robot will use different:

- wheel-ground contact,
- friction,
- wheel inertia,
- motor/controller dynamics,
- mechanical compliance,
- drivetrain behavior.

Therefore, continuing to optimize Gazebo-specific behavior without hardware validation has diminishing engineering value.

The issue will be revisited during physical robot integration if it appears on the real platform.

---

## 15. Current Navigation Baseline

Important current values:

Progress checker:

required_movement_radius: 0.3
movement_time_allowance: 15.0

Goal checker:

xy_goal_tolerance: 0.25
yaw_goal_tolerance: 0.10
stateful: true

RPP:

desired_linear_vel: 0.3
max_linear_accel: 1.0
max_linear_decel: 1.5
approach_velocity_scaling_dist: 0.6
min_approach_linear_velocity: 0.05
lookahead_dist: 0.5
min_lookahead_dist: 0.3
max_lookahead_dist: 0.8
use_velocity_scaled_lookahead_dist: false
use_rotate_to_heading: true
rotate_to_heading_angular_vel: 1.0
max_angular_accel: 2.0
rotate_to_heading_min_angle: 0.78

SmacPlanner2D:

tolerance: 0.25
downsample_costmap: false
use_astar: false
allow_unknown: true
max_iterations: 1000000
max_on_approach_iterations: 1000
use_final_approach_orientation: false
minimum_turning_radius: 0.01
cost_travel_multiplier: 2.0

Custom BT:

DistanceController distance: 0.35 m

---

## 16. Session 7 Conclusion

Session 7 successfully narrowed the final-orientation problem and produced a stable practical navigation baseline.

The main conclusions are:

1. Increasing movement_time_allowance from 5 s to 15 s improved final-heading completion.
2. Increasing XY goal tolerance reduced sensitivity to small translational drift.
3. RPP final-approach parameters affected both small and large final-angle behavior.
4. SmoothPath was not beneficial and was removed.
5. DistanceController = 0.35 m remains the preferred dynamic-obstacle value.
6. The alternative goal-update-only BT did not solve the problem.
7. The custom BT remains the project baseline.
8. Large-angle rotation instability remains in some Gazebo scenarios.
9. The issue is now considered a hardware-validation item rather than a blocker for continuing the software project.
10. Further blind Nav2 tuning is intentionally stopped.

NEXT STEP:
Continue with the next AMR-IX1 project phase rather than spending more time on Gazebo final-rotation tuning.

## Session 8 — Camera Stand Joint Limit / Trajectory Control Investigation

**Date:** 2026-10-05
**Component:** `cam_stand_joint` / camera stand
**Status:** Investigation closed for now — not a project blocker

### Objective

Investigate why `cam_stand_joint` could move normally inside its allowed range but, when commanded through the CLI `JointTrajectoryController` to exactly its upper joint limit, it could become unresponsive to subsequent commands until the Gazebo simulation was restarted.

### Configuration

* Joint type: `revolute`
* Axis: `Y`
* Lower limit: `-0.7854 rad` (~`-45°`)
* Upper limit tested:

  * `0.0 rad`
  * `0.01 rad`
  * `0.2 rad`
* Controller:

  * `joint_trajectory_controller/JointTrajectoryController`
* Command interface:

  * `cam_stand_joint/position`
* Hardware interface:

  * available and claimed
* ROS 2: Humble
* Gazebo: Fortress

### Verified Controller Path

`ros2 control list_controllers` confirmed:

```text
cam_stand_controller    joint_trajectory_controller/JointTrajectoryController    active
```

Hardware interface:

```text
cam_stand_joint/position [available] [claimed]
```

A failed reverse command after reaching the upper limit showed:

```text
reference = -0.4
desired  = -0.4
output   = -0.4
actual   = +upper_limit
```

Therefore, the `JointTrajectoryController` was receiving and generating the requested command correctly. The failure was not caused by the trajectory command itself or by a lost/claimed command interface.

### Controlled Experiments

With `upper = 0.01 rad`:

```text
0       → -0.4       PASS
-0.4    → 0          PASS
0       → +0.005     PASS
+0.005  → -0.4       PASS
0       → +0.01      PASS
+0.01   → -0.4       FAIL
```

After reaching the exact upper limit, the joint remained at the upper boundary and did not respond to a reverse CLI trajectory until Gazebo was restarted.

The upper limit was then increased to `+0.2 rad`:

```text
0       → +0.2       PASS
+0.2    → -0.4       FAIL
```

This showed that simply increasing the positive margin did not eliminate the CLI trajectory behavior when the exact upper boundary was reached.

### Important Additional Test — `rqt_joint_trajectory`

The same joint was then controlled using the slider in `rqt_joint_trajectory`.

Result:

* Smooth movement in both directions.
* Movement to the positive upper limit (`+0.2 rad`) worked.
* Movement back from the upper limit worked normally.
* Movement to the negative lower limit (`-0.7854 rad`) also worked.
* Returning from the negative limit worked normally.
* No permanent lock was observed.

### Conclusion

The camera stand joint itself is functioning correctly in simulation:

* Joint definition is valid.
* Y-axis orientation is valid.
* Full intended negative range is reachable.
* Positive movement is possible.
* Both physical joint limits can be reached.
* The joint can recover from both limits when controlled through `rqt_joint_trajectory`.

The previously observed lock appears to be specific to the current CLI/JTC + Gazebo interaction when the joint reaches the exact upper limit. It has **not** been proven to be a Gazebo bug and is **not considered a project blocker at this stage**.

No further controller changes will be made based on this behavior during Session 8.

### Decision

Keep the current `JointTrajectoryController` configuration unchanged for now.

Treat the observed CLI/limit behavior as:

> **Known simulation behavior / open investigation — non-blocking**

The issue can be revisited later if it appears during:

1. integration with the actual robot,
2. higher-level camera inspection behavior,
3. automated camera positioning,
4. or final simulation validation.

Since `rqt_joint_trajectory` demonstrates correct bidirectional behavior at both limits, further debugging of this issue is deferred.

### Session 8 Result

**Camera stand joint control: FUNCTIONALLY VERIFIED in simulation.**

The joint can:

* move through the intended range,
* reach the upper limit,
* return from the upper limit,
* reach the lower limit,
* and return from the lower limit.

**Session 8 closed.**


## Session 9 — Thermal Camera Simulation & Visualization

### Objective

Develop and verify a usable thermal-camera simulation pipeline for AMR-IX1, including:

* Gazebo Fortress thermal sensor configuration.
* Raw thermal image inspection and temperature conversion.
* Thermal properties for simulated inspection objects.
* Local copies of modified Gazebo models.
* ROS 2 thermal visualization.
* Fixed absolute temperature display range.
* Integration with the main Gazebo launch workflow.

### Initial Thermal Camera Behavior

The thermal camera was already publishing a ROS 2 image on:

`/thermal/image`

The initial raw image was:

* `sensor_msgs/msg/Image`
* `mono8`
* `160 × 120`
* approximately `5 Hz`

The first raw image contained a uniform pixel value of `96`.

This initially raised the possibility that the thermal sensor was not responding to the simulated environment.

Direct Gazebo inspection confirmed that the topic was being published correctly.

### Thermal Sensor Configuration

The thermal camera was configured using the Gazebo Fortress thermal sensor with:

* Horizontal FOV: `0.9599 rad`
* Resolution: `160 × 120`
* Image format: `L8`
* Near clip: `0.1 m`
* Far clip: `30 m`
* Update rate: `5 Hz`
* Minimum temperature: `223.15 K` (`-50°C`)
* Maximum temperature: `673.15 K` (`400°C`)
* Thermal resolution: `3.0 K/pixel`

The raw Gazebo topic was verified using the Fortress `ign` CLI.

### Raw Temperature Conversion

The raw pixel values were investigated numerically instead of treating the image as a normal grayscale image.

The verified conversion for the current configuration is:

`T_C = pixel × 3.0 - 273.15`

For example:

* Pixel `96` → `14.85°C`
* Pixel `100` → `26.85°C`
* Pixel `110` → `56.85°C`

This confirmed that the initial uniform value of `96` represented valid thermal data rather than a failed sensor.

### Thermal Properties for Simulated Objects

To create meaningful temperature variation in the thermal image, thermal properties were added to simulated objects.

The Gazebo Fortress thermal system plugin was used:

```xml
<plugin filename="ignition-gazebo-thermal-system" name="gz::sim::systems::Thermal">
  <temperature>330.0</temperature>
</plugin>
```

The configured temperature was:

`330.0 K ≈ 56.85°C`

The thermal property was placed inside the relevant model `<visual>` element.

The following objects were configured:

* `pallet_box_mobile`
* `shelf`

After this modification, the raw thermal image contained multiple temperature values.

A verified diagnostic result was:

* Minimum: `14.85°C`
* Maximum: `56.85°C`
* Mean: `23.25°C`
* Pixels below `10°C`: `0`
* Pixels at or above `10°C`: `19,200`

Since `160 × 120 = 19,200`, this also confirmed that the complete thermal frame was being received.

### Local Gazebo Models

Because the shelf and pallet models were modified, local copies were created inside the project repository instead of modifying the downloaded Fuel cache.

The local models are stored under:

`src/amr_ix1_gazebo/models/`

The modified world references use local model URIs such as:

`model://shelf`

and:

`model://pallet_box_mobile`

The Gazebo launch file was configured to include the project models directory in `IGN_GAZEBO_RESOURCE_PATH`.

### Model Directory Issue

The downloaded Fuel shelf model originally had the following structure:

```text
shelf/
└── 1/
    ├── model.sdf
    ├── model.config
    ├── meshes/
    └── thumbnails/
```

For the current `model://shelf` configuration, this structure did not resolve as required.

The contents of the version directory were moved one level upward so that the working structure became:

```text
shelf/
├── model.sdf
├── model.config
├── meshes/
└── thumbnails/
```

The local `model://shelf` reference then worked correctly.

This behavior was documented as an important local-model pitfall.

### Thermal Visualization Package

A new ROS 2 Python package was created:

`amr_ix1_thermal`

The package contains the `thermal_visualizer` node.

Its responsibilities are intentionally separated from the thermal sensor itself.

Input:

`/thermal/image`

Outputs:

* `/thermal/image_color`
* `/thermal/legend`

The visualizer converts the raw pixel values into Celsius using the verified thermal resolution and then maps the resulting temperature to a custom dense Ironbow-like color palette.

### Display Range Decision

The thermal sensor range and visualization range were intentionally kept independent.

Sensor range:

`-50°C → 400°C`

Current display range:

`10°C → 70°C`

The visualization uses a fixed absolute range rather than normalizing every frame independently.

This preserves consistent color meaning between different frames.

For example, approximately `50°C` is always mapped to the same part of the palette while the display range remains unchanged.

A horizontal temperature legend was added with labels every `5°C` from `10°C` to `70°C`.

### Launch Integration

The thermal visualization package was integrated into the main Gazebo launch workflow.

The main launch now starts:

* Gazebo Fortress.
* Thermal camera simulation.
* ROS 2 thermal image bridge.
* Local modified Gazebo models.
* `thermal_visualizer`.
* Colorized thermal output.
* Thermal temperature legend.

The thermal image bridge uses:

`/thermal/image@sensor_msgs/msg/Image[ignition.msgs.Image`

The integrated launch was verified successfully.

`ros2 node list | grep thermal` returned:

`/thermal_visualizer`

The thermal visualizer was also verified independently using its own launch file.

### Verification

The following parts of the thermal pipeline were functionally verified:

1. Gazebo thermal sensor publication.
2. Raw `/thermal/image` data.
3. Raw pixel-to-temperature conversion.
4. Thermal properties on simulated models.
5. Local `model://` references.
6. ROS 2 thermal image bridge.
7. `amr_ix1_thermal` visualizer.
8. `/thermal/image_color` publication.
9. `/thermal/legend` publication.
10. Integrated Gazebo launch.

The thermal camera produced visible temperature differences after thermal properties were added to the simulated objects.

### Important Design Decisions

The following decisions were made during this session:

* Keep raw thermal data available independently from visualization.
* Keep sensor temperature range independent from display range.
* Use fixed absolute display limits instead of per-frame normalization.
* Keep modified Gazebo models inside the repository.
* Keep thermal visualization in a dedicated ROS 2 package.
* Use the raw thermal image as the reference for numerical temperature analysis.

### Known Limitations

The current thermal system is intended for simulation and development.

Current limitations include:

* Thermal model temperatures are currently embedded in model SDF files.
* Multiple instances of the same modified model therefore share the same configured temperature.
* The visualization range is currently defined in the Python implementation rather than exposed as ROS 2 parameters.
* The thermal palette is a custom Ironbow-like palette rather than a calibrated representation of a specific physical camera.
* Physical thermal-camera integration and calibration remain future work.

### Session 9 Result

**Thermal camera simulation and visualization: FUNCTIONALLY VERIFIED in simulation.**

The AMR-IX1 thermal pipeline can now:

* publish raw thermal data from Gazebo Fortress,
* convert raw thermal pixels into temperature values,
* represent different temperatures on simulated objects,
* use repository-local modified Gazebo models,
* generate a fixed-range colorized thermal image,
* publish a temperature legend,
* and start as part of the normal Gazebo simulation workflow.

**Session 9 closed.**
