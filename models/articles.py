from typing import Union, List

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Session

from database import Base


class ArticlesCategory(Base):
	__tablename__ = 'articles_category'

	id = Column(Integer, primary_key=True)
	cate_name = Column(String(80), unique=True)
	articles = relationship('Articles', cascade="all, delete")


class Articles(Base):
	__tablename__ = 'articles'

	id = Column(Integer, primary_key=True)
	articles_cate_id = Column(Integer, ForeignKey('articles_category.id'))
	articles_name = Column(String(500), nullable=False)
	articles_url = Column(String(750), unique=True)

	def __repr__(self,):
		return self.articles_url


async def new_article_cate(db: Session, cate_name: str) -> None:
	footage_cate = ArticlesCategory(cate_name=cate_name)
	db.add(footage_cate)


async def delete_article_cate(db: Session, cate_id: int) -> None:
	article = db.query(ArticlesCategory).get(cate_id)
	db.delete(article)


async def delete_article_id(db: Session, articles_id: int) -> None:
	article = db.query(Articles).get(articles_id)
	db.delete(article)


async def add_new_article(db: Session, cate_id: int, article_name: str, article_url: str) -> None:
	article = Articles(articles_cate_id=cate_id, articles_name=article_name, articles_url=article_url)
	db.add(article)


async def all_articles_category(db: Session) -> List[ArticlesCategory]:
	return db.query(ArticlesCategory).all()


async def all_articles(db: Session) -> List[Articles]:
	return db.query(Articles).all()


async def get_article(db: Session, articles_id: int) -> Union[None, Articles]:
	return db.query(Articles).get(articles_id)


async def article_in_cate(db: Session, cate_id: int) -> List[Articles]:
	return db.query(Articles).filter(Articles.articles_cate_id == cate_id).all()
