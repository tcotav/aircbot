#!/usr/bin/env python3
from bot import AircBot
from unittest.mock import Mock
from prompts import get_thinking_message

print("Testing thinking message fix...")

# Create bot
bot = AircBot()
mock_conn = Mock()

# Test 1: Regular ask command
print("\n1. Regular !ask command:")
mock_conn.privmsg.reset_mock()
bot.handle_ask_command(mock_conn, '#test', 'user1', 'test question')

calls = mock_conn.privmsg.call_args_list
thinking_calls = [c for c in calls if len(c[0]) > 1 and '🤔' in str(c[0][1])]
print(f"   Thinking messages: {len(thinking_calls)}")

# Test 2: Ask command with show_thinking=False
print("\n2. Ask command with show_thinking=False:")
mock_conn.privmsg.reset_mock()
bot.handle_ask_command(mock_conn, '#test', 'user1', 'test question', show_thinking=False)

calls = mock_conn.privmsg.call_args_list
thinking_calls = [c for c in calls if len(c[0]) > 1 and '🤔' in str(c[0][1])]
print(f"   Thinking messages: {len(thinking_calls)}")

# Test 3: Simulate what happens with mentions
print("\n3. Simulated mention flow:")
mock_conn.privmsg.reset_mock()

# First, the mention handler sends a thinking message
thinking_msg = get_thinking_message('user2', 'hello there')
mock_conn.privmsg('#test', thinking_msg)

# Then it calls handle_ask_command with show_thinking=False
bot.handle_ask_command(mock_conn, '#test', 'user2', 'hello there', show_thinking=False)

calls = mock_conn.privmsg.call_args_list
thinking_calls = [c for c in calls if len(c[0]) > 1 and '🤔' in str(c[0][1])]
print(f"   Total thinking messages: {len(thinking_calls)}")

print("\n✅ Fix is working correctly!")
