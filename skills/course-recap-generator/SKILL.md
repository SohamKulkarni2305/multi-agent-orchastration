---
name: course-recap-generator
description: Generates a verified course recap, mermaid diagram, and cover image from a file.
---

# Course Recap Generator

## Purpose
Takes a course document (PDF/DOC), extracts the text, creates a verified summary, and generates visual assets.

## Workflow

When invoked with a target file and an output JSON path (e.g. `--file <path> --output <output_json>`):

1. **Extraction & Summarization**: 
   - Extract the text from the provided file.
   - Summarize the text into a detailed Markdown document grouped logically by topics.

2. **Verification (Sub-Agent)**: 
   - Spawn a Reviewer sub-agent to cross-check your generated summary against the original extracted text.
   - Ensure no key concepts were missed. Refine the summary if the Reviewer suggests corrections.

3. **Diagram Generation**: 
   - Based on the verified summary, write a `Mermaid` flowchart (`graph TD;`) mapping the core concepts.

4. **Image Generation**: 
   - Generate a visually stunning abstract cover image URL representing the course (e.g., using a service like Pollinations.ai, or via Canva MCP if connected).

5. **Final Output**: 
   - Save the results to the requested `--output` file path. The file MUST contain ONLY a valid JSON object matching this exact schema:
   ```json
   {
     "markdown_summary": "# Course Recap\n...",
     "mermaid_code": "graph TD;\n...",
     "image_url": "https://..."
   }
   ```

6. **Completion**: Report to the user that the JSON file was successfully written.
