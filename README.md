# IGL Memory Community

[![Latest release](https://img.shields.io/github/v/release/IGLANGUAGE/igl-memory-community)](https://github.com/IGLANGUAGE/igl-memory-community/releases/latest)

Correctable memory for AI agents.

## What this is

When a user corrects or forbids something, most AI agents
eventually use it again. IGL Memory fixes that at the
architecture level: corrections, rejections, and forgetting
are first-class operations, verified by tests, not hoped
for from the LLM.

This repository contains the Community edition of IGL
Memory: a locally installable server, a Python SDK, and
examples.

## What this is not

- Not a wrapper around an LLM provider.
- Not a vector database.
- Not a replacement for your agent framework.
- Not open source. The SDK is provided as source so you
  can inspect what the client sends. The server is
  provided as a self-contained package.

## Quick start

### 1. Install the SDK
```
pip install -e ./sdk/python
```

### 2. Get and start the server

Option A — if you cloned this repository, the server zip is
in `server/`:
```
cd server
unzip igl-memory-server.zip
cd igl-memory-server
pip install -r requirements.txt
./run.sh                   # on Linux / macOS
run.bat                    # on Windows
```

Option B — if you downloaded the release, unzip it in any
directory:
```
unzip igl-memory-server.zip
cd igl-memory-server
pip install -r requirements.txt
./run.sh                   # on Linux / macOS
run.bat                    # on Windows
```

The server listens on `http://127.0.0.1:8000`. See
`server/README_SERVER.md` for configuration and details.

### 3. Issue a demo user token

```
export IGL_ADMIN_KEY="<choose a local admin key>"
python -c "
import os, httpx
r = httpx.post('http://127.0.0.1:8000/auth/token',
json={'user_id': 'demo-user-001'},
headers={'Authorization': 'Bearer ' + os.environ['IGL_ADMIN_KEY']})
print(r.json()['token'])
"
```
Copy the printed token. Export it for the SDK:
```
export IGL_USER_TOKEN="<token from the previous step>"
```

### 4. Run an example

```
python examples/agent_example.py
python examples/creative_example.py
python examples/memory_lifecycle_example.py

```

### 5. Verify the behavioral guarantees (optional)

```  
python verify/smoke_sdk_live.py
```

## What is in this repository

- `README.md` — this file
- `LICENSE.md` — Community license
- `server/` — IGL Memory server package
- `sdk/python/` — public Python SDK
- `examples/` — three worked examples
- `verify/` — black-box verification script
- `docs/PUBLIC_CONTRACT.md` — behavioral guarantees

## What IGL Memory guarantees

Four behavioral guarantees, verified by tests, not
promises:

1. **Correction** — after a correction, the previous value
   is no longer used in the current context.
2. **Forget** — forgotten information is not returned
   after a supported replay.
3. **Reject** — a rejected interpretation does not appear
   in Gate accepted output.
4. **Ownership** — a user cannot access another user's
   memory, even with known IDs.

See `docs/PUBLIC_CONTRACT.md` for details.

## License

Free for personal and research use. Commercial use
requires a separate written license. See `LICENSE.md`.

## Contact

Igor Gnezdilov — igor.gnezdilov1@gmail.com