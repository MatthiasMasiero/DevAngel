#!/bin/bash

# Test the GitHub repository dispatch
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/rayyanh192/git-fix/dispatches \
  -d '{
    "event_type": "auto_fix_request",
    "client_payload": {
      "error_summary": {
        "error_type": "Test Database Error",
        "affected_files": ["src/test.py"],
        "error_count": 5,
        "sample_logs": ["ERROR: Test connection failed"]
      }
    }
  }'
