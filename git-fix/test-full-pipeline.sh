#!/bin/bash

echo "🧪 Testing Complete Error-Fixing Pipeline..."

echo "Step 1: Generating test errors..."
for i in {1..5}; do
  echo "ERROR: Database connection timeout - Test $i $(date)" | sudo tee -a /var/log/nginx/error.log
  sleep 2
done

echo "Step 2: Waiting 30 seconds for CloudWatch processing..."
sleep 30

echo "Step 3: Checking CloudWatch logs..."
aws logs filter-log-events \
  --log-group-name /quietops/website \
  --start-time $(date -d '2 minutes ago' +%s000) \
  --filter-pattern "ERROR"

echo "Step 4: Check GitHub for auto-created issue..."
echo "Go to: https://github.com/MatthiasMasiero/DevAngel/issues"
echo "Look for issue with 'Auto-Fix:' in the title"

echo "Step 5: Manual testing steps:"
echo "1. ✅ Comment '/q plan' on the auto-created issue"
echo "2. ✅ Wait for Amazon Q to analyze and respond"
echo "3. ✅ Comment '/q implement' to get automated fix"
echo "4. ✅ Check for auto-generated PR with fixes"

echo "🎉 Pipeline test complete!"
