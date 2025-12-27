# CPUWeb 系统监控与温度管控平台

这是一个综合的系统监控与温度管理解决方案，包含两个协同工作的子项目：

## 项目结构

```
├── cpuweb/                 # 系统监控Web界面
│   ├── app.py              # 主应用文件
│   ├── file_manager.py     # 文件管理模块
│   ├── manage_service.sh   # 服务管理脚本
│   ├── requirements.txt    # 依赖包列表
│   └── ...
└── temperature-control/    # 温度控制风扇系统
    ├── fan_control.py      # 核心控制程序
    ├── fan_control.service # systemd服务配置
    ├── install.sh          # 自动安装脚本
    ├── start.sh            # 启动脚本
    └── ...
```

## 子项目说明

### CPUWeb - 系统监控平台
一个基于Flask的系统监控与文件管理平台，提供实时系统信息监控、风扇控制、文件管理等功能。

**主要功能：**
- **系统监控**：CPU使用率、温度、频率、内存、磁盘、网络等信息
- **风扇控制**：自动/手动模式切换，循环控制
- **文件管理**：安全的文件浏览、编辑、上传、下载

### 温度管控 - 智能风扇控制系统
基于Python的硬件控制项目，通过GPIO接口控制风扇运行，根据CPU温度自动调节风扇工作模式。

**主要功能：**
- **智能温控**：高温持续运行，低温循环运行
- **硬件控制**：通过GPIO控制风扇
- **状态同步**：与CPUWeb系统集成

## 系统集成

两个子项目深度集成，协同工作实现智能温控管理：
- 温度管控程序通过API接口向CPUWeb同步风扇状态
- CPUWeb提供Web界面展示系统监控信息和风扇控制
- 支持手动和自动控制选项

## 部署说明

### CPUWeb部署
```bash
cd cpuweb
pip install -r requirements.txt
python app.py
```

### 温度管控部署
```bash
cd temperature-control
sudo ./install.sh
```

## 系统要求

- 树莓派或其他支持GPIO的Linux系统
- Python 3.6+
- 相应的硬件连接（风扇、GPIO线等）

## 版权信息

此项目为系统监控与温度管理工具，仅供个人和内部使用。

---
*版本: 1.0*  
*作者: BI9BJV*  
*更新日期: 2025年12月*