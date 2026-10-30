# IGL Memory Server

The server is distributed as a compiled artifact. This
README explains how to start it, configure it, and verify
that it works.

## What the server is

The server is the authoritative memory engine. It is the
single source of truth for memory semantics. The SDK is a
thin client that talks to it over HTTP.

## What you need

- Python 3.10+ (for the packaged build, no additional
  Python packages are required)
- A writable directory for the SQLite database

## Unpack the server

The server is distributed as `igl-memory-server.zip`. Unpack
it to a directory of your choice:

    unzip igl-memory-server.zip -d igl-memory-server
    cd igl-memory-server

You will find a `run.sh` script (Linux/macOS) and a
`run.bat` script (Windows). Both start the server on
port 8000.

## Configure the server

The server reads two environment variables:

    IGL_ADMIN_KEY       — admin credential for token issuance
                          (required to issue user tokens)
    IGL_DB_PATH         — path to the SQLite database file
                          (optional, defaults to ./data/igl.sqlite3)
    AITUNNEL_API_KEY    — only needed if you plan to use
                          use_llm=true during compilation
                          (optional)

Set the admin key before starting:

    export IGL_ADMIN_KEY="<choose a strong local key>"

The admin key is a local secret. Do not share it. Do not
commit it. Use a different value for each deployment.

## Start the server

    ./run.sh        (Linux / macOS)
    run.bat         (Windows)

The server listens on `http://127.0.0.1:8000`.

On first start, it creates the database file at
`$IGL_DB_PATH` (or `./data/igl.sqlite3` if unset).

## Verify the server is running

    curl http://127.0.0.1:8000/health

Expected response:

    {"status": "ok", "architecture": "M -> D -> Trust -> Gate -> K"}

## Issue your first user token

The SDK needs a bearer token. Tokens are issued by an admin
endpoint, using the admin key:

    curl -X POST http://127.0.0.1:8000/auth/token \
         -H "Authorization: Bearer $IGL_ADMIN_KEY" \
         -H "Content-Type: application/json" \
         -d '{"user_id": "demo-user-001"}'

The response contains a `token` field. Export it for the
SDK:

    export IGL_USER_TOKEN="<token from the response>"

## Stop the server

Press Ctrl+C in the terminal where the server is running.

The SQLite database persists across restarts. To start
with a clean database, stop the server and delete the
database file.

## What the server does not expose

- No admin UI.
- No telemetry.
- No outbound network calls unless you set
  `AITUNNEL_API_KEY` and pass `use_llm=true`.

The server runs locally. Your memory data stays on your
machine.

## Troubleshooting

**`IGL_ADMIN_KEY is not set`** — the environment variable
was not exported in the shell where the server runs. Use
the same terminal session for the export and the start
command.

**`Address already in use`** — another process is using
port 8000. Stop it, or change the port in `run.sh` /
`run.bat`.

**`/auth/token` returns 401** — the admin key sent in the
`Authorization` header does not match `IGL_ADMIN_KEY` in
the server environment. Restart both with the same value.