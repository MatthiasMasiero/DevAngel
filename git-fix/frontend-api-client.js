// Frontend API client for error data
class ErrorAPI {
  constructor(apiUrl) {
    this.apiUrl = apiUrl || 'https://your-api-id.execute-api.us-east-1.amazonaws.com/prod';
  }

  async getErrors(bucket, key) {
    try {
      const response = await fetch(`${this.apiUrl}/errors?bucket=${bucket}&key=${key}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      return this.getMockData(); // Fallback to mock data
    }
  }

  getMockData() {
    return {
      error_type: "Database Connection Timeout",
      timestamp: "2024-10-26T04:51:42Z",
      affected_files: ["src/database.py", "src/models/user.py"],
      error_count: 15,
      sample_logs: [
        "ERROR: Connection timeout after 30s",
        "ERROR: Failed to connect to DB pool",
        "ERROR: Max retries exceeded"
      ],
      severity: "high",
      status: "open"
    };
  }
}

// Usage example
const errorAPI = new ErrorAPI();

async function loadErrorData() {
  const errorData = await errorAPI.getErrors('your-error-bucket', 'errors/latest.json');
  
  // Display in your frontend
  document.getElementById('error-type').textContent = errorData.error_type;
  document.getElementById('error-count').textContent = errorData.error_count;
  document.getElementById('affected-files').textContent = errorData.affected_files.join(', ');
}

// Call when page loads
loadErrorData();
