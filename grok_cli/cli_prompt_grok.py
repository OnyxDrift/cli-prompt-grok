import click
import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.status import Status
import json
from dotenv import load_dotenv
import os
from pyfiglet import Figlet
import re
import stat

# Initialize Rich console
console = Console()

# Load environment variables
DEFAULT_ENV_PATH = os.path.expanduser("~/.grok-prompt")
ENV_PATH = os.getenv("GROK_ENV_PATH", DEFAULT_ENV_PATH)
load_dotenv(ENV_PATH)

# TODO: highly suggested that you create your own external encryption process & utilize a contained decryption process, when working with the API_KEY ([SECURITY])
# Suggestion: Use macOS Keychain to store the API key securely and retrieve it using the 'security' command (e.g., security find-generic-password -s 'xai_api_key' -w).
API_KEY = os.getenv("XAI_API_KEY")

BASE_URL = "https://api.x.ai/v1"
VERSION = "0.0.1"
DEBUG_LOGGING = os.getenv("DEBUG_LOGGING", "true").lower() == "true"
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1500"))

# Pricing per 1K tokens (in USD)
GROK_3_BETA_INPUT_PRICE_PER_1K = float(os.getenv("GROK_3_BETA_INPUT_PRICE_PER_1K", "0.005"))
GROK_3_BETA_OUTPUT_PRICE_PER_1K = float(os.getenv("GROK_3_BETA_OUTPUT_PRICE_PER_1K", "0.015"))
GROK_3_MINI_BETA_INPUT_PRICE_PER_1K = float(os.getenv("GROK_3_MINI_BETA_INPUT_PRICE_PER_1K", "0.002"))
GROK_3_MINI_BETA_OUTPUT_PRICE_PER_1K = float(os.getenv("GROK_3_MINI_BETA_OUTPUT_PRICE_PER_1K", "0.006"))

def debug_log(message):
    """Print debug message if DEBUG_LOGGING is enabled."""
    if DEBUG_LOGGING:
        console.print(f"[yellow]DEBUG: {message}[/yellow]")

def clean_response(response):
    """Clean response by normalizing whitespace and preserving markdown lists."""
    if not response:
        return response
    response = re.sub(r'\n\s*\n+', '\n\n', response.strip())
    lines = response.split('\n')
    cleaned_lines = [re.sub(r'\s+', ' ', line).strip() if not line.strip().startswith(('1.', '2.', '3.', '4.', '•')) else line.strip() for line in lines]
    return '\n'.join(cleaned_lines).strip()

def calculate_cost(model, prompt_tokens, completion_tokens):
    """Calculate API cost based on model and token usage."""
    if model == "grok-3-beta":
        input_price = GROK_3_BETA_INPUT_PRICE_PER_1K
        output_price = GROK_3_BETA_OUTPUT_PRICE_PER_1K
    elif model == "grok-3-mini-beta":
        input_price = GROK_3_MINI_BETA_INPUT_PRICE_PER_1K
        output_price = GROK_3_MINI_BETA_OUTPUT_PRICE_PER_1K
    else:
        debug_log(f"Unknown model '{model}' for cost calculation, using $0.0")
        return 0.0

    input_cost = (prompt_tokens / 1000) * input_price
    output_cost = (completion_tokens / 1000) * output_price
    total_cost = input_cost + output_cost
    return total_cost

def check_env_security():
    """Check if .env file permissions are secure."""
    if os.path.exists(ENV_PATH):
        permissions = oct(os.stat(ENV_PATH).st_mode & 0o777)[-3:]
        if permissions != "600":
            console.print(f"[red]Warning: {ENV_PATH} permissions are {permissions}, should be 600 (rw-------). Fix with: chmod 600 {ENV_PATH}[/red]")
        if os.access(ENV_PATH, os.R_OK):
            with open(ENV_PATH, 'r') as f:
                for line in f:
                    if "XAI_API_KEY" in line and not line.strip().startswith("#"):
                        return True
    return False

def print_help():
    """Print a styled help message for the CLI."""
    help_text = f"""
[bold yellow]Grok Prompt CLI[/bold yellow]
A command-line interface for interacting with xAI's Grok 3 API.

[bold]Usage:[/bold]
  prompt-grok [OPTIONS]

[bold]Options:[/bold]
  -h, --help          Show this help message and exit.
  --stream            Enable streaming mode for real-time API responses.
  --model TEXT        Choose the Grok model: grok-3-beta, grok-3-mini-beta (default: grok-3-beta).

[bold]Interactive Commands:[/bold]
  help                Display this help message.
  exit                Exit the interactive prompt.

[bold]Environment Variables:[/bold]
  XAI_API_KEY         Your xAI API key (required, set in {ENV_PATH}).
  GROK_ENV_PATH       Path to .env file (default: {DEFAULT_ENV_PATH}).
  DEBUG_LOGGING       Enable/disable debug logging (true/false, default: true).
  MAX_TOKENS          Maximum tokens for API responses (default: 1500).
  GROK_3_BETA_INPUT_PRICE_PER_1K       Price per 1K input tokens for grok-3-beta (default: 0.005).
  GROK_3_BETA_OUTPUT_PRICE_PER_1K      Price per 1K output tokens for grok-3-beta (default: 0.015).
  GROK_3_MINI_BETA_INPUT_PRICE_PER_1K  Price per 1K input tokens for grok-3-mini-beta (default: 0.002).
  GROK_3_MINI_BETA_OUTPUT_PRICE_PER_1K Price per 1K output tokens for grok-3-mini-beta (default: 0.006).

[bold]Examples:[/bold]
  Start interactive mode:
    $ prompt-grok

  Use streaming mode:
    $ prompt-grok --stream

  Use grok-3-mini-beta model:
    $ prompt-grok --model grok-3-mini-beta

  Show help:
    $ prompt-grok --help

[bold]Notes:[/bold]
- Ensure {ENV_PATH} contains XAI_API_KEY and has 600 permissions (chmod 600 {ENV_PATH}).
- Type 'exit' or Ctrl+C to quit the interactive prompt.
- Update pricing in {ENV_PATH} based on xAI's API rates (check https://x.ai/api).
- Secure your API key by rotating it periodically at https://console.x.ai.
"""
    console.print(Panel(help_text, title="Help", border_style="yellow", expand=False))

def make_non_streaming_call(prompt, model="grok-3-beta"):
    """Send non-streaming prompt to Grok 3 API with a single attempt."""
    debug_log(f"Entered make_non_streaming_call(prompt='{prompt[:30]}...', model={model})")
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
        "stream": False,
    }
    debug_log(f"Payload={json.dumps(payload, indent=2)}")
    try:
        with httpx.Client(timeout=30) as client:
            debug_log("Sending POST request")
            response = client.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers)
            debug_log(f"Response status={response.status_code}")
            response.raise_for_status()
            data = response.json()
            debug_log(f"Response data={json.dumps(data, indent=2)}")
            # Log the model returned by the API, if available
            response_model = data.get("model", "Not specified in response")
            debug_log(f"Model used by API: {response_model}")
            tokens = data.get("usage", {})
            # Extract token counts
            prompt_tokens = tokens.get('prompt_tokens', 0)
            completion_tokens = tokens.get('completion_tokens', 0)
            api_total_tokens = tokens.get('total_tokens', 0)
            # Calculate total tokens locally
            '''calculated_total = prompt_tokens + completion_tokens
            debug_log(f"API reported total_tokens={api_total_tokens}, calculated total={calculated_total}")
            tokens['total_tokens'] = calculated_total  # Override total_tokens'''
            # Extract content and reasoning_content
            message = data["choices"][0]["message"]
            content = message.get("content", "")
            reasoning_content = message.get("reasoning_content", "")
            debug_log(f"Raw content={content}")
            debug_log(f"Raw reasoning_content={reasoning_content}")
            content = clean_response(content)
            reasoning_content = clean_response(reasoning_content)
            debug_log(f"Cleaned content type={type(content)}, length={len(content)}")
            debug_log(f"Cleaned reasoning_content type={type(reasoning_content)}, length={len(reasoning_content)}")
            return content, reasoning_content, tokens
    except KeyboardInterrupt:
        console.print("[yellow]Request interrupted by user.[/yellow]")
        return None, None, None
    except httpx.HTTPStatusError as e:
        debug_log(f"HTTP error: status={e.response.status_code}, text={e.response.text}")
        console.print(f"[red]Error: HTTP {e.response.status_code} - {e.response.text}[/red]")
        return None, None, None
    except httpx.RequestError as e:
        debug_log(f"Network error: {e}")
        console.print(f"[red]Network error: {e}[/red]")
        return None, None, None
    except Exception as e:
        debug_log(f"Unexpected error: {e}")
        console.print(f"[red]Error: {e}[/red]")
        return None, None, None

def make_streaming_call(prompt, model="grok-3-beta"):
    """Send streaming prompt to Grok 3 API with a single attempt."""
    debug_log(f"Entered make_streaming_call(prompt='{prompt[:30]}...', model={model})")
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
        "stream": True,
    }
    debug_log(f"Payload={json.dumps(payload, indent=2)}")
    try:
        with httpx.Client(timeout=30) as client:
            debug_log("Sending streaming POST request")
            with client.stream("POST", f"{BASE_URL}/chat/completions", json=payload, headers=headers) as response:
                debug_log(f"Streaming response status={response.status_code}")
                response.raise_for_status()
                for chunk in response.iter_lines():
                    if chunk.startswith("data: ") and chunk != "data: [DONE]":
                        data = json.loads(chunk[6:])
                        debug_log(f"Stream chunk={json.dumps(data, indent=2)}")
                        if data.get("choices"):
                            yield data["choices"][0]["delta"].get("content", "")
    except KeyboardInterrupt:
        console.print("[yellow]Streaming request interrupted by user.[/yellow]")
        return
    except httpx.HTTPStatusError as e:
        debug_log(f"HTTP error: status={e.response.status_code}, text={e.response.text}")
        console.print(f"[red]Error: HTTP {e.response.status_code} - {e.response.text}[/red]")
        return
    except httpx.RequestError as e:
        debug_log(f"Network error: {e}")
        console.print(f"[red]Network error: {e}[/red]")
        return
    except Exception as e:
        debug_log(f"Unexpected error: {e}")
        console.print(f"[red]Error: {e}[/red]")
        return

@click.command(help="A CLI for interacting with xAI's Grok 3 API. Enter interactive mode to send prompts or use options for specific configurations.")
@click.option("--stream", is_flag=True, help="Enable streaming mode for real-time API responses.")
@click.option("--model", default="grok-3-beta", help="Choose the Grok model: grok-3-beta or grok-3-mini-beta.", type=click.Choice(["grok-3-beta", "grok-3-mini-beta"]))
def prompt_grok(stream, model):
    """Interactive chat with Grok 3 API."""
    # Check .env security
    if not check_env_security():
        console.print(f"[red]Error: XAI_API_KEY not found in {ENV_PATH} or file is missing/insecure.[/red]")
        console.print(f"[red]Please create {ENV_PATH} with XAI_API_KEY and set permissions to 600 (chmod 600 {ENV_PATH}).[/red]")
        return

    # Validate API key
    if not API_KEY or not API_KEY.strip():
        console.print(f"[red]Error: XAI_API_KEY is empty or invalid in {ENV_PATH}.[/red]")
        return

    # Display pyfiglet banner and version
    figlet = Figlet(font="standard")
    console.print(f"[yellow]{figlet.renderText('Prompt Grok')}[/yellow]")
    console.print(f"[yellow]Version: {VERSION}[/yellow]")

    console.print(f"[yellow]Starting chat with {model} (streaming: {'on' if stream else 'off'}). Type 'exit' or Ctrl+C to quit.[/yellow]")

    while True:
        try:
            # Print prompt prefix and capture input
            console.print("[green]>>> [/green]", end="")
            prompt = input().strip()
            if prompt.lower() == "exit":
                console.print("[yellow]Exiting chat.[/yellow]")
                break
            if prompt.lower() == "help":
                print_help()
                continue
            if not prompt:
                continue

            console.print(f"[green bold]>>> You:[/green bold] {prompt}")

            debug_log(f"Processing prompt, stream={stream}, model={model}")
            if stream:
                console.print(f"[blue bold]>>> Grok 3 (streaming):[/blue bold]")
                debug_log("Calling make_streaming_call")
                full_response = ""
                for chunk in make_streaming_call(prompt, model=model):
                    full_response += chunk
                    console.print(chunk, end="", style="blue")
                console.print()
                response = clean_response(full_response)
                console.print(Markdown(response, style="blue"))
            else:
                debug_log("Calling make_non_streaming_call")
                with Status("[yellow]Waiting for response...[/yellow]", spinner="dots") as status:
                    response, reasoning_content, tokens = make_non_streaming_call(prompt, model=model)
                debug_log(f"Response type={type(response)}")
                if response is None:
                    console.print("[red]No response received from API.[/red]")
                    continue
                if not isinstance(response, str):
                    console.print(f"[red]Error: Expected string response, got {type(response)}[/red]")
                    continue
                # Print reasoning_content in cyan, if available
                if reasoning_content:
                    console.print(f"[cyan bold]>>> Reasoning:[/cyan bold]")
                    console.print(Markdown(reasoning_content, style="cyan"))
                # Print the main response in blue (appears as purple in your terminal)
                console.print(f"[blue bold]>>> Grok 3:[/blue bold]")
                parts = re.split(r'(```.*?```)', response, flags=re.DOTALL)
                for part in parts:
                    if part.startswith("```") and part.endswith("```"):
                        code_content = part[3:-3].strip()
                        lines = code_content.split("\n")
                        lang = lines[0].strip() if lines and lines[0].strip() else "text"
                        code = "\n".join(lines[1:] if lines[0].strip() else lines).strip()
                        if code:
                            console.print(Syntax(code, lang, theme="monokai"))
                            console.print()  # Add blank line after code snippet
                    else:
                        part = clean_response(part)
                        if part.strip():
                            console.print(Markdown(part, style="blue"))
                # Print token usage and cost after response
                if tokens:
                    prompt_tokens = tokens.get('prompt_tokens', 0)
                    completion_tokens = tokens.get('completion_tokens', 0)
                    total_tokens = tokens.get('total_tokens', 0)
                    cost = calculate_cost(model, prompt_tokens, completion_tokens)
                    console.print(f"[yellow]Tokens used: prompt={prompt_tokens}, completion={completion_tokens}, total={total_tokens} | Cost: ${cost:.3f}[/yellow]")

        except KeyboardInterrupt:
            console.print("[yellow]\nExiting chat.[/yellow]")
            break
        except Exception as e:
            debug_log(f"Prompt loop error: {e}")
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    prompt_grok()