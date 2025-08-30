# Research Paper Analyzer

This project is a Streamlit application for parsing and analyzing scientific research papers. It extracts structured information from PDF files, including metadata, methods, results, and more, using a configurable LLM backend.

The tool also includes a post-processing pipeline to clean, enrich, and validate the extracted data.

## Features

- **PDF Parsing**: Extracts text and layout information from research papers.
- **Structured Extraction**: Uses LLMs (Gemini, OpenRouter/DeepSeek) to extract key information into a structured JSON format.
- **Streamlit UI**: An interactive web interface to upload papers and view results.
- **Post-processing**: A suite of scripts to improve data quality:
    - **Schema Hygiene**: Normalizes data types (e.g., ensures result values are floats).
    - **Confidence Scoring**: Computes a confidence score for each extracted result based on its provenance.
    - **Data Enrichment**: Automatically populates `tasks` and `datasets` fields if they are missing, based on the content of the paper.
    - **Summary Validation**: Calculates a "summary alignment" score that measures how well the generated summary is supported by evidence snippets from the paper.
- **Sidecar Metadata**: Exports internal metadata (`_meta`) into a separate `.meta.json` file to keep the primary output clean.

## How to Run

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up your environment:**
    Create a `.env` file in the root of the `research-paper-analyzer` directory and add your API keys:
    ```
    GEMINI_API_KEY="your_gemini_api_key"
    OPENROUTER_API_KEY="your_openrouter_api_key"
    ```

3.  **Run the Streamlit app:**
    ```bash
    streamlit run app/app.py
    ```

## Post-processing Scripts

To run the post-processing pipeline on an extracted JSON file:

```bash
python scripts/postprocess_paper.py path/to/your_paper.json
```

This will generate two new files:
- `your_paper.clean.json`: The main, cleaned-up data file.
- `your_paper.meta.json`: A sidecar file containing processing metadata.

To validate the summary of a cleaned file:

```bash
python scripts/validate_summary.py path/to/your_paper.clean.json
```
