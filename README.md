# Psychrometric Chart Application

A web application for generating and interacting with psychrometric charts.

## Deployment on Render

This application is configured for deployment on Render. The following files have been set up for deployment:

- `requirements.txt`: Contains all the Python dependencies
- `Procfile`: Tells Render how to run the application
- `runtime.txt`: Specifies the Python version
- `.gitignore`: Excludes unnecessary files from deployment

### Deployment Steps

1. Sign up for a Render account at [render.com](https://render.com/)
2. From your Render dashboard, click "New" and select "Web Service"
3. Connect your Git repository or use the "Upload Files" option
4. Configure your web service:
   - **Name**: Choose a name for your app (e.g., "psychrochart-app")
   - **Environment**: Select "Python"
   - **Region**: Choose the region closest to your users
   - **Branch**: main (or your default branch)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Click "Create Web Service"

### Local Development

To run the application locally:

```
pip install -r requirements.txt
python main.py
```

The application will be available at http://localhost:8000
