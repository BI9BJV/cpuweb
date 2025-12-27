# 树莓派智能温度控制风扇系统

## 项目简介

树莓派智能温度控制风扇系统是一个基于Python的硬件控制项目，通过GPIO接口控制风扇运行，根据CPU温度自动调节风扇工作模式。系统采用智能控制策略，当CPU温度高于40°C时持续运行风扇，当温度低于40°C时采用循环模式（运行5分钟，停止5分钟）。

### 核心特性
- **智能温度控制**：根据CPU温度自动调节风扇工作模式
- **双重控制模式**：高温持续模式 + 低温循环模式
- **系统集成**：与CPUWeb监控系统集成，实时同步风扇状态
- **高可靠性**：完善的错误处理和资源清理机制
- **易部署**：支持服务化部署和开机自启动

## 硬件要求

- **树莓派**：所有支持GPIO的树莓派型号（推荐4B或更高版本）
- **风扇类型**：5V DC PWM调速风扇或普通DC风扇
- **连接线**：杜邦线或专用GPIO连接线
- **供电**：确保供电充足以驱动风扇

### GPIO连接说明
- **BCM 14引脚**（物理引脚8）- 风扇控制信号线
- **GND**（物理引脚6/9/14/20/25/30/34/39）- 地线
- **5V**（物理引脚2/4）- 电源线（根据风扇规格选择）

## 软件依赖

- **Python 3.6+**
- **RPi.GPIO** - GPIO接口控制库
- **requests** - HTTP请求库（用于与CPUWeb通信）

## 快速部署

### 方法一：使用安装脚本（推荐）
```bash
cd /home/bi9bjv/python/温度管控
sudo ./install.sh
```

### 方法二：手动部署
```bash
# 1. 安装依赖
sudo apt update
sudo apt install python3-rpi.gpio
pip3 install requests

# 2. 设置服务
sudo cp fan_control.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fan_control
sudo systemctl start fan_control
```

## 启动方式

### 1. 直接运行
```bash
cd /home/bi9bjv/python/温度管控
sudo python3 fan_control.py
```

### 2. 使用启动脚本
```bash
cd /home/bi9bjv/python/温度管控
sudo ./start.sh
```

### 3. 系统服务管理（推荐用于生产环境）
```bash
# 启动服务
sudo systemctl start fan_control

# 停止服务
sudo systemctl stop fan_control

# 重启服务
sudo systemctl restart fan_control

# 查看服务状态
sudo systemctl status fan_control

# 启用开机自启
sudo systemctl enable fan_control

# 禁用开机自启
sudo systemctl disable fan_control

# 查看实时日志
sudo journalctl -u fan_control -f
```

## 配置参数详解

### 主要参数（在 `fan_control.py` 中定义）
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `FAN_PIN` | 14 | 风扇控制GPIO引脚（BCM模式） |
| `HIGH_TEMP` | 40.0 | 高温阈值（摄氏度） |
| `TEMP_CHECK_INTERVAL` | 1 | 温度检查间隔（秒） |
| `TEMP_PATH` | /sys/class/thermal/thermal_zone0/temp | 温度传感器路径 |
| `CYCLE_DURATION` | 300 | 循环周期（秒，5分钟） |

### 控制逻辑说明
1. **高温模式**（温度 ≥ 40°C）：风扇持续运行，直到温度降至阈值以下
2. **低温循环模式**（温度 < 40°C）：执行运行5分钟-停止5分钟的循环
3. **模式切换**：当温度变化时，系统会自动切换控制模式

## 系统关系

### 与CPUWeb的协同工作
树莓派智能温度控制风扇系统与CPUWeb系统监控平台紧密协作：
- **数据流向**：温度管控程序读取CPU温度并控制风扇硬件
- **状态同步**：通过API接口向CPUWeb同步风扇状态变化
- **协同控制**：两个系统共同管理风扇运行，提供手动和自动控制选项
- **监控集成**：CPUWeb提供Web界面展示风扇状态和系统监控信息
- **接口协议**：使用HTTP POST请求到 `http://localhost:9001/api/fan/control_event` 端点
- **控制事件**：发送风扇开启/关闭事件，包含当前温度信息

### 与CPUWeb集成
本系统与CPUWeb监控系统深度集成：
- 风扇状态变化时自动向CPUWeb发送控制事件
- 通过API端点 `http://localhost:9001/api/fan/control_event` 同步状态
- 支持外部系统监控和控制风扇状态

## 项目文件结构

```
/home/bi9bjv/python/温度管控/
├── fan_control.py       # 核心控制程序 - 实现温度监控和风扇控制逻辑
├── start.sh            # 手动启动脚本 - 便捷启动程序
├── install.sh          # 自动安装脚本 - 自动配置环境和服务
├── fan_control.service # systemd服务配置文件 - 用于系统服务管理
└── README.md           # 项目说明文档
```

### 文件功能详述
- **fan_control.py**：主要的控制逻辑，包括温度读取、风扇控制、模式切换、状态同步等功能
- **start.sh**：简化启动过程的脚本，自动检查依赖并启动程序
- **install.sh**：完整安装脚本，自动安装依赖、配置服务、启动服务
- **fan_control.service**：systemd服务配置，实现后台运行和开机自启

## 控制算法详解

### 双模式控制策略
系统采用智能双模式控制算法：

#### 持续运行模式
- **触发条件**：CPU温度 ≥ 40°C
- **行为**：风扇持续运行
- **目的**：快速降低CPU温度，防止过热

#### 循环运行模式
- **触发条件**：CPU温度 < 40°C
- **行为**：运行5分钟 → 停止5分钟 → 循环
- **目的**：保持适度散热，减少风扇磨损

### 状态管理
- **fan_status**：记录当前风扇状态（开启/关闭）
- **last_switch_time**：记录上次切换时间
- **is_in_cooling_period**：标识是否处于运行周期

## 故障排除

### 常见问题及解决方案

#### 1. 风扇不工作
- **检查点**：
  - GPIO连接是否正确（BCM 14引脚）
  - 供电是否正常
  - 是否使用root权限运行
- **解决方法**：
  - 确认硬件连接
  - 使用 `sudo` 运行程序

#### 2. 无法读取温度
- **检查点**：
  - `/sys/class/thermal/thermal_zone0/temp` 文件是否存在
  - 系统是否支持温度传感器
- **解决方法**：
  - 检查系统支持情况
  - 更新系统固件

#### 3. 权限问题
- **现象**：GPIO访问被拒绝
- **解决方法**：
  - 使用 `sudo` 运行程序或脚本
  - 将用户添加到gpio组

#### 4. 服务启动失败
- **检查日志**：
  ```bash
  sudo journalctl -u fan_control -f
  ```
- **常见原因**：
  - 依赖库未安装
  - 文件权限问题
  - 路径配置错误

### 调试模式
运行程序时会显示详细信息：
- 当前CPU温度
- 风扇状态
- 工作模式
- 模式切换日志

## 性能监控

### 日志记录
程序运行时会记录以下信息：
- 温度变化
- 风扇开关状态
- 模式切换时间点
- 错误和警告

### 状态同步
- 风扇状态实时同步至CPUWeb系统
- 支持外部系统监控和控制

## 安全注意事项

1. **权限安全**：程序需要root权限访问GPIO
2. **硬件安全**：确保接线正确，避免短路
3. **系统安全**：程序具有完善的错误处理机制
4. **数据安全**：仅读取系统温度信息，不涉及用户数据

## 维护建议

### 日常维护
- 定期检查服务状态
- 监控系统日志
- 清理风扇灰尘

### 性能优化
- 根据实际需求调整温度阈值
- 优化循环周期参数
- 监控系统资源使用情况

### 备份策略
- 定期备份配置文件
- 保存服务配置
- 记录自定义参数设置

## 扩展功能

### 自定义参数
可根据需要修改以下参数：
- 温度阈值
- 循环周期
- 检查间隔
- GPIO引脚

### 集成扩展
- 与更多监控系统集成
- 添加湿度等其他传感器
- 实现更复杂的控制算法

---

*版本: 2.0*  
*更新日期: 2025年12月*  
*作者: BI9BJV*