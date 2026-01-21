# Running Log Web App

A mobile-friendly Flask web application for tracking your running training towards a 50km ultra marathon.

## Features

- **Dashboard**: View today's target, recent runs, and progress towards the 50km goal
- **Quick Logging**: Log runs with a single tap using preset distances
- **Training Plan**: View upcoming targets for the next 7 days
- **History**: Browse all logged runs with comparison to targets
- **Statistics**: Detailed stats including streaks, averages, and weekly summaries

## Running Locally

### Prerequisites

- Python 3.10+
- pip

### Setup

1. Install dependencies:
   ```bash
   cd /path/to/running-log
   pip install -r requirements.txt
   ```

2. Run the development server:
   ```bash
   python web/app.py
   ```

3. Open your browser to: http://localhost:5000

The app will use the SQLite database at `~/.running-log/runs.db` and training plan from `~/.running-log/plan.yaml` (or falls back to `config/plan.yaml`).

## Deploying to PythonAnywhere

### Initial Setup

1. Sign up for a free account at [PythonAnywhere](https://www.pythonanywhere.com)

2. Open a Bash console and clone your repository:
   ```bash
   git clone https://github.com/yourusername/running-log.git
   ```

3. Create a virtual environment:
   ```bash
   cd running-log
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Configure Web App

1. Go to the **Web** tab in PythonAnywhere

2. Click **Add a new web app**

3. Choose **Manual configuration** and select Python 3.10+

4. Set the **Source code** directory:
   ```
   /home/yourusername/running-log/web
   ```

5. Set the **Working directory**:
   ```
   /home/yourusername/running-log
   ```

6. Edit the **WSGI configuration file** and replace the contents with:
   ```python
   import sys
   import os

   # Add your project to the path
   project_home = '/home/yourusername/running-log'
   if project_home not in sys.path:
       sys.path.insert(0, project_home)

   # Set the working directory
   os.chdir(project_home)

   # Import the Flask app
   from web.app import app as application
   ```

7. Set the **Virtualenv** path:
   ```
   /home/yourusername/running-log/venv
   ```

8. Click **Reload** to start your app

### Data Storage

On PythonAnywhere, the database will be stored at `~/.running-log/runs.db`. This persists across reloads.

To set up your training plan:
```bash
mkdir -p ~/.running-log
cp /home/yourusername/running-log/config/plan.yaml ~/.running-log/plan.yaml
# Edit the plan as needed
nano ~/.running-log/plan.yaml
```

### Updating the App

After pushing changes to your repository:
```bash
cd ~/running-log
git pull
```
Then click **Reload** on the Web tab.

## Project Structure

```
running-log/
├── running_log/          # Core modules
│   ├── db.py             # SQLite database operations
│   ├── plan.py           # Training plan loading
│   └── ui.py             # Terminal UI helpers
├── web/                  # Flask web app
│   ├── app.py            # Main Flask application
│   ├── templates/        # Jinja2 templates
│   │   ├── base.html     # Base template with CSS
│   │   ├── dashboard.html
│   │   ├── log.html
│   │   ├── upcoming.html
│   │   ├── history.html
│   │   └── stats.html
│   └── README.md         # This file
├── config/
│   └── plan.yaml         # Default training plan
└── requirements.txt      # Python dependencies
```

## Security Notes

- Change the `secret_key` in `app.py` before deploying to production
- The default configuration is suitable for personal use
- For production deployment, consider using environment variables for configuration
