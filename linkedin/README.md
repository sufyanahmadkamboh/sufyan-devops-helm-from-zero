# LinkedIn package

| File | Use |
|---|---|
| `post.md` | Post text |
| `carousel/carousel.pdf` | **Recommended:** upload as a *Document* post. LinkedIn shows it as a swipeable carousel |
| `carousel/slide-01.png` … `slide-11.png` | The same slides as images (1080×1350), for a multi-image post |
| `carousel/slides.html` | Source of the slides. Edit it and re-render each slide with a headless browser (`slides.html?s=N`) |
| `carousel/qr-repo.svg`, `qr-portfolio.svg` | The QR codes used on the last slide |
| `project-image.png` | Single overview image (1200×627) |
| `project-summary.md` | Short technical summary |
| `hashtags.txt` | Hashtags |

## The slides (visual first: one picture per idea, short captions)

| # | Visual | Message |
|---|---|---|
| 1 | Three 458-line folders → one chart + three small values files | What it is |
| 2 | Four panels: 1 change = 3 edits, no history, passwords in Git, sharing = copying | The pain |
| 3 | Chart + values → rendered YAML → a release with revisions | The idea |
| 4 | `version` vs `appVersion`, three examples including the `1.10` → `1.1` trap | Chart version vs app version |
| 5 | Values stack: values.yaml < -f < -f < --set | Precedence |
| 6 | The capstone's real `helm history`: install, upgrade, failed, rollback | Release lifecycle |
| 7 | One chart version → dev / staging / prod, and the test gate | Multiple environments |
| 8 | Six real error messages from the troubleshooting scenarios | Failures you meet at work |
| 9 | Number tiles: labs, scenarios, challenges, pages, chapters, video, PDF | Study material |
| 10 | Terminal staircase: clone, kind, Traefik, dependency build, install, test | Run it yourself |
| 11 | QR codes to the repository and the portfolio, and a question | Links |

## How to post

1. Start a post, choose **Add a document**, and upload `carousel/carousel.pdf`.
2. Title, for example *"From 1,374 lines of copied YAML to one Helm chart"*.
3. Paste the text from `post.md`.
4. Optional: post `project-image.png` as a single image instead, or the 11 PNGs as a multi-image post.
5. Answer Helm questions in the comments with the matching scenario in `troubleshooting/`.
