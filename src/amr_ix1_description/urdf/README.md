# amr_ix1_description / urdf

| File | Role | Replace when the new design is ready? |
|---|---|---|
| `amr_ix1.urdf.xacro` | Top level: arguments + includes | No |
| `amr_ix1_base.xacro` | Materials, links, joints (CAD-derived) | **Yes — this is the only one** |
| `amr_ix1_ros2_control.xacro` | ros2_control block, `hardware` = sim / mock / real | No (edit joint list only if joints change) |
| `amr_ix1_gazebo.xacro` | Simulation-only: Gazebo plugin, wheel friction, simulated sensors | Only if sensor mounting changes |

## Arguments
- `hardware:=sim|mock|real` (default `sim`)
  - `sim`: Ignition + `ign_ros2_control` (previous behaviour)
  - `mock`: `mock_components/GenericSystem` loop-back, to test the ros2_control / Nav2 chain without a robot
  - `real`: placeholder plugin `amr_ix1_hardware/AmrIx1Hardware` (params are placeholders)
- `use_thermal:=true|false` (default `true`, simulation only)

## Names that the rest of the stack depends on (keep them in the new base file)
- Frames: `base_footprint`, `base_link`, `imu_Link`, `laser_Link`, `camera_Link`
  (`thermal_link` only for the simulated thermal camera)
- Joints: `F_R_W_joint`, `F_L_W_joint`, `B_R_W_joint`, `B_L_W_joint` (continuous, wheels),
  `cam_stand_joint` (revolute, range -0.7854..0.2 rad in ros2_control)
- Wheel links used by the Gazebo friction tags: `F_R_W_Link`, `F_L_W_Link`, `B_R_W_Link`, `B_L_W_Link`
- Values to re-check with the new design (they live outside the URDF):
  `wheel_radius`, `wheel_separation` (controllers.yaml), Nav2 `footprint` (nav2_params.yaml, two places)

## Switching between sim / mock / real

Command line (the value after `:=` is the argument):

```bash
U=$(ros2 pkg prefix amr_ix1_description)/share/amr_ix1_description/urdf/amr_ix1.urdf.xacro
xacro $U                          # sim (default)
xacro $U hardware:=mock           # loop-back hardware, no robot needed
xacro $U hardware:=real           # real robot (placeholder plugin for now)
xacro $U use_thermal:=false       # simulation without the thermal camera
xacro $U hardware:=mock | grep -A4 "<hardware>"   # check which plugin was selected
```

From a launch file (example for `display.launch.py`; `gazebo.launch.py` always uses the default `sim`):

```python
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration

DeclareLaunchArgument('hardware', default_value='sim'),
robot_description = Command(
    ['xacro ', urdf_file, ' hardware:=', LaunchConfiguration('hardware')])
```

The mock/real variants are meant to be started by the real-robot bringup launch (added later), not by `gazebo.launch.py`.

## xacro cheat sheet

| Syntax | Meaning |
|---|---|
| `<xacro:arg name="x" default="v"/>` | Argument passed from outside (`x:=value`). Read it with `$(arg x)`. |
| `<xacro:property name="p" value="1.5"/>` | Constant defined inside the files. Read it with `${p}`. |
| `<xacro:macro name="m" params="a b:=2">…</xacro:macro>` | Define a macro. Call it with `<xacro:m a="1"/>`; inside use `${a}`. |
| `<xacro:if value="${cond}">…</xacro:if>` | Keep the content only if `cond` is true. |
| `<xacro:unless value="${cond}">…</xacro:unless>` | Opposite of `if` (there is no `else`). |
| `<xacro:include filename="$(find pkg)/urdf/f.xacro"/>` | Insert another file. |

Notes:
- `cond` is a Python expression; strings need quotes: `${hardware == 'sim'}`.
- `$(arg x)` is replaced by text first, so in the top-level file an argument is compared as
  `${'$(arg hardware)' == 'sim'}`. Inside a macro, use its parameter directly (`${hardware}`).
- After a change to a file installed with `--symlink-install`, new files need a rebuild
  (`colcon build --packages-select amr_ix1_description`); edits to existing files do not.
