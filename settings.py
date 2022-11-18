from pydantic import BaseSettings


class Settings(BaseSettings):
	TELEGRAM_TOKEN: str = os.environ('TELEGRAM_TOKEN')
	SQLALCHEMY_DATABASE_URL: str = os.environ('SQLALCHEMY_DATABASE_URL')
	REDIS_DSN: str = 'redis://localhost'
	IMG_PATH: str = 'static/img/'
	VIDEO_PATH: str = 'static/videos/'
	CHANNEL_ID: int = -1001506101372#1001599348187


settings = Settings()
