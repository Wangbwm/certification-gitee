import math

import yaml
from sqlalchemy import create_engine, func, true, false
from sqlalchemy.orm import sessionmaker

from Utils.Open import send_open_request
from entity.SysPho import SysPho
from entity.SysStation import SysStation
from entity.SysApprove import SysApprove
from entity.SysManager import SysManager
from entity.SysRole import SysRole
from entity.SysRoom import SysRoom
from entity.SysUser import SysUser
from entity.SysUserRole import SysUserRole

# 读取YAML配置文件
with open('config/database.yaml', 'r') as file:
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


def save_pho(file_location, app_id, app_type):
    session = get_session()
    try:
        pho = SysPho(app_id=app_id, file_path=file_location, type=app_type)
        session.add(pho)
        session.commit()
        return True, f"上传成功"
    except Exception as e:
        session.rollback()
        return False, f"上传失败，原因：{e}"
    finally:
        session.close()


def get_photograph(app_id):
    session = get_session()
    try:
        photos = session.query(SysPho).filter_by(app_id=app_id).all()
        if not photos:
            return False, f"未找到相关图片"
        photos_dict = [{
            "path": pho.file_path,
            "type": pho.type
        } for pho in photos]
        return True, photos_dict
    except Exception as e:
        return False, f"获取失败，原因：{e}"
    finally:
        session.close()
