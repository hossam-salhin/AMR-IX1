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
