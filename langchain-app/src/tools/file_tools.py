"""
文件操作工具模块 - 提供文件读写、目录管理等基本文件系统操作功能
"""

from langchain.tools import tool
import os
import shutil
import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import json

@tool(description="读取文件内容，支持文本文件和二进制文件")
def read_file(file_path_param) -> str:
    """读取文件内容
    
    Args:
        file_path_param: 可以是文件路径字符串，也可以是包含file_path和binary的JSON字符串/字典
        
    Returns:
        str: 文件内容或二进制内容的描述
    """
    # 初始化参数默认值
    file_path = None
    binary = False
    
    try:
        # 1. 尝试解析复杂参数
        if isinstance(file_path_param, dict):
            # 如果是字典类型，直接取出参数
            if 'file_path' in file_path_param:
                file_path = file_path_param['file_path']
            if 'binary' in file_path_param:
                binary = file_path_param['binary']
        elif isinstance(file_path_param, str):
            # 1.1 移除可能的引号和换行符
            file_path_param = file_path_param.strip().strip('"\'').strip()
            
            # 1.2 尝试解析可能的JSON字符串
            json_candidate = file_path_param.strip()
            if (json_candidate.startswith('{') and json_candidate.endswith('}')):
                try:
                    import json
                    params = json.loads(json_candidate)
                    if isinstance(params, dict):
                        if 'file_path' in params:
                            file_path = params['file_path']
                        if 'binary' in params:
                            binary = params['binary']
                except (json.JSONDecodeError, ValueError) as e:
                    # 尝试清理JSON字符串再解析一次
                    cleaned_json = json_candidate.replace("'", '"')  # 替换单引号为双引号
                    try:
                        params = json.loads(cleaned_json)
                        if isinstance(params, dict):
                            if 'file_path' in params:
                                file_path = params['file_path']
                            if 'binary' in params:
                                binary = params['binary']
                    except:
                        # 如果还是失败，则按文本处理
                        pass
            
            # 1.3 如果没有成功解析为JSON，则作为纯文件路径处理
            if file_path is None:
                file_path = file_path_param
        
        # 2. 尝试从frame中获取参数（适用于直接调用）
        if file_path is None:
            import inspect
            frame = inspect.currentframe()
            try:
                # 尝试获取调用者的局部变量
                if frame and frame.f_back:
                    kwargs = frame.f_back.f_locals.get('kwargs', {})
                    if 'file_path' in kwargs:
                        file_path = kwargs['file_path']
                    if 'binary' in kwargs:
                        binary = kwargs['binary']
                    # 尝试获取action_input参数(Agent可能使用的格式)
                    if file_path is None and 'action_input' in frame.f_back.f_locals:
                        action_input = frame.f_back.f_locals.get('action_input')
                        if isinstance(action_input, str):
                            file_path = action_input.strip()
            finally:
                del frame  # 避免循环引用
        
        # 3. 最终检查必要参数
        if file_path is None:
            return "错误: 必须提供file_path参数，指定要读取的文件路径"
        
        # 4. 开始实际的文件操作
        # 统一路径分隔符并去除两端可能的引号
        file_path = file_path.strip('"\'')
        normalized_path = os.path.normpath(file_path)
        
        if binary:
            with open(normalized_path, 'rb') as file:
                content = file.read()
                # 对于二进制文件，返回其大小和类型信息
                return f"读取二进制文件成功: 文件大小 {len(content)} 字节"
        else:
            with open(normalized_path, 'r', encoding='utf-8') as file:
                content = file.read()
                return content
    except FileNotFoundError:
        return f"错误: 文件 '{file_path}' 不存在"
    except PermissionError:
        return f"错误: 没有权限读取文件 '{file_path}'"
    except UnicodeDecodeError:
        return f"错误: 无法以文本模式解码文件 '{file_path}'，可能是二进制文件，请尝试使用 binary=True"
    except Exception as e:
        return f"读取文件时发生错误: {str(e)}"

@tool(description="写入内容到文件，支持创建新文件或覆盖现有文件")
def write_file(file_path_param) -> str:
    """写入内容到文件
    
    Args:
        file_path_param: 可以是文件路径字符串，也可以是包含file_path和content的JSON字符串/字典
        
    Returns:
        str: 操作结果描述
    """
    # 初始化参数默认值
    file_path = None
    content = None
    binary = False
    
    try:
        # 1. 尝试解析复杂参数
        if isinstance(file_path_param, dict):
            # 如果是字典类型，直接取出参数
            if 'file_path' in file_path_param:
                file_path = file_path_param['file_path']
            if 'content' in file_path_param:
                content = file_path_param['content']
            if 'binary' in file_path_param:
                binary = file_path_param['binary']
        elif isinstance(file_path_param, str):
            # 如果是字符串，尝试判断不同格式
            
            # 1.1 尝试解析可能的JSON字符串 - 增强的JSON解析
            json_candidate = file_path_param.strip()
            if (json_candidate.startswith('{') and json_candidate.endswith('}')) or \
               (json_candidate.startswith('[') and json_candidate.endswith(']')):
                try:
                    params = json.loads(json_candidate)
                    if isinstance(params, dict):
                        if 'file_path' in params:
                            file_path = params['file_path']
                        if 'content' in params:
                            content = params['content']
                        if 'binary' in params:
                            binary = params['binary']
                except (json.JSONDecodeError, ValueError) as e:
                    # 尝试清理JSON字符串再解析一次
                    cleaned_json = json_candidate.replace("'", '"')  # 替换单引号为双引号
                    try:
                        params = json.loads(cleaned_json)
                        if isinstance(params, dict):
                            if 'file_path' in params:
                                file_path = params['file_path']
                            if 'content' in params:
                                content = params['content']
                            if 'binary' in params:
                                binary = params['binary']
                    except:
                        # 如果还是失败，则按文本处理
                        pass
            
            # 1.2 检查是否是简单的换行分隔的文件路径和内容
            if file_path is None and '\n' in file_path_param:
                parts = file_path_param.strip().split('\n', 1)
                if len(parts) == 2:
                    file_path = parts[0].strip()
                    content = parts[1]
            elif file_path is None:
                # 不是JSON格式也没有换行，作为纯文件路径处理
                file_path = file_path_param
        
        # 2. 如果没有从参数中获取到内容，查找其他可能的参数
        # 这通常在直接调用时发生，而不是Agent调用
        import inspect
        frame = inspect.currentframe()
        try:
            # 尝试获取调用者的局部变量
            if frame and frame.f_back:
                if content is None and 'content' in frame.f_back.f_locals:
                    content = frame.f_back.f_locals.get('content')
                # 也尝试从kwargs中获取参数
                kwargs = frame.f_back.f_locals.get('kwargs', {})
                if content is None and 'content' in kwargs:
                    content = kwargs['content']
                # 尝试获取action_input参数(Agent可能使用的格式)
                if content is None and 'action_input' in frame.f_back.f_locals:
                    action_input = frame.f_back.f_locals.get('action_input')
                    if isinstance(action_input, str) and file_path:
                        # 如果有action_input且已有file_path，则action_input可能是content
                        content = action_input
        finally:
            del frame  # 避免循环引用
        
        # 3. 最终检查必要参数
        if file_path is None:
            return "错误: 必须提供file_path参数，指定文件路径"
        
        if content is None:
            return "错误: 必须提供content参数，指定要写入的内容"
        
        # 4. 开始实际的文件操作
        # 统一路径分隔符
        normalized_path = os.path.normpath(file_path)
        
        # 确保目标目录存在
        directory = os.path.dirname(normalized_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        if binary:
            # 对于二进制写入，需要将内容转换为bytes
            try:
                if isinstance(content, str):
                    # 尝试将字符串转换为二进制
                    if content.startswith('0x'):
                        # 16进制字符串
                        binary_content = bytes.fromhex(content[2:])
                    else:
                        # 尝试当作hex字符串处理
                        binary_content = bytes.fromhex(content)
                else:
                    # 如果已经是bytes类型
                    binary_content = content
                    
                with open(normalized_path, 'wb') as file:
                    file.write(binary_content)
            except ValueError:
                return f"错误: 无法将内容转换为二进制格式"
        else:
            # 文本文件写入
            with open(normalized_path, 'w', encoding='utf-8') as file:
                file.write(str(content))  # 确保内容是字符串
                
        return f"文件 '{normalized_path}' 写入成功"
    except PermissionError:
        return f"错误: 没有权限写入文件 '{file_path}'"
    except Exception as e:
        return f"写入文件时发生错误: {str(e)}，参数类型: {type(file_path_param).__name__}"

@tool(description="向文件追加内容，不会覆盖原有内容")
def append_to_file(file_path_param) -> str:
    """向文件追加内容
    
    Args:
        file_path_param: 可以是文件路径字符串，也可以是包含file_path和content的JSON字符串/字典
        
    Returns:
        str: 操作结果描述
    """
    # 初始化参数默认值
    file_path = None
    content = None
    
    try:
        # 1. 尝试解析复杂参数
        if isinstance(file_path_param, dict):
            # 如果是字典类型，直接取出参数
            if 'file_path' in file_path_param:
                file_path = file_path_param['file_path']
            if 'content' in file_path_param:
                content = file_path_param['content']
        elif isinstance(file_path_param, str):
            # 如果是字符串，尝试判断不同格式
            
            # 1.1 尝试解析可能的JSON字符串 - 增强的JSON解析
            json_candidate = file_path_param.strip()
            if (json_candidate.startswith('{') and json_candidate.endswith('}')) or \
               (json_candidate.startswith('[') and json_candidate.endswith(']')):
                try:
                    params = json.loads(json_candidate)
                    if isinstance(params, dict):
                        if 'file_path' in params:
                            file_path = params['file_path']
                        if 'content' in params:
                            content = params['content']
                except (json.JSONDecodeError, ValueError) as e:
                    # 尝试清理JSON字符串再解析一次
                    cleaned_json = json_candidate.replace("'", '"')  # 替换单引号为双引号
                    try:
                        params = json.loads(cleaned_json)
                        if isinstance(params, dict):
                            if 'file_path' in params:
                                file_path = params['file_path']
                            if 'content' in params:
                                content = params['content']
                    except:
                        # 如果还是失败，则按文本处理
                        pass
            
            # 1.2 检查是否是简单的换行分隔的文件路径和内容
            if file_path is None and '\n' in file_path_param:
                parts = file_path_param.strip().split('\n', 1)
                if len(parts) == 2:
                    file_path = parts[0].strip()
                    content = parts[1]
            elif file_path is None:
                # 不是JSON格式也没有换行，作为纯文件路径处理
                file_path = file_path_param
        
        # 2. 如果没有从参数中获取到内容，查找其他可能的参数
        # 这通常在直接调用时发生，而不是Agent调用
        import inspect
        frame = inspect.currentframe()
        try:
            # 尝试获取调用者的局部变量
            if frame and frame.f_back:
                if content is None and 'content' in frame.f_back.f_locals:
                    content = frame.f_back.f_locals.get('content')
                # 也尝试从kwargs中获取参数
                kwargs = frame.f_back.f_locals.get('kwargs', {})
                if content is None and 'content' in kwargs:
                    content = kwargs['content']
                # 尝试获取action_input参数(Agent可能使用的格式)
                if content is None and 'action_input' in frame.f_back.f_locals:
                    action_input = frame.f_back.f_locals.get('action_input')
                    if isinstance(action_input, str) and file_path:
                        # 如果有action_input且已有file_path，则action_input可能是content
                        content = action_input
        finally:
            del frame  # 避免循环引用
        
        # 3. 最终检查必要参数
        if file_path is None:
            return "错误: 必须提供file_path参数，指定文件路径"
        
        if content is None:
            return "错误: 必须提供content参数，指定要追加的内容"
        
        # 打印参数值，便于调试
        print(f"Debug - file_path (append): {file_path}")
        print(f"Debug - content type (append): {type(content)}")
        print(f"Debug - content length (append): {len(str(content))}")
        
        # 4. 开始实际的文件操作
        # 统一路径分隔符
        normalized_path = os.path.normpath(file_path)
        
        # 确保目标目录存在
        directory = os.path.dirname(normalized_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        # 文本文件追加
        with open(normalized_path, 'a', encoding='utf-8') as file:
            file.write(str(content))  # 确保内容是字符串
            
        return f"内容已成功追加到文件 '{normalized_path}'"
    except PermissionError:
        return f"错误: 没有权限追加内容到文件 '{file_path}'"
    except Exception as e:
        return f"追加内容时发生错误: {str(e)}，参数类型: {type(file_path_param).__name__}"

@tool(description="列出指定目录下的文件和子目录")
def list_directory(directory_path: str) -> str:
    """列出指定目录下的文件和子目录
    
    Args:
        directory_path: 要列出内容的目录路径，支持相对路径和绝对路径
        
    Returns:
        str: 目录内容的列表
    """
    try:
        # 统一路径分隔符
        normalized_path = os.path.normpath(directory_path)
        
        if not os.path.exists(normalized_path):
            return f"错误: 目录 '{normalized_path}' 不存在"
        
        if not os.path.isdir(normalized_path):
            return f"错误: '{normalized_path}' 不是一个目录"
        
        # 获取目录内容
        items = os.listdir(normalized_path)
        
        if not items:
            return f"目录 '{normalized_path}' 为空"
        
        # 分类文件和目录
        files = []
        directories = []
        
        for item in items:
            full_path = os.path.join(normalized_path, item)
            if os.path.isdir(full_path):
                directories.append(f"📁 {item}/")
            else:
                file_size = os.path.getsize(full_path)
                files.append(f"📄 {item} ({_format_size(file_size)})")
        
        # 格式化输出结果
        result = f"目录 '{normalized_path}' 的内容:\n\n"
        
        if directories:
            result += "目录:\n"
            result += "\n".join(directories)
            result += "\n\n"
            
        if files:
            result += "文件:\n"
            result += "\n".join(files)
            
        return result
    except PermissionError:
        return f"错误: 没有权限访问目录 '{normalized_path}'"
    except Exception as e:
        return f"列出目录内容时发生错误: {str(e)}"

@tool(description="创建新目录")
def create_directory(directory_path: str) -> str:
    """创建新目录
    
    Args:
        directory_path: 要创建的目录路径，支持相对路径和绝对路径
        
    Returns:
        str: 操作结果描述
    """
    try:
        # 统一路径分隔符
        normalized_path = os.path.normpath(directory_path)
        
        if os.path.exists(normalized_path):
            if os.path.isdir(normalized_path):
                return f"目录 '{normalized_path}' 已经存在"
            else:
                return f"错误: '{normalized_path}' 已存在，但不是目录"
                
        os.makedirs(normalized_path)
        return f"目录 '{normalized_path}' 创建成功"
    except PermissionError:
        return f"错误: 没有权限创建目录 '{normalized_path}'"
    except Exception as e:
        return f"创建目录时发生错误: {str(e)}"

@tool(description="删除指定文件")
def delete_file(file_path: str) -> str:
    """删除指定文件
    
    Args:
        file_path: 要删除的文件路径，支持相对路径和绝对路径
        
    Returns:
        str: 操作结果描述
    """
    try:
        # 统一路径分隔符
        normalized_path = os.path.normpath(file_path)
        
        if not os.path.exists(normalized_path):
            return f"错误: 文件 '{normalized_path}' 不存在"
            
        if os.path.isdir(normalized_path):
            return f"错误: '{normalized_path}' 是一个目录，请使用delete_directory工具"
            
        os.remove(normalized_path)
        return f"文件 '{normalized_path}' 删除成功"
    except PermissionError:
        return f"错误: 没有权限删除文件 '{normalized_path}'"
    except Exception as e:
        return f"删除文件时发生错误: {str(e)}"

@tool(description="删除指定目录及其内容")
def delete_directory(directory_path: str, recursive: bool = True) -> str:
    """删除指定目录及其内容
    
    Args:
        directory_path: 要删除的目录路径，支持相对路径和绝对路径
        recursive: 是否递归删除子目录和文件，默认为True
        
    Returns:
        str: 操作结果描述
    """
    try:
        # 统一路径分隔符
        normalized_path = os.path.normpath(directory_path)
        
        if not os.path.exists(normalized_path):
            return f"错误: 目录 '{normalized_path}' 不存在"
            
        if not os.path.isdir(normalized_path):
            return f"错误: '{normalized_path}' 不是一个目录"
            
        if recursive:
            shutil.rmtree(normalized_path)
            return f"目录 '{normalized_path}' 及其内容已成功删除"
        else:
            try:
                os.rmdir(normalized_path)
                return f"空目录 '{normalized_path}' 已成功删除"
            except OSError:
                return f"错误: 目录 '{normalized_path}' 不为空，无法删除。设置recursive=True可递归删除所有内容"
    except PermissionError:
        return f"错误: 没有权限删除目录 '{normalized_path}'"
    except Exception as e:
        return f"删除目录时发生错误: {str(e)}"

@tool(description="移动或重命名文件")
def move_file(source_path_param) -> str:
    """移动或重命名文件
    
    Args:
        source_path_param: 可以是源文件路径字符串，也可以是包含source_path和destination_path的JSON字符串/字典
        
    Returns:
        str: 操作结果描述
    """
    # 初始化参数默认值
    source_path = None
    destination_path = None
    
    try:
        # 1. 尝试解析复杂参数
        if isinstance(source_path_param, dict):
            # 如果是字典类型，直接取出参数
            if 'source_path' in source_path_param:
                source_path = source_path_param['source_path']
            if 'destination_path' in source_path_param:
                destination_path = source_path_param['destination_path']
        elif isinstance(source_path_param, str):
            # 如果是字符串，尝试判断不同格式
            
            # 1.1 尝试解析可能的JSON字符串 - 增强的JSON解析
            json_candidate = source_path_param.strip()
            if (json_candidate.startswith('{') and json_candidate.endswith('}')) or \
               (json_candidate.startswith('[') and json_candidate.endswith(']')):
                try:
                    params = json.loads(json_candidate)
                    if isinstance(params, dict):
                        if 'source_path' in params:
                            source_path = params['source_path']
                        if 'destination_path' in params:
                            destination_path = params['destination_path']
                except (json.JSONDecodeError, ValueError) as e:
                    # 尝试清理JSON字符串再解析一次
                    cleaned_json = json_candidate.replace("'", '"')  # 替换单引号为双引号
                    try:
                        params = json.loads(cleaned_json)
                        if isinstance(params, dict):
                            if 'source_path' in params:
                                source_path = params['source_path']
                            if 'destination_path' in params:
                                destination_path = params['destination_path']
                    except:
                        # 如果还是失败，则按文本处理
                        pass
            
            # 1.2 检查是否是简单的换行分隔的源路径和目标路径
            if source_path is None and '\n' in source_path_param:
                parts = source_path_param.strip().split('\n', 1)
                if len(parts) == 2:
                    source_path = parts[0].strip()
                    destination_path = parts[1].strip()
            elif source_path is None:
                # 不是JSON格式也没有换行，作为源文件路径处理
                source_path = source_path_param
        
        # 2. 如果没有从参数中获取到目标路径，查找其他可能的参数
        import inspect
        frame = inspect.currentframe()
        try:
            # 尝试获取调用者的局部变量
            if frame and frame.f_back:
                if destination_path is None and 'destination_path' in frame.f_back.f_locals:
                    destination_path = frame.f_back.f_locals.get('destination_path')
                # 也尝试从kwargs中获取参数
                kwargs = frame.f_back.f_locals.get('kwargs', {})
                if destination_path is None and 'destination_path' in kwargs:
                    destination_path = kwargs['destination_path']
        finally:
            del frame  # 避免循环引用
        
        # 3. 最终检查必要参数
        if source_path is None:
            return "错误: 必须提供source_path参数，指定源文件路径"
        
        if destination_path is None:
            return "错误: 必须提供destination_path参数，指定目标文件路径"
        
        # 打印参数值，便于调试
        print(f"Debug - source_path: {source_path}")
        print(f"Debug - destination_path: {destination_path}")
        
        # 4. 开始实际的文件操作
        # 统一路径分隔符
        normalized_source = os.path.normpath(source_path)
        normalized_destination = os.path.normpath(destination_path)
        
        if not os.path.exists(normalized_source):
            return f"错误: 源文件 '{normalized_source}' 不存在"
            
        # 确保目标目录存在
        destination_dir = os.path.dirname(normalized_destination)
        if destination_dir and not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
            
        shutil.move(normalized_source, normalized_destination)
        
        if os.path.dirname(normalized_source) == os.path.dirname(normalized_destination):
            return f"文件 '{os.path.basename(normalized_source)}' 已重命名为 '{os.path.basename(normalized_destination)}'"
        else:
            return f"文件已从 '{normalized_source}' 移动到 '{normalized_destination}'"
    except PermissionError:
        return f"错误: 没有权限移动文件"
    except Exception as e:
        return f"移动文件时发生错误: {str(e)}，参数类型: {type(source_path_param).__name__}"

@tool(description="复制文件")
def copy_file(source_path_param) -> str:
    """复制文件
    
    Args:
        source_path_param: 可以是源文件路径字符串，也可以是包含source_path和destination_path的JSON字符串/字典
        
    Returns:
        str: 操作结果描述
    """
    # 初始化参数默认值
    source_path = None
    destination_path = None
    
    try:
        # 1. 尝试解析复杂参数
        if isinstance(source_path_param, dict):
            # 如果是字典类型，直接取出参数
            if 'source_path' in source_path_param:
                source_path = source_path_param['source_path']
            if 'destination_path' in source_path_param:
                destination_path = source_path_param['destination_path']
        elif isinstance(source_path_param, str):
            # 如果是字符串，尝试判断不同格式
            
            # 1.1 尝试解析可能的JSON字符串 - 增强的JSON解析
            json_candidate = source_path_param.strip()
            if (json_candidate.startswith('{') and json_candidate.endswith('}')) or \
               (json_candidate.startswith('[') and json_candidate.endswith(']')):
                try:
                    params = json.loads(json_candidate)
                    if isinstance(params, dict):
                        if 'source_path' in params:
                            source_path = params['source_path']
                        if 'destination_path' in params:
                            destination_path = params['destination_path']
                except (json.JSONDecodeError, ValueError) as e:
                    # 尝试清理JSON字符串再解析一次
                    cleaned_json = json_candidate.replace("'", '"')  # 替换单引号为双引号
                    try:
                        params = json.loads(cleaned_json)
                        if isinstance(params, dict):
                            if 'source_path' in params:
                                source_path = params['source_path']
                            if 'destination_path' in params:
                                destination_path = params['destination_path']
                    except:
                        # 如果还是失败，则按文本处理
                        pass
            
            # 1.2 检查是否是简单的换行分隔的源路径和目标路径
            if source_path is None and '\n' in source_path_param:
                parts = source_path_param.strip().split('\n', 1)
                if len(parts) == 2:
                    source_path = parts[0].strip()
                    destination_path = parts[1].strip()
            elif source_path is None:
                # 不是JSON格式也没有换行，作为源文件路径处理
                source_path = source_path_param
        
        # 2. 如果没有从参数中获取到目标路径，查找其他可能的参数
        import inspect
        frame = inspect.currentframe()
        try:
            # 尝试获取调用者的局部变量
            if frame and frame.f_back:
                if destination_path is None and 'destination_path' in frame.f_back.f_locals:
                    destination_path = frame.f_back.f_locals.get('destination_path')
                # 也尝试从kwargs中获取参数
                kwargs = frame.f_back.f_locals.get('kwargs', {})
                if destination_path is None and 'destination_path' in kwargs:
                    destination_path = kwargs['destination_path']
        finally:
            del frame  # 避免循环引用
        
        # 3. 最终检查必要参数
        if source_path is None:
            return "错误: 必须提供source_path参数，指定源文件路径"
        
        if destination_path is None:
            return "错误: 必须提供destination_path参数，指定目标文件路径"
        
        # 打印参数值，便于调试
        print(f"Debug - source_path (copy): {source_path}")
        print(f"Debug - destination_path (copy): {destination_path}")
        
        # 4. 开始实际的文件操作
        # 统一路径分隔符
        normalized_source = os.path.normpath(source_path)
        normalized_destination = os.path.normpath(destination_path)
        
        if not os.path.exists(normalized_source):
            return f"错误: 源文件 '{normalized_source}' 不存在"
            
        if os.path.isdir(normalized_source):
            return f"错误: '{normalized_source}' 是一个目录，请使用适当的目录复制工具"
            
        # 确保目标目录存在
        destination_dir = os.path.dirname(normalized_destination)
        if destination_dir and not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
            
        shutil.copy2(normalized_source, normalized_destination)
        return f"文件已从 '{normalized_source}' 复制到 '{normalized_destination}'"
    except PermissionError:
        return f"错误: 没有权限复制文件"
    except Exception as e:
        return f"复制文件时发生错误: {str(e)}，参数类型: {type(source_path_param).__name__}"

@tool(description="获取文件的详细信息（大小、修改时间等）")
def get_file_info(file_path: str) -> str:
    """获取文件的详细信息
    
    Args:
        file_path: 文件路径，支持相对路径和绝对路径
        
    Returns:
        str: 文件信息的字符串表示
    """
    try:
        # 统一路径分隔符
        normalized_path = os.path.normpath(file_path)
        
        if not os.path.exists(normalized_path):
            return f"错误: 文件 '{normalized_path}' 不存在"
            
        # 获取文件基本信息
        file_stats = os.stat(normalized_path)
        
        # 获取文件类型
        file_type = "目录" if os.path.isdir(normalized_path) else "文件"
        
        # 获取文件大小
        size = file_stats.st_size
        formatted_size = _format_size(size)
        
        # 获取时间信息
        created_time = datetime.datetime.fromtimestamp(file_stats.st_ctime)
        modified_time = datetime.datetime.fromtimestamp(file_stats.st_mtime)
        accessed_time = datetime.datetime.fromtimestamp(file_stats.st_atime)
        
        # 格式化时间
        created_str = created_time.strftime("%Y-%m-%d %H:%M:%S")
        modified_str = modified_time.strftime("%Y-%m-%d %H:%M:%S")
        accessed_str = accessed_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建信息字符串
        info = f"'{normalized_path}' 的文件信息:\n\n"
        info += f"类型: {file_type}\n"
        info += f"大小: {formatted_size}\n"
        info += f"创建时间: {created_str}\n"
        info += f"修改时间: {modified_str}\n"
        info += f"访问时间: {accessed_str}\n"
        
        # 如果是文件，尝试获取文件扩展名
        if not os.path.isdir(normalized_path):
            _, extension = os.path.splitext(normalized_path)
            if extension:
                info += f"文件扩展名: {extension}\n"
                
        return info
    except PermissionError:
        return f"错误: 没有权限访问文件 '{normalized_path}'"
    except Exception as e:
        return f"获取文件信息时发生错误: {str(e)}"

def _format_size(size_in_bytes: int) -> str:
    """将字节大小格式化为可读的字符串
    
    Args:
        size_in_bytes: 文件大小，以字节为单位
        
    Returns:
        str: 格式化后的大小字符串
    """
    # 定义单位
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    
    # 转换为合适的单位
    unit_index = 0
    size = float(size_in_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
        
    # 格式化结果
    if unit_index == 0:
        # 对于字节，不显示小数点
        return f"{int(size)} {units[unit_index]}"
    else:
        # 对于其他单位，显示两位小数
        return f"{size:.2f} {units[unit_index]}" 