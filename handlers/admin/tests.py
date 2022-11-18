from typing import Any
from asyncio import create_task

from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, FSInputFile, ContentType as CT
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from utils.util import save_img
from utils.keyboards import inline_keyboard 
from redis import RedisCache
from database import get_db
from settings import settings
from models.users import add_admin_list
from ..state import AdminPanel, TestPanel
from utils.minor_func import (
	admin_panel, 
	test_difficulty_level, 
	test_category, 
	test_under_topic,
	footage_categorys,
	articles_categorys
)
from models.tests import (
	test_under_topic_add, 
	new_test_add, 
	test_answer_count,
	under_category_del,
	new_test_answer_add,
	test_del
)

router = Router()


def cehck_int(message) -> bool:
	try: 
		value = int(message.text)
		return True

	except:
		return False


@router.callback_query(StateFilter(AdminPanel.menu))
async def admin_panel_selection(callback: CallbackQuery, bot: Bot, state: FSMContext):
	if callback.data == 'add_test':
		await test_difficulty_level(callback.message, bot, state, True)

	elif callback.data == 'add_video':
		await footage_categorys(callback.message, bot, state, True)

	elif callback.data == 'add_article':
		await articles_categorys(callback.message, bot, state, True)

	elif callback.data == 'add_admin':
		keyboard = inline_keyboard({'< Админ панель': 'admin_panel'})
		await state.set_state(AdminPanel.add_new_user)
		await callback.message.edit_text('Пришлите мне telegram id пользователя', reply_markup=keyboard)


@router.message(StateFilter(AdminPanel.add_new_user), cehck_int)
async def new_admin(message: Message):
	with get_db(True) as session:
		await add_admin_list(session, message.text)

	await message.answer('Ползователь был добавлен', reply_markup=inline_keyboard({'< Админ панель': 'admin_panel'}))


@router.callback_query(StateFilter(AdminPanel.category_selection))
async def category_selection(callback: CallbackQuery, state: FSMContext):
	text, under_topics, keyboard = await test_category(int(callback.data), state, True)

	await state.set_state(AdminPanel.under_topic_selection)
	await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(StateFilter(AdminPanel.under_topic_selection))
async def under_topic_selection(callback: CallbackQuery, state: FSMContext):
	text = ''
	buttons = {}
	menu_button = {}

	if callback.data == 'add_under_category':
		await state.set_state(AdminPanel.save_under_topic)
		text = 'Отправьте мне названия новой подкатегории (минимальная длина 3 символа)'

	else:
		await state.set_state(AdminPanel.choice_of_test)
		text, buttons =  await test_under_topic(int(callback.data), state)

		menu_button['❌ Удалить'] = 'del_under_category' 
		menu_button['➕ Добавить тест'] = 'add_test'

	menu_button['< Админ панель'] = 'admin_panel'
	keyboard = inline_keyboard(buttons, menu_button=menu_button, row=3)
	await callback.message.edit_text(text, parse_mode='html', reply_markup=keyboard)


@router.message(
		StateFilter(AdminPanel.save_under_topic),
		lambda message: len(message.text) >= 3, 
	)
async def save_under_topic(message: Message, bot: Bot, state: FSMContext):
	state_data = await state.get_data()
	test_category = int(state_data['test_category'])

	with get_db(True) as session:
		await test_under_topic_add(session, message.text, test_category)

	create_task(RedisCache.cachin_update('test_under_topics'))

	keyboard = inline_keyboard({'< Админ панель': 'admin_panel'}, row=2)
	await message.answer(f"Новая подкатегория <b>{message.text}</b> была добавлена", 
		parse_mode='html', 
		reply_markup=keyboard
	)


@router.callback_query(StateFilter(AdminPanel.choice_of_test))
async def choice_test(callback: CallbackQuery, state: FSMContext):
	text = ''
	buttons = {}

	if callback.data == 'del_under_category':
		state_data = await state.get_data()

		with get_db(True) as session:
			category_name = await under_category_del(session, state_data['under_topic_id'])
		
		text = f"подкатегория <b>{category_name}</b> со всеми тестами была удалена"
		create_task(RedisCache.cachin_update('test_under_topics'))

	elif callback.data == 'add_test':
		await state.set_state(TestPanel.new_test)
		text = 'Придумайте названия теста'

	else:
		test_id = int(callback.data)
		await state.set_state(TestPanel.test)
		await state.update_data(test_id=test_id)

		with get_db() as session:
			test_question = await test_answer_count(session, test_id)

		text = f"В данном тесте вопросов: {len(test_question)}"
		buttons['❌ Удалить'] = 'del_test'
		buttons['📝 Добавить вопрос'] = 'add_question'

	buttons['< Админ панель'] = 'admin_panel'
	keyboard = inline_keyboard(buttons, row=3)
	await callback.message.edit_text(text, parse_mode='html', reply_markup=keyboard)


@router.message(
		StateFilter(TestPanel.new_test),
		lambda message: len(message.text) >= 3, 
	)
async def new_test(message: Message, state: FSMContext):
	state_data = await state.get_data()
	under_topic_id = int(state_data['under_topic_id'])

	with get_db(True) as session:
		await new_test_add(session, message.text, under_topic_id)
	
	create_task(RedisCache.cachin_update('tests'))
	keyboard = inline_keyboard({'< Админ панель': 'admin_panel'}, row=2)
	
	await message.answer(f"Новы тест <b>{message.text}</b> был добавлен", 
		parse_mode='html', 
		reply_markup=keyboard
	)


@router.callback_query(StateFilter(TestPanel.test))
async def test_menu(callback: CallbackQuery, state: FSMContext):
	text: str = ''
	buttons: dict = {}
	state_data: dict = await state.get_data()

	if callback.data == 'del_test':
		text = 'Данный тест был удален'
		with get_db(True) as session:
			await test_del(session, state_data['test_id'])

		create_task(RedisCache.cachin_update('tests'))

	elif callback.data == 'add_question':
		await state.set_state(TestPanel.new_question)
		
		text = 'Пришлите мне вопрос (не менее 3 символов и не более 200 символов)'		

	buttons['< Админ панель'] = 'admin_panel'
	keyboard = inline_keyboard(buttons, row=2)
	await callback.message.edit_text(text, parse_mode='html', reply_markup=keyboard)


@router.message(
		StateFilter(TestPanel.new_question),
		lambda message: len(message.text) >= 3 and len(message.text) <= 500,
	)
async def test_question(message: Message, state: FSMContext):
	await state.update_data(question=message.text)
	keyboard = inline_keyboard({'Да': 'add_img', 'Нет': 'not_img'}, row=2)

	await state.set_state(TestPanel.question_img)
	await message.answer('Добавить картинку к вопросу ?', reply_markup=keyboard)


@router.callback_query(StateFilter(TestPanel.question_img))
async def question_img(callback: CallbackQuery, state: FSMContext):
	if callback.data == 'add_img':
		await state.set_state(TestPanel.add_img)
		text = 'Отправьте мне изоброжения (не более одной картинке)'

		await callback.message.edit_text(text)

	else:
		await answer_type(callback.message, state)


@router.message(F.content_type.in_([CT.PHOTO, CT.DOCUMENT]), StateFilter(TestPanel.add_img))
async def add_img(message: Message, bot: Bot, state: FSMContext):
	filename, status = await save_img(message, bot)

	if status is False:
		keyboard = inline_keyboard({'Админ панель': 'admin_panel'}, row=1)
		text = 'Не удалось сохранить изображение,\
		отправьте изображения повторно или пришлите новое'

		return await message.answer(text, reply_markup=keyboard)

	await state.update_data(filename=filename)
	await answer_type(message, state, False)


@router.callback_query(StateFilter(TestPanel.answer_type))
async def response_type_selected(callback: CallbackQuery, bot: Bot, state: FSMContext):
	state_data = await state.get_data()
	udpate = False
	answer_type = ('one_answer', 'couple_answer', 'mine_answer')
	keyboard = inline_keyboard({'Готово': 'ready'}, row=1)

	if callback.data in answer_type:
		await state.update_data(correct_answers=[], answer_type=callback.data)
		update = True

		text = 'Пришлите мне необходимое количество <b>верных</b> ответов после нажмите\
		на кнопку <b>Готово</b>'

		await callback.message.edit_text(text, parse_mode='html', reply_markup=keyboard)

	elif callback.data == 'ready' and len(state_data['correct_answers']) >= 1:
		if state_data['answer_type'] == 'mine_answer':
			return await add_test(callback, bot, state)

		else:
			await state.update_data(answer_options=[])

			text = 'Пришлите мне варианты <b>не правельных</b> ответо и после нажмите\
			на кнопку <b>Готово</b>'

			await state.set_state(TestPanel.answer_options)
			await callback.message.answer(text, parse_mode='html', reply_markup=keyboard)

	else:
		text = 'Вы не добавили ни одного верного ответа'
		await callback.message.answer(text)


@router.message(StateFilter(TestPanel.answer_type, TestPanel.answer_options))
async def correct_answers(message: Message, state: FSMContext):
	state_data = await state.get_data()
	state_name = await state.get_state()

	if state_name == TestPanel.answer_type:
		state_data['correct_answers'].append(message.text)
		await state.update_data(correct_answers=state_data['correct_answers'])

	elif state_name == TestPanel.answer_options:
		state_data['answer_options'].append(message.text)
		await state.update_data(answer_options=state_data['answer_options'])


@router.callback_query(StateFilter(TestPanel.answer_options))
async def add_test(callback: CallbackQuery, bot: Bot, state: FSMContext):
	state_data = await state.get_data()
	menu_button = {}

	if callback.data == 'ready':
		buttons = {}
		text = state_data['question']
		correct_answers = state_data['correct_answers']
		answer_options = [] if state_data['answer_type'] == 'mine_answer' else state_data['answer_options']

		for i in correct_answers + answer_options:
			buttons[i] = i[:5]

		menu_button['❌ Заполнить заново'] = 'del_test'
		menu_button['✅ Сохранить'] = 'test_save'
		keyboard = inline_keyboard(buttons, menu_button=menu_button, row=1)
		await state.set_state(TestPanel.test_result)

		if state_data.get('filename') is not None:
			photo = FSInputFile(f"{settings.IMG_PATH}{state_data['filename']}")

			await bot.send_photo(chat_id=callback.message.chat.id, 
				photo=photo, 
				caption=text,
				reply_markup=keyboard
			)

		else:
			await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(StateFilter(TestPanel.test_result))
async def test_result(callback: CallbackQuery, state: FSMContext):
	state_data = await state.get_data()
	keyboard = inline_keyboard({'< Админ панель': 'admin_panel'}, row=1)
	await state.update_data(filename=None)

	if callback.data == 'del_test':
		await state.set_state(TestPanel.new_question)
		text = 'Пришлите мне вопрос (не менее 3 символов и не более 200 символов)'
	
	elif callback.data == 'test_save':
		text = 'Тест сохранён'
		with get_db(True) as session:
			await new_test_answer_add(session, state_data)

	if state_data.get('filename') is not None:
		await callback.message.delete()
		return await callback.message.answer(text, reply_markup=keyboard)
	
	await callback.message.edit_text(text, reply_markup=keyboard)


async def answer_type(message: Message, state: FSMContext, update: bool = True):
	text = 'Тип ответа'
	await state.set_state(TestPanel.answer_type)
		
	buttons = {'Один верны ответ': 'one_answer', 
		'Несколько верных ответов': 'couple_answer',
		'Свой ответ': 'mine_answer'
	}
	keyboard = inline_keyboard(buttons, row=3)

	if update:
		await message.edit_text(text, reply_markup=keyboard)

	else:
		await message.answer(text, reply_markup=keyboard)

