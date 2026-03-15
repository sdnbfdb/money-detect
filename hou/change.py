import pandas as pd
import os
from datetime import datetime
import time
import threading
import re

def delete_transaction_record(row_index):
    """
    从Excel文件中删除指定索引的交易记录
    
    Args:
        row_index (int): 要删除的行索引（从0开始）
    
    Returns:
        dict: 包含操作结果的消息
    """
    try:
        # Excel文件路径
        excel_file_path = r'../建模数据121.xlsx'
        
        # 调试信息
        current_dir = os.getcwd()
        print(f'当前工作目录: {current_dir}')
        print(f'相对路径: {excel_file_path}')
        print(f'相对路径存在: {os.path.exists(excel_file_path)}')
        
        # 如果相对路径不存在，尝试绝对路径
        if not os.path.exists(excel_file_path):
            excel_file_path = r'C:\Users\sanjin\Desktop\新建文件夹\建模数据121.xlsx'
            print(f'使用绝对路径: {excel_file_path}')
            print(f'绝对路径存在: {os.path.exists(excel_file_path)}')
            
        # 再次检查文件是否存在
        if not os.path.exists(excel_file_path):
            return {"success": False, "message": f"Excel文件不存在: {excel_file_path}"}
        
        # 读取现有的Excel数据
        df = pd.read_excel(excel_file_path, engine='openpyxl')
        
        # 验证行索引是否有效
        if row_index < 0 or row_index >= len(df):
            return {"success": False, "message": f"行索引 {row_index} 超出范围。有效范围: 0-{len(df)-1}"}
        
        # 获取要删除的记录信息（用于返回给前端）
        #处理NaN值，避免JSON序列化错误
        deleted_record = df.iloc[row_index].fillna('').to_dict()
        #确保所有值都是JSON可序列化的
        for key, value in deleted_record.items():
            if pd.isna(value):
                deleted_record[key] = ''
            elif isinstance(value, (int, float)) and pd.isna(value):
                deleted_record[key] = None
        
        # 删除指定行
        df = df.drop(index=row_index).reset_index(drop=True)
        
        # 添加重试机制，以防文件被占用
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                print(f"准备保存文件到: {excel_file_path}")
                df.to_excel(excel_file_path, index=False, engine='openpyxl')
                print("文件保存成功")
                break  # 成功保存，跳出重试循环
            except PermissionError as pe:
                print(f"第{retry_count + 1}次尝试保存失败，文件可能被占用: {pe}")
                retry_count += 1
                time.sleep(1)  # 等待1秒后重试
                if retry_count >= max_retries:
                    raise pe  # 如果达到最大重试次数仍失败，则抛出异常
            except Exception as save_error:
                print(f"文件保存失败: {save_error}")
                return {"success": False, "message": f"保存文件时出错: {str(save_error)}"}
        
        return {
            "success": True, 
            "message": f"交易记录删除成功! 删除了第 {row_index + 1} 行记录",
            "deleted_record": deleted_record,
            "record_count": len(df)
        }
        
    except Exception as e:
        return {"success": False, "message": f"删除交易记录时出错: {str(e)}"}


def add_transaction_record(transaction_data, case_index=None, case_name=None, case_time=None):
    """
    将交易记录添加到Excel文件中
    
    Args:
        transaction_data (dict or list): 包含交易记录数据的字典或字典列表
            必填字段: '交易卡号', '交易账号', '交易方户名', '交易时间', '交易金额', '交易余额', '交易币种', '借贷标志'
            选填字段: '对手卡号', '对手账号', '对手户名'
        case_index (str, optional): 案件索引
        case_name (str, optional): 案件名称
        case_time (str, optional): 案件时间
    
    Returns:
        dict: 包含操作结果的消息
    """
    try:
        # 确定交易文件路径
        if case_index and case_name and case_time:
            # 生成案件文件夹名称
            folder_name = f"{case_time}_{case_name}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            
            # 构建案件文件夹路径
            current_file = __file__
            print(f'当前文件路径: {current_file}')
            
            current_dir = os.path.dirname(current_file)
            print(f'当前目录: {current_dir}')
            
            parent_dir = os.path.dirname(current_dir)
            print(f'父目录: {parent_dir}')
            
            case_folder = os.path.join(parent_dir, 'cases', folder_name)
            print(f'案件文件夹路径: {case_folder}')
            
            # 构建交易文件路径
            excel_file_path = os.path.join(case_folder, '建模数据121.xlsx')
            print(f'交易文件路径: {excel_file_path}')
            
            # 确保案件文件夹存在
            if not os.path.exists(case_folder):
                try:
                    os.makedirs(case_folder, exist_ok=True)
                    print(f'创建案件文件夹成功: {case_folder}')
                except Exception as e:
                    print(f'创建案件文件夹失败: {str(e)}')
            else:
                print(f'案件文件夹已存在: {case_folder}')
            
            # 如果交易文件不存在，创建一个新的
            if not os.path.exists(excel_file_path):
                try:
                    # 创建一个新的DataFrame
                    df = pd.DataFrame({
                        '交易卡号': [],
                        '交易账号': [],
                        '交易方户名': [],
                        '交易时间': [],
                        '交易金额': [],
                        '交易余额': [],
                        '交易币种': [],
                        '借贷标志': [],
                        '对手卡号': [],
                        '对手账号': [],
                        '对手户名': [],
                        '对手证件号': [],
                        '对手账户开户银行': [],
                        '对手交易余额': [],
                        '对手所属省份': [],
                        '对手所属城市': [],
                        '对手所属地区': [],
                        '交易方证件号': [],
                        '交易账户开户银行': [],
                        '交易方式': [],
                        '交易银行名': [],
                        '交易网点号': [],
                        '摘要说明': [],
                        '现金标志': [],
                        '交易是否成功': [],
                        '交易类型': [],
                        'IP地址': [],
                        'MAC地址': [],
                        '交易渠道': [],
                        '交易场所': [],
                        '交易发生地': [],
                        '传票号': [],
                        '交易记录ID': [],
                        '报告机构': [],
                        '代办人名称': [],
                        '代办人证件号码': [],
                        '查询反馈结果原因': [],
                        '交易名称所属国家': [],
                        '交易方所属省份': [],
                        '交易方所属城市': [],
                        '交易方所属地区': [],
                        '交易流水号': [],
                        '备注': [],
                        '批次': []
                    })
                    # 保存到文件
                    df.to_excel(excel_file_path, index=False, engine='openpyxl')
                    print(f'创建新的交易文件成功: {excel_file_path}')
                except Exception as e:
                    print(f'创建交易文件失败: {str(e)}')
                    # 如果创建失败，使用默认路径
                    excel_file_path = r'C:\Users\sanjin\Desktop\新建文件夹\建模数据121.xlsx'
                    print(f'使用默认路径: {excel_file_path}')
                    if os.path.exists(excel_file_path):
                        df = pd.read_excel(excel_file_path, engine='openpyxl')
                    else:
                        return {"success": False, "message": f"无法创建或找到交易文件: {str(e)}"}
            else:
                # 读取现有的交易Excel数据
                try:
                    df = pd.read_excel(excel_file_path, engine='openpyxl')
                    print(f'读取现有交易文件成功: {excel_file_path}')
                except Exception as e:
                    print(f'读取交易文件失败: {str(e)}')
                    return {"success": False, "message": f"读取交易文件时出错: {str(e)}"}
        else:
            # 使用默认路径
            excel_file_path = r'../建模数据121.xlsx'
            
            # 调试信息
            current_dir = os.getcwd()
            print(f'当前工作目录: {current_dir}')
            print(f'相对路径: {excel_file_path}')
            print(f'相对路径存在: {os.path.exists(excel_file_path)}')
            
            # 如果相对路径不存在，尝试绝对路径
            if not os.path.exists(excel_file_path):
                excel_file_path = r'C:\Users\sanjin\Desktop\新建文件夹\建模数据121.xlsx'
                print(f'使用绝对路径: {excel_file_path}')
                print(f'绝对路径存在: {os.path.exists(excel_file_path)}')
                
            # 再次检查文件是否存在
            if not os.path.exists(excel_file_path):
                return {"success": False, "message": f"Excel文件不存在: {excel_file_path}"}
            
            # 读取现有的Excel数据
            df = pd.read_excel(excel_file_path, engine='openpyxl')
        
        # 如果传入的是单个字典，转换为列表
        if isinstance(transaction_data, dict):
            transaction_data = [transaction_data]
        elif not isinstance(transaction_data, list):
            return {"success": False, "message": "数据格式错误: 期望字典或字典列表"}
        
        # 验证并添加多条记录
        new_records = []
        failed_records = []
        
        # 智能检测现有数据的列名格式（兼容带制表符和不带制表符的格式）
        def find_column_in_df(df, possible_names):
            """在DataFrame中查找存在的列名"""
            for name in possible_names:
                if name in df.columns:
                    return name
            # 如果都没找到，返回第一个可能的名称（假设有制表符的格式）
            return possible_names[0]
        
        # 查找实际使用的列名格式
        card_no_col = find_column_in_df(df, ['\t交易卡号', '交易卡号'])
        account_no_col = find_column_in_df(df, ['\t交易账号', '交易账号'])
        sender_name_col = find_column_in_df(df, ['\t交易方户名', '交易方户名'])
        sender_id_col = find_column_in_df(df, ['\t交易方证件号', '交易方证件号'])
        bank_account_col = find_column_in_df(df, ['\t交易账户开户银行', '交易账户开户银行'])
        trans_time_col = find_column_in_df(df, ['\t交易时间', '交易时间'])
        trans_method_col = find_column_in_df(df, ['\t交易方式', '交易方式'])
        trans_amount_col = find_column_in_df(df, ['\t交易金额', '交易金额'])
        trans_balance_col = find_column_in_df(df, ['\t交易余额', '交易余额'])
        trans_currency_col = find_column_in_df(df, ['\t交易币种', '交易币种'])
        debit_credit_col = find_column_in_df(df, ['\t借贷标志', '借贷标志'])
        counterparty_card_col = find_column_in_df(df, ['\t对手卡号', '对手卡号'])
        counterparty_account_col = find_column_in_df(df, ['\t对手账号', '对手账号'])
        counterparty_name_col = find_column_in_df(df, ['\t对手户名', '对手户名'])
        counterparty_id_col = find_column_in_df(df, ['\t对手证件号', '对手证件号'])
        counterparty_bank_col = find_column_in_df(df, ['\t对手账户开户银行', '对手账户开户银行'])
        counterparty_balance_col = find_column_in_df(df, ['\t对手交易余额', '对手交易余额'])
        bank_name_col = find_column_in_df(df, ['\t交易银行名', '交易银行名'])
        branch_no_col = find_column_in_df(df, ['\t交易网点号', '交易网点号'])
        memo_col = find_column_in_df(df, ['\t摘要说明', '摘要说明'])
        cash_flag_col = find_column_in_df(df, ['\t现金标志', '现金标志'])
        success_flag_col = find_column_in_df(df, ['\t交易是否成功', '交易是否成功'])
        trans_type_col = find_column_in_df(df, ['\t交易类型', '交易类型'])
        ip_addr_col = find_column_in_df(df, ['\tIP地址', 'IP地址'])
        ip_country_col = find_column_in_df(df, ['\tIP所属国家', 'IP所属国家'])
        ip_province_col = find_column_in_df(df, ['\tIP所属省份', 'IP所属省份'])
        ip_city_col = find_column_in_df(df, ['\tIP所属城市', 'IP所属城市'])
        ip_region_col = find_column_in_df(df, ['\tIP所属地区', 'IP所属地区'])
        mac_addr_col = find_column_in_df(df, ['\tMAC地址', 'MAC地址'])
        channel_col = find_column_in_df(df, ['\t交易渠道', '交易渠道'])
        venue_col = find_column_in_df(df, ['\t交易场所', '交易场所'])
        location_col = find_column_in_df(df, ['\t交易发生地', '交易发生地'])
        voucher_no_col = find_column_in_df(df, ['\t传票号', '传票号'])
        record_id_col = find_column_in_df(df, ['\t交易记录ID', '交易记录ID'])
        report_org_col = find_column_in_df(df, ['\t报告机构', '报告机构'])
        agent_name_col = find_column_in_df(df, ['\t代办人名称', '代办人名称'])
        agent_id_col = find_column_in_df(df, ['\t代办人证件号码', '代办人证件号码'])
        feedback_reason_col = find_column_in_df(df, ['\t查询反馈结果原因', '查询反馈结果原因'])
        country_col = find_column_in_df(df, ['\t交易名称所属国家', '交易名称所属国家'])
        sender_province_col = find_column_in_df(df, ['\t交易方所属省份', '交易方所属省份'])
        sender_city_col = find_column_in_df(df, ['\t交易方所属城市', '交易方所属城市'])
        sender_region_col = find_column_in_df(df, ['\t交易方所属地区', '交易方所属地区'])
        counterparty_province_col = find_column_in_df(df, ['\t对手所属省份', '对手所属省份'])
        counterparty_city_col = find_column_in_df(df, ['\t对手所属城市', '对手所属城市'])
        counterparty_region_col = find_column_in_df(df, ['\t对手所属地区', '对手所属地区'])
        serial_no_col = find_column_in_df(df, ['\t交易流水号', '交易流水号'])
        remarks_col = find_column_in_df(df, ['\t备注', '备注'])
        batch_col = find_column_in_df(df, ['\t批次', '批次'])
        
        # 定义实际使用的列名列表
        excel_columns = [
            card_no_col, account_no_col, sender_name_col, sender_id_col, 
            bank_account_col, trans_time_col, trans_method_col, trans_amount_col, 
            trans_balance_col, trans_currency_col, debit_credit_col, counterparty_card_col,
            counterparty_account_col, counterparty_name_col, counterparty_id_col, counterparty_bank_col, 
            counterparty_balance_col, bank_name_col, branch_no_col, memo_col, 
            cash_flag_col, success_flag_col, trans_type_col, ip_addr_col, 
            ip_country_col, ip_province_col, ip_city_col, ip_region_col, 
            mac_addr_col, channel_col, venue_col, location_col, 
            voucher_no_col, record_id_col, report_org_col, agent_name_col, 
            agent_id_col, feedback_reason_col, country_col, 
            sender_province_col, sender_city_col, sender_region_col, 
            counterparty_province_col, counterparty_city_col, counterparty_region_col, 
            serial_no_col, remarks_col, batch_col
        ]
        
        # 映射表单字段到实际Excel列名
        field_mapping = {
            '交易卡号': card_no_col,
            '交易账号': account_no_col,
            '交易方户名': sender_name_col,
            '交易时间': trans_time_col,
            '交易金额': trans_amount_col,
            '交易余额': trans_balance_col,
            '交易币种': trans_currency_col,
            '借贷标志': debit_credit_col,
            '对手卡号': counterparty_card_col,
            '对手账号': counterparty_account_col,
            '对手户名': counterparty_name_col
        }
        
        for idx, record_data in enumerate(transaction_data):
            # 验证必填字段
            required_fields = [
                '交易卡号', '交易账号', '交易方户名', '交易时间', 
                '交易金额', '交易余额', '交易币种', '借贷标志'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in record_data or not str(record_data[field]).strip():
                    missing_fields.append(field)
            
            if missing_fields:
                failed_records.append({
                    "index": idx,
                    "error": f"缺少必填字段: {', '.join(missing_fields)}"
                })
                continue
            
            # 创建新的交易记录
            new_record = {}
            
            # 初始化新记录的字典，所有字段默认为空字符串
            for col in excel_columns:
                new_record[col] = ''
            
            # 填充数据（兼容带\t和不带\t的字段名）
            for form_field, excel_col in field_mapping.items():
                # 优先检查不带\t的字段名，再检查带\t的字段名
                if form_field in record_data:
                    new_record[excel_col] = record_data[form_field]
                elif f'\t{form_field}' in record_data:
                    new_record[excel_col] = record_data[f'\t{form_field}']
            
            # 处理其他可能的字段（不在field_mapping中的）
            for key, value in record_data.items():
                if value and str(value).strip():  # 如果值不为空
                    clean_key = key.lstrip('\t')  # 移除\t前缀
                    # 如果清理后的键对应的Excel列存在，且尚未填充
                    if clean_key in field_mapping:
                        excel_col = field_mapping[clean_key]
                        if not new_record.get(excel_col):
                            new_record[excel_col] = value
            
            # 清理新记录中所有值里的\t
            for key in new_record:
                value = new_record[key]
                if isinstance(value, str) and value.startswith('\t'):
                    new_record[key] = value.lstrip('\t')
            
            # 如果批次号未提供，可以使用当前时间戳或其他逻辑生成
            batch_col = '\t批次' if '\t批次' in new_record else '批次'
            if not new_record.get(batch_col):
                new_record[batch_col] = datetime.now().strftime('%Y%m%d')
            
            new_records.append(new_record)
        
        # 将新记录添加到DataFrame
        if new_records:
            new_df = pd.DataFrame(new_records)
            # 清理DataFrame中所有字符串列的\t
            for col in new_df.columns:
                if new_df[col].dtype == 'object':
                    new_df[col] = new_df[col].apply(lambda x: x.lstrip('\t') if isinstance(x, str) and x.startswith('\t') else x)
            df = pd.concat([df, new_df], ignore_index=True)
        
        # 添加重试机制，以防文件被占用
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                print(f"准备保存文件到: {excel_file_path}")
                df.to_excel(excel_file_path, index=False, engine='openpyxl')
                print("文件保存成功")
                break  # 成功保存，跳出重试循环
            except PermissionError as pe:
                print(f"第{retry_count + 1}次尝试保存失败，文件可能被占用: {pe}")
                retry_count += 1
                time.sleep(1)  # 等待1秒后重试
                if retry_count >= max_retries:
                    return {"success": False, "message": f"保存文件时出错: {str(pe)}"}
            except Exception as save_error:
                print(f"文件保存失败: {save_error}")
                return {"success": False, "message": f"保存文件时出错: {str(save_error)}"}
        
        return {
            "success": True, 
            "message": f"交易记录添加成功! 成功添加 {len(new_records)} 条记录，失败 {len(failed_records)} 条",
            "record_count": len(df),
            "added_count": len(new_records),
            "failed_count": len(failed_records),
            "failed_records": failed_records,
            "new_records": new_records if len(new_records) <= 5 else new_records[:5]  # 限制返回的新记录数量
        }
        
    except Exception as e:
        return {"success": False, "message": f"添加交易记录时出错: {str(e)}"}


def batch_add_transaction_records_from_file(file_path, case_index=None, case_name=None, case_time=None):
    """
    从Excel文件批量添加交易记录
    兼容带\t和不带\t的列名格式
    
    Args:
        file_path (str): Excel文件路径
        case_index (str, optional): 案件索引
        case_name (str, optional): 案件名称
        case_time (str, optional): 案件时间
    
    Returns:
        dict: 包含操作结果的消息
    """
    try:
        import pandas as pd
        
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 定义所有可能的列名（必填+选填）
        all_possible_columns = [
            # 必填字段
            '交易卡号', '交易账号', '交易方户名', '交易时间', 
            '交易金额', '交易余额', '交易币种', '借贷标志',
            # 选填字段（对手信息）
            '对手卡号', '对手账号', '对手户名', '对手证件号',
            '对手账户开户银行', '对手交易余额',
            '对手所属省份', '对手所属城市', '对手所属地区',
            # 其他常用字段
            '交易方证件号', '交易账户开户银行', '交易方式',
            '交易银行名', '交易网点号', '摘要说明', '现金标志',
            '交易是否成功', '交易类型', 'IP地址', 'MAC地址',
            '交易渠道', '交易场所', '交易发生地', '传票号',
            '交易记录ID', '报告机构', '代办人名称', '代办人证件号码',
            '查询反馈结果原因', '交易名称所属国家',
            '交易方所属省份', '交易方所属城市', '交易方所属地区',
            '交易流水号', '备注', '批次'
        ]
        
        # 检查必要列是否存在
        required_columns = [
            '交易卡号', '交易账号', '交易方户名', '交易时间', 
            '交易金额', '交易余额', '交易币种', '借贷标志'
        ]
        
        missing_columns = []
        for col in required_columns:
            if col not in df.columns and f'\t{col}' not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            return {
                "success": False, 
                "message": f"Excel文件缺少必要列: {', '.join(missing_columns)}",
                "added_count": 0,
                "failed_count": len(df)
            }
        
        # 统一处理列名：将所有带\t的列名转换为不带\t的格式
        column_mapping = {}
        for col in df.columns:
            if col.startswith('\t'):
                clean_col = col.lstrip('\t')
                column_mapping[col] = clean_col
        
        if column_mapping:
            df.rename(columns=column_mapping, inplace=True)
            print(f"列名清理: 将 {len(column_mapping)} 个带\\t的列名转换为标准格式")
            print(f"清理的列名: {list(column_mapping.values())}")
        
        # 同时清理数据内容中的\t
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(lambda x: x.lstrip('\t') if isinstance(x, str) and x.startswith('\t') else x)
        
        # 转换为字典列表
        records_list = df.to_dict('records')
        
        # 使用现有的add_transaction_record函数处理，传递案件参数
        result = add_transaction_record(records_list, case_index, case_name, case_time)
        
        return result
        
    except Exception as e:
        return {"success": False, "message": f"从文件批量添加交易记录时出错: {str(e)}", "added_count": 0, "failed_count": 0}


def delete_transaction_record_by_data(transaction_data):
    """
    根据交易记录的具体信息删除记录
    
    Args:
        transaction_data (dict): 包含用于识别交易记录的字段的字典
            如: {'交易卡号': '1234567890123456', '交易方户名': '张三', 
                 '交易时间': '2023-01-01 10:00:00', '交易金额': 1000.00}
    
    Returns:
        dict: 包含操作结果的消息
    """
    try:
        # Excel文件路径
        excel_file_path = r'../建模数据121.xlsx'
        
        # 调试信息
        current_dir = os.getcwd()
        print(f'当前工作目录: {current_dir}')
        print(f'相对路径: {excel_file_path}')
        print(f'相对路径存在: {os.path.exists(excel_file_path)}')
        
        # 如果相对路径不存在，尝试绝对路径
        if not os.path.exists(excel_file_path):
            excel_file_path = r'C:\Users\sanjin\Desktop\新建文件夹\建模数据121.xlsx'
            print(f'使用绝对路径: {excel_file_path}')
            print(f'绝对路径存在: {os.path.exists(excel_file_path)}')
            
        # 再次检查文件是否存在
        if not os.path.exists(excel_file_path):
            return {"success": False, "message": f"Excel文件不存在: {excel_file_path}"}
        
        # 读取现有的Excel数据
        df = pd.read_excel(excel_file_path, engine='openpyxl')
        
        # 获取原始记录数
        original_count = len(df)
        
        #根据提供的标识符查找并删除记录
        #首先尝试匹配所有提供的字段
        mask = pd.Series([True] * len(df), dtype=bool)
                
        print(f"接收到的删除数据: {transaction_data}")
        print(f"DataFrame列名: {list(df.columns)[:10]}")
                
        for key, value in transaction_data.items():
            if value and str(value).strip():  # 只有当值不为空时才进行匹配
                print(f"处理字段: {key} = {value}")
                if key == '交易时间':
                    # 如果是时间字段，需要特别处理
                    column_name = '	交易时间'
                    clean_value = str(value).lstrip('\t')
                    print(f"原始时间值: {repr(value)},清理后: {repr(clean_value)}")
                    print(f"时间列前5个值: {df[column_name].head().tolist()}")
                    
                    try:
                        #尝多种时间格式解析
                        search_time = pd.to_datetime(clean_value, format='mixed')
                        df_time_col = pd.to_datetime(df[column_name], format='mixed')
                        #比较时间（精确到分钟）
                        time_diff = abs((df_time_col - search_time).dt.total_seconds())
                        time_mask = (time_diff <= 60)  # 1分钟内的都认为是同一时间
                        mask = mask & time_mask
                        print(f"时间匹配结果: {time_mask.sum()}条记录匹配")
                    except Exception as e:
                        print(f"时间转换错误: {e}")
                        # 如果转换失败，尝试字符串匹配
                        str_mask = df[column_name].astype(str).str.lstrip('\t').str.contains(clean_value, na=False)
                        mask = mask & str_mask
                        print(f"字符串时间匹配结果: {str_mask.sum()}条记录匹配")
                        if str_mask.sum() > 0:
                            matched_records = df[str_mask]
                            print("时间匹配的记录示例:")
                            for idx, record in matched_records.head(2).iterrows():
                                print(f"  {idx}: {record[column_name]}")
                elif key in ['交易卡号', '交易账号', '交易方户名', '交易金额', '借贷标志']:
                    #直接匹配，处理可能的制表符前缀
                    column_name = f'	{key}'
                    #检查列是否存在
                    if column_name not in df.columns:
                        print(f"警告:列 {column_name} 不存在于DataFrame中")
                        print(f"可用列: {list(df.columns)[:10]}")
                        continue
                    
                    #移除value中的制表符前缀进行匹配
                    clean_value = str(value).lstrip('\t')
                    print(f"原始值: {repr(value)},清理后: {repr(clean_value)}")
                    print(f"列 {column_name} 的前5个值: {df[column_name].head().tolist()}")
                    
                    # 检查数据类型
                    if key == '交易金额':
                        # 金额字段需要数值比较
                        try:
                            target_amount = float(clean_value)
                            field_mask = abs(df[column_name] - target_amount) < 0.01  #允小的浮点误差
                        except:
                            field_mask = df[column_name].astype(str).str.lstrip('\t') == clean_value
                    else:
                        # 使用lstrip而不是rstrip来移除开头的制表符
                        field_mask = df[column_name].astype(str).str.lstrip('\t') == clean_value
                    
                    mask = mask & field_mask
                    print(f"{key}字段匹配结果: {field_mask.sum()}条记录匹配")
                    if field_mask.sum() > 0:
                        matched_records = df[field_mask]
                        print("匹配的记录示例:")
                        for idx, record in matched_records.head(2).iterrows():
                            print(f"  {idx}: {record[column_name]}")
                else:
                    print(f"未知字段: {key}")
        
        # 获取匹配的行索引
        matched_indices = df[mask].index.tolist()
        
        print(f"总匹配结果: {len(matched_indices)}条记录")
        if len(matched_indices) > 0:
            print(f"匹配的索引: {matched_indices}")
            #显示匹配的记录详情
            print("匹配的记录详情:")
            for idx in matched_indices[:3]:  #只显示前3条
                record = df.iloc[idx]
                print(f"  {idx}: 交易方户名='{record['	交易方户名']}', 金额={record['	交易金额']}, 时间='{record['	交易时间']}'")
        
        if not matched_indices:
            return {"success": False, "message": "未找到匹配的交易记录"}
        
        # 删除匹配的行
        df = df.drop(index=matched_indices).reset_index(drop=True)
        
        # 保存回Excel文件
        try:
            print(f"准备保存文件到: {excel_file_path}")
            df.to_excel(excel_file_path, index=False, engine='openpyxl')
            print("文件保存成功")
        except Exception as save_error:
            print(f"文件保存失败: {save_error}")
            return {"success": False, "message": f"保存文件时出错: {str(save_error)}"}
        
        deleted_count = len(matched_indices)
        return {
            "success": True, 
            "message": f"成功删除 {deleted_count} 条交易记录",
            "original_count": original_count,
            "new_count": len(df),
            "deleted_indices": matched_indices
        }
        
    except Exception as e:
        return {"success": False, "message": f"删除交易记录时出错: {str(e)}"}


def validate_transaction_data(transaction_data):
    """
    验证交易数据的格式
    
    Args:
        transaction_data (dict): 交易数据
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # 验证必填字段
    required_fields = [
        '交易卡号', '交易账号', '交易方户名', '交易时间', 
        '交易金额', '交易余额', '交易币种', '借贷标志'
    ]
    
    for field in required_fields:
        if field not in transaction_data or not str(transaction_data[field]).strip():
            return False, f"字段 '{field}' 是必填的"
    
    # 验证数据类型
    try:
        # 验证交易金额和交易余额是否为数字
        float(transaction_data['交易金额'])
        float(transaction_data['交易余额'])
    except ValueError:
        return False, "交易金额和交易余额必须是数字"
    
    # 验证交易时间格式
    try:
        # 尝试解析交易时间
        pd.to_datetime(transaction_data['交易时间'])
    except:
        return False, "交易时间格式无效，应为 YYYY-MM-DD HH:MM 格式"
    
    # 验证借贷标志
    if transaction_data['借贷标志'] not in ['进', '出']:
        return False, "借贷标志只能是 '进' 或 '出'"
    
    # 验证交易币种
    valid_currencies = ['人民币', '美元', '欧元', '港币']
    if transaction_data['交易币种'] not in valid_currencies:
        return False, f"交易币种只能是: {', '.join(valid_currencies)}"
    
    return True, ""


def add_invoice_record(invoice_data):
    """
    将发票记录添加到发票Excel文件中
    
    Args:
        invoice_data (dict): 包含发票记录数据的字典
            必填字段: '开票日期', '发票类型', '销售方', '购买方', '价税合计'
            选填字段: '商品类别', '商品名称', '数量', '单价', '金额(不含税)', 
                    '税率', '税额', '销售方开户行', '销售方银行账号', 
                    '购买方开户行', '购买方银行账号', '发票状态', '备注'
            可选字段: 'caseIndex', 'caseName', 'caseTime' (用于案件文件夹)
    
    Returns:
        dict: 包含操作结果的消息
    """
    try:
        # 获取案件参数
        case_index = invoice_data.get('caseIndex')
        case_name = invoice_data.get('caseName')
        case_time = invoice_data.get('caseTime')
        
        # 确定发票文件路径
        if case_index and case_name and case_time:
            # 生成案件文件夹名称
            folder_name = f"{case_time}_{case_name}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            
            # 构建案件文件夹路径
            current_file = __file__
            print(f'当前文件路径: {current_file}')
            
            current_dir = os.path.dirname(current_file)
            print(f'当前目录: {current_dir}')
            
            parent_dir = os.path.dirname(current_dir)
            print(f'父目录: {parent_dir}')
            
            case_folder = os.path.join(parent_dir, 'cases', folder_name)
            print(f'案件文件夹路径: {case_folder}')
            
            # 构建发票文件路径
            invoice_file_path = os.path.join(case_folder, '销项整理后.xlsx')
            print(f'发票文件路径: {invoice_file_path}')
            
            # 确保案件文件夹存在
            if not os.path.exists(case_folder):
                try:
                    os.makedirs(case_folder, exist_ok=True)
                    print(f'创建案件文件夹成功: {case_folder}')
                except Exception as e:
                    print(f'创建案件文件夹失败: {str(e)}')
            else:
                print(f'案件文件夹已存在: {case_folder}')
            
            # 如果发票文件不存在，创建一个新的
            if not os.path.exists(invoice_file_path):
                try:
                    # 创建一个新的DataFrame
                    df = pd.DataFrame({
                        '发票代码': [],
                        '发票号码': [],
                        '发票ID': [],
                        '开票日期': [],
                        '发票类型': [],
                        '销售方': [],
                        '购买方': [],
                        '商品类别': [],
                        '商品名称': [],
                        '数量': [],
                        '单价': [],
                        '金额(不含税)': [],
                        '税率': [],
                        '税额': [],
                        '价税合计': [],
                        '销售方开户行': [],
                        '销售方银行账号': [],
                        '购买方开户行': [],
                        '购买方银行账号': [],
                        '发票状态': [],
                        '备注': []
                    })
                    # 保存到文件
                    df.to_excel(invoice_file_path, index=False, engine='openpyxl')
                    print(f'创建新的发票文件成功: {invoice_file_path}')
                except Exception as e:
                    print(f'创建发票文件失败: {str(e)}')
                    # 如果创建失败，使用默认路径
                    invoice_file_path = r'C:\Users\sanjin\Desktop\新建文件夹\销项整理后.xlsx'
                    print(f'使用默认路径: {invoice_file_path}')
                    if os.path.exists(invoice_file_path):
                        df = pd.read_excel(invoice_file_path, engine='openpyxl')
                    else:
                        return {"success": False, "message": f"无法创建或找到发票文件: {str(e)}"}
            else:
                # 读取现有的发票Excel数据
                try:
                    df = pd.read_excel(invoice_file_path, engine='openpyxl')
                    print(f'读取现有发票文件成功: {invoice_file_path}')
                except Exception as e:
                    print(f'读取发票文件失败: {str(e)}')
                    return {"success": False, "message": f"读取发票文件时出错: {str(e)}"}
        else:
            # 使用默认路径
            invoice_file_path = r'../销项整理后.xlsx'
            
            # 调试信息
            current_dir = os.getcwd()
            print(f'当前工作目录: {current_dir}')
            print(f'发票文件路径: {invoice_file_path}')
            print(f'发票文件路径存在: {os.path.exists(invoice_file_path)}')
            
            # 如果路径不存在，尝试绝对路径
            if not os.path.exists(invoice_file_path):
                # 尝试默认绝对路径
                invoice_file_path = r'C:\Users\sanjin\Desktop\新建文件夹\销项整理后.xlsx'
                print(f'使用默认绝对路径: {invoice_file_path}')
                print(f'默认绝对路径存在: {os.path.exists(invoice_file_path)}')
                
            # 再次检查文件是否存在
            if not os.path.exists(invoice_file_path):
                return {"success": False, "message": f"发票Excel文件不存在: {invoice_file_path}"}
            
            # 读取现有的发票Excel数据
            df = pd.read_excel(invoice_file_path, engine='openpyxl')
        
        # 验证必填字段 - 需要检查前端字段名而不是Excel列名
        required_fields_map = {
            'invoiceDate': '开票日期',
            'invoiceType': '发票类型',
            'sellerName': '销售方',
            'buyerName': '购买方',
            'totalAmount': '价税合计'
        }
        
        missing_fields = []
        for form_field, excel_field in required_fields_map.items():
            if form_field not in invoice_data or not str(invoice_data[form_field]).strip():
                missing_fields.append(excel_field)
        
        if missing_fields:
            return {"success": False, "message": f"缺少必填字段: {', '.join(missing_fields)}"}
        
        # 创建新的发票记录
        new_record = {}
        
        # Excel中的发票列名（根据实际发票Excel文件结构）
        excel_invoice_columns = [
            '发票代码', '发票号码', '发票ID', '开票日期', '发票类型', '销售方', '购买方', 
            '商品类别', '商品名称', '数量', '单价', '金额(不含税)', '税率', '税额', 
            '价税合计', '销售方开户行', '销售方银行账号', '购买方开户行', '购买方银行账号', 
            '发票状态', '备注'
        ]
        
        # 初始化新记录的字典，所有字段默认为空字符串
        for col in excel_invoice_columns:
            new_record[col] = ''
        
        # 映射前端字段到Excel列名
        field_mapping = {
            'invoiceDate': '开票日期',
            'invoiceType': '发票类型',
            'sellerName': '销售方',
            'buyerName': '购买方',
            'productCategory': '商品类别',
            'productName': '商品名称',
            'quantity': '数量',
            'unitPrice': '单价',
            'amountWithoutTax': '金额(不含税)',
            'taxRate': '税率',
            'taxAmount': '税额',
            'totalAmount': '价税合计',
            'sellerBank': '销售方开户行',
            'sellerBankAccount': '销售方银行账号',
            'buyerBank': '购买方开户行',
            'buyerBankAccount': '购买方银行账号',
            'invoiceStatus': '发票状态',
            'remark': '备注',
            # 如果字段名相同，则直接对应
            '开票日期': '开票日期',
            '发票类型': '发票类型',
            '销售方': '销售方',
            '购买方': '购买方',
            '商品类别': '商品类别',
            '商品名称': '商品名称',
            '数量': '数量',
            '单价': '单价',
            '金额(不含税)': '金额(不含税)',
            '税率': '税率',
            '税额': '税额',
            '价税合计': '价税合计',
            '销售方开户行': '销售方开户行',
            '销售方银行账号': '销售方银行账号',
            '购买方开户行': '购买方开户行',
            '购买方银行账号': '购买方银行账号',
            '发票状态': '发票状态',
            '备注': '备注'
        }
        
        # 填充数据
        for form_field, excel_col in field_mapping.items():
            if form_field in invoice_data:
                new_record[excel_col] = invoice_data[form_field]
        
        # 将新记录添加到DataFrame
        df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
        
        # 保存回发票Excel文件
        try:
            print(f"准备保存发票文件到: {invoice_file_path}")
            # 添加重试机制，以防文件被占用
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    df.to_excel(invoice_file_path, index=False, engine='openpyxl')
                    print("发票文件保存成功")
                    break
                except PermissionError as pe:
                    print(f"第{retry_count + 1}次尝试保存失败，文件可能被占用: {pe}")
                    retry_count += 1
                    time.sleep(1)  # 等待1秒后重试
                    if retry_count >= max_retries:
                        raise pe
        except Exception as save_error:
            print(f"发票文件保存失败: {save_error}")
            return {"success": False, "message": f"保存发票文件时出错: {str(save_error)}"}
        
        return {
            "success": True, 
            "message": "发票记录添加成功!",
            "record_count": len(df),
            "new_record": new_record
        }
        
    except Exception as e:
        return {"success": False, "message": f"添加发票记录时出错: {str(e)}"}


def validate_invoice_data(invoice_data):
    """
    验证发票数据的格式
    
    Args:
        invoice_data (dict): 发票数据
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # 验证必填字段（前端字段名）
    required_fields = ['invoiceDate', 'invoiceType', 'sellerName', 'buyerName', 'totalAmount']
    
    for field in required_fields:
        if field not in invoice_data or not str(invoice_data[field]).strip():
            field_names_map = {
                'invoiceDate': '开票日期',
                'invoiceType': '发票类型',
                'sellerName': '销售方',
                'buyerName': '购买方',
                'totalAmount': '价税合计'
            }
            return False, f"字段 '{field_names_map.get(field, field)}' 是必填的"
    
    # 验证数据类型
    try:
        # 验证价税合计、税额、金额(不含税)、单价、数量是否为数字（前端字段名）
        float(invoice_data.get('totalAmount', 0))
        float(invoice_data.get('taxAmount', 0) or 0)
        float(invoice_data.get('amountWithoutTax', 0) or 0)
        float(invoice_data.get('unitPrice', 0) or 0)
        float(invoice_data.get('quantity', 0) or 0)
    except ValueError:
        return False, "价税合计、税额、金额(不含税)、单价、数量必须是数字"
    
    # 验证开票日期格式
    try:
        # 尝试解析开票日期（前端字段名）
        pd.to_datetime(invoice_data['invoiceDate'])
    except:
        return False, "开票日期格式无效，应为 YYYY-MM-DD 格式"
    
    # 验证发票类型
    valid_invoice_types = ['增值税专用发票', '增值税普通发票', '电子发票', '机动车销售统一发票', '其他']
    if invoice_data['invoiceType'] not in valid_invoice_types:
        return False, f"发票类型只能是: {', '.join(valid_invoice_types)}"
    
    # 验证发票状态
    valid_status = ['已开票', '已认证', '已抵扣', '已作废', '正常']
    if invoice_data.get('invoiceStatus') and invoice_data['invoiceStatus'] not in valid_status:
        return False, f"发票状态只能是: {', '.join(valid_status)}"
    
    return True, ""


def delete_invoice_record(invoice_identifier):
    """
    从发票Excel文件中删除指定的发票记录
    
    Args:
        invoice_identifier (dict): 包含用于识别发票记录的字段的字典
            如: {'invoiceDate': '2023-01-01', 'sellerName': '销售方名称', 
                 'buyerName': '购买方名称', 'totalAmount': 1000.00}
    
    Returns:
        dict: 包含操作结果的消息
    """
    try:
        # 发票Excel文件路径
        invoice_file_path = r'../发票.xlsx'
        
        # 调试信息
        current_dir = os.getcwd()
        print(f'当前工作目录: {current_dir}')
        print(f'发票文件相对路径: {invoice_file_path}')
        print(f'发票文件相对路径存在: {os.path.exists(invoice_file_path)}')
        
        # 如果相对路径不存在，尝试绝对路径
        if not os.path.exists(invoice_file_path):
            invoice_file_path = r'C:\Users\sanjin\Desktop\新建文件夹\发票.xlsx'
            print(f'使用发票文件绝对路径: {invoice_file_path}')
            print(f'发票文件绝对路径存在: {os.path.exists(invoice_file_path)}')
            
        # 再次检查文件是否存在
        if not os.path.exists(invoice_file_path):
            return {"success": False, "message": f"发票Excel文件不存在: {invoice_file_path}"}
        
        # 读取现有的发票Excel数据
        df = pd.read_excel(invoice_file_path, engine='openpyxl')
        
        # 获取原始记录数
        original_count = len(df)
        
        # 根据提供的标识符查找并删除记录
        # 首先尝试匹配所有提供的字段
        mask = pd.Series([True] * len(df), dtype=bool)
        
        for key, value in invoice_identifier.items():
            if value:  # 只有当值不为空时才进行匹配
                if key == 'invoiceDate':
                    # 如果是日期字段，需要特别处理
                    df_date_col = df['开票日期']
                    # 尝试将值转换为日期格式并与DataFrame中的日期比较
                    try:
                        search_date = pd.to_datetime(value).date()
                        # DataFrame中的日期也可能需要转换
                        df_date_col = pd.to_datetime(df['开票日期']).dt.date
                        mask = mask & (df_date_col == search_date)
                    except:
                        # 如果转换失败，尝试字符串匹配
                        mask = mask & (df['开票日期'].astype(str).str.contains(str(value), na=False))
                elif key in ['sellerName', 'buyerName', 'invoiceType']:
                    # 根据前端字段映射到Excel列名
                    excel_col = {
                        'sellerName': '销售方',
                        'buyerName': '购买方', 
                        'invoiceType': '发票类型'
                    }.get(key, key)
                    mask = mask & (df[excel_col].astype(str).str.contains(str(value), na=False))
                elif key == 'totalAmount':
                    # 金额字段需要数值比较
                    try:
                        search_amount = float(value)
                        mask = mask & (abs(pd.to_numeric(df['价税合计'], errors='coerce') - search_amount) < 0.01)
                    except:
                        # 如果转换失败，尝试字符串匹配
                        mask = mask & (df['价税合计'].astype(str).str.contains(str(value), na=False))
        
        # 获取匹配的行索引
        matched_indices = df[mask].index.tolist()
        
        if not matched_indices:
            return {"success": False, "message": "未找到匹配的发票记录"}
        
        # 删除匹配的行
        df = df.drop(index=matched_indices).reset_index(drop=True)
        
        # 添加重试机制，以防文件被占用
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                # 保存回发票Excel文件
                df.to_excel(invoice_file_path, index=False, engine='openpyxl')
                print("发票文件删除成功记录并保存成功")
                break
            except PermissionError as pe:
                print(f"第{retry_count + 1}次尝试保存失败，文件可能被占用: {pe}")
                retry_count += 1
                time.sleep(1)  # 等待1秒后重试
                if retry_count >= max_retries:
                    raise pe
        
        deleted_count = len(matched_indices)
        return {
            "success": True, 
            "message": f"成功删除 {deleted_count} 条发票记录",
            "original_count": original_count,
            "new_count": len(df),
            "deleted_indices": matched_indices
        }
        
    except Exception as e:
        return {"success": False, "message": f"删除发票记录时出错: {str(e)}"}


# 测试函数
def test_add_transaction():
    """测试添加交易记录功能"""
    test_data = {
        '交易卡号': '1234567890123456',
        '交易账号': '6222021234567890123',
        '交易方户名': '张三',
        '交易时间': '2026-02-25 20:30:00',
        '交易金额': 10000.00,
        '交易余额': 50000.00,
        '交易币种': '人民币',
        '借贷标志': '出',
        '对手卡号': '9876543210987654',
        '对手账号': '6222023210987654321',
        '对手户名': '李四'
    }
    
    result = add_transaction_record(test_data)
    print(result)

def test_delete_transaction():
    """测试删除交易记录功能"""
    # 测试删除第一行记录（索引0）
    result = delete_transaction_record(0)
    print("删除测试结果:", result)
    
    # 测试删除一个不存在的行
    result = delete_transaction_record(9999)
    print("删除不存在行测试结果:", result)


def add_related_data_from_file(file_path, target_node):
    """
    从Excel文件中提取与目标节点相关的数据并追加到主数据文件
    
    Args:
        file_path (str): 上传的Excel文件路径
        target_node (str): 目标节点名称（即当前查看的账户）
    
    Returns:
        dict: 包含操作结果的消息
    """
    try:
        # 主数据文件路径
        main_file_path = r'C:\Users\sanjin\Desktop\新建文件夹\建模数据121.xlsx'
        
        # 检查主数据文件是否存在
        if not os.path.exists(main_file_path):
            return {"success": False, "message": f"主数据文件不存在: {main_file_path}"}
        
        # 读取上传的Excel文件
        uploaded_df = pd.read_excel(file_path, engine='openpyxl')
        
        # 读取主数据文件
        main_df = pd.read_excel(main_file_path, engine='openpyxl')
        
        # 智能检测列名格式，兼容带制表符和不带制表符的列名
        def find_column(df, possible_names):
            """查找DataFrame中存在的列名"""
            for name in possible_names:
                if name in df.columns:
                    return name
            return None
        
        # 查找必要的列（兼容带制表符和不带制表符的格式）
        sender_col = find_column(uploaded_df, ['\t交易方户名', '交易方户名'])
        receiver_col = find_column(uploaded_df, ['\t对手户名', '对手户名'])
        time_col = find_column(uploaded_df, ['\t交易时间', '交易时间'])
        amount_col = find_column(uploaded_df, ['\t交易金额', '交易金额'])
        balance_col = find_column(uploaded_df, ['\t交易余额', '交易余额'])
        currency_col = find_column(uploaded_df, ['\t交易币种', '交易币种'])
        debit_credit_col = find_column(uploaded_df, ['\t借贷标志', '借贷标志'])
        
        # 检查是否找到所有必要的列
        missing_columns = []
        if sender_col is None:
            missing_columns.append('交易方户名 (可能为 \t交易方户名 或 交易方户名)')
        if receiver_col is None:
            missing_columns.append('对手户名 (可能为 \t对手户名 或 对手户名)')
        if time_col is None:
            missing_columns.append('交易时间 (可能为 \t交易时间 或 交易时间)')
        if amount_col is None:
            missing_columns.append('交易金额 (可能为 \t交易金额 或 交易金额)')
        if balance_col is None:
            missing_columns.append('交易余额 (可能为 \t交易余额 或 交易余额)')
        if currency_col is None:
            missing_columns.append('交易币种 (可能为 \t交易币种 或 交易币种)')
        if debit_credit_col is None:
            missing_columns.append('借贷标志 (可能为 \t借贷标志 或 借贷标志)')
        
        if missing_columns:
            return {
                "success": False, 
                "message": f"上传的Excel文件缺少必要列: {', '.join(missing_columns)}",
                "available_columns": list(uploaded_df.columns)[:20],  # 返回前20个可用列名作为参考
                "added_count": 0
            }
        
        # 查找与目标节点相关的记录
        # 处理目标节点可能包含或不包含制表符的情况
        target_node_clean = target_node.lstrip('\t')  # 移除可能的制表符前缀
        target_node_with_tab = '\t' + target_node_clean  # 添加制表符前缀
        
        # 使用更灵活的匹配策略，支持通配符
        def flexible_match(series, target):
            # 移除系列中的制表符前缀进行匹配
            series_clean = series.astype(str).str.lstrip('\t')
            # 处理目标字符串，将*替换为.*以支持通配符匹配
            # 转义特殊字符，但保留*作为通配符
            pattern = re.escape(target).replace('\\*', '.*')
            # 检查是否匹配模式（不区分前后是否有制表符）
            return series_clean.str.contains(pattern, na=False, regex=True, case=False)
        
        # 检查目标节点是否在交易方户名或对手户名列中，使用找到的正确列名
        target_mask = (
            flexible_match(uploaded_df[sender_col], target_node_clean) |
            flexible_match(uploaded_df[receiver_col], target_node_clean)
        )
        
        # 提取相关记录
        related_records = uploaded_df[target_mask].copy()
        
        if len(related_records) == 0:
            # 提供更详细的信息，帮助用户了解为什么找不到匹配项
            unique_sender_names = uploaded_df[sender_col].astype(str).str.lstrip('\t').unique()[:10]  # 只显示前10个
            unique_receiver_names = uploaded_df[receiver_col].astype(str).str.lstrip('\t').unique()[:10]  # 只显示前10个
            
            return {
                "success": False,
                "message": f"在上传的文件中未找到与 '{target_node.lstrip('\\t')}' 相关的交易记录。"+
                         f" 上传文件中的部分交易方户名: {list(unique_sender_names)}..."+
                         f" 上传文件中的部分对手户名: {list(unique_receiver_names)}...",
                "added_count": 0
            }
        
        print(f"找到 {len(related_records)} 条与 '{target_node}' 相关的记录")
        
        # 将相关记录追加到主数据文件
        combined_df = pd.concat([main_df, related_records], ignore_index=True)
        
        # 添加重试机制，以防文件被占用
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                combined_df.to_excel(main_file_path, index=False, engine='openpyxl')
                print(f"成功将 {len(related_records)} 条记录追加到主数据文件")
                break  # 成功保存，跳出重试循环
            except PermissionError as pe:
                print(f"第{retry_count + 1}次尝试保存失败，文件可能被占用: {pe}")
                retry_count += 1
                time.sleep(1)  # 等待1秒后重试
                if retry_count >= max_retries:
                    return {"success": False, "message": f"保存文件时出错: {str(pe)}", "added_count": 0}
            except Exception as save_error:
                print(f"保存文件失败: {save_error}")
                return {"success": False, "message": f"保存文件时出错: {str(save_error)}", "added_count": 0}
        
        return {
            "success": True,
            "message": f"成功将 {len(related_records)} 条与 '{target_node}' 相关的记录追加到主数据文件",
            "added_count": len(related_records),
            "total_records": len(combined_df)
        }
        
    except Exception as e:
        return {"success": False, "message": f"处理相关数据文件时出错: {str(e)}", "added_count": 0}


if __name__ == "__main__":
    print("=== 测试添加交易记录 ===")
    test_add_transaction()
    print("\n=== 测试删除交易记录 ===")
    test_delete_transaction()