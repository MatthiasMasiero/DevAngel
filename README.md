# DevAngel

**DevAngel** helps engineers resolve production outages fast. It ingests error logs, builds a pull request in one click, and gives a clear dashboard so you save hours during each incident.

---

## 🚀 Table of Contents

- [Inspiration](#inspiration)  
- [What It Does](#what-it-does)  
- [How We Built It](#how-we-built-it)  
- [Challenges We Ran Into](#challenges-we-ran-into)  
- [Accomplishments We’re Proud Of](#accomplishments-we’re-proud-of)  
- [What’s Next for DevAngel](#whats-next-for-devangel)  
- [Getting Started](#getting-started)  
- [Architectural Overview](#architectural-overview)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Inspiration  
When incidents hit production, engineers often scramble across multiple dashboards and log files trying to find the root cause. We wanted to create a **unified platform** that gives engineers clarity during chaos in real time. DevAngel is this guardian-angel for DevOps.  [oai_citation:0‡Devpost - The home for hackathons](https://devpost.com/software/devangel)

---

## What It Does  
DevAngel consolidates logs, metrics, and deployment information into one smart interface:
- Visualises error spikes using a custom SVG timeline graph.  [oai_citation:1‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- Maps which files contributed most to the incident.  [oai_citation:2‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- Summarises incidents in readable, human-friendly language.  [oai_citation:3‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- Displays real-time error alerts in a bottom popup.  [oai_citation:4‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- Lets engineers refresh live data, toggle dark/light mode, and open GitHub PRs directly.  [oai_citation:5‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
Powered by AWS infrastructure, DevAngel helps teams see, understand and act on production failures faster than ever.  [oai_citation:6‡Devpost - The home for hackathons](https://devpost.com/software/devangel)

---

## How We Built It  
We combined a full AWS toolchain with a modern frontend stack:
- **Frontend**: React.js  [oai_citation:7‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- **Hosting / CI-CD**: EC2 (and other AWS services)  [oai_citation:8‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- **Monitoring**: AWS CloudWatch Logs Insights — the source of incident & error data  [oai_citation:9‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- **Storage**: Amazon S3 for storing historical data snapshots (`data.json`)  [oai_citation:10‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- **Backend Automation**: AWS Lambda and Step Functions for orchestration  [oai_citation:11‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
Everything is designed to run serverless (or largely so) to scale automatically and deploy easily.  [oai_citation:12‡Devpost - The home for hackathons](https://devpost.com/software/devangel)

---

## Challenges We Ran Into  
- Fixing AWS Amplify build failures due to npm lockfile mismatches.  [oai_citation:13‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- Handling CORS and fetch paths between local testing and hosted environments.  [oai_citation:14‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- Designing a layout that fills all screen space elegantly without overwhelming users.  [oai_citation:15‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- Getting SVG scaling and labeling correct across both dark and light themes.  [oai_citation:16‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- Balancing professional aesthetics with fast load performance.  [oai_citation:17‡Devpost - The home for hackathons](https://devpost.com/software/devangel)

---

## Accomplishments We’re Proud Of  
- A fully deployed dashboard with CI/CD integration.  [oai_citation:18‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- Real-time data visualisation without relying on any third-party charting libraries.  [oai_citation:19‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- A responsive, branded UI that works in both dark and light mode.  [oai_citation:20‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- A single, cohesive view that brings incidents, file impact, error insights and deployments all together.  [oai_citation:21‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- Live popup alerts that don’t block the user flow during incident response.  [oai_citation:22‡Devpost - The home for hackathons](https://devpost.com/software/devangel)

---

## What’s Next for DevAngel  
- Integrate the OpenAI API (or AWS Bedrock) for LLM-powered root-cause summaries.  [oai_citation:23‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- Add live CloudWatch streaming via Lambda + API Gateway.  [oai_citation:24‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- Implement rollback orchestration through Step Functions and GitHub Actions.  [oai_citation:25‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- Expand to multi-service dashboards for enterprise-scale monitoring.  [oai_citation:26‡Devpost - The home for hackathons](https://devpost.com/software/devangel)  
- Add Slack / SES / webhook integrations for incident notifications.  [oai_citation:27‡Devpost - The home for hackathons](https://devpost.com/software/devangel)

---

## Getting Started  
### Prerequisites  
- An AWS account with appropriate permissions (Lambda, S3, Step Functions, CloudWatch, etc)  
- Node.js + npm (or yarn) installed for the React frontend  
- GitHub account + repo access for the PR automation  
- Configure environment variables or AWS credentials locally (for example via `~/.aws/credentials`)

### Installation  
1. Clone the repo  
   ```bash
   git clone https://github.com/MatthiasMasiero/DevAngel.git
   cd DevAngel