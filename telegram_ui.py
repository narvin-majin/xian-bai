from project_manager import (
    load_projects,
    create_project,
    switch_project,
    add_project_task,
    get_project_tasks,
    complete_project_task,
    list_projects
)
projects = load_projects()

from state_manager import (
    track_task,
    complete_task,
    get_status
)

def register_handlers(bot):
    
    # ==================================================
    # COMMANDS
    # ==================================================

    @bot.message_handler(commands=["start"])
    def start(message):
        bot.reply_to(
            message,
            "Assistant ready.\n\n"
            "/track <task>\n"
            "/done\n"
            "/status"
        )


    @bot.message_handler(commands=["track"])
    def track(message):

        task = message.text.replace(
            "/track",
            ""
        ).strip()

        bot.reply_to(
            message,
            track_task(task)
        )


    @bot.message_handler(commands=["done"])
    def done(message):

        bot.reply_to(
            message,
            complete_task()
        )


    @bot.message_handler(commands=["status"])
    def status(message):

        bot.reply_to(
            message,
            get_status()
        )



    @bot.message_handler(commands=["project_create"])
    def project_create(message):

        name = message.text.replace(
            "/project_create",
            ""
        ).strip()

        bot.reply_to(
            message,
            create_project(name)
        )


    @bot.message_handler(commands=["projects"])
    def projects_cmd(message):

        bot.reply_to(
            message,
            list_projects()
        )


    @bot.message_handler(commands=["project_switch"])
    def project_switch(message):

        name = message.text.replace(
            "/project_switch",
            ""
        ).strip()

        bot.reply_to(
            message,
            switch_project(name)
        )

    @bot.message_handler(commands=["project_task_add"])
    def project_task_add(message):

        task_name = (
            message.text
            .replace("/project_task_add", "")
            .strip()
        )

        bot.reply_to(
            message,
            add_project_task(task_name)
        )

    @bot.message_handler(commands=["project_tasks"])
    def project_tasks(message):

        bot.reply_to(
            message,
            get_project_tasks()
        )


    @bot.message_handler(commands=["project_task_done"])
    def project_task_done(message):

        task_number = (
            message.text
            .replace("/project_task_done", "")
            .strip()
        )

        try:
            task_number = int(task_number)

        except ValueError:

            bot.reply_to(
                message,
                "Task number must be a number."
            )
            return

        bot.reply_to(
            message,
            complete_project_task(task_number)
        )