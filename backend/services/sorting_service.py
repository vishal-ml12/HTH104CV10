"""
Virtual Sorting Engine and Stream Routing Service.

Simulates automated material diversion across 6 distinct recycling streams:
- Plastic Stream
- Glass Stream
- Metal Stream
- Paper / Cardboard Stream
- Organic Stream
- Human Review Queue (Low confidence / ambiguous items)

IMPORTANT:
This is a software-based virtual sorting simulation designed to model pneumatic/robotic
ejection and optical sorting behavior. It does not control physical actuators.
"""

from typing import Dict, Any, List
from datetime import datetime


STREAM_DEFINITIONS = {
    "plastic": {
        "name": "Plastic Stream",
        "description": "Thermoplastic polymers, PET bottles, HDPE containers",
        "color": "blue",
        "diverter_bin": "Bin 1 - Air Jet Ejector",
    },
    "glass": {
        "name": "Glass Stream",
        "description": "Container glass, bottles, jars, cullet",
        "color": "amber",
        "diverter_bin": "Bin 2 - Mechanical Paddle",
    },
    "metal": {
        "name": "Metal Stream",
        "description": "Ferrous & non-ferrous aluminum cans, tinplate",
        "color": "slate",
        "diverter_bin": "Bin 3 - Eddy Current / Magnetic Separator",
    },
    "paper": {
        "name": "Paper/Cardboard Stream",
        "description": "Corrugated fiberboard, kraft paper, cellulose packaging",
        "color": "yellow",
        "diverter_bin": "Bin 4 - Vacuum Suction Diverter",
    },
    "organic": {
        "name": "Organic Stream",
        "description": "Compostable organic matter, food packaging residues",
        "color": "emerald",
        "diverter_bin": "Bin 5 - Biological Recovery Bin",
    },
    "review": {
        "name": "Human Review Queue",
        "description": "Uncertain items (<50% confidence), composite multi-layers, or contaminated objects",
        "color": "rose",
        "diverter_bin": "Manual Verification Conveyor",
    },
}

MATERIAL_TO_STREAM: Dict[str, str] = {
    "plastic": "plastic",
    "glass": "glass",
    "metal": "metal",
    "paper": "paper",
    "cardboard": "paper",
    "organic": "organic",
    "food": "organic",
    "mixed_waste": "review",
    "unknown": "review",
}


class VirtualSortingEngine:
    @staticmethod
    def sort_stream(detected_objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sort detected objects into separate virtual material streams and calculate composition statistics.
        """
        total_objects = len(detected_objects)

        # Initialize stream buckets
        stream_items: Dict[str, List[Dict[str, Any]]] = {
            "plastic": [],
            "glass": [],
            "metal": [],
            "paper": [],
            "organic": [],
            "review": [],
        }

        diverter_logs: List[str] = []
        now_str = datetime.now().strftime("%H:%M:%S")

        for item in detected_objects:
            material = str(item.get("material", "unknown")).lower()
            confidence = float(item.get("confidence", 0.0))
            obj_id = item.get("object_id", "obj")

            # Routing logic: items with low confidence (<0.50) or unknown always go to review
            if confidence < 0.50 or material in ["unknown", "mixed_waste"]:
                assigned_stream = "review"
                status = "pending_review"
            elif material == "plastic":
                assigned_stream = "plastic"
                status = "sorted"
            elif material == "glass":
                assigned_stream = "glass"
                status = "sorted"
            elif material == "metal":
                assigned_stream = "metal"
                status = "sorted"
            elif material in ["paper", "cardboard"]:
                assigned_stream = "paper"
                status = "sorted"
            elif material in ["organic", "food"]:
                assigned_stream = "organic"
                status = "sorted"
            else:
                assigned_stream = "review"
                status = "pending_review"

            # Enrich item dictionary with virtual sorting information
            item["stream"] = assigned_stream
            item["status"] = status
            item["stream_name"] = STREAM_DEFINITIONS[assigned_stream]["name"]

            stream_items[assigned_stream].append(item)

            # Generate simulated virtual diverter event log
            bin_name = STREAM_DEFINITIONS[assigned_stream]["diverter_bin"]
            diverter_logs.append(
                f"[{now_str}] Item {obj_id} ({material.upper()} - {int(confidence*100)}% conf) "
                f"virtually routed to {bin_name}"
            )

        # Calculate stream composition statistics
        composition_stats: Dict[str, Any] = {}
        for stream_key, items in stream_items.items():
            count = len(items)
            pct = round((count / total_objects * 100.0), 1) if total_objects > 0 else 0.0
            composition_stats[stream_key] = {
                "name": STREAM_DEFINITIONS[stream_key]["name"],
                "color": STREAM_DEFINITIONS[stream_key]["color"],
                "count": count,
                "percentage": pct,
                "diverter_bin": STREAM_DEFINITIONS[stream_key]["diverter_bin"],
                "items": items,
            }

        # Determine dominant stream
        sorted_streams = sorted(composition_stats.items(), key=lambda kv: kv[1]["count"], reverse=True)
        dominant_stream = sorted_streams[0][0] if sorted_streams and sorted_streams[0][1]["count"] > 0 else "unknown"

        return {
            "total_objects": total_objects,
            "dominant_stream": dominant_stream,
            "streams": composition_stats,
            "diverter_events": diverter_logs,
            "simulation_notice": "Software-based virtual sorting simulation. Does not control physical pneumatic or robotic diverters.",
        }


virtual_sorting_engine = VirtualSortingEngine()


def get_sorting_engine() -> VirtualSortingEngine:
    return virtual_sorting_engine
