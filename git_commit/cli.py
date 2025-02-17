import argparse
from math import e
import os
import subprocess
import requests
import tiktoken
from pathlib import Path
from typing import List, Tuple

MAX_TOKENS = 128000
TOKEN_PER_CHAR = 0.25
BINARY_EXT = {'.png', '.jpg', '.pdf', '.zip', '.docx', '.xlsx'}

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Auto-commit tool with AI generated messages",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Stage all changed files")
    group.add_argument("--add", nargs="+", metavar="FILE", help="Stage specific files/directories")
    return parser.parse_args()

def get_changed_files() -> List[Tuple[str, str]]:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, 
        text=True,
        check=True
    )
    return [
        (line[:2].strip(), line[3:].strip())
        for line in result.stdout.strip().split("\n") if line
    ]

def validate_files(files: List[str]) -> List[str]:
    changed_files = [f[1] for f in get_changed_files()]
    valid_files = []
    
    for pattern in files:
        matched = subprocess.run(
            ["git", "ls-files", pattern],
            capture_output=True,
            text=True
        ).stdout.split()
        
        if not matched:
            raise ValueError(f"No changed files match: {pattern}")
            
        valid_files.extend(
            f for f in matched if f in changed_files
        )
    
    return list(set(valid_files))

def stage_files(args) -> List[Tuple[str, str]]:
    if args.all:
        subprocess.run(["git", "add", "-A"], check=True)
        return get_changed_files()
        
    if args.add:
        valid_files = validate_files(args.add)
        subprocess.run(["git", "add", "--"] + valid_files, check=True)
        return [
            (status, f) 
            for status, f in get_changed_files()
            if f in valid_files
        ]

def get_file_diffs(files: List[Tuple[str, str]]) -> List[Tuple[str, str, str]]:
    return [
        (status, f, subprocess.run(
            ["git", "diff", "--cached", f],  # 只显示已暂存的变化
            capture_output=True, 
            text=True
        ).stdout)
        for status, f in files
    ]

def estimate_tokens(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

def should_ignore_file(file_path: str) -> bool:
    ext = Path(file_path).suffix.lower()
    return ext in BINARY_EXT

def split_changes(changes: List[Tuple[str, str, str]]) -> Tuple[List, List]:
    detailed, summary = [], []
    total_tokens = 0
    
    for status, file, diff in changes:
        if should_ignore_file(file):
            continue
            
        file_info = f"{file} ({status})"
        diff_tokens = estimate_tokens(diff)
        
        if total_tokens + diff_tokens < MAX_TOKENS * 0.8:
            detailed.append((status, file, diff))
            total_tokens += diff_tokens
        else:
            summary.append(file_info)
    
    return detailed, summary

def build_prompt(detailed: List, summary: List) -> str:
    prompt = []
    
    if detailed:
        prompt.append("\nDetailed changes:")
        for status, file, diff in detailed:
            prompt.append(f"\nFile: {file} ({status})\nDiff:\n{diff[:5000]}...")  # 截断长文件
    
    if summary:
        prompt.append("\n[Other changed files:")
        prompt.append("\n".join(summary))


    prompt.append('Above text is the changes of a git commit, please write a brief and friendly Git commit comments according to the changes. \nThe comments will be used as the commit message. \nAnd the final output should be in ENGLISH and the summarized text MUST start with "Comments of commit:", please DO NOT GIVE optimization suggestions.')  
    return "\n".join(prompt)

def generate_commit_message(changes: List[Tuple[str, str, str]]) -> str:
    detailed_changes, summary_changes = split_changes(changes)
    prompt = build_prompt(detailed_changes, summary_changes)
    
    # api_key = os.getenv('AI_API_KEY', 'sk-39c7bfb2f6264d26b3f0afb73a89e630')
    # ai_server = os.getenv('AI_SERVER', 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions')
    # ai_model = os.getenv('AI_MODEL', 'deepseek-r1-distill-qwen-7b')
    ai_server = os.getenv('AI_SERVER', 'http://192.168.125.80:11434/v1/chat/completions')
    ai_model = os.getenv('AI_MODEL', 'deepseek-r1:32b')
    
    # headers = {'Authorization': f"Bearer {api_key}"}
    response = requests.post(
        ai_server,
        # headers=headers,
        json = {
            "model": ai_model,
            "parameters": {
                "temperature": 0.2,
                "top_p": 0.9,
                # "max_tokens": 1024,
                # "presence_penalty": 0,
                # "frequency_penalty": 0,
                # "n": 1,
                # "stop": ["\n\n"]
            },
            "messages": [{
                "role": "system",
                "content": "You are a senior DevOPS software engineer, now you are working on submitting a git commit with AI generated comments."
            }, {
                "role": "user",
                "content": prompt
            }]
        }
    )
    result = response.json()['choices'][0]['message']['content']
    return result.split("Comments of commit:")[-1].strip()

def commit_changes(args):
    try:
        staged_files = stage_files(args)
        diffs = get_file_diffs(staged_files)
        message = generate_commit_message(diffs)
        subprocess.run(["git", "commit", "-m", message], check=True)
        print(f"Successfully committed:\n {message}")
        
    except subprocess.CalledProcessError as e:
        print(f"Git error: {str(e)}")
    except ValueError as e:
        print(f"Validation error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

def main():
    args = parse_arguments()
    commit_changes(args)
        
if __name__ == "__main__":
    main()
