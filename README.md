# CPUWeb 系统监控与温度管控平台

## 🎯 项目概述

这是一个综合的系统监控与温度管理解决方案，包含两个协同工作的子项目：

- **CPUWeb** - 系统监控Web界面（位于 cpuweb/ 目录）
- **温度管控** - 智能风扇控制系统（位于 temperature-control/ 目录）

两个子项目深度集成，协同工作实现智能温控管理。

## 🌟 主要功能

### CPUWeb - 系统监控平台
一个基于Flask的系统监控与文件管理平台，提供实时系统信息监控、风扇控制、文件管理等功能。

#### 系统监控
- ✅ **CPU监控** - 使用率、频率、核心数、型号、温度
- ✅ **功耗监控** - 实时功耗、CPU电压、CPU温度
- ✅ **内存监控** - 使用率、已使用、可用、总容量
- ✅ **磁盘监控** - 使用率、已使用、可用、总容量
- ✅ **网络监控** - 上传速度、下载速度、总上传、总下载
- ✅ **磁盘IO** - 读取速度、写入速度、总读取、总写入
- ✅ **系统信息** - 运行时间、操作系统、内核版本、系统架构

#### 风扇控制
- **自动模式**: 根据温度自动控制风扇运行
- **手动模式**: 手动开启/关闭风扇
- **循环控制**: 可设置运行和停止时长
- **实时监控**: 显示当前运行状态、剩余时间等

#### 文件管理
- ✅ 浏览目录和文件
- ✅ 上传文件（支持拖拽）
- ✅ 下载文件
- ✅ 创建文件夹
- ✅ 重命名文件/文件夹
- ✅ 删除文件/文件夹
- ✅ 文件统计信息

### 温度管控 - 智能风扇控制系统
基于Python的硬件控制项目，通过GPIO接口控制风扇运行，根据CPU温度自动调节风扇工作模式。

#### 核心特性
- **智能温度控制**：根据CPU温度自动调节风扇工作模式
- **双重控制模式**：高温持续模式 + 低温循环模式
- **系统集成**：与CPUWeb监控系统集成，实时同步风扇状态
- **高可靠性**：完善的错误处理和资源清理机制
- **易部署**：支持服务化部署和开机自启动

## 🚀 快速开始

### 环境要求
- Python 3.6+ (CPUWeb需要Python 3.8+)
- Conda 环境：cpuweb
- 树莓派或其他支持GPIO的Linux系统
- 系统端口 9001 未被占用

### 完整安装部署

1. **进入CPUWeb目录并创建 Conda 环境**
```bash
cd cpuweb

# 初始化conda
source /home/bi9bjv/miniconda3/etc/profile.d/conda.sh

# 创建cpuweb环境
conda create -n cpuweb python=3.9 -y

# 激活环境
conda activate cpuweb
```

2. **安装CPUWeb依赖**
```bash
# 确保在cpuweb目录中
cd /home/bi9bjv/github_upload_temp/cpuweb

# 安装依赖
pip install -r requirements.txt
```

3. **部署温度管控系统**
```bash
cd ../temperature-control
sudo ./install.sh
```

4. **启动服务**
```bash
# 启动CPUWeb
cd ../cpuweb
python app.py

# 或使用管理脚本
./manage_service.sh start
```

## 🌐 访问地址

- **本地访问**: http://localhost:9001
- **局域网访问**: http://[你的IP地址]:9001
- **API接口**: http://localhost:9001/api/system

要获取您的局域网IP地址，可以运行：
```bash
hostname -I
```

## 🔧 技术架构

### CPUWeb技术栈
- **后端**: Python Flask（Web框架）
- **系统监控**: psutil（系统和进程信息）
- **HTTP请求**: requests（HTTP库）
- **前端**: HTML5 + CSS3 + JavaScript（实时监控界面）
- **数据更新**: 后台线程定时采集（1秒间隔）
- **API接口**: RESTful JSON格式

### 温度管控技术栈
- **Python 3.6+**
- **RPi.GPIO** - GPIO接口控制库
- **requests** - HTTP请求库（用于与CPUWeb通信）

## 🔄 系统集成

### 与CPUWeb的协同工作
树莓派智能温度控制风扇系统与CPUWeb系统监控平台紧密协作：
- **数据流向**：温度管控程序读取CPU温度并控制风扇硬件
- **状态同步**：通过API接口向CPUWeb同步风扇状态变化
- **协同控制**：两个系统共同管理风扇运行，提供手动和自动控制选项
- **监控集成**：CPUWeb提供Web界面展示风扇状态和系统监控信息
- **接口协议**：使用HTTP POST请求到 `http://localhost:9001/api/fan/control_event` 端点
- **控制事件**：发送风扇开启/关闭事件，包含当前温度信息

### API接口
#### CPUWeb API
- `GET /api/system` - 获取系统信息
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
- `POST /api/fan/mode` - 设置风扇运行模式（auto/manual）
- `POST /api/fan/status` - 设置风扇运行状态（on/off）
- `POST /api/fan/control_event` - 处理外部控制事件

## 📁 项目结构

```
├── cpuweb/                 # 系统监控Web界面
│   ├── app.py              # 主应用文件
│   ├── file_manager.py     # 文件管理模块
│   ├── file_manager.html   # 文件管理前端界面
│   ├── manage_service.sh   # 服务管理脚本
│   ├── requirements.txt    # 依赖包列表
│   ├── cpuweb.service      # systemd服务配置
│   └── ...
└── temperature-control/    # 温度控制风扇系统
    ├── fan_control.py      # 核心控制程序
    ├── fan_control.service # systemd服务配置
    ├── install.sh          # 自动安装脚本
    ├── start.sh            # 启动脚本
    └── ...
```

## ⚠️ 注意事项

1. **硬件要求**: 温度管控需要树莓派GPIO接口连接风扇
2. **权限要求**: 温度管控需要root权限访问GPIO
3. **系统要求**: CPUWeb需要足够的权限访问系统信息
4. **端口占用**: CPUWeb服务运行在9001端口，确保端口未被占用
5. **依赖安装**: 两个系统可能需要独立的依赖安装

## 📞 故障排除

### 服务无法启动
```bash
# 检查端口占用
sudo lsof -i :9001

# 检查CPUWeb服务状态
cd cpuweb
./manage_service.sh status

# 检查温度管控服务状态
sudo systemctl status fan_control

# 查看CPUWeb日志
./manage_service.sh logs

# 查看温度管控日志
sudo journalctl -u fan_control -f
```

## 📄 许可证

此项目为系统监控与温度管理工具，仅供个人和内部使用。

---
*版本: 1.0*  
*作者: BI9BJV*  
*更新日期: 2025年12月*