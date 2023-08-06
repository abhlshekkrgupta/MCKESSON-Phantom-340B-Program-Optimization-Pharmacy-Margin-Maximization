import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

class DiversionChecker:
    """
    340B drug diversion detection engine.
    
    Diversion occurs when 340B-purchased drugs are dispensed to
    patients who do not qualify as 340B-eligible patients of the
    covered entity. This is the most serious compliance violation
    and carries potential program termination.
    
    This checker monitors dispensing patterns, identifies anomalous
    transactions, and flags potential diversion scenarios before
    they result in audit findings or manufacturer investigations.
    """
    
    def __init__(self):
        self.dispensing_records = []
        self.diversion_flags = []
    
    def register_dispensing_event(
        self,
        entity_id: str,
        ndc: str,
        patient_id: str,
        prescribing_npi: str,
        dispensing_location: str,
        date_dispensed: str,
        is_340b_qualified: bool,
        inventory_type: str,
        quantity: int
    ) -> Dict:
        record = {
            "entity_id": entity_id,
            "ndc": ndc,
            "patient_id": patient_id,
            "prescribing_npi": prescribing_npi,
            "dispensing_location": dispensing_location,
            "date_dispensed": date_dispensed,
            "is_340b_qualified": is_340b_qualified,
            "inventory_type": inventory_type,
            "quantity": quantity,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.dispensing_records.append(record)
        return record
    
    def check_diversion_risk(
        self,
        entity_id: str,
        patient_id: str,
        ndc: str,
        is_340b_qualified: bool,
        inventory_type: str,
        prescribing_npi: str,
        dispensing_location: str
    ) -> Dict:
        risk_flags = []
        risk_score = 0.0
        
        if inventory_type == "340b_purchased" and not is_340b_qualified:
            risk_flags.append("340B_DRUG_TO_INELIGIBLE_PATIENT")
            risk_score += 0.50
        
        if inventory_type == "340b_purchased" and is_340b_qualified:
            entity_dispensing = [
                r for r in self.dispensing_records
                if r["entity_id"] == entity_id and r["inventory_type"] == "340b_purchased"
            ]
            
            if len(entity_dispensing) > 100:
                volume_ratio = len(entity_dispensing) / max(1, len(self.dispensing_records))
                if volume_ratio > 0.80:
                    risk_flags.append("UNUSUAL_340B_VOLUME_CONCENTRATION")
                    risk_score += 0.15
        
        if inventory_type == "non_340b" and not is_340b_qualified:
            risk_flags.append("POTENTIAL_REVERSE_DIVERSION")
            risk_score += 0.10
        
        if prescribing_npi not in self._get_entity_providers(entity_id):
            risk_flags.append("OUTSIDE_PROVIDER_PRESCRIBING")
            risk_score += 0.10
        
        if dispensing_location not in self._get_entity_locations(entity_id):
            risk_flags.append("OFF_SITE_DISPENSING")
            risk_score += 0.15
        
        risk_level = "low"
        if risk_score >= 0.50:
            risk_level = "critical"
        elif risk_score >= 0.25:
            risk_level = "high"
        elif risk_score >= 0.10:
            risk_level = "medium"
        
        return {
            "entity_id": entity_id,
            "patient_id": patient_id,
            "ndc": ndc,
            "risk_flags": risk_flags,
            "risk_score": float(risk_score),
            "risk_level": risk_level,
            "is_diversion": risk_level in ["critical", "high"],
            "requires_investigation": risk_level != "low"
        }
    
    def _get_entity_providers(self, entity_id: str) -> List[str]:
        return ["NPI_PLACEHOLDER"]
    
    def _get_entity_locations(self, entity_id: str) -> List[str]:
        return ["LOC_PLACEHOLDER"]
    
    def audit_dispensing_patterns(
        self,
        entity_id: str,
        review_period_days: int = 90
    ) -> Dict:
        entity_records = [
            r for r in self.dispensing_records
            if r["entity_id"] == entity_id
        ]
        
        if len(entity_records) < 10:
            return {"status": "insufficient_data", "n_records": len(entity_records)}
        
        ndc_counts = {}
        patient_counts = {}
        
        for record in entity_records:
            ndc = record["ndc"]
            patient = record["patient_id"]
            
            ndc_counts[ndc] = ndc_counts.get(ndc, 0) + 1
            patient_counts[patient] = patient_counts.get(patient, 0) + 1
        
        high_volume_ndcs = [
            {"ndc": ndc, "dispensing_count": count}
            for ndc, count in sorted(ndc_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        high_volume_patients = [
            {"patient_id": pid, "dispensing_count": count}
            for pid, count in sorted(patient_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        qualified_count = sum(1 for r in entity_records if r["is_340b_qualified"])
        non_qualified_340b = sum(
            1 for r in entity_records
            if r["inventory_type"] == "340b_purchased" and not r["is_340b_qualified"]
        )
        
        diversion_rate = non_qualified_340b / max(len(entity_records), 1)
        
        return {
            "entity_id": entity_id,
            "n_records_reviewed": len(entity_records),
            "qualified_dispensing_rate": float(qualified_count / len(entity_records)),
            "potential_diversion_count": non_qualified_340b,
            "diversion_rate": float(diversion_rate),
            "high_volume_ndcs": high_volume_ndcs,
            "high_volume_patients": high_volume_patients,
            "requires_immediate_action": diversion_rate > 0.02,
            "program_termination_risk": diversion_rate > 0.05
        }
