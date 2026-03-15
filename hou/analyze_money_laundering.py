import pandas as pd
import numpy as np
from datetime import datetime

# 读取Excel文件
file_path = "建模数据121.xlsx"
try:
    # 尝试读取所有工作表
    excel_file = pd.ExcelFile(file_path)
    print(f"Excel文件包含以下工作表: {excel_file.sheet_names}")
    
    # 读取第一个工作表
    df = pd.read_excel(file_path, sheet_name=0)
    print(f"\n数据形状: {df.shape}")
    print(f"列名: {list(df.columns)}")
    
    # 显示前几行数据
    print("\n前5行数据:")
    print(df.head())
    
    # 数据清洗和预处理
    # 重命名列以去除制表符
    df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
    df = df.rename(columns=lambda x: x.replace('\t', '').strip() if isinstance(x, str) else x)
    
    print(f"\n清理后的列名: {list(df.columns)}")
    
    # 分析潜在洗钱指标
    
    print("\n=== 潜在洗钱活动分析 ===")
    
    # 1. 大额交易分析
    if '交易金额' in df.columns:
        df['交易金额'] = pd.to_numeric(df['交易金额'], errors='coerce')
        large_transactions = df[df['交易金额'] > df['交易金额'].quantile(0.95)]
        print(f"\n1. 大额交易分析 (前5%)")
        print(f"大额交易笔数: {len(large_transactions)}")
        if not large_transactions.empty:
            print("大额交易记录:")
            print(large_transactions[['交易方户名', '对手户名', '交易金额', '交易时间']].head(10))
    
    # 2. 频繁交易分析
    if '交易方户名' in df.columns:
        transaction_counts = df['交易方户名'].value_counts()
        frequent_traders = transaction_counts[transaction_counts > transaction_counts.quantile(0.95)]
        print(f"\n2. 高频交易分析 (前5%)")
        print(f"高频交易者数量: {len(frequent_traders)}")
        if not frequent_traders.empty:
            print("高频交易者:")
            for trader, count in frequent_traders.head(10).items():
                print(f"  {trader}: {count} 笔交易")
    
    # 3. 循环交易模式分析
    if '交易方户名' in df.columns and '对手户名' in df.columns:
        print(f"\n3. 循环交易模式分析")
        # 查找A->B->A模式
        df_clean = df.dropna(subset=['交易方户名', '对手户名'])
        df_clean = df_clean[df_clean['交易方户名'] != df_clean['对手户名']]  # 排除自交易
        
        # 检查A->B->A循环模式
        cycle_transactions = []
        for idx, row in df_clean.iterrows():
            sender = row['交易方户名']
            receiver = row['对手户名']
            
            # 查找后续交易中，receiver作为sender的交易
            subsequent_transactions = df_clean[
                (df_clean['交易方户名'] == receiver) & 
                (df_clean['对手户名'] == sender) &
                (pd.to_datetime(df_clean['交易时间']) > pd.to_datetime(row['交易时间']))
            ]
            
            if not subsequent_transactions.empty:
                cycle_transactions.append({
                    'first_sender': sender,
                    'first_receiver': receiver,
                    'first_amount': row.get('交易金额', 'N/A'),
                    'first_time': row.get('交易时间', 'N/A'),
                    'second_amount': subsequent_transactions.iloc[0].get('交易金额', 'N/A'),
                    'second_time': subsequent_transactions.iloc[0].get('交易时间', 'N/A')
                })
        
        print(f"发现 {len(cycle_transactions)} 个循环交易模式")
        if cycle_transactions:
            print("循环交易示例:")
            for cycle in cycle_transactions[:10]:
                print(f"  {cycle['first_sender']} -> {cycle['first_receiver']} -> {cycle['first_sender']}")
                print(f"    第一次: {cycle['first_time']}, 金额: {cycle['first_amount']}")
                print(f"    第二次: {cycle['second_time']}, 金额: {cycle['second_amount']}")
    
    # 4. 时间集中度分析
    if '交易时间' in df.columns:
        df['交易时间'] = pd.to_datetime(df['交易时间'], errors='coerce')
        df_with_time = df.dropna(subset=['交易时间'])
        
        # 按小时分析交易分布
        df_with_time['交易小时'] = df_with_time['交易时间'].dt.hour
        hourly_transactions = df_with_time['交易小时'].value_counts().sort_index()
        
        print(f"\n4. 时间集中度分析")
        peak_hours = hourly_transactions.nlargest(3)
        print("交易高峰时段:")
        for hour, count in peak_hours.items():
            print(f"  {hour}时: {count} 笔交易")
    
    # 5. 金额分布异常分析
    if '交易金额' in df.columns:
        df_numeric = df.dropna(subset=['交易金额'])
        if not df_numeric.empty:
            df_numeric = df_numeric[pd.to_numeric(df_numeric['交易金额'], errors='coerce').notna()]
            df_numeric['交易金额'] = pd.to_numeric(df_numeric['交易金额'])
            
            # 查找接近整数的金额（可能是洗钱特征）
            rounded_amounts = df_numeric['交易金额'][abs(df_numeric['交易金额'] % 100) < 5]
            print(f"\n5. 金额分布异常分析")
            print(f"接近整数的交易数量: {len(rounded_amounts)} (可能是洗钱特征)")
            if len(rounded_amounts) > 0:
                top_rounded = rounded_amounts.value_counts().head(10)
                print("常见整数金额:")
                for amount, count in top_rounded.items():
                    print(f"  {amount}: {count} 次")
    
    # 6. 潜在风险公司识别
    if '交易方户名' in df.columns and '交易金额' in df.columns:
        print(f"\n6. 潜在风险公司识别")
        
        # 计算每个公司的交易统计
        company_stats = df.groupby('交易方户名').agg({
            '交易金额': ['count', 'sum', 'mean', 'std'],
        }).round(2)
        
        # 重命名列
        company_stats.columns = ['交易次数', '总金额', '平均金额', '金额标准差']
        
        # 按交易次数和总金额排序
        company_stats = company_stats.sort_values(['交易次数', '总金额'], ascending=False)
        
        print("交易活跃度排名前10的公司:")
        for company, stats in company_stats.head(10).iterrows():
            print(f"  {company}: 交易{int(stats['交易次数'])}次, 总额{stats['总金额']:.2f}, 平均{stats['平均金额']:.2f}")
    
except FileNotFoundError:
    print(f"找不到文件: {file_path}")
except Exception as e:
    print(f"读取文件时出错: {str(e)}")

print("\n分析完成。以上是基于数据模式的潜在洗钱活动指标，实际判断需要结合更多业务背景和法律专业知识。")