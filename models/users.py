from typing import Union

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship, Session

from database import Base


class AdminList(Base):
	__tablename__ = 'admin_list'

	id = Column(Integer, primary_key=True)
	user_tg_id = Column(String(40), unique=True)

	def __repr__(self,):
		return self.user_tg_id


async def add_admin_list(db: Session, user_tg_id: str) -> None:
	admin_list = AdminList(user_tg_id=user_tg_id)
	db.add(admin_list)


async def get_admin(db: Session, user_tg_id: str) -> Union[AdminList, None]:
	return db.query(AdminList).filter(AdminList.user_tg_id == user_tg_id).one_or_none()
