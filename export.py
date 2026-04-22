import os
import pandas as pd
from datetime import datetime

OUTPUT_DIR = "output"

def export_data(df):
    """Export DataFrame to both CSV and Excel in the output folder"""

    # Create output folder if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    csv_path   = os.path.join(OUTPUT_DIR, "strava_activities.csv")
    excel_path = os.path.join(OUTPUT_DIR, "strava_activities.xlsx")

    # Export CSV
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"[export] CSV saved  → {csv_path}")

    # Export Excel with basic formatting
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Activities")

        # Auto-fit column widths
        ws = writer.sheets["Activities"]
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col) + 4
            ws.column_dimensions[col[0].column_letter].width = min(max_len, 40)

    print(f"[export] Excel saved → {excel_path}")
    print(f"[export] {len(df)} rows exported at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")