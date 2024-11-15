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
        ex_station = session.query(SysStation).filter_by(stationId=station.stationId).first()
        if ex_station:
            raise Exception(f"已存在该站点{station.stationName}")
        else:
            session.add(station)
            session.commit()
            print(f"{station.stationName} 添加成功 ")
            return True, f"添加成功"
    except Exception as e:
        session.rollback()
        print(f"{station.stationName} 添加失败，原因：{e}")
        return False, f"添加失败，原因：{e}"
    finally:
        session.close()


if __name__ == '__main__':
    # 读取原始数据
    table_sheet_1 = pd.read_excel(PATH, sheet_name='Sheet1')
    try:
        # 遍历
        for index, row in table_sheet_1.iterrows():
            stationArea = row['stationArea']
            stationType = row['stationType']
            stationId = row['stationId']
            stationName = row['stationName']
            equipmentId = row['equipmentId']
            name = row['name']
            controlId = row['controlId']
            station = SysStation(stationArea=stationArea, stationType=stationType,
                                 stationId=stationId, stationName=stationName,
                                 equipmentId=equipmentId, name=name, controlId=controlId)
            create_station(station)

    except Exception as e:
        print('e')

