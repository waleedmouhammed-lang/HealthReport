import logging
import pandas as pd
from datetime import datetime
from config import CSV_PATH, EXCEL_PATH, OUTPUT_DIR

log = logging.getLogger(__name__)

def export_data(df):
    """Export DataFrame to both CSV and Excel in the output folder"""

    # Create output folder if it doesn't exist
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Export CSV
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    log.info("[export] CSV saved -> %s", CSV_PATH)

    # Export Excel with basic formatting
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Activities")

        # Auto-fit column widths
        ws = writer.sheets["Activities"]
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col) + 4
            ws.column_dimensions[col[0].column_letter].width = min(max_len, 40)

    log.info("[export] Excel saved -> %s", EXCEL_PATH)
    log.info(
        "[export] %s rows exported at %s",
        len(df),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
