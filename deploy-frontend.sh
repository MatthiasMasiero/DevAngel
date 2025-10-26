#!/bin/bash

echo "🚀 Deploying DevAngel Frontend..."

cd frontend

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the React app
echo "🔨 Building React app..."
npm run build

echo "✅ Frontend built successfully!"
echo ""
echo "🌐 Your API endpoint: https://2eotoxerkj.execute-api.us-east-1.amazonaws.com/prod/incidents"
echo ""
echo "To serve locally:"
echo "  cd frontend && npm start"
echo ""
echo "To deploy to AWS Amplify or S3:"
echo "  Upload the 'build' folder contents"
