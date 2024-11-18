import math
from datetime import datetime

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


def get_room_info(session: Session, room_id: int):
    """根据房间ID获取房间的名称和系统名称"""
    room = session.query(SysRoom).filter_by(id=room_id).first()
    if room:
        return {
            'room_name': room.name,
            'sys_name': room.sys_name
        }
    return {'room_name': '', 'sys_name': ''}


def get_manager_info(session: Session, manager_id: int):
    """根据经理ID获取经理的相关信息"""
    manager = session.query(SysManager).filter_by(id=manager_id).first()
    if manager:
        user = session.query(SysUser).filter_by(id=manager.user_id).first()
        if user:
            return {
                'manager_name': user.username,
                'manager_telephone': manager.telephone
            }
    return {'manager_name': '', 'manager_telephone': ''}


def get_user_info(session: Session, user_id: int):
    """根据用户ID获取用户的相关信息"""
    user = session.query(SysUser).filter_by(id=user_id).first()
    if user:
        return {
            'user_name': user.username,
            'user_telephone': user.telephone
        }
    return {'user_name': '', 'user_telephone': ''}


def get_sys_station_info(session: Session, station_name: str):
    """根据站点名称获取站点状态和备注"""
    station = session.query(SysStation).filter_by(stationName=station_name).first()
    if station:
        return {
            'sys_status': station.status,
            'sys_notes': station.notes
        }
    return {'sys_status': False, 'sys_notes': ''}


def construct_apps_dict_list(session: Session, all_apps_list: list):
    """根据应用列表构造应用字典列表"""
    apps_dict_list = [
        {
            "id": app.id,
            "room_id": app.room_id,
            **get_room_info(session, app.room_id),
            "manager_id": app.manager_id,
            **get_manager_info(session, app.manager_id),
            "user_id": app.user_id,
            **get_user_info(session, app.user_id),
            "pro_status": app.pro_status,
            "app_status": app.app_status,
            "open_status": app.open_status,
            **get_sys_station_info(session, get_room_info(session, app.room_id)['sys_name']),
            "create_time": app.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "notes": app.notes
        } for app in all_apps_list
    ]
    return apps_dict_list

def construct_apps_dict_list_msg(session: Session, all_apps_list: list):
    """根据应用列表构造应用字典列表"""
    apps_dict_list = [
        {
            "id": approve.id,
            "room_id": approve.room_id,
            **get_room_info(session, approve.room_id),
            "manager_id": approve.manager_id,
            **get_manager_info(session, approve.manager_id),
            "user_id": approve.user_id,
            **get_user_info(session, approve.user_id),
            "pro_status": approve.pro_status,
            "app_status": approve.app_status,
            "open_status": approve.open_status,
            **get_sys_station_info(session, get_room_info(session, approve.room_id)['sys_name']),
            "create_time": str(approve.create_time),
            "notes": approve.notes,
            "error_msg": "无开门照片" if approve.open_status else "无关门照片"
        } for approve in all_apps_list
    ]
    return apps_dict_list


def direct_open(current_user, room_id, notes):
    session = get_session()
    try:
        room = session.query(SysRoom).filter_by(id=room_id).first()
        if not room:
            return False, f"申请机房不存在"
        approve = SysApprove(room_id=room_id, manager_id=room.manager_id,
                             user_id=current_user.id, pro_status=True, app_status=True, open_status=False, notes=notes)
        session.add(approve)
        session.flush()
        session.commit()
        return True, f"申请成功"
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
        # 调用方法构造 apps_dict_list
        apps_dict_list = construct_apps_dict_list(session, all_apps_list)
        return True, f"成功", total_pages, apps_dict_list
    except Exception as e:
        session.rollback()
        return False, f"错误: {e}", total_pages, apps_dict_list
    finally:
        session.close()


def get_approve_me(page, pro_status, current_user):
    total_pages = 0
    all_apps_list = []
    apps_dict_list = {}
    page_size = 5
    session = get_session()
    try:
        total_count = session.query(SysApprove).filter_by(user_id=current_user.id, pro_status=pro_status).count()
        apps = session.query(SysApprove).filter_by(user_id=current_user.id, pro_status=pro_status)
        offset = (page - 1) * page_size
        all_apps_list = apps.offset(offset).limit(page_size).all()
        # 计算总页数
        total_pages = math.ceil(total_count / page_size)
        apps_dict_list = construct_apps_dict_list(session, all_apps_list)
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
        session.flush()
        session.commit()
        return True, f"审批成功"
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


def open_room(approve_id, current_user):
    session = get_session()
    try:
        user = session.query(SysUser).filter_by(id=current_user.id).first()
        if not user:
            return False, f"用户不存在"
        approve = session.query(SysApprove).filter_by(id=approve_id).first()
        role = session.query(SysUserRole).filter_by(user_id=current_user.id).first()
        if role.role_id != 1 and user.id != approve.user_id:
            return False, f"你没有权限操作"
        # 查看工单创建时间不能超过24h
        if (datetime.now() - approve.create_time).total_seconds() > 86400:
            return False, f"工单已过期，请联系管理员重新申请"
        # 看是否支持远程开门
        room = session.query(SysRoom).filter_by(id=approve.room_id).first()
        if not room:
            return False, f"未找到工单请求机房"
        station = session.query(SysStation).filter_by(stationName=room.sys_name).first()
        if not station:
            return False, f"未找到工单请求站点信息，请联系相关人员"
        # 调用远程开门接口
        if station.status:
            # result = send_open_request(station.stationId, station.equipmentId, station.controlId, 1)
            result = True, "success"
            if result[0]:
                approve.open_status = True
                session.flush()
                session.commit()
                return True, f"开门成功"
            else:
                return False, f"远程开门失败，请联系管理员开门"
        # 不能调用远程开门接口
        approve.open_status = True
        session.flush()
        session.commit()
        return True, f"当前站点未开启远程开门，相关信息：{station.notes}"
    except Exception as e:
        session.rollback()
        return False, f"开门失败，原因：{e}"
    finally:
        session.close()


def close_room(app_id, current_user):
    session = get_session()
    try:
        user = session.query(SysUser).filter_by(id=current_user.id).first()
        if not user:
            return False, f"用户不存在"
        approve = session.query(SysApprove).filter_by(id=app_id).first()
        role = session.query(SysUserRole).filter_by(user_id=current_user.id).first()
        if role.role_id != 1 and user.id != approve.user_id:
            return False, f"你没有权限操作"
        approve.open_status = False
        session.flush()
        session.commit()
        return True, f"关门成功"
    except Exception as e:
        session.rollback()
        return False, f"错误: {e}"
    finally:
        session.close()


def get_approve_error_me(current_user, page):
    session = get_session()
    page_size = 5
    offset = (page - 1) * page_size

    try:
        manager = session.query(SysManager).filter_by(user_id=current_user.id).first()
        if not manager:
            return False, {"message": "无权限"}

        # 获取当前用户的所有工单
        approve_list_open = session.query(SysApprove).filter_by(manager_id=manager.id, app_status=True,
                                                                open_status=True).all()
        approve_list_close = session.query(SysApprove).filter_by(manager_id=manager.id, app_status=True,
                                                                 open_status=False).all()

        # 过滤没有开门照片的工单
        approve_list_open = [approve for approve in approve_list_open if
                             not session.query(SysPho).filter_by(app_id=approve.id, type="in").all()]

        # 过滤有关门照片但没有关门照片的工单
        approve_list_close = [approve for approve in approve_list_close if
                              session.query(SysPho).filter_by(app_id=approve.id,
                                                              type="in").all() and not session.query(SysPho).filter_by(
                                  app_id=approve.id, type="out").all()]

        # 合并两个列表
        all_approves = approve_list_open + approve_list_close

        # 计算总页数
        total_pages = (len(all_approves) + page_size - 1) // page_size

        # 分页
        approves = all_approves[offset:offset + page_size]

        app_list_dict = construct_apps_dict_list_msg(session, approves)
        return True, total_pages, app_list_dict
    except Exception as e:
        return False, {"message": str(e)}
    finally:
        session.close()


def get_approve_error_list(current_user, page):
    session = get_session()
    page_size = 5
    offset = (page - 1) * page_size
    try:
        # 获取当前用户的所有工单
        approve_list_open = session.query(SysApprove).filter_by(app_status=True,
                                                                open_status=True).all()
        approve_list_close = session.query(SysApprove).filter_by(app_status=True,
                                                                 open_status=False).all()

        # 过滤没有开门照片的工单
        approve_list_open = [approve for approve in approve_list_open if
                             not session.query(SysPho).filter_by(app_id=approve.id, type="in").all()]

        # 过滤有关门照片但没有关门照片的工单
        approve_list_close = [approve for approve in approve_list_close if
                              session.query(SysPho).filter_by(app_id=approve.id,
                                                              type="in").all() and not session.query(SysPho).filter_by(
                                  app_id=approve.id, type="out").all()]

        # 合并两个列表
        all_approves = approve_list_open + approve_list_close

        # 计算总页数
        total_pages = (len(all_approves) + page_size - 1) // page_size

        # 分页
        approves = all_approves[offset:offset + page_size]

        app_list_dict = construct_apps_dict_list_msg(session, approves)
        return True, total_pages, app_list_dict
    except Exception as e:
        return False, {"message": str(e)}
    finally:
        session.close()
