# Tests

Use synthetic, non-personal fixtures for parser and application tests.

Initial test cases should cover:
- Valid Messenger JSON
- Empty or missing message arrays
- Multiple participants
- Missing sender names
- Text and non-text messages
- Invalid timestamps
- Malformed JSON
- Large input files and graceful error reporting
- Ensuring only the selected speaker's messages are used for style profiling
