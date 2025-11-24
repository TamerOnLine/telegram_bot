from telegram import ReplyKeyboardMarkup, KeyboardButton


def make_main_keyboard(role: str) -> ReplyKeyboardMarkup:
    if role == "teacher":
        buttons = [
            [KeyboardButton("/set_role_student"), KeyboardButton("/set_role_teacher")],
            [KeyboardButton("/set_goal"), KeyboardButton("/today")],
            [KeyboardButton("/students")],
        ]
    else:
        buttons = [
            [KeyboardButton("/set_role_student"), KeyboardButton("/set_role_teacher")],
            [KeyboardButton("/set_goal"), KeyboardButton("/today")],
        ]

    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
