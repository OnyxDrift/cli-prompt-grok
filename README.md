# Grok Prompt CLI

**Grok Prompt CLI** is a command-line interface for interacting with xAI's Grok 3 API. It provides a beautified, interactive experience for sending prompts to Grok models (`grok-3-beta` and `grok-3-mini-beta`), with features like syntax-highlighted code blocks, cost estimation, and a loading spinner.

## Features

- **Interactive Prompt**: Enter prompts in an interactive shell with green prompts and purple responses (cyan for reasoning).
- **Model Selection**: Choose between `grok-3-beta` (default) and `grok-3-mini-beta` using the `--model` flag.
- **Streaming Mode**: Enable real-time response streaming with the `--stream` flag.
- **Syntax Highlighting**: Code blocks in responses (e.g., Python, JSON) are rendered with syntax highlighting using `rich`.
- **Markdown Support**: Non-code responses are formatted as Markdown for readability.
- **Cost Estimation**: Displays token usage and estimated API cost per request (e.g., `Tokens used: prompt=11, completion=1000, total=1011 | Cost: $0.015`); unavailable when streaming.
- **Loading Indicator**: Shows a spinner (`⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏`) for non-streaming responses to indicate progress.
- **Interrupt Handling**: Press `Ctrl+C` to interrupt API calls or exit the prompt gracefully.
- **Secure API Key Handling**: Loads `XAI_API_KEY` from a `.grok-prompt` file, enforces `600` permissions, and avoids key exposure in logs.
- **Debug Logging**: Optional debug output (controlled via `DEBUG_LOGGING`) for troubleshooting.
- **Help Command**: Type `help` or use `--help` to view usage, options, and environment variables.
- **Configurable Token Limit**: Set maximum response tokens via `MAX_TOKENS` (default: 1500).

## Future Improvements

- ???

## Requirements

- **Python**: 3.7 or higher (tested with 3.13)
- **Dependencies**:
  - `click>=8.1.3`
  - `rich>=13.3.5`
  - `httpx>=0.24.1`
  - `python-dotenv>=1.0.0`
  - `pyfiglet>=0.8.post1`
- **xAI API Key**: Obtain from [console.x.ai](https://console.x.ai)

## Installation
1. Clone the repository locally
2. Source python virtual environment of choice
3. Install dependencies
    > pip install click rich httpx python-dotenv pyfiglet
4. Install as a Bash command; from root directory of project, execute:
    > pip install .
5. Verify installation
    > which prompt-grok
    > prompt-grok --help

## Configuration
- The script loads configuration from ~/.grok-prompt; you can override this with the GROK_ENV_PATH environment variable.
- A sample configuration file has been included ('.grok-prompt'); place this in the root of your User folder/Home Directory (~/).
- Set permissions
    > chmod 600 ~/.grok-prompt

## Usage
- Start interactive mode
    > prompt-grok
- Enable streaming mode
    > prompt-grok --stream
- Select a model
    > prompt-grok --model grok-3-mini-beta
- View help
    > prompt-grok --help
- View help while in interactive mode (simply just type 'help')
    > help

## Security
- API Key: Stored in ~/.grok-prompt with 600 permissions.
- No Exposure: The key is not logged or displayed in errors.
- HTTPS: API calls use https://api.x.ai/v1
- Recommendations:
    - Add your own cryptography to decrypt a ciphertext version of your API Key (see TODO statement in ./grok_cli/cli_prompt_grok.py)
        -   This would require you to create a method to encrypt the plaintext version of your API Key (which should not directly exist as part of this project, in any way)
    - Rotate your API keyys periodically aat console.x.ai
    - Restrict machine access (strong password, disable remote login)
    - Monitor API usage at console.x.ai

## Troubleshooting
- Uninstall
    > pip uninstall grok-cli -y

## Use Cases
- Extremely Low Bandwith environment 
- CLI Preference
- Testing cost estimation for a perceived business use case

## License
This project is licensed under the MIT License. See the License file for details.