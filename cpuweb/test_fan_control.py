#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试风扇控制功能的脚本
"""
import requests
import json
import time
import sys

def test_fan_control():
    """测试风扇控制功能"""
    base_url = "http://127.0.0.1:9001"
    
    print("开始测试风扇控制功能...")
    print("="*50)
    
    # 测试1: 获取系统信息（包含风扇控制信息）
    print("1. 测试获取系统信息（包含风扇控制信息）:")
    try:
        response = requests.get(f"{base_url}/api/system")
        data = response.json()
        
        if 'fan_control' in data:
            print(f"   ✓ 成功获取风扇控制信息:")
            print(f"     - 运行状态: {data['fan_control']['is_running']}")
            print(f"     - 运行模式: {data['fan_control']['mode']}")
            print(f"     - 状态: {data['fan_control']['status']}")
            print(f"     - 运行时长: {data['fan_control']['running_duration']}秒")
            print(f"     - 停止时长: {data['fan_control']['stop_duration']}秒")
            print(f"     - 当前周期剩余: {data['fan_control']['current_cycle_remaining']}秒")
        else:
            print(f"   ✗ 未获取到风扇控制信息")
    except Exception as e:
        print(f"   ✗ 获取系统信息失败: {e}")
    print()
    
    # 测试2: 设置风扇模式为手动
    print("2. 测试设置风扇模式为手动:")
    try:
        response = requests.post(f"{base_url}/api/fan/mode", 
                                json={"mode": "manual"})
        data = response.json()
        
        if data.get('success'):
            print(f"   ✓ 风扇模式成功设置为: {data['fan_control']['mode']}")
        else:
            print(f"   ✗ 设置风扇模式失败: {data.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"   ✗ 设置风扇模式请求失败: {e}")
    print()
    
    # 测试3: 设置风扇状态为开启
    print("3. 测试设置风扇状态为开启:")
    try:
        response = requests.post(f"{base_url}/api/fan/status", 
                                json={"status": "on"})
        data = response.json()
        
        if data.get('success'):
            print(f"   ✓ 风扇状态成功设置为: {data['fan_control']['status']}")
        else:
            print(f"   ✗ 设置风扇状态失败: {data.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"   ✗ 设置风扇状态请求失败: {e}")
    print()
    
    # 等待一下查看变化
    time.sleep(1)
    
    # 测试4: 获取更新后的系统信息
    print("4. 测试获取更新后的系统信息:")
    try:
        response = requests.get(f"{base_url}/api/system")
        data = response.json()
        
        if 'fan_control' in data:
            print(f"   ✓ 更新后风扇控制信息:")
            print(f"     - 运行状态: {data['fan_control']['is_running']}")
            print(f"     - 运行模式: {data['fan_control']['mode']}")
            print(f"     - 状态: {data['fan_control']['status']}")
            print(f"     - 当前周期剩余: {data['fan_control']['current_cycle_remaining']}秒")
        else:
            print(f"   ✗ 未获取到风扇控制信息")
    except Exception as e:
        print(f"   ✗ 获取系统信息失败: {e}")
    print()
    
    # 测试5: 设置风扇状态为关闭
    print("5. 测试设置风扇状态为关闭:")
    try:
        response = requests.post(f"{base_url}/api/fan/status", 
                                json={"status": "off"})
        data = response.json()
        
        if data.get('success'):
            print(f"   ✓ 风扇状态成功设置为: {data['fan_control']['status']}")
        else:
            print(f"   ✗ 设置风扇状态失败: {data.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"   ✗ 设置风扇状态请求失败: {e}")
    print()
    
    # 等待一下查看变化
    time.sleep(1)
    
    # 测试6: 设置风扇模式为自动
    print("6. 测试设置风扇模式为自动:")
    try:
        response = requests.post(f"{base_url}/api/fan/mode", 
                                json={"mode": "auto"})
        data = response.json()
        
        if data.get('success'):
            print(f"   ✓ 风扇模式成功设置为: {data['fan_control']['mode']}")
        else:
            print(f"   ✗ 设置风扇模式失败: {data.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"   ✗ 设置风扇模式请求失败: {e}")
    print()
    
    # 测试7: 再次获取系统信息确认所有功能正常
    print("7. 再次获取系统信息确认所有功能正常:")
    try:
        response = requests.get(f"{base_url}/api/system")
        data = response.json()
        
        if 'fan_control' in data:
            print(f"   ✓ 最终风扇控制信息:")
            print(f"     - 运行状态: {data['fan_control']['is_running']}")
            print(f"     - 运行模式: {data['fan_control']['mode']}")
            print(f"     - 状态: {data['fan_control']['status']}")
            print(f"     - 目标温度: {data['fan_control']['target_temp']}°C")
            print(f"     - 运行时长: {data['fan_control']['running_duration']}秒")
            print(f"     - 停止时长: {data['fan_control']['stop_duration']}秒")
            print(f"     - 当前周期剩余: {data['fan_control']['current_cycle_remaining']}秒")
        else:
            print(f"   ✗ 未获取到风扇控制信息")
    except Exception as e:
        print(f"   ✗ 获取系统信息失败: {e}")
    print()
    
    # 测试8: 测试外部控制事件API（模拟温度管控程序的调用）
    print("8. 测试外部控制事件API:")
    try:
        response = requests.post(f"{base_url}/api/fan/control_event", 
                                json={"action": "start", "temperature": 50.0})
        data = response.json()
        
        if data.get('success'):
            print(f"   ✓ 外部控制事件成功处理: {data['message']}")
        else:
            print(f"   ✗ 外部控制事件处理失败: {data.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"   ✗ 外部控制事件请求失败: {e}")
    print()
    
    print("="*50)
    print("风扇控制功能测试完成!")

def check_server_running():
    """检查服务器是否运行"""
    try:
        response = requests.get("http://127.0.0.1:9001/api/system", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("检查服务器状态...")
    if not check_server_running():
        print("错误: 服务器未运行，请先启动 app.py")
        print("运行命令: python3 /home/bi9bjv/python/cpuweb/app.py")
        sys.exit(1)
    
    test_fan_control()