# mike

[![PyPi version][pypi-image]][pypi-link]
[![Build status][ci-image]][ci-link]
[![Coverage status][codecov-image]][codecov-link]

**mike** is a Python utility that makes it easy to deploy multiple versions of
your [MkDocs](http://www.mkdocs.org)-powered docs to a Git branch, suitable for
hosting on Github via `gh-pages`. To see an example of this in action, take a
look at the documentation for [bfg9000][bfg9000].

## Why Use mike?

mike is built around the idea that once you've generated your docs for a
particular version, you should never need to touch that version again. This
means you never have to worry about breaking changes in MkDocs, since your old
docs (built with an old version of MkDocs) are already generated and sitting in
your `gh-pages` branch.

While mike is flexible, it's optimized around putting your docs in a
`<major>.<minor>` directory, with optional aliases (e.g. `latest` or `dev`) to
particularly notable versions. This makes it easy to make permalinks to whatever
version of the documentation you want to direct people to.

## How It Works

mike works by creating a new Git commit on your `gh-pages` branch every time you
deploy a new version of your docs using `mike deploy` (or other mike subcommands
that change your `gh-pages` branch). When deploying a particular version,
previously-deployed docs for that version are erased and overwritten, but docs
for other versions remain untouched.

## Installation

Like most Python projects, mike uses [setuptools][setuptools], so installation
is what you might expect:

```sh
pip install mike
```

Once you've installed mike, you might also want to set up shell-completion for
it. If you have [shtab][shtab] installed, you can do this with
`mike generate-completion`, which will print the shell-completion code for your
shell. For more details on how to set this up, consult shtab's
[documentation][shtab-setup].

## Usage

### Before Using Mike

Before using mike for the first time, you may want to use [`mike delete
--all`](#deleting-docs) to delete any old documentation on your `gh-pages`
branch before building your new versioned docs. (If you prefer, you can also
manually move your old documentation to a subdirectory of your `gh-pages` branch
so that it's still accessible.)

### Configuration

To help integrate into the MkDocs build process, mike uses an MkDocs plugin.
This plugin is added by default when building your documentation with mike, but
by adding it explicitly to your `mkdocs.yml` file, you can configure how the
plugin works. The plugin adds a version selector to supported themes as well as
updating the `site_url` (if you set it) to point to the version of the docs that
are being built:

```yaml
plugins:
  - mike:
      # These fields are all optional; the defaults are as below...
      alias_type: symlink
      redirect_template: null
      deploy_prefix: ''
      canonical_version: null
      version_selector: true
      css_dir: css
      javascript_dir: js
```

* `alias_type`: The method to create aliases; one of:
  * `symlink`: Create a symbolic link from the alias to the base directory of
    the documentation
  * `redirect`: Create an HTML redirect for each page of the documentation
  * `copy`: Copy all the files of the documentation to the alias's path
* `redirect_template`: The template file to use when creating HTML redirects; if
  `null`, use the default template
* `deploy_prefix`: The root directory to put the generated docs in; this can be
  useful if you'd like to have other pages at the root of your site, or to host
  multiple, independently-versioned sets of docs side by side
* `canonical_version`: The "canonical" version to use for the documentation,
  useful for telling search engines what pages to prefer (e.g. `latest` if
  you've defined that as an alias that always points to the latest release); if
  `null`, mike will use the version specified via `mike deploy`
* `version_selector`: True if the version selector should be shown on pages;
  false otherwise
* `css_dir`: The directory to place the version selector's CSS
* `javascript_dir`: The directory to place the version selector's Javascript

### Building Your Docs

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

If `[version]` already exists, this command will *also* update all of the
pre-existing aliases for it. Normally, if an alias specified on the command line
is already associated with another version, this will return an error. If you
*do* want to move an alias from another version to this version (e.g. when
releasing a new version and updating the `latest` alias to point to this new
version) or the new version was previously an alias (e.g. when you used the
future release name as an alias for development builds), you can pass
`-u`/`--update-aliases` to allow this.

By default, each alias creates a symbolic link to the base directory of the real
version of the docs; to create a copy of the docs for each alias, you can pass
`--alias-type=copy`, or to use a simple HTML redirect for each page, you can
pass `--alias-type=redirect`. If you're using redirects, you can customize the
redirect template with `-T`/`--template`; this takes a path to a [Jinja][jinja]
template that accepts an `{{href}}` variable.

If you'd like to specify a title for this version that doesn't match the version
string, you can pass `-t TITLE`/`--title=TITLE` as well.

In addition, you can specify where to deploy your docs via `-b`/`--branch`,
`-r`/`--remote`, and `--deploy-prefix`, specifying the branch, remote, and
directory prefix within the branch, respectively. Finally, to push your docs to
a remote branch, simply add `-p`/`--push` to your command.

You can also specify many of these options via your `mkdocs.yml` configuration
as shown above. For example, `--alias-type` can also be specified via
`plugins.mike.alias_type`. (For `--branch` and `--remote`, you can use the
built-in MkDocs fields `remote_branch` and `remote_name`.)

### Viewing Your Docs

To test that your docs have been built as expected, you can serve them locally
from a dev server:

```sh
mike serve
```

By default, this serves the docs on `http://localhost:8000`, but you can
change this with `-a`/`--dev-addr`. Remember though, *this is for testing only*.
To host your docs for real, you should use a real web server.

### Deleting Docs

Sometimes you need to delete an old version of your docs, either because you
made a mistake or you're pruning unsupported versions. You can do this via the
`delete` subcommand:

```sh
mike delete [identifier]...
```

If `identifier` is a version, this will delete the version and all its aliases
from the branch; if it's an alias, it will only delete that alias.

If you'd like to *completely* wipe the contents of your docs branch, just run
`mike delete --all`. Like `deploy` above, you can specify `--branch`, `--push`,
etc to control how the commit is handled.

### Listing Docs

If you ever need to see the list of all currently-deployed doc versions, you can
run:

```sh
mike list
```

To list the info for a particular version, you can just pass the version name or
an alias to that version:

```sh
mike list [identifier]
```

Sometimes, you need this information to be consumed by another tool. In that
case, pass `-j`/`--json` to return the list of doc versions as JSON.

### Setting the Default Version

With all the versions of docs you have, you may want to set a *default* version
so that people going to the root of your site are redirected to the latest
version of the docs:

```sh
mike set-default [identifier]
```

If you want to use a different template from the default, you can pass
`-T`/`--template`; this takes a path to a [Jinja][jinja] template that accepts
an `{{href}}` variable.

Like `deploy` and `delete` above, you can specify `--branch`, `--push`,
etc to control how the commit is handled.

### Changing a Version's Title

As you update your docs, you may want to change the title of a particular
version. For example, your `1.0` docs might have the title `1.0.0`, and when you
release a new patch, you want to update the title to `1.0.1`. You can do this
with the `retitle` command:

```sh
mike retitle [identifier] [title]
```

As with other commands that change your docs, you can specify `--branch`,
`--push`, etc to control how the commit is handled.

### Adding a New Version Alias

Sometimes, you might need to add a new alias for a version without rebuilding
your documentation. You can use the `alias` command for this:

```sh
mike alias [identifier] [alias]...
```

As with `deploy`, you can pass `-u`/`--update-aliases` to change where an
existing alias points to.

Once again, you can specify `--branch`, `--push`, etc to control how the commit
is handled.

### More Details

For more details on the available options, consult the `--help` command for
mike.

## Version Ordering

There are lots of versioning schemes out there, but mike tries its best to order
your versions in a reasonable manner. Version identifiers that "look like"
versions (e.g. `1.2.3`, `1.0b1`, `v1.0`) are treated as ordinary versions,
whereas other identifiers, like `devel`, are treated as development versions,
and placed *above* ordinary versions.

The above scheme should get things right most of the time, but you can always
post-process your `versions.json` file to manipulate the ordering to suit your
needs.

## Staying in Sync

mike will do its best to stay in-sync with your remote repository and will
automatically update your local branch to match the remote's if possible (note
that mike *won't* automatically `git fetch` anything). If your local branch has
diverged from your remote, mike will leave it as-is and ask you what to do. To
ignore the remote's state, just pass `--ignore`; to update to the remote's
state, pass `--rebase`.

## `CNAME` (and Other Special Files)

Some special files that you'd like to deploy along with your documentation (such
as `CNAME`) aren't related to a particular version of the docs, and instead need
to go in the root directory of your site. There's no special handling for this
in mike, but since your built docs live on a Git branch, it's still easy to
manage: check out your `gh-pages` branch (or wherever your built docs
live), and commit the necessary files to the root directory.

## Deploying via CI

Since mike just generates commits to an ordinary Git branch, it should work
smoothly with your favorite CI system. However, you should keep in mind that
some CI systems make shallow clones of your repository, meaning that the CI job
won't have a local instance of your documentation branch to commit to. This will
naturally cause issues when trying to push the commit. This is easy to resolve
though; just manually fetch your `gh-pages` branch (or whichever you deploy to)
before running mike:

```sh
git fetch origin gh-pages --depth=1
```

You may also need to [configure a Git user][gh-action-commit] so that mike can
make commits:

```sh
git config user.name ci-bot
git config user.email ci-bot@example.com
```

Alternately, you can set the environment variables `GIT_COMMITTER_NAME` and
`GIT_COMMITTER_EMAIL` (as well as `GIT_COMMITTER_DATE` if you like):

```sh
GIT_COMMITTER_NAME=ci-bot GIT_COMMITTER_EMAIL=ci-bot@example.com \
mike deploy 1.0
```

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

If you're creating a third-party extension to an existing theme, you add a
setuptools entry point for `mike.themes` pointing to a Python submodule that
contains `css/` and `js/` subdirectories containing the extra code to be
installed into the user's documentation. This will then automatically be
included via the `mike` plugin in the user's `mkdocs.yml` file.

To see some examples of how to work with this, check the
[`mike/themes/mkdocs`](mike/themes/mkdocs) directory.

## License

This project is licensed under the [BSD 3-clause license](LICENSE).

[pypi-image]: https://img.shields.io/pypi/v/mike.svg
[pypi-link]: https://pypi.python.org/pypi/mike
[ci-image]: https://github.com/jimporter/mike/workflows/build/badge.svg
[ci-link]: https://github.com/jimporter/mike/actions?query=branch%3Amaster+workflow%3Abuild
[codecov-image]: https://codecov.io/gh/jimporter/mike/branch/master/graph/badge.svg
[codecov-link]: https://codecov.io/gh/jimporter/mike

[bfg9000]: https://jimporter.github.io/bfg9000
[setuptools]: https://pythonhosted.org/setuptools/
[shtab]: https://github.com/iterative/shtab
[shtab-setup]: https://github.com/iterative/shtab#cli-usage
[jinja]: https://jinja.palletsprojects.com/
[gh-action-commit]: https://github.com/actions/checkout#push-a-commit-using-the-built-in-token
