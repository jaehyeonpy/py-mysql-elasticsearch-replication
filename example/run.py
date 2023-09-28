import os

from pymyelarepl import PyMyElaRepl


config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
pymyelarepl = PyMyElaRepl(config_path)
pymyelarepl.run()