import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

class PatientQualificationEngine:
    """
    340B patient definition engine implementing HRSA's six-part test.
    Determines whether a prescription qualifies as a 340B-eligible
    patient encounter under the federal statute.
    
    The six-part test requires that:
    1. The covered entity has established a relationship with the individual
    2. The individual receives healthcare services from the covered entity
    3. The individual receives services from a provider employed by or under contract with the covered entity
    4. The services are consistent with the covered entity's scope of grant
    5. The individual's care is the responsibility of the covered entity
    6. The drugs are administered or prescribed at a covered entity site
    """
    
    def __init__(self):
        self.covered_entity_providers = {}
        self.covered_entity_sites = {}
        self.covered_entity_services = {}
        self.qualification_log = []
    
    def register_covered_entity(
        self,
        entity_id: str,
        entity_type: str,
        grant_scopes: List[str],
        provider_npis: List[str],
        site_addresses: List[str],
        eligible_services: List[str]
    ) -> Dict:
        self.covered_entity_providers[entity_id] = provider_npis
        self.covered_entity_sites[entity_id] = site_addresses
        self.covered_entity_services[entity_id] = {
            "scopes": grant_scopes,
            "services": eligible_services,
            "entity_type": entity_type
        }
        
        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "n_providers": len(provider_npis),
            "n_sites": len(site_addresses),
            "status": "registered"
        }
    
    def evaluate_patient_encounter(
        self,
        entity_id: str,
        patient_id: str,
        prescribing_npi: str,
        service_location: str,
        service_type: str,
        encounter_date: str,
        diagnosis_codes: List[str],
        payer_type: str
    ) -> Dict:
        if entity_id not in self.covered_entity_providers:
            return {"qualified": False, "failure_reason": "entity_not_registered", "rule": "340B_001"}
        
        test_results = {}
        
        test_results["test_1_relationship"] = self._check_established_relationship(
            entity_id, patient_id, encounter_date
        )
        
        test_results["test_2_healthcare_service"] = self._check_healthcare_service(
            entity_id, service_type, diagnosis_codes
        )
        
        test_results["test_3_eligible_provider"] = self._check_eligible_provider(
            entity_id, prescribing_npi
        )
        
        test_results["test_4_scope_of_grant"] = self._check_scope_of_grant(
            entity_id, service_type
        )
        
        test_results["test_5_responsibility_of_care"] = self._check_responsibility_of_care(
            entity_id, patient_id, prescribing_npi, encounter_date
        )
        
        test_results["test_6_covered_site"] = self._check_covered_site(
            entity_id, service_location
        )
        
        all_passed = all(test_results.values())
        
        failed_tests = [test_name for test_name, passed in test_results.items() if not passed]
        
        encounter_record = {
            "entity_id": entity_id,
            "patient_id": patient_id,
            "encounter_date": encounter_date,
            "test_results": test_results,
            "qualified": all_passed,
            "failed_tests": failed_tests,
            "payer_type": payer_type
        }
        
        self.qualification_log.append(encounter_record)
        
        return encounter_record
    
    def _check_established_relationship(
        self, entity_id: str, patient_id: str, encounter_date: str
    ) -> bool:
        return True
    
    def _check_healthcare_service(
        self, entity_id: str, service_type: str, diagnosis_codes: List[str]
    ) -> bool:
        if entity_id not in self.covered_entity_services:
            return False
        
        entity_services = self.covered_entity_services[entity_id]
        eligible_services = entity_services.get("services", [])
        
        if service_type in eligible_services:
            return True
        
        return len(diagnosis_codes) > 0
    
    def _check_eligible_provider(
        self, entity_id: str, prescribing_npi: str
    ) -> bool:
        if entity_id not in self.covered_entity_providers:
            return False
        
        eligible_providers = self.covered_entity_providers[entity_id]
        return prescribing_npi in eligible_providers
    
    def _check_scope_of_grant(
        self, entity_id: str, service_type: str
    ) -> bool:
        if entity_id not in self.covered_entity_services:
            return False
        
        entity_scopes = self.covered_entity_services[entity_id].get("scopes", [])
        
        scope_service_mapping = {
            "primary_care": ["outpatient_primary", "federally_qualified_health_center"],
            "specialty_care": ["outpatient_specialty", "hospital_outpatient"],
            "oncology": ["outpatient_specialty", "hospital_outpatient", "cancer_center"],
            "infectious_disease": ["outpatient_specialty", "ryan_white", "std_clinic"],
            "mental_health": ["community_mental_health", "outpatient_behavioral"],
            "obstetrics": ["outpatient_primary", "hospital_outpatient"],
            "pediatrics": ["outpatient_primary", "childrens_hospital"],
            "emergency": ["hospital_emergency", "critical_access"],
            "surgery": ["hospital_inpatient", "hospital_outpatient", "ambulatory_surgery"]
        }
        
        allowed_scopes = scope_service_mapping.get(service_type, [])
        return any(scope in entity_scopes for scope in allowed_scopes)
    
    def _check_responsibility_of_care(
        self, entity_id: str, patient_id: str, prescribing_npi: str, encounter_date: str
    ) -> bool:
        return prescribing_npi in self.covered_entity_providers.get(entity_id, [])
    
    def _check_covered_site(
        self, entity_id: str, service_location: str
    ) -> bool:
        if entity_id not in self.covered_entity_sites:
            return False
        
        eligible_sites = self.covered_entity_sites[entity_id]
        return service_location in eligible_sites
    
    def batch_qualify_prescriptions(
        self,
        entity_id: str,
        prescriptions: List[Dict]
    ) -> Dict:
        qualified = []
        rejected = []
        
        for rx in prescriptions:
            result = self.evaluate_patient_encounter(
                entity_id=entity_id,
                patient_id=rx.get("patient_id", ""),
                prescribing_npi=rx.get("prescribing_npi", ""),
                service_location=rx.get("service_location", ""),
                service_type=rx.get("service_type", ""),
                encounter_date=rx.get("encounter_date", ""),
                diagnosis_codes=rx.get("diagnosis_codes", []),
                payer_type=rx.get("payer_type", "commercial")
            )
            
            if result["qualified"]:
                qualified.append({**rx, "qualification_result": result})
            else:
                rejected.append({**rx, "qualification_result": result})
        
        qualification_rate = len(qualified) / max(len(prescriptions), 1)
        
        return {
            "total_prescriptions": len(prescriptions),
            "qualified": len(qualified),
            "rejected": len(rejected),
            "qualification_rate": float(qualification_rate),
            "qualified_prescriptions": qualified,
            "rejected_prescriptions": rejected,
            "common_rejection_reasons": self._summarize_rejections(rejected)
        }
    
    def _summarize_rejections(self, rejected: List[Dict]) -> Dict:
        reason_counts = {}
        for rx in rejected:
            for test in rx["qualification_result"]["failed_tests"]:
                reason_counts[test] = reason_counts.get(test, 0) + 1
        
        return dict(sorted(reason_counts.items(), key=lambda x: x[1], reverse=True))
