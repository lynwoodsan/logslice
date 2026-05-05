# logslice

Stream and filter large log files by time range, level, or regex pattern from the command line.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/yourname/logslice.git && cd logslice && pip install .
```

---

## Usage

```bash
# Filter by log level
logslice app.log --level ERROR

# Filter by time range
logslice app.log --start "2024-01-15 08:00:00" --end "2024-01-15 09:00:00"

# Filter by regex pattern
logslice app.log --pattern "timeout|connection refused"

# Combine filters and stream output
logslice app.log --level WARNING --start "2024-01-15 08:00:00" --pattern "database" | less
```

### Options

| Flag | Description |
|------|-------------|
| `--level` | Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `--start` | Start of time range (ISO format) |
| `--end` | End of time range (ISO format) |
| `--pattern` | Regex pattern to match against log lines |
| `--follow` | Stream new lines as they are written (like `tail -f`) |

---

## Features

- Handles large log files efficiently without loading them into memory
- Supports common log formats out of the box
- Combine multiple filters in a single command
- `--follow` mode for live log monitoring

---

## License

MIT © [yourname](https://github.com/yourname)