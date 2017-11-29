from __future__ import unicode_literals

import re
import subprocess

site_dir = 'site'


def build():
    subprocess.check_call(['mkdocs', 'build'])


def version():
    output = subprocess.check_output(
        ['mkdocs', '--version'], universal_newlines=True
    ).rstrip()
    m = re.search('^mkdocs, version (.*)$', output)
    return m.group(1)
