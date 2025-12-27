#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试可能触发HTML响应的异常情况
"""
import requests
import json
import sys
import os

def test_problematic_endpoints():
    """测试可能导致HTML响应的端点"""
    base_url = "http://127.0.0.1:9001"
    
    # 测试可能触发异常的端点
    test_cases = [
        # 正常API端点
        "/api/files/list?path=../../../",
        "/api/files/info?path=../../../",
        "/api/files/read?path=../../../",
        # 不存在的API端点
        "/api/nonexistent_endpoint",
        "/nonexistent_page",
        # 可能触发路径遍历的端点
        "/api/files/list?path=../../../etc/passwd",
        "/api/files/info?path=../../../etc/shadow",
        # 测试边界情况
        "/api/files/read?path=" + "../" * 100,
    ]
    
    print("测试可能触发HTML响应的端点...")
    
    for endpoint in test_cases:
        try:
            url = base_url + endpoint
            print(f"测试: {url}")
            
            response = requests.get(url, timeout=10)
            
            # 检查响应是否为JSON
            try:
                json_data = response.json()
                print(f"  ✓ 返回JSON格式: {json_data}")
            except ValueError:
                print(f"  ⚠ 返回非JSON格式: {response.text[:200]}...")
                print(f"    状态码: {response.status_code}")
                print(f"    Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
                
                # 如果响应内容以<!DOCTYPE开头，说明是HTML
                if response.text.strip().startswith('<!'):
                    print(f"    警告: 返回了HTML而非JSON!")
                    print(f"    这可能是导致错误的原因")
                
        except requests.exceptions.ConnectionError:
            print(f"  ✗ 无法连接到服务器，可能服务器未运行")
        except requests.exceptions.Timeout:
            print(f"  ✗ 请求超时")
        except Exception as e:
            print(f"  ✗ 发生错误: {e}")
        
        print()

if __name__ == "__main__":
    test_problematic_endpoints()