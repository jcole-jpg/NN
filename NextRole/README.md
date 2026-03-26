# NextRole

An AI-powered CV analysis and optimization platform built with Streamlit.

## Features

- **CV Parsing**: Extract structured information from PDF or DOCX resumes
- **Job Matching**: Generate ranked job recommendations based on your CV
- **Skill Gap Analysis**: Identify missing skills for target roles
- **CV Optimization**: AI-powered rewriting of summary and experience bullets
- **Interview Prep**: Generate STAR-based interview answers

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
echo "OPENAI_API_KEY=your_key_here" > .env

# Run the app
streamlit run streamlit_app.py
```

### Deployment

The app is configured for Streamlit Cloud deployment:
- Repository: `jcole-jpg/ADV-NN`
- Branch: `main`
- Main file: `streamlit_app.py`

## Configuration

Create a `.env` file in the root directory with:

```
OPENAI_API_KEY=your_openai_api_key
```

For Streamlit Cloud, add the same key to Streamlit Secrets.

2. Demo fallback mode
   If the key is missing or quota is exhausted, the app falls back to local heuristic generation so the workflow still completes for a presentation.

Choice:
For a real submission or judged project, use live AI mode.
For a classroom or live demo where reliability matters most, keep live AI mode configured but rely on the fallback as a safety net.

## Local setup

1. Create a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

3. Create your local secrets file:

```bash
mkdir -p .streamlit
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
```

4. Edit `.streamlit/secrets.toml` and paste your real OpenAI key:

```toml
OPENAI_API_KEY = "your_openai_api_key_here"
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TIMEOUT_SECONDS = "20"
```

5. Optional:
You can also keep the key in `.env.local` instead. The app supports both.

6. Run the app:

```bash
python3 -m streamlit run streamlit.py
```

7. Open the local URL shown in the terminal, usually:

```bash
http://localhost:8501
```

## Smooth live demo plan

1. Start the app 5-10 minutes before your presentation.
2. Open the browser page once so Streamlit finishes the first load.
3. Use a clean text-based PDF or DOCX, not a scanned resume image.
4. Keep one backup CV file ready in case the first file has poor formatting.
5. In the app sidebar, use the `Reset demo` button between runs.
6. Keep your OpenAI key configured, but remember the app now has a visible fallback mode if quota fails.

## Deploy on Streamlit Community Cloud

Current Streamlit docs say Community Cloud deployment uses your GitHub repository, an entrypoint file, `requirements.txt`, and app secrets.

Docs used:
- Deploy your app: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- File organization: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization
- Dependencies: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- Secrets: https://docs.streamlit.io/develop/api-reference/connections/secrets.toml

### Exact deployment steps

1. Push this project to your GitHub repository.

2. Make sure these files are present at the repo root:

```text
requirements.txt
streamlit.py
streamlit_app.py
.streamlit/config.toml
backend/agent.py
backend/parser.py
```

3. Go to Streamlit Community Cloud.

4. Click `Create app`.

5. Choose your GitHub repository.

6. Set:

```text
Branch: main
Main file path: streamlit.py
```

7. Open Advanced settings.

8. In the Secrets field, paste:

```toml
OPENAI_API_KEY = "your_openai_api_key_here"
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TIMEOUT_SECONDS = "20"
```

9. Deploy the app.

10. After the first build finishes, open the app and test:
   Upload CV -> Generate Results -> Generate Interview Prep

## GitHub push steps

This folder is already initialized as a local git repo and pointed at:

```bash
https://github.com/jcole-jpg/ADV-NN.git
```

To publish it from your terminal:

```bash
git add .
git commit -m "Add Streamlit deployment version of NextRole"
git push -u origin main
```

If GitHub asks for authentication, use the method already configured on your machine:
- GitHub Desktop
- credential manager
- or a personal access token

## Troubleshooting

### The app says fallback mode is active

This means one of these is true:
- `OPENAI_API_KEY` is missing
- your OpenAI quota is exhausted
- the API timed out

The app will still run, but it will use local fallback generation instead of live GPT responses.

### File upload works but parsing looks weak

Most likely causes:
- the PDF is scanned and not text-based
- the CV layout is highly graphical
- the app is in fallback mode instead of live AI mode

### Streamlit Cloud build fails

Check:
- `requirements.txt` is in the repo root
- the entrypoint is exactly `streamlit.py`
- secrets were pasted in the app settings
- the repo push actually completed
