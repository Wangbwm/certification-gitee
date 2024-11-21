from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SysRoom(Base):
    __tablename__ = 'sys_room'
    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String(255), nullable=False)
    room_type = Column(String(255))
    name = Column(String(255), nullable=False)
    status = Column(String(255))
    manager_id = Column(Integer, nullable=False)
    sys_name = Column(String(255))
    def __repr__(self):
        return (f"<SysRoom(id={self.id}, "  
                f"address='{self.address}', "
                f"room_type='{self.room_type if self.room_type else 'None'}',"
                f"name='{self.name}', "  
                f"status='{self.status if self.status else 'None'}"
                f"manager_id='{self.manager_id}', "    
                f"sys_name='{self.sys_name if self.sys_name else 'None'}"
                f"...)>")
