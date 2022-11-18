from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from utils.minor_func import main_menu, check_sub_channels
from .state import SubChannel

router = Router()


@router.message(Command(commands=["start"]))
async def cmd_start(message: Message, bot: Bot, state: FSMContext):
	print(message.from_user.id)
	await main_menu(message, bot, state, False)


@router.callback_query(StateFilter(SubChannel.sub))
async def check_sub(callback: CallbackQuery, bot: Bot, state: FSMContext):
	sub_state = await check_sub_channels(bot, callback.message.chat.id)
	if sub_state:
		await state.clear()
		await main_menu(callback.message, bot, state)
