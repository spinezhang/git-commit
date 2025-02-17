# AI Git Commit Auto-generator

A CLI tool that automatically generates semantic Git commit messages using AI analysis of code changes. Supports both full repo changes and selective file commits.

![Git Workflow](https://img.shields.io/badge/Workflow-Git-orange) ![AI Integration](https://img.shields.io/badge/Powered%20By-DeepSeek-blue)

## Features

- 🚀 Automatic staging of changes (`--all` or selective `--add`)
- 📊 Smart diff analysis with token budgeting
- 🛡️ Binary file detection (images/docs/archives)
- 🌐 AI model integration (DeepSeek by default)
- ⚙️ Configurable via environment variables
- 🚫 Built-in error handling for Git operations

## Installation

```bash
python setup.py install
```

## Configuration

Create .env file:
```bash
AI_SERVER=http://your_ai_server:11434/v1/chat/completions
AI_MODEL=deepseek-r1:32b
```

## Usage

Commit all changes

```bash
git_commit --all
```

Commit specific files

```bash
git_commit --add src/utils.py tests/ --add README.md
```
