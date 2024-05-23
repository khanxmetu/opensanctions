from zavod import Context
from time import sleep

# 1s delay seems to be enough to avoid getting blocked, while it takes a long
# time to get unblocked after about 10 requests.
SLEEP_SECONDS = 1


def parse_table(table):
    """This function is used to parse the table of Labels and Descriptions
    about the fugitive and return as a dict.
    """

    info_dict = {}

    # The first row will always be the header (Label, Description)
    # So we can skip it.
    for row in table.findall(".//tr")[1:]:
        label = row.findtext(".//td[1]")
        description = row.findtext(".//td[2]")
        info_dict[label] = description

    return info_dict


def crawl_item(fugitive_url: str, context: Context):
    response = context.fetch_html(fugitive_url, cache_days=7)

    name = response.findtext('.//h2[@class="fugitive__title"]')
    info_dict = parse_table(response.find(".//table"))

    entity = context.make("Person")
    entity.id = context.make_id(name)
    entity.add("gender", info_dict.pop("Sex", None))

    entity.add("birthDate", info_dict.pop("Year of Birth", None))
    entity.add("name", name)

    description = "".join(
        [
            d.text_content()
            for d in response.findall('.//div[@class="meta"]')
            if "Wanted for the following" in d.text_content()
        ]
    )

    entity.add("description", description)
    entity.add("sourceUrl", fugitive_url)

    entity.add("topics", "crime")

    context.emit(entity, target=True)


def crawl(context: Context):
    # Each page only displays 10 fugitives at a time, so we need to loop until we don't find any more fugitives

    base_url = context.data_url

    page_num = 0

    while True:
        url = base_url + "?page=" + str(page_num)
        response = context.fetch_html(url, cache_days=1)
        response.make_links_absolute(url)

        # If there are no more fugitives, we can stop crawling.
        if len(response.findall('.//div[@class="teaser "]/div/h3/a')) == 0:
            break

        for item in response.findall('.//div[@class="teaser "]/div/h3/a'):
            sleep(SLEEP_SECONDS)
            crawl_item(item.get("href"), context)

        page_num += 1
