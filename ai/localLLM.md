# start working with Local LLM

### Aider
# https://aider.chat/docs/llms/ollama.html
python -m pip install aider-install
aider-install
- configure your Ollama API endpoint (usually the default):
export OLLAMA_API_BASE=http://127.0.0.1:11434 # Mac/Linux
setx   OLLAMA_API_BASE http://127.0.0.1:11434 # Windows, restart shell after setx

Start working with aider and Ollama on your codebase:

# Pull the model
ollama pull <model>

# Start your ollama server, increasing the context window to 8k tokens
OLLAMA_CONTEXT_LENGTH=8192 ollama serve

# In another terminal window, change directory into your codebase
cd /to/your/project

aider --model ollama_chat/<model> # Using ollama_chat/ is recommended over ollama/.

If you are using an ollama that requires an API key you can set OLLAMA_API_KEY:

export OLLAMA_API_KEY=<api-key> # Mac/Linux
setx   OLLAMA_API_KEY <api-key> # Windows, restart shell after setx