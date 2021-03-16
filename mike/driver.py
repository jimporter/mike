import argparse
import sys

from . import commands
from . import git_utils
from . import mkdocs_utils
from .app_version import version as app_version


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
        cfg = mkdocs_utils.ConfigData(args.config_file)
        if args.branch is None:
            args.branch = cfg.remote_branch
        if args.remote is None:
            args.remote = cfg.remote_name
        return cfg
    except OSError:
        if strict:
            raise RuntimeError('{!r} not found'.format(args.config_file))
        if args.branch is None or args.remote is None:
            raise RuntimeError((
                '{!r} not found; pass --config-file or set ' +
                '--remote/--branch explicitly'
            ).format(args.config_file))


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


def deploy(args):
    cfg = load_mkdocs_config(args, strict=True)
    check_remote_status(args, strict=True)
    with mkdocs_utils.inject_plugin(args.config_file) as config_file:
        mkdocs_utils.build(config_file, args.version)
    commands.deploy(cfg.site_dir, args.version, args.title, args.alias,
                    args.update_aliases, args.redirect, args.template,
                    branch=args.branch, message=args.message,
                    prefix=args.prefix)
    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)


def delete(args):
    load_mkdocs_config(args)
    check_remote_status(args, strict=True)
    commands.delete(args.version, args.all, branch=args.branch,
                    message=args.message, prefix=args.prefix)
    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)


def alias(args):
    load_mkdocs_config(args)
    check_remote_status(args, strict=True)
    commands.alias(args.version, args.alias, args.redirect, args.template,
                   branch=args.branch, message=args.message,
                   prefix=args.prefix)
    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)


def retitle(args):
    load_mkdocs_config(args)
    check_remote_status(args, strict=True)
    commands.retitle(args.version, args.title, branch=args.branch,
                     message=args.message, prefix=args.prefix)
    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)


def list_versions(args):
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


def set_default(args):
    load_mkdocs_config(args)
    check_remote_status(args, strict=True)
    commands.set_default(args.version, args.template, branch=args.branch,
                         message=args.message, prefix=args.prefix)
    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)


def serve(args):
    load_mkdocs_config(args)
    check_remote_status(args)
    commands.serve(args.dev_addr, branch=args.branch)


def main():
    parser = argparse.ArgumentParser(prog='mike')
    subparsers = parser.add_subparsers(metavar='COMMAND')
    subparsers.required = True

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + app_version)

    deploy_p = subparsers.add_parser(
        'deploy', help='build docs and deploy them to a branch'
    )
    deploy_p.set_defaults(func=deploy)
    deploy_p.add_argument('-t', '--title',
                          help='short descriptive title for this version')
    deploy_p.add_argument('-u', '--update-aliases', action='store_true',
                          help='allow aliases pointing to other versions')
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
        'delete', help='delete docs from a branch'
    )
    delete_p.set_defaults(func=delete)
    delete_p.add_argument('--all', action='store_true',
                          help='delete everything')
    add_git_arguments(delete_p)
    delete_p.add_argument('version', nargs='*', metavar='VERSION',
                          help='version (directory) to delete')

    alias_p = subparsers.add_parser(
        'alias', help='alias docs from a branch'
    )
    alias_p.set_defaults(func=alias)
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
        'retitle', help='change the title of a version'
    )
    retitle_p.set_defaults(func=retitle)
    add_git_arguments(retitle_p)
    retitle_p.add_argument('version', metavar='VERSION',
                           help='version (or alias) to retitle')
    retitle_p.add_argument('title', metavar='TITLE',
                           help='the new title to use')

    list_p = subparsers.add_parser(
        'list', help='list deployed docs on a branch'
    )
    list_p.set_defaults(func=list_versions)
    list_p.add_argument('-j', '--json', action='store_true',
                        help='display the result as JSON')
    add_git_arguments(list_p, commit=False)
    list_p.add_argument('version', metavar='VERSION', nargs='?',
                        help='version (directory) to deploy this build to')

    set_default_p = subparsers.add_parser(
        'set-default', help='set the default version for your docs'
    )
    set_default_p.set_defaults(func=set_default)
    set_default_p.add_argument('-T', '--template',
                               help='the template file to use')
    add_git_arguments(set_default_p)
    set_default_p.add_argument('version', metavar='VERSION',
                               help='version to set as default')

    serve_p = subparsers.add_parser(
        'serve', help='serve docs locally for testing'
    )
    serve_p.set_defaults(func=serve)
    add_git_arguments(serve_p, commit=False, prefix=False)
    serve_p.add_argument('-a', '--dev-addr', default='localhost:8000',
                         metavar='IP:PORT',
                         help=('IP address and port to serve from ' +
                               '(default: %(default)s)'))

    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as e:
        parser.exit(1, '{prog}: {error}\n'.format(
            prog=parser.prog, error=str(e)
        ))
