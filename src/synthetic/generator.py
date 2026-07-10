"""Synthetic dataset generator creating golden test dataset JSON files."""

from __future__ import annotations

import json
import os
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.synthetic.templates import SCENARIO_TEMPLATES

DEFAULT_DATASET_PATH = os.path.join("evaluation", "golden_dataset", "golden_dataset.json")


class SyntheticDatasetGenerator:
    """Generates 50-100 structured test tickets representing ground truth cases."""

    def __init__(self, output_path: str = DEFAULT_DATASET_PATH) -> None:
        self.output_path = output_path

    def generate_golden_dataset(self, num_samples: int = 50) -> List[Dict[str, Any]]:
        """Synthesize and format benchmark tickets list."""
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        samples: List[Dict[str, Any]] = []
        
        for i in range(num_samples):
            tpl = random.choice(SCENARIO_TEMPLATES)
            
            # Format custom template fields
            date_ref = (datetime.utcnow() - timedelta(days=random.randint(1, 40))).strftime("%Y-%m-%d")
            days_diff = random.randint(2, 35)
            ticket_num = random.randint(10000, 99999)
            hours = random.randint(4, 48)
            version = random.choice(["v2.1.0", "v2.5.4", "v3.0.0"])
            
            content = tpl["content_template"].format(
                date_ref=date_ref,
                days_diff=days_diff,
                ticket_num=ticket_num,
                hours=hours,
                version=version
            )
            
            # Formulate ground truth answers based on templates
            if tpl["category"] == "billing":
                ground_truth = f"Billing policy states that subscription refunds are valid within 30 days. For {days_diff} days ago: refund eligibility is {'eligible' if days_diff <= 30 else 'ineligible'}."
            elif tpl["category"] == "account_access":
                ground_truth = "Account access keys provision requires security compliance checks verification first."
            elif tpl["category"] == "technical_support":
                ground_truth = f"SLA breach check: Support level SLA guidelines specify response deadlines. Elapsed open hours is {hours}."
            else:
                ground_truth = f"Catalog specifications query for CloudSync Pro version {version}."
                
            sample = {
                "id": f"gt-{i+1:03d}",
                "category": tpl["category"],
                "title": tpl["title"],
                "content": content,
                "priority": tpl["priority"],
                "department": tpl["department"],
                "ground_truth": ground_truth,
                "metadata": {
                    "tier": tpl["metadata_template"].get("tier", "standard"),
                    "sla_tier": tpl["metadata_template"].get("sla_tier", "bronze")
                }
            }
            samples.append(sample)
            
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(samples, f, indent=4)
            
        return samples
