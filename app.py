import io
import re

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
# FIXED MASTER DATA
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
# FIXED SECTION 3 MATRIX
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
# TEXT EXTRACTION
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


def clean_text(text):

    text = text or ""

    text = text.replace(
        "\xa0",
        " ",
    )

    text = text.replace(
        "&nbsp;",
        " ",
    )

    text = text.replace(
        "&amp;",
        "&",
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# HELPER FUNCTIONS
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


def max_level(a, b):

    order = {
        "-": 0,
        "1": 1,
        "2": 2,
        "3": 3,
    }

    if order[str(b)] > order[str(a)]:
        return b

    return a


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
# COMPONENT DETECTION
# ============================================================

def detect_components(text):

    t = text.lower()

    candidates = [

        (
            "Community survey / household survey",
            [
                "survey",
                "household survey",
                "questionnaire",
                "respondent",
                "residents",
                "data collection",
            ],
        ),

        (
            "Electrical wiring and safety assessment",
            [
                "electrical wiring",
                "wiring inspection",
                "wiring assessment",
                "loose connection",
                "damaged wire",
                "electrical shock",
                "short circuit",
            ],
        ),

        (
            "Earthing / grounding assessment",
            [
                "earthing",
                "grounding",
                "earth electrode",
                "earth pit",
                "earth resistance",
                "pipe earthing",
            ],
        ),

        (
            "Awareness session / demonstration",
            [
                "awareness programme",
                "awareness program",
                "awareness session",
                "demonstration",
                "seminar",
                "explained",
                "educated",
                "training",
            ],
        ),

        (
            "Community interaction",
            [
                "community interaction",
                "interaction with residents",
                "interaction with villagers",
                "interaction with farmers",
                "meeting with residents",
                "meeting with villagers",
            ],
        ),

        (
            "Survey data analysis / charts",
            [
                "survey data analysis",
                "data analysis",
                "percentage analysis",
                "graph",
                "graphs",
                "chart",
                "charts",
                "statistical analysis",
            ],
        ),

        (
            "Protective devices / electrical protection",
            [
                "mcb",
                "rcd",
                "elcb",
                "fuse",
                "protective device",
                "electrical protection",
            ],
        ),

        (
            "Energy conservation / efficient use",
            [
                "energy saving",
                "energy conservation",
                "efficient use of electricity",
                "electricity consumption",
                "energy efficiency",
            ],
        ),

        (
            "Environmental / sustainability activity",
            [
                "environmental activity",
                "environment protection",
                "sustainability activity",
                "renewable energy",
                "solar energy",
            ],
        ),

        (
            "Report / documentation",
            [
                "project report",
                "technical report",
                "documentation",
                "presentation",
                "seminar presentation",
            ],
        ),
    ]

    found = []

    for label, keywords in candidates:

        if contains_any(
            t,
            keywords,
        ):
            found.append(label)

    if not found:

        found = [
            "Community survey / field observation",
            "Community interaction",
            "Awareness / service activity",
            "Survey findings and documentation",
        ]

    return found


# ============================================================
# SECTION 2
# ACCURATE AND MORE COMPLETE CO → PO/PSO MAPPING
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

    community_evidence = [
        "community",
        "villagers",
        "residents",
        "farmers",
        "households",
        "survey",
        "field visit",
        "field observation",
        "interaction",
        "questionnaire",
        "respondent",
    ]

    problem_evidence = [
        "problem",
        "issue",
        "need",
        "challenge",
        "difficulty",
        "existing condition",
        "existing practice",
        "deficiency",
        "requirement",
    ]

    safety_evidence = [
        "safety",
        "electrical safety",
        "shock",
        "hazard",
        "short circuit",
        "fire",
        "loose connection",
        "damaged wire",
        "earthing",
        "grounding",
        "mcb",
        "fuse",
        "protective device",
    ]

    electrical_evidence = [
        "electrical",
        "electricity",
        "voltage",
        "current",
        "power",
        "wiring",
        "earthing",
        "grounding",
        "transformer",
        "motor",
        "electrical load",
        "mcb",
        "fuse",
        "rcd",
        "elcb",
    ]

    analysis_evidence = [
        "analysis",
        "analyzed",
        "analyse",
        "analyze",
        "findings",
        "comparison",
        "percentage",
        "calculation",
        "data analysis",
        "survey results",
        "results",
        "observations",
    ]

    data_evidence = [
        "data collection",
        "data analysis",
        "survey data",
        "questionnaire",
        "respondents",
        "percentage",
        "table",
        "graph",
        "chart",
        "statistical",
        "results",
    ]

    design_evidence = [
        "designed",
        "design",
        "developed",
        "development",
        "prototype",
        "circuit design",
        "system design",
        "model developed",
        "fabricated",
        "implemented",
        "installation design",
    ]

    tool_evidence = [
        "matlab",
        "python",
        "simulation",
        "simulink",
        "multimeter",
        "clamp meter",
        "megger",
        "earth tester",
        "measurement instrument",
        "software tool",
        "computer tool",
        "cad",
        "simulation software",
    ]

    sustainability_evidence = [
        "sustainable",
        "sustainability",
        "renewable",
        "solar",
        "energy conservation",
        "energy efficiency",
        "environment",
        "environmental impact",
        "energy saving",
    ]

    ethics_evidence = [
        "ethical",
        "ethics",
        "professional ethics",
        "responsibility",
        "responsible",
        "permission",
        "consent",
        "respect",
        "privacy",
        "confidentiality",
        "inclusive",
    ]

    teamwork_evidence = [
        "team",
        "team members",
        "group",
        "collaborated",
        "collaboration",
        "jointly",
        "members",
        "leader",
        "leadership",
    ]

    communication_evidence = [
        "awareness",
        "explained",
        "educated",
        "communication",
        "presentation",
        "seminar",
        "interaction",
        "discussion",
        "questionnaire",
        "report",
    ]

    management_evidence = [
        "project management",
        "planning",
        "schedule",
        "scheduling",
        "budget",
        "cost estimation",
        "finance",
        "financial",
        "resource management",
        "resource allocation",
        "procurement",
        "time management",
        "work plan",
    ]

    learning_evidence = [
        "learning",
        "learnt",
        "learned",
        "new technology",
        "new technique",
        "skill development",
        "knowledge gained",
        "future learning",
        "self learning",
        "lifelong learning",
    ]

    pso1_evidence = [
        "electrical machine",
        "motor",
        "generator",
        "transformer",
        "control system",
        "instrumentation",
        "power system",
        "power electronic",
        "power electronics",
    ]

    pso2_evidence = [
        "designed",
        "design",
        "developed",
        "development",
        "prototype",
        "circuit design",
        "system design",
        "implemented",
        "fabricated",
        "electrical project",
        "electronics project",
    ]

    pso3_evidence = [
        "smart grid",
        "power quality",
        "advanced protection",
        "control engineering",
        "sustainable technology",
        "renewable technology",
        "solar technology",
        "energy efficiency",
        "modern technique",
    ]

    def set_score(row, index, value):

        current = row[index]

        order = {
            "-": 0,
            "1": 1,
            "2": 2,
            "3": 3,
        }

        if order[str(value)] > order[str(current)]:
            row[index] = value

    matrix = []

    for co, _, _ in COS:

        row = list(
            baseline[co]
        )

        if co == "CO1":

            if contains_any(
                t,
                community_evidence,
            ):

                set_score(row, 1, "3")
                set_score(row, 5, "3")
                set_score(row, 8, "2")

            if contains_any(
                t,
                problem_evidence,
            ):

                set_score(row, 1, "3")

            if contains_any(
                t,
                safety_evidence,
            ):

                set_score(row, 5, "3")
                set_score(row, 6, "2")

            if contains_any(
                t,
                electrical_evidence,
            ):

                set_score(row, 0, "2")
                set_score(row, 11, "2")

        elif co == "CO2":

            electrical_strength = count_matches(
                t,
                electrical_evidence,
            )

            if electrical_strength >= 1:

                set_score(row, 0, "3")
                set_score(row, 1, "2")
                set_score(row, 4, "3")

            if electrical_strength >= 3:

                set_score(row, 11, "3")

            if contains_any(
                t,
                design_evidence,
            ):

                set_score(row, 2, "3")
                set_score(row, 12, "2")

            if contains_any(
                t,
                tool_evidence,
            ):

                set_score(row, 4, "3")

            if contains_any(
                t,
                sustainability_evidence,
            ):

                set_score(row, 5, "2")
                set_score(row, 13, "2")

        elif co == "CO3":

            if contains_any(
                t,
                problem_evidence,
            ):

                set_score(row, 1, "3")

            if contains_any(
                t,
                analysis_evidence,
            ):

                set_score(row, 1, "3")
                set_score(row, 3, "3")

            if contains_any(
                t,
                data_evidence,
            ):

                set_score(row, 3, "3")
                set_score(row, 4, "2")

            if contains_any(
                t,
                design_evidence,
            ):

                set_score(row, 2, "3")
                set_score(row, 12, "2")

            if contains_any(
                t,
                tool_evidence,
            ):

                set_score(row, 4, "3")

            if contains_any(
                t,
                sustainability_evidence,
            ):

                set_score(row, 5, "2")
                set_score(row, 13, "2")

            if contains_any(
                t,
                pso1_evidence,
            ):

                set_score(row, 11, "3")

        elif co == "CO4":

            if contains_any(
                t,
                community_evidence,
            ):

                set_score(row, 5, "3")

            if contains_any(
                t,
                ethics_evidence,
            ):

                set_score(row, 6, "3")

            if contains_any(
                t,
                teamwork_evidence,
            ):

                set_score(row, 7, "3")
                set_score(row, 9, "2")

            if contains_any(
                t,
                communication_evidence,
            ):

                set_score(row, 8, "3")

            if contains_any(
                t,
                safety_evidence,
            ):

                set_score(row, 5, "3")

            if (
                contains_any(
                    t,
                    communication_evidence,
                )
                and contains_any(
                    t,
                    community_evidence,
                )
            ):

                set_score(row, 8, "3")

        elif co == "CO5":

            report_evidence = [
                "project report",
                "technical report",
                "report preparation",
                "documentation",
                "documentation of activities",
            ]

            presentation_evidence = [
                "presentation",
                "seminar",
                "ppt",
                "powerpoint",
                "oral presentation",
            ]

            if contains_any(
                t,
                report_evidence,
            ):

                set_score(row, 8, "3")
                set_score(row, 4, "2")

            if contains_any(
                t,
                presentation_evidence,
            ):

                set_score(row, 8, "3")

            if contains_any(
                t,
                data_evidence,
            ):

                set_score(row, 3, "2")

            if contains_any(
                t,
                management_evidence,
            ):

                set_score(row, 9, "3")

            if contains_any(
                t,
                learning_evidence,
            ):

                set_score(row, 10, "3")

            if contains_any(
                t,
                design_evidence,
            ):

                set_score(row, 12, "2")

            if contains_any(
                t,
                pso3_evidence,
            ):

                set_score(row, 13, "2")

        matrix.append(row)

    return matrix


# ============================================================
# SECTION 4
# PROJECT COMPONENT → SDG MAPPING
# ============================================================

def map_sdg_components(components, text):

    t = text.lower()

    rows = []

    for component in components:

        c = component.lower()

        vals = {
            n: "-"
            for n in range(1, 18)
        }

        # ----------------------------------------------------
        # SDG 4 — Education
        # ----------------------------------------------------

        education = [
            "awareness",
            "education",
            "training",
            "demonstration",
            "seminar",
            "explained",
            "educated",
        ]

        if contains_any(
            c,
            education,
        ):

            vals[4] = "3"

        # ----------------------------------------------------
        # SDG 3 — Health / safety
        # ----------------------------------------------------

        safety = [
            "safety",
            "wiring",
            "earthing",
            "grounding",
            "protective",
            "electrical protection",
        ]

        if contains_any(
            c,
            safety,
        ):

            vals[3] = "2"

        # ----------------------------------------------------
        # SDG 7 — Energy
        # ----------------------------------------------------

        energy = [
            "energy",
            "electricity",
            "solar",
            "renewable",
            "power",
        ]

        if contains_any(
            c,
            energy,
        ):

            vals[7] = "3"

        # ----------------------------------------------------
        # SDG 9 — Infrastructure / innovation
        # ----------------------------------------------------

        infrastructure = [
            "wiring",
            "earthing",
            "grounding",
            "protective devices",
            "electrical protection",
            "design",
            "prototype",
            "system",
        ]

        if contains_any(
            c,
            infrastructure,
        ):

            vals[9] = "2"

        # ----------------------------------------------------
        # SDG 11 — Safe communities
        # ----------------------------------------------------

        if contains_any(
            c,
            [
                "community",
                "survey",
                "safety",
                "wiring",
                "earthing",
                "grounding",
                "protective",
            ],
        ):

            vals[11] = "2"

        # ----------------------------------------------------
        # SDG 12 — Responsible consumption
        # ----------------------------------------------------

        if contains_any(
            c,
            [
                "energy conservation",
                "efficient use",
                "energy efficiency",
                "energy saving",
            ],
        ):

            vals[12] = "3"

        # ----------------------------------------------------
        # SDG 13 — Climate action
        # ----------------------------------------------------

        if contains_any(
            c,
            [
                "solar",
                "renewable",
                "energy efficiency",
                "energy conservation",
                "environment",
                "sustainability",
            ],
        ):

            vals[13] = "2"

        # ----------------------------------------------------
        # SDG 15 — Terrestrial ecosystems
        # ----------------------------------------------------

        if contains_any(
            c,
            [
                "environmental activity",
                "environment protection",
                "ecosystem",
                "tree plantation",
                "biodiversity",
            ],
        ):

            vals[15] = "2"

        # ----------------------------------------------------
        # SDG 16 — Peaceful/inclusive institutions
        # ----------------------------------------------------

        if contains_any(
            c,
            [
                "community interaction",
                "village meeting",
                "public meeting",
            ],
        ):

            vals[16] = "1"

        # ----------------------------------------------------
        # Additional evidence from full project text
        # ----------------------------------------------------

        if "survey" in c:

            if contains_any(
                t,
                [
                    "data analysis",
                    "survey analysis",
                    "percentage",
                    "survey results",
                ],
            ):

                vals[4] = max_level(
                    vals[4],
                    "2",
                )

        rows.append(
            (
                component,
                vals,
            )
        )

    return rows


# ============================================================
# PDF TEXT HELPER
# ============================================================

def P(txt, style):

    text = str(txt)

    text = text.replace(
        "&nbsp;",
        " ",
    )

    text = text.replace(
        "&",
        "&amp;",
    )

    text = text.replace(
        "&lt;b&gt;",
        "<b>",
    )

    text = text.replace(
        "&lt;/b&gt;",
        "</b>",
    )

    return Paragraph(
        text,
        style,
    )


# ============================================================
# BUILD PDF
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
            title,
        )
    )

    # ========================================================
    # REMOVED:
    #
    # story.append(
    #     P(
    #         "COMMUNITY SERVICE PROJECT",
    #         title,
    #     )
    # )
    #
    # ========================================================

    story.append(
        Spacer(
            1,
            4,
        )
    )

    # ========================================================
    # SECTION 1
    # ========================================================

    story.append(
        P(
            "1) Course Outcomes:",
            h,
        )
    )

    story.append(
        P(
            "On successful completion of the Community Service Project, the student will be able to:",
            body,
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
            8,
        )
    )

    # ========================================================
    # SECTION 2
    # ========================================================

    story.append(
        P(
            "2) COs Vs POs and PSOs:",
            h,
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
            5,
        )
    )

    story.append(
        P(
            "Scale: 3 = High    2 = Medium    1 = Low    - = No mapping",
            small,
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
            h,
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
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
            ]
        )
    )

    story.append(tbl)

    story.append(
        Spacer(
            1,
            5,
        )
    )

    story.append(
        P(
            "Scale: 3 = High    2 = Medium    1 = Low",
            small,
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
            h,
        )
    )

    # ========================================================
    # REMOVED:
    #
    # story.append(
    #     P(
    #         f"<b>Community Service Project:</b> {project_title}",
    #         body,
    #     )
    # )
    #
    # ========================================================

    story.append(
        Spacer(
            1,
            5,
        )
    )

    matched_sdgs = []

    for n in range(1, 18):

        if any(
            vals.get(n, "-")
            in {"1", "2", "3"}
            for _, vals in sdg_rows
        ):

            matched_sdgs.append(n)

    if not matched_sdgs:

        story.append(
            P(
                "No SDG mapping was supported by sufficient project evidence.",
                body,
            )
        )

    else:

        data = [
            [
                P(
                    "Project Components",
                    small,
                )
            ]
            + [
                P(
                    f"SDG {n}",
                    small,
                )
                for n in matched_sdgs
            ]
        ]

        for component, vals in sdg_rows:

            data.append(
                [
                    P(
                        component,
                        small,
                    )
                ]
                + [
                    P(
                        vals.get(n, "-"),
                        small,
                    )
                    for n in matched_sdgs
                ]
            )

        component_width = 62 * mm

        available_width = (
            A4[0]
            - 24 * mm
        )

        remaining = (
            available_width
            - component_width
        )

        sdg_width = (
            remaining
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
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "ALIGN",
                        (1, 1),
                        (-1, -1),
                        "CENTER",
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
                        7,
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
                6,
            )
        )

        story.append(
            P(
                "Mapping scale: 3 = High    2 = Medium    1 = Low    - = No contribution",
                small,
            )
        )

    # ========================================================
    # BUILD DOCUMENT
    # ========================================================

    doc.build(story)

    buf.seek(0)

    return buf.getvalue()


# ============================================================
# USER INTERFACE
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

    text = extract_text(uploaded)

    if not text.strip():

        st.error(
            "No selectable text was found. "
            "This version needs a text-readable PDF."
        )

        st.stop()

    cleaned = clean_text(text)

    project_title = extract_title(
        text
    )

    components = detect_components(
        text
    )

    co_matrix = map_co_matrix(
        cleaned
    )

    sdg_rows = map_sdg_components(
        components,
        cleaned,
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
            f"**Detected components:** "
            f"{', '.join(components)}"
        )

        st.text_area(
            "Extracted text preview",
            text[:8000],
            height=250,
        )

    # ========================================================
    # COMPONENT EDITING
    # ========================================================

    st.subheader(
        "Project components used for Section 4"
    )

    edited = st.text_area(
        "One component per line. You may correct/add components before generating.",
        "\n".join(components),
        height=180,
    )

    components = [
        x.strip()
        for x in edited.splitlines()
        if x.strip()
    ]

    sdg_rows = map_sdg_components(
        components,
        cleaned,
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
        section2_data,
        use_container_width=True,
        hide_index=True,
    )

    # ========================================================
    # SECTION 4 PREVIEW
    # ========================================================

    st.subheader(
        "Section 4 — Project Components → SDGs"
    )

    for component, vals in sdg_rows:

        selected = [
            (
                f"SDG {n}",
                value,
            )
            for n, value in vals.items()
            if value in {"1", "2", "3"}
        ]

        if selected:

            st.write(
                f"**{component}:** "
                + ", ".join(
                    f"{sdg}={value}"
                    for sdg, value in selected
                )
            )

        else:

            st.write(
                f"**{component}:** "
                "No contribution identified"
            )

    # ========================================================
    # GENERATE PDF
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

   
    