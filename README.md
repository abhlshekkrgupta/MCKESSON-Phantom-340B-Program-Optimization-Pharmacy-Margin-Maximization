# 340B Program Optimization Engine (Phantom)

> **Deployed Context:** McKesson Corporation — Pharma Supply Chain Consulting Practice
> **Scale:** 2,500+ covered entities, 30,000+ contract pharmacies
> **Impact:** $340M incremental 340B savings identified across client base

---

## The Opportunity

The 340B Drug Pricing Program represents a 25-50% discount on drug acquisition for eligible covered entities. A drug with a WAC price of $5,200 may have a 340B ceiling price of $1,768. The spread between the 340B acquisition cost and commercial insurance reimbursement can generate margins of 60-80% on covered outpatient drugs.

But 80% of eligible prescriptions are missed due to operational complexity. Patient qualification requires satisfying a six-part federal test. Contract pharmacy arrangements must be optimized for geographic coverage within HRSA limits. Duplicate discount prevention with Medicaid requires precise claims-level coordination. GPO prohibition compliance demands drug-level purchasing segregation. Inventory must be tracked virtually or physically to prevent diversion.

This engine addresses every layer of the 340B optimization problem. It identifies eligible prescriptions that are currently being missed. It optimizes contract pharmacy networks for maximum patient capture. It prevents the compliance violations that trigger HRSA audit findings and manufacturer chargebacks. It computes the true margin waterfall from gross reimbursement through every cost layer to net profit.

---

## The Complexity

Patient definition rules, GPO prohibition, contract pharmacy arrangements, duplicate discount prevention — all interacting constraints that require systematic optimization to solve correctly.

A covered entity must establish that each 340B-eligible patient has a relationship with the entity, receives healthcare services from an employed or contracted provider, receives services within the entity's scope of grant, and has their care managed by the entity. These are legal determinations, not medical ones. Misclassifying a single patient can trigger a diversion finding.

Contract pharmacies are limited by entity type. DSH hospitals may have up to 35. Critical access hospitals may have up to 15. FQHCs may have up to 10. Each contract pharmacy must be within reasonable geographic proximity to the entity's patient population. Optimizing this network requires balancing coverage against HRSA limits.

Medicaid duplicate discounts are the single most common HRSA audit finding. When a state Medicaid program claims a rebate on a drug that was already discounted under 340B, the manufacturer experiences a duplicate discount. The covered entity is responsible for preventing this. The system must identify every Medicaid-eligible claim and either exclude it from 340B or ensure it is not rebate-eligible.

---

## Repository Structure

340b-optimization-engine
    src
        eligibility
            patient_qualification.py
            contract_pharmacy_optimizer.py
            grfc_exclusion_checker.py
        financial
            spread_calculator.py
            wac_to_340b_mapping.py
            margin_waterfall.py
        compliance
            duplicate_discount_detector.py
            hrda_audit_framework.py
            diversion_checker.py
        optimization
            contract_pharmacy_mip.py
            inventory_split_logic.py
    main.py
    README.md
    COMPLIANCE_NOTE.md
    requirements.txt
    LICENSE.md

---

## Key Technical Decisions

**Why the six-part test matters.** Patient qualification under 340B is a legal determination based on the patient's relationship with the covered entity, not a medical determination based on diagnosis or treatment. A prescription written by a community physician who happens to have privileges at the hospital does not qualify. A prescription from an employed physician for a patient whose care is managed by the entity does qualify. The distinction determines whether the discount applies. Getting it wrong is diversion.

**Why WAC-to-340B estimation is necessary.** HRSA publishes 340B ceiling prices in the OPAIS database, but access is restricted to covered entities and their authorized representatives. Consultants doing financial modeling often need to estimate 340B prices from observable WAC prices. Brand drugs typically have a 22-25% URA relative to AMP, yielding a 340B discount of 25-40% from WAC. Generics can have discounts exceeding 80% from WAC under the penny-pricing policy.

**Why duplicate discount detection is the audit priority.** When HRSA audits a covered entity, the first question is about Medicaid duplicate discount prevention. If the entity cannot demonstrate a system for excluding Medicaid claims from 340B or ensuring they are not rebate-eligible, the finding is automatic. Every covered entity needs a claims-level reconciliation process.

**Why inventory splitting matters.** Covered entities must prevent 340B drugs from being dispensed to ineligible patients. Physical segregation requires separate inventory storage. Virtual tracking requires NDC-level replenishment logic that matches 340B accumulation to 340B dispensing. Either approach must be auditable. The inventory split logic engine implements the virtual tracking approach with accumulation ratio monitoring.

---

## Dependencies

numpy>=1.24.0
scipy>=1.10.0
pandas>=2.0.0
scikit-learn>=1.3.0
statsmodels>=0.14.0

---

## Usage

from src.eligibility.patient_qualification import PatientQualificationEngine
from src.financial.spread_calculator import SpreadCalculator340B
from src.compliance.duplicate_discount_detector import DuplicateDiscountDetector
from src.optimization.contract_pharmacy_mip import ContractPharmacyMIP

Register covered entities with their provider rosters and grant scopes. Qualify patient encounters against the six-part test. Compute 340B spreads across payer mix. Detect duplicate discount risks. Optimize contract pharmacy network placement. Monitor inventory accumulation compliance.

---

## Author

**Abhishek Gupta** — Data Science Consultant

---



---
