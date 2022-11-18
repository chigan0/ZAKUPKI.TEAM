from asyncio import create_task

from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, FSInputFile, ContentType as CT
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from utils.util import save_video
from utils.minor_func import main_menu, check_sub_channels, videos_list
from utils.keyboards import inline_keyboard
from models.videos import new_footage_cate, get_videos, new_video, delete_video, delete_footage_cate
from database import get_db
from redis import RedisCache
from settings import settings
from ..state import AdminPanel, TestPanel, VideosAdm


router = Router()


@router.callback_query(StateFilter(VideosAdm.cate_selection))
async def cate_selection(callback: CallbackQuery, state: FSMContext):
	menu_button = {'< Админ панель': 'admin_panel'}
	buttons = {}

	if callback.data == 'add_footage_cate':
		await state.set_state(VideosAdm.new_cate)
		text = 'Пришлите мне названия новой категории (Не менее 2 символов)'

	else:
		text, buttons, menu_button = await videos_list(int(callback.data), state, True)
	
	keyboard = inline_keyboard(buttons, menu_button=menu_button, row=2)
	await callback.message.edit_text(text, reply_markup=keyboard)


@router.message(StateFilter(VideosAdm.new_cate), lambda message: len(message.text) >= 2)
async def footage_new_cate(message: Message, state: FSMContext):
	with get_db(True) as session:
		await new_footage_cate(session, message.text)

	text = f'Новая категория <b>{message.text}</b> была добавлена'
	keyboard = inline_keyboard({}, menu_button={'< Админ панель': 'admin_panel'})

	await message.answer(text, reply_markup=keyboard)
	create_task(RedisCache.cachin_update('footage_cate'))


@router.callback_query(StateFilter(VideosAdm.video_selection))
async def video_selection(callback: CallbackQuery, bot: Bot, state: FSMContext):
	buttons = {}
	state_data = await state.get_data()
	video_data = state_data.get('videos')
	menu_button = {'< Админ панель': 'admin_panel'}

	if callback.data == 'add_video':
		await state.set_state(VideosAdm.new_video)
		text = 'Пришлите мне названия видео материала (Не менее 2 символов)'

	elif callback.data == 'del_cate':
		text = 'Данная категория со всеми видео была удалена'
		with get_db(True) as session:
			await delete_footage_cate(session, state_data['footage_cate_id'])

		create_task(RedisCache.cachin_update('footage_cate'))
		create_task(RedisCache.cachin_update('videos'))

	else:
		text = 'Данное видео материал не найден'
		video_data = video_data.get(int(callback.data))
		if video_data is not None:
			message = await callback.message.answer('Загрузка видео ...')
			video = FSInputFile(f"{settings.VIDEO_PATH}{video_data['videos_name']}")
			menu_button['❌ Удалить видео'] = callback.data
			keyboard = inline_keyboard({}, menu_button=menu_button)
			
			await state.set_state(VideosAdm.delete_vidio)
			await callback.message.delete()
			await bot.send_video(chat_id=callback.message.chat.id, 
				video=video, 
				reply_markup=keyboard, 
				caption=video_data['name']
			)
			return await message.delete()


	keyboard = inline_keyboard(buttons, menu_button=menu_button, row=2)
	await callback.message.edit_text(text, reply_markup=keyboard)


@router.message(StateFilter(VideosAdm.new_video), lambda message: len(message.text) >= 2)
async def video_name(message: Message, state: FSMContext):
	await state.update_data(video_name=message.text)
	await state.set_state(VideosAdm.video)

	await message.answer('Пришлите мне видео материал')


@router.message(F.content_type.in_([CT.VIDEO]), StateFilter(VideosAdm.video))
async def create_video(message: Message, bot: Bot, state: FSMContext):
	state_data = await state.get_data()
	filename = await save_video(message, bot)
	menu_button = {'< Админ панель': 'admin_panel'}

	with get_db(True) as session:
		await new_video(
			session, 
			state_data['footage_cate_id'],
			filename,
			state_data['video_name'],
		)

	keyboard = inline_keyboard({}, menu_button=menu_button)
	await message.answer('Видео было добавлено', reply_markup=keyboard)
	create_task(RedisCache.cachin_update('videos'))


@router.callback_query(StateFilter(VideosAdm.delete_vidio))
async def delete_vidio(callback: CallbackQuery, state: FSMContext):
	await callback.message.delete()

	vidio_id = int(callback.data)
	menu_button = {'< Админ панель': 'admin_panel'}

	with get_db(True) as session:
		await delete_video(session, vidio_id)

	keyboard = inline_keyboard({}, menu_button=menu_button)
	await callback.message.answer(text='Видео было удалено', reply_markup=keyboard)
	create_task(RedisCache.cachin_update('videos'))
