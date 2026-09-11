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

# Keep the six newest available issues for each language.
KEEP_ISSUES = 6

# Search this many months backward and forward from the
# current month. Looking forward is important because
# JW.org makes future issues available early.
SEARCH_BACK_MONTHS = 6
SEARCH_FORWARD_MONTHS = 6

API_BASE = "https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS"

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"

ET.register_namespace("itunes", ITUNES_NS)


# Each language has its own feed file.
#
# JW.org language codes:
# E = English
# F = French
# X = German
#
LANGUAGES = {
    "E": {
        "name": "English",
        "feed_file": Path("feedW_E.xml"),
    },
    "F": {
        "name": "French",
        "feed_file": Path("feedW_F.xml"),
    },
    "X": {
        "name": "German",
        "feed_file": Path("feedW_X.xml"),
    },
}


# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------

def shift_month(year, month, offset):
    """Return year, month shifted by offset months."""
    total = year * 12 + (month - 1) + offset
    new_year = total // 12
    new_month = total % 12 + 1
    return new_year, new_month


def make_issue_code(year, month):
    return f"{year:04d}{month:02d}"


def format_date_now():
    """Return current UTC time in RSS pubDate format."""
    return dt.datetime.now(dt.timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )


def read_existing_dates(feed_file):
    """
    Read publication dates from the existing feed.

    This prevents existing episodes from getting a new
    publication date every time the script runs.
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
            "All episodes will receive new publication dates."
        )

    return dates


# ------------------------------------------------------------
# JW.org API
# ------------------------------------------------------------

def get_issue(issue, language):
    """Retrieve one Watchtower issue from the JW.org API."""

    params = {
        "issue": issue,
        "output": "json",
        "pub": "w",
        "fileformat": "MP3",
        "alllangs": "0",
        "langwritten": language,
        "txtCMSLang": language,
    }

    url = API_BASE + "?" + urllib.parse.urlencode(params)

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Watchtower RSS Feed Updater"
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
            print(
                f"  {issue}: not available"
            )
        else:
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
        print(
            f"  {issue}: no {language} MP3 files"
        )
        return None

    print(
        f"  {issue}: found {len(tracks)} MP3 files"
    )

    return data, tracks


# ------------------------------------------------------------
# Build RSS feed
# ------------------------------------------------------------

def build_feed(
    language,
    language_name,
    feed_file,
    issues,
    existing_dates
):
    """Create the RSS feed XML."""

    root = ET.Element(
        "rss",
        {"version": "2.0"}
    )

    channel = ET.SubElement(
        root,
        "channel"
    )

    if language == "E":
        title = "Watchtower — Study Edition"
        description = (
            "Watchtower — Study Edition audio from JW.ORG"
        )
        language_code = "en-us"

    elif language == "F":
        title = "La Tour de Garde — édition d’étude"
        description = (
            "Audio de La Tour de Garde — édition d’étude "
            "de JW.ORG"
        )
        language_code = "fr-fr"

    else:
        title = "Der Wachtturm — Studienausgabe"
        description = (
            "Audio von Der Wachtturm — Studienausgabe "
            "von JW.ORG"
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

    total_tracks = 0

    # Newest issue first.
    for issue, data, tracks in issues:

        year = int(issue[:4])
        month = int(issue[4:6])

        month_name = dt.date(
            year,
            month,
            1
        ).strftime("%B")

        publication_name = data.get(
            "pubName",
            "Watchtower (Study)"
        )

        description = (
            f"{publication_name}, "
            f"{month_name} {year}"
        )

        for index, track in enumerate(
            tracks,
            start=1
        ):

            # Language-specific GUIDs prevent episodes
            # from conflicting between feeds.
            guid = (
                f"w-{language.lower()}-"
                f"{issue}-{index:02d}"
            )

            title = track.get(
                "title",
                f"Watchtower {issue}-{index:02d}"
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
                    f"Warning: {guid} has no audio URL; "
                    "skipping."
                )
                continue

            # Try several possible names for the file size.
            length = (
                file_info.get("size")
                or file_info.get("filesize")
                or file_info.get("length")
                or 0
            )

            # Preserve the old date if this episode already
            # existed in the feed.
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
            ).text = title

            ET.SubElement(
                item,
                "description"
            ).text = description

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
                },
            )

            total_tracks += 1

    # Pretty-print the XML.
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
        f"{len(issues)} issues and "
        f"{total_tracks} episodes."
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
    print("========================================")
    print(
        f"Updating {language_name} feed"
    )
    print("========================================")
    print()

    today = dt.date.today()

    print(
        f"Looking for {language_name} Watchtower "
        f"issues around "
        f"{today.strftime('%B %Y')}..."
    )
    print()

    available_issues = []

    # Search a range of months around the current month.
    for offset in range(
        -SEARCH_BACK_MONTHS,
        SEARCH_FORWARD_MONTHS + 1
    ):

        year, month = shift_month(
            today.year,
            today.month,
            offset
        )

        issue = make_issue_code(
            year,
            month
        )

        result = get_issue(
            issue,
            language
        )

        if result:
            data, tracks = result

            available_issues.append(
                (
                    issue,
                    data,
                    tracks
                )
            )

        # Be polite to the API.
        time.sleep(0.2)

    if not available_issues:
        print()
        print(
            f"ERROR: No {language_name} "
            "Watchtower issues were found."
        )
        print(
            "The feed was not changed."
        )
        return

    # Sort newest issue first.
    available_issues.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # Keep only the six newest available issues.
    selected_issues = available_issues[
        :KEEP_ISSUES
    ]

    print()
    print(
        f"{language_name} issues that will be retained:"
    )

    for issue, data, tracks in selected_issues:
        print(
            f"  {issue} - "
            f"{len(tracks)} MP3 files"
        )

    if len(selected_issues) < KEEP_ISSUES:
        print()
        print(
            f"Warning: only "
            f"{len(selected_issues)} issues "
            "were found."
        )

    print()

    existing_dates = read_existing_dates(
        feed_file
    )

    build_feed(
        language,
        language_name,
        feed_file,
        selected_issues,
        existing_dates
    )


# ------------------------------------------------------------
# Main program
# ------------------------------------------------------------

def main():

    print()
    print("========================================")
    print("Watchtower Study RSS Feed Updater")
    print("English + French + German")
    print("========================================")

    for language, settings in LANGUAGES.items():

        update_language(
            language,
            settings["name"],
            settings["feed_file"]
        )

    print()
    print("========================================")
    print("All feeds updated.")
    print("========================================")


if __name__ == "__main__":
    main()
