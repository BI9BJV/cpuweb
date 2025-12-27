#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细测试前端JavaScript请求行为
"""
import requests
import json
import sys

def test_detailed_requests():
    """详细测试各种可能的请求"""
    base_url = "http://127.0.0.1:9001"
    
    print("详细测试各种API请求...")
    
    # 测试1: 模拟fetch API请求（前端JavaScript实际使用的）
    print("\n1. 测试fetch API样式的请求:")
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.1244 Safari/537.36'
    }
    
    try:
        response = requests.get(f"{base_url}/api/files/list", headers=headers)
        print(f"   状态码: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        try:
            json_data = response.json()
            print(f"   JSON响应: {json_data}")
        except:
            print(f"   非JSON响应: {response.text[:200]}...")
            if response.text.strip().startswith('<!'):
                print(f"   错误: 返回了HTML而非JSON!")
    except Exception as e:
        print(f"   请求失败: {e}")
    
    # 测试2: 测试POST请求
    print("\n2. 测试POST请求:")
    try:
        response = requests.post(
            f"{base_url}/api/files/write", 
            headers=headers,
            json={"path": "", "content": ""}
        )
        print(f"   状态码: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        try:
            json_data = response.json()
            print(f"   JSON响应: {json_data}")
        except:
            print(f"   非JSON响应: {response.text[:200]}...")
            if response.text.strip().startswith('<!'):
                print(f"   错误: 返回了HTML而非JSON!")
    except Exception as e:
        print(f"   请求失败: {e}")
    
    # 测试3: 测试可能触发路径验证错误的请求
    print("\n3. 测试路径验证错误:")
    try:
        response = requests.get(f"{base_url}/api/files/list?path=../../../etc/passwd")
        print(f"   状态码: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        try:
            json_data = response.json()
            print(f"   JSON响应: {json_data}")
        except:
            print(f"   非JSON响应: {response.text[:200]}...")
            if response.text.strip().startswith('<!'):
                print(f"   错误: 返回了HTML而非JSON!")
    except Exception as e:
        print(f"   请求失败: {e}")
    
    # 测试4: 模拟文件上传请求
    print("\n4. 测试文件上传请求:")
    try:
        # 创建一个简单的文本文件用于上传测试
        files = {'file': ('test.txt', 'test content', 'text/plain')}
        data = {'path': ''}
        response = requests.post(f"{base_url}/api/files/upload", files=files, data=data)
        print(f"   状态码: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        try:
            json_data = response.json()
            print(f"   JSON响应: {json_data}")
        except:
            print(f"   非JSON响应: {response.text[:200]}...")
            if response.text.strip().startswith('<!'):
                print(f"   错误: 返回了HTML而非JSON!")
    except Exception as e:
        print(f"   请求失败: {e}")
    
    # 测试5: 测试包含特殊字符的路径
    print("\n5. 测试包含特殊字符的路径:")
    try:
        # URL编码的路径
        import urllib.parse
        special_path = urllib.parse.quote("../../../../../etc/passwd")
        response = requests.get(f"{base_url}/api/files/read?path={special_path}")
        print(f"   状态码: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        try:
            json_data = response.json()
            print(f"   JSON响应: {json_data}")
        except:
            print(f"   非JSON响应: {response.text[:200]}...")
            if response.text.strip().startswith('<!'):
                print(f"   错误: 返回了HTML而非JSON!")
    except Exception as e:
        print(f"   请求失败: {e}")
    
    # 测试6: 检查是否存在路由导致重定向
    print("\n6. 测试可能的重定向:")
    try:
        response = requests.get(f"{base_url}/api/", allow_redirects=False)
        print(f"   状态码: {response.status_code} (允许重定向: {response.is_redirect})")
        if response.status_code in [301, 302, 307, 308]:
            print(f"   重定向到: {response.headers.get('Location', 'Unknown')}")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
    except Exception as e:
        print(f"   请求失败: {e}")

if __name__ == "__main__":
    test_detailed_requests()