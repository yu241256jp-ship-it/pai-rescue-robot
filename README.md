# PAI Rescue Robot MVP

## Overview

ROS 2 Humble + Gazeboによる自律移動ロボットのMVPです。

機能:

- 差動二輪ロボット
- Gazeboシミュレーション
- 前方カメラ
- 色認識ベース標識検出
- 自律行動制御

## Architecture

Camera
→ Sign Detector
→ Mission Controller
→ cmd_vel
→ Robot Motion

## Sign Rules

LEFT  -> Turn Left

RIGHT -> Turn Right

STOP  -> Stop 3 Seconds

GOAL  -> Mission Complete

## Topics

Subscribe

- /front_camera/image_raw
- /detected_sign

Publish

- /cmd_vel

## Launch

```bash
ros2 launch pai_rescue_robot full_system.launch.py
