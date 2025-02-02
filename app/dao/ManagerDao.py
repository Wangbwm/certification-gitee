import math

from app.dao.Session import get_session
from app.entity.SysManager import SysManager
from app.entity.SysUser import SysUser


def get_manager(user):
    session = get_session()
    try:
        # 检查用户是否已存在
        existing_user = session.query(SysUser).filter_by(username=user.username, telephone=user.telephone).first()
        if existing_user:
            user_id = user.id
            existing_user = session.query(SysManager).filter_by(user_id=user_id).first()
            if existing_user:
                return True, existing_user
            else:
                return False, "用户未绑定机房长"
        else:
            return False, "用户不存在"
    except Exception as e:
        session.rollback()
        print(e)
        return False, "服务器内部错误"
    finally:
        session.close()


def create_manager(sys_manager):
    session = get_session()
    try:
        existing_manager = session.query(SysManager).filter_by(user_id=sys_manager.user_id)
        if existing_manager.first():
            return False, "用户已绑定机房长"
        session.add(sys_manager)
        session.flush()
        session.commit()
        return True, f"用户{sys_manager.user_id}绑定机房长成功"
    except Exception as e:
        session.rollback()
        print(e)
        return False, "服务器内部错误"
    finally:
        session.close()


def delete_manager(target_id):
    session = get_session()
    try:
        existing_manager = session.query(SysManager).filter_by(user_id=target_id)
        if existing_manager.first():
            existing_manager.delete()
            session.flush()
            session.commit()
            return True, f"用户{target_id}解绑机房长成功"
        else:
            return False, "用户未绑定机房长"
    except Exception as e:
        session.rollback()
        print(e)
        return False, "服务器内部错误"
    finally:
        session.close()


def user_change(current_user, address):
    session = get_session()
    try:
        # 检查用户是否已存在
        existing_user = session.query(SysManager).filter_by(user_id=current_user.id).first()
        if existing_user:
            existing_user.address = address
            session.flush()
            session.commit()
            return True, f"用户{current_user.username}修改地址成功"
        else:
            return False, "用户未绑定机房长"
    except Exception as e:
        session.rollback()
        print(e)
        return False, "服务器内部错误"
    finally:
        session.close()


def get_manager_list(page):
    total_pages = 0
    all_managers_list = []
    managers_dict_list = {}
    page_size = 5
    session = get_session()
    try:
        # 分页查询列表
        total_count = session.query(SysManager).count()
        offset = (page - 1) * page_size
        managers = session.query(SysManager)
        all_managers_list = managers.offset(offset).limit(page_size).all()
        # 计算总页数
        total_pages = math.ceil(total_count / page_size)

        managers_dict_list = [
            {
                "id": manager.id,
                "manager_name": session.query(SysUser)
                .filter_by(id=manager.user_id).first().username,
                "manager_telephone": session.query(SysUser)
                .filter_by(id=manager.user_id).first().telephone,
                "manager_address": manager.address
            } for manager in all_managers_list
        ]
        return True, f"成功", total_pages, managers_dict_list
    except Exception as e:
        session.rollback()
        return False, f"错误: {e}", total_pages, managers_dict_list
    finally:
        session.close()


def get_user_by_id(manager_id):
    session = get_session()
    try:
        user = session.query(SysUser)\
            .filter_by(id=session.query(SysManager).filter_by(manager_id=manager_id).first().user_id).first()
        return True, f"成功", user
    except Exception as e:
        session.rollback()
        return False, f"错误: {e}", None
    finally:
        session.close()


def selectManagerByTelephone(params):
    session = get_session()
    try:
        # 检查用户是否已存在
        existing_user = session.query(SysManager).filter_by(telephone=params).all()
        if existing_user:
            user_list = [
                session.query(SysUser).filter_by(id=manager.user_id).first()
                for manager in existing_user
            ]
            # 处理可能的 None 值
            valid_users = [user for user in user_list if user is not None]
            return True, valid_users
        else:
            return False, "未找到机房长"
    except Exception as e:
        session.rollback()
        print(e)
        return None
    finally:
        session.close()


def selectManagerByName(params):
    session = get_session()
    try:
        # 检查用户是否已存在
        existing_user = session.query(SysUser).filter(SysUser.username.like(f"%{params}%")).all()
        if existing_user:
            # 找到机房长
            manager_list = [
                session.query(SysManager).filter_by(user_id=user.id).first()
                for user in existing_user
            ]
            # 处理可能的 None 值
            valid_manager = [manager for manager in manager_list if manager is not None]
            # 根据valid_manager的user_id筛选existing_user
            existing_user = [user for user in existing_user if user.id in [manager.user_id for manager in valid_manager]]
            if existing_user:
                return True, existing_user
            return False, "未找到机房长"
        else:
            return False, "未找到机房长"
    except Exception as e:
        session.rollback()
        print(e)
        return None
    finally:
        session.close()