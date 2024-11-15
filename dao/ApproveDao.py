import math

import yaml
from sqlalchemy import create_engine, func, true, false
from sqlalchemy.orm import sessionmaker

from Utils.Open import send_open_request
from entity.SysStation import SysStation
from entity.SysApprove import SysApprove
from entity.SysManager import SysManager
from entity.SysOpen import SysOpen
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



def direct_open(current_user, room_id, notes):
    session = get_session()
    try:
        room = session.query(SysRoom).filter_by(id=room_id).first()
        if not room:
            return False, f"申请机房不存在"
        approve = SysApprove(room_id=room_id, manager_id=room.manager_id,
                             user_id=current_user.id, pro_status=True, app_status=True, notes=notes)
        session.add(approve)
        room_open = SysOpen(room_id=room_id, open_status=False,
                            pro_status=True, room_name=room.name, sys_name=room.sys_name)
        session.add(room_open)
        session.flush()
        session.commit()
        room = session.query(SysRoom).filter_by(id=room_id).first()
        station = session.query(SysStation).filter_by(stationName=room.sys_name).first()
        # 查看支不支持远程开门
        if station:
            res = True, f"开门成功"
            # res = send_open_request(station.stationId, station.equipmentId, station.controlid, 1)
            if res[0]:
                return True, f"申请成功"
            return True, f"申请成功，但是开门失败原因：{res[1]}"
        # 不支持远程开门
        return True, f"申请成功, 但是机房不支持远程开门"
    except Exception as e:
        session.rollback()
        return False, f"申请失败，原因：{e}"
    finally:
        session.close()


def approve_open(current_user, room_id, notes):
    session = get_session()
    try:
        room = session.query(SysRoom).filter_by(id=room_id).first()
        if not room:
            return False, f"申请机房不存在"
        approve = SysApprove(room_id=room_id, manager_id=room.manager_id, user_id=current_user.id, pro_status=False,
                             app_status=False, notes=notes)
        session.add(approve)
        session.flush()
        session.commit()
        return True, f"申请成功"
    except Exception as e:
        session.rollback()
        return False, f"申请失败，原因：{e}"
    finally:
        session.close()


def get_approve_list(page, status, current_user):
    total_pages = 0
    all_apps_list = []
    apps_dict_list = {}
    page_size = 5
    session = get_session()
    try:
        role_id = session.query(SysUserRole).filter_by(user_id=current_user.id).first().role_id
        total_count = None
        apps = None
        if role_id == 1:
            total_count = session.query(SysApprove).filter_by(pro_status=status).count()
            apps = session.query(SysApprove).filter_by(pro_status=status)
        else:
            manager = session.query(SysManager).filter_by(user_id=current_user.id).first()
            if not manager:
                return False, f"你没有权限操作"
            manager_id = manager.id
            total_count = session.query(SysApprove).filter_by(manager_id=manager_id, pro_status=status).count()
            apps = session.query(SysApprove).filter_by(manager_id=manager_id, pro_status=status)
        offset = (page - 1) * page_size
        all_apps_list = apps.offset(offset).limit(page_size).all()
        # 计算总页数
        total_pages = math.ceil(total_count / page_size)
        apps_dict_list = [
            {
                "id": app.id,
                "room_id": app.room_id,
                "room_name": session.query(SysRoom).filter_by(id=app.room_id).first().name,
                "manager_id": app.manager_id,
                "manager_name": session.query(SysUser)
                .filter_by(id=session.query(SysManager).filter_by(id=app.manager_id).first().user_id).first().username,
                "manager_telephone": session.query(SysManager).filter_by(id=app.manager_id).first().telephone,
                "user_id": app.user_id,
                "user_name": session.query(SysUser).filter_by(id=app.user_id).first().username,
                "user_telephone": session.query(SysUser).filter_by(id=app.user_id).first().telephone,
                "pro_status": app.pro_status,
                "app_status": app.app_status,
                "notes": app.notes
            } for app in all_apps_list
        ]
        return True, f"成功", total_pages, apps_dict_list
    except Exception as e:
        session.rollback()
        return False, f"错误: {e}", total_pages, apps_dict_list
    finally:
        session.close()


def approve_approve(approve_id, approve_status, current_user):
    session = get_session()
    try:
        approve = session.query(SysApprove).filter_by(id=approve_id).first()
        if not approve:
            return False, f"审批工单不存在"
        role_id = session.query(SysUserRole).filter_by(user_id=current_user.id).first().role_id
        user_id = session.query(SysManager).filter_by(id=approve.manager_id).first().user_id
        if user_id != current_user.id and role_id != 1:
            return False, f"你没有权限审批该申请"
        approve.app_status = approve_status
        approve.pro_status = True
        room = session.query(SysRoom).filter_by(id=approve.room_id).first()
        room_open = SysOpen(room_id=room.id, open_status=False,
                            pro_status=False, room_name=room.name, sys_name=room.sys_name)
        session.add(room_open)
        session.flush()
        session.commit()
        station = session.query(SysStation).filter_by(stationName=room.sys_name).first()
        # 查看支不支持远程开门
        if station:
            res = send_open_request(station.stationId, station.equipmentId, station.controlid, 1)
            if res[0]:
                return True, f"审批成功"
            return True, f"审批成功，但是开门失败原因：{res[1]}"
        # 不支持远程开门
        return True, f"审批成功, 但是机房不支持远程开门"
    except Exception as e:
        session.rollback()
        return False, f"审批失败，原因：{e}"
    finally:
        session.close()


def delete_approve(approve_id):
    session = get_session()
    try:
        approve = session.query(SysApprove).filter_by(id=approve_id).first()
        if not approve:
            return False, f"审批工单不存在"
        session.delete(approve)
        session.flush()
        session.commit()
        return True, f"删除成功"
    except Exception as e:
        session.rollback()
        return False, f"删除失败，原因：{e}"
    finally:
        session.close()