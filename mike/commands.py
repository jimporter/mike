import http.server
from jinja2 import Template
from pkg_resources import resource_stream

from . import git_utils
from . import mkdocs_utils
from . import server
from .app_version import version as app_version
from .versions import Versions

versions_file = 'versions.json'


def list_versions(branch='gh-pages'):
    try:
        return Versions.loads(git_utils.read_file(
            branch, versions_file, universal_newlines=True
        ))
    except git_utils.GitError:
        return Versions()


def versions_to_file_info(versions):
    return git_utils.FileInfo(versions_file, versions.dumps())


def make_nojekyll():
    return git_utils.FileInfo('.nojekyll', '')


def deploy(site_dir, version, title=None, aliases=[], update_aliases=False,
           branch='gh-pages', message=None):
    if message is None:
        message = (
            'Deployed {rev} to {doc_version} with MkDocs {mkdocs_version} ' +
            'and mike {mike_version}'
        ).format(
            rev=git_utils.get_latest_commit('HEAD', short=True),
            doc_version=version,
            mkdocs_version=mkdocs_utils.version(),
            mike_version=app_version
        )

    all_versions = list_versions(branch)
    info = all_versions.add(version, title, aliases, update_aliases)
    destdirs = [str(info.version)] + list(info.aliases)

    with git_utils.Commit(branch, message) as commit:
        commit.delete_files(destdirs)

        for f in git_utils.walk_real_files(site_dir):
            for d in destdirs:
                commit.add_file(f.copy(d, site_dir))
        commit.add_file(versions_to_file_info(all_versions))
        commit.add_file(make_nojekyll())


def delete(versions=None, all=False, branch='gh-pages', message=None):
    if not all and versions is None:
        raise ValueError('specify `version` or `all`')

    if message is None:
        message = (
            'Removed {doc_version} with mike {mike_version}'
        ).format(
            doc_version='everything' if all else ', '.join(versions),
            mike_version=app_version
        )

    with git_utils.Commit(branch, message) as commit:
        if all:
            commit.delete_files('*')
        else:
            all_versions = list_versions(branch)
            try:
                removed = all_versions.difference_update(versions)
            except KeyError as e:
                raise ValueError('version {} does not exist'.format(e))

            for i in removed:
                if isinstance(i, str):
                    commit.delete_files([i])
                else:
                    commit.delete_files([str(i.version)] + list(i.aliases))
            commit.add_file(versions_to_file_info(all_versions))


def alias(version, aliases, branch='gh-pages', message=None):
    if message is None:
        message = (
            'Copied {doc_version} to {aliases} with mike {mike_version}'
        ).format(
            doc_version=version,
            aliases=', '.join(aliases),
            mike_version=app_version
        )

    all_versions = list_versions(branch)
    try:
        destdirs = all_versions.update(version, aliases=aliases)
    except KeyError as e:
        raise ValueError('version {} does not exist'.format(e))

    with git_utils.Commit(branch, message) as commit:
        commit.delete_files(destdirs)

        for f in git_utils.walk_files(branch, version):
            for d in destdirs:
                commit.add_file(f.copy(d, version))
        commit.add_file(versions_to_file_info(all_versions))


def retitle(version, title, branch='gh-pages', message=None):
    if message is None:
        message = (
            'Set title of {doc_version} to {title} with mike {mike_version}'
        ).format(doc_version=version, title=title, mike_version=app_version)

    all_versions = list_versions(branch)
    try:
        all_versions.update(version, title)
    except KeyError:
        raise ValueError('version {} does not exist'.format(version))

    with git_utils.Commit(branch, message) as commit:
        commit.add_file(versions_to_file_info(all_versions))


def set_default(version, branch='gh-pages', message=None):
    if message is None:
        message = (
            'Set default version to {doc_version} with mike {mike_version}'
        ).format(doc_version=version, mike_version=app_version)

    all_versions = list_versions(branch)
    if not all_versions.find(version):
        raise ValueError('version {} does not exist'.format(version))

    with git_utils.Commit(branch, message) as commit, \
         resource_stream(__name__, 'templates/index.html') as f:  # noqa
        t = Template(f.read().decode('utf-8'))
        commit.add_file(git_utils.FileInfo(
            'index.html', t.render(version=version)
        ))


def serve(address='localhost:8000', branch='gh-pages', verbose=True):
    my_branch = branch

    class Handler(server.GitBranchHTTPHandler):
        branch = my_branch

    host, port = address.split(':')
    httpd = http.server.HTTPServer((host, int(port)), Handler)

    if verbose:
        print('Starting server at http://{}/'.format(address))
        print('Press Ctrl+C to quit.')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        if verbose:
            print('Stopping server...')
