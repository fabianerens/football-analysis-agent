# Football Match Analysis Agent

A football match analysis tool built with [Google ADK](https://google.github.io/adk-docs/) and [Gradio](https://gradio.app/).

Compares two teams based on their recent match statistics and generates AI-powered insights and tactical recommendations.

## Features

- Select teams from major European leagues (Premier League, Bundesliga, Serie A, La Liga, Ligue 1, Champions League)
- Fetches real match data from [football-data.org](https://www.football-data.org/)
- Calculates performance metrics (goals, points, form)
- AI-generated insights and tactical recommendations using Google Gemini

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- API keys (see below)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/football-analysis-agent.git
   cd football-analysis-agent
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Configure API keys**

   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:
   ```env
   FOOTBALL_API_KEY=your_football_data_api_key
   GOOGLE_API_KEY=your_google_api_key
   ```

   **Get your API keys:**
   - Football Data: [football-data.org](https://www.football-data.org/) (free tier available)
   - Google AI: [Google AI Studio](https://aistudio.google.com/apikey)

## Usage

Start the application:
```bash
uv run python app.py
```

Open in browser: http://127.0.0.1:7860

### How to use

1. Select a league for Team A
2. Select Team A from the dropdown
3. Select a league for Team B
4. Select Team B from the dropdown
5. Choose how many recent matches to analyze (3-10)
6. Click "Analyze Match"

## Project Structure

```
football-analysis-agent/
├── app.py                      # Gradio web interface
├── bi_agent/
│   ├── football_tools.py       # API functions for football-data.org
│   ├── football_agent.py       # LLM agent for analysis
│   └── __init__.py
├── .env.example                # Example environment variables
├── pyproject.toml              # Dependencies
└── README.md
```

## Supported Leagues (Free Tier)

- Premier League (England)
- Bundesliga (Germany)
- Serie A (Italy)
- La Liga (Spain)
- Ligue 1 (France)
- Champions League

## Tech Stack

| Component | Technology |
|-----------|------------|
| UI | Gradio |
| Data API | football-data.org v4 |
| LLM | Google Gemini (via ADK) |
| Package Manager | uv |

## License

MIT License
