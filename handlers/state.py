from aiogram.fsm.state import State, StatesGroup


class SubChannel(StatesGroup):
	sub = State()


class AdminPanel(StatesGroup):
	menu = State()
	category_selection = State()
	under_topic_selection = State()
	new_under_topic = State()
	save_under_topic = State()
	choice_of_test = State()
	add_new_user = State()


class TestPanel(StatesGroup):
	new_test = State()
	test = State()
	new_question = State()
	question_img = State()
	add_img = State()
	answer_type = State()
	answer_options = State()
	test_result = State()


class UserTest(StatesGroup):
	difficulty_selection = State()
	under_topic_selection = State()
	test_selection = State()
	test_passing = State()
	test_result = State()


class Videos(StatesGroup):
	cate_selection = State()
	video_selection = State()


class VideosAdm(StatesGroup):
	cate_selection = State()
	footage_cate_name = State()
	new_cate = State()
	video_selection = State()
	new_video = State()
	video = State()
	delete_vidio = State()


class Articles(StatesGroup):
	cate_selection = State()
	article_selection = State()


class ArticlesAdm(StatesGroup):
	cate_selection = State()
	new_cate = State()
	article_selection = State()
	new_article = State()
	article_link = State()
	delete_article = State()

