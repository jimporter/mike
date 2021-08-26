import argparse
import os
import sys

from . import commands
from . import git_utils
from . import mkdocs_utils
from .app_version import version as app_version

description = """
mike is a utility to make it easy to deploy multiple versions of your
MkDocs-powered docs to a Git branch, suitable for deploying to Github via
gh-pages. It's designed to produce one version of your docs at a time. That
way, you can easily deploy a new version without touching any older versions of
your docs.
"""

deploy_desc = """
Build the current documentation and deploy it to the specified version (and
aliases, if any) on the target branch.
"""

delete_desc = """
Delete the documentation for the specified versions or aliases from the target
branch. If deleting a version, that version and all its aliases will be
removed; if deleting an alias, only that alias will be removed.
"""

alias_desc = """
Add one or more new aliases to the specified version of the documentation on
the target branch.
"""

retitle_desc = """
Change the descriptive title of the specified version of the documentation on
the target branch.
"""

list_desc = """
Display a list of the currently-deployed documentation versions on the target
branch.
"""

set_default_desc = """
Set the default version of the documentation on the target branch, redirecting
users from the root of the site to that version.
"""

serve_desc = """
Start the development server, serving pages from the target branch.
"""

generate_completion_desc = """
Generate shell-completion functions for bfg9000 and write them to standard
output. This requires the Python package `shtab`.
"""


def add_git_arguments(parser, *, commit=True, prefix=True):
    # Add this whenever we add git arguments since we pull the remote and
    # branch from mkdocs.yml.
    parser.add_argument('-F', '--config-file', metavar='FILE',
                        default='mkdocs.yml',
                        help='the MkDocs configuration file to use')

    git = parser.add_argument_group('git arguments')
    git.add_argument('-r', '--remote',
                     help='origin to push to (default: origin)')
    git.add_argument('-b', '--branch',
                     help='branch to commit to (default: gh-pages)')

    if commit:
        git.add_argument('-m', '--message', help='commit message')
        git.add_argument('-p', '--push', action='store_true',
                         help='push to {remote}/{branch} after commit')
        git.add_argument('-f', '--force', action='store_true',
                         help='force push when pushing')

    if prefix:
        git.add_argument('--prefix', metavar='PATH', default='',
                         help=('subdirectory within {branch} where docs are ' +
                               'located'))

    group = git.add_mutually_exclusive_group()
    group.add_argument('--rebase', action='store_true',
                       help='rebase with remote')
    group.add_argument('--ignore', action='store_true',
                       help='ignore remote status')


def load_mkdocs_config(args, strict=False):
    try:
        cfg = mkdocs_utils.load_config(args.config_file)
        if args.branch is None:
            args.branch = cfg['remote_branch']
        if args.remote is None:
            args.remote = cfg['remote_name']
        return cfg
    except FileNotFoundError as e:
        if strict:
            raise
        if args.branch is None or args.remote is None:
            raise FileNotFoundError(
                '{}; pass --config-file or set --remote/--branch explicitly'
                .format(str(e))
            )


def check_remote_status(args, strict=False):
    if args.ignore:
        return

    try:
        git_utils.try_rebase_branch(args.remote, args.branch,
                                    force=args.rebase)
    except (git_utils.GitBranchDiverged, git_utils.GitRevUnrelated) as e:
        msg = (str(e) + '\n  Pass --ignore to ignore this or --rebase to ' +
               'rebase onto remote')
        if strict:
            raise ValueError(msg)
        else:
            sys.stderr.write('warning: {}\n'.format(msg))


def deploy(parser, args):
    cfg = load_mkdocs_config(args, strict=True)
    check_remote_status(args, strict=True)
    with commands.deploy(cfg, args.version, args.title, args.alias,
                         args.update_aliases, args.redirect, args.template,
                         branch=args.branch, message=args.message,
                         prefix=args.prefix):
        with mkdocs_utils.inject_plugin(args.config_file) as config_file:
            mkdocs_utils.build(config_file, args.version)
    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)


def delete(parser, args):
    load_mkdocs_config(args)
    check_remote_status(args, strict=True)
    commands.delete(args.version, args.all, branch=args.branch,
                    message=args.message, prefix=args.prefix)
    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)


def alias(parser, args):
    cfg = load_mkdocs_config(args)
    check_remote_status(args, strict=True)
    commands.alias(cfg, args.version, args.alias, args.update_aliases,
                   args.redirect, args.template, branch=args.branch,
                   message=args.message, prefix=args.prefix)
    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)


def retitle(parser, args):
    load_mkdocs_config(args)
    check_remote_status(args, strict=True)
    commands.retitle(args.version, args.title, branch=args.branch,
                     message=args.message, prefix=args.prefix)
    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)


def list_versions(parser, args):
    def print_version(info):
        version = str(info.version)
        aliases = (' [{}]'.format(', '.join(sorted(info.aliases)))
                   if info.aliases else '')
        if info.title != version:
            print('"{title}" ({version}){aliases}'.format(
                title=info.title, version=version, aliases=aliases
            ))
        else:
            print('{version}{aliases}'.format(
                version=version, aliases=aliases
            ))

    load_mkdocs_config(args)
    check_remote_status(args)
    all_versions = commands.list_versions(args.branch, args.prefix)

    if args.version:
        try:
            key = all_versions.find(args.version, strict=True)
            info = all_versions[key[0]]
            if args.json:
                print(info.dumps())
            else:
                print_version(info)
        except KeyError:
            raise ValueError('version {} does not exist'.format(args.version))
    elif args.json:
        print(all_versions.dumps())
    else:
        for i in all_versions:
            print_version(i)


def set_default(parser, args):
    load_mkdocs_config(args)
    check_remote_status(args, strict=True)
    commands.set_default(args.version, args.template, branch=args.branch,
                         message=args.message, prefix=args.prefix)
    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)


def serve(parser, args):
    load_mkdocs_config(args)
    check_remote_status(args)
    commands.serve(args.dev_addr, branch=args.branch)


def help(parser, args):
    parser.parse_args(args.subcommand + ['--help'])


def generate_completion(parser, args):
    try:
        import shtab
        print(shtab.complete(parser, shell=args.shell))
    except ImportError:  # pragma: no cover
        print('shtab not found; install via `pip install shtab`')
        return 1


def main():
    parser = argparse.ArgumentParser(prog='mike', description=description)
    subparsers = parser.add_subparsers(metavar='COMMAND')
    subparsers.required = True

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + app_version)

    deploy_p = subparsers.add_parser(
        'deploy', description=deploy_desc,
        help='build docs and deploy them to a branch'
    )
    deploy_p.set_defaults(func=deploy)
    deploy_p.add_argument('-t', '--title',
                          help='short descriptive title for this version')
    deploy_p.add_argument('-u', '--update-aliases', action='store_true',
                          help='update aliases pointing to other versions')
    deploy_p.add_argument('--no-redirect', dest='redirect', default=True,
                          action='store_false',
                          help='make copies of docs for each alias')
    deploy_p.add_argument('-T', '--template',
                          help='the template file to use for redirects')
    add_git_arguments(deploy_p)
    deploy_p.add_argument('version', metavar='VERSION',
                          help='version (directory) to deploy this build to')
    deploy_p.add_argument('alias', nargs='*', metavar='ALIAS',
                          help='alias for this build (e.g. "latest")')

    delete_p = subparsers.add_parser(
        'delete', description=delete_desc, help='delete docs from a branch'
    )
    delete_p.set_defaults(func=delete)
    delete_p.add_argument('--all', action='store_true',
                          help='delete everything')
    add_git_arguments(delete_p)
    delete_p.add_argument('version', nargs='*', metavar='VERSION',
                          help='version (directory) to delete')

    alias_p = subparsers.add_parser(
        'alias', description=alias_desc, help='alias docs from a branch'
    )
    alias_p.set_defaults(func=alias)
    alias_p.add_argument('-u', '--update-aliases', action='store_true',
                         help='update aliases pointing to other versions')
    alias_p.add_argument('--no-redirect', dest='redirect', default=True,
                         action='store_false',
                         help='make copies of docs for each alias')
    alias_p.add_argument('-T', '--template',
                         help='the template file to use for redirects')
    add_git_arguments(alias_p)
    alias_p.add_argument('version', metavar='VERSION',
                         help='version (directory) to alias')
    alias_p.add_argument('alias', nargs='*', metavar='ALIAS',
                         help='alias to add (e.g. "latest")')

    retitle_p = subparsers.add_parser(
        'retitle', description=retitle_desc,
        help='change the title of a version'
    )
    retitle_p.set_defaults(func=retitle)
    add_git_arguments(retitle_p)
    retitle_p.add_argument('version', metavar='VERSION',
                           help='version (or alias) to retitle')
    retitle_p.add_argument('title', metavar='TITLE',
                           help='the new title to use')

    list_p = subparsers.add_parser(
        'list', description=list_desc, help='list deployed docs on a branch'
    )
    list_p.set_defaults(func=list_versions)
    list_p.add_argument('-j', '--json', action='store_true',
                        help='display the result as JSON')
    add_git_arguments(list_p, commit=False)
    list_p.add_argument('version', metavar='VERSION', nargs='?',
                        help='version (directory) to deploy this build to')

    set_default_p = subparsers.add_parser(
        'set-default', description=set_default_desc,
        help='set the default version for your docs'
    )
    set_default_p.set_defaults(func=set_default)
    set_default_p.add_argument('-T', '--template',
                               help='the template file to use')
    add_git_arguments(set_default_p)
    set_default_p.add_argument('version', metavar='VERSION',
                               help='version to set as default')

    serve_p = subparsers.add_parser(
        'serve', description=serve_desc, help='serve docs locally for testing'
    )
    serve_p.set_defaults(func=serve)
    add_git_arguments(serve_p, commit=False, prefix=False)
    serve_p.add_argument('-a', '--dev-addr', default='localhost:8000',
                         metavar='IP:PORT',
                         help=('IP address and port to serve from ' +
                               '(default: %(default)s)'))

    help_p = subparsers.add_parser(
        'help', help='show this help message and exit', add_help=False
    )
    help_p.set_defaults(func=help)
    help_p.add_argument('subcommand', metavar='CMD', nargs=argparse.REMAINDER,
                        help='subcommand to request help for')

    completion_p = subparsers.add_parser(
        'generate-completion', description=generate_completion_desc,
        help='print shell completion script'
    )
    completion_p.set_defaults(func=generate_completion)
    shell = (os.path.basename(os.environ['SHELL'])
             if 'SHELL' in os.environ else None)
    completion_p.add_argument('-s', '--shell', metavar='SHELL', default=shell,
                              help='shell type (default: %(default)s)')

    args = parser.parse_args()
    try:
        return args.func(parser, args)
    except Exception as e:
        parser.exit(1, 'error: {}\n'.format(str(e)))
