# Running Log

A Python console application to log daily runs and track progress against a 50km ultra marathon training plan.

## Setup

```bash
cd /Users/dancullum/running-log
pip install -r requirements.txt
```

## Usage

```bash
python -m running_log.main
```

## Configuration

### Training Plan

Copy the sample plan to your home directory and customize:

```bash
cp config/plan.yaml ~/.running-log/plan.yaml
```

Edit `~/.running-log/plan.yaml` to set your training schedule:

```yaml
schedule:
  2025-01-20: 5.0   # 5km run
  2025-01-21: 8.0   # 8km run
  2025-01-22: 0     # Rest day
```

## Data Storage

- **Database**: `~/.running-log/runs.db` (SQLite)
- **Training plan**: `~/.running-log/plan.yaml`
- **CSV export**: `~/running-log-export.csv`

## Menu Options

1. **Log run** - Record today's distance
2. **Today** - View target vs actual for today
3. **This week** - Summary of current week's progress
4. **History** - List of all logged runs
5. **Export CSV** - Export runs to `~/running-log-export.csv`
6. **Stats** - Total distance, completion percentage

## Raspberry Pi Deployment

Copy the project to your Pi:

```bash
scp -r /Users/dancullum/running-log pi@raspberrypi:~/
```

Then on the Pi:

```bash
cd ~/running-log
pip install -r requirements.txt
python -m running_log.main
```

To retrieve exported data:

```bash
scp pi@raspberrypi:~/running-log-export.csv .
```
