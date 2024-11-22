from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# 定义获取北京时间的函数
def get_beijing_time():
    return datetime.now(timezone(timedelta(hours=8)))

class SysPho(Base):
    __tablename__ = 'sys_pho'

    id = Column(Integer, primary_key=True, autoincrement=True)
    app_id = Column(Integer, nullable=False)
    type = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    create_time = Column(DateTime, nullable=False, default=get_beijing_time)

    def __repr__(self):
        return "<SysPho(id='%s', app_id='%s', type='%s', file_path='%s', create_time='%s')>" % \
            (self.id, self.app_id, self.type, self.file_path, self.create_time)