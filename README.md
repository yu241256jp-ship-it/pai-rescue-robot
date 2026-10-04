# PAI Rescue Robot

ROS 2 HumbleとGazebo Classic 11を使用した、自律移動レスキューロボットのシミュレーションプロジェクトです。

カメラによる色標識認識、LiDARによる障害物検知、緊急停止、ミッション状態管理、CSVログ記録を統合しています。

## 動作環境

- Ubuntu 22.04
- ROS 2 Humble
- Gazebo Classic 11
- Python 3
- OpenCV
- Docker
- noVNC

使用Dockerイメージ: `airobotbook/ros2-desktop-ai-robot-book-humble:latest`

## レベル1で実装した機能

- Gazebo上の差動二輪ロボット
- `/cmd_vel`による走行
- `/odom`の出力
- 前方カメラ
- `/front_camera/image_raw`
- `/front_camera/camera_info`
- OpenCVによる色標識認識
- `/detected_sign`
- 青色をLEFTとして認識
- 黄色をRIGHTとして認識
- 赤色をSTOPとして認識
- 緑色をGOALとして認識
- LEFTで左旋回
- RIGHTで右旋回
- STOPで3秒停止
- GOALで完全停止
- 1コマンドで全体を起動

## レベル2で実装した機能

- 360度LiDAR
- `/scan`を約10 Hzで配信
- 前方17度の障害物監視
- `/obstacle_detected`
- `/obstacle_distance`
- LiDARによる緊急停止
- 停止距離と解除距離を分けたヒステリシス
- 複数レーザー点と複数フレームによる安定判定
- LEFT、RIGHT、STOPの非ブロッキング制御
- 標識動作中の緊急停止割り込み
- `/sign_confidence`による認識信頼度
- 直近5フレームによる多数決
- 同じ標識への重複反応防止
- 標識消失後の再検出
- `/mission_state`による状態配信
- CSVログ記録
- レベル2専用障害物コース
- レベル2専用1コマンド起動

## 主要ノード

### sign_detector

前方カメラ画像をOpenCVで処理し、色標識を認識します。

- 青色: LEFT
- 黄色: RIGHT
- 赤色: STOP
- 緑色: GOAL

直近5フレームのうち、同じ標識が3票以上になった場合に認識を確定します。

### obstacle_monitor

LiDARの`/scan`を購読し、前方17度の障害物を監視します。

- 停止距離: 0.50 m
- 解除距離: 0.60 m
- 必要な近距離点数: 3点
- 検出確定: 3フレーム連続
- 解除確定: 5フレーム連続

複数のレーザー点を使用し、単発ノイズや自己検出による誤停止を抑制します。

### mission_controller

標識認識結果と障害物判定を受信し、ロボットの走行を制御します。

障害物検出は標識動作より優先され、LEFT、RIGHT、STOPの動作中でも緊急停止できます。

### mission_logger

ミッション状態、認識結果、障害物情報、指令速度、実速度を0.5秒ごとにCSVへ記録します。

保存先: `~/pai_ws/logs/mission_log_YYYYMMDD_HHMMSS.csv`

## 主要トピック

### センサー

- `/front_camera/image_raw`
- `/front_camera/camera_info`
- `/scan`
- `/odom`

### 標識認識

- `/detected_sign`
- `/sign_confidence`

### 障害物監視

- `/obstacle_detected`
- `/obstacle_distance`

### 制御と状態

- `/cmd_vel`
- `/mission_state`

## ミッション状態

- `FORWARD`: 通常前進
- `TURN_LEFT`: 左旋回
- `TURN_RIGHT`: 右旋回
- `STOP_WAIT`: 3秒停止
- `EMERGENCY_STOP`: 障害物による緊急停止
- `GOAL`: ミッション完了

状態の優先順位は、GOAL、EMERGENCY_STOP、標識動作、FORWARDの順です。

## レベル1互換起動

```bash
source /opt/ros/humble/setup.bash
source ~/pai_ws/install/setup.bash
ros2 launch pai_rescue_robot full_system.launch.py
```

レベル1互換起動では、従来の`mvp_course.world`を使用します。

## レベル2起動

```bash
source /opt/ros/humble/setup.bash
source ~/pai_ws/install/setup.bash
ros2 launch pai_rescue_robot level2_simulation.launch.py
```

レベル2起動では、衝突形状付き障害物を配置した`level2_course.world`を使用します。

## ビルド方法

```bash
cd ~/pai_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select pai_rescue_robot --symlink-install
source ~/pai_ws/install/setup.bash
```

## CSVログ

mission_loggerは次の10項目を0.5秒ごとに記録します。

- timestamp
- mission_state
- detected_sign
- sign_confidence
- obstacle_detected
- obstacle_distance
- cmd_linear_x
- cmd_angular_z
- odom_linear_x
- odom_angular_z

保存先: `~/pai_ws/logs/mission_log_YYYYMMDD_HHMMSS.csv`

## 安全設計

### LiDARの自己検出対策

LiDARを車体前方上部へ配置し、監視範囲を前方左右17度に限定しています。

- LiDAR前方位置: x = 0.16 m
- LiDAR高さ: z = 0.16 m

### 障害物判定の安定化

単一の最短距離だけでは停止せず、3点以上のレーザー値と3フレーム連続判定を使用します。

障害物解除には、0.60 mより遠い安全状態を5フレーム連続で確認します。

### 非ブロッキング制御

LEFT、RIGHT、STOPではtime.sleepを使用せず、ROS 2タイマーで動作時間を管理します。

そのため、標識動作中でもLiDARの緊急停止が即座に割り込めます。

## 動作確認コマンド

### LiDAR周波数

```bash
ros2 topic hz /scan
```

### 障害物判定

```bash
ros2 topic echo /obstacle_detected
```

### 障害物距離

```bash
ros2 topic echo /obstacle_distance
```

### ミッション状態

```bash
ros2 topic echo /mission_state
```

### 標識信頼度

```bash
ros2 topic echo /sign_confidence
```

## ファイル構成

```text
pai_rescue_robot/
├── launch/
│   ├── mvp_simulation.launch.py
│   ├── full_system.launch.py
│   ├── level2_base_simulation.launch.py
│   └── level2_simulation.launch.py
├── worlds/
│   ├── mvp_course.world
│   └── level2_course.world
├── urdf/
│   └── rescue_robot.urdf.xacro
├── pai_rescue_robot/
│   ├── sign_detector.py
│   ├── mission_controller.py
│   ├── obstacle_monitor.py
│   └── mission_logger.py
├── package.xml
├── setup.py
├── setup.cfg
├── README.md
└── .gitignore
```

## 最終確認結果

レベル2専用コースの実障害物を使用し、次の結果を確認しました。

- 障害物距離: 約0.397 m
- 障害物判定: true
- ミッション状態: EMERGENCY_STOP
- 指令並進速度: 0.0 m/s
- 指令角速度: 0.0 rad/s
- Gazebo上の実速度: ほぼ0

LiDARによる障害物検出から緊急停止まで、正常に連携することを確認しました。

## 工夫した点

- 完成済みのレベル1を維持したまま段階的に機能を追加
- 各変更前にバックアップを作成
- レベル1用とレベル2用のワールドを分離
- LiDARの取り付け位置と監視角度を調整して自己検出を抑制
- 複数点判定と複数フレーム判定で誤停止を抑制
- 検出距離と解除距離を分けて判定の振動を防止
- 標識認識へ信頼度と多数決を追加
- 同じ標識へ何度も反応しない重複防止を追加
- 標識制御を非ブロッキング化
- ミッション状態とセンサー情報をCSVへ記録

## 制限事項

- 色認識は照明条件やカメラ画像の色に影響されます
- 障害物監視は進行方向の前方17度を対象としています
- CSVログはコンテナ内の~/pai_ws/logsへ保存されます
- Gazebo Classic 11を前提としています

## License

Apache-2.0
