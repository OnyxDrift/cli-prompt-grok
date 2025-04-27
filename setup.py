from setuptools import setup, find_packages

setup(
    name="grok-cli",
    version="0.0.1",
    packages=find_packages(),  # Automatically finds 'grok_cli' package
    install_requires=[
        "click>=8.1.3",
        "rich>=13.3.5",
        "httpx>=0.24.1",
        "python-dotenv>=1.0.0",
        "pyfiglet>=0.8.post1",
    ],
    entry_points={
        "console_scripts": [
            "prompt-grok = grok_cli.cli_prompt_grok:prompt_grok",
        ],
    },
    author="Your Name",
    description="A beautified CLI for prompting Grok 3 API",
    python_requires=">=3.7",
)