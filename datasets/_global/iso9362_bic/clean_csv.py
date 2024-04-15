import re
import sys
import csv
from typing import List, Optional, Dict

NORM_RE = re.compile(r"\s+")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

BIC_NAME: Dict[str, str] = {}
BIC_ADDR: Dict[str, str] = {}


def norm_cell(text: str) -> str:
    return NORM_RE.sub(" ", text).strip()


def norm_header(text: str) -> str:
    return text.replace(" ", "").replace(".", "")


def is_header(row: List[str]) -> bool:
    if len(row) == 0:
        return False
    cell = row[0]
    return "Record" in cell or "Creation" in cell


def is_date(cell: Optional[str]) -> bool:
    if cell is None or not len(cell):
        return True
    return DATE_RE.match(cell) is not None


def merge_broken_lines(csv_in: str, csv_out: str) -> None:
    headers = None
    with open(csv_in, "r") as f_in:
        reader = csv.reader(f_in)
        for row_idx, row in enumerate(reader):
            if headers is None:
                headers = row
                continue
            if headers[0] != "Record creation date":
                if row_idx > 3:
                    raise Exception("Could not construct header")
                for idx, cell in enumerate(row):
                    headers[idx] = f"{headers[idx]} {cell}"
            else:
                header_rows = row_idx
                break
    
    with open(csv_in, "r") as f_in, open(csv_out, "w") as f_out:
        reader = csv.reader(f_in)
        writer = None
        output_row = None
        first_row = True
        for idx, row in enumerate(reader):
            if row[0].startswith("Record"):
                headers = row 
            if row["Record creation date"] == "":
                for k, v in row.items():
                    output_row[k] = f"{output_row[k]} {v}"
            else:
                output_row = row
                if not first_row:
                    print(row)
                    writer.writerow(output_row)
            first_row = False
        writer.writerow(output_row)
            

def clean_csv(csv_in: str, csv_out: str) -> None:
    with open(csv_in, "r") as f_in, open(csv_out, "w") as f_out:
        reader = csv.reader(f_in, dialect=csv.unix_dialect)
        writer: Optional[csv.DictWriter] = None
        headers: Optional[List[str]] = None
        current: Dict[str, str] = {}
        for row in reader:
            row = [norm_cell(c) for c in row]
            if is_header(row):
                if headers is None:
                    headers = [norm_header(c) for c in row]
                    assert "BIC" in headers, headers
                    assert "Full legal name" in headers, headers
                    assert "BrchCode" in headers, headers
                    headers.append("FullBIC")
                    writer = csv.DictWriter(f_out, headers, dialect=csv.unix_dialect)
                    writer.writeheader()
                continue
            if writer is None or headers is None:
                continue
            data = {k: v for k, v in zip(headers, row) if len(v)}
            if not is_date(data.get("RecordCreationDate")):
                # print("FAIL: Creation date", data)
                continue
            if not is_date(data.get("LastUpdateDate")):
                # print("FAIL: Last update", data)
                continue
            ostatus = data.get("RecOwnershipStatus")
            if ostatus and ostatus not in ("TPRG", "SREG"):
                # print("FAIL: Ownership status", data)
                continue
            fbic = data.get("BIC", "") + data.get("BrchCode", "")
            data["FullBIC"] = fbic
            if not data.get("BIC"):
                # print("FAIL: Empty BIC", data)
                for k, v in data.items():
                    current[k] = norm_cell(f"{current.get(k, '')} {v}")
                    # print("APPEND", current[k])
                continue
            if current.get("FullBIC") != fbic:
                cbic = current.get("BIC")
                if cbic and not current.get("BrchCode"):
                    if current.get("FullLegalName") and cbic not in BIC_NAME:
                        BIC_NAME[cbic] = current["FullLegalName"]
                    if current.get("RegisteredAddress") and cbic not in BIC_ADDR:
                        BIC_ADDR[cbic] = current["RegisteredAddress"]

                if cbic:
                    if not current.get("FullLegalName") and cbic in BIC_NAME:
                        current["FullLegalName"] = BIC_NAME[cbic]
                    if not current.get("RegisteredAddress") and cbic in BIC_ADDR:
                        current["RegisteredAddress"] = BIC_ADDR[cbic]

                if len(current):
                    writer.writerow(current)
                current = data

        if writer is not None and len(current):
            writer.writerow(current)


if __name__ == "__main__":
    csv_in = sys.argv[1]
    merged_out = f"{csv_in}.clean.csv"
    clean_out = f"{csv_in}.clean.csv"
    merge_broken_lines(csv_in, merged_out)
    clean_csv(merged_out, clean_out)
