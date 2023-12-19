import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

class HRSAAuditFramework:
    """
    HRSA audit readiness framework for 340B program compliance.
    
    HRSA conducts audits of covered entities to verify compliance
    with 340B program requirements. Common findings include
    duplicate discounts, diversion to ineligible patients,
    GPO prohibition violations, and inadequate record-keeping.
    
    This framework assesses audit readiness, identifies gaps,
    and generates remediation plans organized by HRSA audit
    focus areas.
    """
    
    def __init__(self):
        self.audit_domains = {
            "patient_eligibility": {
                "weight": 0.25,
                "description": "Documentation of patient qualification under six-part test"
            },
            "duplicate_discount_prevention": {
                "weight": 0.25,
                "description": "Systems to prevent Medicaid duplicate discounts"
            },
            "diversion_prevention": {
                "weight": 0.20,
                "description": "Controls preventing 340B drugs reaching ineligible patients"
            },
            "gpo_compliance": {
                "weight": 0.15,
                "description": "GPO exclusion compliance for DSH and children's hospitals"
            },
            "record_keeping": {
                "weight": 0.10,
                "description": "Auditable records maintained for all 340B transactions"
            },
            "policy_procedure": {
                "weight": 0.05,
                "description": "Written policies and procedures for 340B operations"
            }
        }
        self.findings_log = []
    
    def assess_audit_domain(
        self,
        domain: str,
        evidence_available: bool,
        documentation_score: float,
        process_maturity: str,
        prior_findings: int,
        self_identified_issues: int
    ) -> Dict:
        if domain not in self.audit_domains:
            return {"domain": domain, "status": "unknown_domain"}
        
        maturity_scores = {
            "ad_hoc": 0.3,
            "defined": 0.6,
            "managed": 0.8,
            "optimized": 0.95
        }
        
        base_score = (
            (0.4 if evidence_available else 0.0) +
            documentation_score * 0.3 +
            maturity_scores.get(process_maturity, 0.3) * 0.3
        )
        
        prior_penalty = prior_findings * 0.05
        self_issue_penalty = self_identified_issues * 0.03
        
        final_score = max(0.0, min(1.0, base_score - prior_penalty - self_issue_penalty))
        
        if final_score >= 0.85:
            readiness = "audit_ready"
        elif final_score >= 0.65:
            readiness = "minor_gaps"
        elif final_score >= 0.45:
            readiness = "moderate_gaps"
        else:
            readiness = "significant_gaps"
        
        return {
            "domain": domain,
            "score": float(final_score),
            "readiness": readiness,
            "evidence_available": evidence_available,
            "documentation_score": float(documentation_score),
            "process_maturity": process_maturity,
            "prior_findings": prior_findings,
            "self_identified_issues": self_identified_issues
        }
    
    def run_full_assessment(
        self,
        entity_id: str,
        domain_assessments: Dict[str, Dict]
    ) -> Dict:
        domain_results = {}
        weighted_score = 0.0
        
        for domain, config in self.audit_domains.items():
            assessment = domain_assessments.get(domain, {})
            
            result = self.assess_audit_domain(
                domain=domain,
                evidence_available=assessment.get("evidence_available", False),
                documentation_score=assessment.get("documentation_score", 0.5),
                process_maturity=assessment.get("process_maturity", "ad_hoc"),
                prior_findings=assessment.get("prior_findings", 0),
                self_identified_issues=assessment.get("self_identified_issues", 0)
            )
            
            domain_results[domain] = result
            weighted_score += result["score"] * config["weight"]
        
        if weighted_score >= 0.85:
            overall_readiness = "audit_ready"
        elif weighted_score >= 0.65:
            overall_readiness = "minor_gaps_remediate_in_30_days"
        elif weighted_score >= 0.45:
            overall_readiness = "moderate_gaps_remediate_in_90_days"
        else:
            overall_readiness = "significant_gaps_requires_program_redesign"
        
        critical_gaps = [
            domain for domain, result in domain_results.items()
            if result["readiness"] in ["moderate_gaps", "significant_gaps"]
        ]
        
        return {
            "entity_id": entity_id,
            "overall_score": float(weighted_score),
            "overall_readiness": overall_readiness,
            "domain_results": domain_results,
            "critical_gaps": critical_gaps,
            "n_critical_gaps": len(critical_gaps),
            "audit_ready": overall_readiness == "audit_ready",
            "assessment_date": datetime.now().strftime("%Y-%m-%d")
        }
    
    def generate_remediation_plan(
        self,
        assessment: Dict,
        entity_id: str
    ) -> Dict:
        remediation_items = []
        
        for domain, result in assessment.get("domain_results", {}).items():
            if result["readiness"] == "audit_ready":
                continue
            
            if domain == "patient_eligibility":
                remediation_items.append({
                    "domain": domain,
                    "action": "Implement patient qualification checklist in EMR workflow",
                    "timeline_days": 45,
                    "priority": "high" if result["readiness"] == "significant_gaps" else "medium",
                    "estimated_cost": 25000
                })
            
            elif domain == "duplicate_discount_prevention":
                remediation_items.append({
                    "domain": domain,
                    "action": "Configure split-billing software with Medicaid carve-out logic",
                    "timeline_days": 30,
                    "priority": "critical",
                    "estimated_cost": 35000
                })
            
            elif domain == "diversion_prevention":
                remediation_items.append({
                    "domain": domain,
                    "action": "Implement virtual inventory tracking with NDC-level audit trail",
                    "timeline_days": 60,
                    "priority": "high",
                    "estimated_cost": 45000
                })
            
            elif domain == "gpo_compliance":
                remediation_items.append({
                    "domain": domain,
                    "action": "Review all GPO contracts and segregate covered outpatient drugs",
                    "timeline_days": 45,
                    "priority": "high",
                    "estimated_cost": 15000
                })
            
            elif domain == "record_keeping":
                remediation_items.append({
                    "domain": domain,
                    "action": "Establish centralized 340B document repository with retention policy",
                    "timeline_days": 30,
                    "priority": "medium",
                    "estimated_cost": 10000
                })
            
            elif domain == "policy_procedure":
                remediation_items.append({
                    "domain": domain,
                    "action": "Draft and approve formal 340B policies and procedures manual",
                    "timeline_days": 45,
                    "priority": "medium",
                    "estimated_cost": 8000
                })
        
        remediation_items.sort(key=lambda x: 
            (0 if x["priority"] == "critical" else 1 if x["priority"] == "high" else 2,
             x["timeline_days"])
        )
        
        total_cost = sum(item["estimated_cost"] for item in remediation_items)
        
        return {
            "entity_id": entity_id,
            "remediation_items": remediation_items,
            "n_items": len(remediation_items),
            "total_estimated_cost": total_cost,
            "critical_path_days": max((item["timeline_days"] for item in remediation_items), default=0),
            "estimated_completion_date": (datetime.now() + timedelta(days=max((item["timeline_days"] for item in remediation_items), default=0))).strftime("%Y-%m-%d")
        }
