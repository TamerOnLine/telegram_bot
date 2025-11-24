# Quran Hifz Coach Bot

An interactive Telegram bot for Quran memorization. It supports student
and teacher modes, daily progress tracking, and goal setting, all stored
in a simple JSON file.

## Project Structure

    apps/
      quran_hifz_bot/
        bot.py
        config.py
        storage.py
        helpers.py
        commands.py
        handlers.py
        data.json
        .env

## Features

-   Student and teacher modes
-   Set and view memorization goals
-   Record daily progress
-   Persistent storage in `data.json`
-   Clean modular file structure

## Requirements

-   Python 3.10+
-   python-telegram-bot 21+
-   python-dotenv

Install dependencies:

    pip install python-telegram-bot==21.0.1 python-dotenv

## .env Configuration

    TELEGRAM_BOT_TOKEN=YOUR_TOKEN
    BOT_NAME=quran_hifz_bot

## Run the Bot

    python bot.py

## Commands

  Command             Description
  ------------------- ------------------------------
  /start              Start the bot
  /help               Help menu
  /set_role_student   Switch to student mode
  /set_role_teacher   Switch to teacher mode
  /set_goal           Set a memorization goal
  /my_goal            Show your current goal
  /today              Log what you memorized today

## Future Enhancements

-   Full student management for teachers\
-   Weekly/monthly reports\
-   Streamlit dashboard\
-   Audio memorization review\
-   Docker support

Developed by TamerOnLine.
