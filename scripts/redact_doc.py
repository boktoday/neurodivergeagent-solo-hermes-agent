#!/usr/bin/env python3
"""Redact personal information from a document before it reaches a cloud model.

Attaching a letter, plan or statement to a chat with a hosted provider sends the
raw file. This scrubs it locally first, so what leaves the machine is the
substance without the identifiers: the deadline and the amount survive, the name,
address, phone and reference numbers do not.

Usage:
    python scripts/redact_doc.py letter.txt
    python scripts/redact_doc.py letter.txt --names "Brendan O'Keefe"
    python scripts/redact_doc.py plan.pdf --names "..." --out clean.md
    cat email.txt | python scripts/redact_doc.py -

Design rules
------------
- **The redacted text goes to stdout; counts go to stderr.** The agent needs to
  read the result, but a terminal scrollback should never hold the raw values,
  and neither should a log. Nothing in the counts names what it removed.
- **Dates and dollar amounts are preserved deliberately.** A bill you cannot
  triage is useless: the deadline and the amount are the two things worth
  reading. Only dates of birth, when clearly labelled, are scrubbed.
- **Never overwrites the input.** Reading and writing the same file silently
  destroys the original.
- **Rule order is load-bearing.** See the constants below.

Standard library only for text, HTML, Markdown, CSV and DOCX. PDF needs `pypdf`
(or `PyPDF2`) or the `pdftotext` binary; if neither is present the script says
so and stops rather than pretending it redacted something it never read.
"""
import argparse
import html
import logging
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

SUPPORTED_TEXT = {".txt", ".md", ".markdown", ".csv", ".html", ".htm", ".text"}
SUPPORTED_PDF = {".pdf"}
SUPPORTED_DOCX = {".docx"}

# Order is load-bearing, twice over.
#
# 1. Labelled identifiers run before bare digit sweeps. "NDIS Number: 430123456"
#    is claimed by the label first, so the nine-digit sweep cannot mistake part
#    of a phone number for a participant number.
# 2. Phones must run before the bare nine-digit sweep. An Australian mobile is
#    ten digits and an NDIS participant number is nine: run the nine-digit sweep
#    first and it chews the middle out of a mobile, leaving debris that is no
#    safer than the original and unusable to read.
# 3. Names run last. Applied first, a name rule eats the middle of an email or a
#    street and leaves [NAME_A].[NAME_A]@example.com behind.

SCHOOL_WORDS = ("school", "college", "academy", "grammar", "institute",
                "high", "primary", "campus", "university", "kindergarten")
ADULT_TITLES = ("dr", "mr", "mrs", "ms", "miss", "prof", "professor", "sir", "rev")

STREET_TYPES = (
    "Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Court|Ct|Place|Pl|Crescent|Cres|"
    "Parade|Pde|Lane|Ln|Terrace|Tce|Boulevard|Blvd|Bvd|Close|Cl|Grove|Gr|"
    "Highway|Hwy|Circuit|Cct|Way|Square|Sq|Esplanade|Esp|Rise|Glen|View"
)

MONTHS = ("January|February|March|April|May|June|July|August|September|"
          "October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|"
          "Sept|Oct|Nov|Dec")

# Keyword-anchored first: a bare nine-digit number is ambiguous, so anything
# following "NDIS", "CRN" or "Centrelink" is claimed by that label.
RE_CRN = re.compile(
    r"(?i)\b(?:crn|centrelink(?:\s+(?:reference|ref|crn))?(?:\s+number)?)\b"
    r"[\s:#.\-]*(\d{3}\s?\d{3}\s?\d{3}\s?[A-Za-z]?)"
)
RE_NDIS_KEYED = re.compile(
    r"(?i)\b(?:ndis|participant)\b[^0-9\n]{0,28}?(\d{3}\s?\d{3}\s?\d{3})\b"
)
RE_TFN = re.compile(
    r"(?i)\b(?:tfn|tax\s+file\s+(?:number|no\.?))\b[\s:#.\-]*(\d{3}\s?\d{3}\s?\d{2,3})"
)
RE_MEDICARE = re.compile(r"\b[2-6]\d{3}\s?\d{5}\s?\d\b")
RE_BSB = re.compile(r"(?i)\bbsb\b[\s:#.\-]*(\d{3}[\s\-]?\d{3})\b")
RE_ACCOUNT = re.compile(
    r"(?i)\b(?:account|acc(?:ount)?\s*(?:no|number|#)?)\b[\s:#.\-]*(\d{6,10})\b"
)
RE_CARD = re.compile(r"\b\d{4}[\s\-]\d{4}[\s\-]\d{4}[\s\-]\d{1,7}\b")
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
RE_PHONE_MOBILE = re.compile(
    r"(?:\+?61[\s\-]?|\(?0)4\d{2}[\s\-]?\d{3}[\s\-]?\d{3}\b"
)
RE_PHONE_LANDLINE = re.compile(
    r"\b\(?0[2-9]\)?[\s\-]?\d{4}[\s\-]?\d{4}\b"
)
RE_STREET = re.compile(
    r"(?i)\b(?:unit|flat|suite|level|shop|u)?[\s#]*\d{1,4}[a-z]?[/\s]+"
    r"(?:[A-Z][A-Za-z'\-]+\s+){1,4}"
    r"(?:" + STREET_TYPES + r")\b\.?"
)
RE_STATE_POSTCODE = re.compile(r"\b(?:NSW|VIC|QLD|WA|SA|TAS|ACT|NT)\b,?\s+\d{4}\b")
RE_DOB = re.compile(
    r"(?i)\b(?:d\.?o\.?b\.?|date\s+of\s+birth|born)\b[\s:.\-]*"
    r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}"
    r"|\d{1,2}(?:st|nd|rd|th)?\s+(?:" + MONTHS + r")\s+\d{4}"
    r"|\d{4}-\d{2}-\d{2})"
)
RE_NDIS_BARE_FORMATTED = re.compile(r"\b\d{3}\s\d{3}\s\d{3}\b")
RE_NDIS_BARE = re.compile(r"\b\d{9}\b")


def _letters(n):
    """1 -> A, 26 -> Z, 27 -> AA."""
    out = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


class Redactor:
    """Applies the rules in order and counts what it replaced.

    The counts are deliberately bare numbers. A log that says which name was on
    which line is a second copy of the thing being protected.
    """

    def __init__(self, names=(), addresses=()):
        self.counts = {}
        self._names = [n.strip() for n in names if n.strip()]
        self._addresses = [a.strip() for a in addresses if a.strip()]
        self._name_patterns = []
        self._address_patterns = []

    # ---------- custom strings ----------

    def _build_patterns(self, text=""):
        """Turn supplied names and addresses into (pattern, label) pairs.

        Longest first, so "Sarah Whitmore" wins over "Sarah". Then bare tokens,
        because a plan introduces a full name once and uses the first name forty
        times, and a redaction that leaves the first name everywhere has not
        redacted anything.
        """
        self._name_patterns = []
        self._address_patterns = []

        for index, address in enumerate(sorted(set(self._addresses), key=len, reverse=True)):
            pat = re.compile(r"\b" + re.escape(address).replace(r"\ ", r"\s+") + r"\b", re.IGNORECASE)
            self._address_patterns.append((pat, "[ADDRESS_%s]" % _letters(index + 1)))

        schools = [n for n in self._names if any(w in n.lower() for w in SCHOOL_WORDS)]
        people = [n for n in self._names if n not in schools]

        # A surname shared by two people cannot honestly be attributed to either,
        # so it gets its own label rather than quietly meaning "the first one we
        # happened to reach".
        token_counts = {}
        for name in people:
            for token in set(name.split()):
                token = token.strip(".,").lower()
                if token:
                    token_counts[token] = token_counts.get(token, 0) + 1
        shared = {token for token, count in token_counts.items() if count > 1}

        label_of = {}
        for index, name in enumerate(sorted(schools, key=len, reverse=True)):
            label_of[name] = "[SCHOOL_%s]" % _letters(index + 1)
        for index, name in enumerate(sorted(people, key=len, reverse=True)):
            label_of[name] = "[NAME_%s]" % _letters(index + 1)

        for name in sorted(label_of, key=len, reverse=True):
            pat = re.compile(r"\b" + re.escape(name).replace(r"\ ", r"\s+") + r"\b", re.IGNORECASE)
            self._name_patterns.append((pat, label_of[name]))

        surname_n = 0
        surname_map = {}
        for name in sorted(people, key=len, reverse=True):
            for token in name.split():
                token = token.strip(".,")
                if len(token) < 4 or token.lower() in ADULT_TITLES:
                    continue
                key = token.lower()
                if key in shared:
                    if key not in surname_map:
                        surname_n += 1
                        surname_map[key] = "[SURNAME_%s]" % _letters(surname_n)
                    label = surname_map[key]
                else:
                    label = label_of[name]
                tpat = re.compile(r"\b" + re.escape(token) + r"\b", re.IGNORECASE)
                if all(tpat.pattern != p.pattern for p, _ in self._name_patterns):
                    self._name_patterns.append((tpat, label))

    # ---------- substitution ----------

    def _sub(self, category, pattern, text, group=0):
        """Replace matches with [CATEGORY], counting them. Never records values."""
        def repl(match):
            self.counts[category] = self.counts.get(category, 0) + 1
            label = "[%s]" % category
            if group == 0:
                return label
            whole, value = match.group(0), match.group(group)
            start = match.start(group) - match.start(0)
            return whole[:start] + label + whole[start + len(value):]

        return pattern.sub(repl, text)

    def run(self, text):
        self._build_patterns(text)
        self.counts = {}

        # 1. Labelled identifiers, before any bare digit sweep.
        text = self._sub("CRN", RE_CRN, text, group=1)
        text = self._sub("TFN", RE_TFN, text, group=1)
        text = self._sub("NDIS_NUMBER", RE_NDIS_KEYED, text, group=1)
        text = self._sub("MEDICARE_NUMBER", RE_MEDICARE, text)
        text = self._sub("BSB", RE_BSB, text, group=1)
        text = self._sub("ACCOUNT_NUMBER", RE_ACCOUNT, text, group=1)

        # 2. Contact detail. Phones before the bare nine-digit sweep.
        text = self._sub("EMAIL", RE_EMAIL, text)
        text = self._sub("PHONE", RE_PHONE_MOBILE, text)
        text = self._sub("PHONE", RE_PHONE_LANDLINE, text)
        text = self._sub("CARD_NUMBER", RE_CARD, text)

        # 3. Where they live.
        for pat, label in self._address_patterns:
            def repl(_match, label=label):
                self.counts["ADDRESS"] = self.counts.get("ADDRESS", 0) + 1
                return label
            text = pat.sub(repl, text)
        text = self._sub("ADDRESS", RE_STREET, text)
        text = self._sub("ADDRESS", RE_STATE_POSTCODE, text)

        # 4. Dates of birth only when labelled. A bill is full of other dates and
        #    they are the point of reading it; scrubbing every date would leave
        #    the user with a document they cannot act on.
        text = self._sub("DOB", RE_DOB, text, group=1)

        # 5. Whatever digit runs are left that look like a participant number.
        text = self._sub("NDIS_NUMBER", RE_NDIS_BARE_FORMATTED, text)
        text = self._sub("NDIS_NUMBER", RE_NDIS_BARE, text)

        # 6. Names last, once nothing else can be damaged by them.
        for pat, label in self._name_patterns:
            def repl(_match, label=label):
                self.counts["NAME"] = self.counts.get("NAME", 0) + 1
                return label
            text = pat.sub(repl, text)

        return text


# ---------- reading ----------

def html_to_text(raw):
    """Strip tags and leave readable text. Good enough for redaction."""
    raw = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?i)</(p|div|li|tr|h[1-6])>", "\n", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n\s*\n\s*\n+", "\n\n", raw)
    return raw.strip()


def read_docx(path):
    """DOCX is a zip of XML. No third-party package needed.

    Paragraph and line breaks become newlines; `<w:t>` holds the actual text.
    Without the paragraph break the whole document arrives as one line, which
    makes the address and name rules much less reliable.
    """
    with zipfile.ZipFile(str(path)) as archive:
        try:
            xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
        except KeyError:
            raise SystemExit("this .docx has no word/document.xml; it may not be a Word file.")
    xml = re.sub(r"(?i)</w:p>", "\n", xml)
    xml = re.sub(r"(?i)<w:br\s*/?>", "\n", xml)
    xml = re.sub(r"(?i)</w:tc>", "\t", xml)
    xml = re.sub(r"(?s)<[^>]+>", "", xml)
    return html.unescape(xml).strip()


def read_pdf(path):
    """pypdf if installed, else the pdftotext binary, else say so and stop."""
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            PdfReader = None

    logging.getLogger("pypdf").setLevel(logging.CRITICAL)

    reader_failed = False
    if PdfReader is not None:
        try:
            reader = PdfReader(str(path))
            text = "\n\n".join((page.extract_text() or "") for page in reader.pages).strip()
            if text:
                return text
            reader_failed = True
        except Exception as exc:  # noqa: BLE001 - report the type, never the content
            print("warning: pypdf could not read this file (%s)" % type(exc).__name__,
                  file=sys.stderr)
            reader_failed = True

    binary = shutil.which("pdftotext")
    if binary:
        try:
            out = subprocess.run([binary, "-layout", str(path), "-"],
                                 capture_output=True, text=True, timeout=120)
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout
            reader_failed = True
        except (subprocess.SubprocessError, OSError):
            reader_failed = True

    if reader_failed:
        # Different problem, different advice. Telling someone to install pypdf
        # when pypdf is installed and the file is a scan only wastes their time.
        raise SystemExit(
            "this PDF opened but contained no text.\n"
            "That usually means it is a scan or a photo rather than a digital PDF.\n"
            "Run it through OCR first (for example `ocrmypdf in.pdf out.pdf`), or\n"
            "open it, copy the text and paste it into a .txt file."
        )

    raise SystemExit(
        "cannot read PDFs on this machine.\n"
        "Install one of these and try again:\n"
        "    pip install pypdf          (or PyPDF2)\n"
        "    apt install poppler-utils  (gives you pdftotext)\n"
        "Or open the PDF, copy the text, paste it into a .txt file and run this\n"
        "script on that."
    )


def read_document(path):
    suffix = path.suffix.lower()
    if suffix in SUPPORTED_TEXT:
        raw = path.read_text(encoding="utf-8", errors="replace")
        return html_to_text(raw) if suffix in {".html", ".htm"} else raw
    if suffix in SUPPORTED_PDF:
        return read_pdf(path)
    if suffix in SUPPORTED_DOCX:
        return read_docx(path)
    raise SystemExit(
        "unsupported file type: %s\n"
        "Supported: %s, .pdf and .docx.\n"
        "Convert the document to .txt or .md and run it again."
        % (suffix or "(none)", ", ".join(sorted(SUPPORTED_TEXT - {".text"})))
    )


# ---------- main ----------

def split_list(raw):
    return [item.strip() for item in (raw or "").split(",") if item.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Redact personal information from a document before it is sent to a cloud model.",
    )
    parser.add_argument("document", help="path to the document, or - to read standard input")
    parser.add_argument("--names", default="",
                        help='comma-separated real names, e.g. "Brendan O\'Keefe, my GP"')
    parser.add_argument("--addresses", default="",
                        help='comma-separated addresses or suburbs to strip explicitly')
    parser.add_argument("--out", default="",
                        help="write the redacted text here instead of standard output")
    parser.add_argument("--quiet", action="store_true",
                        help="print no summary to standard error")
    args = parser.parse_args(argv)

    names, addresses = split_list(args.names), split_list(args.addresses)

    if args.document == "-":
        text = sys.stdin.read()
        source = "standard input"
    else:
        path = pathlib.Path(args.document).expanduser()
        if not path.is_file():
            print("error: no such file: %s" % path, file=sys.stderr)
            return 2
        if args.out:
            out_path = pathlib.Path(args.out).expanduser()
            try:
                same = out_path.resolve() == path.resolve()
            except OSError:
                same = False
            if same:
                print("error: --out is the input file. Refusing to overwrite the original;\n"
                      "choose another name and run it again.", file=sys.stderr)
                return 2
        text = read_document(path)
        source = path.name

    redactor = Redactor(names=names, addresses=addresses)
    redacted = redactor.run(text)

    if args.out:
        out_path = pathlib.Path(args.out).expanduser()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(redacted, encoding="utf-8")
    else:
        sys.stdout.write(redacted)
        if not redacted.endswith("\n"):
            sys.stdout.write("\n")

    if not args.quiet:
        # Counts only, never values: this line is safe to screenshot.
        if not args.out:
            print("---", file=sys.stderr)
        total = sum(redactor.counts.values())
        detail = ", ".join("%s=%d" % (k, v) for k, v in sorted(redactor.counts.items()))
        print("read %s, redacted %d item(s)%s" % (
            source, total, (": " + detail) if detail else " (nothing matched)",
        ), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
