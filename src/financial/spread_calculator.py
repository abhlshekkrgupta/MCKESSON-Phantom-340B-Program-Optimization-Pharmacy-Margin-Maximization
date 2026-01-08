import numpy as np
from typing import Dict, List, Tuple, Optional

class SpreadCalculator340B:
    """
    340B spread calculator — the core financial engine.
    Computes the margin between 340B acquisition cost and
    commercial reimbursement across all payer types.
    
    The 340B spread is the difference between what the covered
    entity pays for the drug (340B ceiling price) and what the
    payer reimburses (commercial, Medicare Part D, Medicaid FFS,
    or Medicaid MCO). This spread is the fundamental economic
    driver of the 340B program.
    """
    
    def __init__(self):
        self.payer_mix = {}
        self.drug_pricing = {}
        self.calculation_log = []
    
    def set_payer_mix(
        self,
        entity_id: str,
        payer_distribution: Dict[str, float]
    ) -> None:
        total = sum(payer_distribution.values())
        self.payer_mix[entity_id] = {
            payer: fraction / total for payer, fraction in payer_distribution.items()
        }
    
    def load_drug_pricing(
        self,
        ndc: str,
        wac_price: float,
        awp_price: float,
        ceiling_price_340b: float,
        amp_price: float
    ) -> Dict:
        self.drug_pricing[ndc] = {
            "wac": wac_price,
            "awp": awp_price,
            "ceiling_340b": ceiling_price_340b,
            "amp": amp_price,
            "discount_from_wac_pct": float((1 - ceiling_price_340b / wac_price) * 100) if wac_price > 0 else 0
        }
        return self.drug_pricing[ndc]
    
    def compute_payer_spread(
        self,
        ndc: str,
        payer_type: str,
        quantity: int,
        days_supply: int
    ) -> Dict:
        if ndc not in self.drug_pricing:
            return {"error": "drug_not_priced", "ndc": ndc}
        
        pricing = self.drug_pricing[ndc]
        acquisition_cost = pricing["ceiling_340b"] * quantity
        
        reimbursement_rates = {
            "commercial_ppo": 0.85,
            "commercial_hmo": 0.82,
            "commercial_hdhp": 0.88,
            "medicare_part_d": 0.78,
            "medicaid_ffs": 0.70,
            "medicaid_mco": 0.75,
            "medicare_advantage": 0.80,
            "tricare": 0.72,
            "cash_pay": 1.00,
            "uninsured": 0.60
        }
        
        reimbursement_multiplier = reimbursement_rates.get(payer_type, 0.80)
        reimbursement = pricing["awp"] * reimbursement_multiplier * quantity
        
        spread = reimbursement - acquisition_cost
        spread_pct = (spread / acquisition_cost * 100) if acquisition_cost > 0 else 0
        margin_pct = (spread / reimbursement * 100) if reimbursement > 0 else 0
        
        return {
            "ndc": ndc,
            "payer_type": payer_type,
            "quantity": quantity,
            "acquisition_cost_340b": float(acquisition_cost),
            "reimbursement": float(reimbursement),
            "spread_dollars": float(spread),
            "spread_pct": float(spread_pct),
            "margin_pct": float(margin_pct),
            "profitable": spread > 0
        }
    
    def compute_blended_spread(
        self,
        entity_id: str,
        ndc: str,
        quantity: int,
        days_supply: int
    ) -> Dict:
        if entity_id not in self.payer_mix:
            return {"error": "payer_mix_not_set"}
        
        payer_mix = self.payer_mix[entity_id]
        
        total_spread = 0.0
        total_reimbursement = 0.0
        total_acquisition = 0.0
        payer_details = {}
        
        for payer_type, fraction in payer_mix.items():
            result = self.compute_payer_spread(ndc, payer_type, quantity, days_supply)
            
            weighted_spread = result["spread_dollars"] * fraction
            weighted_reimbursement = result["reimbursement"] * fraction
            weighted_acquisition = result["acquisition_cost_340b"] * fraction
            
            total_spread += weighted_spread
            total_reimbursement += weighted_reimbursement
            total_acquisition += weighted_acquisition
            
            payer_details[payer_type] = {
                "fraction": float(fraction),
                "spread_per_unit": float(result["spread_dollars"]),
                "weighted_contribution": float(weighted_spread)
            }
        
        blended_margin = (total_spread / total_reimbursement * 100) if total_reimbursement > 0 else 0
        
        return {
            "entity_id": entity_id,
            "ndc": ndc,
            "blended_acquisition": float(total_acquisition),
            "blended_reimbursement": float(total_reimbursement),
            "blended_spread": float(total_spread),
            "blended_margin_pct": float(blended_margin),
            "payer_breakdown": payer_details
        }
    
    def compute_portfolio_spread(
        self,
        entity_id: str,
        drug_utilization: List[Dict]
    ) -> Dict:
        total_spread = 0.0
        total_revenue = 0.0
        drug_results = []
        
        for drug in drug_utilization:
            ndc = drug["ndc"]
            quantity = drug.get("annual_quantity", 0)
            days_supply = drug.get("avg_days_supply", 30)
            
            blended = self.compute_blended_spread(entity_id, ndc, quantity, days_supply)
            
            total_spread += blended["blended_spread"]
            total_revenue += blended["blended_reimbursement"]
            
            drug_results.append({
                "ndc": ndc,
                "drug_name": drug.get("drug_name", ndc),
                "annual_spread": float(blended["blended_spread"]),
                "annual_reimbursement": float(blended["blended_reimbursement"]),
                "margin_pct": float(blended["blended_margin_pct"])
            })
        
        drug_results.sort(key=lambda x: x["annual_spread"], reverse=True)
        
        return {
            "entity_id": entity_id,
            "total_annual_spread": float(total_spread),
            "total_annual_revenue": float(total_revenue),
            "portfolio_margin_pct": float(total_spread / total_revenue * 100) if total_revenue > 0 else 0,
            "n_drugs": len(drug_results),
            "drug_results": drug_results,
            "top_10_by_spread": drug_results[:10]
        }
