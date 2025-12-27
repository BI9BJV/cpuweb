#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API响应格式的脚本
"""
import requests
import json
import sys
import os

# 添加项目路径
sys.path.append('/home/bi9bjv/python/cpuweb')

def test_api_responses():
    """测试API端点响应格式"""
    base_url = "http://127.0.0.1:9001"
    
    # 测试所有API端点
    api_endpoints = [
        "/api/system",
        "/api/files/list",
        "/api/files/list?path=nonexistent_dir",
        "/api/files/info",
        "/api/files/stats",
        "/api/files/read",
        "/api/files/download?path=nonexistent_file"
    ]
    
    print("测试API响应格式...")
    
    for endpoint in api_endpoints:
        try:
            url = base_url + endpoint
            print(f"测试: {url}")
            
            response = requests.get(url, timeout=10)
            
            # 检查响应是否为JSON
            try:
                json_data = response.json()
                print(f"  ✓ 返回JSON格式: {json_data}")
            except ValueError:
                print(f"  ✗ 返回非JSON格式: {response.text[:200]}...")
                print(f"    状态码: {response.status_code}")
                print(f"    Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                
                # 如果响应内容以<!DOCTYPE开头，说明是HTML
                if response.text.strip().startswith('<!'):
                    print(f"    错误: 返回了HTML而非JSON!")
                
        except requests.exceptions.ConnectionError:
            print(f"  ✗ 无法连接到服务器，可能服务器未运行")
        except requests.exceptions.Timeout:
            print(f"  ✗ 请求超时")
        except Exception as e:
            print(f"  ✗ 发生错误: {e}")
        
        print()

if __name__ == "__main__":
    test_api_responses()