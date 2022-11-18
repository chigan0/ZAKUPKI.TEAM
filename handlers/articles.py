from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from utils.minor_func import articles
from utils.keyboards import inline_keyboard
from database import get_db
from .state import Articles
from models.articles import get_article


router = Router()


@router.callback_query(StateFilter(Articles.cate_selection))
async def cate_selection(callback: CallbackQuery, state: FSMContext):
	state_data = await state.get_data()
	menu_button = {'< Админ панель': 'admin_panel'}
	buttons = {}
	text, buttons, menu_button = await articles(int(callback.data), state)

	
	keyboard = inline_keyboard(buttons, menu_button=menu_button, row=2)
	await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(StateFilter(Articles.article_selection))
async def article_selection(callback: CallbackQuery, state: FSMContext):
	buttons = {}
	state_data = await state.get_data()
	menu_button = {'< Статьи': 'articles'}
	
	with get_db() as session:
		article_data = await get_article(session, int(callback.data))

	text = f"Названия: {article_data.articles_name} \n{article_data.articles_url}"

	keyboard = inline_keyboard(buttons, menu_button=menu_button, row=2)
	await callback.message.edit_text(text, reply_markup=keyboard)
