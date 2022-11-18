from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from settings import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_connect():
	db = SessionLocal()
	return db


@contextmanager
def get_db(autocommit: bool = False):
	db = get_connect()
	try:
		yield db
		if autocommit:
			db.commit()
	except Exception as e:
		db.rollback()
		raise e

	finally:
		db.close()

