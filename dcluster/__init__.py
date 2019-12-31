# Single place to define the software version
__version__ = '0.0.1'

# Environment variable used to determine if we want a development environment.
# For a dev setting, set the environment variable to 'True' when calling a dcluster script
DEVELOPMENT_ENV_VAR = 'DCLUSTER_DEV'

# File to store configuration in a production environment
CONFIG_DIR = '/etc/dcluster'
CONFIG_FILE = 'config.yml'
