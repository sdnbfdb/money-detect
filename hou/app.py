from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import pandas as pd
import sys
import os
import time

# 导入DataSaver和CaseManager类
try:
    from index import DataSaver, CaseManager
except ImportError:
    print("Warning: Could not import DataSaver module")
    class DataSaver:
        def save_to_csv(self, data, filename=None, columns=None):
            return "DataSaver module not found"
        def save_excel_data(self, excel_file_path, output_filename=None):
            return "DataSaver module not found"
    class CaseManager:
        def get_all_cases(self):
            return []
        def add_case(self, case_data):
            return False
        def update_case(self, index, case_data):
            return False
        def delete_case(self, index):
            return False
        def get_case(self, index):
            return None


# 添加change.py所在的路径到系统路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入change.py中的函数
try:
    from change import add_transaction_record, validate_transaction_data, delete_transaction_record, add_invoice_record, validate_invoice_data, add_related_data_from_file
except ImportError:
    print("Warning: Could not import change module")
    def add_transaction_record(transaction_data):
        return {"success": False, "message": "change.py module not found"}
    def validate_transaction_data(transaction_data):
        return False, "change.py module not found"
    def delete_transaction_record(row_index):
        return {"success": False, "message": "change.py module not found"}
    def add_related_data_from_file(file_path, target_node):
        return {"success": False, "message": "change.py module not found", "added_count": 0}
    def add_invoice_record(invoice_data):
        return {"success": False, "message": "change.py module not found"}
    def validate_invoice_data(invoice_data):
        return False, "change.py module not found"

#导入note.py中的函数
try:
    from note import read_invoice_data, get_invoice_summary, filter_invoices_by_criteria
except ImportError:
    print("Warning: Could not import note module")
    def read_invoice_data(file_path):
        return {"success": False, "error": "note.py module not found"}
    def get_invoice_summary(file_path):
        return {"success": False, "error": "note.py module not found"}
    def filter_invoices_by_criteria(df, criteria):
        return df

# 导入simple.py中的函数
try:
    from simple import remove_leaf_nodes_from_source, build_full_transaction_topology, remove_isolated_and_leaf_nodes, create_invoice_network, analyze_invoice_topology
except ImportError:
    print("Warning: Could not import simple module")
    def remove_leaf_nodes_from_source(nodes, links, source_nodes):
        return nodes, links
    def build_full_transaction_topology(df, seed_nodes=None, max_depth=None, start_date=None, end_date=None, min_amount=None, max_amount=None, remove_leaves=False):
        return [], []
    def create_invoice_network(df, seller_col='销售方', buyer_col='购买方', amount_col='价税合计', date_col='开票日期'):
        return [], []
    def analyze_invoice_topology(df, seed_entities=None, max_depth=None):
        return {}

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

# 配置静态文件目录
STATIC_FOLDER = os.path.join(PARENT_DIR, 'qian')

# 基础文件路径
BASE_EXCEL_FILE = '建模数据121.xlsx'
BASE_INVOICE_FILE = '销项整理后.xlsx'
BASE_ALERT_FILE = '预警.xlsx'

@app.route('/')
def index():
    """主页 - 返回 filter.html"""
    return send_from_directory(STATIC_FOLDER, 'filter.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件服务"""
    return send_from_directory(STATIC_FOLDER, filename)

@app.route('/api/health')
def health():
    """健康检查接口"""
    return jsonify({"message": "Flask后端服务运行正常!"})

# 示例数据存储（实际应用中应使用数据库）
data_store = []

@app.route('/api/excel-data')
def get_excel_data():
    """
    读取Excel文件并返回数据
    """
    try:
        # 获取请求参数中的工作表名称或索引，默认为第一个工作表
        sheet_name = request.args.get('sheet_name', 0)
        # 如果参数是数字字符串，则转换为整数索引
        try:
            sheet_name = int(sheet_name)
        except ValueError:
            pass  # 保持为字符串名称
        
        # 获取案件参数
        case_index = request.args.get('caseIndex')
        case_name = request.args.get('caseName')
        case_time = request.args.get('caseTime')
        
        # 确定Excel文件路径
        if case_index and case_name and case_time:
            # 生成案件文件夹名称
            folder_name = f"{case_time}_{case_name}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            # 构建案件文件夹路径
            case_folder = os.path.join(PARENT_DIR, 'cases', folder_name)
            # 构建Excel文件路径
            excel_file_path = os.path.join(case_folder, BASE_EXCEL_FILE)
        else:
            # 使用默认路径
            excel_file_path = os.path.join(PARENT_DIR, BASE_EXCEL_FILE)
        
        # 添加重试机制读取Excel数据，以防文件被占用
        max_retries = 3
        retry_count = 0
        df = None
        while retry_count < max_retries:
            try:
                df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
                break  # 成功读取，跳出重试循环
            except PermissionError as pe:
                print(f"第{retry_count + 1}次尝试读取文件失败，文件可能被占用: {pe}")
                retry_count += 1
                time.sleep(1)  # 等待1秒后重试
                if retry_count >= max_retries:
                    raise pe  # 如果达到最大重试次数仍失败，则抛出异常
            except Exception as e:
                print(f"读取Excel文件时出错: {e}")
                raise e
        
        # 将DataFrame转换为字典格式，便于JSON序列化
        data = df.fillna('').to_dict(orient='records')
        
        # 返回所有数据
        return jsonify({"data": data, "total_rows": len(data), "columns": df.columns.tolist(), "sheet_name": sheet_name, "file_path": excel_file_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/node-related-data')
def get_node_related_data():
    """
    获取与特定节点相关的交易数据
    """
    try:
        # 获取节点ID
        node_id = request.args.get('nodeId')
        if not node_id:
            return jsonify({"success": False, "message": "未提供节点ID"}), 400
        
        # 获取案件参数
        case_index = request.args.get('caseIndex')
        case_name = request.args.get('caseName')
        case_time = request.args.get('caseTime')
        
        # 确定Excel文件路径
        if case_index and case_name and case_time:
            # 生成案件文件夹名称
            folder_name = f"{case_time}_{case_name}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            # 构建案件文件夹路径
            case_folder = os.path.join(PARENT_DIR, 'cases', folder_name)
            # 构建Excel文件路径
            excel_file_path = os.path.join(case_folder, BASE_EXCEL_FILE)
        else:
            # 使用默认路径
            excel_file_path = os.path.join(PARENT_DIR, BASE_EXCEL_FILE)
        
        # 读取Excel数据
        max_retries = 3
        retry_count = 0
        df = None
        while retry_count < max_retries:
            try:
                df = pd.read_excel(excel_file_path)
                break  # 成功读取，跳出重试循环
            except PermissionError as pe:
                print(f"第{retry_count + 1}次尝试读取文件失败，文件可能被占用: {pe}")
                retry_count += 1
                time.sleep(1)  # 等待1秒后重试
                if retry_count >= max_retries:
                    raise pe  # 如果达到最大重试次数仍失败，则抛出异常
            except Exception as e:
                print(f"读取Excel文件时出错: {e}")
                raise e
        
        # 筛选与节点相关的记录
        related_records = []
        for _, row in df.iterrows():
            # 检查交易方户名
            sender_name = row.get('交易方户名', row.get('\t交易方户名', ''))
            # 检查对手户名
            counterparty_name = row.get('对手户名', row.get('\t对手户名', ''))
            # 检查交易卡号
            card_no = row.get('交易卡号', row.get('\t交易卡号', ''))
            # 检查交易账号
            account_no = row.get('交易账号', row.get('\t交易账号', ''))
            
            # 如果任何字段包含节点ID，则认为是相关记录
            if (node_id in str(sender_name) or 
                node_id in str(counterparty_name) or 
                node_id in str(card_no) or 
                node_id in str(account_no)):
                # 将行转换为字典并处理NaN值
                row_dict = {}
                for key, value in row.items():
                    # 处理NaN值
                    if pd.isna(value):
                        row_dict[key] = ''  # 将NaN替换为空字符串
                    else:
                        row_dict[key] = value
                related_records.append(row_dict)
        
        # 返回相关记录
        return jsonify({
            "success": True,
            "data": related_records,
            "total_records": len(related_records),
            "node_id": node_id
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"获取节点相关数据时出错: {str(e)}"}), 500


@app.route('/api/excel-sheets')
def get_excel_sheets():
    """
    获取Excel文件的所有工作表名称
    """
    try:
        # 获取案件参数
        case_index = request.args.get('caseIndex')
        case_name = request.args.get('caseName')
        case_time = request.args.get('caseTime')
        
        # 确定Excel文件路径
        if case_index and case_name and case_time:
            # 生成案件文件夹名称
            folder_name = f"{case_time}_{case_name}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            # 构建案件文件夹路径
            case_folder = os.path.join(PARENT_DIR, 'cases', folder_name)
            # 构建Excel文件路径
            excel_file_path = os.path.join(case_folder, BASE_EXCEL_FILE)
        else:
            # 使用默认路径
            excel_file_path = os.path.join(PARENT_DIR, BASE_EXCEL_FILE)
        
        # 添加重试机制读取Excel文件，以防文件被占用
        max_retries = 3
        retry_count = 0
        excel_file = None
        while retry_count < max_retries:
            try:
                excel_file = pd.ExcelFile(excel_file_path)
                break  # 成功读取，跳出重试循环
            except PermissionError as pe:
                print(f"第{retry_count + 1}次尝试读取文件失败，文件可能被占用: {pe}")
                retry_count += 1
                time.sleep(1)  # 等待1秒后重试
                if retry_count >= max_retries:
                    raise pe  # 如果达到最大重试次数仍失败，则抛出异常
            except Exception as e:
                print(f"读取Excel文件时出错: {e}")
                raise e
        
        sheet_names = excel_file.sheet_names
        return jsonify({"sheet_names": sheet_names, "count": len(sheet_names), "file_path": excel_file_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route('/api/data', methods=['POST'])
def save_data():
    """
    接收前端发送的数据
    """
    try:
        data = request.get_json()
        
        # 验证必需字段
        if 'name' not in data or 'email' not in data:
            return jsonify({"error": "缺少必需字段: name 或 email"}), 400
        
        # 添加到数据存储
        new_entry = {
            "id": len(data_store) + 1,
            "name": data['name'],
            "email": data['email']
        }
        data_store.append(new_entry)
        
        return jsonify({
            "message": f"数据保存成功! 欢迎 {data['name']}!",
            "saved_data": new_entry
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/data', methods=['GET'])
def get_data():
    """
    获取所有已保存的数据
    """
    return jsonify({"data": data_store}), 200

@app.route('/api/data/<int:id>', methods=['GET'])
def get_single_data(id):
    """
    根据ID获取单个数据项
    """
    for item in data_store:
        if item['id'] == id:
            return jsonify({"data": item}), 200
    
    return jsonify({"error": "未找到指定ID的数据"}), 404

@app.route('/api/transaction', methods=['POST'])
def add_transaction():
    """
    接收前端发送的交易记录数据并添加到Excel文件中
    """
    try:
        transaction_data = request.get_json()
        
        if not transaction_data:
            return jsonify({"error": "未收到交易数据"}), 400
        
        # 验证交易数据格式
        is_valid, error_msg = validate_transaction_data(transaction_data)
        if not is_valid:
            return jsonify({"error": f"数据验证失败: {error_msg}"}), 400
        
        # 添加交易记录到Excel文件
        result = add_transaction_record(transaction_data)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": f"添加交易记录时出错: {str(e)}"}), 500


@app.route('/api/batch-transactions', methods=['POST'])
def batch_add_transactions():
    """
    接收前端上传的Excel文件并批量添加交易记录
    """
    try:
        from werkzeug.utils import secure_filename
        import os
        
        # 获取案件参数
        case_index = request.form.get('caseIndex')
        case_name = request.form.get('caseName')
        case_time = request.form.get('caseTime')
        
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "未找到上传的文件"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"success": False, "error": "未选择文件"}), 400
        
        if file and file.filename.lower().endswith(('.xlsx', '.xls')):
            filename = secure_filename(file.filename)
            
            # 保存上传的文件到临时位置
            temp_path = os.path.join("temp", filename)
            os.makedirs("temp", exist_ok=True)
            file.save(temp_path)
            
            # 使用change.py中的函数处理批量导入，传递案件参数
            from change import batch_add_transaction_records_from_file
            result = batch_add_transaction_records_from_file(temp_path, case_index, case_name, case_time)
            
            # 删除临时文件
            os.remove(temp_path)
            
            # 重新构建响应格式以保持一致性
            response_data = {
                "success": result["success"],
                "imported_count": result.get("added_count", 0),
                "total_rows": result.get("added_count", 0) + result.get("failed_count", 0),
                "failed_count": result.get("failed_count", 0),
                "message": result.get("message", ""),
                "failed_records": result.get("failed_records", [])
            }
            
            if result["success"]:
                return jsonify(response_data), 200
            else:
                return jsonify(response_data), 400
        else:
            return jsonify({"success": False, "error": "不支持的文件格式，请上传.xlsx或.xls文件"}), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": f"批量导入交易记录时出错: {str(e)}"}), 500


@app.route('/api/export-alerts', methods=['POST'])
def export_alerts_api():
    """
    接收前端预警数据并导出到Excel文件
    """
    try:
        # 获取前端发送的预警数据
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({"error": "未收到预警数据"}), 400
        
        # 获取案件参数
        case_index = request_data.get('caseIndex', None)
        case_name = request_data.get('caseName', None)
        case_time = request_data.get('caseTime', None)
        
        # 获取预警数据
        alerts_data = request_data.get('alerts', [])
        
        # 即使预警数据为空，也允许更新（删除所有预警）
        # if not alerts_data:
        #     return jsonify({"error": "未收到预警数据"}), 400
        
        # 确定输出文件路径
        if case_index and case_name and case_time:
            # 生成案件文件夹名称
            folder_name = f"{case_time}_{case_name}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            # 构建案件文件夹路径
            case_folder = os.path.join(PARENT_DIR, 'cases', folder_name)
            # 确保案件文件夹存在
            os.makedirs(case_folder, exist_ok=True)
            # 构建预警文件路径
            output_file = os.path.join(case_folder, BASE_ALERT_FILE)
        else:
            # 使用默认路径
            output_file = os.path.join(PARENT_DIR, BASE_ALERT_FILE)
        
        # 调用预警导出功能
        from warning import export_frontend_alerts_to_excel
        result = export_frontend_alerts_to_excel(alerts_data, output_file)
        
        if result:
            return jsonify({
                "success": True,
                "message": f"成功导出 {len(alerts_data)} 条预警信息到案件文件夹",
                "file_path": result,
                "record_count": len(alerts_data),
                "case_folder": case_folder if (case_index and case_name and case_time) else "默认路径"
            }), 200
        else:
            return jsonify({"error": "导出失败"}), 500
            
    except Exception as e:
        return jsonify({"error": f"导出过程中出错: {str(e)}"}), 500


@app.route('/api/alert-data')
def get_alert_data():
    """
    读取预警文件数据
    """
    try:
        # 获取案件参数
        case_index = request.args.get('caseIndex')
        case_name = request.args.get('caseName')
        case_time = request.args.get('caseTime')
        
        # 确定预警文件路径
        if case_index and case_name and case_time:
            # 生成案件文件夹名称
            folder_name = f"{case_time}_{case_name}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            # 构建案件文件夹路径
            case_folder = os.path.join(PARENT_DIR, 'cases', folder_name)
            # 构建预警文件路径
            alert_file_path = os.path.join(case_folder, BASE_ALERT_FILE)
        else:
            # 使用默认路径
            alert_file_path = os.path.join(PARENT_DIR, BASE_ALERT_FILE)
        
        # 检查文件是否存在
        if not os.path.exists(alert_file_path):
            return jsonify({
                "success": True,
                "data": [],
                "message": "预警文件不存在，返回空数据"
            }), 200
        
        # 读取预警文件
        try:
            df = pd.read_excel(alert_file_path, sheet_name='预警信息')
            # 转换为字典格式
            alert_data = df.fillna('').to_dict(orient='records')
            
            # 转换数据格式以匹配前端期望的格式
            formatted_alerts = []
            for record in alert_data:
                # 风险级别映射
                level_mapping = {
                    '低风险': 'low',
                    '中风险': 'medium',
                    '高风险': 'high',
                    '严重风险': 'critical'
                }
                
                # 预警类型映射
                type_mapping = {
                    '金额阈值预警': 'amount_threshold',
                    '频率异常预警': 'frequency_threshold',
                    '可疑模式预警': 'suspicious_pattern',
                    '黑名单匹配预警': 'blacklist_match'
                }
                
                formatted_alert = {
                    "id": record.get('预警ID', ''),
                    "nodeId": record.get('账户名称', ''),
                    "type": type_mapping.get(record.get('预警类型', ''), 'custom'),
                    "amountThreshold": record.get('金额阈值(元)', 'N/A'),
                    "description": record.get('预警描述', ''),
                    "level": level_mapping.get(record.get('风险级别', ''), 'low'),
                    "createTime": record.get('创建时间', ''),
                    "status": 'active' if record.get('状态', '') == '激活' else 'inactive'
                }
                formatted_alerts.append(formatted_alert)
            
            return jsonify({
                "success": True,
                "data": formatted_alerts,
                "total_alerts": len(formatted_alerts),
                "file_path": alert_file_path
            }), 200
        except Exception as e:
            print(f"读取预警文件时出错: {e}")
            return jsonify({
                "success": False,
                "error": f"读取预警文件时出错: {str(e)}"
            }), 500
            
    except Exception as e:
        return jsonify({"error": f"获取预警数据时出错: {str(e)}"}), 500
@app.route('/api/invoice-data')
def get_invoice_data():
    """
    获取发票数据
    """
    try:
        # 获取案件参数
        case_index = request.args.get('caseIndex')
        case_name = request.args.get('caseName')
        case_time = request.args.get('caseTime')
        
        # 从查询参数获取文件路径（可选），支持相对路径和绝对路径
        file_path = request.args.get('file_path', None)
        
        # 如果没有提供文件路径，根据案件参数确定路径
        if not file_path:
            if case_index and case_name and case_time:
                # 生成案件文件夹名称
                folder_name = f"{case_time}_{case_name}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                # 构建案件文件夹路径
                case_folder = os.path.join(PARENT_DIR, 'cases', folder_name)
                # 构建发票文件路径
                file_path = os.path.join(case_folder, BASE_INVOICE_FILE)
            else:
                # 使用默认路径
                file_path = os.path.join(PARENT_DIR, BASE_INVOICE_FILE)
        elif not os.path.isabs(file_path):
            # 如果是相对路径，转换为绝对路径
            file_path = os.path.join(PARENT_DIR, file_path)
        
        # 读取发票数据
        result = read_invoice_data(file_path)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify({"error": result["error"]}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/invoice-summary')
def get_invoice_summary_api():
    """
    获取发票数据摘要
    """
    try:
        # 获取案件参数
        case_index = request.args.get('caseIndex')
        case_name = request.args.get('caseName')
        case_time = request.args.get('caseTime')
        
        # 从查询参数获取文件路径（可选）
        file_path = request.args.get('file_path', None)
        
        # 如果没有提供文件路径，根据案件参数确定路径
        if not file_path:
            if case_index and case_name and case_time:
                # 生成案件文件夹名称
                folder_name = f"{case_time}_{case_name}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                # 构建案件文件夹路径
                case_folder = os.path.join(PARENT_DIR, 'cases', folder_name)
                # 构建发票文件路径
                file_path = os.path.join(case_folder, BASE_INVOICE_FILE)
            else:
                # 使用默认路径
                file_path = os.path.join(PARENT_DIR, BASE_INVOICE_FILE)
        elif not os.path.isabs(file_path):
            # 如果是相对路径，转换为绝对路径
            file_path = os.path.join(PARENT_DIR, file_path)
        
        # 获取发票摘要
        result = get_invoice_summary(file_path)
        
        if result.get("success", False):
            return jsonify(result), 200
        else:
            return jsonify({"error": result.get("error", "未知错误")}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/invoice-filter', methods=['POST'])
def filter_invoice_data():
    """
   根据条件筛选发票数据
    """
    try:
        # 获取筛选条件
        criteria = request.get_json()
        
        if not criteria:
            return jsonify({"error": "未提供筛选条件"}), 400
        
        # 从 criteria 中获取文件路径，如果没提供则使用默认路径
        file_path = criteria.pop('file_path', None)
        
        # 获取案件参数
        case_index = criteria.pop('caseIndex', None)
        case_name = criteria.pop('caseName', None)
        case_time = criteria.pop('caseTime', None)
        
        if not file_path:
            if case_index and case_name and case_time:
                # 生成案件文件夹名称
                folder_name = f"{case_time}_{case_name}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                # 构建案件文件夹路径
                case_folder = os.path.join(PARENT_DIR, 'cases', folder_name)
                # 构建发票文件路径
                file_path = os.path.join(case_folder, BASE_INVOICE_FILE)
            else:
                # 使用默认路径
                file_path = os.path.join(PARENT_DIR, BASE_INVOICE_FILE)
        elif not os.path.isabs(file_path):
            file_path = os.path.join(PARENT_DIR, file_path)
        
        # 读取原始发票数据
        result = read_invoice_data(file_path)
        
        if not result["success"]:
            return jsonify({"error": result["error"]}), 500
        
        #为 DataFrame 进行筛选
        df = pd.DataFrame(result["data"])
        filtered_df = filter_invoices_by_criteria(df, criteria)
        
        # 返回筛选结果
        filtered_data = filtered_df.fillna('').to_dict(orient='records')
        
        return jsonify({
            "success": True,
            "data": filtered_data,
            "total_rows": len(filtered_data),
            "filtered_count": len(filtered_data),
            "original_count": len(result["data"])
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"筛选发票数据时出错：{str(e)}"}), 500

@app.route('/api/transaction/<int:row_index>', methods=['DELETE'])
def delete_transaction(row_index):
    """
    删除指定索引的交易记录
    """
    try:
        # 删除交易记录
        result = delete_transaction_record(row_index)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": f"删除交易记录时出错: {str(e)}"}), 500


@app.route('/api/invoice', methods=['POST'])
def add_invoice():
    """
    接收前端发送的发票记录数据并添加到发票Excel文件中
    """
    try:
        invoice_data = request.get_json()
        
        if not invoice_data:
            return jsonify({"error": "未收到发票数据"}), 400
        
        # 验证发票数据格式
        from change import validate_invoice_data
        is_valid, error_msg = validate_invoice_data(invoice_data)
        if not is_valid:
            return jsonify({"error": f"数据验证失败: {error_msg}"}), 400
        
        # 导入添加发票记录的函数
        from change import add_invoice_record
        # 添加发票记录到Excel文件
        result = add_invoice_record(invoice_data)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": f"添加发票记录时出错: {str(e)}"}), 500


@app.route('/api/delete-transaction', methods=['POST'])
def delete_transaction_by_data():
    """
    根据交易记录的具体信息删除记录
    """
    try:
        # 获取要删除的交易信息
        transaction_data = request.get_json()
        
        if not transaction_data:
            return jsonify({"error": "未收到交易删除数据"}), 400
        
        # 导入删除交易记录的函数
        from change import delete_transaction_record_by_data
        # 删除交易记录
        result = delete_transaction_record_by_data(transaction_data)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": f"删除交易记录时出错: {str(e)}"}), 500


@app.route('/api/delete-invoice', methods=['POST'])
def delete_invoice():
    """
    删除发票记录
    """
    try:
        # 获取要删除的发票信息
        invoice_data = request.get_json()
        
        if not invoice_data:
            return jsonify({"error": "未收到发票删除数据"}), 400
        
        # 导入删除发票记录的函数
        from change import delete_invoice_record
        # 删除发票记录
        result = delete_invoice_record(invoice_data)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"error": f"删除发票记录时出错: {str(e)}"}), 500


@app.route('/api/simplify-graph', methods=['POST'])
def simplify_graph_api():
    """
    图谱简化API - 使用后端算法简化交易网络图
    """
    try:
        # 获取前端发送的图数据
        graph_data = request.get_json()
        
        if not graph_data or 'nodes' not in graph_data or 'links' not in graph_data:
            return jsonify({
                "success": False,
                "error": "缺少必要的图数据: nodes 和 links"
            }), 400
        
        # 提取节点和链接数据
        nodes = graph_data['nodes']
        links = graph_data['links']
        source_nodes = set(graph_data.get('sourceNodes', []))  # 源节点集合
        
        # 标准化节点ID函数
        def normalize_node_id(node_id):
            return node_id.strip().lstrip('\t') if isinstance(node_id, str) else node_id
        
        # 清理source_nodes中的\t前缀
        cleaned_source_nodes = set()
        for node in source_nodes:
            if isinstance(node, str):
                cleaned_source_nodes.add(normalize_node_id(node))
            else:
                cleaned_source_nodes.add(node)
        source_nodes = cleaned_source_nodes
        
        print(f"收到简化请求: 节点数={len(nodes)}, 链接数={len(links)}, 源节点数={len(source_nodes)}")
        print(f"源节点: {source_nodes}")
        
        # 检查是否需要移除孤立节点和叶节点
        remove_isolated = graph_data.get('removeIsolated', False)
        
        # 过滤掉虚拟节点（单边交易创建的临时节点）
        real_nodes = [n for n in nodes if not normalize_node_id(n['id'] if isinstance(n, dict) else n).endswith('_single_transaction')]
        real_node_ids = set(normalize_node_id(n['id'] if isinstance(n, dict) else n) for n in real_nodes)
        real_links = [l for l in links 
                      if normalize_node_id(l['source'] if isinstance(l['source'], str) else l['source']['id']) in real_node_ids
                      and normalize_node_id(l['target'] if isinstance(l['target'], str) else l['target']['id']) in real_node_ids]
        
        print(f"过滤虚拟节点后: 节点数={len(real_nodes)}, 链接数={len(real_links)}")
        
        if remove_isolated:
            # 调用后端简化函数，移除孤立节点和叶节点
            simplified_nodes, simplified_links = remove_isolated_and_leaf_nodes(real_nodes, real_links)
        else:
            # 调用后端简化函数，仅移除叶节点（保护源节点）
            simplified_nodes, simplified_links = remove_leaf_nodes_from_source(real_nodes, real_links, source_nodes)
        
        # 返回简化结果
        return jsonify({
            "success": True,
            "originalNodeCount": len(nodes),
            "originalLinkCount": len(links),
            "simplifiedNodeCount": len(simplified_nodes),
            "simplifiedLinkCount": len(simplified_links),
            "simplifiedNodes": simplified_nodes,
            "simplifiedLinks": simplified_links
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"图谱简化时出错: {str(e)}"
        }), 500


@app.route('/api/build-full-topology', methods=['POST'])
def build_full_topology_api():
    """
    构建完整交易网络拓扑API - 使用后端算法构建完整的交易网络
    """
    try:
        # 获取前端发送的参数
        params = request.get_json()
        
        seed_nodes = params.get('seedNodes', [])
        start_date = params.get('startDate', None)
        end_date = params.get('endDate', None)
        min_amount = params.get('minAmount', None)
        max_amount = params.get('maxAmount', None)
        
        # 获取案件参数
        case_index = params.get('caseIndex')
        case_name = params.get('caseName')
        case_time = params.get('caseTime')
        
        # 确定Excel文件路径
        if case_index and case_name and case_time:
            # 生成案件文件夹名称
            folder_name = f"{case_time}_{case_name}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            # 构建案件文件夹路径
            case_folder = os.path.join(PARENT_DIR, 'cases', folder_name)
            # 构建Excel文件路径
            excel_file_path = os.path.join(case_folder, BASE_EXCEL_FILE)
        else:
            # 使用默认路径
            excel_file_path = os.path.join(PARENT_DIR, BASE_EXCEL_FILE)
        
        # 添加重试机制读取Excel数据，以防文件被占用
        max_retries = 3
        retry_count = 0
        df = None
        while retry_count < max_retries:
            try:
                df = pd.read_excel(excel_file_path, sheet_name=0)
                break  # 成功读取，跳出重试循环
            except PermissionError as pe:
                print(f"第{retry_count + 1}次尝试读取文件失败，文件可能被占用: {pe}")
                retry_count += 1
                time.sleep(1)  # 等待1秒后重试
                if retry_count >= max_retries:
                    raise pe  # 如果达到最大重试次数仍失败，则抛出异常
            except Exception as e:
                print(f"读取Excel文件时出错: {e}")
                raise e
        
        # 应用时间筛选
        if start_date or end_date:
            # 智能查找时间列
            date_col = None
            for col_name in ['\t交易时间', '交易时间']:
                if col_name in df.columns:
                    date_col = col_name
                    break
                    
            if date_col:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                if start_date:
                    df = df[df[date_col] >= pd.to_datetime(start_date)]
                if end_date:
                    df = df[df[date_col] <= pd.to_datetime(end_date)]
        
        # 应用金额筛选
        if min_amount is not None or max_amount is not None:
            # 智能查找金额列
            amount_col = None
            for col_name in ['\t交易金额', '交易金额']:
                if col_name in df.columns:
                    amount_col = col_name
                    break
                    
            if amount_col:
                df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
                if min_amount is not None:
                    df = df[df[amount_col] >= min_amount]
                if max_amount is not None:
                    df = df[df[amount_col] <= max_amount]
        
        # 获取是否删除叶节点的参数
        remove_leaves = params.get('removeLeaves', False)
        
        # 调用后端构建完整拓扑的函数
        from simple import build_full_transaction_topology
        nodes, links = build_full_transaction_topology(df, seed_nodes, start_date=start_date, end_date=end_date, min_amount=min_amount, max_amount=max_amount, remove_leaves=remove_leaves)
        
        # 提取相关的交易数据用于前端显示
        transactions = df.fillna('').to_dict(orient='records')
        
        # 确保节点和链接数据格式正确
        # 如果节点或链接为空，返回空数组而不是None
        if nodes is None:
            nodes = []
        if links is None:
            links = []
        
        # 验证节点和链接数据格式
        validated_nodes = []
        for node in nodes:
            if isinstance(node, dict) and 'id' in node:
                validated_nodes.append(node)
            else:
                print(f"Invalid node format: {node}")
        
        validated_links = []
        for link in links:
            if isinstance(link, dict) and 'source' in link and 'target' in link:
                validated_links.append(link)
            else:
                print(f"Invalid link format: {link}")
        
        # 返回拓扑结果
        return jsonify({
            "success": True,
            "nodes": validated_nodes,
            "links": validated_links,
            "transactions": transactions,
            "nodeCount": len(validated_nodes),
            "linkCount": len(validated_links)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"构建交易网络拓扑时出错: {str(e)}"
        }), 500


@app.route('/api/upload-related-data', methods=['POST'])
def upload_related_data_api():
    """
    从Excel文件中提取与特定节点相关的数据并追加到主数据文件
    """
    try:
        from werkzeug.utils import secure_filename
        import os
        
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "未找到上传的文件"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"success": False, "message": "未选择文件"}), 400
        
        # 获取目标节点名称
        target_node = request.form.get('targetNode', '')
        if not target_node:
            return jsonify({"success": False, "message": "未指定目标节点"}), 400
        
        if file and file.filename.lower().endswith(('.xlsx', '.xls')):
            filename = secure_filename(file.filename)
            
            # 保存上传的文件到临时位置
            temp_path = os.path.join("temp", filename)
            os.makedirs("temp", exist_ok=True)
            file.save(temp_path)
            
            # 使用change.py中的函数处理相关数据追加
            result = add_related_data_from_file(temp_path, target_node)
            
            # 删除临时文件
            try:
                os.remove(temp_path)
            except OSError:
                pass  # 如果无法删除临时文件，继续执行
            
            # 重新构建响应格式以保持一致性
            response_data = {
                "success": result["success"],
                "added_count": result.get("added_count", 0),
                "message": result.get("message", ""),
                "total_records": result.get("total_records", 0)
            }
            
            if result["success"]:
                return jsonify(response_data), 200
            else:
                return jsonify(response_data), 400
        else:
            return jsonify({"success": False, "message": "不支持的文件格式，请上传.xlsx或.xls文件"}), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"处理相关数据文件时出错: {str(e)}"}), 500


@app.route('/api/import-invoice-data', methods=['POST'])
def import_invoice_data():
    """
    接收前端上传的发票Excel文件并导入数据到案件子文件夹
    """
    try:
        from werkzeug.utils import secure_filename
        import os
        
        # 获取案件参数
        case_index = request.form.get('caseIndex')
        case_name = request.form.get('caseName')
        case_time = request.form.get('caseTime')
        
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "未找到上传的文件"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"success": False, "message": "未选择文件"}), 400
        
        if file and file.filename.lower().endswith(('.xlsx', '.xls')):
            filename = secure_filename(file.filename)
            
            # 保存上传的文件到临时位置
            temp_path = os.path.join("temp", filename)
            os.makedirs("temp", exist_ok=True)
            file.save(temp_path)
            
            # 读取上传的发票数据
            df = pd.read_excel(temp_path)
            
            # 处理列名中的 \t 前缀
            column_mapping = {}
            for col in df.columns:
                if col.startswith('\t'):
                    clean_col = col.lstrip('\t')
                    column_mapping[col] = clean_col
            
            if column_mapping:
                df.rename(columns=column_mapping, inplace=True)
            
            # 处理数据内容中的 \t 前缀
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].apply(lambda x: x.lstrip('\t') if isinstance(x, str) and x.startswith('\t') else x)
            
            # 将数据转换为字典格式
            invoice_data = df.fillna('').to_dict(orient='records')
            
            # 确定目标发票文件路径
            if case_index and case_name and case_time:
                # 生成案件文件夹名称
                folder_name = f"{case_time}_{case_name}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                # 构建案件文件夹路径
                case_folder = os.path.join(PARENT_DIR, 'cases', folder_name)
                # 构建发票文件路径
                invoice_file_path = os.path.join(case_folder, '销项整理后.xlsx')
                
                # 确保案件文件夹存在
                if not os.path.exists(case_folder):
                    os.makedirs(case_folder, exist_ok=True)
                    print(f'创建案件文件夹: {case_folder}')
                
                # 读取现有的发票数据（如果文件存在）
                if os.path.exists(invoice_file_path):
                    existing_df = pd.read_excel(invoice_file_path)
                    # 合并数据
                    merged_df = pd.concat([existing_df, df], ignore_index=True)
                    # 保存合并后的数据
                    merged_df.to_excel(invoice_file_path, index=False, engine='openpyxl')
                    print(f'合并发票数据到: {invoice_file_path}')
                else:
                    # 直接保存新数据
                    df.to_excel(invoice_file_path, index=False, engine='openpyxl')
                    print(f'创建新发票文件: {invoice_file_path}')
                
                message = f"成功导入 {len(invoice_data)} 条发票记录到案件文件夹"
            else:
                # 没有案件参数，只返回数据不保存
                message = f"成功读取 {len(invoice_data)} 条发票记录（未保存到案件文件夹）"
            
            # 删除临时文件
            try:
                os.remove(temp_path)
            except OSError:
                pass  # 如果无法删除临时文件，继续执行
            
            # 返回导入的数据信息
            response_data = {
                "success": True,
                "message": message,
                "data": invoice_data,
                "columns": df.columns.tolist(),
                "total_records": len(invoice_data),
                "saved_to_case": bool(case_index and case_name and case_time)
            }
            
            return jsonify(response_data), 200
        else:
            return jsonify({"success": False, "message": "不支持的文件格式，请上传.xlsx或.xls文件"}), 400
            
    except Exception as e:
        return jsonify({"success": False, "message": f"导入发票数据时出错: {str(e)}"}), 500


@app.route('/api/invoice-topology', methods=['POST'])
def analyze_invoice_topology_api():
    """
    分析发票数据的拓扑结构
    """
    try:
        # 获取前端发送的参数
        params = request.get_json()
        
        # 从参数获取文件路径，如果没有则使用默认相对路径
        file_path = params.get('file_path', None)
        if not file_path:
            file_path = os.path.join(PARENT_DIR, '销项整理后.xlsx')
        elif not os.path.isabs(file_path):
            file_path = os.path.join(PARENT_DIR, file_path)
        
        seed_entities = params.get('seed_entities', None)
        max_depth = params.get('max_depth', None)
        
        # 读取发票数据
        df = pd.read_excel(file_path)
        
        # 调用拓扑分析函数
        topology_result = analyze_invoice_topology(df, seed_entities, max_depth)
        
        # 返回拓扑分析结果
        return jsonify({
            "success": True,
            "topology_data": topology_result,
            "message": "发票拓扑分析完成"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"分析发票拓扑时出错：{str(e)}"}), 500


@app.route('/api/create-invoice-network', methods=['POST'])
def create_invoice_network_api():
    """
    从发票数据创建网络图
    """
    try:
        # 获取前端发送的参数
        params = request.get_json()
        
        # 从参数获取文件路径，如果没有则使用默认相对路径
        file_path = params.get('file_path', None)
        if not file_path:
            file_path = os.path.join(PARENT_DIR, '销项整理后.xlsx')
        elif not os.path.isabs(file_path):
            file_path = os.path.join(PARENT_DIR, file_path)
        
        # 读取发票数据
        df = pd.read_excel(file_path)
        
        # 从参数获取列名配置
        seller_col = params.get('seller_col', '销售方')
        buyer_col = params.get('buyer_col', '购买方')
        amount_col = params.get('amount_col', '价税合计')
        date_col = params.get('date_col', '开票日期')
        
        # 调用创建发票网络函数
        nodes, links = create_invoice_network(df, seller_col, buyer_col, amount_col, date_col)
        
        # 返回网络图数据
        return jsonify({
            "success": True,
            "nodes": nodes,
            "links": links,
            "node_count": len(nodes),
            "link_count": len(links),
            "message": "发票网络创建完成"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"创建发票网络时出错：{str(e)}"}), 500


@app.route('/api/save-csv', methods=['POST'])
def save_csv_api():
    """
    保存数据为CSV文件
    """
    try:
        # 获取前端发送的数据
        data = request.get_json()
        
        if not data or 'data' not in data:
            return jsonify({"success": False, "message": "缺少数据参数"}), 400
        
        # 提取数据和参数
        save_data = data['data']
        filename = data.get('filename', None)
        columns = data.get('columns', None)
        append = data.get('append', False)
        
        # 创建DataSaver实例
        saver = DataSaver()
        
        # 保存数据
        file_path = saver.save_to_csv(save_data, filename, columns, append)
        
        # 返回结果
        return jsonify({
            "success": True,
            "message": "数据保存成功",
            "file_path": file_path,
            "file_name": os.path.basename(file_path)
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"保存数据时出错：{str(e)}"}), 500


@app.route('/api/export-excel', methods=['POST'])
def export_excel_api():
    """
    将Excel文件导出为CSV
    """
    try:
        # 获取前端发送的参数
        data = request.get_json()
        
        if not data or 'file_path' not in data:
            return jsonify({"success": False, "message": "缺少文件路径参数"}), 400
        
        # 提取参数
        excel_path = data['file_path']
        filename = data.get('filename', None)
        
        # 处理相对路径
        if not os.path.isabs(excel_path):
            excel_path = os.path.join(PARENT_DIR, excel_path)
        
        # 检查文件是否存在
        if not os.path.exists(excel_path):
            return jsonify({"success": False, "message": f"文件不存在：{excel_path}"}), 404
        
        # 创建DataSaver实例
        saver = DataSaver()
        
        # 导出数据
        file_path = saver.save_excel_data(excel_path, filename)
        
        # 返回结果
        return jsonify({
            "success": True,
            "message": "Excel文件导出成功",
            "file_path": file_path,
            "file_name": os.path.basename(file_path)
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"导出Excel文件时出错：{str(e)}"}), 500


# 案件管理API端点
@app.route('/api/cases', methods=['GET'])
def get_all_cases():
    """
    获取所有案件数据
    """
    try:
        # 创建CaseManager实例
        case_manager = CaseManager()
        
        # 获取所有案件
        cases = case_manager.get_all_cases()
        
        # 返回结果
        return jsonify({
            "success": True,
            "cases": cases,
            "count": len(cases)
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"获取案件数据时出错：{str(e)}"}), 500


@app.route('/api/cases', methods=['POST'])
def add_case():
    """
    添加新案件
    """
    try:
        # 获取前端发送的案件数据
        case_data = request.get_json()
        
        if not case_data:
            return jsonify({"success": False, "message": "缺少案件数据"}), 400
        
        # 创建CaseManager实例
        case_manager = CaseManager()
        
        # 添加案件
        success = case_manager.add_case(case_data)
        
        if success:
            return jsonify({
                "success": True,
                "message": "案件添加成功",
                "case": case_data
            }), 200
        else:
            return jsonify({"success": False, "message": "案件添加失败"}), 400
        
    except Exception as e:
        return jsonify({"success": False, "message": f"添加案件时出错：{str(e)}"}), 500


@app.route('/api/cases/<int:index>', methods=['PUT'])
def update_case(index):
    """
    更新案件数据
    """
    try:
        # 获取前端发送的案件数据
        case_data = request.get_json()
        
        if not case_data:
            return jsonify({"success": False, "message": "缺少案件数据"}), 400
        
        # 创建CaseManager实例
        case_manager = CaseManager()
        
        # 更新案件
        success = case_manager.update_case(index, case_data)
        
        if success:
            return jsonify({
                "success": True,
                "message": "案件更新成功",
                "case": case_data
            }), 200
        else:
            return jsonify({"success": False, "message": "案件更新失败"}), 400
        
    except Exception as e:
        return jsonify({"success": False, "message": f"更新案件时出错：{str(e)}"}), 500


@app.route('/api/cases/<int:index>', methods=['DELETE'])
def delete_case(index):
    """
    删除案件
    """
    try:
        # 创建CaseManager实例
        case_manager = CaseManager()
        
        # 删除案件
        success = case_manager.delete_case(index)
        
        if success:
            return jsonify({
                "success": True,
                "message": "案件删除成功"
            }), 200
        else:
            return jsonify({"success": False, "message": "案件删除失败"}), 400
        
    except Exception as e:
        return jsonify({"success": False, "message": f"删除案件时出错：{str(e)}"}), 500


@app.route('/api/cases/<int:index>', methods=['GET'])
def get_case(index):
    """
    获取单个案件数据
    """
    try:
        # 创建CaseManager实例
        case_manager = CaseManager()
        
        # 获取案件
        case = case_manager.get_case(index)
        
        if case:
            return jsonify({
                "success": True,
                "case": case
            }), 200
        else:
            return jsonify({"success": False, "message": "案件不存在"}), 404
        
    except Exception as e:
        return jsonify({"success": False, "message": f"获取案件时出错：{str(e)}"}), 500


@app.route('/api/case-data', methods=['GET'])
def get_case_data():
    """
    根据案件信息从案件文件夹加载数据
    """
    try:
        # 获取查询参数
        case_index = request.args.get('caseIndex')
        case_name = request.args.get('caseName')
        case_time = request.args.get('caseTime')
        
        if not case_index or not case_name or not case_time:
            return jsonify({"success": False, "message": "缺少案件参数"}), 400
        
        # 创建CaseManager实例
        case_manager = CaseManager()
        
        # 生成案件文件夹名称
        folder_name = f"{case_time}_{case_name}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
        
        # 构建案件文件夹路径
        case_folder = os.path.join(case_manager.data_dir, 'cases', folder_name)
        
        # 查找案件文件夹中的 Excel 文件
        excel_files = []
        if os.path.exists(case_folder):
            for file in os.listdir(case_folder):
                if file.endswith('.xlsx') or file.endswith('.xls'):
                    excel_files.append(os.path.join(case_folder, file))
                
        if not excel_files:
            return jsonify({"success": False, "message": "案件文件夹中没有 Excel 文件"}), 404
                
        # 优先读取"建模数据 121.xlsx"文件，如果没有则读取第一个 Excel 文件
        excel_file = None
        for file in excel_files:
            if '建模数据' in os.path.basename(file) or '建模数据' in file:
                excel_file = file
                break
                
        # 如果没有找到建模数据文件，使用第一个 Excel 文件
        if not excel_file:
            excel_file = excel_files[0]
            print(f"警告：未找到建模数据文件，使用默认文件：{excel_file}")
                
        print(f"读取案件数据文件：{excel_file}")
                
        # 读取第一个 Excel 文件
        df = pd.read_excel(excel_file)
        
        # 将DataFrame转换为字典格式
        data = df.fillna('').to_dict(orient='records')
        
        return jsonify({
            "success": True,
            "data": data,
            "file_path": excel_file,
            "total_rows": len(data),
            "columns": df.columns.tolist()
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"加载案件数据时出错：{str(e)}"}), 500


if __name__ == '__main__':
    print("Flask应用正在启动...")
    print("前端可以访问 http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)