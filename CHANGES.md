# Changes

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
