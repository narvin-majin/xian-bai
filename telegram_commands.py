from telebot.types import BotCommand


def register_commands(bot):

    bot.set_my_commands([
        BotCommand("start", "Start Xian Bai"),
        BotCommand("status", "Show assistant status"),
        BotCommand("track", "Track a task"),
        BotCommand("done", "Complete current task"),
        BotCommand("projects", "List projects"),
        BotCommand("project_create", "Create project"),
        BotCommand("project_switch", "Switch project"),
        BotCommand("project_task_add", "Add project task"),
        BotCommand("project_tasks", "Show project tasks"),
        BotCommand("project_task_done", "Complete project task"),
    ])