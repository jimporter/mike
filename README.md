# mike

[![PyPi version][pypi-image]][pypi-link]
[![Travis build status][travis-image]][travis-link]
[![Appveyor build status][appveyor-image]][appveyor-link]
[![Coverage status][codecov-image]][codecov-link]

**mike** is a Python utility to easily deploy multiple versions of your
[MkDocs](http://www.mkdocs.org)-powered docs to a Git branch, suitable for
deploying to Github via `gh-pages`.

## Installation

Like most Python projects, mike uses [setuptools][setuptools], so installation
is what you might expect:

```sh
pip install mike
```

## Usage

### Building Your Docs

Before your first build, you'll probably want to add the version selector to
your MkDocs config. Simply run the following command in the directory with your
`mkdocs.yml` file to install the extra CSS and JS files to your docs:

```sh
mike install-extras
```

mike is designed to produce one version of your docs at a time. That way, you
can easily deploy a new version without touching any older versions of your
docs; this can be especially important if your old docs are no longer buildable
with the newest version of MkDocs (or if they weren't built with MkDocs at
all!). To deploy the current version of your docs, simply run:

```sh
mike deploy [version]
```

Where `[version]` is the current version of your project, represented however
you like (I recommend using `[major].[minor]` and excluding the patch
number). You can also pass aliases to the `deploy` command to host a
particularly-relevant version of your docs somewhere special (e.g. `latest`):

```sh
mike deploy [version] [alias]...
```

If you'd like to specify a title for this version that doesn't match the version
string, you can pass `-t TITLE`/`--title=TITLE` as well. If `version` already
exists, this command will *also* update all of the pre-existing aliases for it.

Finally, to push your docs to a remote branch, simply add `-p`/`--push` to your
command.

### Viewing Your Docs

To test that your docs have been built as expected, you can serve them locally
from a dev server:

```sh
mike serve
```

By default, this serves the docs on `http://localhost:8000`, but you can
change this with `-a`/`--dev-addr`.

### Deleting Docs

Sometimes you need to delete an old version of your docs, either because you
made a mistake or you're pruning unsupported versions. You can do this via the
`delete` subcommand:

```sh
mike delete [version-or-alias]...
```

If `version-or-alias` is a version, this will delete the version and all its
aliases from the branch; if it's an alias, it will only delete that alias.

If you'd like to *completely* wipe the contents of your docs branch, just run
`mike delete --all`. Like `deploy` above, you can specify `-p`/`--push` to
push this commit as well.

### Listing Docs

If you ever need to see the list of all currently-deployed doc versions, you can
run:

```sh
mike list
```

### Setting the Default Version

With all the versions of docs you have, you may want to set a *default* version
so that people going to the root of your site are redirected to the latest
version of the docs:

```sh
mike set-default [version-or-alias]
```

Like `deploy` and `delete` above, you can specify `-p`/`--push` to` push this
commit as well.

### Changing a Version's Title

As you update your docs, you may want to change the title of a particular
version. For example, your `1.0` docs might have the title `1.0.0`, and when you
release a new patch, you want to update the title to `1.0.1`. You can do this
with the `retitle` command:

```sh
mike retitle [version-or-alias] [title]
```

As with other commands that change your docs, you can specify `-p`/`--push` to
push this commit.

### Adding a New Version Alias

Sometimes, you might need to add a new alias for a version without rebuilding
your documentation. You can use the `alias` command for this:

```sh
mike alias [version-or-alias] [alias]...
```

Once again, you can specify `-p`/`--push` to push this commit.

### More Details

For more details on the available options (e.g. specifying which branch to push
to), consult the `--help` command for mike.

## Staying in Sync

mike will do its best to stay in-sync with your remote repository and will
automatically update your local branch to match the remote's if possible (note
that mike *won't* automatically `git fetch` anything). If your local branch has
diverged from your remote, mike will leave it as-is and ask you what to do. To
ignore the remote's state, just pass `--ignore`; to update to the remote's
state, pass `--rebase`.

## For Theme Authors

If you'd like to provide support for mike in your theme, you just need to
fetch `versions.json` and build a version selector. `versions.json` looks like
this:

```js
[
  {"version": "1.0", "title": "1.0.1", "aliases": ["latest"]},
  {"version": "0.9", "title": "0.9", "aliases": []}
]
```

To see an example of how to work with this, check the
[`mike/themes/mkdocs`](mike/themes/mkdocs) directory.

## License

This project is licensed under the [BSD 3-clause license](LICENSE).

[pypi-image]: https://img.shields.io/pypi/v/mike.svg
[pypi-link]: https://pypi.python.org/pypi/mike
[travis-image]: https://travis-ci.org/jimporter/mike.svg?branch=master
[travis-link]: https://travis-ci.org/jimporter/mike
[appveyor-image]: https://ci.appveyor.com/api/projects/status/rj8e3xa1r7nh22u2/branch/master?svg=true
[appveyor-link]: https://ci.appveyor.com/project/jimporter/mike/branch/master
[codecov-image]: https://codecov.io/gh/jimporter/mike/branch/master/graph/badge.svg
[codecov-link]: https://codecov.io/gh/jimporter/mike
[setuptools]: https://pythonhosted.org/setuptools/
