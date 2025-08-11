from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


# TODO: this should be killed with fire!!!
def render_template_to_string(template_name: str, context: dict) -> str:
    """Renders a Jinja2 template to a string."""
    template = templates.get_template(template_name)
    return template.render(context)
