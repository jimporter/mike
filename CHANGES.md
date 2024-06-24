# Changes

## v2.1.2 (2024-06-23)

### Bug fixes
- Remove ambiguity of some Git commands so that file and branch names don't
  collide

---

## v2.1.1 (2024-05-03)

### Bug fixes
- Support using environment variables for `INHERIT` when injecting the `mike`
  plugin into `mkdocs.yml`

---

## v2.1.0 (2024-05-01)

### New features
- When calling `set-default`, you can now pass `--allow-undefined` to set the
  default to a version that doesn't exist yet
- Add global-level `-q` / `--quiet` option to suppress warning messages
- Add support for handling `!relative` in `mkdocs.yml`

### Bug fixes
- When loading an MkDocs config, mike now runs the `startup` and `shutdown`
  events

---

## v2.0.0 (2023-11-02)

### New features

- Add support for applying arbitrary properties to documentation versions
- Add support for hiding specific versions from the selector when using the
  default themes
- Deploy aliases using symbolic links by default; this can be configured via
  `--alias-type` on the command line or `alias_type` in the `mike` MkDocs plugin
- Avoid creating empty commits by default; if you want empty commits, pass
  `--allow-empty`
- Look for both `mkdocs.yml` and `mkdocs.yaml` configuration files
- Support `GIT_COMMITTER_(NAME|EMAIL|DATE)` when generating commits
- Allow specifying `alias_type`, `redirect_template`, and `deploy_prefix` in the
  `mike` MkDocs plugin
- Add a `--debug` flag to help diagnose bugs with mike
- Port number is now optional for `--dev-addr` in `mike serve`, defaulting to
  8000

### Breaking changes

- `--prefix` is now `--deploy-prefix`
- `--no-redirect` is now `--alias-type=copy`
- `--ignore` is now `--ignore-remote-status`
- `-f` / `--force` is no longer supported on subcommands that can push (this
  option was too error-prone, and users who really need to force-push can use
  Git directly)
- `--rebase` is no longer supported (instead of using this, it's better to use
  Git to resolve any conflicts)

### Bug fixes

- Aliases that are "similar" to preexisting versions (e.g. `1.0` and `1.0.0`)
  can now be set properly
- Versions that *don't* start with a digit (or `v` and then a digit) are now
  treated separately from other versions: they're considered development
  versions, and thus newer than "ordinary" versions
- Fix retrieval of Git user name/email when using non-UTF8 encodings
- Fix version selector for `mkdocs` and `readthedocs` themes when
  `use_directory_urls` is false
- When redirecting to another page, include the `?query`
- Ensure that aliases cannot be circularly defined
- Support file names with double-quotes or newlines

---

## v1.1.2 (2021-10-03)

### Bug fixes

- Improve support for shell-completion

---

## v1.1.1 (2021-09-13)

### Bug fixes

- Fix support for Unicode in redirection templates
- Properly decode paths in the development server

---

## v1.1.0 (2021-09-01)

### New features
- Add support for [`!ENV`][mkdocs-env] and [`INHERIT`][mkdocs-inherit] in
  `mkdocs.yml`
- Add `mike generate-completion` to generate shell-completion functions

[mkdocs-env]: https://www.mkdocs.org/user-guide/configuration/#environment-variables
[mkdocs-inherit]: https://www.mkdocs.org/user-guide/configuration/#configuration-inheritance

---

## v1.0.1 (2021-05-31)

### Bug fixes

- When redirecting to another page, include the `#hash`
- Ensure the MkDocs `search` plugin is correctly enabled when building via mike

---

## v1.0.0 (2021-04-10)

### New features
- Remove `mike install-extras` and replace it with an MkDocs plugin; if you
  previously used `install-extras`, be sure to remove the added JS/CSS from your
  docs directory
- When deploying aliases, deploy redirect pages to the real version by default;
  pass `--no-redirect` to deploy copies
- Improve the default redirect template to support redirection when the user has
  disabled JavaScript
- Allow deploying docs to a subdirectory within the target branch via `--prefix`
- Add support for custom templates with `mike set-default`
- Read from `remote_branch` and `remote_name` if set in `mkdocs.yml`
- Allow updating an existing alias with `mike alias -u`

### Breaking changes
- Require Python 3.6+
- Remove support for installing extras for `material` theme since `material`
  now has [built-in support][material-mike] for mike

### Bug fixes
- Canonical URLs in generated documentation now point to the correct location
- `mike alias` now checks for existing aliases to prevent erroneously setting an
  alias for two different versions
- Replace `packaging` dependency with `verspec` for future stability
- Validate version and alias names to ensure they're non-empty and don't
  contain a directory separator

[material-mike]: https://squidfunk.github.io/mkdocs-material/setup/setting-up-versioning/#versioning

---

## v0.5.5 (2020-11-08)

### Bug fixes
- Add support for `mkdocs.yml` files using `!!python` tags

---

## v0.5.3 (2020-06-23)

### Bug fixes
- Fix some cases of `material` theme's version selector failing to load
- Add support for `material` v5.0+

---

## v0.5.2 (2020-05-23)

### New features
- Add support for custom `site_dir` in `mkdocs.yml`

### Bug fixes
- Preserve quotes in `mkdocs.yml` when running `install-extras`

---

## v0.5.1 (2020-03-16)

### Bug fixes
- Fix version selector with `material` theme when on homepage

---

## v0.5.0 (2020-02-26)

### New features
- Add support for the [`material`][material] theme
- Add support for [`mkdocs-bootswatch-classic`][bootswatch-classic] themes

### Breaking changes
- Drop support for Python 2

### Bug fixes
- Update version selector extras for the `mkdocs` theme to work with both MkDocs
  1.0 and 1.1

[material]: https://github.com/squidfunk/mkdocs-material
[bootswatch-classic]: https://github.com/mkdocs/mkdocs-bootswatch-classic

---

## v0.4.2 (2019-12-15)

### Bug fixes
- Fix using `mike` from subdirectories in some more cases

---

## v0.4.1 (2019-12-14)

### Bug fixes
- Fix using `mike` commands from non-root directories of your project

---

## v0.4.0 (2019-10-31)

### New features
- Add support for listing doc version in JSON format via `-j`/`--json`
- Allow changing where aliases point to when deploying, using the
  `-u`/`--update-aliases` option

---

## v0.3.5 (2018-11-05)

### Bug fixes
- Selectively require `enum34` in a Wheel-compatible way

---

## v0.3.4 (2018-09-08)

### Bug fixes
- Include `templates/index.html` in source dists (fixes `mike set-default`)

---

## v0.3.3 (2018-09-01)

### Bug fixes
- Add support for Python 3.7 as well as newer versions of `ruamel.yaml`

---

## v0.3.2 (2018-04-26)

### Bug fixes
- Support defining theme in `mkdocs.yml` as a mapping instead of just a string

---

## v0.3.1 (2018-04-14)

### Bug fixes
- Fix version selection on real Github pages
- Allow re-specifying aliases if they're already set for a version

---

## v0.3.0 (2018-04-14)

### New features
- Add an `alias` command to copy an existing set of docs to a new alias

### Breaking changes
- Change the name of the `rename` command to `retitle`

### Bug fixes
- Fix handling of remotes so that local changes aren't wiped out
- Rework aliasing to be persistent across deployments

---

## v0.2.0 (2018-04-08)

### New features
- Add support for locally-serving documentation for testing purposes
