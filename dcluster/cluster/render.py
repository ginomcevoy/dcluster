import jinja2

from dcluster import config, logger


class JinjaRenderer(logger.LoggerMixin):

    def __init__(self, templates_dir):
        self.templates_dir = templates_dir

    def render_blueprint(self, cluster_specs, template_filename):

        # build the replacement dictionary
        replacements = dict(**cluster_specs)
        self.logger.debug(replacements)

        # Load Jinja2 template
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(self.templates_dir),
                                 trim_blocks=True, lstrip_blocks=True)

        template = env.get_template(template_filename)
        rendered = template.render(**replacements)
        self.logger.debug(rendered)
        return rendered
