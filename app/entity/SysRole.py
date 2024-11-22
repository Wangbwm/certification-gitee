from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# 定义获取北京时间的函数
def get_beijing_time():
    return datetime.now(timezone(timedelta(hours=8)))

class SysRole(Base):
    __tablename__ = 'sys_role'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    create_time = Column(DateTime, nullable=False, default=get_beijing_time)

