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

カメラ
→ 標識検出
→ ミッションコントローラー
→ cmd_vel
→ ロボットの動作

## Sign Rules

LEFT  -> 左旋回

RIGHT -> 右旋回

STOP  -> 3秒停止

GOAL  -> ミッション完了

## Topics

Subscribe

- /front_camera/image_raw
- /detected_sign

Publish

- /cmd_vel

## Launch

```bash
ros2 launch pai_rescue_robot full_system.launch.py
