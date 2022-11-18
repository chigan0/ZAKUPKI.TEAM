from typing import Union, List

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Session

from database import Base


class FootageCategory(Base):
	__tablename__ = 'footage_category'

	id = Column(Integer, primary_key=True)
	cate_name = Column(String(80), unique=True)
	videos_id = relationship('Videos', cascade="all, delete")

	def __repr__(self,):
		return self.cate_name


class Videos(Base):
	__tablename__ = 'videos'

	id = Column(Integer, primary_key=True)
	footage_cate_id = Column(Integer, ForeignKey('footage_category.id'))
	videos_name = Column(String(500), nullable=False)
	name = Column(String(50), unique=True)


async def new_footage_cate(db: Session, cate_name: str) -> None:
	footage_cate = FootageCategory(cate_name=cate_name)
	db.add(footage_cate)


async def new_video(db: Session, cate_id: int, filename: str, video_name: str) -> None:
	video = Videos(footage_cate_id=cate_id, videos_name=filename, name=video_name)
	db.add(video)


async def delete_footage_cate(db: Session, cate_id: int) -> None:
	footage_cate = db.query(FootageCategory).get(cate_id)
	db.delete(footage_cate)


async def delete_video(db: Session, video_id: int) -> None:
	video = db.query(Videos).get(video_id)
	db.delete(video)


async def all_footage_category(db: Session) -> List[FootageCategory]:
	return db.query(FootageCategory).all()


async def all_videos(db: Session) -> List[Videos]:
	return db.query(Videos).all()


async def get_videos(db: Session, footage_cate_id: int) -> List[Videos]:
	return db.query(Videos).filter(Videos.footage_cate_id == footage_cate_id).all()
