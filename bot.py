from asyncio import run

from aiogram import Bot, Dispatcher

from models import *
from database import engine
from settings import settings
from handlers import main_handler, test_handler, videos, articles
from handlers.admin import tests, footage, article
from middleware import BaseMenuMiddleware
from redis import RedisCache

async def main():
	bot = Bot(settings.TELEGRAM_TOKEN, parse_mode='html')
	dp = Dispatcher()
	rc = RedisCache()

	Base.metadata.create_all(bind=engine)

	dp.include_router(main_handler.router)
	dp.include_router(tests.router)
	dp.include_router(test_handler.router)
	dp.include_router(footage.router)
	dp.include_router(videos.router)
	dp.include_router(article.router)
	dp.include_router(articles.router)

	dp.callback_query.outer_middleware(BaseMenuMiddleware())
	await check_default_caategory()
	await rc.full_caching()
	
	print("BOT WORKS")
	await bot.delete_webhook(drop_pending_updates=True)
	await dp.start_polling(bot)


if __name__ == '__main__':
	try:
		run(main())

	except KeyboardInterrupt:
		print("\n@GoodBye :)")