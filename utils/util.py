from typing import Union
from pickle import dumps, loads
from random import choice

from aiogram import types, Bot
from PIL import Image

from settings import settings


async def save_video(message: types.Message, bot: Bot):
	file = await bot.get_file(message.video.file_id)
	result = await bot.download_file(file.file_path)
	filename: str = f"{random_str(7)}.mp4"

	with open(f'static/videos/{filename}', 'wb') as bfile:
		bfile.write(result.getvalue())

	return filename


async def save_img(message: types.Message, bot: Bot) -> None:
	file_id: str = None
	status: bool = False
	filename: str = ''

	if message.document is not None:
		file = message.document
		if file.mime_type.split('/')[0] == 'image':
			file_id = file.file_id

	else: file_id = message.photo[-1].file_id

	if file_id is not None:
		file = await bot.get_file(file_id)
		result = await bot.download_file(file.file_path)

		img = Image.open(result)
		filename = f"{random_str(7)}.jpg"
		print(f"ADD NEW IMG --- {filename} ---")

		img.save(f"{settings.IMG_PATH}{filename}")
		status = True

	return filename, status


def random_str(length: int = 4):
	symb = 'abcdefghijklmnopqrstuvwxyz1234567890'
	string = [choice(symb) for i in range(length)]

	return ''.join(string)


async def pickle_data_dumps(data: Union[dict, object], status: bool = False) -> Union[bytes, dict, None]:
	if data is None:
		return None

	if status:
		return loads(data)

	else:
		if type(data) == dict:
			picke_dumps = {}
			for i in data:
				picke_dumps[i] = data[i]
		else:
			picke_dumps = data

		return dumps(picke_dumps)