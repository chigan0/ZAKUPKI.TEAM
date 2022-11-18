from typing import Any, Dict, List

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup

from .keyboards import inline_keyboard
from database import get_db
from handlers.state import SubChannel, AdminPanel, UserTest, Videos, VideosAdm, ArticlesAdm, Articles
from models.articles import all_articles_category, all_articles, article_in_cate
from models.users import get_admin
from settings import settings
from redis import redis_sets, get_redis_data


async def check_sub_channels(bot: Bot, user_id: int) -> bool:
	status: bool = True
	try:
		chat_members = await bot.get_chat_member(chat_id=settings.CHANNEL_ID, user_id=user_id)
		if chat_members.status == 'left':
			status = False

	except TelegramBadRequest:
		status = False

	finally:
		return status


async def main_menu(message: Message, bot: Bot, state: FSMContext, update: bool = True) -> Any:
	buttons: dict
	if not update: await message.delete()
	if await state.get_state() is not None:
		await state.clear()
	
	sub_state = await check_sub_channels(bot, message.from_user.id)
	if not sub_state:
		text = 'Для использования данного бота вам необходимо быть подписанным на нашу группу\n\
		\nhttps://t.me/zakupki_team_chat'

		buttons = {'✅ Я подписался': 'sub'}
		return await warning_message(message, text, buttons, False, state, SubChannel.sub)

	text = "Выберите интересующий вас раздел"
	buttons = {'📋 Пройти тест': 'difficulty_level', '📰 Наши статьи': 'articles', '🎥 Наши видео': 'vidios'}

	with get_db() as session:
		admin_state = await get_admin(session, str(message.chat.id))
	
	if admin_state is not None: buttons['🤦‍♂️ Админ панель'] = 'admin_panel'
	
	keyboard = inline_keyboard(buttons, row=2)	

	if update: await message.edit_text(text, reply_markup=keyboard)
	else: await message.answer(text, reply_markup=keyboard)


async def admin_panel(message: Message, bot: Bot, state: FSMContext, update: bool = True) -> Any:
	text = 'Добро пожаловать в админ панель ZAKUPKI.TEAM \nВ данном разделе вы можете\n\
	\nДобавить новые тесты \nДобавить статьи \nДобавить новые видео материалы'
	
	keyboard = inline_keyboard({
		'📋 Добавить тест': 'add_test',
		'📰 Добавить статью':'add_article',
		'🎥 Добавить видео': 'add_video',
		'📝 Добавить пользователя': 'add_admin'
	}, menu_button={'< Главное меню': 'base_menu'}, row=2)

	await state.set_state(AdminPanel.menu)

	if update: await message.edit_text(text, reply_markup=keyboard)
	else:
		await message.delete()
		await message.answer(text, reply_markup=keyboard)


async def warning_message(message: Message, 
		text: str, 
		buttons: dict, 
		update: bool = True,
		state: FSMContext = None,
		state_name: StatesGroup = None
	) -> None:
	keyboard = inline_keyboard(buttons)

	if state is not None:
		await state.set_state(state_name)

	if update:
		await message.edit_text(text, reply_markup=keyboard)

	else:
		await message.answer(text, reply_markup=keyboard)


async def test_difficulty_level(message: Message, bot: Bot, state: FSMContext, admin_state: bool = False):
	text = 'Выберите уровень сложности'
	test_categorys = await redis_sets('test_category', data_set=False)
	menu_button = {}
	buttons = {}
	
	for i in test_categorys:
		buttons[test_categorys[i]] = i

	if admin_state:
		await state.set_state(AdminPanel.category_selection)
		menu_button['< Админ панель'] = 'admin_panel'
	
	else:
		await state.set_state(UserTest.difficulty_selection)
		menu_button['< Главное меню'] = 'base_menu'

	keyboard = inline_keyboard(buttons, menu_button=menu_button, row=3)
	await message.edit_text(text, reply_markup=keyboard)


async def test_category(test_id: int, state: FSMContext, admin_state: bool = False):
	buttons = {}
	text = 'В данной категории отсутствуют подкатегории'
	under_topics = await get_redis_data('test_under_topics', pickle_dumps=True)
	under_topics = under_topics.get(test_id)

	if under_topics is not None:
		text = 'Выберите интересующий вас подкатегорию'
		for cate in under_topics:
			buttons[under_topics[cate].title()] = cate
	
	if admin_state:
		menu_button = {'➕ Добавить категорию': 'add_under_category', '< Админ панель': 'admin_panel'}

	else:
		menu_button = {'< Главное меню': 'base_menu'}

	await state.update_data(under_topics=under_topics, test_category=test_id)
	keyboard = inline_keyboard(buttons, menu_button=menu_button, row=2)
	return text, under_topics, keyboard


async def test_under_topic(under_topic_id: int, state: FSMContext):
	buttons = {}
	state_data: dict = await state.get_data()
	await state.update_data(under_topic_id=under_topic_id)

	tests = await get_redis_data('tests', pickle_dumps=True)
	tests = tests.get(under_topic_id)
		
	if tests is not None:
		for test in tests:
			buttons[tests[test].title()] = test

	text = f"Список тестов подкатегории\
	<b>{state_data['under_topics'][under_topic_id].title()}</b>"


	return text, buttons


async def footage_categorys(message: Message, bot: Bot, state: FSMContext, admin_state: bool = False, update = True):
	menu_button = {'< Главное меню': 'base_menu'}
	categorys = await redis_sets('footage_cate', data_set=False)
	text = 'Выберите интересующую вас категорию'
	buttons = {}

	if admin_state:
		await state.set_state(VideosAdm.cate_selection)
		menu_button = {'➕ Добавить категорию': 'add_footage_cate', '< Админ панель': 'admin_panel'}

	else: await state.set_state(Videos.cate_selection)
	for cate in categorys:
		buttons[categorys[cate]] = cate

	keyboard = inline_keyboard(buttons, menu_button=menu_button, row=2) 

	if update:
		await message.edit_text(text, reply_markup=keyboard)

	else:
		await message.delete()
		await message.answer(text, reply_markup=keyboard)


async def videos_list(footage_cate_id: int, state: FSMContext, admin_state: bool = False):
	buttons = {}
	menu_button = {'< Главное меню': 'base_menu'}
	videos: Dict[int, str] = await get_redis_data('videos', pickle_dumps=True)
	videos = videos.get(footage_cate_id) if videos is not None else None

	await state.update_data(footage_cate_id=footage_cate_id, videos=videos)
	await state.set_state(Videos.video_selection)

	if admin_state:
		await state.set_state(VideosAdm.video_selection)
		menu_button = {'❌ Удалить категорию':'del_cate', 
			'➕ Добавить видео': 'add_video', 
			'< Админ панель': 'admin_panel'
		}
	
	if videos is not None:
		for i in videos:
			buttons[videos[i]['name']] = i

	text = f'В данной категории {len(videos) if videos is not None else 0} видео' 
	keyboard = inline_keyboard(buttons, menu_button=menu_button, row=2)

	return text, buttons, menu_button


async def articles_categorys(message: Message, bot: Bot, state: FSMContext, admin_state: bool = False, update = True):
	buttons = {}
	menu_button = {'< Главное меню': 'base_menu'}
	text = 'Выберите интересующую вас категорию'
	with get_db() as session:
		articles_cate = await all_articles_category(session)
		articles = await all_articles(session)

	await state.update_data(articles_cate=articles_cate)

	if admin_state:
		await state.set_state(ArticlesAdm.cate_selection)
		menu_button = {'➕ Добавить категорию': 'add_article_cate', '< Админ панель': 'admin_panel'}

	else: await state.set_state(Articles.cate_selection)
	for cate in articles_cate:
		buttons[cate.cate_name] = cate.id

	
	keyboard = inline_keyboard(buttons, menu_button=menu_button, row=2)

	if update:await message.edit_text(text, reply_markup=keyboard)
	else:
		await message.delete()
		await message.answer(text, reply_markup=keyboard)	



async def articles(cate_id: int, state: FSMContext, admin_state: bool = False):
	buttons = {}
	text = 'Выберите интересующую вас статью'
	menu_button = {'< Главное меню': 'base_menu'}
	await state.update_data(cate_id=cate_id)

	with get_db() as session:
		articles = await article_in_cate(session, cate_id)

	for article in articles:
		buttons[article.articles_name] = article.id

	await state.set_state(Articles.article_selection)
	if admin_state:
		await state.set_state(ArticlesAdm.article_selection)
		menu_button = {'❌ Удалить категорию':'del_cate', 
			'➕ Добавить статью': 'add_article', 
			'< Админ панель': 'admin_panel'
		}


	return text, buttons, menu_button
