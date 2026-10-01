# RMRbot
My first coding project for my server Roleplay Meets: Reborn. RMRbot was made to address our moderation needs and is essential to our server.

## API (optional)
RMRbot can run inside a FastAPI app, like Banwatch and Ageverifier. On Windows, `run.bat` installs the requirements and starts it on port 8083. Otherwise set `API=TRUE` in `.env` and start it with uvicorn instead of `python main.py`:

```bash
uvicorn main:app --host 0.0.0.0 --port 8083
```

Routes live in the `api/` package and are registered through `api.__all__`. Protected routes use `api.auth.auth.Auth`, which checks the `X-Auth-Token` header against `API_KEY` in `.env` and the IP whitelist in `project/whitelist.py`.

- `POST /ping`: database status and queue sizes.
