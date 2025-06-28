#!/usr/bin/env python3
"""
Test script for bot capability detection functionality

This script tests the _is_asking_for_capabilities method both as a standalone
function and optionally with the actual bot class if dependencies are available.
"""

import sys
import os

def _is_asking_for_capabilities_standalone(message: str) -> bool:
    """
    Standalone version of the capability detection function.
    This mirrors the implementation in bot.py for testing without dependencies.
    """
    capability_phrases = [
        "what can you do", "what do you do", "what are you for",
        "what are your capabilities", "what are your features",
        "what can you help with", "what can you help me with",
        "how can you help", "what commands", "what functions",
        "what are your commands", "what are your functions",
        "help me", "show help", "tell me what you do",
        "what's your purpose", "what is your purpose",
        "how do you work", "what do you offer"
    ]
    
    message_lower = message.lower().strip()
    
    # Check for exact or partial matches
    for phrase in capability_phrases:
        if phrase in message_lower:
            return True
    
    # Check if it's just "help" or "capabilities"
    stripped = message_lower.strip(" ?!.,;:")
    if stripped in ["help", "capabilities", "commands", "functions", "purpose"]:
        return True
        
    return False

def get_bot_method():
    """
    Try to import the bot class and return its capability detection method.
    Returns None if import fails (missing dependencies).
    """
    try:
        # Add the current directory to the path so we can import our modules
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from bot import AircBot
        bot = AircBot()
        return bot._is_asking_for_capabilities
    except ImportError as e:
        print(f"Note: Could not import bot class ({e}), using standalone version")
        return None

def run_tests(test_function, function_name):
    """Run the capability detection tests with the given function"""
    
    # Test cases that should return True (capability questions)
    capability_questions = [
        "what can you do?",
        "what can you do",
        "What can you do?",
        "what are your capabilities?",
        "what are your capabilities",
        "help",
        "Help",
        "help me",
        "what commands do you have?",
        "what are your functions",
        "how can you help?",
        "what's your purpose?",
        "tell me what you do",
        "show help",
        "what do you offer",
        "capabilities",
        "commands",
        "functions",
        "purpose"
    ]
    
    # Test cases that should return False (not capability questions)
    non_capability_questions = [
        "what links do you have?",
        "show me links",
        "what's the weather?",
        "hello",
        "thanks",
        "search for python tutorials",
        "what time is it?",
        "random question about cats",
        "what are you talking about?",
        "what did you say?",
        "show recent links",
        "search links"
    ]
    
    print(f"\n=== Testing {function_name} ===")
    
    # Test positive cases
    print(f"\n--- Capability Questions (should return True) ---")
    passed_positive = 0
    for question in capability_questions:
        result = test_function(question)
        status = "✓" if result else "✗"
        print(f"{status} '{question}' -> {result}")
        if result:
            passed_positive += 1
        else:
            print(f"   ERROR: Expected True but got False")
    
    # Test negative cases
    print(f"\n--- Non-Capability Questions (should return False) ---")
    passed_negative = 0
    for question in non_capability_questions:
        result = test_function(question)
        status = "✓" if not result else "✗"
        print(f"{status} '{question}' -> {result}")
        if not result:
            passed_negative += 1
        else:
            print(f"   ERROR: Expected False but got True")
    
    total_tests = len(capability_questions) + len(non_capability_questions)
    total_passed = passed_positive + passed_negative
    
    print(f"\n{function_name} Results:")
    print(f"  Positive tests: {passed_positive}/{len(capability_questions)} passed")
    print(f"  Negative tests: {passed_negative}/{len(non_capability_questions)} passed")
    print(f"  Overall: {total_passed}/{total_tests} tests passed")
    
    return total_passed == total_tests

def main():
    """Main test runner"""
    print("🧪 Capability Detection Test Suite")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test standalone version
    print("\n1. Testing standalone implementation...")
    standalone_passed = run_tests(_is_asking_for_capabilities_standalone, "Standalone Function")
    all_tests_passed = all_tests_passed and standalone_passed
    
    # Try to test bot class version
    bot_method = get_bot_method()
    if bot_method:
        print("\n2. Testing bot class implementation...")
        bot_passed = run_tests(bot_method, "Bot Class Method")
        all_tests_passed = all_tests_passed and bot_passed
        
        # Compare results between standalone and bot versions
        print("\n3. Comparing implementations...")
        test_cases = [
            "what can you do?", "help", "what's the weather?", "show links"
        ]
        
        implementations_match = True
        for test_case in test_cases:
            standalone_result = _is_asking_for_capabilities_standalone(test_case)
            bot_result = bot_method(test_case)
            match = standalone_result == bot_result
            status = "✓" if match else "✗"
            print(f"{status} '{test_case}': standalone={standalone_result}, bot={bot_result}")
            if not match:
                implementations_match = False
        
        if implementations_match:
            print("✅ Both implementations produce identical results!")
        else:
            print("❌ Implementations differ - check for inconsistencies!")
            all_tests_passed = False
    
    # Final summary
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 All tests passed! Capability detection is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please review the implementation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
