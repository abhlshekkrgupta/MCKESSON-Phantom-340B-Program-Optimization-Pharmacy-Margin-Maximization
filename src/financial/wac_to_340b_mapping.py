import numpy as np
from typing import Dict, List, Tuple, Optional

class WACTo340BMapping:
    """
    WAC to 340B ceiling price mapping engine.
    
    The 340B ceiling price is calculated as Average Manufacturer Price
    minus the Unit Rebate Amount. This engine estimates 340B prices
    from observable WAC prices when ceiling prices are not directly
    available from HRSA's 340B OPAIS database.
    
    Uses the regulatory formula and historical discount patterns
    to estimate the 340B acquisition cost for financial modeling.
    """
    
    def __init__(self):
        self.wac_to_340b_ratios = {}
        self.amp_estimates = {}
        self.ura_estimates = {}
    
    def estimate_340b_from_wac(
        self,
        ndc: str,
        wac_price: float,
        drug_category: str,
        is_brand: bool,
        is_generic: bool
    ) -> Dict:
        if is_generic:
            amp_ratio = 0.45
            ura_ratio = 0.70
        elif is_brand:
            if drug_category in ["oncology", "specialty", "orphan"]:
                amp_ratio = 0.78
                ura_ratio = 0.25
            elif drug_category in ["injectable", "biologic"]:
                amp_ratio = 0.82
                ura_ratio = 0.22
            else:
                amp_ratio = 0.85
                ura_ratio = 0.23
        else:
            amp_ratio = 0.65
            ura_ratio = 0.45
        
        amp_estimate = wac_price * amp_ratio
        ura_estimate = amp_estimate * ura_ratio
        ceiling_340b = amp_estimate - ura_estimate
        
        if ceiling_340b <= 0.01:
            ceiling_340b = wac_price * 0.01
        
        if is_generic:
            ceiling_340b = min(ceiling_340b, wac_price * 0.13)
        
        discount_from_wac = (1 - ceiling_340b / wac_price) * 100 if wac_price > 0 else 0
        
        self.wac_to_340b_ratios[ndc] = {
            "wac": wac_price,
            "amp_estimate": float(amp_estimate),
            "ura_estimate": float(ura_estimate),
            "ceiling_340b": float(ceiling_340b),
            "discount_pct": float(discount_from_wac),
            "drug_category": drug_category,
            "is_brand": is_brand,
            "is_generic": is_generic
        }
        
        return self.wac_to_340b_ratios[ndc]
    
    def estimate_subceiling_price(
        self,
        ndc: str,
        ceiling_340b: float,
        competitor_prices: List[float],
        contract_discount_pct: float = 0.0
    ) -> Dict:
        subceiling = ceiling_340b * (1 - contract_discount_pct)
        
        if len(competitor_prices) > 0:
            min_competitor = min(competitor_prices)
            subceiling = min(subceiling, min_competitor * 0.95)
        
        additional_savings = ceiling_340b - subceiling
        
        return {
            "ndc": ndc,
            "ceiling_340b": float(ceiling_340b),
            "subceiling_price": float(subceiling),
            "additional_savings_per_unit": float(additional_savings),
            "additional_savings_pct": float(additional_savings / ceiling_340b * 100) if ceiling_340b > 0 else 0,
            "contract_discount_applied": contract_discount_pct > 0
        }
    
    def batch_estimate_prices(
        self,
        drug_list: List[Dict]
    ) -> Dict:
        results = []
        total_wac_value = 0.0
        total_340b_value = 0.0
        
        for drug in drug_list:
            result = self.estimate_340b_from_wac(
                ndc=drug.get("ndc", ""),
                wac_price=drug.get("wac_price", 0),
                drug_category=drug.get("category", "oral_solid"),
                is_brand=drug.get("is_brand", False),
                is_generic=drug.get("is_generic", True)
            )
            
            annual_volume = drug.get("annual_volume", 0)
            total_wac_value += result["wac"] * annual_volume
            total_340b_value += result["ceiling_340b"] * annual_volume
            
            results.append({
                **drug,
                "ceiling_340b": result["ceiling_340b"],
                "discount_pct": result["discount_pct"],
                "annual_wac_spend": result["wac"] * annual_volume,
                "annual_340b_spend": result["ceiling_340b"] * annual_volume,
                "annual_savings": (result["wac"] - result["ceiling_340b"]) * annual_volume
            })
        
        results.sort(key=lambda x: x["annual_savings"], reverse=True)
        
        return {
            "n_drugs": len(results),
            "total_annual_wac_spend": float(total_wac_value),
            "total_annual_340b_spend": float(total_340b_value),
            "total_annual_savings": float(total_wac_value - total_340b_value),
            "average_discount_pct": float(np.mean([r["discount_pct"] for r in results])),
            "drug_results": results,
            "top_savings_opportunities": results[:15]
        }
    
    def compare_to_acquisition_benchmarks(
        self,
        ndc: str,
        estimated_340b: float,
        gpo_price: Optional[float] = None,
        wac_direct_price: Optional[float] = None,
        wholesale_price: Optional[float] = None
    ) -> Dict:
        comparison = {
            "ndc": ndc,
            "estimated_340b_price": float(estimated_340b),
            "benchmarks": {}
        }
        
        if gpo_price:
            savings_vs_gpo = (estimated_340b - gpo_price) / gpo_price * 100 if gpo_price > 0 else 0
            comparison["benchmarks"]["gpo"] = {
                "price": float(gpo_price),
                "savings_vs_340b_pct": float(-savings_vs_gpo),
                "better_than_340b": gpo_price < estimated_340b
            }
        
        if wac_direct_price:
            savings_vs_wac = (estimated_340b - wac_direct_price) / wac_direct_price * 100 if wac_direct_price > 0 else 0
            comparison["benchmarks"]["wac_direct"] = {
                "price": float(wac_direct_price),
                "savings_vs_340b_pct": float(-savings_vs_wac),
                "better_than_340b": wac_direct_price < estimated_340b
            }
        
        return comparison
