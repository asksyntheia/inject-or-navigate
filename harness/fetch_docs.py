"""Download the six scored SEC filings into ``docs/*.txt`` as plain text.

Run from the ``harness/`` directory::

    python3 fetch_docs.py

SEC EDGAR requires a descriptive ``User-Agent``; set your own contact string if
you adapt this. Re-running overwrites ``docs/*.txt``.
"""

import html
import os
import re
import urllib.request

# SEC EDGAR fair-access policy requires a descriptive User-Agent.
USER_AGENT = "Syntheia Research (mourad@syntheia.io)"

DOCS = {
    "FA_fluor_amendment": "https://www.sec.gov/Archives/edgar/data/0001124198/000110465923090465/tm2323493d1_ex10-1.htm",
    "FA_generac_amendment": "https://www.sec.gov/Archives/edgar/data/0001474735/000143774924022233/gnrc20240703_8k.htm",
    "LP_thomas_green": "https://www.sec.gov/Archives/edgar/data/1283709/000119312508059814/dex1036.htm",
    "LP_carlyle": "https://www.sec.gov/Archives/edgar/data/0002065337/000162828025033288/exhibit32-form10a.htm",
    "SP_first_avenue": "https://www.sec.gov/Archives/edgar/data/1010286/000119312504212899/dex104.htm",
    "SP_meta_giphy": "https://www.sec.gov/Archives/edgar/data/1549346/000114036123026154/brhc20053362_ex2-1.htm",
}


def strip_html(raw):
    """Reduce raw EDGAR HTML to readable plain text."""
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</(p|div|tr|h[1-6]|li)>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(" ", " ", text)  # non-breaking space -> normal space
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


try:
    import tiktoken

    _encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(text):
        return len(_encoder.encode(text))

except Exception:

    def count_tokens(text):
        return len(text) // 4  # rough fallback when tiktoken is unavailable


def fetch(url):
    """Fetch a URL and return its decoded body."""
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
    )
    return urllib.request.urlopen(request, timeout=45).read().decode("utf-8", "ignore")


def main():
    os.makedirs("docs", exist_ok=True)
    total_tokens = 0
    for name, url in DOCS.items():
        try:
            raw = fetch(url)
            text = strip_html(raw)
            with open(f"docs/{name}.txt", "w") as handle:
                handle.write(text)
            tokens = count_tokens(text)
            total_tokens += tokens
            print(
                f"{name:24s} html={len(raw):>8d}  "
                f"text_chars={len(text):>8d}  ~tokens={tokens:>7d}"
            )
        except Exception as error:
            print(f"{name:24s} ERROR: {error}")
    print(f"{'TOTAL':24s} ~tokens={total_tokens} (paper's 20Q INJECT corpus ~163K)")


if __name__ == "__main__":
    main()
