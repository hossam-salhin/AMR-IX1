# AMR-IX1 Thermal Camera

## 1. Overview

The AMR-IX1 simulation includes a thermal camera mounted on the robot and exposed through ROS 2 as a standard `sensor_msgs/msg/Image` topic.

The thermal-camera system has two separate responsibilities:

1. **Thermal sensor simulation**
   - Gazebo Fortress generates the raw thermal image.
   - The simulated sensor produces an `L8` grayscale image.
   - Each pixel represents an absolute temperature according to the configured thermal sensor parameters.

2. **Thermal visualization**
   - The ROS 2 package `amr_ix1_thermal` converts the raw thermal image into a colorized image.
   - The visualization uses a fixed absolute display range rather than normalizing each frame independently.
   - This preserves the meaning of the displayed colors across different frames.
   - A temperature legend is published alongside the colorized image.

### Current Thermal Pipeline

```text
Gazebo Fortress Thermal Sensor
            |
            v
      /thermal/image
            |
            v
   amr_ix1_thermal
   thermal_visualizer
            |
            +--------------------+
            |                    |
            v                    v
 /thermal/image_color     /thermal/legend
```
### Important Design Decision

The physical thermal sensor range and the display temperature range are intentionally independent.

The current sensor is configured to represent temperatures from approximately -50°C to 400°C, while the visualization currently displays 10°C to 70°C.

This means changing the visualization range does not change the simulated sensor's physical measurement range.

The current implementation is intended for development and simulation of the AMR-IX1 inspection system. The visualization is designed to make thermal differences easy to identify while keeping the underlying raw thermal data available separately.

## 2. Thermal Camera Sensor Configuration

### Sensor Configuration

The thermal camera is implemented in the AMR-IX1 Xacro description using the Gazebo Fortress thermal sensor.

The sensor uses the following configuration:

```xml
<gazebo reference="thermal_link">
  <sensor name="thermal_camera" type="thermal">
    <camera>
      <horizontal_fov>0.9599</horizontal_fov>
      <image>
        <width>160</width>
        <height>120</height>
        <format>L8</format>
      </image>
      <clip>
        <near>0.1</near>
        <far>30</far>
      </clip>
    </camera>

    <always_on>true</always_on>
    <update_rate>5</update_rate>
    <visualize>false</visualize>
    <topic>thermal/image</topic>

    <plugin
      filename="ignition-gazebo-thermal-sensor-system"
      name="gz::sim::systems::ThermalSensor">
      <min_temp>223.15</min_temp>
      <max_temp>673.15</max_temp>
      <resolution>3.0</resolution>
    </plugin>
  </sensor>
</gazebo>
```

### Sensor Parameters

| Parameter | Value | Description |
|---|---:|---|
| Sensor type | `thermal` | Gazebo Fortress thermal sensor |
| Resolution | `160 × 120` | Raw thermal image resolution |
| Image format | `L8` | 8-bit grayscale thermal data |
| Horizontal FOV | `0.9599 rad` | Approximately 55° |
| Near clip | `0.1 m` | Minimum sensor range |
| Far clip | `30 m` | Maximum sensor range |
| Update rate | `5 Hz` | Thermal image frequency |
| Minimum temperature | `223.15 K` | -50°C |
| Maximum temperature | `673.15 K` | 400°C |
| Thermal resolution | `3.0 K/pixel` | Raw pixel-to-temperature scale |
| ROS 2 topic | `/thermal/image` | Raw thermal image |

### Important Notes

The <min_temp> and <max_temp> parameters define the thermal sensor's configured temperature range.

The <resolution> parameter is critical because the raw L8 pixel values are not interpreted as a normalized 0–255 display value. In the current Fortress configuration, the measured temperature can be recovered using the relationship documented in Section 4.

The sensor itself publishes the raw thermal data. Colorization, display limits, and the temperature legend are handled separately by the amr_ix1_thermal visualization package.

## 3. Raw Thermal Data

### ROS 2 Raw Image

The thermal sensor publishes the raw thermal image on:

`/thermal/image`

The topic is bridged from Gazebo Fortress to ROS 2 as:

`/thermal/image@sensor_msgs/msg/Image[ignition.msgs.Image`

The ROS 2 message type is:

`sensor_msgs/msg/Image`

The current raw image properties are:

| Property | Value |
|---|---|
| Topic | `/thermal/image` |
| Message type | `sensor_msgs/msg/Image` |
| Encoding | `mono8` |
| Resolution | `160 × 120` |
| Pixel depth | 8-bit |
| Update rate | Approximately `5 Hz` |
| QoS reliability | `RELIABLE` |
| QoS durability | `VOLATILE` |

### Raw Pixel Behavior

During the initial thermal-camera test, the raw image contained a uniform pixel value of `96`.

This was initially investigated because a uniform grayscale image could indicate that the thermal sensor was not responding to the simulated environment.

Further testing showed that the value was valid thermal data rather than a failed camera output.

With the configured thermal resolution of `3.0 K/pixel`, a raw pixel value of `96` corresponds to:

`96 × 3.0 - 273.15 = 14.85°C`

After thermal properties were added to simulated models, the raw image produced multiple temperature values. A verified diagnostic result was:

| Measurement | Value |
|---|---:|
| Minimum temperature | `14.85°C` |
| Maximum temperature | `56.85°C` |
| Mean temperature | `23.25°C` |
| Pixels below `10°C` | `0` |
| Pixels at or above `10°C` | `19,200` |

Since the image contains `160 × 120 = 19,200` pixels, this confirmed that the complete frame was being received and that the temperature variation originated from the simulated scene.

### Diagnostic Command

The raw Gazebo thermal message can be inspected directly with:

```bash
ign topic -e -t /thermal/image -n 1
```
Fortress uses the ign command-line interface for topic inspection in this setup.

The raw data should be treated as the source measurement. Colorization and display scaling are performed later by the amr_ix1_thermal visualization package.

## 4. Temperature Conversion

The raw thermal image uses 8-bit grayscale pixel values, but the pixel value represents temperature rather than a normalized display intensity.

For the current Gazebo Fortress configuration, the verified conversion is:

`T_C = pixel × 3.0 - 273.15`

Where:

- `pixel` is the raw `mono8` pixel value.
- `3.0` is the configured thermal resolution in Kelvin per pixel.
- `273.15` converts Kelvin to Celsius.
- `T_C` is the resulting temperature in degrees Celsius.

### Conversion Examples

| Raw pixel | Calculated temperature |
|---:|---:|
| `96` | `14.85°C` |
| `100` | `26.85°C` |
| `110` | `56.85°C` |

For example:

`110 × 3.0 - 273.15 = 56.85°C`

This matches the verified maximum temperature observed after adding thermal properties to the simulated models.

### Important Distinction

The raw pixel-to-temperature conversion is independent from the visualization range.

The thermal sensor is configured with:

- Minimum temperature: `-50°C`
- Maximum temperature: `400°C`
- Resolution: `3.0 K/pixel`

The current visualization displays only:

- Minimum display temperature: `10°C`
- Maximum display temperature: `70°C`

Therefore, changing the visualization limits does not change the underlying thermal measurement.

The raw `/thermal/image` topic should remain the reference source for temperature data, while `/thermal/image_color` is intended primarily for human visualization.

### Implementation

The current visualizer performs the conversion using:

```python
temperature_c = image.astype(np.float32) * 3.0 - 273.15
```
The resulting temperature array is then mapped to the configured absolute display range before colorization.

## 5. Thermal Visualization

The raw thermal image is converted into a colorized image by the ROS 2 package `amr_ix1_thermal`.

The visualization is intentionally separated from the thermal sensor itself. This allows the simulated sensor to preserve its configured physical temperature range while the displayed temperature range can be adjusted independently.

### Visualization Pipeline

```text
/thermal/image
      |
      v
thermal_visualizer
      |
      +----------------------+
      |                      |
      v                      v
/thermal/image_color   /thermal/legend
```

### Input

The visualizer subscribes to:

`/thermal/image`

The input is the raw `sensor_msgs/msg/Image` thermal image using `mono8` encoding.

### Outputs

The visualizer publishes:

| Topic                  | Message type            | Purpose                 |
| ---------------------- | ----------------------- | ----------------------- |
| `/thermal/image_color` | `sensor_msgs/msg/Image` | Colorized thermal image |
| `/thermal/legend`      | `sensor_msgs/msg/Image` | Temperature legend      |

The colorized image is intended for visualization, while the original `/thermal/image` topic remains the source of the raw thermal measurement.

### Absolute Display Range

The current visualization range is:

| Parameter                   |  Value |
| --------------------------- | -----: |
| Minimum display temperature | `10°C` |
| Maximum display temperature | `70°C` |

The visualizer uses an absolute temperature range rather than normalizing each frame independently.

This is an important design choice.

If each frame were normalized independently, the same color could represent different temperatures in different frames. Using a fixed absolute range makes the color meaning consistent between frames.

For example, a temperature of approximately `50°C` will always be mapped to the same part of the color palette while the display range remains `10–70°C`.

### Color Palette

The visualizer uses a dense custom Ironbow-like thermal palette.

The palette transitions through dark purple, violet, red, orange, yellow, and white as temperature increases.

The palette is applied after converting the raw pixels to degrees Celsius and clipping the temperature values to the configured display range.

### Temperature Legend

The visualizer also publishes a horizontal temperature legend.

The current legend covers:

`10°C → 70°C`

with labels at:

`10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70°C`

The legend provides a direct reference for interpreting the colors in `/thermal/image_color`.

### Visualizer Launch

The thermal visualizer can be launched independently with:

```bash
cd ~/ROS2_Master_Journey/AMR_inspection
source install/setup.bash
ros2 launch amr_ix1_thermal thermal_visualizer.launch.py
```

The node starts as:

`/thermal_visualizer`

The startup log currently reports:

`Thermal visualizer started | Display range: 10.0 to 70.0 C`

### Integrated Launch

The visualizer is also included automatically when the main Gazebo launch file is used:

```bash
ros2 launch amr_ix1_gazebo gazebo.launch.py
```

This keeps the thermal camera, thermal visualization, and Gazebo simulation integrated into the normal AMR-IX1 simulation workflow.

## 6. Thermal Properties for Gazebo Models

Gazebo Fortress does not automatically assign meaningful thermal temperatures to every simulated object.

To make objects appear at different temperatures in the thermal camera, a thermal property can be added to the appropriate Gazebo model visual.

### Thermal System Plugin

The thermal property uses the Fortress thermal system plugin:

```xml
<plugin filename="ignition-gazebo-thermal-system" name="gz::sim::systems::Thermal">
  <temperature>330.0</temperature>
</plugin>
```

The `<temperature>` value is specified in Kelvin.

For example:

`330.0 K - 273.15 = 56.85°C`

Therefore, the configuration above makes the associated visual represent approximately `56.85°C`.

### Placement

The thermal plugin must be placed inside the relevant `<visual>` element of the model.

Example:

```xml
<visual name="example_visual">
  <geometry>
    ...
  </geometry>

  <plugin filename="ignition-gazebo-thermal-system" name="gz::sim::systems::Thermal">
    <temperature>330.0</temperature>
  </plugin>
</visual>
```

The thermal temperature is therefore associated with the visual rather than being configured globally for the entire world.

### AMR-IX1 Model Configuration

The thermal property was added to the following simulated objects:

* `pallet_box_mobile`
* `shelf`

Both models were configured with:

`330.0 K ≈ 56.85°C`

This produced the expected temperature variation in the raw thermal image.

### Important Limitation

When the temperature is embedded directly in a model's SDF, every instance of that model uses the same configured temperature.

For example, if several objects use:

`model://shelf`

and the temperature is defined as `330.0 K` inside the shelf model, all instances use that same thermal property.

If different instances need different temperatures, the model or simulation setup must be extended to support per-instance thermal configuration.

### Verification

After adding thermal properties, the raw thermal image should be checked rather than relying only on the colorized display.

For example:

```bash
ign topic -e -t /thermal/image -n 1
```

The raw image should contain different pixel values when the thermal camera observes objects with different configured temperatures.

## 7. Using Local Gazebo Models

Some Gazebo models used by the AMR-IX1 simulation originally came from the Ignition Fuel model repository.

When a model needs to be modified locally, such as adding thermal properties, it is preferable to copy the model into the project repository and reference the local copy.

This makes the simulation reproducible and prevents changes from depending on external Fuel resources.

### Model Cache Location

Downloaded Fuel models are cached locally under:

```text
~/.ignition/fuel/fuel.ignitionrobotics.org/
```

For example, the cached shelf model was found under:

```text
~/.ignition/fuel/fuel.ignitionrobotics.org/movai/models/shelf
```

The model was copied into the AMR-IX1 Gazebo package:

```text
src/amr_ix1_gazebo/models/shelf
```

Similarly, the `pallet_box_mobile` model was copied into:

```text
src/amr_ix1_gazebo/models/pallet_box_mobile
```

### Local Model References

After copying a model into the project, the world can reference it using:

```xml
<include>
  <uri>model://shelf</uri>
  <name>shelf_4</name>
  <pose>5.60144 5.30708 0 0 0 0</pose>
</include>
```

This replaces the original external Fuel URI.

For example, the original shelf reference used an external resource:

```xml
<uri>
  https://fuel.ignitionrobotics.org/1.0/MovAi/models/shelf
</uri>
```

The local reference is:

```xml
<uri>model://shelf</uri>
```

### Model Directory Structure

For the current AMR-IX1 setup, the model must be structured so that `model.sdf` and `model.config` are directly inside the model directory.

Correct:

```text
models/
└── shelf/
    ├── model.sdf
    ├── model.config
    ├── meshes/
    └── thumbnails/
```

The following structure was found in the downloaded Fuel cache:

```text
models/
└── shelf/
    └── 1/
        ├── model.sdf
        ├── model.config
        ├── meshes/
        └── thumbnails/
```

For the current `model://shelf` setup, the version directory had to be removed by moving its contents one level upward.

### Gazebo Resource Path

The AMR-IX1 Gazebo launch file adds the local models directory to `IGN_GAZEBO_RESOURCE_PATH`.

The relevant configuration is:

```python
gazebo_models_dir = os.path.join(pkg_gazebo, 'models')

set_ign_resource_path = SetEnvironmentVariable(
    name='IGN_GAZEBO_RESOURCE_PATH',
    value=ros2_share_dir + ':' + gazebo_models_dir
)
```

This allows Gazebo to resolve local model references such as:

```text
model://shelf
model://pallet_box_mobile
```

without requiring the external Fuel repository at runtime.

### Why Local Models Are Preferred for Modified Objects

Using local copies is especially useful when a model has been modified for the AMR-IX1 simulation.

For example, the local `shelf` and `pallet_box_mobile` models contain the thermal system plugin.

Keeping these modified models inside the repository provides:

* reproducible simulation behavior,
* version-controlled model modifications,
* independence from external model availability,
* easier debugging,
* and a clear record of which thermal properties were applied.

## 8. Launch Integration

The thermal system is integrated into the main AMR-IX1 Gazebo launch workflow so that the thermal camera, ROS 2 bridge, local models, and thermal visualizer can be started together.

### Thermal Visualization Package

The main Gazebo launch file includes the thermal visualization launch file from:

`amr_ix1_thermal`

The launch file used by the package is:

`thermal_visualizer.launch.py`

This starts the:

`thermal_visualizer`

node.

The node is available as:

`/thermal_visualizer`

### Thermal Image Bridge

The Gazebo thermal image is bridged to ROS 2 using `ros_gz_bridge`.

The relevant bridge configuration is:

```python
'/thermal/image@sensor_msgs/msg/Image[ignition.msgs.Image',
```

This exposes the Gazebo thermal sensor output as:

`/thermal/image`

with the ROS 2 message type:

`sensor_msgs/msg/Image`

### Local Model Resource Path

The main Gazebo launch file also adds the project-local models directory to:

`IGN_GAZEBO_RESOURCE_PATH`

The configured path includes:

```text
<ROS 2 package share directory>:<Gazebo models directory>
```

This allows the simulation to resolve local model references such as:

```text
model://shelf
model://pallet_box_mobile
```

without depending on external Fuel model downloads during normal execution.

### Main Launch

The complete thermal pipeline can therefore be started using:

```bash
cd ~/ROS2_Master_Journey/AMR_inspection
source install/setup.bash
ros2 launch amr_ix1_gazebo gazebo.launch.py
```

The expected pipeline is:

```text
Gazebo Fortress
      |
      v
Thermal Sensor
      |
      v
/thermal/image
      |
      +--------------------+
      |                    |
      v                    v
ROS 2 Bridge        thermal_visualizer
                           |
                  +--------+--------+
                  |                 |
                  v                 v
        /thermal/image_color   /thermal/legend
```

### Verification of Integration

After launching the main simulation, the thermal visualizer node can be checked with:

```bash
ros2 node list | grep thermal
```

A successful integrated launch should include:

```text
/thermal_visualizer
```

The thermal image topic can also be checked with:

```bash
ros2 topic info /thermal/image --verbose
```

This confirms that the Gazebo thermal sensor is connected to ROS 2 through the bridge.

## 9. Verification and Diagnostic Commands

The following commands were used to verify the thermal camera, Gazebo thermal topics, ROS 2 bridge, and thermal visualization pipeline.

### 1. Check Gazebo Thermal Topics

Use the Fortress `ign` command-line interface:

```bash
ign topic -l | grep -i thermal
```

Expected thermal topics include:

```text
/thermal/camera_info
/thermal/image
```

### 2. Inspect One Raw Thermal Frame

To inspect the raw Gazebo thermal message:

```bash
ign topic -e -t /thermal/image -n 1
```

This is useful for checking whether the sensor is publishing data and whether the raw image contains valid values.

### 3. Check ROS 2 Topic Information

To inspect the ROS 2 thermal image topic:

```bash
ros2 topic info /thermal/image --verbose
```

This verifies the ROS 2 message type, publishers, subscribers, and QoS information.

### 4. Check Thermal Image Frequency

To measure the received ROS 2 thermal image rate:

```bash
ros2 topic hz /thermal/image
```

The configured thermal sensor update rate is `5 Hz`.

### 5. Check Thermal Visualizer Node

After starting the integrated Gazebo launch:

```bash
ros2 node list | grep thermal
```

Expected result:

```text
/thermal_visualizer
```

### 6. Build the Thermal Package

After modifying the `amr_ix1_thermal` package:

```bash
cd ~/ROS2_Master_Journey/AMR_inspection
colcon build --packages-select amr_ix1_thermal
```

Then source the workspace:

```bash
source install/setup.bash
```

### 7. Build the Gazebo Package

After modifying the Gazebo package:

```bash
colcon build --packages-select amr_ix1_gazebo
```

Then source the workspace again:

```bash
source install/setup.bash
```

### 8. Launch the Thermal Visualizer Standalone

For testing the visualization package independently:

```bash
ros2 launch amr_ix1_thermal thermal_visualizer.launch.py
```

This is useful when debugging the visualization without restarting the complete Gazebo simulation.

### 9. Launch the Complete Simulation

For end-to-end verification:

```bash
ros2 launch amr_ix1_gazebo gazebo.launch.py
```

This verifies the complete chain:

```text
Gazebo Thermal Sensor
        ↓
/thermal/image
        ↓
ros_gz_bridge
        ↓
ROS 2
        ↓
amr_ix1_thermal
        ↓
/thermal/image_color
        +
/thermal/legend
```

### 10. Raw Temperature Diagnostic

When numerical temperature statistics are required, the raw image can be converted using:

```text
T_C = pixel × 3.0 - 273.15
```

The resulting minimum, maximum, and mean temperatures can then be used to verify whether the simulated thermal scene behaves as expected.

## 10. Common Issues and Pitfalls

### 1. Use `ign`, Not `gz`, for Fortress Topic Inspection

This project uses Gazebo Fortress.

For direct Gazebo topic inspection, use:

```bash
ign topic -l
```

and:

```bash
ign topic -e -t /thermal/image -n 1
```

The `gz` command-line interface should not be assumed to be available for this Fortress installation.

### 2. A Uniform Raw Thermal Image Does Not Necessarily Mean the Sensor Is Broken

During the initial test, `/thermal/image` contained a uniform pixel value of `96`.

This was initially suspicious because the image did not show visible thermal variation.

However:

`96 × 3.0 - 273.15 = 14.85°C`

The value was therefore valid thermal data.

The correct diagnostic approach is to inspect the raw numerical values and then introduce thermal properties into simulated objects rather than assuming that a uniform image indicates a sensor failure.

### 3. Do Not Treat Raw `mono8` Values as Normalized Display Intensities

The raw thermal image uses 8-bit pixels, but the values represent thermal information according to the configured sensor resolution.

The current verified relationship is:

`T_C = pixel × 3.0 - 273.15`

Therefore, directly displaying the raw image as a normal grayscale image does not provide a meaningful thermal visualization.

### 4. Avoid Per-Frame Normalization for the Thermal Display

Normalizing every frame independently can make the same color represent different temperatures at different times.

For the current AMR-IX1 visualization, the display range is fixed at:

`10°C → 70°C`

This preserves consistent color-to-temperature meaning between frames.

### 5. Keep Sensor Range and Display Range Separate

The simulated thermal sensor is configured for:

`-50°C → 400°C`

while the current display range is:

`10°C → 70°C`

These are intentionally independent.

Changing the visualization limits should not be treated as changing the physical measurement range of the simulated sensor.

### 6. Thermal Properties Must Be Added to the Appropriate Model Visual

Adding the thermal system plugin to the wrong part of an SDF model may not produce the expected thermal behavior.

The current working configuration places:

```xml
<plugin filename="ignition-gazebo-thermal-system" name="gz::sim::systems::Thermal">
  <temperature>330.0</temperature>
</plugin>
```

inside the relevant `<visual>` element.

### 7. `model://` Requires the Local Model to Be Discoverable

When replacing an external Fuel model with:

```xml
<uri>model://shelf</uri>
```

Gazebo must be able to find the local model through `IGN_GAZEBO_RESOURCE_PATH`.

The AMR-IX1 launch file therefore adds:

```text
src/amr_ix1_gazebo/models
```

through the installed package's models directory.

### 8. Be Careful with Fuel Model Version Directories

Downloaded Fuel models may have a version directory such as:

```text
shelf/1/model.sdf
```

For the current AMR-IX1 local `model://shelf` configuration, the working structure is:

```text
shelf/model.sdf
shelf/model.config
shelf/meshes/
shelf/thumbnails/
```

If the model remains under `shelf/1/`, `model://shelf` may fail to resolve in this setup.

### 9. Modified Local Models Should Be Kept in the Repository

If a model is modified to add thermal properties, keeping the modified copy only in the local Gazebo cache makes the simulation difficult to reproduce.

The modified models should remain under:

```text
src/amr_ix1_gazebo/models/
```

and should be tracked by Git.

### 10. Check the Raw Topic Before Debugging the Visualization

If the colorized image looks incorrect, first verify:

```bash
ign topic -e -t /thermal/image -n 1
```

Then verify the ROS 2 topic:

```bash
ros2 topic info /thermal/image --verbose
```

Only after confirming that the raw thermal data is valid should the visualization package be investigated.

## 11. Current Configuration

The following configuration represents the current verified AMR-IX1 thermal simulation setup.

### Thermal Sensor

| Parameter | Current value |
|---|---|
| Sensor type | Gazebo Fortress `thermal` |
| Raw topic | `/thermal/image` |
| Image format | `L8` / `mono8` |
| Resolution | `160 × 120` |
| Update rate | `5 Hz` |
| Horizontal FOV | `0.9599 rad` |
| Near clip | `0.1 m` |
| Far clip | `30 m` |
| Minimum sensor temperature | `-50°C` |
| Maximum sensor temperature | `400°C` |
| Thermal resolution | `3.0 K/pixel` |

### ROS 2 Thermal Package

Package:

`amr_ix1_thermal`

Main executable:

`thermal_visualizer`

Node:

`/thermal_visualizer`

### Visualization

| Parameter | Current value |
|---|---|
| Input | `/thermal/image` |
| Colorized output | `/thermal/image_color` |
| Legend output | `/thermal/legend` |
| Display minimum | `10°C` |
| Display maximum | `70°C` |
| Palette | Custom dense Ironbow-like palette |
| Frame normalization | Disabled |
| Legend interval | `5°C` |

### Thermal Model Properties

The following local Gazebo models currently have thermal properties configured:

- `shelf`
- `pallet_box_mobile`

Current configured model temperature:

`330.0 K ≈ 56.85°C`

### Local Model Storage

Modified Gazebo models are stored under:

```text
src/amr_ix1_gazebo/models/
```

Current local models include:

```text
models/
├── pallet_box_mobile/
└── shelf/
```

### Main Launch

The complete simulation is launched with:

```bash
ros2 launch amr_ix1_gazebo gazebo.launch.py
```

The main launch integrates:

* Gazebo Fortress simulation
* thermal camera sensor
* ROS 2 thermal image bridge
* local Gazebo models
* `amr_ix1_thermal` visualization
* thermal colorized image
* thermal temperature legend

### Verification Status

The thermal pipeline has been functionally verified in simulation.

Verified components include:

* raw thermal image publication,
* ROS 2 thermal image bridge,
* temperature conversion,
* thermal properties on simulated models,
* colorized thermal image,
* temperature legend,
* local modified Gazebo models,
* standalone thermal visualizer launch,
* integrated Gazebo launch.

## 12. Future Improvements

The current thermal system is sufficient for simulation and development of the AMR-IX1 inspection pipeline. The following improvements may be considered in future development.

### 1. Configurable Visualization Range

Move the display minimum and maximum temperatures from fixed values in the Python implementation to ROS 2 parameters.

For example:

```text
display_min_c
display_max_c
```

This would allow the visualization range to be changed without modifying the source code.

### 2. Configurable Thermal Resolution

The current temperature conversion assumes:

`3.0 K/pixel`

This value is tied to the current Gazebo Fortress thermal sensor configuration.

A future implementation could expose the thermal resolution as a configurable parameter so that the conversion remains synchronized with different sensor configurations.

### 3. Improved Thermal Palette

The current palette is a custom Ironbow-like palette designed for clear simulation visualization.

A future version could support multiple palettes, for example:

* Ironbow
* Rainbow
* White-hot
* Black-hot
* Grayscale

This would make the visualizer more flexible for different inspection scenarios.

### 4. Temperature-Based Analysis

The thermal pipeline could be extended beyond visualization to support automated inspection.

Possible future features include:

* hottest-region detection,
* cold-region detection,
* configurable temperature thresholds,
* region-of-interest temperature statistics,
* maximum-temperature alerts,
* and thermal anomaly logging.

These features would allow the thermal camera to contribute directly to predictive-maintenance workflows.

### 5. Thermal Data Logging

Future versions could store selected thermal measurements together with:

* timestamp,
* robot pose,
* inspection waypoint,
* RGB image,
* thermal image,
* and detected thermal statistics.

This would make the thermal data more useful for inspection reports and later analysis.

### 6. Per-Instance Thermal Properties

The current thermal property is embedded in the local model SDF.

As a result, multiple instances of the same model use the same configured temperature.

A future simulation architecture could support different temperatures for different instances of the same model.

### 7. Real Thermal Camera Integration

When the AMR-IX1 hardware is available, the simulated thermal pipeline can be replaced or supplemented with a real thermal camera.

The desired architecture is to preserve a similar ROS 2 interface so that higher-level inspection software can consume thermal data without depending on whether the source is simulated or physical.

### 8. Radiometric Thermal Data

The current simulation provides temperature information through the configured Gazebo thermal sensor model.

A future hardware implementation may require radiometric thermal data from the physical sensor rather than only colorized images.

The raw temperature data should remain available independently from visualization whenever the hardware supports it.

### 9. Calibration Against the Physical Sensor

After the real thermal camera is integrated, simulation values and visualization behavior should be compared against the physical sensor.

This could include:

* temperature accuracy,
* field of view,
* image resolution,
* update rate,
* temperature range,
* and thermal response to known objects.
