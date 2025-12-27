#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟前端JavaScript行为的测试脚本
"""
import requests
import json
import time
import sys
import os

def simulate_frontend_behavior():
    """模拟前端JavaScript的行为"""
    base_url = "http://127.0.0.1:9001"
    
    print("模拟前端JavaScript行为...")
    print()
    
    # 测试1: 加载目录列表
    print("测试1: 加载目录列表")
    try:
        response = requests.get(f"{base_url}/api/files/list")
        try:
            data = response.json()
            print(f"  ✓ 返回JSON: {data.get('success', 'Unknown')}")
        except ValueError as e:
            print(f"  ✗ 非JSON响应: {response.text[:200]}...")
            print(f"    Content-Type: {response.headers.get('Content-Type')}")
            if response.text.strip().startswith('<!'):
                print(f"    错误: 返回HTML而非JSON!")
    except Exception as e:
        print(f"  ✗ 请求失败: {e}")
    print()
    
    # 测试2: 获取文件统计信息
    print("测试2: 获取文件统计信息")
    try:
        response = requests.get(f"{base_url}/api/files/stats")
        try:
            data = response.json()
            print(f"  ✓ 返回JSON: {data.get('success', 'Unknown')}")
        except ValueError as e:
            print(f"  ✗ 非JSON响应: {response.text[:200]}...")
            print(f"    Content-Type: {response.headers.get('Content-Type')}")
            if response.text.strip().startswith('<!'):
                print(f"    错误: 返回HTML而非JSON!")
    except Exception as e:
        print(f"  ✗ 请求失败: {e}")
    print()
    
    # 测试3: 访问不存在的API端点
    print("测试3: 访问不存在的API端点")
    try:
        response = requests.get(f"{base_url}/api/files/nonexistent")
        try:
            data = response.json()
            print(f"  ✓ 返回JSON: {data}")
        except ValueError as e:
            print(f"  ✗ 非JSON响应: {response.text[:200]}...")
            print(f"    Content-Type: {response.headers.get('Content-Type')}")
            if response.text.strip().startswith('<!'):
                print(f"    错误: 返回HTML而非JSON!")
    except Exception as e:
        print(f"  ✗ 请求失败: {e}")
    print()
    
    # 测试4: 模拟文件读取操作
    print("测试4: 模拟文件读取操作（缺少必需参数）")
    try:
        response = requests.get(f"{base_url}/api/files/read")
        try:
            data = response.json()
            print(f"  ✓ 返回JSON: {data.get('success', 'Unknown')}")
        except ValueError as e:
            print(f"  ✗ 非JSON响应: {response.text[:200]}...")
            print(f"    Content-Type: {response.headers.get('Content-Type')}")
            if response.text.strip().startswith('<!'):
                print(f"    错误: 返回HTML而非JSON!")
    except Exception as e:
        print(f"  ✗ 请求失败: {e}")
    print()
    
    # 测试5: 模拟文件写入操作
    print("测试5: 模拟文件写入操作（无效请求体）")
    try:
        response = requests.post(f"{base_url}/api/files/write", json={})
        try:
            data = response.json()
            print(f"  ✓ 返回JSON: {data.get('success', 'Unknown')}")
        except ValueError as e:
            print(f"  ✗ 非JSON响应: {response.text[:200]}...")
            print(f"    Content-Type: {response.headers.get('Content-Type')}")
            if response.text.strip().startswith('<!'):
                print(f"    错误: 返回HTML而非JSON!")
    except Exception as e:
        print(f"  ✗ 请求失败: {e}")
    print()
    
    # 测试6: 模拟异常情况 - 尝试访问服务器内部可能的错误
    print("测试6: 模拟可能导致内部错误的请求")
    try:
        # 发送格式错误的JSON
        response = requests.post(
            f"{base_url}/api/files/write", 
            data="invalid json {",
            headers={"Content-Type": "application/json"}
        )
        try:
            data = response.json()
            print(f"  ✓ 返回JSON: {data.get('success', 'Unknown')}")
        except ValueError as e:
            print(f"  ✗ 非JSON响应: {response.text[:200]}...")
            print(f"    Content-Type: {response.headers.get('Content-Type')}")
            if response.text.strip().startswith('<!'):
                print(f"    错误: 返回HTML而非JSON!")
    except Exception as e:
        print(f"  ✗ 请求失败: {e}")
    print()

if __name__ == "__main__":
    simulate_frontend_behavior()