"""astra-textverse test suite.

Organization (see ARCHITECTURE.md §10):
- Unit tests (fast): grammar parser, strip rule, leak detector, validator
- Integration tests (mid-speed): nexus_bridge, observation_calc
- End-to-end tests (slow, CI nightly): full scenario runs
"""
