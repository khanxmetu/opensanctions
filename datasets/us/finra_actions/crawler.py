from typing import Generator, Dict, Tuple, Optional
from lxml.etree import _Element
from normality import slugify
from zavod import Context, helpers as h


def parse_table(
    table: _Element,
) -> Generator[Dict[str, Tuple[str, Optional[str]]], None, None]:
    headers = None
    for row in table.findall(".//tr"):
        if headers is None:
            headers = []
            for el in row.findall("./th"):
                headers.append(slugify(el.text_content()))
            continue

        cells = []
        for el in row.findall("./td"):
            for span in el.findall(".//span"):
                # add newline to split spans later if we want
                span.tail = "\n" + span.tail if span.tail else "\n"

            a = el.find(".//a")
            if a is None:
                cells.append((el.text_content(), None))
            else:
                cells.append((el.text_content(), a.get("href")))

        assert len(headers) == len(cells)
        yield {hdr: c for hdr, c in zip(headers, cells)}


def crawl_item(input_dict: dict, context: Context):
    schema = "LegalEntity"
    names = []
    for dirty_name in input_dict.pop("firms-individuals")[0].split("\n"):
        names.extend(h.split_comma_names(context, dirty_name))
    case_summary = input_dict.pop("case-summary")[0].strip()
    case_id, source_url = input_dict.pop("case-id")
    date = input_dict.pop("action-date-sort-ascending")[0].strip()
    formatted_date = h.parse_date(date, formats=["%m/%d/%Y"])[0]

    for name in names:
        entity = context.make(schema)
        entity.id = context.make_slug(name)
        entity.add("name", name)
        entity.add("topics", "reg.action")
        entity.add("country", "us")
        context.emit(entity, target=True)

        sanction = h.make_sanction(context, entity, key=case_id)
        description = f"{formatted_date}: {case_summary}"
        sanction.add("description", description)
        sanction.add("authorityId", case_id.strip())
        sanction.add("sourceUrl", source_url)
        context.emit(sanction)

    context.audit_data(input_dict, ignore=["document-type"])


def crawl(context: Context):
    # Each page only displays 15 rows at a time, so we need to loop until we find an empty table

    base_url = context.data_url

    page_num = 0

    while True:
        context.log.info(f"Crawling page {page_num}")
        url = base_url + "?page=" + str(page_num)
        response = context.fetch_html(url, cache_days=7)
        response.make_links_absolute(url)
        table = response.find(".//table")

        if table is None:
            break

        for item in parse_table(table):
            crawl_item(item, context)

        page_num += 1
