import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

class DuplicateDiscountDetector:
    """
    Medicaid duplicate discount prevention engine.
    
    The single most common audit finding in 340B program audits.
    Federal law prohibits a manufacturer from providing both a
    340B discount AND a Medicaid drug rebate on the same drug
    claim. Covered entities must have systems to prevent this
    duplicate discount from occurring.
    
    This detector identifies claims at risk of duplicate discount
    before they result in manufacturer chargeback disputes or
    HRSA audit findings.
    """
    
    def __init__(self):
        self.medicaid_claims = {}
        self.claims_340b = {}
        self.duplicate_risk_log = []
    
    def register_medicaid_claim(
        self,
        claim_id: str,
        ndc: str,
        patient_id: str,
        entity_id: str,
        date_of_service: str,
        medicaid_id: str,
        rebate_eligible: bool
    ) -> Dict:
        key = f"{ndc}:{patient_id}:{date_of_service}"
        
        self.medicaid_claims[key] = {
            "claim_id": claim_id,
            "ndc": ndc,
            "patient_id": patient_id,
            "entity_id": entity_id,
            "date_of_service": date_of_service,
            "medicaid_id": medicaid_id,
            "rebate_eligible": rebate_eligible,
            "status": "registered"
        }
        
        return self.medicaid_claims[key]
    
    def register_340b_claim(
        self,
        claim_id: str,
        ndc: str,
        patient_id: str,
        entity_id: str,
        date_of_service: str,
        acquisition_type: str,
        is_340b_eligible: bool
    ) -> Dict:
        key = f"{ndc}:{patient_id}:{date_of_service}"
        
        self.claims_340b[key] = {
            "claim_id": claim_id,
            "ndc": ndc,
            "patient_id": patient_id,
            "entity_id": entity_id,
            "date_of_service": date_of_service,
            "acquisition_type": acquisition_type,
            "is_340b_eligible": is_340b_eligible,
            "status": "registered"
        }
        
        return self.claims_340b[key]
    
    def detect_duplicates(
        self,
        entity_id: str,
        lookback_days: int = 90
    ) -> Dict:
        duplicates = []
        
        for key, claim_340b in self.claims_340b.items():
            if claim_340b["entity_id"] != entity_id:
                continue
            
            if not claim_340b["is_340b_eligible"]:
                continue
            
            if key in self.medicaid_claims:
                medicaid_claim = self.medicaid_claims[key]
                
                if medicaid_claim["rebate_eligible"]:
                    duplicates.append({
                        "ndc": claim_340b["ndc"],
                        "patient_id": claim_340b["patient_id"],
                        "date_of_service": claim_340b["date_of_service"],
                        "claim_340b_id": claim_340b["claim_id"],
                        "medicaid_claim_id": medicaid_claim["claim_id"],
                        "medicaid_id": medicaid_claim["medicaid_id"],
                        "risk_level": "high",
                        "resolution": "exclude_from_340b_or_medicaid_rebate"
                    })
        
        near_matches = self._detect_near_duplicates(entity_id, lookback_days)
        
        all_duplicates = duplicates + near_matches
        
        return {
            "entity_id": entity_id,
            "n_exact_duplicates": len(duplicates),
            "n_near_duplicates": len(near_matches),
            "total_duplicate_risk": len(all_duplicates),
            "duplicates": all_duplicates,
            "requires_immediate_action": len(duplicates) > 0,
            "potential_manufacturer_chargeback_exposure": len(duplicates) * 8500
        }
    
    def _detect_near_duplicates(
        self,
        entity_id: str,
        lookback_days: int
    ) -> List[Dict]:
        near_matches = []
        
        for key_340b, claim_340b in self.claims_340b.items():
            if claim_340b["entity_id"] != entity_id:
                continue
            if not claim_340b["is_340b_eligible"]:
                continue
            
            ndc = claim_340b["ndc"]
            patient_id = claim_340b["patient_id"]
            
            for key_med, claim_med in self.medicaid_claims.items():
                if claim_med["entity_id"] != entity_id:
                    continue
                if not claim_med["rebate_eligible"]:
                    continue
                
                if claim_med["ndc"] == ndc and claim_med["patient_id"] == patient_id:
                    continue
                
                if claim_med["patient_id"] == patient_id and self._dates_within_window(
                    claim_340b["date_of_service"], claim_med["date_of_service"], lookback_days
                ):
                    near_matches.append({
                        "ndc_340b": ndc,
                        "ndc_medicaid": claim_med["ndc"],
                        "patient_id": patient_id,
                        "date_340b": claim_340b["date_of_service"],
                        "date_medicaid": claim_med["date_of_service"],
                        "risk_level": "medium",
                        "resolution": "verify_dispensing_event_distinct"
                    })
        
        return near_matches
    
    def _dates_within_window(self, date1: str, date2: str, window_days: int) -> bool:
        try:
            d1 = datetime.strptime(date1, "%Y-%m-%d")
            d2 = datetime.strptime(date2, "%Y-%m-%d")
            return abs((d1 - d2).days) <= window_days
        except ValueError:
            return False
    
    def generate_prevention_rules(self, entity_id: str) -> Dict:
        return {
            "entity_id": entity_id,
            "rules": [
                {
                    "rule_id": "DD_001",
                    "description": "Medicaid FFS claims must be excluded from 340B if rebate-eligible",
                    "implementation": "Configure split-billing software to carve out Medicaid FFS",
                    "priority": "critical"
                },
                {
                    "rule_id": "DD_002",
                    "description": "Medicaid MCO claims require state-specific determination",
                    "implementation": "Check state Medicaid MCO 340B policy before including",
                    "priority": "high"
                },
                {
                    "rule_id": "DD_003",
                    "description": "Maintain auditable records of Medicaid exclusion decisions",
                    "implementation": "Document carve-out rationale for each Medicaid claim type",
                    "priority": "high"
                },
                {
                    "rule_id": "DD_004",
                    "description": "Reconcile 340B accumulator against Medicaid rebate files monthly",
                    "implementation": "Cross-reference 340B claims against state rebate files",
                    "priority": "medium"
                }
            ]
        }
