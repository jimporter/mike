import argparse
import json
import subprocess

import git_utils

versions_file = 'versions.json'
mkdocs_site_dir = 'site'


def make_nojekyll():
    return git_utils.FileInfo('.nojekyll', '')


def run_mkdocs():
    return subprocess.call(['mkdocs', 'build'])


def get_versions(branch, filename=versions_file):
    try:
        data = git_utils.read_file(branch, filename)
        return set(json.loads(data))
    except:
        return set()


def make_versions_json(versions, filename=versions_file):
    return git_utils.FileInfo(filename, json.dumps(sorted(versions)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--message', default='commit',
                        help='commit message')
    parser.add_argument('-D', '--delete', action='append', default=[],
                        help='files to delete')
    parser.add_argument('-r', '--remote', default='origin',
                        help='origin to push to [%default]')
    parser.add_argument('-b', '--branch', default='gh-pages',
                        help='branch to commit to [%default]')
    parser.add_argument('-p', '--push', action='store_true',
                        help='push to {remote}/{branch} after commit')
    parser.add_argument('-f', '--force', action='store_true',
                        help='force push when pushing')
    parser.add_argument('version', nargs='*')
    args = parser.parse_args()

    if not args.version and not args.delete:
        parser.error('must either add or remove a version')

    if args.version:
        run_mkdocs()

    all_versions = get_versions(args.branch)
    all_versions.difference_update(args.delete)
    all_versions.update(args.version)

    commit = git_utils.Commit(args.branch, args.message)
    commit.delete_files(args.delete)
    commit.delete_files(args.version)

    for f in git_utils.walk_files(mkdocs_site_dir, args.version):
        commit.add_file_data(f)
    commit.add_file_data(make_versions(all_versions))
    commit.add_file_data(make_nojekyll())

    commit.finish()

    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)
