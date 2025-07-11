#!/bin/bash
# AircBot Test Runner
# Simple script to run the consolidated test suite

echo "🤖 AircBot Test Suite"
echo "===================="
echo

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: No virtual environment detected."
    echo "   Consider running: source venv/bin/activate"
    echo
fi

# Run the consolidated test suite
echo "📋 Running consolidated test suite..."
python -m pytest tests/test_consolidated.py -v

# Check test result
if [ $? -eq 0 ]; then
    echo
    echo "✅ All tests passed!"
    echo
    echo "📊 Test Summary:"
    echo "   • 24 tests covering all major components"
    echo "   • Database, Link Handler, LLM, Privacy, Rate Limiting"
    echo "   • Integration tests for end-to-end workflows"
    echo "   • Performance and error handling validation"
else
    echo
    echo "❌ Some tests failed. Check output above for details."
    echo
    echo "💡 Tips:"
    echo "   • Ensure database files are writable"
    echo "   • Check network connectivity for integration tests"
    echo "   • Verify all dependencies are installed"
fi

echo
echo "📝 For more details, see tests/test_consolidation_report.md"
