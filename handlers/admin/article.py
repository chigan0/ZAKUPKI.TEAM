from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from utils.minor_func import main_menu, check_sub_channels, videos_list, articles
from utils.keyboards import inline_keyboard
from models.articles import new_article_cate, article_in_cate, delete_article_cate, add_new_article, get_article, delete_article_id
from database import get_db
from redis import RedisCache
from settings import settings
from ..state import ArticlesAdm


router = Router()


@router.callback_query(StateFilter(ArticlesAdm.cate_selection))
async def cate_selection(callback: CallbackQuery, state: FSMContext):
	state_data = await state.get_data()
	menu_button = {'< Админ панель': 'admin_panel'}
	buttons = {}

	if callback.data == 'add_article_cate':
		await state.set_state(ArticlesAdm.new_cate)
		text = 'Пришлите мне названия новой категории (Не менее 2 символов)'

	else:
		text, buttons, menu_button = await articles(int(callback.data), state, True)

	
	keyboard = inline_keyboard(buttons, menu_button=menu_button, row=2)
	await callback.message.edit_text(text, reply_markup=keyboard)


@router.message(StateFilter(ArticlesAdm.new_cate), lambda message: len(message.text) >= 2)
async def footage_new_cate(message: Message, state: FSMContext):
	with get_db(True) as session:
		await new_article_cate(session, message.text)

	text = f'Новая категория <b>{message.text}</b> была добавлена'
	keyboard = inline_keyboard({}, menu_button={'< Админ панель': 'admin_panel'})
	await message.answer(text, reply_markup=keyboard)


@router.callback_query(StateFilter(ArticlesAdm.article_selection))
async def article_selection(callback: CallbackQuery, state: FSMContext):
	buttons = {}
	state_data = await state.get_data()
	menu_button = {'< Админ панель': 'admin_panel'}

	if callback.data == 'del_cate':
		text = 'Категория была удалена'
		with get_db(True) as session:
			await delete_article_cate(session, state_data['cate_id'])

	elif callback.data == 'add_article':
		text = 'Пришлите заголовок статьи'
		await state.set_state(ArticlesAdm.new_article)

	else:
		with get_db() as session:
			article_data = await get_article(session, int(callback.data))

		text = f"Названия: {article_data.articles_name} \n{article_data.articles_url}"
		menu_button = {'❌ Удалить': article_data.id, '< Админ панель': 'admin_panel'}
		await state.set_state(ArticlesAdm.delete_article)

	keyboard = inline_keyboard(buttons, menu_button=menu_button, row=2)
	await callback.message.edit_text(text, reply_markup=keyboard)


@router.message(StateFilter(ArticlesAdm.new_article), lambda message: len(message.text) >= 2)
async def new_article(message: Message, state: FSMContext):
	await state.update_data(article_tile=message.text)
	await state.set_state(ArticlesAdm.article_link)

	await message.answer('Пришлите ссылку на статью')


@router.message(StateFilter(ArticlesAdm.article_link), lambda message: len(message.text) >= 2)
async def article_link(message: Message, state: FSMContext):
	state_data = await state.get_data()

	with get_db(True) as session:
		await add_new_article(session, state_data['cate_id'], state_data['article_tile'], message.text)

	keyboard = inline_keyboard({}, menu_button={'< Админ панель': 'admin_panel'})
	await message.answer(f"Новая статья <b>{state_data['article_tile']}</b> была добавлена", reply_markup=keyboard)


@router.callback_query(StateFilter(ArticlesAdm.delete_article))
async def delete_article(callback: CallbackQuery, state: FSMContext):
	menu_button = {'< Админ панель': 'admin_panel'}
	with get_db(True) as session:
		await delete_article_id(session, int(callback.data))

	keyboard = inline_keyboard({}, menu_button=menu_button)
	await callback.message.edit_text('Статья была удалена', reply_markup=keyboard)
