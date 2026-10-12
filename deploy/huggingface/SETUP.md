# Deploying `amr-engine` to a Hugging Face Space

This repository does not need a server: the three panels are self-contained
HTML and already run on GitHub Pages. So why a Space at all?

**Discovery.** GitHub Pages is a URL you have to already know. Hugging Face
Spaces has a browse page, a trending list, likes and a tag system — people
arrive without being sent. The Space is not a better runtime, it is a second
front door, and it costs nothing: a `static` Space is free, never sleeps, and
has no build step.

The authoritative copy stays on GitHub. The Space mirrors the landing page,
the three panels and the documents, and links back.

## 1. Create the Space

```bash
hf repos create vinhatson/amr-engine --type space --sdk static
```

Or at <https://huggingface.co/new-space>: SDK **Static**, license
`apache-2.0`, public.

## 2. Push the front end

A static Space serves whatever is at its root, so only the browser-facing
files go up. The Python engine, the tests and the tools stay on GitHub —
shipping `.py` files to a host that cannot run them is noise in the file
listing.

```bash
# from a clean staging directory, not the repository itself
cp -r /path/to/amr-engine/{index.html,panels,docs,SPEC.md,LICENSE,NOTICE,CITATION.cff} .
cp /path/to/amr-engine/deploy/huggingface/README.md README.md   # carries the frontmatter

hf upload vinhatson/amr-engine . . --type space
```

The Space's own `README.md` must be the one in this directory: it holds the
`sdk: static` and `app_file: index.html` frontmatter the platform reads. The
repository's own `README.md` is written for GitHub and has no frontmatter, so
uploading it instead produces a Space that builds but shows nothing.

## 3. Link the two together

Put the Space URL in the GitHub repository's About sidebar. The Space README
already points back at GitHub. A Space with no source link reads as a toy,
and a repository that does not mention its live copy loses the visitor who
wanted to click rather than clone.

## What not to do

Do not give this Space the `docker` SDK. There is nothing to serve — a
container would add a build, a cold start and a sleep timer in exchange for
nothing. `sccdx-engine` needs Docker because it computes server-side on
purpose; this one does not.
