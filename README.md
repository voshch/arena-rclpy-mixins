# arena_rclpy_mixins

Shared rclpy and asyncio glue of [Arena-Rosnav](https://github.com/voshch/Arena): the
`ArenaMixinNode` base class, typed ROS parameters and launch arguments, lifecycle clients,
namespaces, time and spin helpers, and the parameter census. The package API is described in
[arena_rclpy_mixins/README.md](arena_rclpy_mixins/README.md).

## Layout

```
arena_rclpy_mixins/          this repository, the uv workspace root
`-- arena_rclpy_mixins/      ament_python package
    |-- arena_rclpy_mixins/
    `-- tests/
        |-- unit/            plain pytest
        `-- ros/             need a sourced ROS 2 environment
```

Arena carries this repository as the submodule `utils/arena_rclpy_mixins`, and its
`uv.lock` is derived from Arena's composed workspace there.

## Build and test

```
mkdir -p ws/src && git clone https://github.com/voshch/arena-rclpy-mixins ws/src/arena_rclpy_mixins
cd ws
rosdep install --from-paths src --ignore-src -y
pip install aiomonitor pytest
colcon build --packages-select arena_rclpy_mixins
source install/setup.bash
cd src/arena_rclpy_mixins/arena_rclpy_mixins && pytest tests
```

Lint runs from the repository root with the pinned hooks: `pre-commit run --all-files`.
