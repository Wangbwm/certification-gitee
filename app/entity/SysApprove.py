from datetime import datetime, timezone, timedelta

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# 定义获取北京时间的函数
def get_beijing_time():
    return datetime.now(timezone(timedelta(hours=8)))

class SysApprove(Base):
    __tablename__ = 'sys_approve'
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, nullable=False)
    manager_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    pro_status = Column(Boolean, nullable=False)
    app_status = Column(Boolean, nullable=False)
    open_status = Column(Boolean, nullable=False)
    create_time = Column(DateTime, nullable=False, default=get_beijing_time)
    notes = Column(String(255))
    def __repr__(self):
        return "<SysApprove(id='%s', room_id='%s', manager_id='%s', user_id='%s', pro_status='%s', app_status='%s', create_time='%s', notes='%s')>" % (
            self.id, self.room_id, self.manager_id, self.user_id, self.pro_status, self.app_status, self.create_time, self.notes)
