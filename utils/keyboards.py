from typing import Union

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# Функция для создания inline кнопок
def inline_keyboard(items: Union[dict, list], 
		default = True, 
		menu_button:dict = None,
		row = 1
	) -> InlineKeyboardMarkup:
	row_num: int = 0
	key_num: int = 0
	key_len: int = len(items.keys())
	buttons: list = []
	ram: list = []

	for it in items:
		text = it

		if default:
			button = InlineKeyboardButton(text=text, callback_data=items[it])

		else:
			button_type = items[it]['button_type']
			value = items[it]['value']
			button = InlineKeyboardButton(
					text=text,
					callback_data=value if button_type == 'c_data' else None,
					switch_inline_query=value if button_type == 's_inline_query' else None,
					switch_inline_query_current_chat=value if button_type == 's_inline_query_c' else None,
				)
		
		if row > 1:
			ram.append(button)
			row_num += 1
			if row_num >= row or key_num+1 >= key_len:
				buttons.append(ram)
				ram = []
				row_num = 0
		
		else:
			buttons.append([button])

		key_num += 1

	if menu_button is not None:
		mb = []
		for i in menu_button:
			mb.append(InlineKeyboardButton(text=i, callback_data=menu_button[i]))

		buttons.append(mb)

	return InlineKeyboardMarkup(row_width=2, inline_keyboard=buttons)
