"""
本地知识库工具模块 - 提供从本地知识库检索信息的功能
"""

from langchain.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
import numpy as np
import json
import uuid
import os
from typing import List, Optional, Dict, Any, Tuple
from collections import Counter

# 初始化嵌入模型
embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-zh-v1.5"  # 使用中文嵌入模型
)

# 本地知识库目录
persist_dir = "chroma_data_dir"
metadata_dir = "knowledge_metadata"

# 确保元数据目录存在
os.makedirs(metadata_dir, exist_ok=True)

# 加载本地知识库
try:
    vector_store = Chroma(
        persist_directory=persist_dir, 
        embedding_function=embedding_model
    )
    print("本地知识库加载成功")
except Exception as e:
    print(f"本地知识库加载失败: {str(e)}")
    vector_store = None

def generate_summary(text: str, max_length: int = 50) -> str:
    """
    使用LLM生成文本摘要
    
    Args:
        text: 原文本
        max_length: 摘要最大长度
        
    Returns:
        str: 摘要文本
    """
    try:
        # 导入LLM相关模块
        from langchain.chains.summarize import load_summarize_chain
        from langchain_core.documents import Document
        from langchain.prompts import PromptTemplate
        from ..models import initialize_model
        
        # 如果文本很短，直接返回
        if len(text) <= max_length:
            return text
            
        # 初始化一个本地LLM用于生成摘要
        llm = initialize_model()
        
        # 创建摘要模板
        prompt_template = """请为以下内容生成一个简洁的摘要，不超过{max_length}个字符：

{text}

摘要:"""
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["text", "max_length"]
        )
        
        # 创建文档对象
        doc = Document(page_content=text)
        
        # 使用LLM直接生成摘要
        chain = load_summarize_chain(
            llm,
            chain_type="stuff",
            prompt=prompt
        )
        
        # 尝试替代方案
        try:
            # 方案1：使用字典传递所有参数
            input_dict = {"input_documents": [doc], "max_length": str(max_length)}
            summary = chain.run(input_dict)
        except Exception as e:
            print(f"方案1失败: {str(e)}")
            try:
                # 方案2：先在文本中替换max_length参数
                # 创建一个新的仅包含text变量的提示模板
                simple_prompt = PromptTemplate(
                    template=f"请为以下内容生成一个简洁的摘要，不超过{max_length}个字符：\n\n{{text}}\n\n摘要:",
                    input_variables=["text"]
                )
                
                # 重新创建摘要链
                simple_chain = load_summarize_chain(
                    llm,
                    chain_type="stuff",
                    prompt=simple_prompt
                )
                
                # 只传递文档作为参数
                summary = simple_chain.run([doc])
            except Exception as e2:
                print(f"方案2失败: {str(e2)}")
                # 方案3：直接使用LLM
                summary = llm.invoke(f"请为以下内容生成一个简洁的摘要，不超过{max_length}个字符：\n\n{text}\n\n摘要:").content
                
        # 确保摘要不超过最大长度
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
            
        return summary.strip()
        
    except Exception as e:
        print(f"LLM摘要生成失败: {str(e)}，将使用简单截取方法")
        # 如果LLM摘要失败，回退到简单的截取方式
        if len(text) <= max_length:
            return text
        
        # 尝试在句子结束处截断
        truncated = text[:max_length]
        last_period = max(truncated.rfind('。'), truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
        
        if last_period > max_length / 2:  # 确保至少有一半长度
            return truncated[:last_period+1]
        return truncated + "..."

def save_metadata(doc_id: str, metadata: Dict[str, Any]) -> None:
    """保存文档元数据到文件"""
    filename = os.path.join(metadata_dir, f"{doc_id}.json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

def load_metadata(doc_id: str) -> Dict[str, Any]:
    """加载文档元数据"""
    filename = os.path.join(metadata_dir, f"{doc_id}.json")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def delete_metadata(doc_id: str) -> None:
    """删除文档元数据"""
    filename = os.path.join(metadata_dir, f"{doc_id}.json")
    if os.path.exists(filename):
        os.remove(filename)

@tool(description="从本地知识库中检索信息")
def retrieve_from_knowledge_base(query: str, top_k: int = 3, score_threshold: float = 0.3) -> str:
    """
    从本地知识库中检索与查询相关的信息，并根据相似度得分筛选结果
    
    Args:
        query: 用户查询字符串
        top_k: 返回的最相关文档数量，默认为3
        score_threshold: 相似度分数阈值，默认为0.3，分数低于此值的结果将被过滤
        
    Returns:
        str: 检索到的信息内容
    """
    if vector_store is None:
        return "错误：本地知识库未成功加载"
    
    try:
        # 使用带分数的相似性搜索
        docs_with_scores = vector_store.similarity_search_with_score(query, k=top_k*2)  # 扩大初始检索范围
        
        if not docs_with_scores:
            return "在知识库中未找到相关信息"
        
        # 筛选得分高于阈值的文档
        filtered_docs = []
        
        for doc, score in docs_with_scores:
            # 有些向量库的分数是距离（越小越好），有些是相似度（越大越好）
            # 这里我们假设分数是相似度，Chroma通常返回欧几里得距离，需要转换
            # 将欧几里得距离转换为相似度 (1 / (1 + 距离))
            similarity = 1 / (1 + score)
            
            if similarity > score_threshold:
                filtered_docs.append((doc, similarity))
        
        # 按相似度排序（从高到低）
        filtered_docs.sort(key=lambda x: x[1], reverse=True)
        
        # 限制返回数量
        filtered_docs = filtered_docs[:top_k]
        
        if not filtered_docs:
            return "没有找到足够相关的信息（相似度低于阈值）"
        
        # 准备检索结果
        results = []
        for i, (doc, similarity) in enumerate(filtered_docs):
            # 将相似度转换为百分比并保留两位小数
            similarity_percentage = round(similarity * 100, 2)
            
            # 获取元数据
            doc_id = doc.metadata.get('doc_id', '')
            summary = ""
            if doc_id:
                meta = load_metadata(doc_id)
                summary = meta.get('summary', '')
            
            # 构建结果
            result = f"[{i+1}] 相关度: {similarity_percentage}%"
            if doc_id:
                result += f" [ID: {doc_id}]"
            if summary:
                result += f"\n摘要: {summary}"
            result += f"\n{doc.page_content}"
            
            results.append(result)
        
        content = "\n\n".join(results)
        return f"从知识库中找到以下相关信息：\n\n{content}"
    
    except Exception as e:
        return f"检索过程中发生错误: {str(e)}"

@tool(description="获取知识库状态信息和内容概览")
def get_knowledge_base_info() -> str:
    """
    获取本地知识库的状态信息和内容概览
    
    Returns:
        str: 知识库状态信息和内容概览
    """
    if vector_store is None:
        return "本地知识库未加载"
    
    try:
        doc_count = vector_store._collection.count()
        
        # 获取元数据文件数量
        metadata_files = [f for f in os.listdir(metadata_dir) if f.endswith('.json')]
        
        result = f"本地知识库已加载，共包含 {doc_count} 个文档向量\n"
        result += f"元数据目录中有 {len(metadata_files)} 个文档的元数据\n\n"
        
        # 如果没有文档，返回提示信息
        if not metadata_files:
            return result + "知识库中暂无内容，请使用add_website_to_knowledge_base工具添加网页内容"
        
        # 收集所有元数据信息
        all_metadata = []
        sources = Counter()
        titles = []
        
        # 加载所有元数据
        for filename in metadata_files:
            doc_id = filename.replace('.json', '')
            metadata = load_metadata(doc_id)
            if metadata:
                all_metadata.append(metadata)
                sources[metadata.get('source', '未知来源')] += 1
                if 'title' in metadata and metadata['title']:
                    titles.append(metadata['title'])
        
        # 添加内容概览
        result += "知识库内容概览：\n"
        
        # 添加来源统计
        result += "1. 来源分布：\n"
        for source, count in sources.most_common():
            result += f"   - {source}: {count}个文档 ({round(count/len(metadata_files)*100, 1)}%)\n"
        
        # 添加部分摘要展示
        result += "\n2. 内容摘要(随机10个示例)：\n"
        import random
        sample_size = min(10, len(all_metadata))
        sampled_metadata = random.sample(all_metadata, sample_size)
        
        for i, metadata in enumerate(sampled_metadata):
            summary = metadata.get('summary', '无摘要')
            source = metadata.get('source', '未知来源')
            result += f"   [{i+1}] 来源: {source}\n   摘要: {summary}\n\n"
        
        # 如果有标题，展示一些标题
        if titles:
            result += "3. 部分标题：\n"
            sample_titles = random.sample(titles, min(5, len(titles)))
            for i, title in enumerate(sample_titles):
                result += f"   - {title}\n"
        
        # 添加使用建议
        result += "\n要查询知识库内容，请使用retrieve_from_knowledge_base工具，并提供关键词或问题。"
        
        return result
    
    except Exception as e:
        return f"获取知识库信息时发生错误: {str(e)}"

@tool(description="从网页链接添加内容到知识库")
def add_website_to_knowledge_base(urls: str, chunk_size: int = 3000, chunk_overlap: int = 300) -> str:
    """
    从网页链接加载内容并添加到知识库
    
    Args:
        urls: 网页链接，多个链接用逗号分隔
        chunk_size: 分割文本的大小，默认1000个字符
        chunk_overlap: 分割文本的重叠大小，默认200个字符
        
    Returns:
        str: 添加结果信息
    """
    global vector_store
    
    # 检查知识库是否已加载
    if vector_store is None:
        # 初始化一个新的向量存储
        try:
            vector_store = Chroma(
                persist_directory=persist_dir, 
                embedding_function=embedding_model
            )
        except Exception as e:
            return f"初始化知识库失败: {str(e)}"
    
    try:
        # 处理可能的JSON格式输入
        if isinstance(urls, dict) and "urls" in urls:
            # 如果是字典格式 {"urls": "https://example.com"}
            urls = urls["urls"]
        elif isinstance(urls, str) and urls.startswith("{") and "urls" in urls:
            # 如果是JSON字符串 '{"urls": "https://example.com"}'
            try:
                import json
                data = json.loads(urls)
                if "urls" in data:
                    urls = data["urls"]
            except:
                pass  # 如果解析失败，保持原样
                
        # 确保urls是字符串类型
        if not isinstance(urls, str):
            # 如果是列表或其他类型，尝试转换为逗号分隔的字符串
            if isinstance(urls, (list, tuple)):
                urls = ",".join(str(u) for u in urls)
            else:
                urls = str(urls)
        
        # 解析URL列表
        url_list = []
        for url in urls.split(','):
            url = url.strip()
            # 忽略空URL
            if not url:
                continue
            # 确保URL有效
            if not (url.startswith('http://') or url.startswith('https://')):
                url = 'https://' + url
            url_list.append(url)
        
        if not url_list:
            return "未提供有效的URL，请确保提供了正确的网址"
        
        # 加载网页数据
        print(f"尝试加载以下URL: {url_list}")
        loader = WebBaseLoader(
            web_paths=url_list,
            encoding="utf-8",  # 明确指定编码，确保中文正确处理
        )
        
        # 执行文档加载
        docs = loader.load()
        
        if not docs:
            return "未能从提供的URL加载任何内容"
        
        # 初始化文本分割器
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        
        # 分割文档
        split_docs = splitter.split_documents(docs)
        
        if not split_docs:
            return "文档分割失败，未生成任何文本块"
        
        # 为每个文档添加唯一ID和摘要
        enhanced_docs = []
        added_ids = []
        
        for doc in split_docs:
            # 生成唯一ID
            doc_id = str(uuid.uuid4())
            added_ids.append(doc_id)
            
            # 生成摘要
            summary = generate_summary(doc.page_content)
            
            # 构建元数据
            metadata = doc.metadata.copy()
            metadata['doc_id'] = doc_id
            
            # 保存元数据和摘要到外部文件
            save_metadata(doc_id, {
                'summary': summary,
                'source': metadata.get('source', '未知来源'),
                'title': metadata.get('title', ''),
                'created_at': metadata.get('created_at', ''),
            })
            
            # 创建新文档
            enhanced_doc = Document(
                page_content=doc.page_content,
                metadata=metadata
            )
            
            enhanced_docs.append(enhanced_doc)
        
        # 将分割后的文档添加到向量存储中
        vector_store.add_documents(enhanced_docs)
        
        # 持久化存储
        if hasattr(vector_store, 'persist'):
            vector_store.persist()
        
        # 统计各URL的文档数量
        source_counts = {}
        for doc in enhanced_docs:
            source = doc.metadata.get('source', '未知来源')
            if source in source_counts:
                source_counts[source] += 1
            else:
                source_counts[source] = 1
        
        # 生成结果报告
        result = f"成功添加 {len(enhanced_docs)} 个文本块到知识库，并生成了摘要\n\n"
        result += "各来源文档的分块数量:\n"
        for source, count in source_counts.items():
            result += f"- {source}: {count}个分块\n"
        
        try:
            doc_count = vector_store._collection.count()
            result += f"\n知识库现在共包含 {doc_count} 个文档向量"
        except:
            pass
        
        return result
        
    except Exception as e:
        return f"添加网页内容到知识库时发生错误: {str(e)}"

@tool(description="查看文档的详细元数据")
def get_document_metadata(doc_id: str) -> str:
    """
    获取指定文档的详细元数据信息
    
    Args:
        doc_id: 文档ID
        
    Returns:
        str: 文档元数据信息
    """
    if not doc_id:
        return "错误：必须提供文档ID"
    
    try:
        # 加载元数据
        metadata = load_metadata(doc_id)
        
        if not metadata:
            return f"未找到ID为 {doc_id} 的文档元数据"
        
        # 格式化输出
        result = f"文档 {doc_id} 的元数据信息:\n"
        for key, value in metadata.items():
            result += f"- {key}: {value}\n"
            
        return result
    
    except Exception as e:
        return f"获取元数据时发生错误: {str(e)}"