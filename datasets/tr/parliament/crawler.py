from lxml import etree
import re

from zavod import Context, helpers as h
from zavod.http import request_hash
from zavod.logic.pep import categorise
from zavod.shed.zyte_api import fetch_html

CACHE_LONG = 30
CACHE_SHORT = 1
INDEX_UNBLOCK_ACTIONS = [
    {
        "action": "waitForNavigation",
        "waitUntil": "networkidle0",
        "timeout": 31,
        "onError": "return",
    },
]
DETAIL_UNBLOCK_ACTIONS = [
    {
        "action": "waitForNavigation",
        "waitUntil": "networkidle0",
        "timeout": 31,
        "onError": "return",
    },
    {
        "action": "waitForSelector",
        "selector": {
            "type": "css",
            "value": '#milletvekili-detay-holder-desktop',
            "state": "attached",
        },
        "timeout": 15,
    },
]

REGEX_PHONE = re.compile(r"\+\d{2} \(\d{3}\) \d{3} \d{2} \d{2}")
# Adana / Ceyhan – 1969, Abdülkadir, Hatice.
# Parents - date, place
REGEXP_BIRTH = re.compile(r"^.* [–-] (\d{4}), (.*)$", re.MULTILINE)


def parse_table(table):
    """This function is used to parse the table of Informations
    about the deputy and return as a dict.
    """

    info_dict = {}

    # The second column is the two dots, so we ignore it
    for row in table.findall(".//tr"):
        label = row.find(".//td[1]").text_content().strip()
        description = row.find(".//td[3]").text_content().strip()
        info_dict[label] = description

    return info_dict


def index_validator(doc):
    return len(doc.xpath('//ul[contains(@class, "tbmm-list-ul")]')) > 0


def mp_detail_validator(doc):
    return len(doc.xpath('//div[@id="milletvekili-detay-holder-desktop"]')) == 1


def crawl_item(context: Context, item: etree):
    anchor = item.find(".//a")
    if anchor is None:
        return
    deputy_url = anchor.get("href")
    name = anchor.text_content().strip()
    party = (
        item.xpath('//div[contains(@class, "text-right")]')[0].text_content().strip()
    )

    entity = context.make("Person")
    entity.id = context.make_slug(name, party)
    entity.add("name", name)
    entity.add("sourceUrl", deputy_url)
    entity.add("political", party)

    # MP page URL changes from one crawl to the next so cache based on name and party.
    fake_url = f"{context.data_url}/fake/{name}-{party}"
    cache_key = request_hash(
        fake_url, {"actions": DETAIL_UNBLOCK_ACTIONS, "javascript": True}
    )
    doc = fetch_html(
        context,
        deputy_url,
        mp_detail_validator,
        actions=DETAIL_UNBLOCK_ACTIONS,
        javascript=True,
        cache_days=CACHE_LONG,
        fingerprint=cache_key,
    )

    info_dict = parse_table(doc.find(".//table"))
    profile_els = doc.xpath('//div[contains(@class, "profile-ozgecmis-div")]')
    if profile_els:

        for p in profile_els[0].xpath(".//*"):
            p.tail = p.tail + "\n" if p.tail else "\n"
        profile = profile_els[0].text_content()
        birth_match = REGEXP_BIRTH.search(profile)
        if birth_match:
            entity.add("birthDate", h.parse_date(birth_match.group(1).strip(), ["%Y"]))
            entity.add("birthPlace", birth_match.group(2).strip())

    entity.add("email", info_dict.pop("E-Posta", None))
    entity.add("address", info_dict.pop("Adres", None))

    position = h.make_position(
        context, "Member of the Grand National Assembly", country="tr"
    )
    categorisation = categorise(context, position, is_pep=True)

    occupancy = h.make_occupancy(
        context,
        entity,
        position,
        True,
        categorisation=categorisation,
    )

    if occupancy:
        context.emit(entity, target=True)
        context.emit(position)
        context.emit(occupancy)


def crawl(context: Context):
    doc = fetch_html(
        context,
        context.data_url,
        index_validator,
        actions=INDEX_UNBLOCK_ACTIONS,
        javascript=True,
        cache_days=CACHE_SHORT,
    )
    doc.make_links_absolute(context.data_url)

    for item in doc.xpath('//li[contains(@class, "tbmm-list-item")]'):
        crawl_item(context, item)
