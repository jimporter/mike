import argparse
import json

import git_utils

def make_nojekyll():
    return git_utils.FileInfo(".nojekyll", "")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--message", help="commit message")
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
    parser.add_argument("srcdir")
    parser.add_argument("destdir")
    args = parser.parse_args()

    try:
        dirs = set(json.loads(git_utils.read_file(args.branch, "dirs.json")))
    except:
        dirs = set()
    for i in args.delete:
        dirs.discard(i)
    dirs.add(args.destdir)

    commit = git_utils.Commit(args.branch, args.message)
    commit.delete_files(args.delete)

    for f in git_utils.walk_files(args.srcdir, args.destdir):
        commit.add_file_data(f)
    commit.add_file_data(git_utils.FileInfo(
        "dirs.json", json.dumps(sorted(dirs))
    ))
    commit.finish()

    if args.push:
        git_utils.push_branch(args.remote, args.branch, args.force)
