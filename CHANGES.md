# Changes

## v0.5.0 (in progress)

- Drop support for Python 2
- Update version selector extras for the `mkdocs` theme to work with both MkDocs
  1.0 and 1.1

---

## v0.4.2 (2018-12-15)

- Fix using `mike` from subdirectories in some more cases

---

## v0.4.1 (2018-12-14)

- Fix using `mike` commands from non-root directories of your project

---

## v0.4.0 (2019-10-31)

- Add support for listing doc version in JSON format via `-j`/`--json`
- Allow changing where aliases point to when deploying, using the
  `-u`/`--update-aliases` option

---

## v0.3.5 (2018-11-05)

- Selectively require `enum34` in a Wheel-compatible way

---

## v0.3.4 (2018-09-08)

- Include `templates/index.html` in source dists (fixes `mike set-default`)

---

## v0.3.3 (2018-09-01)

- Add support for Python 3.7 as well as newer versions of `ruamel.yaml`

---

## v0.3.2 (2018-04-26)

- Support defining theme in `mkdocs.yml` as a mapping instead of just a string

---

## v0.3.1 (2018-04-14)

- Fix version selection on real Github pages
- Allow re-specifying aliases if they're already set for a version

---

## v0.3.0 (2018-04-14)

- Fix handling of remotes so that local changes aren't wiped out
- Rework aliasing to be persistent across deployments
- Add an `alias` command to copy an existing set of docs to a new alias
- Change the name of the `rename` command to `retitle`

---

## v0.2.0 (2018-04-08)

- Add support for locally-serving documentation for testing purposes
