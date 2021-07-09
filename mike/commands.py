import http.server
import os
import posixpath
from contextlib import contextmanager
from jinja2 import Template
from pkg_resources import resource_stream

from . import git_utils
from . import mkdocs_utils
from . import server
from .app_version import version as app_version
from .versions import Versions

versions_file = 'versions.json'


def _redirect_template(user_template=None):
    f = (open(user_template, 'rb') if user_template else
         resource_stream(__name__, 'templates/redirect.html'))
    with f:
        return Template(f.read().decode('utf-8'), autoescape=True)


def _add_redirect_to_commit(commit, template, src, dst,
                            use_directory_urls):
    if os.path.splitext(src)[1] == '.html':
        reldst = os.path.relpath(dst, os.path.dirname(src))
        href = '/'.join(reldst.split(os.path.sep))
        if use_directory_urls and posixpath.basename(href) == 'index.html':
            href = posixpath.dirname(href) + '/'
        commit.add_file(git_utils.FileInfo(src, template.render(href=href)))


def list_versions(branch='gh-pages', prefix=''):
    try:
        return Versions.loads(git_utils.read_file(
            branch, os.path.join(prefix, versions_file),
            universal_newlines=True
        ))
    except git_utils.GitError:
        return Versions()


def versions_to_file_info(versions, prefix=''):
    return git_utils.FileInfo(os.path.join(prefix, versions_file),
                              versions.dumps())


def make_nojekyll():
    return git_utils.FileInfo('.nojekyll', '')


@contextmanager
def deploy(cfg, version, title=None, aliases=[], update_aliases=False,
           redirect=True, template=None, *, branch='gh-pages', message=None,
           prefix=''):
    if message is None:
        message = (
            'Deployed {rev} to {doc_version}{prefix} with MkDocs ' +
            '{mkdocs_version} and mike {mike_version}'
        ).format(
            rev=git_utils.get_latest_commit('HEAD', short=True),
            doc_version=version,
            prefix=' in {}'.format(prefix) if prefix else '',
            mkdocs_version=mkdocs_utils.version(),
            mike_version=app_version
        )

    all_versions = list_versions(branch, prefix)
    info = all_versions.add(version, title, aliases, update_aliases)
    version_str = str(info.version)
    destdir = os.path.join(prefix, version_str)
    alias_destdirs = [os.path.join(prefix, i) for i in info.aliases]

    # Let the caller perform the build.
    yield

    if redirect and info.aliases:
        t = _redirect_template(template)

    with git_utils.Commit(branch, message) as commit:
        commit.delete_files([version_str] + list(info.aliases))

        for f in git_utils.walk_real_files(cfg['site_dir']):
            canonical_file = f.copy(destdir, cfg['site_dir'])
            commit.add_file(canonical_file)
            for d in alias_destdirs:
                alias_file = f.copy(d, cfg['site_dir'])
                if redirect:
                    _add_redirect_to_commit(
                        commit, t, alias_file.path, canonical_file.path,
                        cfg['use_directory_urls']
                    )
                else:
                    commit.add_file(alias_file)

        commit.add_file(versions_to_file_info(all_versions, prefix))
        commit.add_file(make_nojekyll())


def delete(versions=None, all=False, *, branch='gh-pages', message=None,
           prefix=''):
    if not all and versions is None:
        raise ValueError('specify `version` or `all`')

    if message is None:
        message = (
            'Removed {doc_version}{prefix} with mike {mike_version}'
        ).format(
            doc_version='everything' if all else ', '.join(versions),
            prefix=' in {}'.format(prefix) if prefix else '',
            mike_version=app_version
        )

    with git_utils.Commit(branch, message) as commit:
        if all:
            if prefix:
                commit.delete_files([prefix])
            else:
                commit.delete_files('*')
        else:
            all_versions = list_versions(branch, prefix)
            try:
                removed = all_versions.difference_update(versions)
            except KeyError as e:
                raise ValueError('version {!r} does not exist'.format(e))

            for i in removed:
                if isinstance(i, str):
                    commit.delete_files([os.path.join(prefix, i)])
                else:
                    commit.delete_files(
                        [os.path.join(prefix, str(i.version))] +
                        [os.path.join(prefix, j) for j in i.aliases]
                    )
            commit.add_file(versions_to_file_info(all_versions, prefix))


def alias(cfg, version, aliases, update_aliases=False, redirect=True,
          template=None, *, branch='gh-pages', message=None, prefix=''):
    all_versions = list_versions(branch, prefix)
    try:
        real_version = all_versions.find(version, strict=True)[0]
    except KeyError as e:
        raise ValueError('version {!r} does not exist'.format(e))

    if message is None:
        message = (
            'Copied {doc_version} to {aliases}{prefix} with mike ' +
            '{mike_version}'
        ).format(
            doc_version=real_version,
            aliases=', '.join(aliases),
            prefix=' in {}'.format(prefix) if prefix else '',
            mike_version=app_version
        )

    new_aliases = all_versions.update(real_version, aliases=aliases,
                                      update_aliases=update_aliases)
    destdirs = [os.path.join(prefix, i) for i in new_aliases]

    if redirect and destdirs:
        t = _redirect_template(template)

    with git_utils.Commit(branch, message) as commit:
        commit.delete_files(destdirs)

        canonical_dir = os.path.join(prefix, str(real_version))
        for canonical_file in git_utils.walk_files(branch, canonical_dir):
            for d in destdirs:
                alias_file = canonical_file.copy(d, canonical_dir)
                if redirect:
                    _add_redirect_to_commit(
                        commit, t, alias_file.path, canonical_file.path,
                        cfg['use_directory_urls']
                    )
                else:
                    commit.add_file(alias_file)
        commit.add_file(versions_to_file_info(all_versions, prefix))


def retitle(version, title, *, branch='gh-pages', message=None, prefix=''):
    if message is None:
        message = (
            'Set title of {doc_version} to {title}{prefix} with mike ' +
            '{mike_version}'
        ).format(
            doc_version=version,
            title=title,
            prefix=' in {}'.format(prefix) if prefix else '',
            mike_version=app_version
        )

    all_versions = list_versions(branch, prefix)
    try:
        all_versions.update(version, title)
    except KeyError:
        raise ValueError('version {!r} does not exist'.format(version))

    with git_utils.Commit(branch, message) as commit:
        commit.add_file(versions_to_file_info(all_versions, prefix))


def set_default(version, template=None, *, branch='gh-pages', message=None,
                prefix=''):
    if message is None:
        message = (
            'Set default version to {doc_version}{prefix} with mike ' +
            '{mike_version}'
        ).format(
            doc_version=version,
            prefix=' in {}'.format(prefix) if prefix else '',
            mike_version=app_version
        )

    all_versions = list_versions(branch, prefix)
    if not all_versions.find(version):
        raise ValueError('version {!r} does not exist'.format(version))

    t = _redirect_template(template)
    with git_utils.Commit(branch, message) as commit:
        commit.add_file(git_utils.FileInfo(
            os.path.join(prefix, 'index.html'), t.render(href=version + '/')
        ))


def serve(address='localhost:8000', *, branch='gh-pages', verbose=True):
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
