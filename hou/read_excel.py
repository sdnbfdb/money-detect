import pandas as pd

def read_excel_file(file_path):
    """
    读取Excel文件并返回数据
    """
    try:
        # 读取Excel文件的所有工作表
        excel_file = pd.ExcelFile(file_path)
        all_sheets_data = {}
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            # 将DataFrame转换为字典格式，便于JSON序列化
            all_sheets_data[sheet_name] = df.fillna('').to_dict(orient='records')
        
        return all_sheets_data
    except Exception as e:
        print(f"读取Excel文件时出错: {e}")
        return None

if __name__ == "__main__":
    file_path = r"C:\Users\sanjin\Desktop\新建文件夹\建模数据121.xlsx"
    data = read_excel_file(file_path)
    
    if data:
        print("Excel文件内容:")
        for sheet_name, sheet_data in data.items():
            print(f"\n工作表: {sheet_name}")
            print(f"行数: {len(sheet_data)}")
            if sheet_data:
                print("前几行数据:", sheet_data[:3])  # 显示前3行
    else:
        print("无法读取Excel文件")