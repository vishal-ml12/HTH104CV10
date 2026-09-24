import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from backend.database.session import engine, Base
from backend.models import WasteAnalysis, DetectedObject, StreamAnalysis


def migrate():
    print("Starting MySQL schema migration for Phase 2 Stream-Wise Contamination & Yield Optimization...")
    with engine.connect() as conn:
        # 1. Update waste_analysis columns
        res = conn.execute(text("SHOW COLUMNS FROM waste_analysis;")).fetchall()
        existing_cols = {row[0].lower() for row in res}

        phase2_waste_cols = [
            ("recommendation_reason", "VARCHAR(500) NULL"),
            ("processing_route", "VARCHAR(64) NULL"),
            ("input_mass_kg", "FLOAT NOT NULL DEFAULT 100.0"),
            ("recoverable_mass_kg", "FLOAT NULL"),
            ("waste_loss_kg", "FLOAT NULL"),
        ]

        for col_name, col_type in phase2_waste_cols:
            if col_name.lower() not in existing_cols:
                try:
                    conn.execute(text(f"ALTER TABLE waste_analysis ADD COLUMN {col_name} {col_type};"))
                    conn.commit()
                    print(f"Added column '{col_name}' to waste_analysis.")
                except Exception as e:
                    print(f"Error adding {col_name} to waste_analysis: {e}")
            else:
                print(f"Column '{col_name}' already exists in waste_analysis.")

        # 2. Update detected_objects columns
        res_objs = conn.execute(text("SHOW COLUMNS FROM detected_objects;")).fetchall()
        existing_obj_cols = {row[0].lower() for row in res_objs}

        phase2_obj_cols = [
            ("contamination_score", "FLOAT NOT NULL DEFAULT 0.0"),
            ("contamination_category", "VARCHAR(64) NOT NULL DEFAULT 'none'"),
        ]

        for col_name, col_type in phase2_obj_cols:
            if col_name.lower() not in existing_obj_cols:
                try:
                    conn.execute(text(f"ALTER TABLE detected_objects ADD COLUMN {col_name} {col_type};"))
                    conn.commit()
                    print(f"Added column '{col_name}' to detected_objects.")
                except Exception as e:
                    print(f"Error adding {col_name} to detected_objects: {e}")
            else:
                print(f"Column '{col_name}' already exists in detected_objects.")

        # 3. Create stream_analyses table
        Base.metadata.create_all(bind=engine)
        conn.commit()
        print("Phase 2 MySQL schema migration completed successfully!")


if __name__ == "__main__":
    migrate()
