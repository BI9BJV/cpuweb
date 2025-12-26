# CPUWeb 系统监控面板

## 🎯 功能概述

CPUWeb 是一个基于 Flask 的系统监控 Web 应用，提供实时系统资源监控、文件管理等功能。专为树莓派等 ARM64 架构设备优化，采用复古 DOS 风格界面设计。

## 🌟 主要功能

### 系统监控
- ✅ **CPU监控** - 使用率、频率、核心数、型号、温度
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
- 系统端口 9001 未被占用

### 系统配置检查

在安装前，请确认您的系统满足以下条件：

```bash
# 检查Python版本
python3 --version

# 检查系统架构
uname -a

# 检查端口9001是否被占用
sudo netstat -tuln | grep :9001

# 检查是否已安装conda
conda --version
```

### 完整安装部署

1. **进入项目目录**
```bash
cd /home/bi9bjv/python/cpuweb
```

2. **创建 Conda 环境**
```bash
# 初始化conda
source /home/bi9bjv/miniconda3/etc/profile.d/conda.sh

# 创建cpuweb环境
conda create -n cpuweb python=3.9 -y

# 激活环境
conda activate cpuweb
```

3. **安装依赖**
```bash
# 确保在项目目录中
cd /home/bi9bjv/python/cpuweb

# 安装依赖
pip install -r requirements.txt
```

4. **测试应用**
```bash
# 激活环境
source /home/bi9bjv/miniconda3/etc/profile.d/conda.sh
conda activate cpuweb

# 运行应用
cd /home/bi9bjv/python/cpuweb
python app.py
```

5. **设置开机自启动（systemd）**
```bash
# 复制服务文件到系统目录
sudo cp /home/bi9bjv/python/cpuweb/cpuweb.service /etc/systemd/system/

# 重新加载systemd配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start cpuweb

# 启用开机自启动
sudo systemctl enable cpuweb

# 检查服务状态
sudo systemctl status cpuweb
```

## 🌐 访问地址

- **本地访问**: http://localhost:9001
- **局域网访问**: http://[你的IP地址]:9001
- **API接口**: http://localhost:9001/api/system

要获取您的局域网IP地址，可以运行：
```bash
hostname -I
```

## 📊 监控功能详解

### CPU监控
- **使用率**: 实时CPU使用百分比，通过 psutil.cpu_percent() 获取
- **频率**: 当前CPU频率（MHz），通过 psutil.cpu_freq() 获取
- **核心数**: CPU核心数量，通过 psutil.cpu_count() 获取
- **型号**: CPU型号信息，从 /proc/cpuinfo 读取，支持ARM和x86架构
- **温度**: CPU核心温度（°C），从 /sys/class/thermal/thermal_zone* 读取

### 功耗监控
- **实时功耗**: 系统功耗估算（W），基于CPU使用率估算（空闲2.5W，满载7W）
- **CPU电压**: 使用 vcgencmd 读取树莓派CPU电压（V）
- **CPU温度**: 从系统热传感器读取CPU温度（°C）

### 内存监控
- **使用率**: 内存使用百分比，通过 psutil.virtual_memory() 获取
- **已使用**: 已使用内存（GB），通过 psutil.virtual_memory() 获取
- **可用**: 可用内存（GB），通过 psutil.virtual_memory() 获取
- **总容量**: 总内存容量（GB），通过 psutil.virtual_memory() 获取

### 磁盘监控
- **使用率**: 磁盘使用百分比，通过 psutil.disk_usage() 获取
- **已使用**: 已使用空间（GB），通过 psutil.disk_usage() 获取
- **可用**: 可用空间（GB），通过 psutil.disk_usage() 获取
- **总容量**: 总容量（GB），通过 psutil.disk_usage() 获取

### 网络监控
- **上传速度**: 实时上传速度（KB/s），基于 psutil.net_io_counters() 计算
- **下载速度**: 实时下载速度（KB/s），基于 psutil.net_io_counters() 计算
- **总上传**: 累计上传流量（MB），通过 psutil.net_io_counters() 获取
- **总下载**: 累计下载流量（MB），通过 psutil.net_io_counters() 获取

### 磁盘IO
- **读取速度**: 实时读取速度（KB/s），基于 psutil.disk_io_counters() 计算
- **写入速度**: 实时写入速度（KB/s），基于 psutil.disk_io_counters() 计算
- **总读取**: 累计读取量（MB），通过 psutil.disk_io_counters() 获取
- **总写入**: 累计写入量（MB），通过 psutil.disk_io_counters() 获取

### 系统信息
- **运行时间**: 系统运行时间，基于 psutil.boot_time() 计算
- **操作系统**: 系统名称，通过 platform.system() 获取
- **内核版本**: 内核版本，通过 platform.release() 获取
- **系统架构**: 系统架构，通过 platform.machine() 获取

## 🎨 界面特点

- **复古DOS风格**: 经典的命令行界面设计，包含CRT屏幕效果
- **实时更新**: 每1秒自动刷新数据，通过JavaScript定时请求API
- **可视化进度条**: 直观显示使用率，颜色根据负载变化（绿色<60%，橙色60-80%，红色>80%）
- **全中文界面**: 所有信息都以中文显示
- **响应式布局**: 支持桌面和移动端访问

## 🔧 技术架构

- **后端**: Python Flask（Web框架）
- **系统监控**: psutil（系统和进程信息）
- **HTTP请求**: requests（HTTP库）
- **前端**: HTML5 + CSS3 + JavaScript（实时监控界面）
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
# 确保在项目目录中
cd /home/bi9bjv/python/cpuweb

# 启动服务
./manage_service.sh start

# 停止服务
./manage_service.sh stop

# 重启服务
./manage_service.sh restart

# 查看状态
./manage_service.sh status

# 开机自启
./manage_service.sh enable

# 禁用自启
./manage_service.sh disable

# 查看日志
./manage_service.sh logs
```

### 使用 systemd
```bash
# 启动服务
sudo systemctl start cpuweb

# 停止服务
sudo systemctl stop cpuweb

# 重启服务
sudo systemctl restart cpuweb

# 查看状态
sudo systemctl status cpuweb

# 开机自启
sudo systemctl enable cpuweb

# 禁用自启
sudo systemctl disable cpuweb

# 查看日志
sudo journalctl -u cpuweb -f

# 查看最近50行日志
sudo journalctl -u cpuweb -n 50
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
- **click** (8.1.7) - 命令行界面
- **blinker** (1.9.0) - 信号库

### 依赖安装路径
所有依赖将安装在 conda 环境中：
- 环境路径: `/home/bi9bjv/miniconda3/envs/cpuweb`
- Python 解释器: `/home/bi9bjv/miniconda3/envs/cpuweb/bin/python`

## 📁 项目结构

```
/home/bi9bjv/python/cpuweb/
├── app.py                 # 主应用文件
├── file_manager.html      # 文件管理界面
├── file_manager.py        # 文件管理后端
├── requirements.txt       # Python依赖
├── start.sh               # 启动脚本
├── cpuweb.service         # systemd服务配置
├── manage_service.sh      # 服务管理脚本
├── DEPENDENCIES.md        # 依赖说明
├── nginx_config_example.conf # Nginx配置示例
└── README.md              # 项目说明
```

## ⚠️ 注意事项

1. **端口占用**: 服务运行在9001端口，确保端口未被占用
2. **CPU温度**: 温度检测依赖于系统硬件支持，支持多种路径检测
3. **CPU电压**: 电压检测使用 vcgencmd，仅支持树莓派
4. **功耗估算**: 功耗基于CPU使用率估算（空闲2.5W，满载7W）
5. **文件管理**: 文件管理功能基于当前用户权限，可能需要sudo权限访问系统文件
6. **浏览器**: 建议在现代浏览器中使用以获得最佳体验
7. **系统权限**: 服务以 bi9bjv 用户运行，确保该用户有足够权限访问系统信息

## ⚙️ 自定义配置

### 修改服务配置
如果需要修改服务配置（如端口、运行用户等），编辑 `/etc/systemd/system/cpuweb.service`：

```bash
sudo nano /etc/systemd/system/cpuweb.service
```

修改后需要重新加载配置：
```bash
sudo systemctl daemon-reload
sudo systemctl restart cpuweb
```

### 修改应用端口
要修改应用运行的端口，需要修改 `app.py` 中的端口配置：

```python
# 在 app.py 文件的最后部分
if __name__ == '__main__':
    # 启动Flask应用，修改port参数来更改端口
    app.run(host='0.0.0.0', port=9001, debug=False, threaded=True)
```

## 🔄 更新日志

### v2.0 (2025-12-26)
- ✨ 新增功耗监控功能（实时功耗、CPU电压、CPU温度）
- ✨ 新增系统信息显示（操作系统、内核版本、系统架构）
- 🗑️ 移除SSH终端功能
- 🗑️ 移除VNC远程桌面功能
- 🎨 优化界面为DOS风格设计
- 📦 更新依赖，移除不需要的SSH相关包
- 🔧 优化系统信息采集，添加缓存机制

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

# 查看详细日志
sudo journalctl -u cpuweb -f

# 查看最近50行日志
sudo journalctl -u cpuweb -n 50

# 检查服务配置
sudo systemctl cat cpuweb

# 重新加载配置
sudo systemctl daemon-reload
```

### 依赖安装失败
```bash
# 检查conda环境
conda info --envs

# 激活环境
source /home/bi9bjv/miniconda3/etc/profile.d/conda.sh
conda activate cpuweb

# 更新pip
pip install --upgrade pip

# 重新安装依赖
pip install -r requirements.txt --force-reinstall --no-cache-dir
```

### 环境激活问题
```bash
# 手动激活conda环境
source /home/bi9bjv/miniconda3/etc/profile.d/conda.sh
conda activate cpuweb

# 验证Python路径
which python

# 验证已安装的包
pip list
```

### 文件权限问题
```bash
# 检查项目目录权限
ls -la /home/bi9bjv/python/cpuweb

# 确保文件可执行
chmod +x /home/bi9bjv/python/cpuweb/*.sh

# 检查服务配置文件权限
ls -la /etc/systemd/system/cpuweb.service
```

### Python解释器路径问题
```bash
# 检查Python解释器路径
ls -la /home/bi9bjv/miniconda3/envs/cpuweb/bin/python

# 检查服务中配置的Python路径
cat /etc/systemd/system/cpuweb.service | grep ExecStart
```

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

- Flask - Web框架
- psutil - 系统监控库
- 树莓派基金会 - 硬件平台