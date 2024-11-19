import pandas as pd
import os
import yaml
from sqlalchemy import create_engine, func, true, false
from sqlalchemy.orm import sessionmaker
from entity.SysStation import SysStation


def find_latest_xlsx(directory):
    files = [f for f in os.listdir(directory) if f.endswith('.xlsx')]
    if not files:
        return None
    latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
    return os.path.join(directory, latest_file)


PATH = find_latest_xlsx('../renew_file')
# 读取YAML配置文件
with open('../config/database.yaml', 'r') as file:
    db_config = yaml.safe_load(file)
default_db_config = db_config['mysql']

# 创建SQLAlchemy引擎
engine = create_engine(
    f"mysql+pymysql://{default_db_config['user']}:{default_db_config['password']}@{default_db_config['host']}:{default_db_config['port']}/{default_db_config['database']}?charset=utf8")

# 创建会话类型
Session = sessionmaker(bind=engine)


# 创建会话实例
def get_session():
    return Session()

def create_station(station):
    session = get_session()
    try:
        ex_station = session.query(SysStation).filter_by(stationName=station.stationName).first()
        if ex_station:
            raise Exception(f"已存在该站点{station.stationName}")
        else:
            session.add(station)
            session.commit()
            print(f"{station.stationName} 添加成功 ")
            return True
    except Exception as e:
        session.rollback()
        print(f"{station.stationName} 添加失败，原因：{e}")
        return False
    finally:
        session.close()

if __name__ == '__main__':
    # 读取原始数据
    table_sheet_1 = pd.read_excel(PATH, sheet_name='需核实填写')
    # 提取表格式
    df = pd.DataFrame(table_sheet_1)
    # 保留第2、6、7、8列
    df = df.iloc[:, [1, 8, 9, 10, 11]]
    # 保留是否可远程开门列为空的数据
    df = df[df['是否可远程开门'].isnull()]
    # 去除动环名称列为空的数据
    df = df[df['动环名称'].notnull()]
    # 遍历
    for index, row in df.iterrows():
        stationArea = row['区县']
        stationName = row['动环名称']
        status = False
        # 组合第3列和第5列的内容，处理 NaN 值
        col3_value = '' if pd.isna(row[df.columns[2]]) else str(row[df.columns[2]])
        col5_value = '' if pd.isna(row[df.columns[4]]) else str(row[df.columns[4]])
        notes = f"{col3_value} + {col5_value}"
        station = SysStation(stationArea=stationArea, stationName=stationName, notes=notes, status=status)
        create_station(station)
    print("数据处理完成")