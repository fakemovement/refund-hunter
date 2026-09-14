# Submission checklist (deadline Mon Sep 14, 5:00 PM PT; aim for 1 PM)

## 1. Record the video (30 to 45 min)

1. Open two terminals in `refund-hunter/backend`:
   ```
   .venv\Scripts\refundhunter reset
   .venv\Scripts\refundhunter serve
   ```
   Open http://127.0.0.1:8000 in a clean browser window (no bookmarks bar, 1280 px wide or more).
2. Have `backend/fixtures/inbox.json` open in another tab to show the "inbox" for 5 seconds.
3. Follow `docs/video-script.md`. Press **Run today's check** once (about 30 to 40 s), then approve
   Costco, skip Target, approve Amazon, approve Instacart. Open one sent email.
4. Show the AgentCore console (Bedrock > AgentCore > Runtimes > RefundHunter_Hunter) and the
   architecture diagram `docs/architecture.png`.
5. Keep it under 5:00. Upload to YouTube as **Public** (not unlisted). Title:
   "Refund Hunter - Agents for Humans Hackathon (Strands Agents + AgentCore)".

## 2. Devpost form

- Project name: Refund Hunter
- Tagline and description: copy from `docs/devpost.md`
- Track: Everyday Agents
- Repo: https://github.com/fakemovement/refund-hunter (public, MIT visible in About)
- Video: the YouTube link
- Architecture diagram: upload `docs/architecture.png` as a project image (also in the README)
- Screenshots: `docs/dashboard.png`
- AWS Builder ID email: the one on your Builder ID
- Live demo link: https://nj9f6ojm51.execute-api.us-east-1.amazonaws.com/
  (Lambda + function URL, wired to the AgentCore runtime; Reset is hidden there unless you open it with `#admin`)
- Pre-existing code disclosure: "Deployment config (AgentCore CDK scaffold) reused from my earlier
  project; all agent code written during the submission period."
- Built with: Python, Strands Agents SDK, Amazon Bedrock, AgentCore Runtime, DynamoDB, S3,
  EventBridge Scheduler, FastAPI

## 3. Before you press submit

- [ ] Video plays publicly in an incognito window
- [ ] Repo README shows the diagram and the dashboard screenshot
- [ ] `git status` clean, last commit pushed
- [ ] Submit by 1 PM PT, not 4:59
