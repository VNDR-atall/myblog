## Target：实现一个

```bash
def load_document(file_path):
    ...
```

应能支持：

- PDF
- .txt
- .doc
等等格式的加载。

---

## 一、准备data

获取 _Attention Is All You Need_ 的PDF文档，放入data中。
```bash
(rag-venv) (base) vd@vndrdeMacBook rag % ls data

Attention Is All You Need.pdf
```

---

## 二、编写模块

### 1. 编写文档加载器 `app/services/loader.py`

```python
# app/services/loader.py
import os
from typing import List, Optional

# PDF 支持
import PyPDF2
import pdfplumber

# Word 支持
from docx import Document

# 文本文件支持
import chardet


class DocumentLoader:
    """统一文档加载器，支持 .txt, .pdf, .docx 格式"""

    @staticmethod
    def load_txt(file_path: str) -> str:
        """加载文本文件，自动检测编码"""
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
        return raw_data.decode(encoding)

    @staticmethod
    def load_pdf(file_path: str, use_pdfplumber: bool = True) -> str:
        """加载 PDF 文件，优先使用 pdfplumber（表格/布局友好）"""
        text = ""
        if use_pdfplumber:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        else:
            # 备用方案：PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        return text.strip()

    @staticmethod
    def load_docx(file_path: str) -> str:
        """加载 Word 文档"""
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)

    def load_file(self, file_path: str) -> Optional[str]:
        """根据文件扩展名自动选择加载器"""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.txt':
            return self.load_txt(file_path)
        elif ext == '.pdf':
            return self.load_pdf(file_path)
        elif ext == '.docx':
            return self.load_docx(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {ext}")

    def load_directory(self, dir_path: str, recursive: bool = True) -> List[dict]:
        """
        加载目录下所有支持的文件，返回列表，每个元素为 {"path": str, "content": str}
        """
        results = []
        supported_ext = ('.txt', '.pdf', '.docx')
        if not os.path.isdir(dir_path):
            raise NotADirectoryError(f"目录不存在: {dir_path}")

        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.lower().endswith(supported_ext):
                    full_path = os.path.join(root, file)
                    try:
                        content = self.load_file(full_path)
                        results.append({
                            "path": full_path,
                            "content": content
                        })
                        print(f"✓ 已加载: {full_path} (字符数: {len(content)})")
                    except Exception as e:
                        print(f"✗ 加载失败: {full_path} - {e}")
            if not recursive:
                break
        return results
```

### 2. 编写数据摄取脚本 `scripts/ingest.py

```python
# scripts/ingest.py
import sys
import os
import json

# 将项目根目录加入 Python 路径，以便导入 app 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.loader import DocumentLoader


def main():
    data_dir = "data"          # 项目中的 data 目录
    output_file = "loaded_docs.json"   # 临时保存加载结果

    loader = DocumentLoader()
    print(f"开始加载目录: {data_dir}")
    documents = loader.load_directory(data_dir, recursive=True)

    if not documents:
        print("未找到任何支持的文档（.txt, .pdf, .docx）")
        return

    # 将加载结果保存为 JSON，便于后续分块处理
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 文档加载完成！共加载 {len(documents)} 个文件，结果已保存至 {output_file}")


if __name__ == "__main__":
    main()
```

---

## 三、试运行

```bash
python scripts/ingest.py
```

结果输出：
```bash
(rag-venv) (base) vd@vndrdeMacBook rag % python scripts/ingest.py

开始加载目录: data

✓ 已加载: data/Attention Is All You Need.pdf (字符数: 35525)

✅ 文档加载完成！共加载 1 个文件，结果已保存至 loaded_docs.json
```

---

## 四、代码优化

### 问题描述

#### 1. JSON存储格式问题（没有metadata）
目前：
```json
{
  "path": "...",
  "content": "..."
}
```

问题：

- 无法显示“引用来源”
- 无法定位问题chunk
- 无法做多文档区分

期望：
```json
{
  "path": "...",
  "content": "..."
  "source": "文件名",
  "page": 页码,
  "chunk_id": ?
}
```

修改 `app/services/loader.py`（记得注释也要修改）：
```python
results.append({
    "path": full_path,
    "content": content,
    "metadata": {
        "source": os.path.basename(full_path)
    }
})
```

#### 2. PDF没有“分页信息”（chunk无法知道来自哪一页）
目前：
```python
text += page_text
```

问题：

- chunk无法知道来自哪一页

期望：
```python
documents = []

for i, page in enumerate(pdf.pages):
    page_text = page.extract_text()
    if page_text:
        documents.append({
            "content": page_text,
            "metadata": {
                "page": i + 1,
                "source": file_path
            }
        })
```

#### 3. JSON结构未来不可拓展
目前：
```json
[
  {"path": "...", "content": "..."}
]
```

期望：
```json
[
  {
    "content": "...",
    "metadata": {
      "source": "...",
      "page": ...
    }
  }
]
```

#### 4. 输出内容问题
存在文本粘连（缺少空格）和提取顺序问题，这会影响分块质量和后续检索效果。我们需要优化 PDF 文本提取的质量。

- **空格丢失**：PDF 中的字符可能通过绝对定位绘制，没有显式空格字符，导致 `extract_text()` 直接拼接字符。
    
- **提取顺序**：双栏布局可能导致文本按视觉位置交错。
    
- **噪声内容**：版权声明出现在正文之前。


优化方案
1. 使用 `layout=True` 参数保留布局和空格。
    
2. 调整 `x_tolerance` 和 `y_tolerance` 合并相近字符。
    
3. 添加简单的后处理：在英文小写字母后跟大写字母或数字的位置插入空格（启发式修复）。
    
4. 保留每页完整文本，不删除任何内容（用户可自行过滤）。


### 完整优化代码

修改后的完整 `app/services/loader.py` :
```python
# app/services/loader.py
import os
import re
from typing import List, Dict, Optional

import PyPDF2
import pdfplumber
from docx import Document
import chardet


class DocumentLoader:
    """统一文档加载器，支持 .txt, .pdf, .docx，返回结构化数据（含元数据）"""

    @staticmethod
    def _fix_missing_spaces(text: str) -> str:
        """
        简单修复缺少空格的情况：在小写字母后跟大写字母或数字的位置插入空格。
        例如 "HelloWorld" -> "Hello World"
        """
        # 匹配小写字母 + 大写字母 或 小写字母 + 数字
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        text = re.sub(r'([a-z])(\d)', r'\1 \2', text)
        # 匹配字母 + 标点符号 + 字母（如 "end,start" -> "end, start"）
        text = re.sub(r'([a-zA-Z])([,.!?;:])([a-zA-Z])', r'\1\2 \3', text)
        return text

    @staticmethod
    def load_txt(file_path: str) -> List[Dict]:
        """加载文本文件，自动检测编码"""
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
        text = raw_data.decode(encoding)

        return [{
            "content": text,
            "metadata": {
                "source": os.path.basename(file_path),
                "file_path": file_path,
                "page": None
            }
        }]

    @staticmethod
    def load_pdf(file_path: str, use_pdfplumber: bool = True) -> List[Dict]:
        """
        加载 PDF 文件，按页拆分，优化文本提取（保留空格，修复粘连）。
        """
        pages = []
        if use_pdfplumber:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    # 使用 layout=True 保留空格和相对位置
                    # 调整 x_tolerance, y_tolerance 合并相近字符
                    page_text = page.extract_text(
                        layout=True,
                        x_tolerance=2,   # 水平方向合并距离
                        y_tolerance=2    # 垂直方向合并距离
                    )
                    if page_text and page_text.strip():
                        # 修复丢失的空格
                        fixed_text = DocumentLoader._fix_missing_spaces(page_text)
                        pages.append({
                            "content": fixed_text.strip(),
                            "metadata": {
                                "source": os.path.basename(file_path),
                                "file_path": file_path,
                                "page": i + 1
                            }
                        })
                    else:
                        # 降级：尝试无布局提取
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            fixed_text = DocumentLoader._fix_missing_spaces(page_text)
                            pages.append({
                                "content": fixed_text.strip(),
                                "metadata": {
                                    "source": os.path.basename(file_path),
                                    "file_path": file_path,
                                    "page": i + 1
                                }
                            })
        else:
            # 备用方案：PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        fixed_text = DocumentLoader._fix_missing_spaces(page_text)
                        pages.append({
                            "content": fixed_text.strip(),
                            "metadata": {
                                "source": os.path.basename(file_path),
                                "file_path": file_path,
                                "page": i + 1
                            }
                        })
        return pages

    @staticmethod
    def load_docx(file_path: str) -> List[Dict]:
        """加载 Word 文档，整体作为一个单元"""
        doc = Document(file_path)
        full_text = "\n".join([para.text for para in doc.paragraphs])

        return [{
            "content": full_text,
            "metadata": {
                "source": os.path.basename(file_path),
                "file_path": file_path,
                "page": None
            }
        }]

    def load_file(self, file_path: str) -> Optional[List[Dict]]:
        """根据扩展名调用对应加载器"""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.txt':
            return self.load_txt(file_path)
        elif ext == '.pdf':
            return self.load_pdf(file_path)
        elif ext == '.docx':
            return self.load_docx(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {ext}")

    def load_directory(self, dir_path: str, recursive: bool = True) -> List[Dict]:
        """递归加载目录下所有支持的文件"""
        results = []
        supported_ext = ('.txt', '.pdf', '.docx')
        if not os.path.isdir(dir_path):
            raise NotADirectoryError(f"目录不存在: {dir_path}")

        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.lower().endswith(supported_ext):
                    full_path = os.path.join(root, file)
                    try:
                        items = self.load_file(full_path)
                        if items:
                            results.extend(items)
                            print(f"✓ 已加载: {full_path} (共 {len(items)} 个页面/单元)")
                    except Exception as e:
                        print(f"✗ 加载失败: {full_path} - {e}")
            if not recursive:
                break
        return results
```

### 优化后的输出
```bash
(rag-venv) (base) vd@vndrdeMacBook rag % python scripts/ingest.py
开始加载目录: data
✓ 已加载: data/Attention Is All You Need.pdf (共 15 个页面/单元)

✅ 文档加载完成！共加载 15 个文档单元，已保存至 loaded_docs.json

示例单元元数据:
{
  "source": "Attention Is All You Need.pdf",
  "file_path": "data/Attention Is All You Need.pdf",
  "page": 1
}

内容预览: Provided proper attribution is provided, Google hereby grants permission to
                 reproduce the tables and figures in this paper solely for use in journalistic or
                           ...
```

---

## 五、优化说明

优化后的输出显示空格已正常（如 "Provided proper attribution" 而非 "Providedproperattribution"），PDF 文本提取质量显著提升。以下是最初版与优化版的详细对比说明：

### 📊 `loader.py` 优化对比说明

| 维度           | 最初版                               | 优化版                                                                                   | 改进效果                                |
| ------------ | --------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------- |
| **返回数据结构**   | `[{"path": str, "content": str}]` | `[{"content": str, "metadata": {"source": str, "file_path": str, "page": int/None}}]` | 支持多文档区分、页码追溯、扩展元数据                  |
| **PDF 分页处理** | 整篇 PDF 拼接成一个字符串                   | 每页独立成一个单元，`page` 记录页码                                                                 | 可精确定位 chunk 来源页码                    |
| **文本提取参数**   | `page.extract_text()` 无参数         | `page.extract_text(layout=True, x_tolerance=2, y_tolerance=2)`                        | 保留空格，避免字符粘连                         |
| **空格修复**     | 无                                 | `_fix_missing_spaces()` 正则修复（小写+大写、小写+数字、标点后接字母）                                      | 解决 "HelloWorld" → "Hello World" 的问题 |
| **降级机制**     | 无                                 | 若 `layout=True` 提取失败，自动回退到普通 `extract_text()`                                         | 提高兼容性，避免空内容                         |
| **元数据扩展性**   | 仅保存 `path`                        | 预留 `metadata` 字典，可随时增加 `author`、`title`、`chapter` 等字段                                 | 未来无需修改调用方代码                         |
| **输出信息**     | 打印文件加载成功                          | 同时打印单元数量（如“共 15 个页面/单元”）                                                              | 更清晰的进度反馈                            |

### 核心改进代码片段

**最初版 PDF 加载**：
```python
with pdfplumber.open(file_path) as pdf:
    for page in pdf.pages:
        page_text = page.extract_text()
        text += page_text + "\n"
return text
```

**优化版 PDF 加载**：
```python
with pdfplumber.open(file_path) as pdf:
    for i, page in enumerate(pdf.pages):
        page_text = page.extract_text(layout=True, x_tolerance=2, y_tolerance=2)
        fixed_text = self._fix_missing_spaces(page_text)
        pages.append({
            "content": fixed_text.strip(),
            "metadata": {"source": basename, "file_path": file_path, "page": i+1}
        })
```

