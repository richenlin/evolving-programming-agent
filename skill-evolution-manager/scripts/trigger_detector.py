#!/usr/bin/env python3
"""
Evolution Trigger Detector

Determines when to trigger skill evolution based on session context.
"""


def should_trigger_evolution(session_summary: dict) -> bool:
    """
    Determine if evolution should be triggered based on session summary.

    Args:
        session_summary: dict with keys:
            - attempts: number of fix attempts made
            - success: whether the task was completed successfully
            - feedback: user's explicit feedback (optional)

    Returns:
        bool: True if evolution should be triggered
    """
    # Condition 1: Complex bug fix (multiple attempts)
    if session_summary.get('attempts', 1) > 1:
        return True

    # Condition 2: User explicit feedback
    feedback = session_summary.get('feedback', '')
    if feedback and any(keyword in feedback.lower() for keyword in ['记住', '以后', '保存', '重要', 'remember', 'save', 'important']):
        return True

    # Condition 3: Successful completion with specific indicators
    if session_summary.get('success', False):
        # Could add more sophisticated conditions here
        pass

    return False


if __name__ == "__main__":
    import json

    # Test cases
    test_cases = [
        ({'attempts': 3, 'success': True}, True),
        ({'attempts': 1, 'success': True}, False),
        ({'attempts': 1, 'success': True, 'feedback': '记住这个'}, True),
        ({'attempts': 1, 'success': True, 'feedback': '很好'}, False),
    ]

    for summary, expected in test_cases:
        result = should_trigger_evolution(summary)
        status = "✓" if result == expected else "✗"
        print(f"{status} {summary} -> {result} (expected: {expected})")
