import os

from sqlalchemy import create_engine, func, true, false
from sqlalchemy.orm import sessionmaker

import yaml


def get_db_config():
    # 获取环境变量，如果ENV变量没有设置，则默认为'dev'
    env = os.getenv('ENV', 'dev')

    # 根据环境变量加载相应的数据库配置
    with open('config/database.yaml', 'r') as file:
        db_config = yaml.safe_load(file)

    # 检查环境变量是否有效，并选择相应的配置
    if env in db_config['mysql']:
        return db_config['mysql'][env]
    else:
        raise ValueError(f"Unsupported environment: {env}")


# 使用函数获取数据库配置
default_db_config = get_db_config()

# 创建SQLAlchemy引擎
engine = create_engine(
    f"mysql+pymysql://{default_db_config['user']}:{default_db_config['password']}@{default_db_config['host']}:{default_db_config['port']}/{default_db_config['database']}?charset=utf8")

# 创建会话类型
Session = sessionmaker(bind=engine)


def get_session():
    return Session()
