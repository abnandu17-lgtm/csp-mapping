import io
import re

import pandas as pd
import streamlit as st
from pypdf import PdfReader

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
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


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="CSP Outcome Mapping Generator",
    page_icon="📘",
    layout="wide",
)


# ============================================================
# FIXED COURSE OUTCOMES
# ============================================================

COS = [
    (
        "CO1",
        "Describe/Explain the social, technical, and safety-related conditions, needs, and problems observed in the community.",
        "Understand (L2)",
    ),
    (
        "CO2",
        "Apply fundamental concepts of electrical and electronics engineering to understand and address real-time problems identified in the community.",
        "Apply (L3)",
    ),
    (
        "CO3",
        "Analyze the problems, needs, existing practices, and possible solutions identified during the community service activities.",
        "Analyze (L4)",
    ),
    (
        "CO4",
        "Demonstrate professional ethics, social responsibility, teamwork, communication, and safety practices while interacting with the community and conducting service activities.",
        "Apply/Evaluate (L3/L5)",
    ),
    (
        "CO5",
        "Prepare and present a technical Community Service Project report/seminar documenting the community observations, survey findings, activities carried out, outcomes, and learning experiences using appropriate technical vocabulary and presentation tools.",
        "Create (L6)",
    ),
]


# ============================================================
# PROGRAM OUTCOMES
# ============================================================

POS = [
    (
        "PO1",
        "Engineering Knowledge: Apply knowledge of mathematics, natural science, computing, engineering fundamentals and an engineering specialization to develop solutions to complex engineering problems.",
    ),
    (
        "PO2",
        "Problem Analysis: Identify, formulate, review research literature and analyze complex engineering problems, reaching substantiated conclusions with consideration for sustainable development.",
    ),
    (
        "PO3",
        "Design/Development of Solutions: Design creative solutions for complex engineering problems and design system components/processes to meet identified needs with consideration for public health and safety, whole-life cost, net zero carbon, culture, society and environment.",
    ),
    (
        "PO4",
        "Conduct Investigations of Complex Problems: Conduct investigations of complex engineering problems using research-based knowledge including design of experiments, modelling, analysis & interpretation of data to provide valid conclusions.",
    ),
    (
        "PO5",
        "Engineering Tool Usage: Create, select and apply appropriate techniques, resources and modern engineering & IT tools, including prediction and modelling recognizing their limitations to solve complex engineering problems.",
    ),
    (
        "PO6",
        "The Engineer and The World: Analyze and evaluate societal and environmental aspects while solving complex engineering problems for its impact on sustainability with reference to economy, health, safety, societal, legal framework, culture and environment.",
    ),
    (
        "PO7",
        "Ethics: Apply ethical principles and commit to professional ethics, human values, diversity and inclusion; adhere to national & international laws.",
    ),
    (
        "PO8",
        "Individual and Collaborative Team work: Function effectively as an individual, and as a member or leader in diverse/multi-disciplinary teams.",
    ),
    (
        "PO9",
        "Communication: Communicate effectively and inclusively within the engineering community and society at large, such as being able to comprehend and write effective reports and design documentation, make effective presentations considering cultural, language, and learning differences.",
    ),
    (
        "PO10",
        "Project Management and Finance: Apply knowledge and understanding of engineering management principles and economic decision-making and apply these to one's own work, as a member and leader in a team, and to manage projects and in multidisciplinary environments.",
    ),
    (
        "PO11",
        "Life-Long Learning: Recognize the need for, and have the preparation and ability for independent and life-long learning, adaptability to new and emerging technologies and critical thinking in the broader context of technological change.",
    ),
]


# ============================================================
# PROGRAM SPECIFIC OUTCOMES
# ============================================================

PSOS = [
    (
        "PSO1",
        "Apply fundamental knowledge to analyze and solve complex problems of Electrical Machines, Control Systems, Instrumentation Systems, Power Systems and Power Electronic Systems.",
    ),
    (
        "PSO2",
        "Design electrical, electronics and interdisciplinary projects to meet industrial demands and solve real-time problems.",
    ),
    (
        "PSO3",
        "Utilize recent techniques and sustainable technologies in areas such as Control Engineering, Smart Grid, Power Quality and Advanced Power System Protection for lifelong learning.",
    ),
]


# ============================================================
# KNOWLEDGE PROFILE
# ============================================================

WKS = [
    (
        "WK1",
        "A systematic, theory-based understanding of the natural sciences applicable to the discipline and awareness of relevant social sciences.",
    ),
    (
        "WK2",
        "Conceptually-based mathematics, numerical analysis, data analysis, statistics and formal aspects of computer and information science to support detailed analysis and modelling applicable to the discipline.",
    ),
    (
        "WK3",
        "A systematic, theory-based formulation of engineering fundamentals required in the engineering discipline.",
    ),
    (
        "WK4",
        "Engineering specialist knowledge that provides theoretical frameworks and bodies of knowledge for the accepted practice areas in the engineering discipline; much is at the forefront of the discipline.",
    ),
    (
        "WK5",
        "Knowledge, including efficient resource use, environmental impacts, whole-life cost, re-use of resources, net zero carbon, and similar concepts, that supports engineering design and operations in a practice area.",
    ),
    (
        "WK6",
        "Knowledge of engineering practice (technology) in the practice areas in the engineering discipline.",
    ),
    (
        "WK7",
        "Knowledge of the role of engineering in society and identified issues in engineering practice, such as the professional responsibility of an engineer to public safety and sustainable development.",
    ),
    (
        "WK8",
        "Engagement with selected knowledge in the current research literature of the discipline, awareness of the power of critical thinking and creative approaches to evaluate emerging issues.",
    ),
    (
        "WK9",
        "Ethics, inclusive behavior and conduct. Knowledge of professional ethics, responsibilities, and norms of engineering practice. Awareness of the need for diversity by reason of ethnicity, gender, age, physical ability etc. with mutual understanding and respect, and of inclusive attitudes.",
    ),
]


# ============================================================
# FIXED WK → PO/PSO MATRIX
# ============================================================

FIXED_WK_MATRIX = [
    [2, 2, "-", "-", "-", 1, "-", "-", "-", "-", "-", "-", "-", "-"],
    [2, 2, "-", "-", 2, "-", "-", "-", "-", "-", "-", 1, "-", "-"],
    [3, 3, "-", "-", "-", "-", "-", "-", "-", "-", "-", 2, "-", "-"],
    [3, 3, "-", "-", "-", "-", "-", "-", "-", "-", "-", 3, 1, "-"],
    ["-", "-", 3, "-", "-", 3, "-", "-", "-", "-", "-", "-", 2, 2],
    ["-", "-", "-", "-", 3, "-", "-", "-", "-", "-", "-", "-", 3, 3],
    ["-", "-", "-", "-", "-", 3, "-", "-", "-", "-", "-", "-", "-", "-"],
    ["-", "-", "-", 3, "-", "-", "-", "-", "-", "-", 3, "-", "-", 2],
    ["-", "-", "-", "-", "-", "-", 3, "-", "-", "-", "-", "-", "-", "-"],
]

FIXED_WK_MATRIX = [
    [
        str(x).strip() if isinstance(x, str) else x
        for x in row
    ]
    for row in FIXED_WK_MATRIX
]


# ============================================================
# SDGs
# ============================================================

SDGS = {
    1: "End poverty in all its forms everywhere",
    2: "End hunger, achieve food security and improved nutrition and promote sustainable agriculture",
    3: "Ensure healthy lives and promote well-being for all at all ages",
    4: "Ensure inclusive and equitable quality education and promote lifelong learning opportunities for all",
    5: "Achieve gender equality and empower all women and girls",
    6: "Ensure availability and sustainable management of water and sanitation for all",
    7: "Ensure access to affordable, reliable, sustainable and modern energy for all",
    8: "Promote sustained, inclusive, and sustainable economic growth, full and productive employment and decent work for all",
    9: "Build resilient infrastructure, promote inclusive and sustainable industrialization and foster innovation",
    10: "Reduce inequality within and among countries",
    11: "Make cities and human settlements inclusive, safe, resilient and sustainable",
    12: "Ensure sustainable consumption and production patterns",
    13: "Take urgent action to combat climate change and its impacts",
    14: "Conserve and sustainably use the oceans, seas and marine resources for sustainable development",
    15: "Protect, restore and promote sustainable use of terrestrial ecosystems, sustainably manage forests, combat desertification, and halt and reverse land degradation and halt biodiversity loss",
    16: "Promote peaceful and inclusive societies for sustainable development, provide access to justice for all and build effective, accountable and inclusive institutions at all levels",
    17: "Strengthen the means of implementation and revitalize the global partnership for sustainable development",
}


HEADERS = (
    [f"PO{i}" for i in range(1, 12)]
    + ["PSO1", "PSO2", "PSO3"]
)


# ============================================================
# EXTRACT PDF TEXT
# ============================================================

def extract_text(uploaded):

    reader = PdfReader(uploaded)

    pages = []

    for page in reader.pages:

        try:
            pages.append(
                page.extract_text() or ""
            )

        except Exception:
            pages.append("")

    return "\n".join(pages)


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):

    text = text or ""

    text = text.replace(
        "\xa0",
        " "
    )

    text = text.replace(
        "&nbsp;",
        " "
    )

    text = text.replace(
        "&amp;",
        "&"
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# HELPERS
# ============================================================

def contains_any(text, keywords):

    return any(
        keyword in text
        for keyword in keywords
    )


def count_matches(text, keywords):

    return sum(
        1
        for keyword in keywords
        if keyword in text
    )


# ============================================================
# PROJECT TITLE
# ============================================================

def extract_title(text):

    patterns = [
        r"(?:project title|title of the project)\s*[:\-]\s*(.{5,180})",
        r"(?:project)\s*[:\-]\s*(.{5,180})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            title = clean_text(
                match.group(1)
            )

            return title[:180]

    return "Community Service Project"


# ============================================================
# DETECT ONLY RELEVANT PROJECT COMPONENTS
# ============================================================

def detect_components(text):

    t = clean_text(text).lower()

    component_rules = [

        (
            "Electrical Safety and Shock Prevention",
            [
                "electrical safety",
                "electric shock",
                "electrical shock",
                "shock prevention",
                "electrical hazards",
                "electrical hazard",
                "shock hazards",
            ],
        ),

        (
            "Electrical Earthing Awareness",
            [
                "earthing awareness",
                "grounding awareness",
                "awareness about earthing",
                "awareness on earthing",
                "importance of earthing",
                "importance of grounding",
                "earthing system awareness",
            ],
        ),

        (
            "Household Electrical Wiring and Earthing",
            [
                "household wiring",
                "house wiring",
                "domestic wiring",
                "household electrical",
                "electrical wiring and earthing",
                "wiring and earthing",
                "earthing in houses",
                "earthing in households",
            ],
        ),

        (
            "Agricultural Electrical Installations and Pump-Set Earthing",
            [
                "agricultural pump",
                "agricultural pump-set",
                "pump set earthing",
                "pump-set earthing",
                "agricultural electrical",
                "irrigation pump",
                "farm pump",
            ],
        ),

        (
            "Earthing Installation and Maintenance",
            [
                "earthing installation",
                "earthing maintenance",
                "maintenance of earthing",
                "installation of earthing",
                "earthing system installation",
                "earthing system maintenance",
                "grounding installation",
                "grounding maintenance",
            ],
        ),

        (
            "Fault Protection and Protective Devices",
            [
                "fault protection",
                "electrical protection",
                "protective devices",
                "protective device",
                "mcb",
                "rccb",
                "rcd",
                "elcb",
                "fuse protection",
                "overcurrent protection",
                "leakage protection",
            ],
        ),

        (
            "Earth Resistance Testing",
            [
                "earth resistance testing",
                "earth resistance measurement",
                "earth resistance",
                "ground resistance",
                "resistance of earth",
                "earth tester",
                "earth resistance tester",
                "megger",
                "earth continuity",
                "continuity testing",
            ],
        ),

        (
            "Safe Electrical Wiring Practices",
            [
                "safe wiring",
                "safe electrical wiring",
                "wiring practices",
                "electrical wiring practices",
                "proper wiring",
                "safe electrical practices",
            ],
        ),
    ]


    detected = []


    for component, keywords in component_rules:

        if contains_any(
            t,
            keywords
        ):

            if component not in detected:

                detected.append(
                    component
                )


    # No generic survey/report/teamwork fallback.

    if not detected:

        if (
            "earthing" in t
            or "grounding" in t
        ):

            detected = [
                "Electrical Earthing System"
            ]


    return detected


# ============================================================
# SECTION 2 — CO → PO/PSO
# ============================================================

def map_co_matrix(text):

    t = text.lower()

    baseline = {

        "CO1": [
            "1",
            "3",
            "-",
            "1",
            "1",
            "3",
            "2",
            "2",
            "2",
            "-",
            "1",
            "1",
            "-",
            "1",
        ],

        "CO2": [
            "3",
            "2",
            "2",
            "1",
            "3",
            "2",
            "1",
            "1",
            "1",
            "-",
            "1",
            "3",
            "2",
            "2",
        ],

        "CO3": [
            "2",
            "3",
            "2",
            "3",
            "2",
            "2",
            "-",
            "1",
            "1",
            "1",
            "2",
            "2",
            "2",
            "1",
        ],

        "CO4": [
            "-",
            "1",
            "1",
            "-",
            "1",
            "3",
            "3",
            "3",
            "3",
            "1",
            "2",
            "1",
            "1",
            "1",
        ],

        "CO5": [
            "1",
            "2",
            "1",
            "1",
            "2",
            "1",
            "1",
            "2",
            "3",
            "2",
            "3",
            "1",
            "1",
            "1",
        ],
    }


    matrix = []


    for co, _, _ in COS:

        matrix.append(
            list(
                baseline[co]
            )
        )


    return matrix


# ============================================================
# SECTION 4 — STRICT PROJECT COMPONENT → SDG MAPPING
# ============================================================

def map_sdg_components(
    components,
    text,
):

    rows = []


    for component in components:

        vals = {}


        # ----------------------------------------------------
        # Electrical Safety and Shock Prevention
        # ----------------------------------------------------

        if component == "Electrical Safety and Shock Prevention":

            vals[3] = "3"
            vals[9] = "2"
            vals[11] = "3"


        # ----------------------------------------------------
        # Electrical Earthing Awareness
        # ----------------------------------------------------

        elif component == "Electrical Earthing Awareness":

            vals[3] = "3"
            vals[9] = "2"
            vals[11] = "3"


        # ----------------------------------------------------
        # Household Electrical Wiring and Earthing
        # ----------------------------------------------------

        elif component == "Household Electrical Wiring and Earthing":

            vals[3] = "3"
            vals[9] = "3"
            vals[11] = "3"


        # ----------------------------------------------------
        # Agricultural Electrical Installations
        # ----------------------------------------------------

        elif component == "Agricultural Electrical Installations and Pump-Set Earthing":

            vals[3] = "3"
            vals[9] = "3"
            vals[11] = "2"


        # ----------------------------------------------------
        # Earthing Installation and Maintenance
        # ----------------------------------------------------

        elif component == "Earthing Installation and Maintenance":

            vals[3] = "3"
            vals[9] = "3"
            vals[11] = "2"


        # ----------------------------------------------------
        # Fault Protection and Protective Devices
        # ----------------------------------------------------

        elif component == "Fault Protection and Protective Devices":

            vals[3] = "3"
            vals[9] = "3"
            vals[11] = "3"


        # ----------------------------------------------------
        # Earth Resistance Testing
        # ----------------------------------------------------

        elif component == "Earth Resistance Testing":

            vals[3] = "3"
            vals[9] = "3"
            vals[11] = "2"


        # ----------------------------------------------------
        # Safe Electrical Wiring Practices
        # ----------------------------------------------------

        elif component == "Safe Electrical Wiring Practices":

            vals[3] = "3"
            vals[9] = "2"
            vals[11] = "3"


        # ----------------------------------------------------
        # Fallback
        # ----------------------------------------------------

        elif component == "Electrical Earthing System":

            vals[3] = "3"
            vals[9] = "3"
            vals[11] = "3"


        if vals:

            rows.append(
                (
                    component,
                    vals
                )
            )


    return rows


# ============================================================
# FIND COMMON SDGs
#
# AN SDG IS DISPLAYED ONLY WHEN EVERY COMPONENT MAPS TO IT.
# ============================================================

def get_common_sdgs(sdg_rows):

    if not sdg_rows:

        return []


    common_sdgs = []


    for sdg_number in range(1, 18):

        mapped_by_every_component = all(

            vals.get(sdg_number)
            in {"1", "2", "3"}

            for _, vals in sdg_rows
        )


        if mapped_by_every_component:

            common_sdgs.append(
                sdg_number
            )


    return common_sdgs


# ============================================================
# VALIDATE FINAL SECTION 4 MATRIX
#
# MINIMUM 3 COMMON SDGs REQUIRED.
# ============================================================

def get_valid_sdg_rows(sdg_rows):

    if not sdg_rows:

        return [], []


    common_sdgs = get_common_sdgs(
        sdg_rows
    )


    # --------------------------------------------------------
    # Minimum 3 common SDGs.
    # --------------------------------------------------------

    if len(common_sdgs) < 3:

        return [], []


    valid_rows = []


    for component, vals in sdg_rows:

        if all(
            vals.get(sdg)
            in {"1", "2", "3"}
            for sdg in common_sdgs
        ):

            valid_rows.append(
                (
                    component,
                    vals
                )
            )


    # --------------------------------------------------------
    # Every detected component must participate.
    # --------------------------------------------------------

    if len(valid_rows) != len(sdg_rows):

        return [], []


    return (
        valid_rows,
        common_sdgs
    )


# ============================================================
# REPORTLAB PARAGRAPH HELPER
# ============================================================

def P(
    txt,
    style,
):

    return Paragraph(
        str(txt),
        style
    )


# ============================================================
# BUILD FINAL PDF
#
# IMPORTANT:
# NO BORDER
# NO PAGE NUMBER
# NO DEPARTMENT FOOTER
# ============================================================

def build_pdf(
    project_title,
    co_matrix,
    components,
    sdg_rows,
):

    buf = io.BytesIO()


    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )


    styles = getSampleStyleSheet()


    title = ParagraphStyle(
        "title",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=15,
        leading=18,
        spaceAfter=8,
    )


    h = ParagraphStyle(
        "h",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=6,
        spaceAfter=6,
    )


    body = ParagraphStyle(
        "body",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=11,
    )


    small = ParagraphStyle(
        "small",
        parent=body,
        fontSize=7,
        leading=9,
    )


    story = []


    # ========================================================
    # TITLE
    # ========================================================

    story.append(
        P(
            "CO-PO-PSO & WK-PO-PSO Mapping",
            title
        )
    )


    story.append(
        Spacer(
            1,
            4
        )
    )


    # ========================================================
    # SECTION 1
    # ========================================================

    story.append(
        P(
            "1) Course Outcomes:",
            h
        )
    )


    story.append(
        P(
            "On successful completion of the Community Service Project, the student will be able to:",
            body
        )
    )


    data = [
        [
            P("CO No.", small),
            P("Course Outcome", small),
            P("Bloom's Level", small),
        ]
    ]


    for co, desc, bloom in COS:

        data.append(
            [
                P(co, small),
                P(desc, small),
                P(bloom, small),
            ]
        )


    tbl = Table(
        data,
        colWidths=[
            18 * mm,
            126 * mm,
            35 * mm,
        ],
        repeatRows=1,
    )


    tbl.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.black,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.whitesmoke,
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
                    (-1, 0),
                    "CENTER",
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )


    story.append(tbl)


    story.append(
        Spacer(
            1,
            8
        )
    )


    # ========================================================
    # SECTION 2
    # ========================================================

    story.append(
        P(
            "2) COs Vs POs and PSOs:",
            h
        )
    )


    data = [
        [P("CO", small)]
        + [
            P(x, small)
            for x in HEADERS
        ]
    ]


    for (co, _, _), row in zip(
        COS,
        co_matrix,
    ):

        data.append(
            [P(co, small)]
            + [
                P(x, small)
                for x in row
            ]
        )


    tbl = Table(
        data,
        colWidths=[
            14 * mm
        ]
        + [
            12.2 * mm
        ] * 14,
        repeatRows=1,
    )


    tbl.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.black,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.whitesmoke,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )


    story.append(tbl)


    story.append(
        Spacer(
            1,
            5
        )
    )


    story.append(
        P(
            "Scale: 3 = High    2 = Medium    1 = Low    - = No mapping",
            small
        )
    )


    story.append(
        PageBreak()
    )


    # ========================================================
    # SECTION 3
    # ========================================================

    story.append(
        P(
            "3) Knowledge and Attitude Profile Vs Program Outcomes and Program Specific Outcomes",
            h
        )
    )


    data = [
        [P("", small)]
        + [
            P(x, small)
            for x in HEADERS
        ]
    ]


    for (wk, _), row in zip(
        WKS,
        FIXED_WK_MATRIX,
    ):

        data.append(
            [P(wk, small)]
            + [
                P(x, small)
                for x in row
            ]
        )


    tbl = Table(
        data,
        colWidths=[
            15 * mm
        ]
        + [
            12.1 * mm
        ] * 14,
        repeatRows=1,
    )


    tbl.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.black,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.whitesmoke,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )


    story.append(tbl)


    story.append(
        Spacer(
            1,
            5
        )
    )


    story.append(
        P(
            "Scale: 3 = High    2 = Medium    1 = Low",
            small
        )
    )


    story.append(
        PageBreak()
    )


    # ========================================================
    # SECTION 4
    # ========================================================

    story.append(
        P(
            "4) SDGs Vs Community Service Project Components:",
            h
        )
    )


    story.append(
        Spacer(
            1,
            5
        )
    )


    # --------------------------------------------------------
    # STRICT COMMON SDG CALCULATION
    # --------------------------------------------------------

    valid_sdg_rows, matched_sdgs = get_valid_sdg_rows(
        sdg_rows
    )


    # --------------------------------------------------------
    # FINAL SECTION 4 TABLE
    # --------------------------------------------------------

    if valid_sdg_rows and matched_sdgs:

        data = [
            [
                P(
                    "Project Component",
                    small
                )
            ]
            + [
                P(
                    f"SDG {n}",
                    small
                )
                for n in matched_sdgs
            ]
        ]


        # ----------------------------------------------------
        # Every cell contains 1 / 2 / 3.
        # No "-" and no blank cells.
        # ----------------------------------------------------

        for component, vals in valid_sdg_rows:

            row = [
                P(
                    component,
                    small
                )
            ]


            for n in matched_sdgs:

                row.append(
                    P(
                        vals[n],
                        small
                    )
                )


            data.append(
                row
            )


        # ----------------------------------------------------
        # TABLE WIDTH
        # ----------------------------------------------------

        component_width = 68 * mm

        available_width = (
            A4[0] - 24 * mm
        )

        remaining_width = (
            available_width
            - component_width
        )

        sdg_width = (
            remaining_width
            / len(matched_sdgs)
        )


        tbl = Table(
            data,
            colWidths=[
                component_width
            ]
            + [
                sdg_width
            ] * len(matched_sdgs),
            repeatRows=1,
        )


        tbl.setStyle(
            TableStyle(
                [
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.black,
                    ),
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.whitesmoke,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (-1, -1),
                        "CENTER",
                    ),
                    (
                        "ALIGN",
                        (0, 1),
                        (0, -1),
                        "LEFT",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                ]
            )
        )


        story.append(tbl)


        story.append(
            Spacer(
                1,
                6
            )
        )


        story.append(
            P(
                "Mapping scale: 3 = High    2 = Medium    1 = Low",
                small
            )
        )


    else:

        story.append(
            P(
                "No minimum three common SDG mappings were identified across all project components.",
                body
            )
        )


    # ========================================================
    # BUILD PDF
    #
    # NO onFirstPage
    # NO onLaterPages
    # NO BORDER
    # NO PAGE NUMBER
    # NO FOOTER
    # ========================================================

    doc.build(
        story
    )


    buf.seek(0)

    return buf.getvalue()


# ============================================================
# STREAMLIT UI
# ============================================================

st.title(
    "📘 CSP Outcome Mapping Generator"
)


st.caption(
    "Upload one Community Service Project book → "
    "extract evidence → generate Sections 1–4 as a PDF."
)


# ============================================================
# FILE UPLOAD
# ============================================================

uploaded = st.file_uploader(
    "Upload your CSP Project Book (PDF)",
    type=["pdf"],
)


# ============================================================
# MAIN PROCESS
# ============================================================

if uploaded:

    text = extract_text(
        uploaded
    )


    if not text.strip():

        st.error(
            "No selectable text was found. "
            "This version needs a text-readable PDF."
        )

        st.stop()


    cleaned = clean_text(
        text
    )


    # ========================================================
    # PROJECT TITLE
    # ========================================================

    project_title = extract_title(
        text
    )


    # ========================================================
    # PROJECT COMPONENTS
    # ========================================================

    components = detect_components(
        text
    )


    # ========================================================
    # SECTION 2
    # ========================================================

    co_matrix = map_co_matrix(
        cleaned
    )


    # ========================================================
    # SECTION 4
    # ========================================================

    sdg_rows = map_sdg_components(
        components,
        cleaned
    )


    st.success(
        f"Project book extracted successfully. "
        f"Detected {len(text):,} characters."
    )


    # ========================================================
    # EXTRACTED INFORMATION
    # ========================================================

    with st.expander(
        "🔎 Extracted project information",
        expanded=False,
    ):

        st.write(
            f"**Detected title:** {project_title}"
        )


        st.write(
            "**Detected relevant project components:**"
        )


        if components:

            for component in components:

                st.write(
                    f"- {component}"
                )

        else:

            st.write(
                "No specific project components detected."
            )


        st.text_area(
            "Extracted text preview",
            text[:8000],
            height=250,
        )


    # ========================================================
    # COMPONENT EDITOR
    # ========================================================

    st.subheader(
        "Project components used for Section 4"
    )


    edited = st.text_area(
        "Only relevant project-specific components should be kept. One component per line.",
        "\n".join(components),
        height=180,
    )


    components = [
        x.strip()
        for x in edited.splitlines()
        if x.strip()
    ]


    # Recalculate Section 4
    sdg_rows = map_sdg_components(
        components,
        cleaned
    )


    # ========================================================
    # SECTION 2 PREVIEW
    # ========================================================

    st.subheader(
        "Section 2 — CO → PO/PSO mapping"
    )


    section2_data = {
        "CO": [
            co[0]
            for co in COS
        ]
    }


    for i, header in enumerate(
        HEADERS
    ):

        section2_data[header] = [
            co_matrix[row][i]
            for row in range(5)
        ]


    st.dataframe(
        pd.DataFrame(
            section2_data
        ),
        use_container_width=True,
        hide_index=True,
    )


    # ========================================================
    # SECTION 4 PREVIEW
    #
    # SAME STRICT RULE AS PDF
    # ========================================================

    st.subheader(
        "Section 4 — Project Components → SDGs"
    )


    valid_sdg_rows, preview_sdgs = get_valid_sdg_rows(
        sdg_rows
    )


    if valid_sdg_rows and preview_sdgs:

        preview_rows = []


        for component, vals in valid_sdg_rows:

            row = {
                "Project Component": component
            }


            for n in preview_sdgs:

                row[
                    f"SDG {n}"
                ] = vals[n]


            preview_rows.append(
                row
            )


        # Explicit column names prevent the old
        # 0, 1, 2, 3, 4 problem.

        df_preview = pd.DataFrame(
            preview_rows,
            columns=[
                "Project Component"
            ]
            + [
                f"SDG {n}"
                for n in preview_sdgs
            ]
        )


        st.dataframe(
            df_preview,
            use_container_width=True,
            hide_index=True,
        )


        st.caption(
            "Only SDGs mapped by EVERY project component are displayed."
        )


    else:

        st.warning(
            "At least 3 common SDGs mapped by every project component are required."
        )


    # ========================================================
    # GENERATE FINAL PDF
    # ========================================================

    if st.button(
        "📄 Generate Final CSP PDF",
        type="primary",
    ):

        try:

            pdf = build_pdf(
                project_title,
                co_matrix,
                components,
                sdg_rows,
            )


            st.success(
                "Final CSP PDF generated successfully."
            )


            st.download_button(
                label="⬇️ Download Final PDF",
                data=pdf,
                file_name="CSP_CO_PO_PSO_WK_SDG_Mapping.pdf",
                mime="application/pdf",
                key="download_final_csp_pdf",
            )


        except Exception as e:

            st.error(
                f"PDF generation failed: {e}"
            )


# ============================================================
# INITIAL SCREEN
# ============================================================

else:

    st.info(
        "Start by uploading your CSP project book PDF."
    )
