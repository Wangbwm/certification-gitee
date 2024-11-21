from .Session import get_session
from ..entity.SysPho import SysPho


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
