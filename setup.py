import os
import re
from setuptools import setup

root_dir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(root_dir, 'README.md'), 'r') as f:
    # Read from the file and strip out the badges.
    long_desc = re.sub(r'(^# mike)\n\n(.+\n)*', r'\1', f.read())

setup(long_description=long_desc,
      long_description_content_type='text/markdown',
      # TODO: Move this to pyproject.toml after dropping Python 3.8 support.
      license='BSD-3-Clause')
