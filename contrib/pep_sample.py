import random
import click
from csv import DictWriter

from zavod.meta import Dataset, get_catalog
from zavod.dedupe import get_resolver
from zavod.store import get_view, clear_store
from rigour.ids.wikidata import is_qid


def get_entities(view):
    for entity in view.entities():
        if entity.schema.name != "Person":
            continue
        topics = entity.get("topics")
        if "role.pep" not in topics:
            continue
        for prop, person_related in view.get_adjacent(entity):
            if prop.name != "positionOccupancies":
                continue
            for prop, occupancy_related in view.get_adjacent(person_related):
                if prop.name != "post":
                    continue
                if "us" not in occupancy_related.get("country"):
                    continue
                if "gov.muni" not in occupancy_related.get("topics"):
                    continue
                yield entity, person_related, occupancy_related
                
    
def first_or_none(values):
    if values:
        return values[0]
    return None


def sample_peps(dataset: Dataset, sample_size: int, outfile: str) -> None:
    view = get_view(dataset, external=False)
    count = 0
    for entity, person_related, occupancy_related in get_entities(view):
        count += 1
    if count < sample_size:
        print("Not enough entities for sample size. Exiting...")
        exit(1)
    indexes = list(range(count))
    sample_indexes = set(random.sample(indexes, sample_size))
    with open(outfile, "w") as fh:
        writer = DictWriter(fh, fieldnames=["id", "wikidata_url", "name", "website", "position", "start_date", "end_date"])
        writer.writeheader()
        for idx, (entity, person_related, occupancy_related) in enumerate(get_entities(view)):
            if idx in sample_indexes:
                qid = entity.id if is_qid(entity.id) else None
                wikidata_url = f"https://www.wikidata.org/wiki/{qid}" if qid else None
                writer.writerow({
                    "id": entity.id,
                    "wikidata_url": wikidata_url,
                    "name": entity.caption,
                    "website": ", ".join(entity.get("website")),
                    "position": occupancy_related.caption,
                    "start_date": first_or_none(person_related.get("startDate")),
                    "end_date": first_or_none(person_related.get("endDate")),
                })
            
    
@click.command()
@click.argument("dataset", type=str)
@click.argument("sample_size", type=int)
@click.argument("outfile", type=str)
@click.option("-c", "--clear", is_flag=True, default=False)
def main(dataset: str, sample_size: int, outfile: str, clear: bool = False):
    dataset = get_catalog().require(dataset)
    if clear:
        clear_store(dataset)
    sample_peps(dataset, sample_size, outfile)


if __name__ == "__main__":
    main()
