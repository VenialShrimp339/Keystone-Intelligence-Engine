# Worked Examples: Minto-Derived Issue-Tree Shapes

These examples are paraphrased into reusable evaluation forms. They are not source text reproductions.

## Example 1: Customer Billing Change Request

### Visible Executor Prompt

A major customer asks to change the billing process. Instead of the supplier processing delivery tickets, issuing a bill, receiving payment, and then posting payment weeks later, the customer wants to keep the tickets, record them electronically, calculate the monthly total, and send the payment with a data file. The head of accounting is asked whether the change makes sense. Build the issue tree for the response.

### Hidden Reference Logic

The governing question is whether the proposed process change is a good idea. The answer can be supported by reasons, not by describing process mechanics. The key branches should prove that the new process gives the supplier the information it needs, improves cash timing, and reduces internal workload. Implementation details sit below those reasons.

### Reusable Tree Shape

```text
Should we accept the customer's proposed billing change?
|-- It preserves the information needed to process and control the account
|   |-- Required identifiers and ticket-level fields can be captured
|   |-- Data can be formatted for the existing posting process
|   `-- Balancing controls can verify payment against ticket detail
|-- It improves economics or cash timing
|   |-- Payment arrives with the file
|   `-- Billing cycle time shrinks materially
`-- It reduces supplier workload
    |-- Manual ticket processing declines
    `-- Exceptions can be isolated rather than reprocessed wholesale
```

### Hidden Grading Properties

Good answers identify the decision question first, avoid listing mechanics as the top branches, and support the recommendation with reasons. The strongest answers distinguish control requirements from benefits and put process details below the relevant reason. Common traps are writing a process description, mixing implementation steps with reasons, or failing to say whether the change should be accepted.

## Example 2: Distribution Capacity Strategy

### Visible Executor Prompt

A retailer operates three distribution centers plus rented overflow space. The centers were designed to serve roughly the current store base, but actual demand already strains them. Store count and volume are expected to grow materially over the next two years. Management can expand existing centers, build a new center, upgrade handling methods, or keep using third parties. It wants enough capacity while minimizing capital, operating cost, and disruption to its full-line distribution model. Build the issue tree.

### Hidden Reference Logic

The governing question is which distribution strategy to choose among known alternatives. The answer should not be a generic warehouse analysis. It should evaluate paths against the desired result and constraints, then recommend an incremental capacity approach if supported. The tree should separate capacity sufficiency, economics, operating model continuity, and implementation timing.

### Reusable Tree Shape

```text
Which distribution strategy should the retailer adopt?
|-- Capacity: which option closes the two-year capacity gap with enough timing slack?
|   |-- Expand existing nodes
|   |-- Add a new node
|   |-- Increase throughput through process or handling changes
|   `-- Use third-party capacity selectively
|-- Economics: which option minimizes capital and operating cost for the same service level?
|   |-- Up-front capital required
|   |-- Unit handling and transport cost
|   `-- ROI impact under growth scenarios
|-- Operating model: which option preserves the full-line strategy and processing speed?
|   |-- Service-level consistency
|   |-- Complexity added to replenishment
|   `-- Dependence on third parties
`-- Timing and reversibility: which option avoids premature irreversible capacity?
    |-- Lead time to execute
    |-- Ability to stage decisions
    `-- Trigger points for adding the next increment
```

### Hidden Grading Properties

Good answers turn the alternatives into a decision tree governed by criteria. They show how the desired result defines the criteria, and they avoid treating alternatives as isolated essays. Excellent answers include trigger-based staging and recognize that incremental capacity can preserve option value. Common traps are recommending a new warehouse because capacity is short, ignoring processing methods, or failing to distinguish capital outlay from operating cost.

## Example 3: Sales Decline After Long Stable Growth

### Visible Executor Prompt

A company has grown sales steadily for many years using a stable sales process: identify prospects, prepare a sales script, and deliver the pitch. Recent projections show sales will decline instead of continuing to grow. Management wants to restore growth quickly. Build a diagnostic issue tree and a pruned research plan.

### Hidden Reference Logic

The problem is a gap between expected continued growth and projected decline. Likely causes lie inside the sales process that had previously produced growth. The diagnostic tree should inspect the prospect list, the message, and the delivery. The pruned plan should test the easiest or most likely failure points first, then proceed to deeper causes.

### Reusable Tree Shape

```text
Why are projected sales falling below expected growth?
|-- Prospect universe problem
|   |-- List no longer covers the right buyers
|   |-- Demand pool has changed
|   `-- Prior conversion assumptions no longer hold
|-- Message problem
|   |-- Script no longer matches buyer priorities
|   |-- Offer differentiation has weakened
|   `-- Objections are not addressed
`-- Delivery problem
    |-- Salespeople are not reaching prospects effectively
    |-- Pitch execution quality has declined
    `-- Channel or format is no longer persuasive
```

### Pruned Research Plan

```text
1. Test whether the list still maps to buyers with current demand.
2. Test whether conversion falls before, during, or after the pitch.
3. Test whether message changes restore conversion in the weakest segment.
```

### Hidden Grading Properties

Good answers derive the diagnostic branches from the existing sales process, not from generic sales frameworks. They state R1 and R2 explicitly and avoid jumping directly to solutions. Strong answers attach observable tests to each cause. Common traps are broad PEST or market-factor trees that ignore the known process, or premature recommendations like "increase marketing" without diagnosis.

## Example 4: Information Systems Division Cannot Keep Up With Growth

### Visible Executor Prompt

A fast-growing manufacturing division uses new planning and control systems that are not working smoothly. Orders are late, required parts are missing, users may not understand the systems, and support groups appear unproductive. Management wants production capability and support productivity to cope with expected growth. Build an analysis structure.

### Hidden Reference Logic

The opening scene is a production planning and control system. A diagnostic framework should map the process rather than start with a broad data request list. Questions should test order inputs, purchased items, stock availability, capacity, dispatching, controls, and management reporting. Each issue should be answerable yes/no.

### Reusable Tree Shape

```text
Why can't the production system support expected growth?
|-- Demand and order inputs
|   |-- Are lead-time promises realistic?
|   `-- Are order priorities clear and stable?
|-- Materials availability
|   |-- Are purchased items delayed or too costly?
|   |-- Are stock-outs constraining production?
|   `-- Are inventory records accurate enough for planning?
|-- Capacity and scheduling
|   |-- Is capacity adequate for forecast demand?
|   |-- Are load formulas and routing data accurate?
|   `-- Are dispatch rules creating bottlenecks?
|-- User adoption and process discipline
|   |-- Do users understand the new system?
|   `-- Are procedures followed consistently?
`-- Management control
    |-- Do reports expose the right exceptions?
    `-- Are local controls increasing total system cost?
```

### Hidden Grading Properties

Good answers model the operating system first, then derive data needs from the model. They should avoid dumping a shopping list of interviews and metrics. Strong answers state what evidence would confirm or eliminate each branch and identify upstream constraints before downstream symptoms. Common traps are treating "user training" as the whole problem or confusing data-gathering categories with diagnostic branches.

## Example 5: Inventory Cost Too High in a Distribution Business

### Visible Executor Prompt

A pipe-and-fittings distributor has a central warehouse supplying regional warehouses. Inventory in the central warehouse is expensive, and some stock-outs cause regions to order directly from suppliers. New owners believe the inventory investment is too high and want to reduce it without damaging customer service. Build the issue tree.

### Hidden Reference Logic

The first issue is whether current inventory exceeds the level needed to meet service objectives. If yes, causes can be mapped to ordering too much, holding too long, stocking the wrong items, or compensating for poor service from the central system. The output should separate the target inventory level from causes of excess.

### Reusable Tree Shape

```text
Can the distributor reduce inventory investment without hurting service?
|-- Required level: is current inventory above what service targets require?
|   |-- Target service levels by product and region
|   |-- Demand variability and replenishment lead times
|   `-- Safety stock requirements
|-- Ordering behavior: are we ordering more than required?
|   |-- Forecasting and reorder parameters
|   |-- Regional direct-order triggers
|   `-- Central replenishment rules
|-- Holding behavior: are we keeping inventory too long?
|   |-- Obsolete and slow-moving stock
|   |-- Product proliferation
|   `-- Write-off and disposal discipline
`-- Network design: is centralization still cost-effective?
    |-- Central versus regional stock economics
    |-- Service impact of central stock-outs
    `-- Supplier lead-time and shipment economics
```

### Hidden Grading Properties

Good answers convert "inventory issues" into testable yes/no questions. They first establish the right target before diagnosing excess. Strong answers distinguish current-state diagnosis from future network design. Common traps are assuming centralization is bad, treating direct regional orders only as noncompliance, or failing to preserve customer service as a constraint.

## Example 6: Energy Cost Reduction in a Factory

### Visible Executor Prompt

A factory wants to reduce energy costs. Proposed areas include operating practices, low-capital fixes, capital projects, fuel mix, sourcing, government incentives, organization, product-to-mill assignment, and an energy strategy. Build a clean issue tree and identify likely irrelevant or secondary branches.

### Hidden Reference Logic

The root is reducing energy cost. The logical breakdown should split units consumed from cost per unit, then break each into equipment, operations, fuel choices, and sourcing. Organization, government programs, and assignment questions may matter only as enablers or constraints, not as peer branches unless they directly change cost.

### Reusable Tree Shape

```text
How can the factory reduce energy costs?
|-- Reduce energy units consumed
|   |-- Repair, maintain, or insulate existing equipment
|   |-- Modify existing equipment
|   |-- Improve operating practices
|   `-- Design or buy equipment that uses less energy
|-- Reduce cost per energy unit
|   |-- Switch to lower-cost fuels where feasible
|   |-- Improve sourcing contracts
|   `-- Add equipment compatible with lower-cost energy inputs
`-- Enable and sequence the program
    |-- Capital evaluation and prioritization
    |-- Operating accountability
    `-- External funding or regulatory opportunities
```

### Hidden Grading Properties

Good answers use a driver tree rather than a list of named initiatives. They place enablers beneath the cost-reduction levers unless the prompt makes them decisive constraints. Strong answers include benefit, capital intensity, and implementation risk for pruning. Common traps are making "strategy" a branch without content, mixing cost levers with governance topics, or omitting the distinction between consumption and unit cost.
