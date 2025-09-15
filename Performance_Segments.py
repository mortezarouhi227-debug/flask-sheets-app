import os, json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import math

# ------------------------
# تنظیمات شیت
# ------------------------
SPREADSHEET_ID = "1VgKCQ8EjVF2sS8rSPdqFZh2h6CuqWAeqSMR56APvwes"
ALL_DATA_SHEET = "All_Data"
OUTPUT_SHEET = "Performance_Segments"
WARNING_SHEET = "Warning_Detail"
QUALITY_SHEET = "Task Time Header"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ------------------------
# اتصال به Google Sheets
# ------------------------
if "GOOGLE_CREDENTIALS" in os.environ:
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
else:
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)

client = gspread.authorize(creds)
ss = client.open_by_key(SPREADSHEET_ID)

all_ws = ss.worksheet(ALL_DATA_SHEET)
try:
    out_ws = ss.worksheet(OUTPUT_SHEET)
except gspread.WorksheetNotFound:
    out_ws = ss.add_worksheet(title=OUTPUT_SHEET, rows="2000", cols="60")

# ------------------------
# توابع کمکی
# ------------------------
def parse_date(s):
    if not s:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except:
            continue
    return None


def find_idx(headers, name):
    target = name.strip().lower().replace(" ", "").replace("_", "")
    for i, h in enumerate(headers):
        if (h or "").strip().lower().replace(" ", "").replace("_", "") == target:
            return i
    return -1


def parse_percent(x):
    if not x:
        return None
    try:
        v = float(str(x).replace("%", "").replace(",", ""))
        if v <= 1:
            v *= 100
        return v
    except:
        return None


def collect_counts(ws_name, name_col, date_col, count_col, start_date, end_date):
    """جمع آوری تعداد خطا/وارنینگ برای هر نفر"""
    m = {}
    try:
        ws = ss.worksheet(ws_name)
    except gspread.WorksheetNotFound:
        return m

    vals = ws.get_all_values()
    if not vals or len(vals) < 2:
        return m

    hdr, body = vals[0], vals[1:]

    def find_idx2(c):
        t = c.strip().lower().replace(" ", "").replace("_", "")
        for i, h in enumerate(hdr):
            if (h or "").strip().lower().replace(" ", "").replace("_", "") == t:
                return i
        return -1

    i_n, i_d, i_c = find_idx2(name_col), find_idx2(date_col), find_idx2(count_col)
    if -1 in (i_n, i_d, i_c):
        return m

    for r in body:
        nm = r[i_n]
        d = parse_date(r[i_d]) if i_d < len(r) else None
        if not nm or not d:
            continue
        if d < start_date or d > end_date:
            continue
        try:
            cnt = int(float(r[i_c])) if r[i_c] else 0
        except:
            cnt = 0
        m[nm] = m.get(nm, 0) + cnt
    return m

# ------------------------
# تابع اصلی
# ------------------------
def main():
    # خواندن فیلترها از شیت Performance_Segments
    start_date = parse_date(out_ws.acell("B1").value)
    end_date = parse_date(out_ws.acell("C1").value)
    shift_val = (out_ws.acell("D1").value or "").strip()

    try:
        days_threshold = int(out_ws.acell("F1").value)
    except:
        days_threshold = 10

    try:
        perf_threshold = float((out_ws.acell("H1").value or "95").replace("%", "").strip())
    except:
        perf_threshold = 95

    vals = all_ws.get_all_values()
    headers, rows = vals[0], vals[1:]

    idx_full = find_idx(headers, "full_name")
    idx_date = find_idx(headers, "date")
    idx_hour = find_idx(headers, "hour")
    idx_perf = find_idx(headers, "performance_with_rotation")
    idx_shift = find_idx(headers, "shift")

    # گرفتن خطاها و وارنینگ‌ها
    warn_map = collect_counts(WARNING_SHEET, "full_name", "date", "warning_count", start_date, end_date)
    qual_map = collect_counts(QUALITY_SHEET, "full_name", "date", "error_count", start_date, end_date)

    # پردازش دیتا
    user_data = {}
    for r in rows:
        name = r[idx_full] if idx_full < len(r) else ""
        d = parse_date(r[idx_date]) if idx_date < len(r) else None
        if not name or not d:
            continue
        if d < start_date or d > end_date:
            continue
        sh = r[idx_shift] if idx_shift < len(r) else ""
        if shift_val and sh != shift_val:
            continue
        try:
            hr = int(float(r[idx_hour])) if idx_hour < len(r) and r[idx_hour] else None
        except:
            hr = None
        perf = parse_percent(r[idx_perf]) if idx_perf < len(r) else None
        user_data.setdefault(name, {}).setdefault(d, []).append((hr, perf))

    results = []
    for name, dates in user_data.items():
        daily_means, presence_days = [], 0
        for d, logs in dates.items():
            perfs = [p for h, p in logs if p is not None]
            if perfs:
                daily_means.append(sum(perfs) / len(perfs))
            has_day = any((h is not None and h >= 6) for h, _ in logs)
            has_night = any((h is not None and 0 <= h <= 5) for h, _ in logs)
            if has_day or (has_night and not has_day):
                presence_days += 1
        if daily_means:
            avg_perf = sum(daily_means) / len(daily_means)
            results.append(
                (
                    name,
                    avg_perf,
                    presence_days,
                    "" if warn_map.get(name, 0) == 0 else warn_map.get(name, 0),
                    "" if qual_map.get(name, 0) == 0 else qual_map.get(name, 0),
                )
            )

    # دسته‌بندی به 4 جدول
    table1 = [r for r in results if r[1] >= perf_threshold and r[2] >= days_threshold]
    table2 = [r for r in results if r[1] >= perf_threshold and r[2] < days_threshold]
    table3 = [r for r in results if r[1] < perf_threshold and r[2] >= days_threshold]
    table4 = [r for r in results if r[1] < perf_threshold and r[2] < days_threshold]

    tables = [table1, table2, table3, table4]
    titles = [
        "پرفورمنس بالا - توالی بالا",
        "پرفورمنس بالا - توالی پایین",
        "پرفورمنس پایین - توالی بالا",
        "پرفورمنس پایین - توالی پایین",
    ]

    # پاکسازی فقط از ردیف 5 به بعد
    last_row = out_ws.row_count
    last_col = out_ws.col_count
    out_ws.batch_clear([f"A5:{gspread.utils.rowcol_to_a1(last_row, last_col)}"])

    starts = ["A", "G", "M", "S"]
    mean_cells = ["F3", "L3", "R3", "X3"]

    for i, tbl in enumerate(tables):
        col = starts[i]
        rng = f"{col}3:{chr(ord(col) + 4)}3"
        out_ws.update(range_name=rng, values=[[titles[i]]])
        out_ws.merge_cells(rng)
        headers = ["نام", "میانگین پرفورمنس", "توالی حضور", "Warning", "Quality"]
        out_ws.update(range_name=f"{col}4", values=[headers])
        if tbl:
            tbl_sorted = sorted(tbl, key=lambda x: x[1], reverse=True)
            data = [[n, f"{p:.1f}%", d, w, q] for n, p, d, w, q in tbl_sorted]
            out_ws.update(range_name=f"{col}5", values=data)
            mean_perf = sum([x[1] for x in tbl_sorted]) / len(tbl_sorted)
            out_ws.update(range_name=mean_cells[i], values=[[f"{mean_perf:.1f}%"]])

    # جدول پنجم (انتخاب درصدی)
    perc_cells = ["AA1", "AB1", "AC1", "AD1"]
    percents = []
    for c in perc_cells:
        val = out_ws.acell(c).value
        try:
            perc = float(val.replace("%", "").strip())
        except:
            perc = 0
        percents.append(perc)

    out_ws.update(range_name="AA3", values=[["جدول یک", "جدول دو", "جدول سه", "جدول چهار"]])
    headers2 = [["اسامی جدول یک", "اسامی جدول دو", "اسامی جدول سه", "اسامی جدول چهار"]]
    out_ws.update(range_name="AA4", values=headers2)

    final = []
    max_len = 0
    cols = []
    for t, p in zip(tables, percents):
        tbl_sorted = sorted(t, key=lambda x: x[1], reverse=True)
        k = math.ceil(len(tbl_sorted) * p / 100)
        sel = [r[0] for r in tbl_sorted[:k]]
        cols.append(sel)
        max_len = max(max_len, len(sel))

    for i in range(max_len):
        row = []
        for c in cols:
            row.append(c[i] if i < len(c) else "")
        final.append(row)

    if final:
        out_ws.update(range_name="AA5", values=final)

    msg = "[OK] Performance_Segments updated (rows 1–4 fixed, only rows 5+ refreshed)."
    print(msg)
    return msg
