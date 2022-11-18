from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

from utils.minor_func import (
		main_menu, 
		check_sub_channels, 
		admin_panel, 
		test_difficulty_level,
		footage_categorys,
		articles_categorys
	)


# Это будет outer-мидлварь на любые колбэки
class BaseMenuMiddleware(BaseMiddleware):
	async def __call__(self,
		handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
		event: CallbackQuery,
		data: Dict[str, Any],
	) -> Any:
		callback_data_router = {
			'base_menu': main_menu, 
			'admin_panel': admin_panel,
			'difficulty_level': test_difficulty_level,
			'vidios': footage_categorys,
			'articles': articles_categorys
		}
		callback_func = callback_data_router.get(event.data)

		if callback_func is not None:
			try:
				return await callback_func(event.message, data['bot'], data['state'])
			except:
				return await callback_func(event.message, data['bot'], data['state'], update=False)

		return await handler(event, data)
