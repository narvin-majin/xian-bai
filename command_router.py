def handle_command(
    command,
    projects
):

    if command == "/projects":

        if not projects["projects"]:
            return "No projects found."

        output = "Projects:\n\n"

        for project_name in projects["projects"]:

            marker = ""

            if project_name == projects["active_project"]:
                marker = " (ACTIVE)"

            output += f"- {project_name}{marker}\n"

        return output

    return "Unknown command."
