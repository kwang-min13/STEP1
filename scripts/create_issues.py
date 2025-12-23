import re
import subprocess
import argparse
import sys
from pathlib import Path

def parse_tasks_from_phases(file_path):
    """
    Phase 기반의 새로운 TASKS.md 형식 파싱
    각 Phase의 세부 작업(####)을 개별 이슈로 생성
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    tasks = []
    
    # Phase 단위로 분할
    phase_pattern = r'## (Phase \d+:.*?)(?=## Phase|\Z)'
    phases = re.findall(phase_pattern, content, re.DOTALL)
    
    for phase_match in phases:
        phase_title = phase_match.split('\n')[0].strip()
        phase_content = phase_match
        
        # Phase 내의 목표 추출
        goal_match = re.search(r'### 목표\n(.*?)(?=###|\n####)', phase_content, re.DOTALL)
        phase_goal = goal_match.group(1).strip() if goal_match else ""
        
        # 세부 작업(####) 추출
        subtask_pattern = r'#### (\d+\.\d+) (.*?)\n(.*?)(?=####|\*\*체크포인트\*\*|\Z)'
        subtasks = re.findall(subtask_pattern, phase_content, re.DOTALL)
        
        for task_num, task_title, task_content in subtasks:
            # 파일 경로 추출
            file_match = re.search(r'\*\*파일\*\*: `(.*?)`', task_content)
            file_path_str = file_match.group(1) if file_match else ""
            
            # 체크리스트 추출
            checklist_match = re.search(r'\*\*체크리스트\*\*:(.*?)(?=```|\*\*|$)', task_content, re.DOTALL)
            checklist = checklist_match.group(1).strip() if checklist_match else ""
            
            # 코드 블록 제거 (이슈 본문이 너무 길어지지 않도록)
            content_without_code = re.sub(r'```.*?```', '[코드 예제는 TASKS.md 참조]', task_content, flags=re.DOTALL)
            
            tasks.append({
                'phase': phase_title,
                'task_num': task_num,
                'title': task_title.strip(),
                'goal': phase_goal,
                'content': content_without_code.strip(),
                'file_path': file_path_str,
                'checklist': checklist
            })
    
    return tasks

def create_issue_body(task):
    """
    GitHub 이슈 본문 생성: 작업 배경, 작업 내용, 인수 조건
    """
    background = f"""### 작업 배경 (Background)
이 이슈는 **{task['phase']}**의 세부 작업입니다.

**Phase 목표**: {task['goal']}
"""
    
    work_detail = f"""### 작업 내용 (Work Detail)
**작업 번호**: {task['task_num']}
**작업명**: {task['title']}
"""
    
    if task['file_path']:
        work_detail += f"\n**구현 파일**: `{task['file_path']}`\n"
    
    work_detail += f"\n{task['content']}\n"
    
    acceptance_criteria = """### 인수 조건 (Acceptance Criteria)
"""
    
    if task['checklist']:
        acceptance_criteria += task['checklist'] + "\n"
    else:
        acceptance_criteria += "- [ ] 위 작업 내용이 모두 완료되어야 합니다.\n"
    
    acceptance_criteria += "\n**참고**: 상세 구현 가이드는 [TASKS.md](../TASKS.md) 참조"
    
    return f"{background}\n{work_detail}\n{acceptance_criteria}"

def main():
    # Force utf-8 output for Windows console to handle emojis
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass  # Python < 3.7

    parser = argparse.ArgumentParser(description='Create GitHub issues from TASKS.md')
    parser.add_argument('--dry-run', action='store_true', help='Print commands without executing')
    parser.add_argument('--repo', type=str, default='kwang-min13/STEP1', help='Target GitHub repository')
    parser.add_argument('--label', type=str, default='enhancement', help='Label to add to issues')
    args = parser.parse_args()

    # Assume script is in scripts/ and TASKS.md is in the root of the repo
    script_dir = Path(__file__).parent
    tasks_file = script_dir.parent / "TASKS.md"
    
    if not tasks_file.exists():
        print(f"Error: File not found at {tasks_file}")
        sys.exit(1)

    tasks = parse_tasks_from_phases(tasks_file)
    
    print(f"Found {len(tasks)} tasks across all phases.")

    for i, task in enumerate(tasks):
        title = f"[{task['task_num']}] {task['title']}"
        body = create_issue_body(task)
        
        print(f"\n[{i+1}/{len(tasks)}] Processing: {title}")
        
        if args.dry_run:
            print(f"--- DRY RUN: Issue Content ---")
            print(f"Title: {title}")
            print(f"Body:\n{body[:500]}...")  # 처음 500자만 출력
            print("------------------------------")
        else:
            try:
                cmd = ['gh', 'issue', 'create', '--title', title, '--body', body, '--repo', args.repo]
                if args.label:
                    cmd.extend(['--label', args.label])
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(f"✓ Created: {result.stdout.strip()}")
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to create issue '{title}':")
                print(f"  Error: {e.stderr}")

if __name__ == "__main__":
    main()
