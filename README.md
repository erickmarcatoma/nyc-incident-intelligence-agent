# Daily Risk Briefer

An automated AI agent for municipal operations that monitors localized street safety, detects hazard clusters, and delivers a ranked daily risk report of motor vehicle collisions[cite: 1, 2].

## 📖 Overview

Municipal operations managers currently rely on weekly manual data pulls from the massive NYC Open Data portal to track motor vehicle collisions, creating a 7-day blind spot in identifying emerging crash clusters. 

The **Daily Risk Briefer** shifts street safety monitoring from a slow weekly chore to a daily proactive check:
* **Automated Data Fetching:** Runs automatically on a daily schedule (e.g., 7:00 AM) using the `query_nyc_open_data` tool to fetch the prior 24 hours of collision data via the Socrata REST API.
* **Cluster Detection:** Groups incidents by exact intersection (`on_street_name` and `cross_street_name`) to instantly distinguish acute hazards from routine accidents.
* **Time Savings:** Recovers 2-3 hours per week per district manager while reducing the threat detection turnaround from 7 days to 24 hours.

## 🚨 Risk Thresholds & Reporting

The agent processes collision data using strict mathematical rules to generate a 3-part briefing:

1. **URGENT HAZARDS:** Flags intersections meeting at least one of the following criteria:
   * **Frequency:** 2 or more collisions occurred at the exact intersection.
   * **Severity:** A crash resulted in $\ge 3$ `number_of_persons_injured` OR $\ge 1$ `number_of_persons_killed`.
2. **ROUTINE INCIDENTS:** Briefly summarizes the total count of non-urgent crashes without listing them individually.
3. **PRIMARY CAUSES:** Summarizes the most common `contributing_factor_vehicle_1` across all fetched records.

## 🛠 Setup & Installation

This project requires a standard Python environment and an `.env` file to manage API credentials securely.

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd daily-risk-briefer
Set up the virtual environment:

Bash
python3 -m venv .venv
source .venv/bin/activate
Configure environment variables:

Bash
cp .env.example .env
Do not commit the .env file. Populate it with your LLM API keys and your Socrata API credentials if required.

🛡️ Safeguards & Blast Radius
Because this agent operates in a municipal safety context, strict safeguards are in place:   
PDF

Read-Only: The tool is strictly read-only and cannot alter official NYPD records.   
PDF

No Data Fabrication: The system prompt strictly prohibits inventing crash data; if the API fails or no records are found, the agent must output "No collisions reported or unable to retrieve data".

Graceful Degradation: A Python try-except block in the tool prevents stack trace leaks by returning a clean failure string during Socrata API timeouts.

👥 Owners
James Alvarado
Erick Marcatoma

