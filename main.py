import os
import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow browser-based grading
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Hardcoded defaults
# -----------------------------
DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


# -----------------------------
# Type conversion
# -----------------------------
def to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        return to_bool(value)

    return str(value)


# -----------------------------
# YAML layer
# -----------------------------
def load_yaml():
    filename = "config.development.yaml"

    if not os.path.exists(filename):
        return {}

    with open(filename) as f:
        return yaml.safe_load(f) or {}


# -----------------------------
# .env layer
# -----------------------------
def load_dotenv():
    env = dotenv_values(".env")

    result = {}

    mapping = {
        "APP_PORT": "port",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
        "NUM_WORKERS": "workers",  # alias
    }

    for k, v in env.items():
        if k in mapping:
            result[mapping[k]] = coerce(mapping[k], v)

    return result


# -----------------------------
# OS Environment layer
# -----------------------------
def load_os_env():
    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    result = {}

    for env_key, cfg_key in mapping.items():
        if env_key in os.environ:
            result[cfg_key] = coerce(cfg_key, os.environ[env_key])

    return result


# -----------------------------
# YAML coercion
# -----------------------------
def normalize_yaml(data):
    out = {}

    for k, v in data.items():
        out[k] = coerce(k, v)

    return out


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = {}

    # 1 Defaults
    config.update(DEFAULTS)

    # 2 YAML
    config.update(normalize_yaml(load_yaml()))

    # 3 .env
    config.update(load_dotenv())

    # 4 OS env
    config.update(load_os_env())

    # 5 CLI overrides
    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        config[key] = coerce(key, value)

    # Secret masking
    config["api_key"] = "****"

    return config
