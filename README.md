# devops-dockerignore-lint

Check a Docker build context before it ships. A missing or leaky
`.dockerignore` is how `.env` files, `.git` history and private keys end up
in an image layer, and how a 2 MB app turns into a 600 MB build context.

This is a small stdlib-only Python script. It reads the `.dockerignore`,
applies Docker's matching rules (root-anchored patterns, `**`, last match
wins, `!` re-includes) to a list of risky probe paths, and reports the ones
that would still be sent to the daemon.

## Usage

```sh
python3 dockerignorelint.py path/to/context
python3 dockerignorelint.py path/to/context --dockerfile Dockerfile.prod
```

Exit code is `0` when there are no errors, `1` when there is at least one
error, `2` when the Dockerfile cannot be found. Warnings do not fail the run.

```sh
$ python3 dockerignorelint.py examples/leaky
examples/leaky: error DI002 .git/config (git history) is sent to the daemon
examples/leaky: error DI002 .env (environment file) is sent to the daemon
...
```

## Rules

| Code  | Severity | Meaning |
| ----- | -------- | ------- |
| DI001 | error / warning | No `.dockerignore`. An error when a `COPY`/`ADD` takes the whole context (`.`), a warning otherwise. |
| DI002 | error | A credential or history probe (`.git`, `.env`, `*.pem`, `id_rsa`, terraform state, `.aws`) is not ignored. |
| DI003 | warning | A bulky probe (`node_modules`, `__pycache__`, `.venv`, `*.log`) is not ignored. |

The probe lists are the `SECRET_PROBES` and `BLOAT_PROBES` constants in
`dockerignorelint.py`.

## Caveats

- Patterns are anchored at the context root, exactly as Docker does it:
  `.env` does not ignore `app/.env`. Use `**/.env` for that. The probes only
  check root-level paths.
- `COPY --from=<stage>` is not treated as a whole-context copy.
- Only the Dockerfile's `COPY`/`ADD` are inspected, not compose `build:`
  settings or `docker build -f` flags.

## Validate

```sh
make validate
```

Runs the unit tests, requires `examples/good` to pass and `examples/leaky`
to fail.
