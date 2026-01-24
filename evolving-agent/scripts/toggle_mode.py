#!/usr/bin/env python3
"""
Evolution Mode Toggle Script

Controls the persistent evolution mode state for a session.
"""

import argparse
import sys
from pathlib import Path


def get_workspace_root() -> Path:
    """
    Detect the current workspace root directory.
    
    Returns:
        Path: The workspace root directory
    """
    current = Path.cwd()

    # Try to find .opencode directory
    opencode_dir = current / '.opencode'
    if opencode_dir.exists():
        return current

    # If not found, use current directory
    return current


def get_mode_marker_path() -> Path:
    """
    Get the path to the evolution mode marker file.
    
    Returns:
        Path: Path to .evolution_mode_active file
    """
    root = get_workspace_root()
    return root / '.opencode' / '.evolution_mode_active'


def enable_mode() -> str:
    """
    Enable evolution mode by creating the marker file.
    
    Returns:
        str: Success message
    """
    marker_path = get_mode_marker_path()
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.touch()
    return "✓ Evolution Mode ENABLED for this session"


def disable_mode() -> str:
    """
    Disable evolution mode by removing the marker file.
    
    Returns:
        str: Success message
    """
    marker_path = get_mode_marker_path()
    if marker_path.exists():
        marker_path.unlink()
        return "✓ Evolution Mode DISABLED for this session"
    return "ℹ Evolution Mode was not active"


def is_mode_active() -> bool:
    """
    Check if evolution mode is currently active.
    
    Returns:
        bool: True if mode is active
    """
    return get_mode_marker_path().exists()


def get_status_message() -> str:
    """
    Get the current status message.
    
    Returns:
        str: Status message
    """
    status = "ACTIVE" if is_mode_active() else "INACTIVE"
    marker_path = get_mode_marker_path()
    return f"Evolution Mode Status: {status}\nMarker file: {marker_path}"


def get_context_prompt() -> str:
    """
    Get the context prompt that should be injected into the AI's context.
    
    Returns:
        str: The reinforcement prompt
    """
    if not is_mode_active():
        return ""
    
    return """
## Evolution Mode Active
This session is in EVOLUTION MODE.
- After completing tasks, automatically check for extractable knowledge
- Run trigger detection even without explicit user commands
- Store valuable experiences to the knowledge base
- Only report to user when new knowledge is extracted
""".strip()


def main():
    parser = argparse.ArgumentParser(
        description='Toggle or check evolution mode status',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python toggle_mode.py                    # Show current status
  python toggle_mode.py --init            # Full init: start coordinator + enable mode
  python toggle_mode.py --on              # Enable evolution mode
  python toggle_mode.py --off              # Disable evolution mode
  python toggle_mode.py --on --inject      # Enable and print context prompt
  python toggle_mode.py --status           # Show detailed status
        """
    )

    parser.add_argument('--init', '-i', action='store_true',
                        help='Full initialization: start coordinator and enable evolution mode')
    parser.add_argument('--on', '-e', action='store_true',
                        help='Enable evolution mode')
    parser.add_argument('--off', '-d', action='store_true',
                        help='Disable evolution mode')
    parser.add_argument('--toggle', '-t', action='store_true',
                        help='Toggle current state')
    parser.add_argument('--inject', action='store_true',
                        help='Print context prompt for injection')
    parser.add_argument('--status', '-s', action='store_true',
                        help='Show detailed status')
    
    args = parser.parse_args()

    # Full initialization (manual trigger /evolve)
    if args.init:
        was_active = is_mode_active()
        result = enable_mode()

        # Only show message if this is a fresh activation
        if not was_active:
            print(result)  # Print the enable message
            print("\n" + "="*60)
            print("🚀 协调器已启动")
            print("="*60)
            print("\n📋 下一步建议：")
            print("   - 输入编程任务（如：帮我实现一个登录功能）")
            print("   - 或直接开始描述您的需求")
            print("\n💡 提示：")
            print("   - programming-assistant 将自动加载")
            print("   - 进化模式已激活，会自动提取有价值经验")
            print("   - 使用 'python toggle_mode.py --off' 可关闭进化模式")
            print("="*60 + "\n")
        return 0

    # Inject context prompt (can be combined with other operations)
    if args.inject:
        if args.on or args.off or args.toggle:
            # Combine with state change
            if args.on:
                print(enable_mode())
            elif args.off:
                print(disable_mode())
            elif args.toggle:
                if is_mode_active():
                    print(disable_mode())
                else:
                    print(enable_mode())
            # Then print context if enabled
            if is_mode_active():
                print("\n--- Context Prompt ---")
                print(get_context_prompt())
            else:
                print("\n--- Context Prompt ---")
                print("(No context prompt - evolution mode is inactive)")
        else:
            # Just print context
            if is_mode_active():
                print("--- Context Prompt ---")
                print(get_context_prompt())
            else:
                print("Evolution mode is not active. No context prompt to inject.")
        return 0

    # Enable
    if args.on:
        print(enable_mode())
        return 0
    
    # Disable
    if args.off:
        print(disable_mode())
        return 0
    
    # Toggle
    if args.toggle:
        if is_mode_active():
            print(disable_mode())
        else:
            print(enable_mode())
        return 0
    
    # Status query
    if args.status:
        print(get_status_message())
        return 0
    
    # Default: show status
    print(get_status_message())
    return 0


if __name__ == '__main__':
    sys.exit(main())
