"""
HRIS CSV Analyzer
=================
Parses, validates, and analyzes an HRIS CSV file entirely in memory.
Returns a structured results dict with summary stats, row-level validation
errors, root employees, manager direct-report counts, and cycle detection.
"""

import csv
import io


EXPECTED_COLUMNS = {
    "employee_id",
    "employee_name",
    "email",
    "manager_id",
    "manager_email",
    "department",
}


def analyze(csv_text: str) -> dict:
    """
    Analyze raw CSV text and return a results dictionary.

    Parameters
    ----------
    csv_text : str
        The full contents of the uploaded CSV file as a UTF-8 string.

    Returns
    -------
    dict with keys:
        total_rows, accepted_count, errors, root_employees,
        managers, cycle_participants
    """
    reader = csv.DictReader(io.StringIO(csv_text))

    # ── Normalise header names ──────────────────────────────────────────
    if reader.fieldnames:
        reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]

    # ── First pass: parse rows, strip cells, assign source row numbers ──
    raw_rows = []
    for i, row in enumerate(reader, start=2):  # row 1 = header
        cleaned = {k.strip(): (v.strip() if v else "") for k, v in row.items()}
        cleaned["_source_row"] = i
        raw_rows.append(cleaned)

    total_rows = len(raw_rows)
    errors: list[dict] = []
    seen_ids: set[str] = set()
    accepted: list[dict] = []

    # ── Second pass: row-level validation ───────────────────────────────
    for row in raw_rows:
        eid = row.get("employee_id", "")
        ename = row.get("employee_name", "")
        email = row.get("email", "")
        mid = row.get("manager_id", "")
        src = row["_source_row"]

        # Required-field checks
        if not eid:
            errors.append({
                "row": src,
                "employee_id": eid or "(blank)",
                "field": "employee_id",
                "message": "Missing employee_id",
            })
            continue  # cannot accept a row with no id

        if not ename:
            errors.append({
                "row": src,
                "employee_id": eid,
                "field": "employee_name",
                "message": "Missing employee_name",
            })

        if not email:
            errors.append({
                "row": src,
                "employee_id": eid,
                "field": "email",
                "message": "Missing email",
            })

        # Duplicate check
        if eid in seen_ids:
            errors.append({
                "row": src,
                "employee_id": eid,
                "field": "employee_id",
                "message": f"Duplicate employee_id '{eid}'",
            })
        else:
            seen_ids.add(eid)

        # Self-manager check
        if mid and mid == eid:
            errors.append({
                "row": src,
                "employee_id": eid,
                "field": "manager_id",
                "message": "Employee cannot be their own manager",
            })

        accepted.append(row)

    # Build lookup for accepted employees by id
    emp_by_id: dict[str, dict] = {}
    for row in accepted:
        eid = row["employee_id"]
        if eid not in emp_by_id:
            emp_by_id[eid] = row

    # ── Dangling manager_id check (needs full id set) ───────────────────
    for row in accepted:
        mid = row.get("manager_id", "")
        if mid and mid not in emp_by_id:
            errors.append({
                "row": row["_source_row"],
                "employee_id": row["employee_id"],
                "field": "manager_id",
                "message": f"manager_id '{mid}' not found in dataset",
            })

    # Sort errors by source row number for consistent display
    errors.sort(key=lambda e: e["row"])

    # ── Root employees (no manager) ─────────────────────────────────────
    root_employees = [
        {
            "employee_id": r["employee_id"],
            "employee_name": r["employee_name"],
            "department": r.get("department", ""),
        }
        for r in accepted
        if not r.get("manager_id", "")
    ]

    # ── Manager direct-report counts ────────────────────────────────────
    report_counts: dict[str, int] = {}
    for row in accepted:
        mid = row.get("manager_id", "")
        if mid:
            report_counts[mid] = report_counts.get(mid, 0) + 1

    managers = sorted(
        [
            {
                "manager_id": mid,
                "manager_name": emp_by_id[mid]["employee_name"] if mid in emp_by_id else "(unknown)",
                "direct_reports": count,
            }
            for mid, count in report_counts.items()
        ],
        key=lambda m: m["direct_reports"],
        reverse=True,
    )

    # ── Cycle detection ─────────────────────────────────────────────────
    cycle_ids: set[str] = set()
    for eid in emp_by_id:
        visited: set[str] = set()
        current = eid
        while current and current in emp_by_id:
            if current in visited:
                # Everything still in the walk from 'current' onward is in a cycle
                cycle_ids.update(visited)
                break
            visited.add(current)
            current = emp_by_id[current].get("manager_id", "")

    cycle_participants = [
        {
            "employee_id": eid,
            "employee_name": emp_by_id[eid]["employee_name"],
        }
        for eid in sorted(cycle_ids)
        if eid in emp_by_id
    ]

    return {
        "total_rows": total_rows,
        "accepted_count": len(accepted),
        "errors": errors,
        "root_employees": root_employees,
        "managers": managers,
        "cycle_participants": cycle_participants,
    }
