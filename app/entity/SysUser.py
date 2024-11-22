from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# 定义获取北京时间的函数
def get_beijing_time():
    return datetime.now(timezone(timedelta(hours=8)))

class SysUser(Base):
    __tablename__ = 'sys_user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), nullable=False)
    password = Column(String(255))
    telephone = Column(String(20))
    create_time = Column(DateTime, nullable=False, default=get_beijing_time)

    def __repr__(self):
        return (f"<SysUser(id={self.id}, "  
                f"user_name='{self.username}', "  
                f"tel='{self.telephone if self.telephone else 'None'}', "  
                f"create_time='{self.create_time.isoformat() if self.create_time else 'None'}', "  
                f"...)>")
