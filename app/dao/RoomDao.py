import math

from .Session import get_session, Session
from ..entity.SysManager import SysManager
from ..entity.SysRoom import SysRoom
from ..entity.SysStation import SysStation
from ..entity.SysUser import SysUser


def get_manager_info(session: Session, manager_id: int):
    """根据经理ID获取经理的相关信息"""
    manager = session.query(SysManager).filter_by(id=manager_id).first()
    if manager:
        user = session.query(SysUser).filter_by(id=manager.user_id).first()
        if user:
            return {
                'manager_name': user.username,
                'manager_telephone': user.telephone
            }
    return {'manager_name': '', 'manager_telephone': ''}

def get_sys_station_info(session: Session, station_name: str):
    """根据站点名称获取站点状态和备注"""
    station = session.query(SysStation).filter_by(stationName=station_name).first()
    if station:
        return {
            'sys_status': station.status,
            'sys_notes': station.notes
        }
    return {'sys_status': False, 'sys_notes': ''}

def construct_rooms_dict_list(session: Session, all_rooms_list: list):
    """根据房间列表构造房间字典列表"""
    rooms_dict_list = [
        {
            "id": room.id,
            "address": room.address,
            "name": room.name,
            "manager_id": room.manager_id,
            **get_manager_info(session, room.manager_id),
            "room_type": room.room_type,
            "status": room.status,
            "sys_name": room.sys_name,
            **get_sys_station_info(session, room.sys_name)
        } for room in all_rooms_list
    ]
    return rooms_dict_list

def get_room_list(page):
    total_pages = 0
    all_rooms_list = []
    rooms_dict_list = {}
    page_size = 5
    session = get_session()
    try:
        # 分页查询列表
        total_count = session.query(SysRoom).count()
        offset = (page - 1) * page_size
        rooms = session.query(SysRoom)
        all_rooms_list = rooms.offset(offset).limit(page_size).all()
        # 计算总页数
        total_pages = math.ceil(total_count / page_size)

        # 调用方法构造 rooms_dict_list
        rooms_dict_list = construct_rooms_dict_list(session, all_rooms_list)
        return True, f"成功", total_pages, rooms_dict_list
    except Exception as e:
        session.rollback()
        return False, f"错误: {e}", total_pages, rooms_dict_list
    finally:
        session.close()


def get_room_by_name(name):
    session = get_session()
    try:
        # 根据name模糊搜索
        rooms = session.query(SysRoom).filter(SysRoom.name.like(f"%{name}%")).all()

        if rooms:
            # 调用方法构造 rooms_dict_list
            rooms_dict_list = construct_rooms_dict_list(session, rooms)
            return True, rooms_dict_list
        return False, "未找到该机房"
    except Exception as e:
        session.rollback()
        return False, f"错误: {e}"
    finally:
        session.close()


def create_room(sys_room):
    session = get_session()
    try:
        exiting_room = session.query(SysRoom).filter_by(name=sys_room.name)
        exiting_manager = session.query(SysManager).filter_by(id=sys_room.manager_id)
        if exiting_room.first():
            return False, "该机房已存在"
        if not exiting_manager.first():
            return False, "数据库没有指定的机房长"
        session.add(sys_room)
        session.flush()
        session.commit()
        return True, f"机房：{sys_room.name}添加成功"
    except Exception as e:
        session.rollback()
        return False, f"错误: {e}"
    finally:
        session.close()


def delete_room_by_name(name):
    session = get_session()
    try:
        room = session.query(SysRoom).filter_by(name=name).first()
        if not room:
            return False, "未找到该机房"
        session.delete(room)
        session.flush()
        session.commit()
        return True, f"已删除该机房：{room.name}"
    except Exception as e:
        session.rollback()
        return False, f"错误: {e}"
    finally:
        session.close()


def change_room(sys_room):
    session = get_session()
    try:
        room = session.query(SysRoom).filter_by(name=sys_room.name).first()
        if not room:
            return False, "未找到该机房"
        sys_room.id = room.id
        # 更新
        session.merge(sys_room)
        session.flush()
        session.commit()
        return True, f"已修改该机房：{room.name}"
    except Exception as e:
        session.rollback()
        return False, f"错误: {e}"
    finally:
        session.close()


def get_room_by_id(room_id):
    session = get_session()
    try:
        room = session.query(SysRoom).filter_by(id=room_id).first()
        if not room:
            return False, "未找到该机房"
        all_rooms_list = [room]
        # 调用方法构造 rooms_dict_list
        rooms_dict_list = construct_rooms_dict_list(session, all_rooms_list)
        room = rooms_dict_list[0]
        return True, room
    except Exception as e:
        session.rollback()
        return False, f"错误: {e}"
    finally:
        session.close()


def delete_room_by_id(room_id):
    session = get_session()
    try:
        room = session.query(SysRoom).filter_by(id=room_id).first()
        if not room:
            return False, "未找到该机房"
        session.delete(room)
        session.flush()
        session.commit()
        return True, f"已删除该机房：{room.name}"
    except Exception as e:
        session.rollback()
        return False, f"错误: {e}"
    finally:
        session.close()
