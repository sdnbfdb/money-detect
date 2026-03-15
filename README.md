# 票务资金展示系统

一个基于 Flask 和 D3.js 的金融数据分析与可视化平台，用于银行交易数据分析和洗钱风险监测。

## 项目简介

本项目是一个专业的金融数据分析系统，提供以下核心功能：

- **交易数据可视化** - 交互式表格和力导向图展示
- **交易关系图谱** - 展示账户间资金往来关系
- **发票图谱分析** - 分析销方和购方的发票往来
- **预警管理系统** - 添加/删除预警，实时高亮显示
- **数据筛选功能** - 多维度筛选交易数据
- **统计分析** - 交易金额、频次等统计分析
- **数据导入导出** - 支持Excel文件导入导出

## 技术栈

### 后端
- **Python 3.x**
- **Flask 2.3.3** - Web框架
- **Flask-CORS** - 跨域支持
- **Pandas** - 数据处理
- **NumPy** - 数值计算
- **OpenPyXL** - Excel文件读写

### 前端
- **HTML5 + CSS3**
- **JavaScript (ES6+)**
- **D3.js v7** - 数据可视化

## 项目结构

```
票务资金展示/
├── hou/                          # 后端服务目录
│   ├── app.py                    # Flask主应用服务器
│   ├── simple.py                 # 图谱简化算法
│   ├── analyze_money_laundering.py  # 风险分析脚本
│   ├── change.py                 # 数据变更处理
│   ├── index.py                  # 数据管理类
│   ├── note.py                   # 笔记记录功能
│   ├── read_excel.py             # Excel数据读取工具
│   ├── warning.py                # 预警处理模块
│   ├── big.py                    # 大数据处理
│   └── requirements.txt          # Python依赖包列表
├── qian/                         # 前端界面目录
│   ├── index.html                # 主数据展示页面
│   ├── filter.html               # 数据筛选和图谱页面
│   ├── detal.html                # 详情页面
│   └── d3.v7.min.js              # D3.js库文件
├── start.bat                     # Windows启动脚本
├── .gitignore                    # Git忽略配置
└── README.md                     # 项目说明文档
```

## 安装与运行

### 环境要求
- Python 3.8+
- pip 包管理器

### 1. 克隆项目

```bash
git clone https://github.com/sdnbfdb/-.git
cd 票务资金展示
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. 安装依赖

```bash
cd hou
pip install -r requirements.txt
```

### 4. 运行项目

**方式一：使用启动脚本（Windows）**
```bash
# 在项目根目录下
start.bat
```

**方式二：手动启动**
```bash
cd hou
python app.py
```

### 5. 访问应用

打开浏览器访问：http://localhost:5000

## 主要功能说明

### 1. 数据筛选页面 (filter.html)

提供多维度数据筛选功能：
- **户名搜索** - 按交易方户名或对手户名筛选
- **卡号搜索** - 按交易卡号或对手卡号筛选
- **借贷标志** - 筛选进账或出账交易
- **金额范围** - 按交易金额范围筛选
- **时间范围** - 按交易时间范围筛选

**功能按钮：**
- 应用筛选 - 执行筛选操作
- 清除筛选 - 重置筛选条件
- 下载Excel - 导出筛选结果
- 查看往来图谱 - 可视化展示交易关系
- 发票结点交易频率 - 分析发票交易频次

### 2. 主展示页面 (index.html)

- 交易数据表格展示
- 分页浏览功能
- 数据排序功能

### 3. 详情页面 (detal.html)

- 单笔交易详细信息
- 关联数据展示

## API 接口

### 数据接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/excel-data` | GET | 获取Excel数据 |
| `/api/filter-data` | POST | 筛选数据 |
| `/api/add-transaction` | POST | 添加交易记录 |
| `/api/add-invoice` | POST | 添加发票记录 |
| `/api/delete-transaction` | POST | 删除交易记录 |
| `/api/alerts` | GET/POST | 获取/添加预警 |
| `/api/export-data` | POST | 导出数据 |

### 图谱接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/transaction-graph` | GET | 获取交易图谱数据 |
| `/api/invoice-graph` | GET | 获取发票图谱数据 |
| `/api/node-frequency` | GET | 获取节点交易频率 |

## 数据文件说明

系统使用以下数据文件（需自行准备）：

- **建模数据121.xlsx** - 核心交易数据
- **销项整理后.xlsx** - 发票数据
- **预警.xlsx** - 预警数据
- **cases_data.csv** - 案例数据索引

> 注意：数据文件已添加到 .gitignore，不会上传到GitHub

## 配置说明

### 后端配置 (app.py)

```python
# 数据文件路径配置
EXCEL_FILE_PATH = r'C:\path\to\your\data.xlsx'

# Flask服务器配置
app.run(host='0.0.0.0', port=5000, debug=True)
```

### 前端配置

前端通过相对路径访问后端API，无需额外配置。

## 开发说明

### 添加新功能

1. **后端API开发**
   - 在 `hou/app.py` 中添加新的路由
   - 实现业务逻辑
   - 返回JSON格式数据

2. **前端页面开发**
   - 在 `qian/` 目录下创建新的HTML文件
   - 使用Fetch API调用后端接口
   - 使用D3.js进行数据可视化

### 代码规范

- 后端：遵循PEP 8 Python编码规范
- 前端：使用ES6+语法，保持代码简洁

## 常见问题

### 1. 启动失败

**问题：** `ModuleNotFoundError: No module named 'flask'`

**解决：**
```bash
pip install -r hou/requirements.txt
```

### 2. 数据读取失败

**问题：** 页面显示"没有找到数据"

**解决：**
- 检查数据文件路径是否正确
- 确认Excel文件格式正确
- 查看后端控制台错误信息

### 3. 跨域问题

**问题：** 浏览器报CORS错误

**解决：**
后端已配置Flask-CORS，如仍有问题请检查：
```python
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 本项目
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 许可证

本项目仅供学习交流使用。

## 联系方式

如有问题或建议，欢迎通过GitHub Issue联系。

---

**项目地址：** https://github.com/sdnbfdb/-
