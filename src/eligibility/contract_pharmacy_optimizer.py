import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy.spatial.distance import cdist

class ContractPharmacyOptimizer:
    """
    Contract pharmacy network design optimizer for 340B programs.
    Determines optimal contract pharmacy locations and count
    to maximize 340B-eligible prescription capture while
    respecting HRSA guidelines on contract pharmacy arrangements.
    """
    
    def __init__(self):
        self.covered_entity_location = None
        self.existing_pharmacies = []
        self.candidate_pharmacies = []
        self.patient_population = None
    
    def set_covered_entity(
        self,
        entity_location: Tuple[float, float],
        entity_type: str,
        max_contract_pharmacies: Optional[int] = None
    ) -> Dict:
        self.covered_entity_location = np.array(entity_location)
        
        if max_contract_pharmacies is None:
            if entity_type in ["disproportionate_share_hospital", "childrens_hospital"]:
                max_contract_pharmacies = 35
            elif entity_type == "critical_access_hospital":
                max_contract_pharmacies = 15
            elif entity_type == "federally_qualified_health_center":
                max_contract_pharmacies = 10
            elif entity_type == "ryan_white_clinic":
                max_contract_pharmacies = 5
            else:
                max_contract_pharmacies = 8
        
        return {
            "entity_location": entity_location,
            "entity_type": entity_type,
            "max_contract_pharmacies": max_contract_pharmacies
        }
    
    def add_candidate_pharmacies(
        self,
        pharmacy_data: List[Dict]
    ) -> None:
        self.candidate_pharmacies = pharmacy_data
    
    def set_patient_population(
        self,
        patient_locations: np.ndarray,
        patient_volumes: np.ndarray
    ) -> None:
        self.patient_population = {
            "locations": patient_locations,
            "volumes": patient_volumes
        }
    
    def compute_pharmacy_coverage(
        self,
        pharmacy_locations: np.ndarray,
        patient_locations: np.ndarray,
        max_distance_miles: float = 5.0
    ) -> Dict:
        distances = cdist(patient_locations, pharmacy_locations)
        
        min_distances = np.min(distances, axis=1)
        nearest_pharmacy = np.argmin(distances, axis=1)
        
        covered = min_distances <= (max_distance_miles / 69.0)
        coverage_pct = np.mean(covered)
        
        unique_pharmacies_used = len(np.unique(nearest_pharmacy[covered]))
        
        return {
            "coverage_pct": float(coverage_pct),
            "mean_distance": float(np.mean(min_distances)),
            "median_distance": float(np.median(min_distances)),
            "max_distance": float(np.max(min_distances)),
            "unique_pharmacies_accessed": unique_pharmacies_used,
            "patients_covered": int(np.sum(covered)),
            "total_patients": len(patient_locations)
        }
    
    def greedy_pharmacy_selection(
        self,
        max_pharmacies: int,
        max_distance_miles: float = 5.0
    ) -> Dict:
        if self.patient_population is None or len(self.candidate_pharmacies) == 0:
            return {"status": "insufficient_data"}
        
        patient_locations = self.patient_population["locations"]
        patient_volumes = self.patient_population["volumes"]
        
        candidate_locations = np.array([p["location"] for p in self.candidate_pharmacies])
        
        n_patients = len(patient_locations)
        covered = np.zeros(n_patients, dtype=bool)
        
        selected_indices = []
        coverage_history = []
        
        for step in range(max_pharmacies):
            best_coverage_gain = 0
            best_idx = None
            
            for i in range(len(candidate_locations)):
                if i in selected_indices:
                    continue
                
                distances_to_i = np.linalg.norm(
                    patient_locations - candidate_locations[i], axis=1
                )
                
                newly_covered = (~covered) & (distances_to_i <= (max_distance_miles / 69.0))
                coverage_gain = np.sum(patient_volumes[newly_covered])
                
                if coverage_gain > best_coverage_gain:
                    best_coverage_gain = coverage_gain
                    best_idx = i
            
            if best_idx is None:
                break
            
            selected_indices.append(best_idx)
            
            distances_to_best = np.linalg.norm(
                patient_locations - candidate_locations[best_idx], axis=1
            )
            covered = covered | (distances_to_best <= (max_distance_miles / 69.0))
            
            coverage_history.append({
                "step": step + 1,
                "pharmacy_added": self.candidate_pharmacies[best_idx].get("name", f"PHARM_{best_idx}"),
                "cumulative_coverage_pct": float(np.mean(covered) * 100),
                "cumulative_volume_covered": float(np.sum(patient_volumes[covered]))
            })
        
        selected_pharmacies = [self.candidate_pharmacies[i] for i in selected_indices]
        
        return {
            "selected_pharmacies": selected_pharmacies,
            "n_selected": len(selected_pharmacies),
            "coverage_history": coverage_history,
            "final_coverage_pct": float(np.mean(covered) * 100),
            "final_volume_covered": float(np.sum(patient_volumes[covered])),
            "total_patient_volume": float(np.sum(patient_volumes)),
            "coverage_saturation_point": self._find_saturation_point(coverage_history)
        }
    
    def _find_saturation_point(self, coverage_history: List[Dict]) -> int:
        if len(coverage_history) < 3:
            return len(coverage_history)
        
        for i in range(1, len(coverage_history)):
            gain = coverage_history[i]["cumulative_coverage_pct"] - coverage_history[i-1]["cumulative_coverage_pct"]
            if gain < 2.0:
                return i + 1
        
        return len(coverage_history)
