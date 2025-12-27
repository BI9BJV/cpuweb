# CPUWeb 项目依赖说明

## 项目概述

CPUWeb 是一个基于 Flask 的系统监控 Web 应用，提供系统资源监控、文件管理等功能。

## 环境要求

- Python 3.8+
- Conda 环境：cpuweb
- 树莓派或 Linux 系统（ARM64/x86_64）

## 核心依赖

### Web 框架
- **Flask** (3.1.2) - Web 应用框架
- **Werkzeug** (3.1.4) - WSGI 工具库
- **Jinja2** (3.1.6) - 模板引擎
- **MarkupSafe** (3.0.3) - HTML/XML 安全标记
- **itsdangerous** (2.2.0) - 数据签名
- **click** (8.3.1) - 命令行界面
- **blinker** (1.9.0) - 信号库

### 系统监控
- **psutil** (7.2.0) - 系统和进程信息

### 网络请求
- **requests** (2.32.5) - HTTP 库

## 安装方法

### 1. 创建 Conda 环境

```bash
conda create -n cpuweb python=3.10
conda activate cpuweb
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install Flask==3.1.2
pip install psutil==7.2.0
pip install requests==2.32.5
pip install Werkzeug==3.1.4
pip install Jinja2==3.1.6
pip install itsdangerous==2.2.0
pip install MarkupSafe==3.0.3
pip install click==8.3.1
pip install blinker==1.9.0
```

## 依赖说明

### Flask 及相关组件

Flask 是项目的核心 Web 框架，提供路由、模板渲染、请求处理等功能。

- **Flask**: 主框架
- **Werkzeug**: 提供 WSGI 工具和实用程序
- **Jinja2**: 模板渲染引擎
- **MarkupSafe**: 自动转义不安全的 HTML/XML 标记
- **itsdangerous**: 安全地签名数据
- **click**: 命令行工具支持
- **blinker**: 信号系统，用于事件通知

### 系统监控模块

psutil 用于获取系统信息：
- CPU 使用率
- 内存使用情况
- 磁盘使用情况
- 网络流量
- 进程信息

### 网络请求

requests 用于 HTTP 请求：
- API 调用
- 外部服务集成

## 版本兼容性

所有依赖版本都经过测试，确保兼容性：
- Python 3.10
- ARM64 架构（树莓派）
- x86_64 架构

## 更新依赖

如需更新依赖，请先测试兼容性：

```bash
# 更新单个包
pip install --upgrade <package_name>

# 更新所有包
pip list --outdated
pip install --upgrade <package_name>
```

## 故障排除

### 常见问题

1. **psutil 安装失败**
   ```bash
   pip install --upgrade pip
   pip install psutil
   ```

2. **Flask 版本冲突**
   ```bash
   pip install --force-reinstall Flask
   ```

3. **导入错误**
   ```bash
   pip install --upgrade <package_name>
   ```

## 安全注意事项

- 定期更新依赖包以获取安全补丁
- 使用虚拟环境隔离项目依赖
- 不要在生产环境中使用 `debug=True`
- 定期审查依赖包的安全公告

## 许可证

本项目使用的所有依赖包均为开源软件，遵循各自的开源许可证。

## 联系方式

如有问题或建议，请通过项目 Issue 跟踪器反馈。