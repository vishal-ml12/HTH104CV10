"""
Phase 3 Virtual Conveyor Belt Software Simulation Engine.

Simulates an industrial automated optical sorting conveyor belt in software:
AI CAMERA ➔ MOVING MIXED WASTE ➔ OBJECT DETECTION ➔ SORTING DECISION ➔ 6 VIRTUAL LANES

Features:
- Moving waste items with normalized conveyor coordinates (X: 0 to 100).
- Optical inspection zone, Diverter decision trigger line, and 6 virtual sorting lanes.
- Live object counters: Total Processed, Plastic, Glass, Metal, Paper, Organic, Manual Review.
- Current active object telemetry (ID, material, confidence, contamination, quality, yield, recommendation).
- Timestamped chronological event logs.
- Future-ready architecture for PLC/Modbus/MQTT industrial actuator signals.

IMPORTANT DISCLAIMER:
This is a SOFTWARE SIMULATION modeling industrial sorting mechanics.
It does not connect to or drive physical conveyor belts, pneumatics, PLCs, or robotic sorters.
"""

from typing import Dict, Any, List
import random
import time

STREAM_LANES = {
    "plastic": {"name": "Plastic Lane", "bin": "Lane 1 - Air Jet Ejector", "color": "blue"},
    "glass": {"name": "Glass Lane", "bin": "Lane 2 - Mechanical Paddle", "color": "amber"},
    "metal": {"name": "Metal Lane", "bin": "Lane 3 - Eddy Current Separator", "color": "slate"},
    "paper": {"name": "Paper Lane", "bin": "Lane 4 - Vacuum Suction Diverter", "color": "yellow"},
    "organic": {"name": "Organic Lane", "bin": "Lane 5 - Biological Recovery Bin", "color": "emerald"},
    "review": {"name": "Manual Review Lane", "bin": "Lane 6 - Manual QC Conveyor", "color": "rose"},
}


class VirtualConveyorSimulation:
    def __init__(self):
        self.state = "RUNNING"  # RUNNING | PAUSED | STOPPED
        self.speed = 1.0        # Conveyor speed multiplier (0.5x, 1.0x, 2.0x)
        self.total_processed = 0
        self.stream_counts = {
            "plastic": 0,
            "glass": 0,
            "metal": 0,
            "paper": 0,
            "organic": 0,
            "review": 0,
        }
        self.active_items: List[Dict[str, Any]] = []
        self.item_counter = 1
        self.event_logs: List[str] = []
        self.current_object: Dict[str, Any] = {}
        self._seed_initial_items()

    def _seed_initial_items(self):
        """Seed initial items along the conveyor belt for immediate live visualization."""
        initial_configs = [
            ("plastic", 0.94, 12.0, "none", 15.0),
            ("glass", 0.88, 18.0, "organic_residue", 45.0),
            ("metal", 0.91, 14.0, "label_adhesive", 75.0),
        ]
        for mat, conf, contam, cat, x_pos in initial_configs:
            self._create_item(material=mat, confidence=conf, contamination=contam, category=cat, x_pos=x_pos)

    def _create_item(
        self,
        material: str = "plastic",
        confidence: float = 0.90,
        contamination: float = 14.0,
        category: str = "none",
        x_pos: float = 0.0
    ):
        item_id = f"BELT_OBJ_{self.item_counter}"
        self.item_counter += 1

        quality = max(0.0, min(100.0, round(100.0 - (contamination * 1.15), 1)))
        base_recovery = {"plastic": 88.0, "glass": 92.0, "metal": 95.0, "paper": 82.0, "organic": 75.0}.get(material, 70.0)
        yield_score = max(0.0, min(98.0, round(base_recovery - 3.5 - (contamination * 0.95), 1)))

        if confidence < 0.50:
            assigned_stream = "review"
            rec = "Manual inspection conveyor diversion"
            route = "MANUAL_REVIEW_FLAGGED"
        elif contamination < 15.0:
            assigned_stream = material
            rec = "Direct mechanical reprocessing"
            route = "DIRECT_RECYCLING"
        elif contamination <= 35.0:
            assigned_stream = material
            rec = "Pre-processing recommended"
            route = "PRE_PROCESSING_WASHING"
        else:
            assigned_stream = material
            rec = "Secondary processing / shredding required"
            route = "SECONDARY_PROCESSING_SHREDDING"

        item = {
            "object_id": item_id,
            "material": material,
            "confidence": confidence,
            "stream": assigned_stream,
            "lane_name": STREAM_LANES[assigned_stream]["name"],
            "diverter_bin": STREAM_LANES[assigned_stream]["bin"],
            "contamination_score": contamination,
            "contamination_category": category,
            "quality_score": quality,
            "recycling_yield": yield_score,
            "processing_route": route,
            "recommendation": rec,
            "recommendation_reason": f"Contamination = {contamination}%, Quality = {quality}/100, Est. Yield = {yield_score}%",
            "x": x_pos,
            "stage": "ingestion" if x_pos < 25 else ("inspection" if x_pos < 55 else ("diverter" if x_pos < 75 else "sorted")),
            "created_at": time.strftime("%H:%M:%S"),
        }
        self.active_items.append(item)
        return item

    def step(self, delta_time: float = 1.0) -> Dict[str, Any]:
        """
        Advance virtual conveyor simulation by one step.
        """
        if self.state == "PAUSED":
            return self.get_snapshot()

        step_dist = 6.0 * self.speed * delta_time

        surviving_items = []
        now_str = time.strftime("%H:%M:%S")

        for it in self.active_items:
            prev_x = it["x"]
            it["x"] += step_dist

            # Update current object for inspector
            if 30 <= it["x"] <= 75:
                self.current_object = it

            # Stage transitions and events
            if prev_x < 25 <= it["x"]:
                it["stage"] = "inspection"
                self.event_logs.append(
                    f"[{now_str}] Optical sensor scanned {it['object_id']} ({it['material'].upper()} - {int(it['confidence']*100)}% conf). Contamination: {it['contamination_score']}%."
                )
            elif prev_x < 65 <= it["x"]:
                it["stage"] = "diverter"
                self.event_logs.append(
                    f"[{now_str}] {it['object_id']} reached Diverter Decision line -> Actuating {it['diverter_bin']}."
                )
            elif it["x"] >= 95:
                it["stage"] = "sorted"
                stream = it["stream"]
                self.total_processed += 1
                self.stream_counts[stream] = self.stream_counts.get(stream, 0) + 1
                self.event_logs.append(
                    f"[{now_str}] {it['object_id']} successfully diverted into {STREAM_LANES[stream]['name']}."
                )
                continue  # Removed from belt as it lands in bin

            surviving_items.append(it)

        self.active_items = surviving_items

        # Spawn new items at entrance if conveyor has space
        if len(self.active_items) < 4:
            min_x = min([it["x"] for it in self.active_items], default=100.0)
            if min_x > 25.0:
                mat = random.choice(["plastic", "plastic", "metal", "glass", "paper", "organic"])
                conf = round(random.uniform(0.75, 0.96), 2)
                contam = round(random.uniform(6.0, 32.0), 1)
                cat = random.choice(["none", "label_adhesive", "organic_residue", "cross_polymer"])
                new_item = self._create_item(material=mat, confidence=conf, contamination=contam, category=cat, x_pos=0.0)
                self.event_logs.append(
                    f"[{now_str}] Mixed waste object {new_item['object_id']} ({mat.upper()}) entered conveyor infeed."
                )

        # Keep last 50 logs
        if len(self.event_logs) > 50:
            self.event_logs = self.event_logs[-50:]

        return self.get_snapshot()

    def get_snapshot(self) -> Dict[str, Any]:
        """Return full live telemetry snapshot of the virtual conveyor belt."""
        total_p = max(1, self.total_processed)
        avg_contam = round(
            sum(it.get("contamination_score", 15.0) for it in self.active_items) / max(1, len(self.active_items)), 1
        )
        avg_quality = round(max(0.0, 100.0 - (avg_contam * 1.15)), 1)
        avg_yield = round(max(0.0, 86.0 - 3.5 - (avg_contam * 0.95)), 1)

        return {
            "simulation_state": self.state,
            "conveyor_speed": self.speed,
            "belt_length": 100.0,
            "diverter_line_x": 65.0,
            "total_objects_processed": self.total_processed,
            "stream_counters": self.stream_counts,
            "active_belt_items": self.active_items,
            "current_inspected_object": self.current_object,
            "live_statistics": {
                "average_contamination": avg_contam,
                "average_quality_score": avg_quality,
                "average_recycling_yield": avg_yield,
            },
            "diverter_event_logs": self.event_logs[-20:],
            "system_health": {
                "belt_motor": "NORMAL (Simulated 1.2 m/s)",
                "optical_sorter_fps": 30.0,
                "actuator_latency_ms": 12.5,
                "plc_ready": True,
            },
            "disclaimer": "Software-based conveyor diversion simulation. No physical machinery connected.",
        }

    def start(self):
        """Resume / start the virtual conveyor belt simulation."""
        self.state = "RUNNING"
        self.event_logs.append(f"[{time.strftime('%H:%M:%S')}] Virtual conveyor belt started (Speed: {self.speed}x).")
        return self.get_snapshot()

    def pause(self):
        """Pause the virtual conveyor belt simulation."""
        self.state = "PAUSED"
        self.event_logs.append(f"[{time.strftime('%H:%M:%S')}] Virtual conveyor belt paused.")
        return self.get_snapshot()

    def set_speed(self, speed: float):
        """Update simulation conveyor speed multiplier (e.g. 0.5x, 1.0x, 2.0x)."""
        self.speed = max(0.25, min(5.0, float(speed)))
        self.event_logs.append(f"[{time.strftime('%H:%M:%S')}] Conveyor speed adjusted to {self.speed}x.")
        return self.get_snapshot()

    def reset(self):
        """Reset virtual conveyor belt state and counters."""
        self.total_processed = 0
        self.stream_counts = {k: 0 for k in self.stream_counts}
        self.active_items = []
        self.item_counter = 1
        self.event_logs = [f"[{time.strftime('%H:%M:%S')}] Virtual conveyor belt reset to initial state."]
        self.current_object = {}
        self._seed_initial_items()
        return self.get_snapshot()



# Global singleton instance
conveyor_simulation = VirtualConveyorSimulation()
