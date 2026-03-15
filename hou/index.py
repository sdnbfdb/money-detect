import os
import csv
import pandas as pd
from datetime import datetime

# 获取根目录路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

class DataSaver:
    """
    数据保存类，用于将生成的字段保存为CSV文件
    """
    
    def __init__(self, output_dir=ROOT_DIR):
        """
        初始化数据保存器
        
        Args:
            output_dir: 输出目录，默认为根目录
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def save_to_csv(self, data, filename=None, columns=None, append=False):
        """
        将数据保存为CSV文件
        
        Args:
            data: 要保存的数据，可以是列表、字典或DataFrame
            filename: 输出文件名，不包含扩展名
            columns: 列名列表，仅当data为列表时使用
            append: 是否追加数据到现有文件
            
        Returns:
            str: 保存的文件路径
        """
        # 生成默认文件名
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data_output_{timestamp}"
        
        # 构建完整文件路径
        output_path = os.path.join(self.output_dir, f"{filename}.csv")
        
        try:
            # 处理不同类型的数据
            if isinstance(data, pd.DataFrame):
                # 如果是DataFrame
                if append and os.path.exists(output_path):
                    # 追加数据
                    data.to_csv(output_path, index=False, encoding='utf-8-sig', mode='a', header=False)
                else:
                    # 直接保存
                    data.to_csv(output_path, index=False, encoding='utf-8-sig')
            elif isinstance(data, list):
                # 如果是列表
                if not data:
                    raise ValueError("数据列表为空")
                
                # 检查列表元素类型
                if isinstance(data[0], dict):
                    # 如果是字典列表，使用字典的键作为列名
                    if columns:
                        fieldnames = columns
                    else:
                        fieldnames = data[0].keys()
                    
                    # 检查文件是否存在
                    file_exists = os.path.exists(output_path)
                    
                    # 确定文件模式
                    mode = 'a' if append and file_exists else 'w'
                    
                    # 确定是否写入表头
                    write_header = not (append and file_exists)
                    
                    with open(output_path, mode, newline='', encoding='utf-8-sig') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        if write_header:
                            writer.writeheader()
                        for row in data:
                            writer.writerow(row)
                elif isinstance(data[0], list):
                    # 如果是列表的列表，使用指定的列名或默认列名
                    file_exists = os.path.exists(output_path)
                    mode = 'a' if append and file_exists else 'w'
                    write_header = not (append and file_exists)
                    
                    with open(output_path, mode, newline='', encoding='utf-8-sig') as f:
                        writer = csv.writer(f)
                        if write_header and columns:
                            writer.writerow(columns)
                        writer.writerows(data)
                else:
                    raise ValueError("列表元素类型不支持")
            else:
                raise ValueError("数据类型不支持")
            
            print(f"数据成功保存到: {output_path}")
            return output_path
        except Exception as e:
            print(f"保存数据时出错: {str(e)}")
            raise
    
    def save_excel_data(self, excel_file_path, output_filename=None):
        """
        读取Excel文件并保存为CSV
        
        Args:
            excel_file_path: Excel文件路径
            output_filename: 输出文件名，不包含扩展名
            
        Returns:
            str: 保存的文件路径
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(excel_file_path)
            
            # 保存为CSV
            return self.save_to_csv(df, output_filename)
        except Exception as e:
            print(f"处理Excel文件时出错: {str(e)}")
            raise

class CaseManager:
    """
    案件管理类，用于处理案件数据的CRUD操作
    """
    
    def __init__(self, data_dir=ROOT_DIR):
        """
        初始化案件管理器
        
        Args:
            data_dir: 数据存储目录，默认为根目录
        """
        self.data_dir = data_dir
        self.cases_file = os.path.join(data_dir, "cases_data.csv")
        self.columns = ['caseTime', 'caseName', 'caseDescription']
        os.makedirs(data_dir, exist_ok=True)
        
        # 如果文件不存在，创建一个空的CSV文件
        if not os.path.exists(self.cases_file):
            self._create_empty_file()
    
    def _create_empty_file(self):
        """
        创建一个空的案件数据CSV文件
        """
        with open(self.cases_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(self.columns)
    
    def get_all_cases(self):
        """
        获取所有案件数据
        
        Returns:
            list: 案件数据列表
        """
        try:
            # 读取CSV文件，指定所有列的数据类型为字符串
            df = pd.read_csv(self.cases_file, dtype=str)
            return df.to_dict('records')
        except Exception as e:
            print(f"读取案件数据时出错: {str(e)}")
            return []
    
    def add_case(self, case_data):
        """
        添加新案件
        
        Args:
            case_data: 案件数据字典
            
        Returns:
            bool: 添加是否成功
        """
        try:
            # 读取现有数据，指定所有列的数据类型为字符串
            df = pd.read_csv(self.cases_file, dtype=str)
            
            # 确保所有值都转换为字符串类型
            case_data_str = {k: str(v) for k, v in case_data.items()}
            
            # 添加新数据
            new_row = pd.DataFrame([case_data_str])
            df = pd.concat([df, new_row], ignore_index=True)
            
            # 保存回文件
            df.to_csv(self.cases_file, index=False, encoding='utf-8-sig')
            
            # 为案件创建文件夹并保存Excel文件
            self._create_case_folder(case_data_str)
            
            print(f"案件添加成功: {case_data_str['caseName']}")
            return True
        except Exception as e:
            print(f"添加案件时出错: {str(e)}")
            return False
    
    def _create_case_folder(self, case_data):
        """
        为案件创建文件夹并保存Excel文件
        
        Args:
            case_data: 案件数据字典
        """
        try:
            # 打印调试信息
            print(f"开始创建案件文件夹，案件数据: {case_data}")
            
            # 生成案件文件夹名称
            case_name = case_data.get('caseName', '未命名案件')
            case_time = case_data.get('caseTime', datetime.now().strftime('%Y%m%d_%H%M%S'))
            
            # 打印调试信息
            print(f"案件名称: {case_name}, 案件时间: {case_time}")
            
            # 清理文件夹名称中的特殊字符
            folder_name = f"{case_time}_{case_name}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            
            # 打印调试信息
            print(f"生成的文件夹名称: {folder_name}")
            
            # 创建案件文件夹
            case_folder = os.path.join(self.data_dir, 'cases', folder_name)
            print(f"案件文件夹路径: {case_folder}")
            
            # 确保cases目录存在
            cases_dir = os.path.join(self.data_dir, 'cases')
            os.makedirs(cases_dir, exist_ok=True)
            print(f"确保cases目录存在: {cases_dir}")
            
            # 创建具体的案件文件夹
            os.makedirs(case_folder, exist_ok=True)
            print(f"创建案件文件夹成功: {case_folder}")
            
            # 创建案件Excel文件
            excel_file = os.path.join(case_folder, f"{case_name}_案件信息.xlsx")
            print(f"Excel文件路径: {excel_file}")
            
            # 将案件数据转换为DataFrame并保存为Excel
            df = pd.DataFrame([case_data])
            df.to_excel(excel_file, index=False)
            print(f"Excel文件保存成功: {excel_file}")
            
            print(f"案件文件夹和Excel文件创建成功: {case_folder}")
        except Exception as e:
            print(f"创建案件文件夹时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_case(self, index, case_data):
        """
        更新案件数据
        
        Args:
            index: 案件索引
            case_data: 新的案件数据
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 读取现有数据，指定所有列的数据类型为字符串
            df = pd.read_csv(self.cases_file, dtype=str)
            
            # 检查索引是否有效
            if index < 0 or index >= len(df):
                raise ValueError("无效的案件索引")
            
            # 更新数据，确保所有值都转换为字符串类型
            for key, value in case_data.items():
                if key in df.columns:
                    # 将值转换为字符串，避免类型不匹配问题
                    df.at[index, key] = str(value)
            
            # 保存回文件
            df.to_csv(self.cases_file, index=False, encoding='utf-8-sig')
            
            # 为更新后的案件创建新的文件夹和Excel文件
            # 先获取更新后的案件数据
            updated_case_data = df.iloc[index].to_dict()
            self._create_case_folder(updated_case_data)
            
            print(f"案件更新成功: {case_data['caseName']}")
            return True
        except Exception as e:
            print(f"更新案件时出错: {str(e)}")
            return False
    
    def delete_case(self, index):
        """
        删除案件
        
        Args:
            index: 案件索引
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 读取现有数据，指定所有列的数据类型为字符串
            df = pd.read_csv(self.cases_file, dtype=str)
            
            # 检查索引是否有效
            if index < 0 or index >= len(df):
                raise ValueError("无效的案件索引")
            
            # 获取要删除的案件数据
            case_data = df.iloc[index].to_dict()
            
            # 删除数据
            df = df.drop(index)
            df = df.reset_index(drop=True)
            
            # 保存回文件
            df.to_csv(self.cases_file, index=False, encoding='utf-8-sig')
            
            # 删除案件对应的文件夹
            self._delete_case_folder(case_data)
            
            print(f"案件删除成功，索引: {index}")
            return True
        except Exception as e:
            print(f"删除案件时出错: {str(e)}")
            return False
    
    def _delete_case_folder(self, case_data):
        """
        删除案件对应的文件夹
        
        Args:
            case_data: 案件数据字典
        """
        try:
            # 生成案件文件夹名称
            case_name = case_data.get('caseName', '未命名案件')
            case_time = case_data.get('caseTime', datetime.now().strftime('%Y%m%d_%H%M%S'))
            
            # 清理文件夹名称中的特殊字符
            folder_name = f"{case_time}_{case_name}".replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            
            # 构建案件文件夹路径
            case_folder = os.path.join(self.data_dir, 'cases', folder_name)
            
            # 删除文件夹及其内容
            if os.path.exists(case_folder):
                import shutil
                shutil.rmtree(case_folder)
                print(f"案件文件夹删除成功: {case_folder}")
        except Exception as e:
            print(f"删除案件文件夹时出错: {str(e)}")
    
    def get_case(self, index):
        """
        获取单个案件数据
        
        Args:
            index: 案件索引
            
        Returns:
            dict: 案件数据字典，若不存在返回None
        """
        try:
            # 读取CSV文件，指定所有列的数据类型为字符串
            df = pd.read_csv(self.cases_file, dtype=str)
            
            # 检查索引是否有效
            if index < 0 or index >= len(df):
                return None
            
            return df.iloc[index].to_dict()
        except Exception as e:
            print(f"获取案件时出错: {str(e)}")
            return None

# 示例用法
if __name__ == "__main__":
    # 创建数据保存器实例
    saver = DataSaver()
    
    # 示例1: 保存字典列表
    sample_data = [
        {"name": "张三", "age": 30, "city": "北京"},
        {"name": "李四", "age": 25, "city": "上海"},
        {"name": "王五", "age": 35, "city": "广州"}
    ]
    saver.save_to_csv(sample_data, "sample_data")
    
    # 示例2: 保存Excel文件为CSV
    # 假设根目录有建模数据121.xlsx文件
    excel_path = os.path.join(ROOT_DIR, "建模数据121.xlsx")
    if os.path.exists(excel_path):
        saver.save_excel_data(excel_path, "modeling_data")
    else:
        print(f"Excel文件不存在: {excel_path}")
