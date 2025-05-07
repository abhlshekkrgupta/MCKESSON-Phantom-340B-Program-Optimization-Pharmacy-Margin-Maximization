import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

class GRFCExclusionChecker:
    """
    GPO prohibition compliance checker for 340B program.
    
    Disproportionate Share Hospitals, Children's Hospitals, and
    Free-Standing Cancer Hospitals are prohibited from obtaining
    covered outpatient drugs through a Group Purchasing Organization
    if they participate in 340B. This checker ensures compliance
    with the GPO exclusion requirement across the drug portfolio.
    """
    
    def __init__(self):
        self.gpo_excluded_entity_types = [
            "disproportionate_share_hospital",
            "childrens_hospital",
            "free_standing_cancer_hospital"
        ]
        self.gpo_contracts = {}
        self.exclusion_violations = []
    
    def register_entity(
        self,
        entity_id: str,
        entity_type: str,
        participates_in_340b: bool,
        has_gpo_contracts: bool
    ) -> Dict:
        is_excluded = entity_type in self.gpo_excluded_entity_types
        
        status = "compliant"
        violations = []
        
        if is_excluded and participates_in_340b and has_gpo_contracts:
            status = "violation"
            violations.append("GPO_EXCLUSION_VIOLATION")
        
        if not is_excluded and not participates_in_340b:
            status = "not_applicable"
        
        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "gpo_exclusion_applies": is_excluded,
            "status": status,
            "violations": violations
        }
    
    def check_drug_purchases(
        self,
        entity_id: str,
        drug_ndc: str,
        purchase_channel: str,
        purchase_date: str,
        is_covered_outpatient_drug: bool
    ) -> Dict:
        if not is_covered_outpatient_drug:
            return {
                "entity_id": entity_id,
                "drug_ndc": drug_ndc,
                "status": "exempt",
                "reason": "not_covered_outpatient_drug"
            }
        
        gpo_channels = ["gpo", "group_purchasing", "gpo_contract", "novation", "vizient", "premier"]
        
        if purchase_channel.lower() in gpo_channels:
            return {
                "entity_id": entity_id,
                "drug_ndc": drug_ndc,
                "purchase_date": purchase_date,
                "status": "potential_violation",
                "reason": "gpo_channel_used_for_covered_drug",
                "channel": purchase_channel
            }
        
        return {
            "entity_id": entity_id,
            "drug_ndc": drug_ndc,
            "status": "compliant",
            "channel": purchase_channel
        }
    
    def audit_gpo_compliance(
        self,
        entity_id: str,
        purchase_history: List[Dict],
        entity_type: str,
        participates_in_340b: bool
    ) -> Dict:
        entity_check = self.register_entity(
            entity_id, entity_type, participates_in_340b,
            has_gpo_contracts=True
        )
        
        if entity_check["status"] != "violation":
            return {
                "entity_id": entity_id,
                "status": entity_check["status"],
                "message": "GPO exclusion does not apply or entity not in 340B"
            }
        
        violations = []
        
        covered_outpatient_ndcs = set()
        for purchase in purchase_history:
            if purchase.get("is_covered_outpatient", False):
                covered_outpatient_ndcs.add(purchase.get("drug_ndc"))
        
        for purchase in purchase_history:
            check_result = self.check_drug_purchases(
                entity_id=entity_id,
                drug_ndc=purchase.get("drug_ndc", ""),
                purchase_channel=purchase.get("channel", ""),
                purchase_date=purchase.get("date", ""),
                is_covered_outpatient_drug=purchase.get("is_covered_outpatient", False)
            )
            
            if check_result["status"] == "potential_violation":
                violations.append({
                    **purchase,
                    "violation_type": "GPO_PURCHASE_OF_COVERED_DRUG"
                })
        
        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "status": "violations_found" if violations else "compliant",
            "n_violations": len(violations),
            "violations": violations,
            "total_purchases_reviewed": len(purchase_history),
            "covered_outpatient_ndcs": list(covered_outpatient_ndcs),
            "remediation_required": len(violations) > 0
        }
    
    def generate_remediation_plan(
        self,
        violations: List[Dict],
        entity_id: str
    ) -> Dict:
        affected_ndcs = list(set(v["drug_ndc"] for v in violations))
        affected_dates = [v.get("date", "") for v in violations]
        
        return {
            "entity_id": entity_id,
            "action": "terminate_gpo_contracts_for_covered_drugs",
            "affected_ndcs": affected_ndcs,
            "n_affected_drugs": len(affected_ndcs),
            "alternative_sourcing": "establish_wac_direct_accounts",
            "estimated_savings_impact": self._estimate_remediation_impact(affected_ndcs),
            "implementation_timeline_days": 90,
            "compliance_deadline": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        }
    
    def _estimate_remediation_impact(self, affected_ndcs: List[str]) -> float:
        avg_savings_per_drug = 35000
        return len(affected_ndcs) * avg_savings_per_drug * 0.12
