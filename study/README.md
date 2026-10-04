# Study material

Everything you need to revise after (or alongside) the hands-on labs.

| File | What it is | Use it when |
|---|---|---|
| [study-guide.pdf](study-guide.pdf) | Level 1, the 16 concept pages, the cheat sheet, the troubleshooting method, the capstone, the glossary and the interview questions as one printable PDF (answers expanded, with a table of contents; built by `study/tools/build_pdf.py`) | you want to read offline, print, or annotate |
| [glossary.md](glossary.md) | every term used in the course, A–Z, in one or two plain sentences, with a link to where it is explained | a word in a lesson is unclear |
| [interview-questions.md](interview-questions.md) | 25 questions with model answers, from chart versions to server-side apply conflicts | before an interview, or to test yourself |
| [../tutorial/](../tutorial/README.md) | the 24-chapter guided course through the repository | you want to be taught, step by step |

## How to revise

1. Work through the [tutorial](../tutorial/README.md); it sends you to the labs and docs in the right order.
2. After each chapter, look up every glossary term you could not explain to a colleague.
3. At the end, answer the interview questions **out loud**, then compare with the model answers. Explaining is a
   different skill from knowing; it needs practice.
4. Finish with the [capstone](../labs/16-capstone.md), the [challenges](../challenges/README.md) and the
   [final review](../tutorial/24-cleanup-and-review.md).

## Rebuild the PDF

```text
pip install markdown
python study/tools/build_pdf.py        (uses a headless Chrome or Edge to print the PDF)
```
