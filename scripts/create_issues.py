import re
import subprocess
import argparse
import sys
from pathlib import Path

def parse_tasks(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_section = ""
    tasks = []
    current_task = None
    
    # Regex to match tasks with bold title: "- [ ] **Title**: Description"
    # We will checks startswith('-') to ensure it is a top-level task (not indented).
    task_pattern = re.compile(r'^\s*-\s*\[\s*\]\s*\*\*(.*?)\*\*:(.*)')
    
    for line in lines:
        stripped_line = line.strip()
        
        # Detect Section
        if line.startswith('## '):
            current_section = line.replace('## ', '').strip()
            # If we were building a task, it's done.
            current_task = None 
            continue
            
        # Detect Main Task (Must start with '-' at column 0)
        # We also ensure it matches the pattern **Title**: ...
        if line.startswith('- [ ]') and task_pattern.match(stripped_line):
            match = task_pattern.match(stripped_line)
            
            # If there was a previous task, save it
            if current_task:
                tasks.append(current_task)
            
            title = match.group(1).strip()
            description = match.group(2).strip()
            
            current_task = {
                'section': current_section,
                'title': title,
                'description': [description] if description else [],
                'subtasks': []
            }
        
        elif current_task and stripped_line.startswith('- [ ]'):
            # Detect subtask (indented or just a bullet in the body)
            # If it has **Title**: format, we keep that format in the text
            subtask_text = stripped_line.replace('- [ ]', '', 1).strip()
            current_task['subtasks'].append(subtask_text)
            
        elif current_task and stripped_line != "":
             # Append continuation lines
             current_task['description'].append(stripped_line)

    # Append the last task
    if current_task:
        tasks.append(current_task)
        
    return tasks

def create_issue_body(task):
    background = f"### 작업 배경 (Background)\n이 이슈는 **{task['section']}** 단계의 세부 작업입니다."
    
    work_detail = f"### 작업 내용 (Work Draft)\n"
    for desc_line in task['description']:
        work_detail += f"{desc_line}\n"
    
    if task['subtasks']:
        work_detail += "\n**세부 할 일:**\n"
        for sub in task['subtasks']:
            work_detail += f"- [ ] {sub}\n"

    acceptance_criteria = "### 인수 조건 (Acceptance Criteria)\n- [ ] 위 작업 내용이 모두 완료되어야 합니다.\n"
    if task['subtasks']:
         acceptance_criteria += "- [ ] 모든 세부 할 일이 완료되어야 합니다.\n"

    return f"{background}\n\n{work_detail}\n\n{acceptance_criteria}"

def main():
    # Force utf-8 output for Windows console to handle emojis
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass # Python < 3.7, though unlikely in modern envs

    parser = argparse.ArgumentParser(description='Create GitHub issues from TASKS.md')
    parser.add_argument('--dry-run', action='store_true', help='Print commands without executing')
    parser.add_argument('--repo', type=str, help='Target GitHub repository (e.g. owner/repo)')
    args = parser.parse_args()

    # tasks_file = Path(r"c:\workspace\STEP1\TASKS.md")
    # Assume script is in scripts/ and TASKS.md is in the root of the repo (one level up)
    script_dir = Path(__file__).parent
    tasks_file = script_dir.parent / "TASKS.md"
    
    if not tasks_file.exists():
        print(f"Error: File not found at {tasks_file}")
        sys.exit(1)

    tasks = parse_tasks(tasks_file)
    
    print(f"Found {len(tasks)} tasks.")

    for i, task in enumerate(tasks):
        title = task['title']
        body = create_issue_body(task)
        
        # Escape quotes for shell command if needed, but subprocess handles list args better
        # We will use list args with subprocess.
        
        print(f"[{i+1}/{len(tasks)}] Processing: {title}")
        
        if args.dry_run:
            print(f"--- DRY RUN: Issue Content ---")
            print(f"Title: {title}")
            print(f"Body:\n{body}")
            print("------------------------------\n")
        else:
            try:
                cmd = ['gh', 'issue', 'create', '--title', title, '--body', body]
                if args.repo:
                    cmd.extend(['--repo', args.repo])
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(f"Created issue: {result.stdout.strip()}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to create issue '{title}': {e.stderr}")

if __name__ == "__main__":
    main()
