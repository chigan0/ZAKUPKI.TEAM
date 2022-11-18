from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, FSInputFile, ContentType as CT
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.minor_func import videos_list
from utils.keyboards import inline_keyboard
from settings import settings
from .state import Videos

router = Router()


@router.callback_query(StateFilter(Videos.cate_selection))
async def cate_selection(callback: CallbackQuery, state: FSMContext):
	text, buttons, menu_button = await videos_list(int(callback.data), state)

	keyboard = inline_keyboard(buttons, menu_button=menu_button, row=2)
	await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(StateFilter(Videos.video_selection))
async def video_selection(callback: CallbackQuery, bot: Bot, state: FSMContext):
	message = await callback.message.answer('Загрузка видео ...')

	state_data = await state.get_data()
	keyboard = inline_keyboard({}, menu_button={'🎥 Видео': 'vidios'})
	video_data = state_data['videos'].get(int(callback.data))

	if video_data is None:
		await message.delete()
		return await callback.message.edit_text('Видео не найденно', reply_markup=keyboard)

	video = FSInputFile(f"{settings.VIDEO_PATH}{video_data['videos_name']}")

	await callback.message.delete()
	await bot.send_video(chat_id=callback.message.chat.id, 
		video=video, 
		reply_markup=keyboard, 
		caption=video_data['name']
	)
	await message.delete()

