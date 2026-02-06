# Example User Prompts – processIQ

---

## 1. High-quality, well-structured
**Enterprise / High impact**

We are a multinational manufacturing company (~4,500 employees) and want to analyze our **procurement-to-payment process** for inefficiencies.

### Current workflow
1. A production planner creates a purchase requisition in SAP.
2. The requisition is reviewed by the department manager and then by finance.
3. After approval, procurement converts it into a purchase order and sends it to the supplier.
4. The supplier sends an order confirmation by email.
5. Goods are delivered to the warehouse and manually checked against the purchase order.
6. The warehouse posts the goods receipt in SAP.
7. The supplier sends the invoice via PDF email.
8. Accounts payable manually matches invoice, purchase order, and goods receipt.
9. Finance schedules the payment.

### Issues
- Approval steps take too long and often get stuck.
- Manual invoice matching causes delays and errors.
- Lack of transparency regarding where requisitions are blocked.

### Goal
- Reduce cycle time and manual effort.
- Improve visibility and control.

Please analyze this process, identify bottlenecks, and suggest improvement opportunities (automation or process redesign).

---

## 2. Medium quality, partial information
**Mid-size company / Medium impact**

I work at a logistics company with around 120 employees. We’re struggling with how we handle **customer onboarding and contract setup**.

### Current situation
- Sales closes a deal and sends the details by email to operations.
- Operations creates the customer in our TMS.
- Finance is informed separately to set up billing.
- Compliance checks are sometimes done before onboarding and sometimes after.
- Customers often complain that it takes too long until shipments can start.

### Problems
- A lot of back-and-forth emails.
- Unclear ownership and responsibilities.
- Errors in customer data lead to billing issues later.

We want to understand where the process is breaking down and how to make onboarding faster and more reliable.

---

## 3. Low quality, vague, messy
**Small business / Low but very visible impact**

We’re a small digital agency (8 people) and our internal processes are kind of a mess.

When a new project comes in, someone talks to the client, then files get shared somewhere, tasks are created at some point, invoices are sent later, and sometimes we forget things.

There’s no fixed order and everyone does it differently. Sometimes projects are profitable, sometimes not, and we don’t really know why.

Can you take a look at this and tell us what’s wrong and what we should fix?

---

# Example User Prompt – Complex Workflow (Gold Standard)

## Company context
We are a **mid-to-large healthcare services provider** operating diagnostic labs and outpatient clinics across multiple regions (~1,200 employees).

We want to analyze and improve our **patient billing and insurance reimbursement workflow**, which is complex, non-linear, and prone to delays and errors.

---

## Workflow overview

Each step includes:
- **Average time**
- **Average cost per case**
- **Estimated error rate**
- **Dependencies on previous steps**

### 1. Patient appointment scheduled
- Time: 5 minutes
- Cost: €2
- Error rate: 1%
- Depends on: —

### 2. Patient demographic data entered
- Time: 10 minutes
- Cost: €5
- Error rate: 4%
- Depends on: Step 1

### 3. Insurance information collected
- Time: 8 minutes
- Cost: €4
- Error rate: 6%
- Depends on: Step 1

### 4. Insurance eligibility check (automated)
- Time: 2 minutes
- Cost: €1
- Error rate: 3%
- Depends on: Step 3

### 5. Manual insurance verification (if eligibility unclear)
- Time: 15 minutes
- Cost: €12
- Error rate: 5%
- Depends on: Step 4
- Triggered if: Step 4 fails

### 6. Appointment confirmation sent to patient
- Time: 1 minute
- Cost: €0.50
- Error rate: 1%
- Depends on: Step 2, Step 4 or Step 5

### 7. Patient visit / service delivery
- Time: 60 minutes
- Cost: €80
- Error rate: 2%
- Depends on: Step 6

### 8. Clinical documentation completed by provider
- Time: 20 minutes
- Cost: €25
- Error rate: 7%
- Depends on: Step 7

### 9. Coding of procedures (CPT / ICD)
- Time: 15 minutes
- Cost: €18
- Error rate: 8%
- Depends on: Step 8

### 10. Internal documentation quality check
- Time: 10 minutes
- Cost: €10
- Error rate: 4%
- Depends on: Step 9

### 11. Documentation sent back for correction
- Time: 30 minutes
- Cost: €20
- Error rate: 3%
- Depends on: Step 10
- Triggered if: Step 10 fails

### 12. Claim created in billing system
- Time: 5 minutes
- Cost: €4
- Error rate: 2%
- Depends on: Step 9 or Step 11

### 13. Claim submitted to insurance
- Time: 2 minutes
- Cost: €1
- Error rate: 1%
- Depends on: Step 12

### 14. Insurance claim adjudication
- Time: 14 days
- Cost: €0
- Error rate: 10%
- Depends on: Step 13

### 15. Claim rejection received
- Time: 5 minutes
- Cost: €2
- Error rate: 1%
- Depends on: Step 14
- Triggered if: Claim is rejected

### 16. Claim analysis and rework
- Time: 25 minutes
- Cost: €22
- Error rate: 6%
- Depends on: Step 15

### 17. Claim resubmission
- Time: 3 minutes
- Cost: €1
- Error rate: 2%
- Depends on: Step 16

### 18. Payment received from insurance
- Time: 1 day
- Cost: €0
- Error rate: 1%
- Depends on: Step 14 or Step 17

### 19. Patient invoicing for remaining balance
- Time: 5 minutes
- Cost: €3
- Error rate: 3%
- Depends on: Step 18

### 20. Payment reconciliation and case closure
- Time: 10 minutes
- Cost: €6
- Error rate: 2%
- Depends on: Step 18, Step 19

---

## Known issues and concerns
- High rejection rates due to coding and documentation errors.
- Long end-to-end cycle time because of insurance adjudication and rework loops.
- Significant manual effort in verification, correction, and rework steps.
- Poor transparency for finance on where cases are delayed.

---

## Goal
We want to:
- Reduce end-to-end billing cycle time.
- Lower error rates and rework.
- Identify automation and decision-support opportunities.
- Understand cost and delay drivers across the workflow.

Please analyze this workflow, identify bottlenecks, rework loops, cost drivers, and suggest concrete improvement measures.
