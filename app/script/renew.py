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


def create_user(username, telephone, role_id):
    session = get_session()
    try:
        user = session.query(SysUser).filter_by(username=username, telephone=telephone).first()
        if user:
            # 抛出异常
            raise ValueError(f"User with username '{username}' and telephone '{telephone}' already exists.")
        new_user = SysUser(username=username, telephone=telephone, password=hash_password(INIT_PASSWORD))
        session.add(new_user)
        session.commit()
        # 赋权
        role = session.query(SysUserRole).filter_by(user_id=new_user.id).first()
        if role:
            raise ValueError(f"User with username '{username}' "
                             f"and telephone '{telephone}' already have role '{role.role_id}'.")
        session.add(SysUserRole(role_id=role_id, user_id=new_user.id))
        session.commit()
        print(f"User {username} created successfully.")
    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")
    finally:
        session.close()


def create_manager(username, telephone):
    session = get_session()
    try:
        user = session.query(SysUser).filter_by(username=username, telephone=telephone).first()
        if not user:
            raise ValueError(f"User with username '{username}' and telephone '{telephone}' does not exist.")
        manager = session.query(SysManager).filter_by(user_id=user.id).first()
        if manager:
            raise ValueError(f"User with username '{username}' "
                             f"and telephone '{telephone}' already have manager.")
        session.add(SysManager(user_id=user.id, address='', telephone=telephone))
        session.commit()
        print(f"Manager {username} created successfully.")
    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")
    finally:
        session.close()


def create_room(username, telephone, room):
    session = get_session()
    try:
        user = session.query(SysUser).filter_by(username=username, telephone=telephone).first()
        if not user:
            raise ValueError(f"User with username '{username}' and telephone '{telephone}' does not exist.")
        manager = session.query(SysManager).filter_by(user_id=user.id).first()
        if not manager:
            raise ValueError(f"User with username '{username}' "
                             f"and telephone '{telephone}' does not have manager.")
        room.manager_id = manager.id
        session.add(room)
        session.commit()
        print(f"Room {room.name} created successfully.")
    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")
    finally:
        session.close()


if __name__ == '__main__':
    # 读取原始数据
    table_sheet_1 = pd.read_excel(PATH, sheet_name='人员对应机房详表')
    table_sheet_2 = pd.read_excel(PATH, sheet_name='人员信息')
    table_extra_data = table_sheet_2[['姓名', '部门', '电话号码']]
    table_extra_data = table_extra_data.rename(columns={
        '姓名': 'username', '部门': 'role_id', '电话号码': 'telephone'
    })
    table_extra_data['role_id'] = table_extra_data['role_id'].map(lambda x: 3 if x == '施工队' else 2)
    try:
        # 遍历table_extra_data
        for index, row in table_extra_data.iterrows():
            username = row['username']
            telephone = row['telephone']
            role_id = row['role_id']
            create_user(username, telephone, role_id)
    except Exception as e:
        print(f"An error occurred: {e}")
    table_extra_data = table_sheet_1[
        ['区县', '机房类型', '机房名称', '生命周期状态', '机房长姓名', '机房长电话号码', '动环名称']]
    table_extra_data = table_extra_data.rename(columns={
        '区县': 'address', '机房类型': 'room_type', '机房名称': 'name', '生命周期状态': 'status',
        '机房长姓名': 'username',
        '机房长电话号码': 'telephone', '动环名称': 'sys_name'
    })
    try:
        # 遍历
        for index, row in table_extra_data.iterrows():
            address = row['address']
            room_type = row['room_type']
            name = row['name']
            status = row['status']
            username = row['username']
            telephone = row['telephone']
            sys_name = row['sys_name']
            room = SysRoom(address=address, room_type=room_type, name=name,
                           status=status, manager_id=-1, sys_name=sys_name)
            create_manager(username, telephone)
            create_room(username, telephone, room)
    except Exception as e:
        print(f"An error occurred: {e}")
