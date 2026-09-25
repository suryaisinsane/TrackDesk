import re
from bs4 import BeautifulSoup


def clean_email_body(body: str) -> str:
    """
    Clean an email body before sending it to the LLM.
    """

    # Convert HTML into plain text
    soup = BeautifulSoup(body, "html.parser")
    text = soup.get_text("\n")

    # Remove common forwarded-email headers
    text = re.split(
        r"\n\s*(From:|Sent:|To:|Subject:)\s*",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    # Remove quoted reply lines
    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        if line.strip().startswith(">"):
            continue

        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)

    # Collapse excessive blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # Remove leading/trailing whitespace
    return text.strip()