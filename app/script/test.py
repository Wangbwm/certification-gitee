import pandas as pd
import os
import yaml
from sqlalchemy import create_engine, func, true, false
from sqlalchemy.orm import sessionmaker

from Utils.hash import hash_password
from entity.SysManager import SysManager
from entity.SysRoom import SysRoom
from entity.SysUser import SysUser
from entity.SysUserRole import SysUserRole


# 找到renew_file目录最新xlsx文件
def find_latest_xlsx(directory):
    files = [f for f in os.listdir(directory) if f.endswith('.xlsx')]
    if not files:
        return None
    latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
    return os.path.join(directory, latest_file)


PATH = find_latest_xlsx('../renew_file')
INIT_PASSWORD = 'password'
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

session = get_session()
# 将所有role_id = 3 改为2
session.query(SysUserRole).filter(SysUserRole.role_id == 3).update({'role_id': 2})
session.commit()