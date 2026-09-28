name: Test Public Watchtower API

on:
  workflow_dispatch:

jobs:
  test_wp_api:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: '3.x'

      - name: Run Public Watchtower API test
        run: python test_wp_api.py
