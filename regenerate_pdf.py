#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

FONT_REGULAR = os.path.expanduser("~/.local/share/fonts/NotoSerifCJKsc-VF.ttf")
FONT_BOLD = os.path.expanduser("~/.local/share/fonts/NotoSerifCJKsc-VF.ttf")
FONT_NAME = "NotoSerifCJKSC"

pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_REGULAR))

PAGE_W, PAGE_H = A4

DATA_PATH = "/home/yfisher/projects/github/Resume/resume_data.json"
OUTPUT_PATH = "/home/yfisher/projects/github/Resume/俞凡简历_架构_修复.pdf"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

SECTION_TITLES = {"个人优势", "工作经历", "项目经历", "教育经历", "资格证书"}
COMPANY_LINE_HEIGHT = 12.0


def fontSizeForHeight(fontHeight):
    if fontHeight >= 20:
        return 16
    elif fontHeight >= 14:
        return 12
    elif fontHeight >= COMPANY_LINE_HEIGHT:
        return 10.5
    else:
        return 9.5


def isSectionTitle(text):
    return text.strip() in SECTION_TITLES


def buildPdf():
    c = canvas.Canvas(OUTPUT_PATH, pagesize=A4)
    c.setTitle("俞凡简历_架构")

    for pageKey in sorted(data.keys()):
        lines = data[pageKey]
        for line in lines:
            yTop = line["y"]
            xLeft = line["x0"]
            heights = line["heights"]
            text = line["text"]

            fontHeight = max(heights) if heights else 11.0
            drawSize = fontSizeForHeight(fontHeight)

            # Convert top coordinate: pdfplumber top from page top, reportlab y from page bottom
            yReportlab = PAGE_H - yTop - drawSize

            c.setFont(FONT_NAME, drawSize)
            c.drawString(xLeft, yReportlab, text)

        c.showPage()

    c.save()
    print(f"PDF saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    buildPdf()
