#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理模块 - 重构版
提供安全的文件操作功能，包括浏览、创建、删除、重命名、上传、下载等
"""
import os
import shutil
import mimetypes
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, base_path: str = "/home/bi9bjv", max_file_size: int = 10 * 1024 * 1024):  # 10MB默认限制
        """
        初始化文件管理器
        :param base_path: 基础路径，所有操作将限制在此路径下
        :param max_file_size: 最大文件大小限制（字节）
        """
        self.base_path = Path(base_path).resolve()
        self.max_file_size = max_file_size
        self._validate_base_path()
        
    def _validate_base_path(self):
        """验证基础路径是否存在且可访问"""
        if not self.base_path.exists():
            raise ValueError(f"基础路径不存在: {self.base_path}")
        if not self.base_path.is_dir():
            raise ValueError(f"基础路径不是目录: {self.base_path}")
    
    def _safe_path(self, path: str) -> Optional[Path]:
        """
        确保路径在安全范围内，防止路径遍历攻击
        :param path: 用户提供的路径
        :return: 安全的路径对象，如果路径不安全则返回None
        """
        try:
            # 防止路径遍历攻击
            # 允许空路径（表示基础路径/根目录）
            if path and ('..' in path or path.startswith('/')):
                return None
                
            full_path = (self.base_path / path).resolve()
            
            # 验证路径是否在基础路径内
            if not str(full_path).startswith(str(self.base_path)):
                return None
                
            return full_path
        except Exception as e:
            logger.error(f"路径验证错误: {e}")
            return None
    
    def _get_file_info(self, path: Path) -> Dict:
        """
        获取文件的详细信息
        :param path: 文件路径
        :return: 包含文件信息的字典
        """
        stat = path.stat()
        mime_type, _ = mimetypes.guess_type(str(path))
        
        return {
            "name": path.name,
            "path": str(path.relative_to(self.base_path)),
            "type": "directory" if path.is_dir() else "file",
            "size": stat.st_size if path.is_file() else 0,
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            "created": datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
            "accessed": datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S'),
            "permissions": oct(stat.st_mode)[-3:],
            "mime_type": mime_type,
            "is_readable": os.access(path, os.R_OK),
            "is_writable": os.access(path, os.W_OK),
            "is_executable": os.access(path, os.X_OK)
        }
    
    def list_directory(self, path: str = "") -> Dict:
        """
        列出目录内容
        :param path: 要列出的目录路径
        :return: 包含目录内容的字典
        """
        safe_path = self._safe_path(path)
        if not safe_path:
            return {"success": False, "message": "路径不安全或不存在"}
        
        if not safe_path.exists():
            return {"success": False, "message": "路径不存在或无权访问"}
        
        if not safe_path.is_dir():
            return {"success": False, "message": "指定路径不是目录"}
        
        try:
            items = []
            for item in safe_path.iterdir():
                try:
                    item_info = self._get_file_info(item)
                    items.append(item_info)
                except PermissionError:
                    # 如果无法访问某个文件/目录，跳过它
                    logger.warning(f"无法访问: {item}, 跳过...")
                    continue
            
            # 按类型和名称排序（目录在前，然后按名称）
            items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
            
            return {
                "success": True,
                "items": items,
                "current_path": str(safe_path.relative_to(self.base_path)) if safe_path != self.base_path else "",
                "parent_path": str(safe_path.parent.relative_to(self.base_path)) 
                    if safe_path.parent != self.base_path and str(safe_path.parent).startswith(str(self.base_path)) 
                    else None,
                "total_items": len(items)
            }
            
        except PermissionError:
            return {"success": False, "message": "无权限访问该目录"}
        except Exception as e:
            logger.error(f"读取目录失败: {e}")
            return {"success": False, "message": f"读取目录失败: {str(e)}"}
    
    def get_file_info(self, path: str) -> Dict:
        """
        获取文件/目录的详细信息
        :param path: 文件路径
        :return: 包含文件信息的字典
        """
        safe_path = self._safe_path(path)
        if not safe_path or not safe_path.exists():
            return {"success": False, "message": "文件不存在或无权访问"}
        
        try:
            return {
                "success": True,
                **self._get_file_info(safe_path)
            }
        except PermissionError:
            return {"success": False, "message": "无权限访问该文件"}
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return {"success": False, "message": f"获取文件信息失败: {str(e)}"}
    
    def create_directory(self, path: str, name: str) -> Dict:
        """
        创建目录
        :param path: 父目录路径
        :param name: 新目录名称
        :return: 操作结果
        """
        parent_safe_path = self._safe_path(path)
        if not parent_safe_path or not parent_safe_path.exists() or not parent_safe_path.is_dir():
            return {"success": False, "message": "父目录不存在"}
        
        if not name or name in ['.', '..']:
            return {"success": False, "message": "无效的目录名"}
        
        new_dir_path = parent_safe_path / name
        if new_dir_path.exists():
            return {"success": False, "message": "目录已存在"}
        
        try:
            new_dir_path.mkdir(parents=True, exist_ok=True)
            return {"success": True, "message": "目录创建成功", "path": str(new_dir_path.relative_to(self.base_path))}
        except PermissionError:
            return {"success": False, "message": "无权限创建目录"}
        except Exception as e:
            logger.error(f"创建目录失败: {e}")
            return {"success": False, "message": f"创建目录失败: {str(e)}"}
    
    def delete_item(self, path: str) -> Dict:
        """
        删除文件或目录
        :param path: 要删除的文件/目录路径
        :return: 操作结果
        """
        safe_path = self._safe_path(path)
        if not safe_path or not safe_path.exists():
            return {"success": False, "message": "文件或目录不存在"}
        
        try:
            if safe_path.is_dir():
                shutil.rmtree(safe_path)
            else:
                safe_path.unlink()
            return {"success": True, "message": "删除成功"}
        except PermissionError:
            return {"success": False, "message": "无权限删除该文件/目录"}
        except OSError as e:
            if e.errno == 39:  # 目录不为空
                return {"success": False, "message": "目录不为空，无法删除"}
            else:
                logger.error(f"删除失败: {e}")
                return {"success": False, "message": f"删除失败: {str(e)}"}
        except Exception as e:
            logger.error(f"删除失败: {e}")
            return {"success": False, "message": f"删除失败: {str(e)}"}
    
    def rename_item(self, path: str, new_name: str) -> Dict:
        """
        重命名文件或目录
        :param path: 当前路径
        :param new_name: 新名称
        :return: 操作结果
        """
        safe_path = self._safe_path(path)
        if not safe_path or not safe_path.exists():
            return {"success": False, "message": "文件或目录不存在"}
        
        if not new_name or new_name in ['.', '..']:
            return {"success": False, "message": "无效的新名称"}
        
        new_path = safe_path.parent / new_name
        if new_path.exists():
            return {"success": False, "message": "目标名称已存在"}
        
        try:
            safe_path.rename(new_path)
            return {
                "success": True, 
                "message": "重命名成功",
                "old_path": path,
                "new_path": str(new_path.relative_to(self.base_path))
            }
        except PermissionError:
            return {"success": False, "message": "无权限重命名"}
        except Exception as e:
            logger.error(f"重命名失败: {e}")
            return {"success": False, "message": f"重命名失败: {str(e)}"}
    
    def format_size(self, size: float) -> str:
        """
        格式化文件大小的辅助函数
        :param size: 文件大小（字节）
        :return: 格式化后的大小字符串
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def get_directory_stats(self, path: str = "") -> Dict:
        """
        获取目录统计信息
        :param path: 目录路径
        :return: 包含统计信息的字典
        """
        safe_path = self._safe_path(path)
        if not safe_path or not safe_path.exists():
            return {"success": False, "message": "路径不存在"}
        
        try:
            total_size = 0
            file_count = 0
            dir_count = 0
            
            def _count_items_recursive(item_path: Path):
                nonlocal total_size, file_count, dir_count
                for sub_item in item_path.iterdir():
                    try:
                        if sub_item.is_file():
                            file_count += 1
                            total_size += sub_item.stat().st_size
                        elif sub_item.is_dir():
                            dir_count += 1
                            _count_items_recursive(sub_item)  # 递归遍历子目录
                    except PermissionError:
                        # 跳过无法访问的文件/目录
                        continue
            
            if safe_path.is_file():
                file_count = 1
                total_size = safe_path.stat().st_size
            else:
                _count_items_recursive(safe_path)
            
            return {
                "success": True,
                "path": str(safe_path.relative_to(self.base_path)),
                "file_count": file_count,
                "directory_count": dir_count,
                "total_items": file_count + dir_count,
                "size": self.format_size(total_size),
                "size_bytes": total_size
            }
            
        except PermissionError:
            return {"success": False, "message": "无权限访问目录内容"}
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {"success": False, "message": f"获取统计信息失败: {str(e)}"}
    
    def read_file_content(self, path: str, max_size: Optional[int] = None) -> Dict:
        """
        读取文件内容
        :param path: 文件路径
        :param max_size: 最大大小限制（如果提供，则覆盖实例的默认限制）
        :return: 包含文件内容的字典
        """
        allowed_text_extensions = {
            '.txt', '.py', '.js', '.html', '.htm', '.css', '.json', '.xml', 
            '.md', '.csv', '.log', '.ini', '.cfg', '.yml', '.yaml', '.sh',
            '.sql', '.ts', '.tsx', '.jsx', '.vue', '.dart', '.go', '.java',
            '.cpp', '.c', '.h', '.hpp', '.rb', '.php', '.pl', '.pm'
        }
        
        if max_size is None:
            max_size = self.max_file_size
        
        safe_path = self._safe_path(path)
        if not safe_path or not safe_path.exists():
            return {"success": False, "message": "文件不存在或无权访问"}
        
        if safe_path.is_dir():
            return {"success": False, "message": "不能读取目录内容"}
        
        try:
            # 检查文件大小
            stat = safe_path.stat()
            if stat.st_size > max_size:
                return {
                    "success": False, 
                    "message": f"文件过大 ({self.format_size(stat.st_size)})，无法预览",
                    "size_limit": self.format_size(max_size),
                    "size_bytes": stat.st_size
                }
            
            # 检查文件扩展名，只允许显示文本文件
            file_ext = safe_path.suffix.lower()
            if file_ext not in allowed_text_extensions:
                # 对于非文本文件，返回文件信息而不是内容
                return {
                    "success": False,
                    "message": f"不支持的文件类型: {file_ext}，仅支持以下文本类型: {', '.join(sorted(allowed_text_extensions))}",
                    "type": "unsupported",
                    "file_info": self._get_file_info(safe_path)
                }
            
            # 尝试以文本模式读取文件
            try:
                with open(safe_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {
                    "success": True,
                    "content": content,
                    "type": "text",
                    "lines": len(content.splitlines()),
                    "size": self.format_size(len(content.encode('utf-8')))
                }
            except UnicodeDecodeError:
                # 如果不是UTF-8编码，尝试其他常见编码
                for encoding in ['gbk', 'gb2312', 'latin-1']:
                    try:
                        with open(safe_path, "r", encoding=encoding) as f:
                            content = f.read()
                        return {
                            "success": True,
                            "content": content,
                            "type": "text",
                            "encoding": encoding,
                            "lines": len(content.splitlines()),
                            "size": self.format_size(len(content.encode('utf-8')))
                        }
                    except UnicodeDecodeError:
                        continue
                
                # 如果所有编码都失败，返回二进制文件信息
                return {
                    "success": False,
                    "message": "文件为二进制格式或不支持的编码，无法预览",
                    "type": "binary",
                    "file_info": self._get_file_info(safe_path)
                }
        except PermissionError:
            return {"success": False, "message": "无权限读取文件"}
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return {"success": False, "message": f"读取文件失败: {str(e)}"}
    
    def write_file_content(self, path: str, content: str, overwrite: bool = True) -> Dict:
        """
        写入文件内容
        :param path: 文件路径
        :param content: 要写入的内容
        :param overwrite: 是否覆盖已存在的文件
        :return: 操作结果
        """
        safe_path = self._safe_path(path)
        if not safe_path:
            return {"success": False, "message": "路径不安全"}
        
        if safe_path.exists() and not overwrite:
            return {"success": False, "message": "文件已存在，且不允许覆盖"}
        
        try:
            # 确保父目录存在
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return {
                "success": True,
                "message": "文件保存成功",
                "path": str(safe_path.relative_to(self.base_path)),
                "size": self.format_size(len(content.encode('utf-8')))
            }
        except PermissionError:
            return {"success": False, "message": "无权限写入文件"}
        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            return {"success": False, "message": f"写入文件失败: {str(e)}"}

# 创建文件管理器实例
file_manager = FileManager(base_path="/home/bi9bjv")