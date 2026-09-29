import json
import urllib.error
import urllib.parse
import urllib.request


API_BASE = "https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS"

LANGUAGES = {
    "E": "English",
    "F": "French",
    "X": "German",
}


def test_issue(issue, language):
    params = {
        "issue": issue,
        "output": "json",
        "pub": "wp",
        "fileformat": "MP3",
        "alllangs": "0",
        "langwritten": language,
        "txtCMSLang": language,
    }

    url = API_BASE + "?" + urllib.parse.urlencode(params)

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Watchtower RSS Feed Test"
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=30
        ) as response:
            data = json.load(response)

        tracks = (
            data.get("files", {})
            .get(language, {})
            .get("MP3", [])
        )

        if tracks:
            print()
            print("=" * 60)
            print(f"{language}: {LANGUAGES[language]}")
            print(f"Requested issue: {issue}")
            print(f"Returned issue:  {data.get('issue')}")
            print(f"Publication:    {data.get('pubName')}")
            print(f"Date:            {data.get('formattedDate')}")
            print(f"MP3 tracks:     {len(tracks)}")
            print("=" * 60)

            for track in tracks:
                print()
                print("Title:")
                print(track.get("title"))

                file_info = track.get("file", {})

                print("URL:")
                print(file_info.get("url"))

            return data

        return None

    except urllib.error.HTTPError as error:
        print(
            f"{language} / {issue}: HTTP {error.code}"
        )

    except Exception as error:
        print(
            f"{language} / {issue}: {error}"
        )

    return None


def main():

    print()
    print("=" * 60)
    print("PUBLIC WATCHTOWER API DISCOVERY TEST")
    print("=" * 60)

    issues = []

    for year in (2025, 2026, 2027):
        for month in range(1, 13):
            issues.append(f"{year:04d}{month:02d}")

    for language, language_name in LANGUAGES.items():

        print()
        print("-" * 60)
        print(f"Searching for {language_name} Public Watchtower")
        print("-" * 60)

        found = []

        for issue in issues:

            data = test_issue(
                issue,
                language
            )

            if data:
                found.append(data)

        print()
        print(
            f"Found {len(found)} Public Watchtower "
            f"media issues for {language_name}."
        )

        if found:
            print()
            print("Issues found:")

            for data in found:
                print(
                    f"  {data.get('issue')}  "
                    f"{data.get('formattedDate')}"
                )


if __name__ == "__main__":
    main()
