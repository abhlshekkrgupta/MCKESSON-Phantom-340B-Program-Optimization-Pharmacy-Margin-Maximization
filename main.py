"""
Phantom — 340B Program Optimization & Pharmacy Margin Maximization
McKesson Corporation — Pharma Supply Chain Consulting

Execution entry point for 340B eligibility determination,
financial spread analysis, compliance monitoring, and
contract pharmacy network optimization.
"""

import numpy as np
from src.eligibility.patient_qualification import PatientQualificationEngine
from src.eligibility.contract_pharmacy_optimizer import ContractPharmacyOptimizer
from src.eligibility.grfc_exclusion_checker import GRFCExclusionChecker
from src.financial.spread_calculator import SpreadCalculator340B
from src.financial.wac_to_340b_mapping import WACTo340BMapping
from src.financial.margin_waterfall import MarginWaterfall
from src.compliance.duplicate_discount_detector import DuplicateDiscountDetector
from src.compliance.hrda_audit_framework import HRSAAuditFramework
from src.compliance.diversion_checker import DiversionChecker
from src.optimization.contract_pharmacy_mip import ContractPharmacyMIP
from src.optimization.inventory_split_logic import InventorySplitLogic

np.random.seed(42)

print("=" * 65)
print("  PHANTOM — 340B Program Optimization Engine")
print("  McKesson Corporation — Pharma Supply Chain Consulting")
print("=" * 65)

print("
[1/6] Configuring covered entities and patient qualification...")

qual_engine = PatientQualificationEngine()

entities = [
    {
        "entity_id": "DSH_HOSPITAL_001",
        "entity_type": "disproportionate_share_hospital",
        "grant_scopes": ["hospital_outpatient", "hospital_inpatient", "hospital_emergency"],
        "provider_npis": [f"NPI_{i:010d}" for i in range(1, 51)],
        "site_addresses": ["MAIN_CAMPUS", "CLINIC_A", "CLINIC_B", "EMERGENCY_DEPT"],
        "eligible_services": ["oncology", "cardiology", "infectious_disease", "orthopedics", "primary_care"]
    },
    {
        "entity_id": "FQHC_002",
        "entity_type": "federally_qualified_health_center",
        "grant_scopes": ["federally_qualified_health_center", "outpatient_primary"],
        "provider_npis": [f"NPI_{i:010d}" for i in range(101, 121)],
        "site_addresses": ["FQHC_MAIN", "FQHC_SATELLITE_1"],
        "eligible_services": ["primary_care", "pediatrics", "mental_health", "obstetrics"]
    },
    {
        "entity_id": "CAH_003",
        "entity_type": "critical_access_hospital",
        "grant_scopes": ["critical_access", "hospital_outpatient", "hospital_emergency"],
        "provider_npis": [f"NPI_{i:010d}" for i in range(201, 211)],
        "site_addresses": ["CAH_MAIN"],
        "eligible_services": ["primary_care", "emergency", "surgery"]
    }
]

for entity in entities:
    result = qual_engine.register_covered_entity(**entity)
    print(f"  Registered: {result['entity_id']} ({result['entity_type']}) - {result['n_providers']} providers")

print("
[2/6] Running patient qualification on sample prescriptions...")

sample_prescriptions = []
for i in range(50):
    entity = entities[i % len(entities)]
    sample_prescriptions.append({
        "patient_id": f"PAT_{i:06d}",
        "prescribing_npi": entity["provider_npis"][i % len(entity["provider_npis"])],
        "service_location": entity["site_addresses"][i % len(entity["site_addresses"])],
        "service_type": entity["eligible_services"][i % len(entity["eligible_services"])],
        "encounter_date": "2025-06-15",
        "diagnosis_codes": ["E11.9", "I10"],
        "payer_type": "commercial_ppo"
    })

batch_result = qual_engine.batch_qualify_prescriptions("DSH_HOSPITAL_001", sample_prescriptions[:20])
print(f"  DSH_HOSPITAL_001: {batch_result['qualification_rate']:.0%} qualification rate")
print(f"  Qualified: {batch_result['qualified']}, Rejected: {batch_result['rejected']}")

print("
[3/6] Computing 340B spreads and financial impact...")

spread_calc = SpreadCalculator340B()

spread_calc.set_payer_mix("DSH_HOSPITAL_001", {
    "commercial_ppo": 0.35, "commercial_hmo": 0.15, "medicare_part_d": 0.20,
    "medicaid_mco": 0.15, "medicaid_ffs": 0.05, "medicare_advantage": 0.08, "uninsured": 0.02
})

spread_calc.load_drug_pricing("NDC_0001", wac_price=850.00, awp_price=1020.00, ceiling_price_340b=289.00, amp_price=680.00)
spread_calc.load_drug_pricing("NDC_0002", wac_price=3200.00, awp_price=3840.00, ceiling_price_340b=1088.00, amp_price=2560.00)
spread_calc.load_drug_pricing("NDC_0003", wac_price=12500.00, awp_price=15000.00, ceiling_price_340b=4250.00, amp_price=10000.00)

for ndc in ["NDC_0001", "NDC_0002", "NDC_0003"]:
    blended = spread_calc.compute_blended_spread("DSH_HOSPITAL_001", ndc, quantity=1, days_supply=30)
    print(f"  {ndc}: blended spread = ${blended['blended_spread']:,.2f}, margin = {blended['blended_margin_pct']:.1f}%")

wac_mapper = WACTo340BMapping()

drug_list = [
    {"ndc": "NDC_BRAND_001", "wac_price": 5200, "category": "oncology", "is_brand": True, "is_generic": False, "annual_volume": 1200},
    {"ndc": "NDC_GENERIC_001", "wac_price": 180, "category": "oral_solid", "is_brand": False, "is_generic": True, "annual_volume": 15000},
    {"ndc": "NDC_SPECIALTY_001", "wac_price": 8500, "category": "specialty", "is_brand": True, "is_generic": False, "annual_volume": 450}
]

price_estimates = wac_mapper.batch_estimate_prices(drug_list)
print(f"
  WAC to 340B estimates:")
print(f"    Total annual WAC spend: ${price_estimates['total_annual_wac_spend']:,.0f}")
print(f"    Total annual 340B spend: ${price_estimates['total_annual_340b_spend']:,.0f}")
print(f"    Total annual savings: ${price_estimates['total_annual_savings']:,.0f} ({price_estimates['average_discount_pct']:.1f}% avg discount)")

print("
[4/6] Checking compliance and detecting duplicate discount risk...")

dd_detector = DuplicateDiscountDetector()

for i in range(30):
    dd_detector.register_medicaid_claim(
        claim_id=f"CLAIM_MED_{i:05d}",
        ndc=f"NDC_{(i%3)+1:04d}",
        patient_id=f"PAT_{i:06d}",
        entity_id="DSH_HOSPITAL_001",
        date_of_service="2025-06-15",
        medicaid_id=f"MEDICAID_{i:08d}",
        rebate_eligible=(i % 4 != 0)
    )

for i in range(25):
    dd_detector.register_340b_claim(
        claim_id=f"CLAIM_340B_{i:05d}",
        ndc=f"NDC_{(i%3)+1:04d}",
        patient_id=f"PAT_{i:06d}",
        entity_id="DSH_HOSPITAL_001",
        date_of_service="2025-06-15",
        acquisition_type="340b_purchase",
        is_340b_eligible=True
    )

duplicates = dd_detector.detect_duplicates("DSH_HOSPITAL_001")
print(f"  Exact duplicates: {duplicates['n_exact_duplicates']}")
print(f"  Near duplicates: {duplicates['n_near_duplicates']}")
print(f"  Potential chargeback exposure: ${duplicates['potential_manufacturer_chargeback_exposure']:,.0f}")
print(f"  Requires immediate action: {duplicates['requires_immediate_action']}")

diversion_check = DiversionChecker()

for i in range(30):
    diversion_check.register_dispensing_event(
        entity_id="DSH_HOSPITAL_001",
        ndc=f"NDC_{(i%3)+1:04d}",
        patient_id=f"PAT_{i:06d}",
        prescribing_npi=f"NPI_{i%50+1:010d}",
        dispensing_location="MAIN_CAMPUS" if i < 25 else "OFF_SITE_UNKNOWN",
        date_dispensed="2025-06-15",
        is_340b_qualified=(i < 28),
        inventory_type="340b_purchased" if i < 25 else "non_340b",
        quantity=np.random.randint(1, 5)
    )

audit_result = diversion_check.audit_dispensing_patterns("DSH_HOSPITAL_001")
print(f"
  Diversion audit:")
print(f"    Records reviewed: {audit_result['n_records_reviewed']}")
print(f"    Potential diversion rate: {audit_result['diversion_rate']:.2%}")
print(f"    Program termination risk: {audit_result['program_termination_risk']}")

print("
[5/6] Optimizing contract pharmacy network...")

mip = ContractPharmacyMIP()

pharmacies = []
for i in range(50):
    pharmacies.append({
        "name": f"PHARMACY_{i:03d}",
        "location": [np.random.uniform(-0.5, 0.5), np.random.uniform(-0.5, 0.5)],
        "coverage_radius": np.random.uniform(3, 8),
        "setup_cost": np.random.uniform(3000, 15000),
        "estimated_volume": np.random.randint(200, 5000)
    })

patient_zones = []
for j in range(100):
    patient_zones.append({
        "zone_id": f"ZONE_{j:03d}",
        "centroid": [np.random.uniform(-0.5, 0.5), np.random.uniform(-0.5, 0.5)],
        "patient_volume": np.random.randint(50, 2000)
    })

mip.build_model(pharmacies, patient_zones, max_pharmacies=12, min_coverage_pct=0.75)
solution = mip.solve_greedy(max_pharmacies=12)

print(f"  Pharmacies selected: {solution['n_selected']}")
print(f"  Coverage achieved: {solution['coverage_pct']:.1f}%")
print(f"  Total setup cost: ${solution['total_setup_cost']:,.0f}")
print(f"  Estimated annual revenue: ${solution['estimated_annual_revenue']:,.0f}")
print(f"  Payback period: {solution['payback_months']:.1f} months")

print("
[6/6] Computing margin waterfall...")

waterfall = MarginWaterfall()

for ndc, pricing in [("NDC_0001", 289.00), ("NDC_0002", 1088.00), ("NDC_0003", 4250.00)]:
    result = waterfall.compute_margin_waterfall(
        entity_id="DSH_HOSPITAL_001",
        gross_reimbursement=spread_calc.drug_pricing[ndc]["awp"] * 0.82,
        drug_acquisition_cost=pricing,
        dispensing_cost_per_rx=12.50,
        n_prescriptions=100,
        tpa_fee_pct=0.05,
        distribution_fee_per_unit=2.50,
        n_units=100,
        inventory_carrying_days=21,
        annual_cost_of_capital=0.06
    )
    
    leakage = waterfall.identify_margin_leakage(result, {})
    print(f"  {ndc}: net margin = {result['net_margin_pct']:.1f}%, leakage = ${leakage['total_identified_leakage']:,.0f}")

print("
" + "=" * 65)
print("  ANALYSIS COMPLETE")
print("=" * 65)

total_340b_savings = price_estimates['total_annual_savings']
total_pharmacy_revenue = solution['estimated_annual_revenue']

print(f"
  Total identified 340B savings opportunity: ${total_340b_savings + total_pharmacy_revenue:,.0f}")
print(f"  Key recommendations:")
print(f"    1. Implement duplicate discount prevention rules immediately")
print(f"    2. Expand contract pharmacy network to {solution['n_selected']} locations")
print(f"    3. Review {duplicates['n_exact_duplicates']} duplicate discount claims")
print(f"    4. Address {len(leakage['leakage_points'])} margin leakage points")
print(f"    5. Validate patient qualification for all 340B-eligible prescriptions")
