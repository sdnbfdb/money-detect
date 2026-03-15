import pandas as pd
import os
from datetime import datetime

# 获取当前文件所在目录的父目录（项目根目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

def read_invoice_data(file_path=None):
    """
    读取发票Excel文件数据
    
    Args:
        file_path (str): 发票Excel文件路径，支持相对路径和绝对路径
                        如果为 None，则使用默认的相对路径 '销项整理后.xlsx'
    
    Returns:
        dict:包含发票数据的字典，包括原始数据和统计信息
    """
    try:
        # 如果没有提供文件路径，使用默认相对路径
        if file_path is None:
            file_path = os.path.join(PARENT_DIR, '销项整理后.xlsx')
        elif not os.path.isabs(file_path):
            # 如果是相对路径，转换为绝对路径
            file_path = os.path.join(PARENT_DIR, file_path)
        
        #检查文件是否存在
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"发票文件不存在：{file_path}",
                "data": None,
                "stats": None
            }
        
        # 添加重试机制读取Excel数据，以防文件被占用
        max_retries = 3
        retry_count = 0
        df = None
        while retry_count < max_retries:
            try:
                df = pd.read_excel(file_path)
                break  # 成功读取，跳出重试循环
            except PermissionError as pe:
                print(f"第{retry_count + 1}次尝试读取文件失败，文件可能被占用: {pe}")
                retry_count += 1
                import time
                time.sleep(1)  # 等待1秒后重试
                if retry_count >= max_retries:
                    raise pe  # 如果达到最大重试次数仍失败，则抛出异常
            except Exception as e:
                print(f"读取Excel文件时出错: {e}")
                raise e
        
        # 数据预处理
        #处理日期列
        if '开票日期' in df.columns:
            df['开票日期'] = pd.to_datetime(df['开票日期'], errors='coerce')
        
        #处理金额列
        amount_columns = ['金额', '税额', '价税合计', '新价税合计']
        for col in amount_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        #为字典格式
        data = df.fillna('').to_dict(orient='records')
        
        # 生成统计信息
        stats = generate_invoice_statistics(df)
        
        return {
            "success": True,
            "error": None,
            "data": data,
            "total_rows": len(data),
            "columns": df.columns.tolist(),
            "stats": stats
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"读取发票数据时出错: {str(e)}",
            "data": None,
            "stats": None
        }

def generate_invoice_statistics(df):
    """
    生成发票数据统计信息
    
    Args:
        df (pandas.DataFrame): 发票数据DataFrame
    
    Returns:
        dict:统计信息字典
    """
    try:
        stats = {}
        
        #基本统计
        stats['total_count'] = len(df)
        stats['earliest_date'] = df['开票日期'].min().strftime('%Y-%m-%d') if '开票日期' in df.columns else 'N/A'
        stats['latest_date'] = df['开票日期'].max().strftime('%Y-%m-%d') if '开票日期' in df.columns else 'N/A'
        
        # 金额统计
        if '价税合计' in df.columns:
            stats['total_amount'] = float(df['价税合计'].sum())
            stats['average_amount'] = float(df['价税合计'].mean())
            stats['max_amount'] = float(df['价税合计'].max())
            stats['min_amount'] = float(df['价税合计'].min())
        elif '新价税合计' in df.columns:
            stats['total_amount'] = float(df['新价税合计'].sum())
            stats['average_amount'] = float(df['新价税合计'].mean())
            stats['max_amount'] = float(df['新价税合计'].max())
            stats['min_amount'] = float(df['新价税合计'].min())
        
        # 分类统计
        if '发票代码' in df.columns:
            stats['invoice_code_distribution'] = df['发票代码'].value_counts().to_dict()
        
        if '销方名称' in df.columns:
            stats['top_sellers'] = df['销方名称'].value_counts().head(10).to_dict()
        
        if '购方企业名称' in df.columns:
            stats['top_buyers'] = df['购方企业名称'].value_counts().head(10).to_dict()
        
        return stats
        
    except Exception as e:
        return {"error": f"生成统计信息时出错: {str(e)}"}

def find_column_in_df(df, possible_names):
    """在DataFrame中查找存在的列名"""
    for name in possible_names:
        if name in df.columns:
            return name
    # 如果都没找到，返回None
    return None

def filter_invoices_by_criteria(df, criteria):
    """
   根据条件筛选发票数据
   
    Args:
        df (pandas.DataFrame):原发票数据
        criteria (dict):筛条件字典
    
    Returns:
        pandas.DataFrame:筛后的数据
    """
    try:
        filtered_df = df.copy()
        
        # 智能检测列名（兼容带制表符和不带制表符的格式）
        invoice_code_col = find_column_in_df(filtered_df, ['\t发票代码', '发票代码'])
        invoice_number_col = find_column_in_df(filtered_df, ['\t发票号码', '发票号码'])
        seller_col = find_column_in_df(filtered_df, ['\t销方名称', '销方名称'])
        seller_tax_code_col = find_column_in_df(filtered_df, ['\t销方税号', '销方税号'])
        buyer_col = find_column_in_df(filtered_df, ['\t购方企业名称', '购方企业名称'])
        buyer_tax_code_col = find_column_in_df(filtered_df, ['\t购方税号', '购方税号'])
        amount_col = find_column_in_df(filtered_df, ['\t金额', '金额'])
        total_amount_col = find_column_in_df(filtered_df, ['\t价税合计', '价税合计'])
        new_total_amount_col = find_column_in_df(filtered_df, ['\t新价税合计', '新价税合计'])
        tax_amount_col = find_column_in_df(filtered_df, ['\t税额', '税额'])
        date_col = find_column_in_df(filtered_df, ['\t开票日期', '开票日期', '\t日期', '日期'])
        
        # 按发票代码筛选
        if 'invoice_code' in criteria and criteria['invoice_code']:
            if invoice_code_col:
                filtered_df = filtered_df[filtered_df[invoice_code_col] == criteria['invoice_code']]
        
        # 按发票号码筛选
        if 'invoice_number' in criteria and criteria['invoice_number']:
            if invoice_number_col:
                filtered_df = filtered_df[filtered_df[invoice_number_col].astype(str).str.strip().str.contains(criteria['invoice_number'], na=False, regex=False)]
        
        # 按销方名称筛选
        if 'seller' in criteria and criteria['seller']:
            if seller_col:
                # 去除空白字符并进行匹配，禁用正则表达式以处理特殊字符
                filtered_df = filtered_df[filtered_df[seller_col].astype(str).str.strip().str.contains(criteria['seller'], na=False, regex=False)]
        
        # 按销方税号筛选
        if 'seller_tax_code' in criteria and criteria['seller_tax_code']:
            if seller_tax_code_col:
                filtered_df = filtered_df[filtered_df[seller_tax_code_col].astype(str).str.strip().str.contains(criteria['seller_tax_code'], na=False, regex=False)]
        
        # 按购方企业名称筛选
        if 'buyer' in criteria and criteria['buyer']:
            if buyer_col:
                filtered_df = filtered_df[filtered_df[buyer_col].astype(str).str.strip().str.contains(criteria['buyer'], na=False, regex=False)]
        
        # 按购方税号筛选
        if 'buyer_tax_code' in criteria and criteria['buyer_tax_code']:
            if buyer_tax_code_col:
                filtered_df = filtered_df[filtered_df[buyer_tax_code_col].astype(str).str.strip().str.contains(criteria['buyer_tax_code'], na=False, regex=False)]
        
        # 按金额范围筛选
        if 'min_amount' in criteria and criteria['min_amount']:
            # 优先使用金额，如果不存在则使用价税合计，再使用新价税合计
            amount_col_final = amount_col if amount_col else total_amount_col if total_amount_col else new_total_amount_col if new_total_amount_col else None
            if amount_col_final:
                filtered_df = filtered_df[pd.to_numeric(filtered_df[amount_col_final], errors='coerce') >= float(criteria['min_amount'])]
        
        if 'max_amount' in criteria and criteria['max_amount']:
            # 优先使用金额，如果不存在则使用价税合计，再使用新价税合计
            amount_col_final = amount_col if amount_col else total_amount_col if total_amount_col else new_total_amount_col if new_total_amount_col else None
            if amount_col_final:
                filtered_df = filtered_df[pd.to_numeric(filtered_df[amount_col_final], errors='coerce') <= float(criteria['max_amount'])]
        
        # 按价税合计范围筛选
        if 'min_total_amount' in criteria and criteria['min_total_amount']:
            total_amount_col_final = total_amount_col if total_amount_col else new_total_amount_col if new_total_amount_col else amount_col if amount_col else None
            if total_amount_col_final:
                filtered_df = filtered_df[pd.to_numeric(filtered_df[total_amount_col_final], errors='coerce') >= float(criteria['min_total_amount'])]
        
        if 'max_total_amount' in criteria and criteria['max_total_amount']:
            total_amount_col_final = total_amount_col if total_amount_col else new_total_amount_col if new_total_amount_col else amount_col if amount_col else None
            if total_amount_col_final:
                filtered_df = filtered_df[pd.to_numeric(filtered_df[total_amount_col_final], errors='coerce') <= float(criteria['max_total_amount'])]
        
        # 按新价税合计范围筛选
        if 'min_new_total_amount' in criteria and criteria['min_new_total_amount']:
            new_total_amount_col_final = new_total_amount_col if new_total_amount_col else total_amount_col if total_amount_col else amount_col if amount_col else None
            if new_total_amount_col_final:
                filtered_df = filtered_df[pd.to_numeric(filtered_df[new_total_amount_col_final], errors='coerce') >= float(criteria['min_new_total_amount'])]
        
        if 'max_new_total_amount' in criteria and criteria['max_new_total_amount']:
            new_total_amount_col_final = new_total_amount_col if new_total_amount_col else total_amount_col if total_amount_col else amount_col if amount_col else None
            if new_total_amount_col_final:
                filtered_df = filtered_df[pd.to_numeric(filtered_df[new_total_amount_col_final], errors='coerce') <= float(criteria['max_new_total_amount'])]
        
        # 按税额范围筛选
        if 'min_tax_amount' in criteria and criteria['min_tax_amount']:
            tax_col_final = tax_amount_col if tax_amount_col else total_amount_col if total_amount_col else amount_col if amount_col else None
            if tax_col_final:
                filtered_df = filtered_df[pd.to_numeric(filtered_df[tax_col_final], errors='coerce') >= float(criteria['min_tax_amount'])]
        
        if 'max_tax_amount' in criteria and criteria['max_tax_amount']:
            tax_col_final = tax_amount_col if tax_amount_col else total_amount_col if total_amount_col else amount_col if amount_col else None
            if tax_col_final:
                filtered_df = filtered_df[pd.to_numeric(filtered_df[tax_col_final], errors='coerce') <= float(criteria['max_tax_amount'])]
        
        #按日期范围筛选
        if 'start_date' in criteria and criteria['start_date']:
            if date_col:
                start_date = pd.to_datetime(criteria['start_date'])
                filtered_df = filtered_df[pd.to_datetime(filtered_df[date_col], errors='coerce') >= start_date]
        
        if 'end_date' in criteria and criteria['end_date']:
            if date_col:
                end_date = pd.to_datetime(criteria['end_date'])
                filtered_df = filtered_df[pd.to_datetime(filtered_df[date_col], errors='coerce') <= end_date]
        
        return filtered_df
        
    except Exception as e:
        print(f"筛选发票数据时出错: {e}")
        return df

def get_invoice_summary(file_path=None):
    """
    获取发票数据摘要信息
    
    Args:
        file_path (str): 发票Excel文件路径，支持相对路径和绝对路径
                        如果为 None，则使用默认的相对路径 '销项整理后.xlsx'
    
    Returns:
        dict: 发票数据摘要
    """
    # 如果没有提供文件路径，使用默认相对路径
    if file_path is None:
        file_path = os.path.join(PARENT_DIR, '销项整理后.xlsx')
    elif not os.path.isabs(file_path):
        file_path = os.path.join(PARENT_DIR, file_path)
    
    result = read_invoice_data(file_path)
    
    if not result['success']:
        return result
    
    df = pd.DataFrame(result['data'])
    
    summary = {
        "success": True,
        "error": None,
        "文件信息": {
            "文件路径": file_path,
            "总记录数": result['total_rows'],
            "列数": len(result['columns']),
            "列名": result['columns']
        },
        "数据统计": result['stats'],
        "数据示例": result['data'][:3] if result['data'] else []
    }
    
    return summary

#测试函数
if __name__ == "__main__":
    print("=== 发票数据读取测试 ===")
    
    # 读取发票数据
    result = read_invoice_data()
    
    if result['success']:
        print(f"✅ 成功读取 {result['total_rows']}条记录")
        print(f"📊列名: {result['columns']}")
        
        #显示统计信息
        stats = result['stats']
        if stats:
            print(f"\n📈统计摘要:")
            print(f"总记录数: {stats.get('total_count', 'N/A')}")
            print(f"最早开票日期: {stats.get('earliest_date', 'N/A')}")
            print(f"最新开票日期: {stats.get('latest_date', 'N/A')}")
            if 'total_amount' in stats:
                print(f"总金额: ¥{stats['total_amount']:,.2f}")
            if 'average_amount' in stats:
                print(f"平均金额: ¥{stats['average_amount']:,.2f}")
            
            #显示发票代码分布
            if 'invoice_code_distribution' in stats:
                print(f"\n📋 发票代码分布:")
                for code, count in stats['invoice_code_distribution'].items():
                    print(f"  {code}: {count}张")
            
            #显示销售方Top10
            if 'top_sellers' in stats:
                print(f"\n🏷️ 销售方Top10:")
                for seller, count in list(stats['top_sellers'].items())[:10]:
                    print(f"  {seller}: {count}张")
            
            #显示购买方Top10
            if 'top_buyers' in stats:
                print(f"\n🛒 购买方Top10:")
                for buyer, count in list(stats['top_buyers'].items())[:10]:
                    print(f"  {buyer}: {count}张")
    else:
        print(f"❌ 读取失败: {result['error']}")