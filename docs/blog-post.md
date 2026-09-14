# Agents for Humans: building Refund Hunter, an agent that collects the small refunds you're owed

*Post for builder.aws.com. Title must contain "Agents for Humans". Publish publicly before the deadline.*

---

Stores owe people money all the time. Target refunds the difference when its own price drops within 14 days of your order. Costco gives you 30 days. Amazon refunds the shipping fee when it misses a guaranteed delivery date. Grocery delivery apps credit late orders.

Almost nobody collects it. For a $22 air fryer you would have to notice the price dropped, know the rule, find the order number, write the email, and chase the reply. So the money stays with the store.

For the AWS Agents for Humans hackathon I built **Refund Hunter**: an agent that reads your receipts, finds the refunds you are owed, and files the claim once you say yes. If it finds nothing, you never hear from it. Code is MIT on GitHub: https://github.com/fakemovement/refund-hunter

## What it does

Once a day, in the background:

1. **Reads mail.** Order confirmations, shipping notices, delivery notices. Newsletters and personal mail are ignored.
2. **Knows the rules.** A small editable policy table: price-adjustment windows, what a missed delivery earns, where to send the claim.
3. **Checks every open purchase.** Today's price versus what you paid. Delivery date versus the promised date.
4. **Asks one question when it finds money.** "Target dropped your air fryer by $22, 9 days into the 14-day window. File it?" Yes or skip.
5. **Files the claim and follows up.** The email has the order number, the dates, the rule, the amount. Five quiet days later, one polite nudge.

## How it's built

Two agents on the **Strands Agents SDK**, running Claude Sonnet 4.6 on **Amazon Bedrock**.

**The Receipt Reader** uses Strands structured output. It turns a batch of raw emails into a Pydantic `Extraction`: purchases with merchant, item, price, order date, promised delivery, and delivery updates with the actual date. It is told never to invent a value; a missing date stays empty.

**The Hunter** is a Strands `Agent` with five `@tool` tools that share a `State` object through `invocation_state`:

- `list_open_purchases`, `lookup_policy`, `check_price`, `close_purchase`
- `file_claim`, which is where the hackathon theme lives.

### The interrupt is the product

The brief asked for agents that "run autonomously and only surface when there's a real decision to make." Strands has a primitive for exactly that. Inside `file_claim`:

```python
decision = tool_context.interrupt(
    f"approve_claim_{purchase.id}_{kind}",
    reason={"claim": claim.model_dump(), "question": question, "options": ["approve", "skip"]},
)
```

The agent stops mid-tool. `AgentResult.stop_reason` is `"interrupt"`, and the dashboard shows the question. When the person answers, the same agent is rebuilt with the same session manager and invoked with an `interruptResponse`. The tool re-runs from the top, `interrupt()` returns the answer instead of raising, and the claim email goes out. `FileSessionManager` locally and `S3SessionManager` on AgentCore make the pause survive hours or days.

Two details that took real thought:

- **Tools re-run on resume**, so anything created before the interrupt must have a deterministic id. Claim ids are `clm_<purchase>_<kind>`.
- **Several claims can be waiting at once.** Strands wants a response for every open interrupt in the session. When the person answers only one, the others are answered `"pending"` and the tool raises a fresh interrupt under a new name, so each claim keeps waiting for its own answer.

### On AWS

- **Amazon Bedrock AgentCore Runtime** hosts the agents (CodeZip, Python 3.12). One entrypoint, three actions: `run`, `decide`, `state`.
- **DynamoDB** holds the state: purchases, claims, decisions, sent emails, run reports. One document per user.
- **S3** holds the paused agent sessions.
- **EventBridge Scheduler** wakes the runtime once a day through the universal target `bedrockagentcore:invokeAgentRuntime`. No pollers, no idle compute; a day costs pennies.
- **CloudWatch and AgentCore observability** for logs and traces.

The dashboard is a single FastAPI page. Locally it runs the agents in-process; deployed, it forwards `run` and `decide` to the runtime and reads state from DynamoDB.

## What I learned

- Interrupts are the right primitive for "surfaces only for real decisions." Everything else was plumbing.
- Policy knowledge belongs in an editable YAML table, not in a prompt. The agent reasons over it; a human maintains it.
- A synthetic inbox with dates relative to "today" means the demo always lands inside the stores' windows, whenever a judge runs it.

## What's next

Real store support addresses and a chat-paste mode, credit-card price-protection benefits, airline delay compensation, and reading the store's reply to close the loop automatically.

Repo: https://github.com/fakemovement/refund-hunter
