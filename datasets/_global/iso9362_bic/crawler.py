import csv

from zavod import Context
from zavod import helpers as h
from zavod.shed.internal_data import fetch_internal_data


def crawl(context: Context) -> None:
    hash_ = "3fed0992e33d528c7063a568e0832a5578433526"
    h.assert_url_hash(context, context.data_url, hash_)

    data_path = context.get_resource_path("source.csv")
    fetch_internal_data("iso9362_bic/20240403/iso.csv.clean.csv", data_path)
    context.export_resource(data_path, "text/csv", title="ISO 9362 BIC Codes (CSV)")

    with open(data_path, "r") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            print(row)
            return
            entity = context.make("Organization")
            bic = row.pop("BIC")
            if bic[4:6] == "UT":
                continue
            if len(row.pop("BrchCode")) == 3:
                # Skip branches for now:
                continue
            entity.id = f"bic-{bic}"
            entity.add("name", row.pop("FullLegalName"))
            entity.add("swiftBic", bic)
            entity.add("country", bic[4:6])
            entity.add("address", row.pop("RegisteredAddress"))
            entity.add("address", row.pop("OperationalAddress"))
            entity.add("createdAt", row.pop("RecordCreationDate"))
            entity.add("modifiedAt", row.pop("LastUpdateDate"))
            row.pop("RecordExpirationDate")
            type_ = row.pop("InstitType")
            if type_ == "FIIN":
                entity.add("topics", "fin.bank")
            context.audit_data(row, ignore=["FullBIC", "RecOwnershipStatus"])
            context.emit(entity)
