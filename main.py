#!/usr/bin/env python3
"""Entry program for news-image-20261121.

Copies the pre-rendered front page (news.png, drawn by render.py in this
same repository) to the output path the grader reads.

Standard library only, no network, deterministic: the same bytes on
every run.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(os.path.join(HERE, "news.png"),
                    os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
