import datetime as dt
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


# ------------------------------------------------------------
# Settings
# ------------------------------------------------------------

API_BASE = (
    "https://b.jw-cdn.org/apis/pub-media/"
    "GETPUBMEDIALINKS"
)

ITUNES_NS = (
    "http://www.itunes.com/dtds/podcast-1.0.dtd"
)

ET.register_namespace("itunes", ITUNES_NS)


# Search two years back and one year forward.
#
# The Public Watchtower normally has one issue per year,
# but its media issue code contains YYYYMM.
#
# Searching the surrounding years means the script can
# discover a newly released issue without us having to
# change the script each year.
SEARCH_BACK_YEARS = 2
SEARCH_FORWARD_YEARS = 1


LANGUAGES = {
    "E": {
        "name": "English",
        "feed_file": Path("feedWP_E.xml"),
    },
    "F": {
        "name": "French",
        "feed_file": Path("feedWP_F.xml"),
    },
    "X": {
        "name": "German",
        "feed_file": Path("feedWP_X.xml"),
    },
}


# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------

def format_date_now():
    """Return current UTC time in RSS pubDate format."""

    return dt.datetime.now(
        dt.timezone.utc
    ).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )


def read_existing_dates(feed_file):
    """
    Preserve the existing pubDate for episodes already
    present in the feed.
    """

    dates = {}

    if not feed_file.exists():
        return dates

    try:
        tree = ET.parse(feed_file)
        root = tree.getroot()
        channel = root.find("channel")

        if channel is None:
            return dates

        for item in channel.findall("item"):

            guid = item.findtext("guid")
            pub_date = item.findtext("pubDate")

            if guid and pub_date:
                dates[guid] = pub_date

    except ET.ParseError:
        print(
            f"Warning: {feed_file} could not be parsed."
        )
        print(
            "Existing publication dates will not be preserved."
        )

    return dates


# ------------------------------------------------------------
# JW.org API
# ------------------------------------------------------------

def get_issue(issue, language):
    """Retrieve one Public Watchtower issue."""

    params = {
        "issue": issue,
        "output": "json",
        "pub": "wp",
        "fileformat": "MP3",
        "alllangs": "0",
        "langwritten": language,
        "txtCMSLang": language,
    }

    url = (
        API_BASE
        + "?"
        + urllib.parse.urlencode(params)
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Watchtower Public RSS Feed Updater"
            )
        },
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:

            data = json.load(response)

    except urllib.error.HTTPError as error:

        if error.code in (400, 404):
            return None

        print(
            f"  {issue}: HTTP error {error.code}"
        )

        return None

    except (
        urllib.error.URLError,
        TimeoutError
    ) as error:

        print(
            f"  {issue}: connection error: {error}"
        )

        return None

    except json.JSONDecodeError:

        print(
            f"  {issue}: invalid JSON returned"
        )

        return None

    tracks = (
        data.get("files", {})
        .get(language, {})
        .get("MP3", [])
    )

    if not tracks:
        return None

    return data, tracks


# ------------------------------------------------------------
# Find available issues
# ------------------------------------------------------------

def find_available_issues(language):

    today = dt.date.today()

    found = []

    for year_offset in range(
        -SEARCH_BACK_YEARS,
        SEARCH_FORWARD_YEARS + 1
    ):

        year = today.year + year_offset

        for month in range(1, 13):

            issue = f"{year:04d}{month:02d}"

            result = get_issue(
                issue,
                language
            )

            if result:

                data, tracks = result

                found.append(
                    (
                        issue,
                        data,
                        tracks
                    )
                )

                print(
                    f"  Found {issue}: "
                    f"{data.get('formattedDate')} "
                    f"({len(tracks)} MP3 files)"
                )

            time.sleep(0.15)

    return found


# ------------------------------------------------------------
# Build RSS feed
# ------------------------------------------------------------

def build_feed(
    language,
    language_name,
    feed_file,
    selected_issue,
    existing_dates
):

    issue, data, tracks = selected_issue

    root = ET.Element(
        "rss",
        {"version": "2.0"}
    )

    channel = ET.SubElement(
        root,
        "channel"
    )

    if language == "E":

        title = (
            "The Watchtower — Public Edition"
        )

        description = (
            "The Watchtower — Public Edition "
            "audio from JW.ORG"
        )

        language_code = "en-us"

    elif language == "F":

        title = (
            "La Tour de Garde — édition publique"
        )

        description = (
            "Audio de La Tour de Garde — "
            "édition publique de JW.ORG"
        )

        language_code = "fr-fr"

    else:

        title = (
            "Der Wachtturm — Ausgabe für die Öffentlichkeit"
        )

        description = (
            "Audio von Der Wachtturm — "
            "Ausgabe für die Öffentlichkeit von JW.ORG"
        )

        language_code = "de-de"

    ET.SubElement(
        channel,
        "title"
    ).text = title

    ET.SubElement(
        channel,
        "description"
    ).text = description

    ET.SubElement(
        channel,
        "link"
    ).text = "https://www.jw.org/"

    ET.SubElement(
        channel,
        "language"
    ).text = language_code

    ET.SubElement(
        channel,
        f"{{{ITUNES_NS}}}author"
    ).text = "JW.ORG"

    ET.SubElement(
        channel,
        f"{{{ITUNES_NS}}}category",
        {"text": "Religion & Spirituality"}
    )

    current_date = format_date_now()

    year = issue[:4]

    for index, track in enumerate(
        tracks,
        start=1
    ):

        # Keep the language in the GUID so that
        # the three feeds cannot conflict.
        guid = (
            f"wp-{language.lower()}-"
            f"{issue}-{index:02d}"
        )

        title_text = track.get(
            "title",
            f"Watchtower Public {issue}-{index:02d}"
        )

        file_info = track.get(
            "file",
            {}
        )

        audio_url = file_info.get(
            "url"
        )

        if not audio_url:

            print(
                f"Warning: {guid} has no audio URL. "
                "Skipping."
            )

            continue

        length = (
            file_info.get("size")
            or file_info.get("filesize")
            or file_info.get("length")
            or 0
        )

        pub_date = existing_dates.get(
            guid,
            current_date
        )

        item = ET.SubElement(
            channel,
            "item"
        )

        ET.SubElement(
            item,
            "title"
        ).text = title_text

        ET.SubElement(
            item,
            "description"
        ).text = (
            f"{data.get('pubName', 'Watchtower (Public)')}, "
            f"{year}"
        )

        ET.SubElement(
            item,
            "guid",
            {"isPermaLink": "false"}
        ).text = guid

        ET.SubElement(
            item,
            "pubDate"
        ).text = pub_date

        ET.SubElement(
            item,
            "enclosure",
            {
                "url": audio_url,
                "length": str(length),
                "type": "audio/mpeg",
            }
        )

    ET.indent(
        root,
        space="  "
    )

    tree = ET.ElementTree(root)

    tree.write(
        feed_file,
        encoding="utf-8",
        xml_declaration=True
    )

    print()
    print(
        f"Wrote {feed_file} with "
        f"{len(tracks)} episodes."
    )


# ------------------------------------------------------------
# Update one language
# ------------------------------------------------------------

def update_language(
    language,
    language_name,
    feed_file
):

    print()
    print("=" * 60)
    print(
        f"Updating Public Watchtower — "
        f"{language_name}"
    )
    print("=" * 60)

    print()
    print(
        "Searching JW.org for available Public "
        "Watchtower issues..."
    )

    available = find_available_issues(
        language
    )

    if not available:

        print()
        print(
            f"ERROR: No Public Watchtower issue "
            f"was found for {language_name}."
        )

        print(
            "The existing feed was not changed."
        )

        return

    # Most recent media issue first.
    available.sort(
        key=lambda x: x[0],
        reverse=True
    )

    selected = available[0]

    issue, data, tracks = selected

    print()
    print(
        f"Selected issue: {issue}"
    )

    print(
        f"Publication: "
        f"{data.get('pubName')}"
    )

    print(
        f"Date: "
        f"{data.get('formattedDate')}"
    )

    print(
        f"MP3 tracks: "
        f"{len(tracks)}"
    )

    existing_dates = read_existing_dates(
        feed_file
    )

    build_feed(
        language,
        language_name,
        feed_file,
        selected,
        existing_dates
    )


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    print()
    print("=" * 60)
    print("Public Watchtower RSS Feed Updater")
    print("English + French + German")
    print("=" * 60)

    for language, settings in LANGUAGES.items():

        update_language(
            language,
            settings["name"],
            settings["feed_file"]
        )

    print()
    print("=" * 60)
    print("All Public Watchtower feeds updated.")
    print("=" * 60)


if __name__ == "__main__":
    main()
