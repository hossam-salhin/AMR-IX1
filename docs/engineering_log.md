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
