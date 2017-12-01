# mkultra

[![Travis build status][travis-image]][travis-link]
[![Appveyor build status][appveyor-image]][appveyor-link]
[![Coverage status][codecov-image]][codecov-link]

**mkultra** is a work-in-progress Python utility to easily deploy multiple
versions of your [MkDocs](http://www.mkdocs.org)-powered docs to a Git branch,
suitable for deploying to Github via `gh-pages`.

## Installation

Like most Python projects, mkultra uses [setuptools][setuptools], so you can
install it by downloading the source and running the following (PyPI hosting
coming soon!):

```sh
python setup.py install
```

## Usage

### Building Your Docs

Before your first build, you'll probably want to add the version selector to
your MkDocs config. Simply run the following command in the directory with your
`mkdocs.yml` file to install the extra CSS and JS files to your docs:

```sh
mkultra install-extras
```

mkultra is designed to produce one version of your docs at a time. That way, you
can easily deploy a new version without touching any older versions of your
docs; this can be especially important if your old docs are no longer buildable
with the newest version of MkDocs (or if they weren't built with MkDocs at
all!). To deploy the current version of your docs, simply run:

```sh
mkultra deploy [version]
```

Where `[version]` is the current version of your project, represented however
you like (I recommend using `[major].[minor]` and excluding the patch
number). You can also pass aliases to the `deploy` command to host a
particularly-relevant version of your docs somewhere special (e.g. `latest`):

```sh
mkultra deploy [version] [alias]...
```

Finally, to push your docs to a remote branch, simply add `-p`/`--push` to your
command. (Note: this will likely become the default eventually.)

### Deleting Docs

Sometimes you need to delete an old version of your docs, either because you
made a mistake or you're pruning unsupported versions. You can do this via the
`delete` subcommand:

```sh
mkultra delete [version-or-alias]...
```

If you'd like to completely wipe the contents of your docs branch, just run
`mkultra delete --all`. Like `deploy` above, you can specify `-p`/`--push` to
push this commit as well.

### Listing Docs

If you ever need to see the list of all currently-deployed doc versions, you can
run:

```sh
mkultra list
```

### Setting the Default Version

With all the versions of docs you have, you may want to set a *default* version
so that people going to the root of your site are redirected to the latest
version of the docs:

```sh
mkultra set-default [version-or-alias]
```

Like `deploy` and `delete` above, you can specify `-p`/`--push` to` push this
commit as well.

### More Details

For more details on the available options (e.g. specifying which branch to push
to), consult the `--help` command for mkultra.

## For Theme Authors

If you'd like to provide support for mkultra in your theme, you just need to
fetch `versions.json` and build a version selector. `versions.json` looks like
this:

```js
[
  {"version": "1.0", "title": "1.0.1", "aliases": ["latest"]},
  {"version": "0.9", "title": "0.9", "aliases": []}
]
```

To see an example of how to work with this, check the
[`mkultra/themes/mkdocs`](mkultra/themes/mkdocs) directory.

## License

This project is licensed under the BSD 3-clause [license](LICENSE).

[setuptools]: https://pythonhosted.org/setuptools/
[travis-image]: https://travis-ci.org/jimporter/mkultra.svg?branch=master
[travis-link]: https://travis-ci.org/jimporter/mkultra
[appveyor-image]: https://ci.appveyor.com/api/projects/status/rq4ycpphei6rnfkx/branch/master?svg=true
[appveyor-link]: https://ci.appveyor.com/project/jimporter/mkultra/branch/master
[codecov-image]: https://codecov.io/gh/jimporter/mkultra/branch/master/graph/badge.svg
[codecov-link]: https://codecov.io/gh/jimporter/mkultra
