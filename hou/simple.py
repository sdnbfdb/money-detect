import pandas as pd
import numpy as np
from collections import defaultdict, deque
import os


def load_financial_data(file_path='建模数据121.xlsx'):
    """
    从Excel文件加载金融数据
    
    Args:
        file_path: Excel文件路径
    
    Returns:
        DataFrame: 加载的数据
    """
    if not os.path.exists(file_path):
        print(f"错误: 找不到文件 {file_path}")
        return None
    
    try:
        df = pd.read_excel(file_path)
        print(f"成功加载数据，共 {len(df)} 行，列数: {len(df.columns)}")
        print(f"列名: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"加载文件时出错: {e}")
        return None


def filter_data_by_keyword(df, keyword, columns=None):
    """
    根据关键词过滤数据
    
    Args:
        df: 数据DataFrame
        keyword: 搜索关键词
        columns: 要搜索的列名列表，如果为None则搜索所有列
    
    Returns:
        DataFrame: 过滤后的数据
    """
    if df is None:
        return None
    
    if columns is None:
        columns = df.columns.tolist()
    
    # 处理列名中的制表符
    columns = [col for col in columns if col in df.columns]
    
    mask = pd.Series([False] * len(df), dtype=bool)
    
    for col in columns:
        if col in df.columns:
            # 处理可能的制表符前缀和NaN值
            col_data = df[col].astype(str).fillna('')
            mask |= col_data.str.contains(str(keyword), na=False, case=False)
    
    filtered_df = df[mask]
    print(f"关键词 '{keyword}' 过滤结果: {len(filtered_df)} 条记录")
    return filtered_df


def filter_data_by_amount_range(df, min_amount=None, max_amount=None):
    """
    按金额范围过滤数据
    
    Args:
        df: 数据DataFrame
        min_amount: 最小金额
        max_amount: 最大金额
    
    Returns:
        DataFrame: 过滤后的数据
    """
    if df is None:
        return None
    
    amount_col = '\t交易金额' if '\t交易金额' in df.columns else '交易金额'
    
    if amount_col not in df.columns:
        print(f"警告: 找不到金额列 '{amount_col}'")
        return df
    
    # 将金额列转换为数值型
    df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
    
    mask = pd.Series([True] * len(df), dtype=bool)
    
    if min_amount is not None:
        mask &= (df[amount_col] >= min_amount)
    
    if max_amount is not None:
        mask &= (df[amount_col] <= max_amount)
    
    filtered_df = df[mask]
    print(f"金额范围过滤 ({min_amount} - {max_amount}): {len(filtered_df)} 条记录")
    return filtered_df


def filter_data_by_date_range(df, start_date=None, end_date=None):
    """
    按日期范围过滤数据
    
    Args:
        df: 数据DataFrame
        start_date: 开始日期 (字符串格式，如 '2023-01-01')
        end_date: 结束日期 (字符串格式，如 '2023-12-31')
    
    Returns:
        DataFrame: 过滤后的数据
    """
    if df is None:
        return None
    
    date_col = '\t交易时间' if '\t交易时间' in df.columns else '交易时间'
    
    if date_col not in df.columns:
        print(f"警告: 找不到日期列 '{date_col}'")
        return df
    
    # 将日期列转换为datetime格式
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    mask = pd.Series([True] * len(df), dtype=bool)
    
    if start_date is not None:
        start_dt = pd.to_datetime(start_date)
        mask &= (df[date_col] >= start_dt)
    
    if end_date is not None:
        end_dt = pd.to_datetime(end_date)
        mask &= (df[date_col] <= end_dt)
    
    filtered_df = df[mask]
    print(f"日期范围过滤 ({start_date} - {end_date}): {len(filtered_df)} 条记录")
    return filtered_df


def filter_data_by_account(df, account_name, account_type='both'):
    """
    按账户名称过滤数据
    
    Args:
        df: 数据DataFrame
        account_name: 账户名称
        account_type: 账户类型 ('sender', 'receiver', 'both')
    
    Returns:
        DataFrame: 过滤后的数据
    """
    if df is None:
        return None
    
    sender_col = '\t交易方户名' if '\t交易方户名' in df.columns else '交易方户名'
    receiver_col = '\t对手户名' if '\t对手户名' in df.columns else '对手户名'
    
    mask = pd.Series([False] * len(df), dtype=bool)
    
    if account_type in ['sender', 'both'] and sender_col in df.columns:
        col_data = df[sender_col].astype(str).fillna('')
        mask |= col_data.str.contains(str(account_name), na=False, case=False)
    
    if account_type in ['receiver', 'both'] and receiver_col in df.columns:
        col_data = df[receiver_col].astype(str).fillna('')
        mask |= col_data.str.contains(str(account_name), na=False, case=False)
    
    filtered_df = df[mask]
    print(f"账户 '{account_name}' 过滤结果: {len(filtered_df)} 条记录")
    return filtered_df


def create_transaction_network(df, account_col1='\t交易方户名', account_col2='\t对手户名'):
    """
    从交易数据创建网络图的节点和链接
    
    Args:
        df: 交易数据DataFrame
        account_col1: 第一个账户列名
        account_col2: 第二个账户列名
    
    Returns:
        tuple: (nodes, links) 节点列表和链接列表
    """
    if df is None:
        return [], []
    
    # 确保列名正确
    if account_col1 not in df.columns:
        account_col1 = '交易方户名' if '交易方户名' in df.columns else df.columns[0] if len(df.columns) > 0 else None
    if account_col2 not in df.columns:
        account_col2 = '对手户名' if '对手户名' in df.columns else df.columns[1] if len(df.columns) > 1 else None
    
    if account_col1 is None or account_col2 is None:
        print("错误: 找不到适当的账户列")
        return [], []
    
    # 获取所有唯一账户名
    all_accounts = set()
    if account_col1 in df.columns:
        all_accounts.update(df[account_col1].dropna().astype(str))
    if account_col2 in df.columns:
        all_accounts.update(df[account_col2].dropna().astype(str))
    
    # 创建节点
    nodes = [{'id': acc, 'name': acc} for acc in all_accounts if acc != 'nan']
    
    # 创建链接
    links = []
    for _, row in df.iterrows():
        sender = str(row[account_col1]) if account_col1 in row and pd.notna(row[account_col1]) else None
        receiver = str(row[account_col2]) if account_col2 in row and pd.notna(row[account_col2]) else None
        
        if sender and receiver and sender != 'nan' and receiver != 'nan':
            link = {
                'source': sender,
                'target': receiver,
                'amount': row.get('\t交易金额', row.get('交易金额', 0)),
                'date': row.get('\t交易时间', row.get('交易时间', ''))
            }
            links.append(link)
    
    print(f"创建网络图: {len(nodes)} 个节点, {len(links)} 条链接")
    return nodes, links


def remove_leaf_nodes_from_source(nodes, links, source_nodes):
    """
    从指定的源节点开始，删除所有叶节点和孤立节点（非源节点且度数为1或0的节点）
    使用逐步迭代的方式，每次移除节点后重新计算度数
    
    Args:
        nodes: 节点列表，每个节点包含id、name等信息
        links: 边列表，每个边包含source、target等信息
        source_nodes: 源节点集合，这些节点不会被删除
    
    Returns:
        simplified_nodes: 简化后的节点列表
        simplified_links: 简化后的边列表
    """
    if not nodes or not links:
        return nodes, links
    
    # 标准化节点ID（去除首尾空格和\t）
    def normalize_node_id(node_id):
        return node_id.strip().lstrip('\t') if isinstance(node_id, str) else node_id
    
    # 转换为字典形式以便快速查找，使用标准化后的ID
    node_map = {}
    for node in nodes:
        normalized_id = normalize_node_id(node['id'])
        node_map[normalized_id] = node
    
    # 标准化源节点ID
    source_nodes = set(normalize_node_id(s) for s in source_nodes) if source_nodes else set()
    
    # 构建邻接表（使用标准化ID）
    adjacency_list = defaultdict(set)  # 使用set避免重复
    for link in links:
        source_id = link['source'] if isinstance(link['source'], str) else link['source']['id']
        target_id = link['target'] if isinstance(link['target'], str) else link['target']['id']
        
        normalized_source = normalize_node_id(source_id)
        normalized_target = normalize_node_id(target_id)
        
        if normalized_source in node_map and normalized_target in node_map and normalized_source != normalized_target:
            adjacency_list[normalized_source].add(normalized_target)
            adjacency_list[normalized_target].add(normalized_source)
    
    # 持续移除叶节点和孤立节点直到没有更多可移除的
    nodes_to_remove = set()
    iteration = 0
    
    while True:
        iteration += 1
        
        # 计算当前状态下各节点的度数（排除已标记删除的节点）
        current_degree_map = {}
        for node_id in node_map:
            if node_id not in nodes_to_remove:
                # 计算与未删除节点的连接数
                valid_neighbors = {n for n in adjacency_list[node_id] if n not in nodes_to_remove}
                current_degree_map[node_id] = len(valid_neighbors)
        
        # 查找当前可移除的节点（度数为0或1且不是源节点）
        current_removable_nodes = {
            node_id for node_id, degree in current_degree_map.items()
            if degree <= 1 and node_id not in source_nodes
        }
        
        print(f"迭代 {iteration}: 当前可移除节点数={len(current_removable_nodes)}, 度数映射={ {k:v for k,v in list(current_degree_map.items())[:5]} }")
        
        # 如果没有可移除的节点，则退出循环
        if not current_removable_nodes:
            break
        
        # 将当前可移除的节点加入删除集合
        nodes_to_remove.update(current_removable_nodes)
        print(f"  移除节点: {list(current_removable_nodes)[:5]}{'...' if len(current_removable_nodes) > 5 else ''}")
    
    # 生成最终的简化结果
    simplified_nodes = [
        node for node_id, node in node_map.items() 
        if node_id not in nodes_to_remove
    ]
    
    simplified_links = [
        link for link in links
        if not (
            normalize_node_id(link['source'] if isinstance(link['source'], str) else link['source']['id']) in nodes_to_remove or
            normalize_node_id(link['target'] if isinstance(link['target'], str) else link['target']['id']) in nodes_to_remove
        )
    ]
    
    print(f"原始节点数: {len(nodes)}, 原始链接数: {len(links)}")
    print(f"简化后节点数: {len(simplified_nodes)}, 简化后链接数: {len(simplified_links)}")
    print(f"移除节点数: {len(nodes_to_remove)}")
    if source_nodes:
        print(f"源节点数: {len(source_nodes)}")
    
    return simplified_nodes, simplified_links


def simplify_graph(nodes, links, center_nodes=None, max_iterations=10):
    """
    简化交易关系图谱，移除外围叶节点
    
    Args:
        nodes: 节点列表，每个节点包含id、name等信息
        links: 边列表，每个边包含source、target等信息
        center_nodes: 中心节点集合，这些节点不会被删除
        max_iterations: 最大迭代次数，防止无限循环
    
    Returns:
        simplified_nodes: 简化后的节点列表
        simplified_links: 简化后的边列表
    """
    # 转换为字典形式以便快速查找
    node_map = {node['id']: node for node in nodes}
    center_nodes = center_nodes or set()
    
    # 构建邻接表
    adjacency_list = defaultdict(list)
    for link in links:
        source_id = link['source'] if isinstance(link['source'], str) else link['source']['id']
        target_id = link['target'] if isinstance(link['target'], str) else link['target']['id']
        
        if source_id in node_map and target_id in node_map:
            adjacency_list[source_id].append(target_id)
            adjacency_list[target_id].append(source_id)
    
    # 从中心节点开始，深度优先搜索所有可达节点
    reachable_nodes = set()
    queue = deque(center_nodes) if center_nodes else deque(node_map.keys())
    
    while queue:
        node_id = queue.popleft()
        if node_id not in reachable_nodes:
            reachable_nodes.add(node_id)
            for neighbor_id in adjacency_list[node_id]:
                if neighbor_id not in reachable_nodes:
                    queue.append(neighbor_id)
    
    # 过滤出可达的节点和边
    current_nodes = [node for node_id, node in node_map.items() if node_id in reachable_nodes]
    current_links = []
    for link in links:
        source_id = link['source'] if isinstance(link['source'], str) else link['source']['id']
        target_id = link['target'] if isinstance(link['target'], str) else link['target']['id']
        
        if source_id in reachable_nodes and target_id in reachable_nodes:
            current_links.append(link)
    
    # 计算可达子图中每个节点的度数
    degree_map = defaultdict(int)
    for node_id in reachable_nodes:
        degree_map[node_id] = 0
    
    for link in current_links:
        source_id = link['source'] if isinstance(link['source'], str) else link['source']['id']
        target_id = link['target'] if isinstance(link['target'], str) else link['target']['id']
        
        if source_id in reachable_nodes and target_id in reachable_nodes:
            degree_map[source_id] += 1
            degree_map[target_id] += 1
    
    # 递归移除叶节点（度数为1的节点，但不移除中心节点）
    removed_nodes = set()
    iteration_count = 0
    
    while iteration_count < max_iterations:
        iteration_count += 1
        nodes_to_remove = []
        
        # 查找当前度数为1的节点（叶节点），但不移除中心节点
        for node_id, degree in degree_map.items():
            if degree == 1 and node_id not in center_nodes and node_id not in removed_nodes:
                nodes_to_remove.append(node_id)
        
        if not nodes_to_remove:
            break
            
        # 移除叶节点
        for node_id in nodes_to_remove:
            removed_nodes.add(node_id)
        
        # 更新剩余节点的度数
        for link in current_links:
            source_id = link['source'] if isinstance(link['source'], str) else link['source']['id']
            target_id = link['target'] if isinstance(link['target'], str) else link['target']['id']
            
            if source_id in removed_nodes or target_id in removed_nodes:
                continue
                
            if source_id not in removed_nodes and target_id not in removed_nodes:
                # 更新度数
                if source_id in degree_map:
                    degree_map[source_id] = sum(
                        1 for neighbor in adjacency_list[source_id] 
                        if neighbor not in removed_nodes and neighbor != source_id
                    )
                if target_id in degree_map:
                    degree_map[target_id] = sum(
                        1 for neighbor in adjacency_list[target_id] 
                        if neighbor not in removed_nodes and neighbor != target_id
                    )
    
    # 生成最终的简化结果
    simplified_nodes = [
        node for node_id, node in node_map.items() 
        if node_id not in removed_nodes
    ]
    
    simplified_links = [
        link for link in current_links
        if not (
            (link['source'] if isinstance(link['source'], str) else link['source']['id']) in removed_nodes or
            (link['target'] if isinstance(link['target'], str) else link['target']['id']) in removed_nodes
        )
    ]
    
    print(f"原始节点数: {len(nodes)}, 原始链接数: {len(links)}")
    print(f"简化后节点数: {len(simplified_nodes)}, 简化后链接数: {len(simplified_links)}")
    print(f"移除节点数: {len(removed_nodes)}")
    
    return simplified_nodes, simplified_links


def filter_transactions_by_keywords(transactions_df, keywords, columns=None):
    """
    根据关键词过滤交易数据
    
    Args:
        transactions_df: 交易数据的DataFrame
        keywords: 要搜索的关键词列表
        columns: 要搜索的列名列表，默认为所有列
    
    Returns:
        filtered_df: 过滤后的DataFrame
    """
    if columns is None:
        columns = transactions_df.columns.tolist()
    
    # 去除列名中的制表符（如果有的话）
    columns = [col.lstrip('\t') if isinstance(col, str) else col for col in columns]
    
    mask = pd.Series([False] * len(transactions_df), dtype=bool)
    
    for keyword in keywords:
        keyword_mask = pd.Series([False] * len(transactions_df), dtype=bool)
        for col in columns:
            # 处理制表符前缀的列名
            actual_col = f'\t{col}' if f'\t{col}' in transactions_df.columns else col
            if actual_col in transactions_df.columns:
                # 将列转换为字符串进行比较，同时处理NaN值
                col_data = transactions_df[actual_col].astype(str).fillna('')
                keyword_mask |= col_data.str.contains(str(keyword), na=False, case=False)
        mask |= keyword_mask
    
    filtered_df = transactions_df[mask]
    print(f"原始交易数: {len(transactions_df)}, 过滤后交易数: {len(filtered_df)}")
    return filtered_df


def filter_transactions_by_amount_range(transactions_df, min_amount=None, max_amount=None):
    """
    根据金额范围过滤交易数据
    
    Args:
        transactions_df: 交易数据的DataFrame
        min_amount: 最小金额阈值
        max_amount: 最大金额阈值
    
    Returns:
        filtered_df: 过滤后的DataFrame
    """
    amount_col = '\t交易金额' if '\t交易金额' in transactions_df.columns else '交易金额'
    
    if amount_col not in transactions_df.columns:
        print(f"警告: 找不到金额列 '{amount_col}'")
        return transactions_df
    
    mask = pd.Series([True] * len(transactions_df), dtype=bool)
    
    if min_amount is not None:
        mask &= (pd.to_numeric(transactions_df[amount_col], errors='coerce') >= min_amount)
    
    if max_amount is not None:
        mask &= (pd.to_numeric(transactions_df[amount_col], errors='coerce') <= max_amount)
    
    filtered_df = transactions_df[mask]
    print(f"按金额范围过滤: {min_amount} - {max_amount}, 结果数: {len(filtered_df)}")
    return filtered_df


def filter_transactions_by_date_range(transactions_df, start_date=None, end_date=None):
    """
    根据日期范围过滤交易数据
    
    Args:
        transactions_df: 交易数据的DataFrame
        start_date: 开始日期 (字符串格式，如 '2023-01-01')
        end_date: 结束日期 (字符串格式，如 '2023-12-31')
    
    Returns:
        filtered_df: 过滤后的DataFrame
    """
    date_col = '\t交易时间' if '\t交易时间' in transactions_df.columns else '交易时间'
    
    if date_col not in transactions_df.columns:
        print(f"警告: 找不到日期列 '{date_col}'")
        return transactions_df
    
    # 尝试将日期列转换为datetime格式
    date_series = pd.to_datetime(transactions_df[date_col], errors='coerce')
    
    mask = pd.Series([True] * len(transactions_df), dtype=bool)
    
    if start_date is not None:
        start_dt = pd.to_datetime(start_date)
        mask &= (date_series >= start_dt)
    
    if end_date is not None:
        end_dt = pd.to_datetime(end_date)
        mask &= (date_series <= end_dt)
    
    filtered_df = transactions_df[mask]
    print(f"按日期范围过滤: {start_date} - {end_date}, 结果数: {len(filtered_df)}")
    return filtered_df


def remove_duplicate_transactions(transactions_df, subset_columns=None):
    """
    移除重复的交易记录
    
    Args:
        transactions_df: 交易数据的DataFrame
        subset_columns: 用于判断重复的列名列表，默认使用关键交易字段
    
    Returns:
        deduplicated_df: 去重后的DataFrame
    """
    if subset_columns is None:
        # 默认使用交易的关键字段来判断重复
        possible_cols = ['\t交易卡号', '\t交易账号', '\t交易时间', '\t交易金额', '\t借贷标志']
        subset_columns = [col for col in possible_cols if col in transactions_df.columns]
        
        if not subset_columns:
            # 如果找不到预设的列，则使用所有列
            subset_columns = transactions_df.columns.tolist()
    
    original_count = len(transactions_df)
    deduplicated_df = transactions_df.drop_duplicates(subset=subset_columns)
    removed_count = original_count - len(deduplicated_df)
    
    print(f"移除重复记录: {removed_count} 条，剩余: {len(deduplicated_df)} 条")
    return deduplicated_df


def filter_high_frequency_accounts(transactions_df, threshold=10):
    """
    过滤高频交易账户（交易次数超过阈值的账户）
    
    Args:
        transactions_df: 交易数据的DataFrame
        threshold: 交易次数阈值
    
    Returns:
        filtered_df: 过滤后的DataFrame
    """
    account_cols = ['\t交易方户名', '\t对手户名']
    valid_account_cols = [col for col in account_cols if col in transactions_df.columns]
    
    if not valid_account_cols:
        print("警告: 找不到账户相关列")
        return transactions_df
    
    # 统计每个账户的交易次数
    all_accounts = pd.concat([transactions_df[col].dropna() for col in valid_account_cols if col in transactions_df.columns])
    account_counts = all_accounts.value_counts()
    
    # 找出高频账户
    high_freq_accounts = set(account_counts[account_counts >= threshold].index)
    
    # 过滤出包含高频账户的交易记录
    mask = pd.Series([False] * len(transactions_df), dtype=bool)
    for col in valid_account_cols:
        if col in transactions_df.columns:
            mask |= transactions_df[col].isin(high_freq_accounts)
    
    filtered_df = transactions_df[mask]
    print(f"高频账户过滤 (≥{threshold}次交易): 找到 {len(high_freq_accounts)} 个高频账户，相关交易 {len(filtered_df)} 条")
    return filtered_df


def apply_composite_filter(transactions_df, filters_config):
    """
    应用复合过滤器
    
    Args:
        transactions_df: 交易数据的DataFrame
        filters_config: 过滤配置字典
    
    Returns:
        filtered_df: 经过多重过滤后的DataFrame
    """
    result_df = transactions_df.copy()
    
    # 1. 关键词过滤
    if 'keywords' in filters_config and filters_config['keywords']:
        result_df = filter_transactions_by_keywords(result_df, filters_config['keywords'])
    
    # 2. 金额范围过滤
    if ('min_amount' in filters_config and filters_config['min_amount'] is not None) or \
       ('max_amount' in filters_config and filters_config['max_amount'] is not None):
        min_amt = filters_config.get('min_amount')
        max_amt = filters_config.get('max_amount')
        result_df = filter_transactions_by_amount_range(result_df, min_amt, max_amt)
    
    # 3. 日期范围过滤
    if ('start_date' in filters_config and filters_config['start_date']) or \
       ('end_date' in filters_config and filters_config['end_date']):
        start_date = filters_config.get('start_date')
        end_date = filters_config.get('end_date')
        result_df = filter_transactions_by_date_range(result_df, start_date, end_date)
    
    # 4. 去重
    if filters_config.get('remove_duplicates', False):
        result_df = remove_duplicate_transactions(result_df)
    
    # 5. 高频账户过滤
    if 'high_freq_threshold' in filters_config and filters_config['high_freq_threshold'] > 0:
        result_df = filter_high_frequency_accounts(result_df, filters_config['high_freq_threshold'])
    
    return result_df


def detect_high_value_transactions(df, amount_threshold=None, percentile=95):
    """
    检测高价值交易
    
    Args:
        df: 交易数据DataFrame
        amount_threshold: 金额阈值，如果为None则使用百分位数
        percentile: 百分位数值（默认95%）
    
    Returns:
        DataFrame: 高价值交易记录
    """
    if df is None:
        return pd.DataFrame()
    
    amount_col = '\t交易金额' if '\t交易金额' in df.columns else '交易金额'
    
    if amount_col not in df.columns:
        print(f"警告: 找不到金额列 '{amount_col}'")
        return pd.DataFrame()
    
    # 将金额列转换为数值型
    numeric_amounts = pd.to_numeric(df[amount_col], errors='coerce').dropna()
    
    if amount_threshold is None:
        if len(numeric_amounts) > 0:
            amount_threshold = numeric_amounts.quantile(percentile/100.0)
        else:
            print("没有有效的金额数据")
            return pd.DataFrame()
    
    mask = pd.Series([False] * len(df), dtype=bool)
    df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
    mask = df[amount_col] >= amount_threshold
    
    high_value_df = df[mask]
    print(f"检测到 {len(high_value_df)} 条高价值交易 (阈值: {amount_threshold:.2f})")
    return high_value_df


def find_all_connected_nodes(nodes, links, source_nodes, max_depth=None):
    """
    查找从源节点集合出发能到达的所有节点（考虑所有可能路径）
    
    Args:
        nodes: 节点列表
        links: 链接列表
        source_nodes: 源节点集合
        max_depth: 最大搜索深度，如果为None则不限制
    
    Returns:
        set: 所有从源节点集合可达的节点ID
    """
    if not nodes or not links:
        return set()
    
    # 构建邻接表
    adjacency_list = defaultdict(set)
    node_ids = {node['id'] for node in nodes}
    
    for link in links:
        source_id = link['source'] if isinstance(link['source'], str) else link['source']['id']
        target_id = link['target'] if isinstance(link['target'], str) else link['target']['id']
        
        if source_id in node_ids and target_id in node_ids:
            adjacency_list[source_id].add(target_id)
            adjacency_list[target_id].add(source_id)  # 无向图
    
    # BFS查找所有可达节点
    visited = set()
    queue = deque([(node, 0) for node in source_nodes if node in node_ids])  # (node, depth)
    
    while queue:
        current_node, depth = queue.popleft()
        
        if current_node in visited:
            continue
            
        visited.add(current_node)
        
        # 如果达到最大深度，停止进一步探索
        if max_depth is not None and depth >= max_depth:
            continue
        
        # 添加所有未访问的邻居节点
        for neighbor in adjacency_list[current_node]:
            if neighbor not in visited:
                queue.append((neighbor, depth + 1))
    
    print(f"从 {len(source_nodes)} 个源节点出发，找到 {len(visited)} 个可达节点")
    return visited


def find_all_paths_between(nodes, links, start_node, end_node, max_length=5):
    """
    查找两点之间的所有路径
    
    Args:
        nodes: 节点列表
        links: 链接列表
        start_node: 起始节点
        end_node: 结束节点
        max_length: 最大路径长度
    
    Returns:
        list: 包含所有路径的列表，每条路径是一个节点列表
    """
    if not nodes or not links:
        return []
    
    # 构建邻接表
    adjacency_list = defaultdict(set)
    node_ids = {node['id'] for node in nodes}
    
    if start_node not in node_ids or end_node not in node_ids:
        return []
    
    for link in links:
        source_id = link['source'] if isinstance(link['source'], str) else link['source']['id']
        target_id = link['target'] if isinstance(link['target'], str) else link['target']['id']
        
        if source_id in node_ids and target_id in node_ids:
            adjacency_list[source_id].add(target_id)
            adjacency_list[target_id].add(source_id)  # 无向图
    
    all_paths = []
    
    def dfs(current, target, path, visited, length):
        if length > max_length:
            return
            
        if current == target:
            all_paths.append(path[:])  # 添加路径副本
            return
        
        for neighbor in adjacency_list[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                dfs(neighbor, target, path, visited, length + 1)
                path.pop()  # 回溯
                visited.remove(neighbor)
    
    visited = {start_node}
    dfs(start_node, end_node, [start_node], visited, 1)
    
    print(f"从 '{start_node}' 到 '{end_node}' 找到 {len(all_paths)} 条路径")
    return all_paths


def detect_bridges_and_cut_points(nodes, links):
    """
    检测网络中的桥接节点和割点（关键连接点）
    
    Args:
        nodes: 节点列表
        links: 链接列表
    
    Returns:
        dict: 包含桥接边和割点的信息
    """
    if not nodes or not links:
        return {"bridges": [], "cut_points": []}
    
    # 构建邻接表
    adjacency_list = defaultdict(list)
    node_ids = {node['id'] for node in nodes}
    
    for link in links:
        source_id = link['source'] if isinstance(link['source'], str) else link['source']['id']
        target_id = link['target'] if isinstance(link['target'], str) else link['target']['id']
        
        if source_id in node_ids and target_id in node_ids:
            adjacency_list[source_id].append(target_id)
            adjacency_list[target_id].append(source_id)
    
    nodes_list = list(node_ids)
    n = len(nodes_list)
    node_index = {node: i for i, node in enumerate(nodes_list)}
    
    disc = [-1] * n
    low = [-1] * n
    parent = [-1] * n
    bridges = []
    cut_points = set()
    time = [0]  # 使用列表来允许内部函数修改
    
    def dfs(u, visited):
        disc[node_index[u]] = time[0]
        low[node_index[u]] = time[0]
        time[0] += 1
        children = 0
        
        for v in adjacency_list[u]:
            v_idx = node_index[v]
            u_idx = node_index[u]
            
            if disc[v_idx] == -1:  # 未访问过的节点
                parent[v_idx] = u_idx
                children += 1
                dfs(v, visited)
                
                low[u_idx] = min(low[u_idx], low[v_idx])
                
                # 检查是否为桥
                if low[v_idx] > disc[u_idx]:
                    bridges.append((u, v))
                
                # 检查是否为割点
                if parent[u_idx] != -1 and low[v_idx] >= disc[u_idx]:
                    cut_points.add(u)
            elif v_idx != parent[u_idx]:  # 回边
                low[u_idx] = min(low[u_idx], disc[v_idx])
        
        # 根节点的特殊情况
        if parent[node_index[u]] == -1 and children > 1:
            cut_points.add(u)
    
    visited = set()
    for node in nodes_list:
        if disc[node_index[node]] == -1:
            dfs(node, visited)
    
    result = {
        "bridges": bridges,
        "cut_points": list(cut_points)
    }
    
    print(f"检测到 {len(bridges)} 个桥接边和 {len(cut_points)} 个割点")
    return result


def remove_isolated_and_leaf_nodes(nodes, links, max_iterations=10):
    """
    去除图中的孤立节点（度数为0的节点）和叶节点（度数为1的节点）
    
    Args:
        nodes: 节点列表，每个节点包含id、name等信息
        links: 边列表，每个边包含source、target等信息
        max_iterations: 最大迭代次数，防止无限循环
    
    Returns:
        simplified_nodes: 去除孤立和叶节点后的节点列表
        simplified_links: 去除相应边后的边列表
    """
    if not nodes or not links:
        # 如果没有边，所有节点都是孤立节点，全部移除
        if nodes and not links:
            print(f"原始节点数: {len(nodes)}, 原始链接数: {len(links)}")
            print(f"移除孤立节点数: {len(nodes)}")
            return [], []
        return nodes, links
    
    # 标准化节点ID（去除首尾空格和\t）
    def normalize_node_id(node_id):
        return node_id.strip().lstrip('\t') if isinstance(node_id, str) else node_id
    
    # 将节点列表转换为字典以便快速查找，使用标准化后的ID作为key
    node_map = {}
    id_mapping = {}  # 原始ID -> 标准化ID 的映射
    for node in nodes:
        original_id = node['id']
        normalized_id = normalize_node_id(original_id)
        node_map[normalized_id] = node
        id_mapping[original_id] = normalized_id
    
    original_node_ids = set(node_map.keys())
    
    print(f"节点标准化完成，原始节点数: {len(nodes)}, 标准化后: {len(node_map)}")
    
    # 构建邻接表，记录每个节点的邻居（使用标准化ID）
    adjacency_list = defaultdict(set)
    for link in links:
        source_id = link['source'] if isinstance(link['source'], str) else link['source']['id']
        target_id = link['target'] if isinstance(link['target'], str) else link['target']['id']
        
        # 标准化ID
        normalized_source = normalize_node_id(source_id)
        normalized_target = normalize_node_id(target_id)
        
        if normalized_source in node_map and normalized_target in node_map and normalized_source != normalized_target:
            adjacency_list[normalized_source].add(normalized_target)
            adjacency_list[normalized_target].add(normalized_source)
    
    removed_nodes = set()
    iteration_count = 0
    
    # 迭代地移除孤立节点和叶节点，直到没有更多的节点可移除或达到最大迭代次数
    while iteration_count < max_iterations:
        iteration_count += 1
        
        # 当前迭代中要移除的孤立节点和叶节点
        current_nodes_to_remove = []
        
        # 遍历所有节点，找出度数为0或1的节点
        for node_id in original_node_ids:
            if node_id not in removed_nodes:
                # 计算当前节点的有效邻居数量（排除已被移除的节点）
                valid_neighbors = {n for n in adjacency_list[node_id] if n not in removed_nodes}
                
                # 如果有效邻居数为0（孤立节点）或1（叶节点），则移除
                if len(valid_neighbors) <= 1:
                    current_nodes_to_remove.append(node_id)
        
        # 如果这一轮没有找到要移除的节点，结束循环
        if not current_nodes_to_remove:
            break
        
        # 将找到的节点加入移除集合
        removed_nodes.update(current_nodes_to_remove)
    
    # 生成最终的简化结果
    simplified_nodes = [
        node for node_id, node in node_map.items() 
        if node_id not in removed_nodes
    ]
    
    # 过滤链接时使用标准化后的ID进行判断
    simplified_links = []
    for link in links:
        source_id = link['source'] if isinstance(link['source'], str) else link['source']['id']
        target_id = link['target'] if isinstance(link['target'], str) else link['target']['id']
        normalized_source = normalize_node_id(source_id)
        normalized_target = normalize_node_id(target_id)
        
        if normalized_source not in removed_nodes and normalized_target not in removed_nodes:
            simplified_links.append(link)
    
    print(f"原始节点数: {len(nodes)}, 原始链接数: {len(links)}")
    print(f"简化后节点数: {len(simplified_nodes)}, 简化后链接数: {len(simplified_links)}")
    print(f"移除节点数: {len(removed_nodes)} (孤立节点和叶节点)")
    
    return simplified_nodes, simplified_links

def remove_leaf_nodes(nodes, links, max_iterations=10):
    """
    去除图中的叶节点（度数为1的节点）
    
    Args:
        nodes: 节点列表，每个节点包含id、name等信息
        links: 边列表，每个边包含source、target等信息
        max_iterations: 最大迭代次数，防止无限循环
    
    Returns:
        simplified_nodes: 去除叶节点后的节点列表
        simplified_links: 去除相应边后的边列表
    """
    if not nodes or not links:
        # 如果没有边，所有节点都是孤立节点，全部移除
        if nodes and not links:
            print(f"原始节点数: {len(nodes)}, 原始链接数: {len(links)}")
            print(f"移除孤立节点数: {len(nodes)}")
            return [], []
        return nodes, links
    
    # 将节点列表转换为字典以便快速查找
    node_map = {node['id']: node for node in nodes}
    original_node_ids = set(node_map.keys())
    
    # 构建邻接表，记录每个节点的邻居
    adjacency_list = defaultdict(set)
    for link in links:
        source_id = link['source'] if isinstance(link['source'], str) else link['source']['id']
        target_id = link['target'] if isinstance(link['target'], str) else link['target']['id']
        
        if source_id in node_map and target_id in node_map and source_id != target_id:
            adjacency_list[source_id].add(target_id)
            adjacency_list[target_id].add(source_id)
    
    removed_nodes = set()
    iteration_count = 0
    
    # 迭代地移除叶节点，直到没有更多的叶节点或达到最大迭代次数
    while iteration_count < max_iterations:
        iteration_count += 1
        
        # 当前迭代中要移除的叶节点
        current_leaf_nodes = []
        
        # 遍历所有节点，找出度数为1的节点（即叶节点）
        for node_id in original_node_ids:
            if node_id not in removed_nodes:
                # 计算当前节点的有效邻居数量（排除已被移除的节点）
                valid_neighbors = {n for n in adjacency_list[node_id] if n not in removed_nodes}
                
                # 如果有效邻居数恰好为1，则为叶节点
                if len(valid_neighbors) == 1:
                    current_leaf_nodes.append(node_id)
        
        # 如果这一轮没有找到叶节点，结束循环
        if not current_leaf_nodes:
            break
        
        # 将找到的叶节点加入移除集合
        removed_nodes.update(current_leaf_nodes)
    
    # 生成最终的简化结果
    simplified_nodes = [
        node for node_id, node in node_map.items() 
        if node_id not in removed_nodes
    ]
    
    simplified_links = [
        link for link in links
        if not (
            (link['source'] if isinstance(link['source'], str) else link['source']['id']) in removed_nodes or
            (link['target'] if isinstance(link['target'], str) else link['target']['id']) in removed_nodes
        )
    ]
    
    print(f"原始节点数: {len(nodes)}, 原始链接数: {len(links)}")
    print(f"去除叶节点后节点数: {len(simplified_nodes)}, 去除叶节点后链接数: {len(simplified_links)}")
    print(f"移除叶节点数: {len(removed_nodes)}")
    
    return simplified_nodes, simplified_links


def build_full_transaction_topology(df, seed_nodes=None, max_depth=None, start_date=None, end_date=None, min_amount=None, max_amount=None, remove_leaves=False):
    """
    构建完整的交易网络拓扑，从种子节点开始遍历整个网络

    Args:
        df: 交易数据的DataFrame
        seed_nodes: 种子节点列表，如果为None则使用所有节点
        max_depth: 最大搜索深度，如果为None则不限制
        start_date: 开始日期筛选条件
        end_date: 结束日期筛选条件
        min_amount: 最小金额筛选条件
        max_amount: 最大金额筛选条件
        remove_leaves: 是否删除叶节点

    Returns:
        tuple: (nodes, links) 完整的节点和链接列表
    """
    if df is None:
        return [], []

    # 应用时间范围和金额范围筛选
    filtered_df = df.copy()

    # 时间筛选
    if start_date or end_date:
        # 智能查找时间列
        date_col = None
        for col_name in ['\t交易时间', '交易时间']:
            if col_name in filtered_df.columns:
                date_col = col_name
                break
                
        if date_col:
            filtered_df[date_col] = pd.to_datetime(filtered_df[date_col], errors='coerce')
            if start_date:
                start_dt = pd.to_datetime(start_date)
                filtered_df = filtered_df[filtered_df[date_col] >= start_dt]
            if end_date:
                end_dt = pd.to_datetime(end_date)
                filtered_df = filtered_df[filtered_df[date_col] <= end_dt]

    # 金额筛选
    if min_amount is not None or max_amount is not None:
        # 智能查找金额列
        amount_col = None
        for col_name in ['\t交易金额', '交易金额']:
            if col_name in filtered_df.columns:
                amount_col = col_name
                break
                
        if amount_col:
            filtered_df[amount_col] = pd.to_numeric(filtered_df[amount_col], errors='coerce')
            if min_amount is not None:
                filtered_df = filtered_df[filtered_df[amount_col] >= min_amount]
            if max_amount is not None:
                filtered_df = filtered_df[filtered_df[amount_col] <= max_amount]

    print(f"筛选后数据行数: {len(filtered_df)} (原数据: {len(df)})")

    # 智能确定账户列名，兼容带制表符和不带制表符的格式
    sender_col = None
    receiver_col = None
    
    # 查找交易方户名列
    for col_name in ['\t交易方户名', '交易方户名']:
        if col_name in filtered_df.columns:
            sender_col = col_name
            break
    
    # 查找对手户名列
    for col_name in ['\t对手户名', '对手户名']:
        if col_name in filtered_df.columns:
            receiver_col = col_name
            break

    if sender_col is None or receiver_col is None:
        print("错误: 找不到交易方或对手方列")
        return [], []

    # 获取所有唯一账户名
    all_accounts = set()
    if sender_col in filtered_df.columns:
        all_accounts.update(filtered_df[sender_col].dropna().astype(str))
    if receiver_col in filtered_df.columns:
        all_accounts.update(filtered_df[receiver_col].dropna().astype(str))

    # 如果没有提供种子节点，则使用所有节点
    if seed_nodes is None:
        seed_nodes = all_accounts
    else:
        # 标准化种子节点名称，尝试匹配数据中的格式
        normalized_seed_nodes = set()
        for seed in seed_nodes:
            # 检查是否在原始账户中存在（可能带制表符前缀）
            if seed in all_accounts:
                normalized_seed_nodes.add(seed)
            # 尝试加上制表符前缀再匹配
            elif f"\t{seed}" in all_accounts:
                normalized_seed_nodes.add(f"\t{seed}")
            # 检查是否是带制表符的版本
            elif seed.startswith('\t') and seed.lstrip('\t') in all_accounts:
                normalized_seed_nodes.add(seed.lstrip('\t'))
            else:
                # 如果都不匹配，可能用户输入的格式与数据中的格式不一致
                # 逐个检查all_accounts中是否包含种子节点作为子串
                for account in all_accounts:
                    if seed in account or account.lstrip('\t') == seed:
                        normalized_seed_nodes.add(account)
                        break

        seed_nodes = normalized_seed_nodes & all_accounts  # 确保种子节点存在于数据中

    print(f"种子节点数: {len(seed_nodes)}, 总账户数: {len(all_accounts)}")

    # 构建邻接表，用于BFS遍历
    adjacency_list = defaultdict(set)

    # 为每一笔交易建立连接
    for _, row in filtered_df.iterrows():
        sender = str(row[sender_col]) if sender_col in row and pd.notna(row[sender_col]) else None
        receiver = str(row[receiver_col]) if receiver_col in row and pd.notna(row[receiver_col]) else None

        # 如果sender和receiver都存在且非空，则建立连接
        if sender and receiver and sender != 'nan' and receiver != 'nan':
            adjacency_list[sender].add(receiver)
            adjacency_list[receiver].add(sender)  # 无向图
        # 如果只有sender存在，也要将其加入到图中（即使没有连接）
        elif sender and sender != 'nan':
            adjacency_list[sender]  # 确保节点被添加到邻接表中
        # 如果只有receiver存在，也要将其加入到图中（即使没有连接）
        elif receiver and receiver != 'nan':
            adjacency_list[receiver]  # 确保节点被添加到邻接表中

    # 使用BFS从种子节点开始遍历整个网络
    visited = set()
    queue = deque(seed_nodes)
    depth = 0

    while queue and (max_depth is None or depth < max_depth):
        depth += 1
        current_level_size = len(queue)

        for _ in range(current_level_size):
            current_node = queue.popleft()

            if current_node in visited:
                continue

            visited.add(current_node)

            # 添加所有未访问的邻居节点到队列
            for neighbor in adjacency_list[current_node]:
                if neighbor not in visited:
                    queue.append(neighbor)

    # 获取所有访问过的节点
    connected_nodes = list(visited)

    # 创建节点列表
    nodes = [{'id': acc, 'name': acc} for acc in connected_nodes if acc != 'nan']

    # 创建链接列表，包含所有已访问节点的交易
    links = []
    for _, row in filtered_df.iterrows():
        sender = str(row[sender_col]) if sender_col in row and pd.notna(row[sender_col]) else None
        receiver = str(row[receiver_col]) if receiver_col in row and pd.notna(row[receiver_col]) else None

        # 如果sender和receiver都存在且都在访问列表中，创建链接
        if (sender and receiver and
            sender != 'nan' and receiver != 'nan' and
            sender in visited and receiver in visited):

            link = {
                'source': sender,
                'target': receiver,
                'amount': row.get('\t交易金额', row.get('交易金额', 0)),
                'date': row.get('\t交易时间', row.get('交易时间', ''))
            }
            links.append(link)
        # 如果只有sender存在且在访问列表中，也可以创建一个特殊的单边节点表示
        elif (sender and sender != 'nan' and sender in visited and 
              receiver and (not receiver or receiver == 'nan')):
            # 为只有发送方的交易创建一个虚拟节点或特殊链接
            virtual_target = f"{sender}_single_transaction"
            link = {
                'source': sender,
                'target': virtual_target,
                'amount': row.get('\t交易金额', row.get('交易金额', 0)),
                'date': row.get('\t交易时间', row.get('交易时间', '')),
                'type': 'single_side_transaction'  # 标记为单边交易
            }
            links.append(link)
        # 如果只有receiver存在且在访问列表中
        elif (receiver and receiver != 'nan' and receiver in visited and 
              sender and (not sender or sender == 'nan')):
            # 为只有接收方的交易创建一个虚拟节点或特殊链接
            virtual_source = f"{receiver}_single_transaction"
            link = {
                'source': virtual_source,
                'target': receiver,
                'amount': row.get('\t交易金额', row.get('交易金额', 0)),
                'date': row.get('\t交易时间', row.get('交易时间', '')),
                'type': 'single_side_transaction'  # 标记为单边交易
            }
            links.append(link)

    print(f"完整拓扑构建完成: {len(nodes)} 个节点, {len(links)} 条链接")

    # 如果需要删除叶节点和孤立节点
    if remove_leaves and nodes and links:
        print("开始删除叶节点和孤立节点...")
        nodes, links = remove_isolated_and_leaf_nodes(nodes, links)
        print(f"删除叶节点和孤立节点后: {len(nodes)} 个节点, {len(links)} 条链接")

    return nodes, links


def build_multi_center_network(df, seed_nodes=None, max_depth=None):
    """
    构建多中心交易网络，允许每个节点成为中心节点
    
    Args:
        df: 交易数据的DataFrame
        seed_nodes: 种子节点列表
        max_depth: 最大搜索深度
    
    Returns:
        tuple: (nodes, links) 多中心网络的节点和链接列表
    """
    return build_full_transaction_topology(df, seed_nodes, max_depth)


# 发票拓扑分析相关函数

def create_invoice_network(df, seller_col='销售方', buyer_col='购买方', amount_col='价税合计', date_col='开票日期'):
    """
    从发票数据创建网络图的节点和链接
    
    Args:
        df: 发票数据DataFrame
        seller_col: 销售方列名
        buyer_col: 购买方列名
        amount_col: 金额列名
        date_col: 日期列名
    
    Returns:
        tuple: (nodes, links) 节点列表和链接列表
    """
    if df is None:
        return [], []
    
    # 确保列名正确
    if seller_col not in df.columns:
        possible_seller_cols = ['销售方', '销方名称', '销方企业名称', 'Seller', 'SellerName']
        for col in possible_seller_cols:
            if col in df.columns:
                seller_col = col
                break
    
    if buyer_col not in df.columns:
        possible_buyer_cols = ['购买方', '购方企业名称', 'Buyer', 'BuyerName']
        for col in possible_buyer_cols:
            if col in df.columns:
                buyer_col = col
                break
    
    if amount_col not in df.columns:
        possible_amount_cols = ['价税合计', 'Amount', 'TotalAmount']
        for col in possible_amount_cols:
            if col in df.columns:
                amount_col = col
                break
    
    if date_col not in df.columns:
        possible_date_cols = ['开票日期', 'Date', 'InvoiceDate']
        for col in possible_date_cols:
            if col in df.columns:
                date_col = col
                break
    
    if seller_col not in df.columns or buyer_col not in df.columns:
        print("错误: 找不到销售方或购买方列")
        return [], []
    
    # 获取所有唯一企业名
    all_entities = set()
    if seller_col in df.columns:
        all_entities.update(df[seller_col].dropna().astype(str))
    if buyer_col in df.columns:
        all_entities.update(df[buyer_col].dropna().astype(str))
    
    # 创建节点
    nodes = [{'id': entity, 'name': entity} for entity in all_entities if entity != 'nan']
    
    # 创建链接
    links = []
    for _, row in df.iterrows():
        seller = str(row[seller_col]) if seller_col in row and pd.notna(row[seller_col]) else None
        buyer = str(row[buyer_col]) if buyer_col in row and pd.notna(row[buyer_col]) else None
        
        if seller and buyer and seller != 'nan' and buyer != 'nan' and seller != buyer:
            link = {
                'source': seller,
                'target': buyer,
                'amount': row.get(amount_col, row.get('价税合计', 0)),
                'date': row.get(date_col, row.get('开票日期', '')),
                'invoice_code': row.get('发票代码', ''),
                'invoice_number': row.get('发票号码', '')
            }
            links.append(link)
    
    print(f"创建发票网络图: {len(nodes)} 个节点, {len(links)} 条链接")
    return nodes, links


def analyze_invoice_topology(df, seed_entities=None, max_depth=None):
    """
    分析发票数据的拓扑结构
    
    Args:
        df: 发票数据DataFrame
        seed_entities: 种子实体列表，如果为None则分析整个网络
        max_depth: 最大搜索深度，如果为None则不限制
    
    Returns:
        dict: 拓扑分析结果
    """
    if df is None:
        return {}
    
    # 创建发票网络
    nodes, links = create_invoice_network(df)
    
    if not nodes or not links:
        print("没有足够的数据创建网络")
        return {}
    
    # 如果提供了种子实体，则从这些实体开始构建子网络
    if seed_entities:
        seed_set = set(seed_entities)
        # 查找从种子实体可达的所有节点
        reachable_nodes = find_all_connected_nodes(nodes, links, seed_set, max_depth)
        
        # 过滤出可达的节点和链接
        filtered_nodes = [node for node in nodes if node['id'] in reachable_nodes]
        filtered_links = [
            link for link in links 
            if link['source'] in reachable_nodes and link['target'] in reachable_nodes
        ]
        
        nodes = filtered_nodes
        links = filtered_links
    
    # 计算网络指标
    result = {
        'total_nodes': len(nodes),
        'total_links': len(links),
        'nodes': nodes,
        'links': links,
        'density': calculate_network_density(nodes, links),
        'central_entities': find_central_entities(nodes, links),
        'connected_components': find_connected_components(nodes, links)
    }
    
    print(f"发票拓扑分析完成: {result['total_nodes']} 个节点, {result['total_links']} 条链接")
    print(f"网络密度: {result['density']:.4f}")
    print(f"中心实体数: {len(result['central_entities'])}")
    print(f"连通分量数: {len(result['connected_components'])}")
    
    return result


def calculate_network_density(nodes, links):
    """
    计算网络密度
    
    Args:
        nodes: 节点列表
        links: 链接列表
    
    Returns:
        float: 网络密度
    """
    if not nodes or len(nodes) < 2:
        return 0.0
    
    n = len(nodes)
    max_possible_edges = n * (n - 1) / 2  # 对于无向图
    actual_edges = len(links)
    
    density = actual_edges / max_possible_edges if max_possible_edges > 0 else 0.0
    return density


def find_central_entities(nodes, links, top_n=10):
    """
    查找网络中的中心实体（基于度数）
    
    Args:
        nodes: 节点列表
        links: 链接列表
        top_n: 返回前N个中心实体
    
    Returns:
        list: 中心实体列表，按度数排序
    """
    if not nodes or not links:
        return []
    
    # 计算每个节点的度数
    degree_count = defaultdict(int)
    
    for link in links:
        source_id = link['source']
        target_id = link['target']
        degree_count[source_id] += 1
        degree_count[target_id] += 1
    
    # 按度数排序
    sorted_entities = sorted(degree_count.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_entities[:top_n]


def find_connected_components(nodes, links):
    """
    查找网络中的连通分量
    
    Args:
        nodes: 节点列表
        links: 链接列表
    
    Returns:
        list: 连通分量列表，每个元素是一个包含节点ID的集合
    """
    if not nodes:
        return []
    
    if not links:
        # 如果没有链接，每个节点都是独立的连通分量
        return [{node['id']} for node in nodes]
    
    # 构建邻接表
    adjacency_list = defaultdict(set)
    node_ids = {node['id'] for node in nodes}
    
    for link in links:
        source_id = link['source']
        target_id = link['target']
        
        if source_id in node_ids and target_id in node_ids:
            adjacency_list[source_id].add(target_id)
            adjacency_list[target_id].add(source_id)
    
    visited = set()
    components = []
    
    for node_id in node_ids:
        if node_id not in visited:
            # BFS查找连通分量
            component = set()
            queue = deque([node_id])
            
            while queue:
                current = queue.popleft()
                if current not in visited:
                    visited.add(current)
                    component.add(current)
                    
                    for neighbor in adjacency_list[current]:
                        if neighbor not in visited:
                            queue.append(neighbor)
            
            if component:
                components.append(component)
    
    return components


def find_invoice_rings(df, max_ring_size=5):
    """
    查找发票网络中的环形结构（可能表示回环开票等异常行为）
    
    Args:
        df: 发票数据DataFrame
        max_ring_size: 最大环大小
    
    Returns:
        list: 环形结构列表
    """
    nodes, links = create_invoice_network(df)
    
    if not nodes or not links:
        return []
    
    # 构建邻接表
    adjacency_list = defaultdict(set)
    node_ids = {node['id'] for node in nodes}
    
    for link in links:
        source_id = link['source']
        target_id = link['target']
        
        if source_id in node_ids and target_id in node_ids:
            adjacency_list[source_id].add(target_id)
    
    rings = []
    
    # 使用DFS查找环
    def dfs(start_node, current_path, visited_edges, path_sources):
        current_node = current_path[-1]
        
        # 如果当前节点已经在路径中（除了起点），则找到了一个环
        if current_node in current_path[:-1]:
            ring_start_idx = current_path.index(current_node)
            ring = current_path[ring_start_idx:]
            if len(ring) >= 3 and ring not in rings:  # 环至少需要3个节点
                rings.append(ring)
            return
        
        # 如果路径长度超过限制，停止搜索
        if len(current_path) > max_ring_size:
            return
        
        # 探索邻居节点
        for neighbor in adjacency_list[current_node]:
            if neighbor in path_sources:
                # 形成潜在环，添加到路径
                new_path = current_path + [neighbor]
                dfs(start_node, new_path, visited_edges, path_sources | {neighbor})
            elif neighbor != start_node or len(current_path) >= max_ring_size-1:
                # 继续搜索
                new_path = current_path + [neighbor]
                new_sources = path_sources | {neighbor}
                dfs(start_node, new_path, visited_edges, new_sources)
    
    # 从每个节点开始搜索环
    for node in node_ids:
        dfs(node, [node], set(), {node})
    
    # 去重并标准化环的表示（以最小节点ID开始）
    unique_rings = []
    for ring in rings:
        # 找到字典序最小的起始点
        min_idx = min(range(len(ring)), key=lambda i: ring[i])
        normalized_ring = ring[min_idx:] + ring[:min_idx]
        if normalized_ring not in unique_rings:
            unique_rings.append(normalized_ring)
    
    print(f"发现 {len(unique_rings)} 个环形结构")
    return unique_rings


# 示例用法
if __name__ == "__main__":
    # 示例：如何使用这些过滤函数
    print("化简和过滤逻辑库已加载")
    print("可用函数:")
    print("- load_financial_data: 加载金融数据")
    print("- filter_data_by_keyword: 按关键词过滤数据")
    print("- filter_data_by_amount_range: 按金额范围过滤数据")
    print("- filter_data_by_date_range: 按日期范围过滤数据")
    print("- filter_data_by_account: 按账户过滤数据")
    print("- create_transaction_network: 创建交易网络图")
    print("- remove_leaf_nodes_from_source: 从源节点开始删除所有叶节点")
    print("- simplify_graph: 简化图谱，移除叶节点")
    print("- remove_leaf_nodes: 去除图中的叶节点")
    print("- filter_transactions_by_keywords: 按关键词过滤")
    print("- filter_transactions_by_amount_range: 按金额范围过滤")
    print("- filter_transactions_by_date_range: 按日期范围过滤")
    print("- remove_duplicate_transactions: 移除重复记录")
    print("- filter_high_frequency_accounts: 过滤高频账户")
    print("- apply_composite_filter: 应用复合过滤器")
    print("- detect_high_value_transactions: 检测高价值交易")
    print("- find_all_connected_nodes: 查找所有连通节点")
    print("- find_all_paths_between: 查找两节点间所有路径")
    print("- detect_bridges_and_cut_points: 检测网络关键点")
    print("- build_full_transaction_topology: 构建完整交易网络拓扑")
    print("- build_multi_center_network: 构建多中心交易网络")
    print("- create_invoice_network: 创建发票网络")
    print("- analyze_invoice_topology: 分析发票拓扑结构")
    print("- calculate_network_density: 计算网络密度")
    print("- find_central_entities: 查找中心实体")
    print("- find_connected_components: 查找连通分量")
    print("- find_invoice_rings: 查找发票网络中的环形结构")