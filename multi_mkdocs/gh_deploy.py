import argparse
import json
import subprocess

import git_utils

def make_nojekyll():
    return git_utils.FileInfo(".nojekyll", "")


def run_mkdocs():
    subprocess.call(["mkdocs", "build"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--message", default="commit",
                        help="commit message")
    parser.add_argument("-D", "--delete", action="append",
                        help="files to delete")
    parser.add_argument("-r", "--remote", default="origin",
                        help="origin to push to [%default]")
    parser.add_argument("-b", "--branch", default="gh-pages",
                        help="branch to commit to [%default]")
    parser.add_argument("-p", "--push", action="store_true",
                        help="push to {remote}/{branch} after commit")
    parser.add_argument("-f", "--force", action="store_true",
                        help="force push when pushing")
    parser.add_argument("version", nargs="*")
    args = parser.parse_args()

    if not args.version and not args.delete:
        parser.error("must either add or remove a version")

    if args.version:
        run_mkdocs()

    try:
        dirs = set(json.loads(git_utils.read_file(
            args.branch, "versions.json"
        )))
    except:
        dirs = set()
    commit = git_utils.Commit(args.branch, args.message)

    if args.delete:
        commit.delete_files(args.delete)
        for i in args.delete:
            dirs.discard(i)

    commit.delete_files(args.version)
    for i in args.version:
        dirs.add(i)

    for f in git_utils.walk_files("site", args.version):
        commit.add_file_data(f)
    commit.add_file_data(git_utils.FileInfo(
        "versions.json", json.dumps(sorted(dirs))
    ))

    commit.finish()

    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)
