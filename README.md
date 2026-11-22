# CAMAP: Indoor Campus Navigation System

A web app that helps students, staff and visitors find their way around a multi-floor college building. It calculates the shortest walking route between any two rooms using Dijkstra's algorithm and shows the path floor by floor.

## Features

- **Shortest-path routing** between rooms, labs, offices and facilities (Dijkstra's algorithm)
- **Multi-floor support**: ground to third floor, connected by stairs and lifts
- **Role-based routes**: students get stair-only routes, while staff and guests can use lifts
- **Multilingual interface**: English, Hindi, Kannada, Tamil, Telugu
- **Campus assistant chatbot** for quick questions about rooms and facilities
- **User login and route history** stored in SQLite
- **Dashboard and profile pages**

## Tech Stack

Python, Flask, SQLite, HTML, CSS, JavaScript

## Getting Started

1. Clone the repository
   ```
   git clone https://github.com/deeksha27sharu-oss/CAMAP-Indoor-Campus-Navigation-System-.git
   cd CAMAP-Indoor-Campus-Navigation-System-
   ```
2. Create and activate a virtual environment
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies
   ```
   pip install -r requirements.txt
   ```
4. Create your settings file
   ```
   copy .env.example .env
   ```
   Open `.env` and fill in `SECRET_KEY` and `ADMIN_TOKEN`. To generate a key:
   ```
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
5. Run the app
   ```
   python app.py
   ```
   Open http://127.0.0.1:5000

## Project Structure

```
app.py          Flask app, routes, graph data, Dijkstra
templates/      HTML pages
static/         CSS, JavaScript, images
requirements.txt
.env.example    Template for environment settings
```

## Configuration

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Signs login sessions (required) |
| `ADMIN_TOKEN` | Password for `/admin/stats?key=...` |
| `FLASK_DEBUG` | `1` for development, `0` for production |
| `HOST` | `127.0.0.1` (local only) or `0.0.0.0` (network) |

## Roadmap

- Turn-by-turn text directions
- Accessibility routing options
- Nearest-facility search
- QR-code start points
- Smarter chatbot
- Admin dashboard and password-based login

## Author

Deeksha S