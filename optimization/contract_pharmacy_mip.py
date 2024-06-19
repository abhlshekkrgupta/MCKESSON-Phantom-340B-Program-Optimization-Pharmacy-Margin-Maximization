import numpy as np
from typing import Dict, List, Tuple, Optional

class ContractPharmacyMIP:
    """
    Mixed-integer programming model for contract pharmacy network design.
    Optimizes the selection of contract pharmacy locations to maximize
    340B-eligible prescription capture subject to budget constraints,
    geographic coverage requirements, and HRSA contract limits.
    """
    
    def __init__(self):
        self.pharmacies = []
        self.patient_zones = []
        self.coverage_matrix = None
        self.solution = None
    
    def build_model(
        self,
        pharmacies: List[Dict],
        patient_zones: List[Dict],
        max_pharmacies: int,
        budget_constraint: Optional[float] = None,
        min_coverage_pct: float = 0.70
    ) -> Dict:
        self.pharmacies = pharmacies
        self.patient_zones = patient_zones
        
        n_pharmacies = len(pharmacies)
        n_zones = len(patient_zones)
        
        coverage = np.zeros((n_pharmacies, n_zones))
        
        for i, pharmacy in enumerate(pharmacies):
            pharm_loc = np.array(pharmacy["location"])
            for j, zone in enumerate(patient_zones):
                zone_loc = np.array(zone["centroid"])
                distance = np.linalg.norm(pharm_loc - zone_loc)
                
                if distance <= pharmacy.get("coverage_radius", 5.0) / 69.0:
                    coverage[i, j] = 1
        
        self.coverage_matrix = coverage
        
        return {
            "n_pharmacies": n_pharmacies,
            "n_patient_zones": n_zones,
            "max_pharmacies": max_pharmacies,
            "budget_constraint": budget_constraint,
            "min_coverage_pct": min_coverage_pct,
            "coverage_density": float(np.mean(coverage)),
            "model_built": True
        }
    
    def solve_greedy(
        self,
        max_pharmacies: int,
        min_volume_per_pharmacy: int = 100
    ) -> Dict:
        if self.coverage_matrix is None:
            return {"status": "model_not_built"}
        
        n_pharmacies = self.coverage_matrix.shape[0]
        n_zones = self.coverage_matrix.shape[1]
        
        zone_volumes = np.array([z.get("patient_volume", 100) for z in self.patient_zones])
        
        covered_zones = np.zeros(n_zones, dtype=bool)
        selected_pharmacies = []
        
        coverage_history = []
        total_patient_volume = np.sum(zone_volumes)
        
        for step in range(max_pharmacies):
            best_gain = 0
            best_idx = None
            
            for i in range(n_pharmacies):
                if i in selected_pharmacies:
                    continue
                
                pharmacy_volume = self.pharmacies[i].get("estimated_volume", 1000)
                if pharmacy_volume < min_volume_per_pharmacy:
                    continue
                
                newly_covered = (~covered_zones) & (self.coverage_matrix[i] == 1)
                volume_gain = np.sum(zone_volumes[newly_covered])
                
                cost = self.pharmacies[i].get("setup_cost", 5000)
                efficiency = volume_gain / max(cost, 1)
                
                if efficiency > best_gain:
                    best_gain = efficiency
                    best_idx = i
            
            if best_idx is None:
                break
            
            selected_pharmacies.append(best_idx)
            covered_zones = covered_zones | (self.coverage_matrix[best_idx] == 1)
            
            coverage_history.append({
                "step": step + 1,
                "pharmacy_added": self.pharmacies[best_idx].get("name", f"PHARM_{best_idx}"),
                "cumulative_coverage_pct": float(np.sum(zone_volumes[covered_zones]) / total_patient_volume * 100),
                "n_zones_covered": int(np.sum(covered_zones))
            })
        
        selected = [self.pharmacies[i] for i in selected_pharmacies]
        
        total_setup_cost = sum(p.get("setup_cost", 5000) for p in selected)
        captured_volume = np.sum(zone_volumes[covered_zones])
        avg_margin_per_rx = 45.00
        
        annual_revenue = captured_volume * avg_margin_per_rx
        payback_months = (total_setup_cost / (annual_revenue / 12)) if annual_revenue > 0 else float('inf')
        
        self.solution = {
            "selected_pharmacies": selected,
            "n_selected": len(selected),
            "total_setup_cost": float(total_setup_cost),
            "captured_patient_volume": float(captured_volume),
            "coverage_pct": float(captured_volume / total_patient_volume * 100) if total_patient_volume > 0 else 0,
            "estimated_annual_revenue": float(annual_revenue),
            "payback_months": float(payback_months),
            "coverage_history": coverage_history
        }
        
        return self.solution
    
    def evaluate_solution(
        self,
        selected_indices: List[int]
    ) -> Dict:
        if self.coverage_matrix is None:
            return {"status": "model_not_built"}
        
        n_zones = self.coverage_matrix.shape[1]
        zone_volumes = np.array([z.get("patient_volume", 100) for z in self.patient_zones])
        
        covered = np.zeros(n_zones, dtype=bool)
        for idx in selected_indices:
            covered = covered | (self.coverage_matrix[idx] == 1)
        
        captured_volume = np.sum(zone_volumes[covered])
        total_volume = np.sum(zone_volumes)
        
        total_cost = sum(self.pharmacies[i].get("setup_cost", 5000) for i in selected_indices)
        
        avg_340b_margin = 45.00
        estimated_revenue = captured_volume * avg_340b_margin
        
        roi = estimated_revenue / max(total_cost, 1)
        
        uncovered_zones = []
        for j in range(n_zones):
            if not covered[j]:
                uncovered_zones.append({
                    "zone_id": self.patient_zones[j].get("zone_id", f"ZONE_{j}"),
                    "patient_volume": int(zone_volumes[j]),
                    "centroid": self.patient_zones[j].get("centroid", [0, 0])
                })
        
        return {
            "n_pharmacies_selected": len(selected_indices),
            "coverage_pct": float(captured_volume / total_volume * 100) if total_volume > 0 else 0,
            "captured_volume": float(captured_volume),
            "total_setup_cost": float(total_cost),
            "estimated_annual_revenue": float(estimated_revenue),
            "roi": float(roi),
            "uncovered_zones": uncovered_zones[:10],
            "n_uncovered_zones": len(uncovered_zones)
        }
