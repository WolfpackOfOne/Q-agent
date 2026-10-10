---
path: "infrastructure/pipelines/wrds/src/wrds_lean/connection.py"
hub: "wrds"
lines: 220
tags:
  - "code/python"
  - "pipelines/wrds"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py"
---
# connection.py

`infrastructure/pipelines/wrds/src/wrds_lean/connection.py` · hub [[Hubs/Pipelines/wrds|wrds]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py)

## Purpose

WRDS database connection helper using named profiles, env vars, or ~/.pgpass.

## Dependencies


**Imports (external):** [[Indexes/External packages#json|json]], [[Indexes/External packages#os|os]], [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#wrds|wrds]]

**Imported by:** [[Code/infrastructure/pipelines/wrds/scripts/compare_tables.py|compare_tables.py]], [[Code/infrastructure/pipelines/wrds/scripts/probe_fx_access.py|probe_fx_access.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_13f_pipeline.py|run_13f_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_broad_fscore_pipeline.py|run_broad_fscore_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_broad_ibes_pipeline.py|run_broad_ibes_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_broad_quarterly_pipeline.py|run_broad_quarterly_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_broad_sector_pipeline.py|run_broad_sector_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_credit_pipeline.py|run_credit_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_etf_pipeline.py|run_etf_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_finratio_pipeline.py|run_finratio_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_fundamentals_pipeline.py|run_fundamentals_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_ibes_pipeline.py|run_ibes_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_macro_pipeline.py|run_macro_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_pipeline.py|run_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_quarterly_fundamentals_pipeline.py|run_quarterly_fundamentals_pipeline.py]], [[Code/infrastructure/pipelines/wrds/scripts/run_sector_pipeline.py|run_sector_pipeline.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/credit.py|credit.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/etf_constituents.py|etf_constituents.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/extract.py|extract.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/fundamentals.py|fundamentals.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ibes.py|ibes.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/macro.py|macro.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ownership.py|ownership.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/quarterly_fundamentals.py|quarterly_fundamentals.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/ratios.py|ratios.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/sectors.py|sectors.py]], [[Code/infrastructure/pipelines/wrds/src/wrds_lean/symbols.py|symbols.py]]

## Constants

| Name | Value | Line |
|---|---|---|
| `DEFAULT_WRDS_HOSTNAME` | `'wrds-pgdata.wharton.upenn.edu'` | [9](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py#L9) |
| `DEFAULT_WRDS_PORT` | `'9737'` | [10](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py#L10) |
| `DEFAULT_WRDS_DBNAME` | `'wrds'` | [11](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py#L11) |
| `DEFAULT_WRDS_USERNAME` | `None` | [12](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py#L12) |
| `DEFAULT_PROFILES_FILE` | `Path(__file__).resolve().parents[2] / '.wrds_profiles.json'` | [13](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py#L13) |

## Functions

### `_normalize_profile_name()`

```python
def _normalize_profile_name(profile_name)
```
[line 19](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py#L19)

### `set_connection_profile()`

```python
def set_connection_profile(profile_name)
```
[line 27](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py#L27)

Set the active named WRDS profile for future connections.

### `_matches_pgpass_field()`

```python
def _matches_pgpass_field(value, candidate)
```
[line 44](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py#L44)

### `_load_pgpass_credentials()`

```python
def _load_pgpass_credentials(hostname, port, dbname, username)
```
[line 48](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py#L48)

Return a password from ~/.pgpass when an entry matches the WRDS connection.

### `_load_profiles_config()`

```python
def _load_profiles_config()
```
[line 78](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py#L78)

### `_load_named_profile()`

```python
def _load_named_profile(profile_name, config, profiles_path)
```
[line 94](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py#L94)

### `_has_explicit_connection_identity()`

```python
def _has_explicit_connection_identity()
```
[line 117](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py#L117)

### `_resolve_connection_settings()`

```python
def _resolve_connection_settings()
```
[line 131](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py#L131)

### `get_connection()`

```python
def get_connection()
```
[line 195](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py#L195)

Get or create a singleton WRDS connection.

### `close_connection()`

```python
def close_connection()
```
[line 214](https://github.com/WolfpackOfOne/Q-agent/blob/main/infrastructure/pipelines/wrds/src/wrds_lean/connection.py#L214)

Close the singleton connection if open.

## Source

> [!example]- infrastructure/pipelines/wrds/src/wrds_lean/connection.py (220 lines)
> ```python
> """WRDS database connection helper using named profiles, env vars, or ~/.pgpass."""
>
> import json
> import os
> from pathlib import Path
>
> import wrds
>
> DEFAULT_WRDS_HOSTNAME = 'wrds-pgdata.wharton.upenn.edu'
> DEFAULT_WRDS_PORT = '9737'
> DEFAULT_WRDS_DBNAME = 'wrds'
> DEFAULT_WRDS_USERNAME = None
> DEFAULT_PROFILES_FILE = Path(__file__).resolve().parents[2] / '.wrds_profiles.json'
>
> _connection = None
> _connection_profile = None
>
>
> def _normalize_profile_name(profile_name):
>     if profile_name is None:
>         return None
>
>     profile_name = str(profile_name).strip()
>     return profile_name or None
>
>
> def set_connection_profile(profile_name):
>     """Set the active named WRDS profile for future connections."""
>     global _connection
>     global _connection_profile
>
>     normalized = _normalize_profile_name(profile_name)
>     if normalized == _connection_profile:
>         return normalized
>
>     if _connection is not None:
>         _connection.close()
>         _connection = None
>
>     _connection_profile = normalized
>     return normalized
>
>
> def _matches_pgpass_field(value, candidate):
>     return value == '*' or value == str(candidate)
>
>
> def _load_pgpass_credentials(hostname, port, dbname, username):
>     """Return a password from ~/.pgpass when an entry matches the WRDS connection."""
>     pgpass_path = Path(os.environ.get('PGPASSFILE', Path.home() / '.pgpass'))
>     if not pgpass_path.exists():
>         return None
>
>     for raw_line in pgpass_path.read_text().splitlines():
>         line = raw_line.strip()
>         if not line or line.startswith('#'):
>             continue
>
>         parts = line.split(':', 4)
>         if len(parts) != 5:
>             continue
>
>         file_host, file_port, file_db, file_user, file_password = parts
>         if not _matches_pgpass_field(file_host, hostname):
>             continue
>         if not _matches_pgpass_field(file_port, port):
>             continue
>         if not _matches_pgpass_field(file_db, dbname):
>             continue
>         if not _matches_pgpass_field(file_user, username):
>             continue
>
>         return file_password
>
>     return None
>
>
> def _load_profiles_config():
>     profiles_path = Path(os.environ.get('WRDS_PROFILES_FILE', DEFAULT_PROFILES_FILE))
>     if not profiles_path.exists():
>         return {}, profiles_path
>
>     try:
>         config = json.loads(profiles_path.read_text())
>     except json.JSONDecodeError as exc:
>         raise ValueError(f"Invalid WRDS profiles JSON in {profiles_path}: {exc}") from exc
>
>     if not isinstance(config, dict):
>         raise ValueError(f"WRDS profiles file must contain a JSON object: {profiles_path}")
>
>     return config, profiles_path
>
>
> def _load_named_profile(profile_name, config, profiles_path):
>     profiles = config.get('profiles', {})
>     if not isinstance(profiles, dict):
>         raise ValueError(
>             f"WRDS profiles file has invalid 'profiles' mapping: {profiles_path}"
>         )
>
>     if profile_name not in profiles:
>         available_profiles = ', '.join(sorted(profiles)) if profiles else 'none'
>         raise ValueError(
>             f"WRDS profile '{profile_name}' not found in {profiles_path}. "
>             f"Available profiles: {available_profiles}"
>         )
>
>     profile_settings = profiles[profile_name]
>     if not isinstance(profile_settings, dict):
>         raise ValueError(
>             f"WRDS profile '{profile_name}' must map to an object in {profiles_path}"
>         )
>
>     return profile_settings
>
>
> def _has_explicit_connection_identity():
>     identity_keys = (
>         'WRDS_HOSTNAME',
>         'WRDS_PORT',
>         'WRDS_DBNAME',
>         'WRDS_USERNAME',
>         'PGHOST',
>         'PGPORT',
>         'PGDATABASE',
>         'PGUSER',
>     )
>     return any(os.environ.get(key) for key in identity_keys)
>
>
> def _resolve_connection_settings():
>     config, profiles_path = _load_profiles_config()
>
>     explicit_profile = _normalize_profile_name(
>         _connection_profile or os.environ.get('WRDS_PROFILE')
>     )
>     if explicit_profile:
>         profile_name = explicit_profile
>         profile_settings = _load_named_profile(profile_name, config, profiles_path)
>     elif _has_explicit_connection_identity():
>         profile_name = None
>         profile_settings = {}
>     else:
>         default_profile = _normalize_profile_name(config.get('default_profile'))
>         if default_profile:
>             profile_name = default_profile
>             profile_settings = _load_named_profile(profile_name, config, profiles_path)
>         else:
>             profile_name = None
>             profile_settings = {}
>
>     hostname = (
>         profile_settings.get('hostname')
>         or os.environ.get('WRDS_HOSTNAME')
>         or os.environ.get('PGHOST')
>         or DEFAULT_WRDS_HOSTNAME
>     )
>     port = (
>         profile_settings.get('port')
>         or os.environ.get('WRDS_PORT')
>         or os.environ.get('PGPORT')
>         or DEFAULT_WRDS_PORT
>     )
>     dbname = (
>         profile_settings.get('dbname')
>         or os.environ.get('WRDS_DBNAME')
>         or os.environ.get('PGDATABASE')
>         or DEFAULT_WRDS_DBNAME
>     )
>     username = (
>         profile_settings.get('username')
>         or os.environ.get('WRDS_USERNAME')
>         or os.environ.get('PGUSER')
>         or DEFAULT_WRDS_USERNAME
>     )
>     password = (
>         os.environ.get('WRDS_PASSWORD')
>         or os.environ.get('PGPASSWORD')
>         or profile_settings.get('password')
>     )
>
>     if not password:
>         password = _load_pgpass_credentials(hostname, port, dbname, username)
>
>     return {
>         'profile_name': profile_name,
>         'hostname': hostname,
>         'port': int(port),
>         'dbname': dbname,
>         'username': username,
>         'password': password,
>     }
>
>
> def get_connection():
>     """Get or create a singleton WRDS connection."""
>     global _connection
>     if _connection is None:
>         settings = _resolve_connection_settings()
>
>         connection_kwargs = {
>             'wrds_hostname': settings['hostname'],
>             'wrds_port': settings['port'],
>             'wrds_dbname': settings['dbname'],
>             'wrds_username': settings['username'],
>         }
>         if settings['password']:
>             connection_kwargs['wrds_password'] = settings['password']
>
>         _connection = wrds.Connection(**connection_kwargs)
>     return _connection
>
>
> def close_connection():
>     """Close the singleton connection if open."""
>     global _connection
>     if _connection is not None:
>         _connection.close()
>         _connection = None
> ```
