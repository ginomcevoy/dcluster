from dcluster.config import main_config
from dcluster.util import fs as fs_util
from dcluster.util import logger


def get_workpath(args):
    '''
    Set the work path of dcluster. By default, it is set by the configuration (paths:work),
    but it can be overridden by the user using the --workpath optional variable.
    '''
    log = logger.logger_for_me(get_workpath)
    if args.workpath is not None:
        workpath = args.workpath
    else:
        # work_path_with_shell_variables = main_config.paths('work')
        # log.debug('workpath shell %s' % work_path_with_shell_variables)
        # workpath = fs_util.evaluate_shell_path(work_path_with_shell_variables)
        workpath = main_config.paths('work')

    # create the directory, it may not exist but we need it now
    log.debug('workpath %s' % workpath)
    fs_util.create_dir_dont_complain(workpath)
    return workpath
