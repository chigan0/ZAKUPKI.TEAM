from contextlib import contextmanager
from typing import Union, Any, Dict
from asyncio import sleep, run

import aioredis

from settings import settings
from database import get_connect
from utils.util import pickle_data_dumps
from models.videos import all_footage_category, all_videos
from models.articles import all_articles_category, all_articles
from models.tests import (
	all_test_category, 
	all_under_topics,
	all_tests
)


async def redis_connect(encoding="utf-8", decode_responses: bool = True):
	redis = aioredis.from_url(
		settings.REDIS_DSN, encoding=encoding, decode_responses=decode_responses
	)

	return redis


async def add_redis_data(key:str, 
		value: Union[str, int, float, list, dict], 
		decode_responses: bool = False,
		expire=None, 
		pickle_dumps = True,
	) -> None:

	redis_conn = await redis_connect('unicode_escape' if pickle_dumps else 'utf-8', decode_responses)
	if pickle_dumps:
		value = await pickle_data_dumps(value)

	await redis_conn.set(key, value, expire)
	await redis_conn.close()


async def get_redis_data(key: Union[str, int],
		decode_responses: bool = False,
		pickle_dumps: bool = False,
		project_data: bool = True,
	):

	redis_conn = await redis_connect('unicode_escape' if pickle_dumps else 'utf-8', decode_responses)
	result = await redis_conn.get(key)

	if project_data and result is None:
		rc = RedisCache()
		await rc.cachin_update(key)
		result = await redis_conn.get(key)

	if pickle_dumps:
		result = await pickle_data_dumps(result, True)

	await redis_conn.close()
	return result


async def redis_sets(key: str, 
		value: dict = {}, 
		data_set=True, 
		update=False,
		redis_conn=None,
		auto_close: bool = False,
		project_data: bool = True
	) -> Union[None, dict]:
	
	result = None
	if redis_conn is None: redis_conn = await redis_connect()

	if data_set:
		await redis_conn.delete(key)
		if update:
			old_value: dict = await redis_conn.hgetall(key)
			value = {**old_value, **value} if old_value is not None else value

		await redis_conn.hset(key, mapping=value)

	else:
		result = await redis_conn.hgetall(key)
		if project_data and result == {}:
			rc = RedisCache()
			await rc.cachin_update(key)
			result = await redis_conn.hgetall(key)

	if auto_close: await redis_conn.close()
	return result


class RedisCache:
	db = get_connect()
	redis_conn = aioredis.from_url(
		settings.REDIS_DSN, 
		encoding="utf-8", 
		decode_responses=True
	)

	@classmethod
	async def caching_test_cate(cls):
		test_categorys: list = await all_test_category(cls.db)
		caching_data = {}
		for cate in test_categorys:
			caching_data[cate.id] = cate.cate_name

		if len(caching_data) > 0:
			await redis_sets('test_category', caching_data, True, redis_conn=cls.redis_conn)

	@classmethod
	async def caching_tests(cls):
		tests: list = await all_tests(cls.db)
		caching_data = {}
		for test in tests:
			if caching_data.get(test.under_topic_id) is None:
				caching_data[test.under_topic_id] = {}

			caching_data[test.under_topic_id][test.id] = test.test_name

		await add_redis_data('tests', caching_data)

	@classmethod
	async def caching_test_under_cate(cls):	
		under_categorys = await all_under_topics(cls.db)
		caching_data: dict = {}

		for cate in under_categorys:
			if caching_data.get(cate.category_id) is None:
				caching_data[cate.category_id] = {}

			caching_data[cate.category_id][cate.id] = cate.cate_name

		await add_redis_data('test_under_topics', caching_data)

	@classmethod
	async def caching_footage_cate(cls):
		footage_cate = await all_footage_category(cls.db)
		caching_data: Dict[str, str] = {}

		for cate in footage_cate:
			caching_data[cate.id] = cate.cate_name 

		if len(caching_data) > 0:
			await redis_sets('footage_cate', caching_data, True, redis_conn=cls.redis_conn)

	@classmethod
	async def caching_videos(cls):	
		videos = await all_videos(cls.db)
		caching_data: dict = {}

		for video in videos:
			if caching_data.get(video.footage_cate_id) is None:
				caching_data[video.footage_cate_id] = {}

			caching_data[video.footage_cate_id][video.id] = {
				'videos_name': video.videos_name,
				'name': video.name
			}

		await add_redis_data('videos', caching_data)

	@classmethod
	async def cachin_update(cls, func_name: str):
		print('cachin_update')
		func = {'test_category': cls.caching_test_cate, 
			'test_under_topics': cls.caching_test_under_cate,
			'tests': cls.caching_tests,
			'footage_cate': cls.caching_footage_cate,
			'videos': cls.caching_videos,
		}

		await func[func_name]()
		await cls.connect_close(cls)

	async def full_caching(self):
		await self.caching_test_cate()
		await self.caching_test_under_cate()
		await self.caching_tests()
		await self.caching_footage_cate()
		await self.caching_videos()
		await self.connect_close()

	async def connect_close(self,):
		await self.redis_conn.close()
		self.db.close()
