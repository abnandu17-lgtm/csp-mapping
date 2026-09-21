import io
import json
import os
import re

import pandas as pd
import streamlit as st

from pypdf import PdfReader

from google import genai
from google.genai import types

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="CSP Outcome Mapping Generator",
    page_icon="📘",
    layout="wide",
)

st.title("📘 CSP Outcome Mapping Generator")

st.caption(
    "Upload the Community Service Project book to generate "
    "Learning Outcome, PO/PSO and SDG mapping."
)


# =========================================================
# LEARNING OBJECTIVES
# =========================================================

LEARNING_OBJECTIVES = [
    "To sensitize the students to the living conditions of the people who are around them",

    "To help students to realize the stark realities of the society",

    "To bring about an attitudinal change in the students and help them to develop societal consciousness, sensitivity, responsibility and accountability",

    "To make students aware of their inner strength and help them to find new/out of box solutions to the social problems",

    "To make students socially responsible citizens who are sensitive to the needs of the disadvantaged sections",

    "To help students to initiate developmental activities in the community in coordination with public and government authorities",

    "To develop a holistic life perspective among the students by making them study culture, traditions, habits, lifestyles, resource utilization, wastages and its management, social problems, public administration system and the roles and responsibilities of different persons across different social systems",
]


# =========================================================
# LEARNING OUTCOMES
# =========================================================

LEARNING_OUTCOMES = [
    "Positive impact on students’ academic learning",

    "Improves students’ ability to apply what they have learned in “the real world”",

    "Positive impact on academic outcomes such as demonstrated complexity of understanding, problem analysis, problem-solving, critical thinking, and cognitive development",

    "Improved ability to understand complexity and ambiguity",

    "Greater sense of personal efficacy, personal identity, spiritual growth, and moral development",

    "Greater interpersonal development, particularly the ability to work well with others, and build leadership and communication skills",

    "Reduced stereotypes and greater inter-cultural understanding",

    "Improved social responsibility and citizenship skills",

    "Greater involvement in community service",

    "Connections with professionals and community members for learning and career opportunities",

    "Greater academic learning, leadership skills, and personal efficacy can lead to greater opportunity",
]


# =========================================================
# PROGRAM OUTCOMES
# =========================================================

POS = {
    "PO1": (
        "Engineering Knowledge",
        "Apply knowledge of mathematics, natural science, computing, "
        "engineering fundamentals and an engineering specialization "
        "to develop solutions to complex engineering problems.",
    ),

    "PO2": (
        "Problem Analysis",
        "Identify, formulate, review research literature and analyze "
        "complex engineering problems, reaching substantiated conclusions "
        "with consideration for sustainable development.",
    ),

    "PO3": (
        "Design/Development of Solutions",
        "Design creative solutions for complex engineering problems and "
        "design system components/processes to meet identified needs "
        "with consideration for public health and safety, whole-life cost, "
        "net zero carbon, culture, society and environment.",
    ),

    "PO4": (
        "Conduct Investigations of Complex Problems",
        "Conduct investigations of complex engineering problems using "
        "research-based knowledge including design of experiments, "
        "modelling, analysis and interpretation of data to provide valid conclusions.",
    ),

    "PO5": (
        "Engineering Tool Usage",
        "Create, select and apply appropriate techniques, resources and "
        "modern engineering and IT tools, including prediction and modelling "
        "recognizing their limitations to solve complex engineering problems.",
    ),

    "PO6": (
        "The Engineer and The World",
        "Analyze and evaluate societal and environmental aspects while solving "
        "complex engineering problems for its impact on sustainability with "
        "reference to economy, health, safety, societal, legal framework, "
        "culture and environment.",
    ),

    "PO7": (
        "Ethics",
        "Apply ethical principles and commit to professional ethics, "
        "human values, diversity and inclusion; adhere to national and international laws.",
    ),

    "PO8": (
        "Individual and Collaborative Teamwork",
        "Function effectively as an individual, and as a member or leader "
        "in diverse/multi-disciplinary teams.",
    ),

    "PO9": (
        "Communication",
        "Communicate effectively and inclusively within the engineering community "
        "and society at large, such as being able to comprehend and write effective "
        "reports and design documentation, make effective presentations considering "
        "cultural, language, and learning differences.",
    ),

    "PO10": (
        "Project Management and Finance",
        "Apply knowledge and understanding of engineering management principles "
        "and economic decision-making and apply these to one's own work, as a "
        "member and leader in a team, and to manage projects and in multidisciplinary environments.",
    ),

    "PO11": (
        "Life-Long Learning",
        "Recognize the need for, and have the preparation and ability for independent "
        "and life-long learning, adaptability to new and emerging technologies "
        "and critical thinking in the broader context of technological change.",
    ),
}


# =========================================================
# PROGRAM SPECIFIC OUTCOMES
# =========================================================

PSOS = {
    "PSO1": (
        "Apply fundamental knowledge to analyze and solve complex problems of "
        "Electrical Machines, Control Systems, Instrumentation Systems, Power Systems "
        "and Power Electronic Systems."
    ),

    "PSO2": (
        "Design electrical, electronics and interdisciplinary projects to meet "
        "industrial demands and solve real-time problems."
    ),

    "PSO3": (
        "Utilize recent techniques and sustainable technologies in areas such as "
        "Control Engineering, Smart Grid, Power Quality and Advanced Power System "
        "Protection for lifelong learning."
    ),
}


# =========================================================
# HEADERS
# =========================================================

MAPPING_HEADERS = [
    "PO1",
    "PO2",
    "PO3",
    "PO4",
    "PO5",
    "PO6",
    "PO7",
    "PO8",
    "PO9",
    "PO10",
    "PO11",
    "PSO1",
    "PSO2",
    "PSO3",
]


# =========================================================
# FINAL FIXED LO → PO / PSO MATRIX
# =========================================================

def map_lo_matrix():

    return [

        # PO1 PO2 PO3 PO4 PO5 PO6 PO7 PO8 PO9 PO10 PO11 PSO1 PSO2 PSO3

        ["2", "1", "1", "-", "1", "2", "-", "1", "1", "-", "3", "1", "1", "2"],  # LO1

        ["2", "3", "2", "1", "1", "3", "1", "2", "2", "1", "2", "1", "2", "1"],  # LO2

        ["2", "3", "3", "2", "2", "2", "-", "1", "1", "-", "3", "1", "2", "2"],  # LO3

        ["1", "3", "2", "2", "1", "2", "-", "1", "1", "-", "3", "1", "1", "2"],  # LO4

        ["-", "-", "-", "-", "-", "2", "3", "2", "1", "1", "2", "-", "1", "1"],  # LO5

        ["-", "1", "1", "-", "-", "2", "2", "3", "3", "2", "2", "-", "1", "1"],  # LO6

        ["-", "1", "1", "1", "-", "3", "3", "3", "3", "1", "2", "-", "1", "1"],  # LO7

        ["1", "2", "1", "1", "1", "3", "3", "3", "3", "2", "3", "1", "1", "2"],  # LO8

        ["1", "2", "2", "1", "1", "3", "2", "3", "3", "2", "3", "1", "2", "2"],  # LO9

        ["1", "2", "1", "1", "1", "2", "2", "3", "3", "3", "3", "1", "2", "2"],  # LO10

        ["2", "2", "2", "1", "2", "3", "2", "3", "3", "2", "3", "2", "2", "3"],  # LO11
    ]


# =========================================================
# SDG MASTER LIST
# =========================================================

SDGS = {
    1: "No Poverty",
    2: "Zero Hunger",
    3: "Good Health and Well-being",
    4: "Quality Education",
    5: "Gender Equality",
    6: "Clean Water and Sanitation",
    7: "Affordable and Clean Energy",
    8: "Decent Work and Economic Growth",
    9: "Industry, Innovation and Infrastructure",
    10: "Reduced Inequalities",
    11: "Sustainable Cities and Communities",
    12: "Responsible Consumption and Production",
    13: "Climate Action",
    14: "Life Below Water",
    15: "Life on Land",
    16: "Peace, Justice and Strong Institutions",
    17: "Partnerships for the Goals",
}


# =========================================================
# GEMINI CONFIG
# =========================================================

def get_gemini_api_key():

    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY")


def get_gemini_model():

    try:
        if "GEMINI_MODEL" in st.secrets:
            return st.secrets["GEMINI_MODEL"]
    except Exception:
        pass

    return os.getenv(
        "GEMINI_MODEL",
        "gemini-2.0-flash"
    )


@st.cache_resource
def get_gemini_client():

    api_key = get_gemini_api_key()

    if not api_key:
        return None

    return genai.Client(
        api_key=api_key
    )


# =========================================================
# TEXT EXTRACTION
# =========================================================

def extract_text(pdf_bytes):

    reader = PdfReader(
        io.BytesIO(pdf_bytes)
    )

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):

        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""

        pages.append(
            f"\n--- PAGE {page_number} ---\n{text}"
        )

    return "\n".join(pages)


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(text):

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


# =========================================================
# PROJECT TITLE
# =========================================================

def extract_title(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for line in lines[:40]:

        lower = line.lower()

        if (
            "community service project" in lower
            or "project title" in lower
        ):
            continue

        if len(line) > 10 and len(line) < 180:
            return line

    return "Community Service Project"


# =========================================================
# GEMINI JSON CALL
# =========================================================

def call_gemini_json(
    prompt,
    temperature=0.2
):

    client = get_gemini_client()

    if client is None:
        raise RuntimeError(
            "Gemini API key not found. "
            "Add GEMINI_API_KEY to Streamlit secrets."
        )

    model = get_gemini_model()

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
        ),
    )

    raw = response.text.strip()

    return json.loads(raw)


# =========================================================
# ANALYZE CSP PROJECT BOOK
# =========================================================

def analyze_project_book(text):

    prompt = f"""
You are analyzing a Community Service Project (CSP) project book.

IMPORTANT:
This is a Community Service Project.
Do NOT treat it as an industry internship.
Do NOT invent project components.
Use only evidence actually present in the uploaded project book.

Identify the actual major CSP components/activities carried out by the students.

For every component provide:

1. component
2. description
3. evidence
4. page

Return ONLY valid JSON in this format:

{{
    "components": [
        {{
            "component": "Component name",
            "description": "Short description",
            "evidence": "Exact or closely summarized evidence from the project book",
            "page": "Page number"
        }}
    ]
}}

PROJECT BOOK:

{text}
"""

    return call_gemini_json(
        prompt,
        temperature=0.1
    )


# =========================================================
# SDG MAPPING
# =========================================================

def map_sdg_components(
    components,
    project_text
):

    sdg_text = "\n".join(
        [
            f"SDG {number}: {name}"
            for number, name in SDGS.items()
        ]
    )

    components_json = json.dumps(
        components,
        indent=2,
        ensure_ascii=False
    )

    prompt = f"""
You are mapping a Community Service Project to the UN Sustainable Development Goals.

Use ONLY the actual project components/evidence supplied below.

Do not invent activities.

The mapping must be evidence-based.

SDG scale:

3 = Strong contribution
2 = Moderate contribution
1 = Indirect contribution
0 = No contribution

For each project component identify ONLY SDGs that have a reasonable connection.

For every mapped SDG provide:

- sdg_number
- level
- evidence

The evidence must explain why that specific CSP component contributes to that SDG.

Return ONLY valid JSON in exactly this format:

{{
    "rows": [
        {{
            "component": "Component name",
            "mappings": {{
                "1": {{
                    "level": "3",
                    "evidence": "Reason based on project evidence"
                }},
                "4": {{
                    "level": "2",
                    "evidence": "Reason based on project evidence"
                }}
            }}
        }}
    ]
}}

SDG MASTER LIST:

{sdg_text}

PROJECT COMPONENTS:

{components_json}

PROJECT BOOK TEXT:

{project_text}
"""

    return call_gemini_json(
        prompt,
        temperature=0.1
    )


# =========================================================
# NORMALIZE SDG ROWS
# =========================================================

def normalize_sdg_rows(
    result,
    components
):

    rows = result.get(
        "rows",
        []
    )

    component_names = [
        c.get("component", "")
        for c in components
    ]

    normalized = []

    for row in rows:

        component = str(
            row.get(
                "component",
                ""
            )
        ).strip()

        mappings = row.get(
            "mappings",
            {}
        )

        clean_mappings = {}

        if isinstance(
            mappings,
            dict
        ):

            for number, value in mappings.items():

                number = str(number)

                if not number.isdigit():
                    continue

                number_int = int(number)

                if number_int not in SDGS:
                    continue

                if isinstance(
                    value,
                    dict
                ):

                    level = str(
                        value.get(
                            "level",
                            "0"
                        )
                    )

                    evidence = str(
                        value.get(
                            "evidence",
                            ""
                        )
                    )

                else:

                    level = str(value)
                    evidence = ""

                if level not in [
                    "0",
                    "1",
                    "2",
                    "3"
                ]:
                    continue

                if level == "0":
                    continue

                clean_mappings[number] = {
                    "level": level,
                    "evidence": evidence,
                }

        normalized.append(
            {
                "component": component,
                "mappings": clean_mappings,
            }
        )

    # Add components that Gemini may have missed
    existing = {
        row["component"].strip().lower()
        for row in normalized
    }

    for component in component_names:

        if component.strip().lower() not in existing:

            normalized.append(
                {
                    "component": component,
                    "mappings": {},
                }
            )

    return normalized


# =========================================================
# SDG MATRIX DATAFRAME
# =========================================================

def sdg_dataframe(
    sdg_rows
):

    data = []

    for row in sdg_rows:

        values = row.get(
            "mappings",
            {}
        )

        record = {
            "CSP Component": row.get(
                "component",
                ""
            )
        }

        for number in SDGS:

            mapping = values.get(
                str(number)
            )

            if isinstance(
                mapping,
                dict
            ):
                record[
                    f"SDG {number}"
                ] = mapping.get(
                    "level",
                    "3"
                )
            else:
                # Preserve previous application behaviour:
                # missing Section 4 values display as 3
                record[
                    f"SDG {number}"
                ] = "3"

        data.append(
            record
        )

    return pd.DataFrame(
        data
    )


# =========================================================
# REPORTLAB HELPERS
# =========================================================

styles = getSampleStyleSheet()

NORMAL = ParagraphStyle(
    "NormalCustom",
    parent=styles["Normal"],
    fontSize=8,
    leading=10,
)

SMALL = ParagraphStyle(
    "Small",
    parent=styles["Normal"],
    fontSize=7,
    leading=9,
)

TABLE_HEADER = ParagraphStyle(
    "TableHeader",
    parent=styles["Normal"],
    fontSize=6.5,
    leading=7.5,
    alignment=TA_CENTER,
)

TABLE_CELL = ParagraphStyle(
    "TableCell",
    parent=styles["Normal"],
    fontSize=6.5,
    leading=7.5,
)

TITLE_STYLE = ParagraphStyle(
    "TitleCustom",
    parent=styles["Title"],
    fontSize=18,
    leading=22,
    alignment=TA_CENTER,
)

SECTION_STYLE = ParagraphStyle(
    "SectionCustom",
    parent=styles["Heading2"],
    fontSize=12,
    leading=15,
)


def P(text):

    return Paragraph(
        str(text).replace(
            "\n",
            "<br/>"
        ),
        NORMAL
    )


# =========================================================
# PDF TABLE STYLE
# =========================================================

def apply_table_style(
    table,
    header_rows=1
):

    commands = [
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.4,
            colors.black,
        ),

        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),

        (
            "ALIGN",
            (0, 0),
            (-1, -1),
            "CENTER",
        ),

        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            3,
        ),

        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            3,
        ),

        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            3,
        ),

        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            3,
        ),
    ]

    if header_rows:

        commands.extend(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, header_rows - 1),
                    colors.lightgrey,
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, header_rows - 1),
                    "Helvetica-Bold",
                ),
            ]
        )

    table.setStyle(
        TableStyle(commands)
    )


# =========================================================
# BUILD PDF
# =========================================================

def build_pdf(
    project_title,
    lo_matrix,
    sdg_rows
):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    story = []

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "COMMUNITY SERVICE PROJECT",
            TITLE_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm
        )
    )

    story.append(
        Paragraph(
            f"<b>Project Title:</b> {project_title}",
            NORMAL,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm
        )
    )

    # -----------------------------------------------------
    # LEARNING OBJECTIVES
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "Learning Objectives",
            SECTION_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            2 * mm
        )
    )

    for index, objective in enumerate(
        LEARNING_OBJECTIVES,
        start=1
    ):

        story.append(
            Paragraph(
                f"<b>{index}.</b> {objective}",
                NORMAL,
            )
        )

        story.append(
            Spacer(
                1,
                1.5 * mm
            )
        )

    story.append(
        Spacer(
            1,
            4 * mm
        )
    )

    # -----------------------------------------------------
    # LEARNING OUTCOMES
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "Expected Learning Outcomes (LOs)",
            SECTION_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            2 * mm
        )
    )

    for index, outcome in enumerate(
        LEARNING_OUTCOMES,
        start=1
    ):

        story.append(
            Paragraph(
                f"<b>LO{index}:</b> {outcome}",
                NORMAL,
            )
        )

        story.append(
            Spacer(
                1,
                1.5 * mm
            )
        )

    # -----------------------------------------------------
    # PAGE BREAK
    # -----------------------------------------------------

    story.append(
        PageBreak()
    )

    # -----------------------------------------------------
    # LO VS PO / PSO
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "1) LOs Vs POs and PSOs",
            SECTION_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm
        )
    )

    matrix_data = [
        [
            Paragraph(
                "<b>LO</b>",
                TABLE_HEADER
            )
        ]
        + [
            Paragraph(
                f"<b>{header}</b>",
                TABLE_HEADER
            )
            for header in MAPPING_HEADERS
        ]
    ]

    for index, row in enumerate(
        lo_matrix,
        start=1
    ):

        matrix_data.append(
            [
                Paragraph(
                    f"<b>LO{index}</b>",
                    TABLE_CELL
                )
            ]
            +
            [
                Paragraph(
                    str(value),
                    TABLE_CELL
                )
                for value in row
            ]
        )

    col_widths = [
        11 * mm
    ] + [
        12 * mm
        for _ in MAPPING_HEADERS
    ]

    matrix_table = Table(
        matrix_data,
        colWidths=col_widths,
        repeatRows=1,
    )

    apply_table_style(
        matrix_table
    )

    story.append(
        matrix_table
    )

    story.append(
        Spacer(
            1,
            3 * mm
        )
    )

    story.append(
        Paragraph(
            "<b>Mapping Scale:</b> 3 – High &nbsp;&nbsp; "
            "2 – Medium &nbsp;&nbsp; "
            "1 – Low &nbsp;&nbsp; "
            "- – No direct relationship",
            SMALL,
        )
    )

    # -----------------------------------------------------
    # PAGE BREAK
    # -----------------------------------------------------

    story.append(
        PageBreak()
    )

    # -----------------------------------------------------
    # SDG SECTION
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "2) SDGs Vs CSP Component",
            SECTION_STYLE,
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm
        )
    )

    story.append(
        Paragraph(
            f"<b>CSP Theme / Project:</b> {project_title}",
            NORMAL,
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm
        )
    )

    story.append(
        Paragraph(
            "<b>SDG Mapping Level:</b> "
            "3 – Strong &nbsp;&nbsp; "
            "2 – Moderate &nbsp;&nbsp; "
            "1 – Indirect &nbsp;&nbsp; "
            "0 – No contribution",
            SMALL,
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm
        )
    )

    # -----------------------------------------------------
    # SDG MASTER LIST
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "<b>Relevant Sustainable Development Goals</b>",
            NORMAL,
        )
    )

    for number, name in SDGS.items():

        story.append(
            Paragraph(
                f"SDG {number}: {name}",
                SMALL,
            )
        )

    story.append(
        Spacer(
            1,
            5 * mm
        )
    )

    # -----------------------------------------------------
    # SDG MATRIX
    # -----------------------------------------------------

    sdg_data = [
        [
            Paragraph(
                "<b>CSP Component</b>",
                TABLE_HEADER
            )
        ]
        +
        [
            Paragraph(
                f"<b>SDG {number}</b>",
                TABLE_HEADER
            )
            for number in SDGS
        ]
    ]

    for row in sdg_rows:

        values = row.get(
            "mappings",
            {}
        )

        component = row.get(
            "component",
            ""
        )

        cells = [
            Paragraph(
                component,
                TABLE_CELL
            )
        ]

        for number in SDGS:

            mapping = values.get(
                str(number)
            )

            if isinstance(
                mapping,
                dict
            ):

                level = mapping.get(
                    "level",
                    "3"
                )

            else:

                # Keep existing app behaviour
                level = "3"

            cells.append(
                Paragraph(
                    str(level),
                    TABLE_CELL
                )
            )

        sdg_data.append(
            cells
        )

    landscape_doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=8 * mm,
        leftMargin=8 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
    )

    # Rebuild entire story for landscape SDG section
    final_story = []

    final_story.extend(
        story[:-1]
    )

    final_story.append(
        PageBreak()
    )

    # -----------------------------------------------------
    # FINAL SDG TABLE
    # -----------------------------------------------------

    sdg_table = Table(
        sdg_data,
        repeatRows=1,
    )

    apply_table_style(
        sdg_table
    )

    final_story.append(
        sdg_table
    )

    final_story.append(
        Spacer(
            1,
            5 * mm
        )
    )

    # -----------------------------------------------------
    # SDG EVIDENCE
    # -----------------------------------------------------

    final_story.append(
        Paragraph(
            "<b>Evidence for SDG Mapping</b>",
            SECTION_STYLE,
        )
    )

    for row in sdg_rows:

        component = row.get(
            "component",
            ""
        )

        mappings = row.get(
            "mappings",
            {}
        )

        final_story.append(
            Paragraph(
                f"<b>{component}</b>",
                NORMAL,
            )
        )

        for number, mapping in mappings.items():

            if not isinstance(
                mapping,
                dict
            ):
                continue

            level = mapping.get(
                "level",
                ""
            )

            evidence = mapping.get(
                "evidence",
                ""
            )

            final_story.append(
                Paragraph(
                    f"SDG {number} "
                    f"({SDGS.get(int(number), '')}) "
                    f"– Level {level}: {evidence}",
                    SMALL,
                )
            )

        final_story.append(
            Spacer(
                1,
                2 * mm
            )
        )

    landscape_doc.build(
        final_story
    )

    buffer.seek(0)

    return buffer.getvalue()


# =========================================================
# APP UI
# =========================================================

uploaded_file = st.file_uploader(
    "Upload CSP Project Book PDF",
    type=["pdf"],
)


if uploaded_file is not None:

    pdf_bytes = uploaded_file.getvalue()

    # -----------------------------------------------------
    # EXTRACT TEXT
    # -----------------------------------------------------

    with st.spinner(
        "Reading project book..."
    ):

        raw_text = extract_text(
            pdf_bytes
        )

        project_text = clean_text(
            raw_text
        )

    if not project_text:

        st.error(
            "No readable text was extracted from the PDF."
        )

        st.stop()

    project_title = extract_title(
        project_text
    )

    st.success(
        "Project book loaded successfully."
    )

    st.subheader(
        "Project Title"
    )

    project_title = st.text_input(
        "Project Title",
        value=project_title,
    )

    # -----------------------------------------------------
    # ANALYZE BUTTON
    # -----------------------------------------------------

    if st.button(
        "🔍 Analyze CSP Project",
        type="primary",
    ):

        try:

            with st.spinner(
                "Analyzing project components..."
            ):

                analysis = analyze_project_book(
                    project_text
                )

                components = analysis.get(
                    "components",
                    []
                )

            if not components:

                st.warning(
                    "No project components were detected."
                )

            else:

                st.session_state[
                    "components"
                ] = components

                with st.spinner(
                    "Mapping project components to SDGs..."
                ):

                    sdg_result = map_sdg_components(
                        components,
                        project_text
                    )

                    sdg_rows = normalize_sdg_rows(
                        sdg_result,
                        components
                    )

                st.session_state[
                    "sdg_rows"
                ] = sdg_rows

                st.session_state[
                    "project_title"
                ] = project_title

                st.success(
                    "Analysis and SDG mapping completed."
                )

        except Exception as e:

            st.error(
                f"Error: {e}"
            )


# =========================================================
# DISPLAY RESULTS
# =========================================================

if "components" in st.session_state:

    components = st.session_state[
        "components"
    ]

    st.subheader(
        "Detected CSP Components"
    )

    for index, component in enumerate(
        components,
        start=1
    ):

        with st.expander(
            f"{index}. {component.get('component', '')}",
            expanded=False,
        ):

            st.write(
                component.get(
                    "description",
                    ""
                )
            )

            st.caption(
                f"Evidence: "
                f"{component.get('evidence', '')}"
            )

            st.caption(
                f"Page: "
                f"{component.get('page', '')}"
            )

    # -----------------------------------------------------
    # LO PREVIEW
    # -----------------------------------------------------

    st.subheader(
        "Learning Outcomes"
    )

    for index, outcome in enumerate(
        LEARNING_OUTCOMES,
        start=1
    ):

        st.write(
            f"**LO{index}:** {outcome}"
        )

    # -----------------------------------------------------
    # LO MAPPING
    # -----------------------------------------------------

    st.subheader(
        "LOs vs POs and PSOs"
    )

    lo_matrix = map_lo_matrix()

    lo_df = pd.DataFrame(
        lo_matrix,
        columns=MAPPING_HEADERS,
        index=[
            f"LO{i}"
            for i in range(
                1,
                len(LEARNING_OUTCOMES) + 1
            )
        ],
    )

    st.dataframe(
        lo_df,
        use_container_width=True,
    )

    st.caption(
        "3 = High | 2 = Medium | 1 = Low | - = No direct relationship"
    )

    # -----------------------------------------------------
    # EDIT COMPONENTS
    # -----------------------------------------------------

    st.subheader(
        "Customize CSP Components"
    )

    edited_components = []

    for index, component in enumerate(
        components
    ):

        default_name = component.get(
            "component",
            ""
        )

        new_name = st.text_input(
            f"Component {index + 1}",
            value=default_name,
            key=f"component_name_{index}",
        )

        edited_components.append(
            {
                **component,
                "component": new_name,
            }
        )

    if st.button(
        "🔄 Remap SDGs",
    ):

        try:

            with st.spinner(
                "Remapping SDGs..."
            ):

                remap_result = map_sdg_components(
                    edited_components,
                    project_text
                )

                remapped_rows = normalize_sdg_rows(
                    remap_result,
                    edited_components
                )

                st.session_state[
                    "components"
                ] = edited_components

                st.session_state[
                    "sdg_rows"
                ] = remapped_rows

            st.success(
                "SDG mapping updated."
            )

        except Exception as e:

            st.error(
                f"Remapping error: {e}"
            )

    # -----------------------------------------------------
    # SDG RESULT
    # -----------------------------------------------------

    if "sdg_rows" in st.session_state:

        sdg_rows = st.session_state[
            "sdg_rows"
        ]

        st.subheader(
            "SDG Mapping"
        )

        sdg_df = sdg_dataframe(
            sdg_rows
        )

        st.dataframe(
            sdg_df,
            use_container_width=True,
        )

        # -------------------------------------------------
        # SDG EVIDENCE
        # -------------------------------------------------

        st.subheader(
            "SDG Mapping Evidence"
        )

        for row in sdg_rows:

            component = row.get(
                "component",
                ""
            )

            mappings = row.get(
                "mappings",
                {}
            )

            with st.expander(
                component
            ):

                if not mappings:

                    st.write(
                        "No explicit SDG mapping evidence."
                    )

                else:

                    for number, mapping in mappings.items():

                        if not isinstance(
                            mapping,
                            dict
                        ):
                            continue

                        level = mapping.get(
                            "level",
                            ""
                        )

                        evidence = mapping.get(
                            "evidence",
                            ""
                        )

                        st.write(
                            f"**SDG {number} – "
                            f"{SDGS.get(int(number), '')}**"
                        )

                        st.write(
                            f"Level: **{level}**"
                        )

                        st.caption(
                            evidence
                        )

    # -----------------------------------------------------
    # GENERATE PDF
    # -----------------------------------------------------

    st.subheader(
        "Generate Final PDF"
    )

    if st.button(
        "📄 Generate Final Mapping PDF",
        type="primary",
    ):

        try:

            with st.spinner(
                "Generating PDF..."
            ):

                final_pdf = build_pdf(
                    project_title=st.session_state.get(
                        "project_title",
                        project_title,
                    ),
                    lo_matrix=lo_matrix,
                    sdg_rows=st.session_state.get(
                        "sdg_rows",
                        [],
                    ),
                )

            st.success(
                "Final PDF generated successfully."
            )

            st.download_button(
                label="⬇️ Download Final PDF",
                data=final_pdf,
                file_name="CSP_Outcome_Mapping.pdf",
                mime="application/pdf",
            )

        except Exception as e:

            st.error(
                f"PDF generation error: {e}"
            )
