# CSP Outcome Mapping Generator

A simple local Streamlit website for generating the Community Service Project CO/PO/PSO/WK/SDG mapping PDF.

## Run on your laptop

1. Install Python 3.10+.
2. Open Command Prompt/Terminal in this folder.
3. Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

4. The browser will open the website.
5. Upload the CSP Project Book PDF.
6. Review detected project components.
7. Click **Generate Final CSP PDF**.

## Structure

- Section 1: fixed CSP CO1–CO5
- Section 2: dynamic CO → PO/PSO mapping based on project evidence
- Section 3: fixed WK1–WK9 → PO/PSO matrix
- Section 4: dynamic project component → SDG mapping
- SDG1–SDG17: pre-installed

## Important

The current version uses transparent keyword/evidence rules, so it works without an API key. For higher-quality semantic mapping, an AI provider can be connected later.


## Latest PDF changes
- Section 2 uses a more conservative CSP-specific CO→PO/PSO mapping.
- Section 4 is a true component-by-SDG matrix.
- Only matched SDG columns are shown.
- Cells contain only 1, 2, 3, or -.
- SDG descriptions are not printed in the final PDF.
- Mapping scale text uses plain symbols only.
