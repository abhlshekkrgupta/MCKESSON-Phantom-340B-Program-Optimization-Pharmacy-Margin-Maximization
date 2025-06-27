import numpy as np
from typing import Dict, List, Tuple, Optional

class MarginWaterfall:
    """
    End-to-end margin decomposition for 340B pharmacy operations.
    Traces every dollar from gross reimbursement through all
    cost layers to net margin, identifying leakage points
    and optimization opportunities.
    """
    
    def __init__(self):
        self.cost_components = {
            "drug_acquisition": "340B ceiling price or sub-ceiling",
            "dispensing_cost": "Pharmacy labor and overhead per prescription",
            "third_party_admin_fee": "TPA or contract pharmacy administration fee",
            "wholesaler_distribution_fee": "Distribution and logistics cost",
            "inventory_carrying_cost": "Working capital cost of held inventory",
            "chargeback_processing": "Manufacturer chargeback administration",
            "compliance_cost": "340B program compliance and audit preparation",
            "technology_cost": "340B split-billing software and TPA platform",
            "payer_underpayment": "Below-contract reimbursement or denials",
            "bad_debt": "Uncollectible patient responsibility amounts"
        }
    
    def compute_margin_waterfall(
        self,
        entity_id: str,
        gross_reimbursement: float,
        drug_acquisition_cost: float,
        dispensing_cost_per_rx: float,
        n_prescriptions: int,
        tpa_fee_pct: float,
        distribution_fee_per_unit: float,
        n_units: int,
        inventory_carrying_days: int,
        annual_cost_of_capital: float
    ) -> Dict:
        dispensing_total = dispensing_cost_per_rx * n_prescriptions
        tpa_fee = gross_reimbursement * tpa_fee_pct
        distribution_fee = distribution_fee_per_unit * n_units
        
        avg_inventory_value = drug_acquisition_cost * (inventory_carrying_days / 365)
        inventory_cost = avg_inventory_value * annual_cost_of_capital
        
        chargeback_cost = drug_acquisition_cost * 0.005
        
        compliance_cost = gross_reimbursement * 0.008
        
        technology_cost = n_prescriptions * 3.50
        
        payer_underpayment = gross_reimbursement * 0.015
        
        bad_debt = gross_reimbursement * 0.012
        
        total_costs = (
            drug_acquisition_cost +
            dispensing_total +
            tpa_fee +
            distribution_fee +
            inventory_cost +
            chargeback_cost +
            compliance_cost +
            technology_cost +
            payer_underpayment +
            bad_debt
        )
        
        net_margin = gross_reimbursement - total_costs
        margin_pct = (net_margin / gross_reimbursement * 100) if gross_reimbursement > 0 else 0
        
        waterfall = {
            "gross_reimbursement": {"amount": float(gross_reimbursement), "pct_of_gross": 100.0},
            "drug_acquisition": {"amount": float(-drug_acquisition_cost), "pct_of_gross": float(-drug_acquisition_cost / gross_reimbursement * 100) if gross_reimbursement > 0 else 0},
            "dispensing_cost": {"amount": float(-dispensing_total), "pct_of_gross": float(-dispensing_total / gross_reimbursement * 100) if gross_reimbursement > 0 else 0},
            "tpa_fee": {"amount": float(-tpa_fee), "pct_of_gross": float(-tpa_fee_pct * 100)},
            "distribution": {"amount": float(-distribution_fee), "pct_of_gross": float(-distribution_fee / gross_reimbursement * 100) if gross_reimbursement > 0 else 0},
            "inventory_carrying": {"amount": float(-inventory_cost), "pct_of_gross": float(-inventory_cost / gross_reimbursement * 100) if gross_reimbursement > 0 else 0},
            "chargeback_processing": {"amount": float(-chargeback_cost), "pct_of_gross": -0.5},
            "compliance_cost": {"amount": float(-compliance_cost), "pct_of_gross": -0.8},
            "technology_cost": {"amount": float(-technology_cost), "pct_of_gross": float(-technology_cost / gross_reimbursement * 100) if gross_reimbursement > 0 else 0},
            "payer_underpayment": {"amount": float(-payer_underpayment), "pct_of_gross": -1.5},
            "bad_debt": {"amount": float(-bad_debt), "pct_of_gross": -1.2}
        }
        
        return {
            "entity_id": entity_id,
            "waterfall": waterfall,
            "total_costs": float(total_costs),
            "net_margin": float(net_margin),
            "net_margin_pct": float(margin_pct),
            "n_prescriptions": n_prescriptions,
            "margin_per_rx": float(net_margin / n_prescriptions) if n_prescriptions > 0 else 0,
            "profitable": net_margin > 0
        }
    
    def identify_margin_leakage(
        self,
        waterfall: Dict,
        benchmark_comparisons: Dict[str, float]
    ) -> Dict:
        leakage_points = []
        
        component_benchmarks = {
            "tpa_fee": 0.04,
            "distribution": 0.005,
            "inventory_carrying": 0.003,
            "payer_underpayment": 0.01,
            "bad_debt": 0.008
        }
        
        for component, benchmark_pct in component_benchmarks.items():
            actual = abs(waterfall["waterfall"].get(component, {}).get("pct_of_gross", 0))
            if actual > benchmark_pct * 100:
                excess = actual - benchmark_pct * 100
                leakage_points.append({
                    "component": component,
                    "actual_pct": round(actual, 1),
                    "benchmark_pct": round(benchmark_pct * 100, 1),
                    "excess_pct": round(excess, 1),
                    "estimated_annual_impact": float(waterfall["gross_reimbursement"]["amount"] * excess / 100)
                })
        
        leakage_points.sort(key=lambda x: x["estimated_annual_impact"], reverse=True)
        
        total_leakage = sum(l["estimated_annual_impact"] for l in leakage_points)
        
        return {
            "leakage_points": leakage_points,
            "total_identified_leakage": float(total_leakage),
            "leakage_as_pct_of_gross": float(total_leakage / waterfall["gross_reimbursement"]["amount"] * 100) if waterfall["gross_reimbursement"]["amount"] > 0 else 0,
            "top_leakage_priority": leakage_points[0]["component"] if leakage_points else None
        }
    
    def optimize_margin_scenario(
        self,
        base_waterfall: Dict,
        optimization_params: Dict
    ) -> Dict:
        optimized = {
            "tpa_fee_reduction": 0,
            "distribution_optimization": 0,
            "inventory_optimization": 0,
            "payer_underpayment_recovery": 0,
            "bad_debt_reduction": 0
        }
        
        gross = base_waterfall["gross_reimbursement"]["amount"]
        
        if "tpa_rate" in optimization_params:
            current_tpa = abs(base_waterfall["waterfall"]["tpa_fee"]["amount"])
            new_tpa = gross * optimization_params["tpa_rate"]
            optimized["tpa_fee_reduction"] = float(current_tpa - new_tpa)
        
        if "inventory_days" in optimization_params:
            current_inv = abs(base_waterfall["waterfall"]["inventory_carrying"]["amount"])
            reduction_pct = 1 - (optimization_params["inventory_days"] / base_waterfall.get("inventory_days", 30))
            optimized["inventory_optimization"] = float(current_inv * reduction_pct)
        
        total_optimization = sum(optimized.values())
        
        new_margin = base_waterfall["net_margin"] + total_optimization
        new_margin_pct = (new_margin / gross * 100) if gross > 0 else 0
        
        return {
            "base_net_margin": base_waterfall["net_margin"],
            "optimization_components": optimized,
            "total_optimization": float(total_optimization),
            "optimized_net_margin": float(new_margin),
            "optimized_margin_pct": float(new_margin_pct),
            "margin_improvement_pct": float((new_margin_pct - base_waterfall["net_margin_pct"])) if base_waterfall["net_margin_pct"] else 0
        }
