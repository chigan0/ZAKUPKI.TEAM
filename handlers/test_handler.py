from typing import Dict, List
from random import shuffle

from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, FSInputFile, ContentType as CT
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from utils.keyboards import inline_keyboard
from utils.util import random_str
from database import get_db
from .state import UserTest
from models.tests import test_answers, test_answer_options
from settings import settings
from utils.minor_func import (
	admin_panel, 
	test_difficulty_level, 
	test_category, 
	test_under_topic
)

router = Router()


@router.callback_query(StateFilter(UserTest.difficulty_selection))
async def difficulty_selection(callback: CallbackQuery, state: FSMContext):
	text, under_topics, keyboard = await test_category(int(callback.data), state)

	await state.set_state(UserTest.under_topic_selection)
	await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(StateFilter(UserTest.under_topic_selection))
async def under_topic_selection(callback: CallbackQuery, state: FSMContext):
	await state.set_state(UserTest.test_selection)
	text, buttons = await test_under_topic(int(callback.data), state)

	menu_button = {'< Главное меню': 'base_menu'}
	keyboard = inline_keyboard(buttons, menu_button=menu_button, row=3)
	await callback.message.edit_text(text, parse_mode='html', reply_markup=keyboard)


@router.callback_query(StateFilter(UserTest.test_selection))
async def test_selection(callback: CallbackQuery, state: FSMContext):
	await callback.message.edit_text('Ваш тест генерируется, пожалуйста подождите')

	state_data: dict = await state.get_data()
	test_id = int(callback.data)
	tests_id = []
	correct_answers_id = {}
	tests = {}
	correct_answers = {}
	answer_options = {}

	ram = []

	await state.update_data(test_id=test_id)

	with get_db() as session:
		test_answer = await test_answers(session, test_id)
		for i in test_answer:
			test = i[0]
			correct_answer = i[1]

			tests[test.id] = {
				'question': test.question, 
				'question_img': test.question_img,
				'not_answer': test.not_answer
			}

			if correct_answers.get(test.id) is None:
				correct_answers[test.id] = {}

			if correct_answer.id not in ram:
				correct_answer_key: str = random_str()
				correct_answers[test.id][correct_answer.answer] = correct_answer_key
				correct_answers_id[correct_answer_key] = correct_answer.id
				ram.append(correct_answer.id)

			if not test.not_answer:
				answer_option = await test_answer_options(session, test.id)
				answer_options[test.id] = {}

				for option in answer_option:
					answer_options[test.id][option.answer] = option.id

			if test.id not in tests_id: tests_id.append(test.id)

	await state.update_data(tests=tests, 
		correct_answers=correct_answers, 
		answer_options=answer_options,
		correct_answers_id=correct_answers_id,
		tests_id=tests_id,
		index=0
	)

	text = 'Ваш тест был сгенерирован ✅'
	menu_button = {'Начать 🏁': 'begin', '< Главное меню': 'base_menu'}
	keyboard = inline_keyboard(menu_button, row=1)

	await state.set_state(UserTest.test_passing)
	await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(StateFilter(UserTest.test_passing))
async def test_passing_callback(callback: CallbackQuery, bot: Bot, state: FSMContext):
	menu_button: Dict[str, str] = {'< Главное меню': 'base_menu', 'Следующий вопрос': 'next'}
	state_data: Dict[str, Dict] = await state.get_data()

	tests: Dict[int, Dict[str, str]] = state_data['tests']
	correct_answers_id: Dict[str, int] = state_data['correct_answers_id']
	correct_answers: Dict[int, Dict[int, str]] = state_data['correct_answers'] 
	answer_options: Dict[int, List[str]] = state_data['answer_options']
	tests_id_list: List[int] = state_data['tests_id']
	index: int = state_data['index']
	user_answer: List[str] = state_data.get('user_answer')

	if callback.data == 'next' or callback.data == 'begin':
		if len(tests_id_list)-1 >= index:
			await callback.message.delete()

			test_id: int = tests_id_list[index]
			test = tests.get(test_id)
			photo = test.get('question_img')
			text = test.get('question')
			buttons = {}
			options_l = {}

			if not test['not_answer']:
				keys = correct_answers[test_id] | answer_options[test_id]
				options = [x for x in keys]
				shuffle(options)

				for i in options:
					for key in keys:
						if key == i:
							key = str(keys[key])
							buttons[i] = key
							options_l[key] = i
							break

			else:
				text = f"{text}\n\n<b>На данный вопрос нет точного ответа, введите свой вариант ответа</b>"

			test['test_id'] = test_id
			keyboard = inline_keyboard(buttons, menu_button=menu_button, row=1)
			index += 1

			if user_answer is not None and user_answer.get(test_id) is None: user_answer[test_id] = []
			if photo is not None:
				message_type = 'media'
				photo = FSInputFile(f"{settings.IMG_PATH}{photo}")

				await bot.send_photo(chat_id=callback.message.chat.id, 
					photo=photo, 
					reply_markup=keyboard, 
					caption=text
				)

			else:
				message_type = 'message'
				await callback.message.answer(text, reply_markup=keyboard)
			

			await state.update_data(index=index, 
				options_l=options_l, 
				test=test, 
				message_type=message_type,  
				user_answer={test_id: []} if user_answer is None else user_answer
			)

		else:
			await callback.message.delete()

			keyboard = inline_keyboard({}, menu_button={'Получить результат теста': 'test_result'}, row=1) 
			await state.set_state(UserTest.test_result)
			await callback.message.answer('Тест завершен', reply_markup=keyboard)

	else:
		await callback.message.delete()
		options_l: Union(Dict[str, str], None) = state_data.get('options_l')
		test: Dict[str, str] = state_data.get('test')
		test_answer = user_answer[test['test_id']]
		answer_key = callback.data
		buttons = {}

		if answer_key in test_answer: test_answer.remove(answer_key)
		else: test_answer.append(answer_key)

		for i in options_l:
			text = options_l.get(i)
			if i in test_answer:
				text = f"► {text}"

			buttons[text] = i
		
		user_answer[test['test_id']] = test_answer
		keyboard = inline_keyboard(buttons, menu_button=menu_button, row=1)
		await state.update_data(user_answer=user_answer)

		if test['question_img'] is not None:
			photo = FSInputFile(f"{settings.IMG_PATH}{test['question_img']}")
			await bot.send_photo(chat_id=callback.message.chat.id, 
				photo=photo, 
				reply_markup=keyboard, 
				caption=test['question']
			)
		
		else:
			await callback.message.answer(test['question'], reply_markup=keyboard)


@router.message(StateFilter(UserTest.test_passing))
async def test_passing_message(message: Message, state: FSMContext):
	state_data = await state.get_data()

	user_answer: List[str] = state_data.get('user_answer')
	test: Dict[str, str] = state_data.get('test')

	user_answer[test['test_id']].append(message.text)
	await state.update_data(user_answer=user_answer)


@router.callback_query(StateFilter(UserTest.test_result))
async def test_result(callback: CallbackQuery, state: FSMContext):
	state_data = await state.get_data()
	menu_button = {"Главное меню": 'base_menu'}
	text = 'Результаты вашего теста\n'

	user_answers: List[str] = state_data['user_answer']
	tests: Dict[int, Dict[str, str]] = state_data['tests']
	correct_answers_id: Dict[str, int] = state_data['correct_answers_id']
	correct_answers: Dict[int, Dict[int, str]] = state_data['correct_answers'] 
	tests_id_list: List[int] = state_data['tests_id']

	question_num = 1

	for t in tests_id_list:
		text += f"\n<b>Вопрос {question_num} / {len(tests_id_list)}</b>\n"
		correct_answer = correct_answers.get(t)
		user_answer = user_answers.get(t)
		test = tests.get(t)
		incorect = True

		if len(user_answer) > 0:
			correct_answer_key = []
			for c in correct_answer:
				correct_answer_key.append(correct_answer[c])

			if correct_answer_key == user_answer:
				incorect = False
				text += 'Правильно'
		
		if incorect:
			if len(user_answer) == 0:text += 'Вы не дали ответа на данный вопрос\n'
			elif test['not_answer']: text += 'На этот вопрос нет однозначного ответа ниже указан ответ администратора\n'
			else: text += 'Вы указали неверный ответ\n'
			
			text += '\n<b>Ответ</b>:'
			for a in correct_answer:
				text += f"\n{a}"

		text += '\n'
		question_num += 1
	
	keyboard = inline_keyboard({}, menu_button={'< Главное меню': 'base_menu'})
	await callback.message.edit_text(text=text, reply_markup=keyboard)
