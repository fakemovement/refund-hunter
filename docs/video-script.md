# Refund Hunter, 5-minute video script

Record at 1080p. Screen recording of the dashboard + a few slides. Talk slowly; 4 min 30 is the target.

## 0:00 to 0:40, the problem (slide or talking head)

"Stores owe you money more often than you think. Target will refund the difference if their price drops
within 14 days of your order. Costco gives you 30 days. Amazon refunds the shipping you paid when it
misses a guaranteed delivery date. Instacart credits late orders.

Almost nobody collects it. You'd have to notice the price dropped, know the rule, find the order number,
write the email, and chase the reply. For a $22 air fryer, nobody does that. So the money stays with the
store."

## 0:40 to 1:10, who and why (slide)

"Refund Hunter is for anyone who shops online. It's an agent that reads your receipts, checks every
store's rules and prices in the background, and asks you exactly one question when it finds money:
file it, or skip it. If there's nothing to claim, you never hear from it. Built with the Strands Agents
SDK and running on Amazon Bedrock AgentCore."

## 1:10 to 2:20, the daily run (dashboard)

- Open the dashboard, empty state. "This is Sam's inbox: a dozen emails from the last three weeks.
  Orders from Target, Costco, Amazon, Best Buy, Walmart, Home Depot, a newsletter, a note from a
  friend."
- Press **Run today's check**. While it works (30 s): "The first agent, the Receipt Reader, turns
  those emails into purchases: what, where, how much, when, promised delivery. The second agent, the
  Hunter, looks up each store's policy, checks today's price, compares delivery dates, and decides."
- The run finishes. Show the **Purchases** table: six purchases, Best Buy closed "outside the 15-day
  window", Walmart closed "no price adjustment, delivered on time".
- Show the **Needs you** panel: three questions. Read one: "Target: paid $129.99 nine days ago,
  now $107.99, inside the 14-day window. Claim $22?"

## 2:20 to 3:20, the human decision (dashboard)

"This is the part that matters. The agent didn't send anything. Filing a claim raises a Strands
interrupt: the agent stops mid-tool, the question lands here, and it waits, for hours or days if it
has to, because the session is saved."

- Tap **Yes, file it** on Costco ($50). Wait 5 s. Open **Emails the agent sent**: show the email
  with the order number, the dates, the rule, the amount.
- Tap **Skip** on Target. "Maybe I don't want to bother for $22. Skipped, remembered, no email."
- Tap **Yes** on Amazon ($12.99 late delivery). "Two days late on a guaranteed date. Shipping refunded."
- Point at the tiles: money found, claims filed.

## 3:20 to 3:50, background and follow-up

"Every morning EventBridge wakes the agent on AgentCore. New receipts get read, prices get
re-checked while purchases are still inside their windows, and any claim the store hasn't answered in
five days gets one polite follow-up. The person only sees the dashboard when there's a decision."

Show the **Runs** log briefly, then the AgentCore console (runtime READY, a trace).

## 3:50 to 4:30, architecture (diagram slide)

"Two Strands agents. The Reader uses structured output. The Hunter has five tools, and one of them,
file_claim, raises the interrupt. State lives in DynamoDB, the paused agent in S3, the model is Claude
on Bedrock, the schedule is EventBridge. Everything in the demo is synthetic data, and the same code
reads a real Gmail inbox over IMAP."

## 4:30 to 4:50, close

"Refund Hunter: the agent that collects the small money you're owed, and only talks to you when it
needs a yes. Code is MIT on GitHub."
