import pandas as pd
import json
import os
from datetime import datetime

def load_alerts_from_localstorage():
    """
    从localStorage格式的JSON文件中加载预警数据
    """
    try:
        # 假设预警数据存储在前端的localStorage中，这里模拟读取
        # 在实际应用中，这部分数据应该从前端传递过来
        alerts_data = [
            {
                "id": 12345,
                "nodeId": "测试账户",
                "type": "amount_threshold",
                "amountThreshold": 1000000,
                "description": "测试大额交易预警",
                "level": "high",
                "createTime": "2026-02-25T10:00:00Z",
                "status": "active"
            }
        ]
        return alerts_data
    except Exception as e:
        print(f"加载预警数据时出错: {e}")
        return []

def get_excel_data(file_path=r"C:\Users\sanjin\Desktop\新建文件夹\建模数据121.xlsx"):
    """
    读取原始Excel数据
    """
    try:
        excel_file = pd.ExcelFile(file_path)
        all_sheets_data = {}
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            all_sheets_data[sheet_name] = df
        
        return all_sheets_data
    except Exception as e:
        print(f"读取Excel文件时出错: {e}")
        return None

def filter_data_by_alerts(excel_data, alerts):
    """
    根据预警条件筛选相关数据
    """
    filtered_data = {}
    
    for sheet_name, df in excel_data.items():
        filtered_data[sheet_name] = []
        
        for alert in alerts:
            if alert['status'] != 'active':
                continue
                
            # 根据预警类型筛选数据
            if alert['type'] == 'amount_threshold':
                # 筛选金额超过阈值的交易
                amount_column = None
                # 尝试找到金额相关的列
                for col in df.columns:
                    if '金额' in col or 'amount' in col.lower() or '交易' in col:
                        amount_column = col
                        break
                
                if amount_column:
                    try:
                        # 筛选大于阈值的数据
                        threshold_data = df[df[amount_column] >= alert['amountThreshold']]
                        if not threshold_data.empty:
                            filtered_data[sheet_name].append({
                                'alert_info': alert,
                                'filtered_rows': threshold_data.to_dict(orient='records')
                            })
                    except Exception as e:
                        print(f"筛选数据时出错: {e}")
                        continue
    
    return filtered_data

def export_frontend_alerts_to_excel(frontend_alerts_data, output_file=r"C:\Users\sanjin\Desktop\新建文件夹\预警.xlsx"):
    """
    将前端的预警数据导出到Excel文件
    
    Args:
        frontend_alerts_data: 前端传入的预警数据（JSON格式）
        output_file: 输出Excel文件路径
    
    Returns:
        str: 输出文件路径，如果失败返回None
    """
    try:
        # 解析前端数据
        if isinstance(frontend_alerts_data, str):
            alerts = json.loads(frontend_alerts_data)
        else:
            alerts = frontend_alerts_data
        
        # 准备数据结构
        alert_records = []
        
        # 风险级别映射
        level_mapping = {
            'low': '低风险',
            'medium': '中风险', 
            'high': '高风险',
            'critical': '严重风险'
        }
        
        # 预警类型映射
        type_mapping = {
            'amount_threshold': '金额阈值预警',
            'frequency_threshold': '频率异常预警',
            'suspicious_pattern': '可疑模式预警',
            'blacklist_match': '黑名单匹配预警'
        }
        
        # 转换数据格式
        for alert in alerts:
            record = {
                '预警ID': alert.get('id', ''),
                '账户名称': alert.get('nodeId', ''),
                '预警类型': type_mapping.get(alert.get('type', ''), '自定义预警'),
                '风险级别': level_mapping.get(alert.get('level', ''), alert.get('level', '')),
                '金额阈值(元)': alert.get('amountThreshold', 'N/A'),
                '预警描述': alert.get('description', ''),
                '创建时间': alert.get('createTime', ''),
                '状态': '激活' if alert.get('status') == 'active' else alert.get('status', ''),
                '预警编号': f"ALERT_{alert.get('id', '')}"
            }
            alert_records.append(record)
        
        # 创建DataFrame
        df = pd.DataFrame(alert_records)
        
        # 按创建时间排序
        if '创建时间' in df.columns and not df.empty:
            df['创建时间'] = pd.to_datetime(df['创建时间'], errors='coerce')
            df = df.sort_values('创建时间', ascending=False).reset_index(drop=True)
            df['创建时间'] = df['创建时间'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存到Excel
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 主要预警数据表
            df.to_excel(writer, sheet_name='预警信息', index=False)
            
            # 添加统计汇总表
            summary_data = {
                '统计项目': [
                    '总预警数量',
                    '高风险预警数',
                    '中风险预警数', 
                    '低风险预警数',
                    '严重风险预警数',
                    '激活状态预警数',
                    '最早创建时间',
                    '最新创建时间'
                ],
                '数值': [
                    len(alerts),
                    len([a for a in alerts if a.get('level') == 'high']),
                    len([a for a in alerts if a.get('level') == 'medium']),
                    len([a for a in alerts if a.get('level') == 'low']),
                    len([a for a in alerts if a.get('level') == 'critical']),
                    len([a for a in alerts if a.get('status') == 'active']),
                    min([a.get('createTime', '') for a in alerts if a.get('createTime')])[:19] if any(a.get('createTime') for a in alerts) else 'N/A',
                    max([a.get('createTime', '') for a in alerts if a.get('createTime')])[:19] if any(a.get('createTime') for a in alerts) else 'N/A'
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='统计汇总', index=False)
            
            # 按风险级别分类的详细表
            if '风险级别' in df.columns and not df.empty:
                risk_level_groups = df.groupby('风险级别')
                for level, group in risk_level_groups:
                    # 限制工作表名称长度
                    sheet_name = f'风险_{level}'[:31]  # Excel工作表名限制31字符
                    group.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"✅ 成功导出 {len(alerts)} 条预警信息到: {output_file}")
        print(f"📊 包含 {len(df.columns)} 个数据字段")
        return output_file
        
    except Exception as e:
        print(f"❌ 导出预警数据到Excel时出错: {e}")
        return None

def get_frontend_alerts_from_localstorage():
    """
    模拟从前端localStorage获取预警数据
    在实际应用中，这部分数据应该通过API从前端传递
    """
    # 这里模拟一些测试数据
    test_alerts = [
        {
            "id": 1708945200000,
            "nodeId": "山西圣煤炭物流贸易有限公司",
            "type": "amount_threshold",
            "amountThreshold": 1000000,
            "description": "大额交易监控预警",
            "level": "high",
            "createTime": "2024-02-26T10:00:00Z",
            "status": "active"
        },
        {
            "id": 1708945300000,
            "nodeId": "测试账户A",
            "type": "frequency_threshold",
            "amountThreshold": 500000,
            "description": "高频交易异常预警",
            "level": "medium",
            "createTime": "2024-02-26T11:30:00Z",
            "status": "active"
        },
        {
            "id": 1708945400000,
            "nodeId": "高风险客户B",
            "type": "suspicious_pattern",
            "amountThreshold": 2000000,
            "description": "可疑交易模式预警",
            "level": "critical",
            "createTime": "2024-02-26T14:15:00Z",
            "status": "active"
        }
    ]
    return test_alerts
    """
    创建预警Excel报告
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"预警报告_{timestamp}.xlsx"
    
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 创建汇总表
            summary_data = []
            for sheet_name, alerts_data in filtered_data.items():
                for alert_data in alerts_data:
                    alert_info = alert_data['alert_info']
                    row_count = len(alert_data['filtered_rows'])
                    summary_data.append({
                        '工作表': sheet_name,
                        '预警账户': alert_info['nodeId'],
                        '预警类型': '大额交易' if alert_info['type'] == 'amount_threshold' else alert_info['type'],
                        '阈值': alert_info.get('amountThreshold', 'N/A'),
                        '风险级别': alert_info['level'],
                        '匹配记录数': row_count,
                        '预警描述': alert_info['description'],
                        '创建时间': alert_info['createTime']
                    })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='预警汇总', index=False)
            
            # 为每个预警创建详细数据表
            sheet_counter = 1
            for sheet_name, alerts_data in filtered_data.items():
                for alert_data in alerts_data:
                    alert_info = alert_data['alert_info']
                    filtered_rows = alert_data['filtered_rows']
                    
                    if filtered_rows:
                        # 创建详细数据表
                        detail_df = pd.DataFrame(filtered_rows)
                        detail_sheet_name = f'预警详情_{sheet_counter}'
                        detail_df.to_excel(writer, sheet_name=detail_sheet_name, index=False)
                        sheet_counter += 1
        
        print(f"预警Excel报告已生成: {output_path}")
        return output_path
    except Exception as e:
        print(f"创建Excel报告时出错: {e}")
        return None

def generate_alert_report_from_frontend(alerts_json_data, excel_file_path=None):
    """
    从前端传入的预警数据生成Excel报告
    """
    try:
        # 解析前端传入的预警数据
        alerts = json.loads(alerts_json_data) if isinstance(alerts_json_data, str) else alerts_json_data
        
        # 获取Excel数据
        if excel_file_path is None:
            excel_file_path = r"C:\Users\sanjin\Desktop\新建文件夹\建模数据121.xlsx"
        
        excel_data = get_excel_data(excel_file_path)
        if not excel_data:
            return None
        
        # 根据预警筛选数据
        filtered_data = filter_data_by_alerts(excel_data, alerts)
        
        # 生成Excel报告
        output_path = create_alert_excel_report(filtered_data)
        return output_path
        
    except Exception as e:
        print(f"从前端数据生成报告时出错: {e}")
        return None

def main():
    """
    主函数 - 演示如何使用
    """
    print("=== 金融预警Excel报告生成器 ===")
    
    # 方法1: 使用默认数据生成报告
    print("\n1. 使用默认预警数据生成报告...")
    alerts = load_alerts_from_localstorage()
    excel_data = get_excel_data()
    
    if alerts and excel_data:
        filtered_data = filter_data_by_alerts(excel_data, alerts)
        output_file = create_alert_excel_report(filtered_data)
        if output_file:
            print(f"✅ 报告生成成功: {output_file}")
    
    # 方法2: 演示从前端数据生成
    print("\n2. 演示从前端数据生成报告...")
    frontend_alerts = json.dumps([
        {
            "id": 12346,
            "nodeId": "高风险账户A",
            "type": "amount_threshold",
            "amountThreshold": 500000,
            "description": "监控大额资金流动",
            "level": "high",
            "createTime": datetime.now().isoformat(),
            "status": "active"
        }
    ])
    
    output_file2 = generate_alert_report_from_frontend(frontend_alerts)
    if output_file2:
        print(f"✅ 前端数据报告生成成功: {output_file2}")
    
    # 方法3: 导出前端预警数据到指定Excel文件
    print("\n3. 导出前端预警数据到预警.xlsx...")
    frontend_alerts_data = get_frontend_alerts_from_localstorage()
    output_file3 = export_frontend_alerts_to_excel(frontend_alerts_data)
    if output_file3:
        print(f"✅ 预警数据导出成功: {output_file3}")

if __name__ == "__main__":
    main()