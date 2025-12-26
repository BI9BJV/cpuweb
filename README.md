# CPUWeb 系统监控面板

## 🎯 功能概述

CPUWeb 是一个基于 Flask 的系统监控 Web 应用，提供实时系统资源监控、文件管理等功能。专为树莓派等 ARM64 架构设备优化，采用复古 DOS 风格界面设计。

## 🌟 主要功能

### 系统监控
- ✅ **CPU监控** - 使用率、频率、核心数、型号
- ✅ **功耗监控** - 实时功耗、CPU电压、CPU温度
- ✅ **内存监控** - 使用率、已使用、可用、总容量
- ✅ **磁盘监控** - 使用率、已使用、可用、总容量
- ✅ **网络监控** - 上传速度、下载速度、总上传、总下载
- ✅ **磁盘IO** - 读取速度、写入速度、总读取、总写入
- ✅ **系统信息** - 运行时间、操作系统、内核版本、系统架构

### 文件管理
- ✅ 浏览目录和文件
- ✅ 上传文件（支持拖拽）
- ✅ 下载文件
- ✅ 创建文件夹
- ✅ 重命名文件/文件夹
- ✅ 删除文件/文件夹
- ✅ 文件统计信息

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Conda 环境：cpuweb
- 树莓派或 Linux 系统（ARM64/x86_64）

### 一键部署

```bash
cd /home/bi9bjv/BF/cpuweb
./deploy.sh
```

### 手动安装

1. **创建 Conda 环境**
```bash
conda create -n cpuweb python=3.10 -y
conda activate cpuweb
```

2. **安装依赖**
```bash
cd /home/bi9bjv/cpuweb
pip install -r requirements.txt
```

3. **启动服务**
```bash
./start.sh
```

## 🌐 访问地址

- **本地访问**: http://localhost:9001
- **局域网访问**: http://[你的IP地址]:9001
- **API接口**: http://localhost:9001/api/system

## 📊 监控功能详解

### CPU监控
- **使用率**: 实时CPU使用百分比
- **频率**: 当前CPU频率（MHz）
- **核心数**: CPU核心数量
- **型号**: CPU型号信息（支持ARM和x86架构）

### 功耗监控
- **实时功耗**: 系统功耗估算（W）
- **CPU电压**: 使用 vcgencmd 读取树莓派CPU电压（V）
- **CPU温度**: CPU核心温度（°C）

### 内存监控
- **使用率**: 内存使用百分比
- **已使用**: 已使用内存（GB）
- **可用**: 可用内存（GB）
- **总容量**: 总内存容量（GB）

### 磁盘监控
- **使用率**: 磁盘使用百分比
- **已使用**: 已使用空间（GB）
- **可用**: 可用空间（GB）
- **总容量**: 总容量（GB）

### 网络监控
- **上传速度**: 实时上传速度（KB/s）
- **下载速度**: 实时下载速度（KB/s）
- **总上传**: 累计上传流量（MB）
- **总下载**: 累计下载流量（MB）

### 磁盘IO
- **读取速度**: 实时读取速度（KB/s）
- **写入速度**: 实时写入速度（KB/s）
- **总读取**: 累计读取量（MB）
- **总写入**: 累计写入量（MB）

## 🎨 界面特点

- **复古DOS风格**: 经典的命令行界面设计
- **实时更新**: 每1秒自动刷新数据
- **可视化进度条**: 直观显示使用率，颜色根据负载变化
- **全中文界面**: 所有信息都以中文显示
- **响应式布局**: 支持桌面和移动端访问

## 🔧 技术架构

- **后端**: Python Flask
- **依赖库**: psutil, requests
- **前端**: HTML5 + CSS3 + JavaScript
- **数据更新**: 后台线程定时采集（1秒间隔）
- **API接口**: RESTful JSON格式

## 📝 API使用

### 获取系统信息
```bash
curl http://localhost:9001/api/system
```

### 返回数据格式
```json
{
  "cpu": {
    "percent": 37.9,
    "temp": 45.3,
    "freq": 1800.0,
    "count": 4,
    "model": "ARM Cortex-A76",
    "voltage": 0.926
  },
  "power": {
    "watts": 4.21
  },
  "memory": {
    "total": 7.6,
    "used": 2.4,
    "free": 5.2,
    "percent": 31.6
  },
  "disk": {
    "total": 118.4,
    "used": 39.1,
    "free": 79.3,
    "percent": 33.0
  },
  "network": {
    "bytes_sent": 1024.5,
    "bytes_recv": 2048.2,
    "upload_speed": 52.09,
    "download_speed": 3.96
  },
  "io": {
    "read_bytes": 1024.5,
    "write_bytes": 2048.2,
    "read_speed": 100.0,
    "write_speed": 50.0
  },
  "uptime": 3630.6,
  "timestamp": "2025-12-26 01:42:21",
  "system": {
    "system": "Linux",
    "release": "6.12.47+rpt-rpi-v8",
    "machine": "aarch64"
  }
}
```

## 🛠️ 服务管理

### 使用管理脚本
```bash
./manage_service.sh start    # 启动服务
./manage_service.sh stop     # 停止服务
./manage_service.sh restart  # 重启服务
./manage_service.sh status   # 查看状态
./manage_service.sh enable   # 开机自启
./manage_service.sh disable  # 禁用自启
./manage_service.sh logs     # 查看日志
```

### 使用 systemd
```bash
sudo systemctl start cpuweb       # 启动服务
sudo systemctl stop cpuweb        # 停止服务
sudo systemctl restart cpuweb     # 重启服务
sudo systemctl status cpuweb      # 查看状态
sudo systemctl enable cpuweb      # 开机自启
sudo systemctl disable cpuweb     # 禁用自启
sudo journalctl -u cpuweb -f      # 查看日志
```

## 📦 依赖说明

### 核心依赖
- **Flask** (3.1.2) - Web应用框架
- **psutil** (7.2.0) - 系统和进程信息
- **requests** (2.32.5) - HTTP库

### Flask相关
- **Werkzeug** (3.1.4) - WSGI工具库
- **Jinja2** (3.1.6) - 模板引擎
- **itsdangerous** (2.2.0) - 数据签名
- **MarkupSafe** (3.0.3) - HTML/XML安全标记
- **click** (8.3.1) - 命令行界面
- **blinker** (1.9.0) - 信号库

## ⚠️ 注意事项

1. **端口占用**: 服务运行在9001端口，确保端口未被占用
2. **CPU温度**: 温度检测依赖于系统硬件支持
3. **CPU电压**: 电压检测使用 vcgencmd，仅支持树莓派
4. **功耗估算**: 功耗基于CPU使用率估算（空闲2.5W，满载7W）
5. **文件管理**: 文件管理功能基于当前用户权限，可能需要sudo权限访问系统文件
6. **浏览器**: 建议在现代浏览器中使用以获得最佳体验

## 🔄 更新日志

### v2.0 (2025-12-26)
- ✨ 新增功耗监控功能（实时功耗、CPU电压、CPU温度）
- ✨ 新增系统信息显示（操作系统、内核版本、系统架构）
- 🗑️ 移除SSH终端功能
- 🗑️ 移除VNC远程桌面功能
- 🎨 优化界面为DOS风格设计
- 📦 更新依赖，移除不需要的SSH相关包

### v1.0
- 初始版本
- 基础系统监控功能
- 文件管理功能

## 📞 故障排除

### 服务无法启动
```bash
# 检查端口占用
sudo lsof -i :9001

# 检查服务状态
sudo systemctl status cpuweb

# 查看日志
sudo journalctl -u cpuweb -n 50
```

### 依赖安装失败
```bash
# 更新pip
pip install --upgrade pip

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### 文件管理权限问题
```bash
# 检查当前用户权限
whoami

# 使用sudo启动服务（需要修改cpuweb.service中的User）
sudo systemctl start cpuweb
```

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

- Flask - Web框架
- psutil - 系统监控库
- 树莓派基金会 - 硬件平台