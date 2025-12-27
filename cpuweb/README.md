# CPUWeb 系统监控与文件管理平台

CPUWeb是一个基于Flask的系统监控与文件管理平台，提供实时系统信息监控、风扇控制、文件管理等功能。

## 功能特性

### 1. 系统监控
- **CPU信息**: 使用率、温度、频率、核心数、型号
- **功耗监控**: 实时功耗、CPU电压、CPU温度
- **内存信息**: 使用率、已用/可用/总量
- **磁盘信息**: 使用率、已用/可用/总量
- **网络信息**: 上传/下载速度、总上传/下载量
- **IO信息**: 读取/写入速度、总读取/写入量
- **系统信息**: 运行时间、操作系统、内核版本、系统架构

### 2. 风扇控制
- **自动模式**: 根据温度自动控制风扇运行
- **手动模式**: 手动开启/关闭风扇
- **循环控制**: 可设置运行和停止时长
- **实时监控**: 显示当前运行状态、剩余时间等

### 3. 文件管理
- **安全路径访问**: 防止路径遍历攻击
- **文件操作**: 浏览、创建、删除、重命名、上传、下载
- **文本编辑**: 在线编辑多种格式的文本文件
- **文件预览**: 支持预览多种文本格式文件

## 技术架构

### 前端
- **HTML/CSS**: 现代化界面设计，使用CSS Grid布局
- **JavaScript**: 异步API调用，实时数据更新
- **视觉效果**: CRT屏幕风格、发光效果、响应式设计

### 后端
- **Python 3.9+**: 主要开发语言
- **Flask**: Web框架
- **psutil**: 系统信息获取
- **requests**: HTTP请求处理

## 安装与部署

### 环境要求
- Python 3.9+
- pip
- 系统权限访问（获取CPU温度、电压等信息）

### 依赖安装
```bash
pip install -r requirements.txt
```

### 启动服务
```bash
# 直接运行
python app.py

# 或使用管理脚本
./manage_service.sh start
```

### 服务管理
```bash
# 启动服务
./manage_service.sh start

# 停止服务
./manage_service.sh stop

# 重启服务
./manage_service.sh restart

# 查看状态
./manage_service.sh status

# 查看日志
./manage_service.sh logs

# 设置开机自启
./manage_service.sh enable
```

## 系统配置

### 端口配置
- 默认端口: 9001
- 如需修改端口，请编辑 `app.py` 中的启动参数

### 基础路径
- 默认基础路径: `/home/bi9bjv`
- 可在 `file_manager.py` 中修改

## API接口

### 系统信息接口
- `GET /api/system` - 获取系统信息

### 文件管理接口
- `GET /api/files/list?path=PATH` - 列出目录内容
- `GET /api/files/info?path=PATH` - 获取文件信息
- `GET /api/files/read?path=PATH` - 读取文件内容
- `POST /api/files/write` - 写入文件内容
- `POST /api/files/create_dir` - 创建目录
- `POST /api/files/delete` - 删除文件/目录
- `POST /api/files/rename` - 重命名文件/目录
- `POST /api/files/upload` - 上传文件
- `GET /api/files/download?path=PATH` - 下载文件
- `GET /api/files/stats?path=PATH` - 获取目录统计信息

### 风扇控制接口
- `POST /api/fan/mode` - 设置风扇运行模式（auto/manual）
- `POST /api/fan/status` - 设置风扇运行状态（on/off）
- `POST /api/fan/control_event` - 处理外部控制事件

## 风扇控制说明

### 自动模式
- 当CPU温度 ≥ 60°C 时，风扇持续运行
- 当CPU温度 < 60°C 时，风扇按循环模式运行
  - 运行时长: 5分钟（300秒）
  - 停止时长: 2分钟（120秒）

### 手动模式
- 可手动控制风扇开启/关闭
- 不受温度和循环模式影响

### 状态变量
- `enabled`: 风扇控制是否启用
- `status`: 当前运行状态（off/on/auto）
- `mode`: 运行模式（manual/auto）
- `speed`: 风扇转速（0-100）
- `target_temp`: 自动模式目标温度
- `running_duration`: 连续运行时长（秒）
- `stop_duration`: 停止时长（秒）
- `current_cycle_remaining`: 当前周期剩余时间（秒）

## 安全特性

### 文件访问安全
- 路径遍历防护
- 基础路径限制
- 权限检查
- 文件类型验证

### API安全
- 输入验证
- 错误处理
- 访问控制

## 使用场景

### 系统监控
- 实时监控系统各项指标
- 观察系统健康状态
- 性能分析

### 温度管理
- 监控CPU温度
- 自动控制风扇运行
- 防止系统过热

### 文件管理
- 远程文件浏览
- 简单文件编辑
- 文件上传下载

## 温度控制子项目

本仓库包含一个配套的温度控制子项目 (`temperature-control/`)，用于实现基于温度的自动化风扇控制。

### 子项目概述
- **项目位置**: `temperature-control/` 目录
- **核心功能**: 根据CPU温度自动控制风扇运行
- **控制逻辑**: 温度≥40°C时持续运行，温度<40°C时循环运行（运行5分钟，停止5分钟）

### 部署方式
#### 服务模式（推荐）
```bash
cd temperature-control
sudo ./install.sh
```

#### 手动启动
```bash
cd temperature-control
sudo ./start.sh
```

#### 直接运行
```bash
cd temperature-control
sudo python3 fan_control.py
```

### 硬件连接
- **GPIO引脚**: BCM 14 (物理引脚8)
- **电源**: 连接5V电源(物理引脚2/4)
- **地线**: 连接GND(物理引脚6/9/14/20/25/30/34/39)

### 工作模式
- **高温模式** (≥40°C): 风扇持续运行
- **低温模式** (<40°C): 风扇循环运行 (运行5分钟，停止5分钟)
- **状态同步**: 风扇状态变化会自动同步到CPUWeb主程序

## 故障排除

### 常见问题
1. **无法获取CPU温度**
   - 检查系统是否支持温度传感器
   - 确认访问权限

2. **无法获取CPU电压**
   - 树莓派系统需要vcgencmd命令
   - 确认系统权限

3. **端口被占用**
   - 检查端口使用情况
   - 修改配置使用其他端口

### 服务日志
- 日志文件: `service.log`
- 使用管理脚本查看日志: `./manage_service.sh logs`

## 系统集成

### 与温度控制子项目的深度集成
CPUWeb系统与同目录下的温度控制子项目（temperature-control）深度集成，共同构建完整的系统监控和温度管理解决方案：

#### 集成架构
- **CPUWeb主程序** (`app.py`)：提供Web界面、系统监控、手动风扇控制功能
- **温度控制子项目** (`temperature-control/`)：独立的温度监控和自动风扇控制程序
- **协同工作机制**：两个程序通过API接口进行状态同步和协调控制

#### API接口协议
- **控制事件端点**: `http://localhost:9001/api/fan/control_event`
- **请求格式**: POST JSON数据 `{action: 'start'|'stop', temperature: number}`
- **功能**: 温度控制子项目向主程序报告风扇状态变化

#### 双重控制策略
- **Web手动控制**: 用户可通过Web界面手动开启/关闭风扇（手动模式）
- **自动温度控制**: 温度控制子项目根据CPU温度自动控制风扇（自动模式）
- **智能协调**: 当温度控制子项目检测到高温时，会自动接管风扇控制权

## 维护与扩展

### 日志管理
- 定期清理日志文件
- 监控服务运行状态

### 功能扩展
- 可扩展更多硬件监控功能
- 可添加更多文件操作功能
- 可集成其他系统管理功能

## 版权与许可

此项目为系统监控工具，仅供个人和内部使用。

---

*版本: 1.0*  
*作者: BI9BJV*  
*最后更新: 2025年12月*