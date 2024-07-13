import numpy as np
from typing import Dict, List, Tuple, Optional

class InventorySplitLogic:
    """
    340B vs. non-340B inventory splitting and tracking logic.
    
    Covered entities must physically or virtually segregate 340B
    drug inventory from non-340B inventory. Virtual tracking
    requires NDC-level replenishment logic that ensures 340B
    accumulation matches 340B dispensing within each order cycle.
    
    This engine implements the replenishment logic, tracks
    accumulation-to-dispensing ratios, and flags potential
    commingling or diversion scenarios.
    """
    
    def __init__(self):
        self.inventory_340b = {}
        self.inventory_non_340b = {}
        self.dispensing_log = []
        self.replenishment_log = []
    
    def initialize_inventory(
        self,
        entity_id: str,
        ndc: str,
        quantity_340b: int,
        quantity_non_340b: int,
        unit_cost_340b: float,
        unit_cost_wac: float
    ) -> Dict:
        key = f"{entity_id}:{ndc}"
        
        self.inventory_340b[key] = {
            "quantity_on_hand": quantity_340b,
            "unit_cost": unit_cost_340b,
            "total_value": quantity_340b * unit_cost_340b
        }
        
        self.inventory_non_340b[key] = {
            "quantity_on_hand": quantity_non_340b,
            "unit_cost": unit_cost_wac,
            "total_value": quantity_non_340b * unit_cost_wac
        }
        
        return {
            "entity_id": entity_id,
            "ndc": ndc,
            "quantity_340b": quantity_340b,
            "quantity_non_340b": quantity_non_340b,
            "total_inventory": quantity_340b + quantity_non_340b
        }
    
    def determine_dispensing_source(
        self,
        entity_id: str,
        ndc: str,
        patient_is_340b_eligible: bool,
        quantity_needed: int
    ) -> Dict:
        key = f"{entity_id}:{ndc}"
        
        if key not in self.inventory_340b:
            return {"status": "ndc_not_in_inventory", "entity_id": entity_id, "ndc": ndc}
        
        if patient_is_340b_eligible:
            available_340b = self.inventory_340b[key]["quantity_on_hand"]
            
            if available_340b >= quantity_needed:
                source = "340b_inventory"
                self.inventory_340b[key]["quantity_on_hand"] -= quantity_needed
            else:
                partial_340b = available_340b
                remaining = quantity_needed - partial_340b
                
                if self.inventory_non_340b[key]["quantity_on_hand"] >= remaining:
                    source = "mixed_inventory"
                    self.inventory_340b[key]["quantity_on_hand"] = 0
                    self.inventory_non_340b[key]["quantity_on_hand"] -= remaining
                else:
                    return {"status": "insufficient_inventory"}
        else:
            available_non = self.inventory_non_340b[key]["quantity_on_hand"]
            
            if available_non >= quantity_needed:
                source = "non_340b_inventory"
                self.inventory_non_340b[key]["quantity_on_hand"] -= quantity_needed
            else:
                return {"status": "insufficient_inventory"}
        
        dispensing_event = {
            "entity_id": entity_id,
            "ndc": ndc,
            "quantity": quantity_needed,
            "source": source,
            "patient_340b_eligible": patient_is_340b_eligible,
            "remaining_340b": self.inventory_340b[key]["quantity_on_hand"],
            "remaining_non_340b": self.inventory_non_340b[key]["quantity_on_hand"]
        }
        
        self.dispensing_log.append(dispensing_event)
        
        return dispensing_event
    
    def compute_replenishment_quantity(
        self,
        entity_id: str,
        ndc: str,
        order_cycle_days: int = 14,
        safety_stock_days: int = 5,
        lead_time_days: int = 3
    ) -> Dict:
        key = f"{entity_id}:{ndc}"
        
        recent_dispensing = [
            d for d in self.dispensing_log
            if d["entity_id"] == entity_id and d["ndc"] == ndc
        ]
        
        if len(recent_dispensing) < 5:
            return {"status": "insufficient_history"}
        
        avg_daily_usage_340b = np.mean([
            d["quantity"] for d in recent_dispensing
            if d["source"] in ["340b_inventory", "mixed_inventory"]
        ])
        
        avg_daily_usage_non = np.mean([
            d["quantity"] for d in recent_dispensing
            if d["source"] == "non_340b_inventory"
        ])
        
        reorder_340b = int(np.ceil(avg_daily_usage_340b * (order_cycle_days + safety_stock_days + lead_time_days)))
        reorder_non = int(np.ceil(avg_daily_usage_non * (order_cycle_days + safety_stock_days + lead_time_days)))
        
        current_340b = self.inventory_340b.get(key, {}).get("quantity_on_hand", 0)
        current_non = self.inventory_non_340b.get(key, {}).get("quantity_on_hand", 0)
        
        order_340b = max(0, reorder_340b - current_340b)
        order_non = max(0, reorder_non - current_non)
        
        replenishment = {
            "entity_id": entity_id,
            "ndc": ndc,
            "order_quantity_340b": order_340b,
            "order_quantity_non_340b": order_non,
            "total_order_quantity": order_340b + order_non,
            "estimated_order_cost": float(order_340b * self.inventory_340b.get(key, {}).get("unit_cost", 0) + order_non * self.inventory_non_340b.get(key, {}).get("unit_cost", 0))
        }
        
        self.replenishment_log.append(replenishment)
        
        return replenishment
    
    def check_accumulation_compliance(
        self,
        entity_id: str,
        ndc: str,
        review_period_days: int = 30
    ) -> Dict:
        key = f"{entity_id}:{ndc}"
        
        relevant_dispensing = [
            d for d in self.dispensing_log
            if d["entity_id"] == entity_id and d["ndc"] == ndc
        ]
        
        relevant_replenishment = [
            r for r in self.replenishment_log
            if r["entity_id"] == entity_id and r["ndc"] == ndc
        ]
        
        total_340b_dispensed = sum(
            d["quantity"] for d in relevant_dispensing
            if d["source"] in ["340b_inventory", "mixed_inventory"]
        )
        
        total_340b_replenished = sum(
            r["order_quantity_340b"] for r in relevant_replenishment
        )
        
        if total_340b_dispensed > 0:
            accumulation_ratio = total_340b_replenished / total_340b_dispensed
        else:
            accumulation_ratio = 1.0
        
        compliant = 0.90 <= accumulation_ratio <= 1.10
        
        return {
            "entity_id": entity_id,
            "ndc": ndc,
            "total_340b_dispensed": total_340b_dispensed,
            "total_340b_replenished": total_340b_replenished,
            "accumulation_ratio": float(accumulation_ratio),
            "compliant": compliant,
            "risk_of_overaccumulation": accumulation_ratio > 1.10,
            "risk_of_underaccumulation": accumulation_ratio < 0.90,
            "potential_violation": not compliant
        }
