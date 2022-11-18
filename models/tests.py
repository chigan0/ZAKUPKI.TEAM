from typing import Union

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship, Session

from database import Base, get_connect


class TestCategory(Base):
	__tablename__ = 'test_category'

	id = Column(Integer, primary_key=True)
	cate_name = Column(String(60), unique=True, nullable=False)
	under_category = relationship('TestUnderCategory', cascade="all, delete")

	def __repr__(self,):
		return self.cate_name


class TestUnderCategory(Base):
	__tablename__ = 'test_under_category'

	id = Column(Integer, primary_key=True)
	cate_name = Column(String(80), unique=True, nullable=False)
	category_id = Column(Integer, ForeignKey('test_category.id'))
	tests = relationship('Tests', cascade="all, delete")

	def __repr__(self,):
		return self.cate_name


class Tests(Base):
	__tablename__ = 'tests'

	id = Column(Integer, primary_key=True)
	test_name = Column(String(80), unique=True, nullable=False)
	under_topic_id = Column(Integer, ForeignKey('test_under_category.id'))
	test_answer = relationship('TestAnswer', cascade='all, delete')

	def __repr__(self,):
		return self.test_name


class TestAnswer(Base):
	__tablename__ = 'test_answer'

	id = Column(Integer, primary_key=True)
	question = Column(String(500), nullable=False)
	question_img = Column(String(50), nullable=True, unique=True, default=None)
	not_answer = Column(Boolean, default=False)
	tests_id = Column(Integer, ForeignKey('tests.id'))
	correct_answer = relationship('CorrectAnswers', cascade="all, delete")
	answer_options = relationship('AnswerOptions', cascade="all, delete")

	def __repr__(self,):
		return self.question


class CorrectAnswers(Base):
	__tablename__ = 'correct_answers'

	id = Column(Integer, primary_key=True)
	test_id = Column(Integer, ForeignKey('test_answer.id'))
	answer = Column(String(650), nullable=False)

	def __repr__(self):
		return self.answer


class AnswerOptions(Base):
	__tablename__ = 'answer_options'

	id = Column(Integer, primary_key=True)
	test_id = Column(Integer, ForeignKey('test_answer.id'))
	answer = Column(String(650), nullable=False)

	def __repr__(self,):
		return self.answer


async def test_under_topic_add(db: Session, name: str, category_id: int) -> None:
	under_topic = TestUnderCategory(cate_name=name, category_id=category_id)
	db.add(under_topic)


async def new_test_add(db: Session, test_name: str, under_topic_id: int) -> None:
	tests = Tests(test_name=test_name, under_topic_id=under_topic_id)
	db.add(tests)


async def under_category_del(db: Session, under_category_id: int) -> str:
	under_category = db.query(TestUnderCategory).get(under_category_id)
	category_name = under_category.cate_name
	db.delete(under_category)

	return category_name


async def test_del(db: Session, test_id: int) -> None:
	test = db.query(Tests).get(test_id)
	db.delete(test)


async def new_test_answer_add(db: Session, test_data: dict) -> None:
	test = TestAnswer(
		question=test_data['question'],
		question_img=test_data.get('filename'),
		not_answer=True if test_data['answer_type'] == 'mine_answer' else False,
		tests_id=test_data['test_id']
	)

	db.add(test)
	db.commit()

	for correct in test_data['correct_answers']:
		db.add(CorrectAnswers(test_id=test.id, answer=correct))

	if not test.not_answer:
		for options in test_data['answer_options']:
			db.add(AnswerOptions(test_id=test.id, answer=options))


async def all_test_category(db: Session) -> list:
	return db.query(TestCategory).all()


async def all_under_topics(db: Session) -> list:
	return db.query(TestUnderCategory).all()


async def all_tests(db: Session) -> list:
	return db.query(Tests).all()


async def get_under_topic(db: Session, test_category_id: int) -> Union[TestUnderCategory, None]:
	return db.query(TestUnderCategory
		).filter(TestUnderCategory.category_id == test_category_id
	).one_or_none()


async def test_answer_count(db: Session, test_id: int) -> list:
	return db.query(TestAnswer).filter(TestAnswer.tests_id == test_id).all()


async def test_answers(db: Session, test_id: int) -> list:

	return db.query(TestAnswer, CorrectAnswers
		).join(
			CorrectAnswers, TestAnswer.id == CorrectAnswers.test_id
		).filter(
			TestAnswer.tests_id == test_id
		).all()


async def test_answer_options(db: Session, test_answer_id: int) -> list:
	return db.query(AnswerOptions).filter(AnswerOptions.test_id==test_answer_id).all()


async def check_default_caategory() -> None:
	db = get_connect()

	for cate in ('Новичок', 'Продвинуты', 'Эксперт'):
		category = db.query(TestCategory).filter(TestCategory.cate_name == cate).one_or_none()
		if category is None:
			category = TestCategory(cate_name=cate)
			db.add(category)

	db.commit()
	db.close()
