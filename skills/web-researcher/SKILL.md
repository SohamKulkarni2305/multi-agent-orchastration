---
name: web-researcher
description: Conducts deep web research on a specific topic and generates a comprehensive, structured Markdown report with citations.
---

# Web Researcher Skill

## Purpose
Acts as an autonomous research assistant. When given a topic or question, it performs web searches, reads documentation or articles, and synthesizes the findings into a highly structured Markdown report.

## Workflow

When the user asks you to "research [topic]" using this skill:

1. **Initial Search Strategy**: 
   - Identify the core keywords and concepts from the user's prompt.
   - Use the `search_web` tool to gather initial context.
   - For complex topics, break them down into 2-3 sub-queries and perform parallel searches.

2. **Deep Dive & Content Extraction**:
   - Identify the most credible URLs from the search results (prefer official docs, academic papers, or reputable tech blogs).
   - Use the `read_url_content` or `read_browser_page` tools to extract detailed information from those specific pages.
   - Take mental notes of key findings, statistics, and code examples.

3. **Report Generation**:
   - Synthesize the gathered information.
   - Create a new Markdown file (e.g., in an `artifacts/` or `research/` directory) containing the report.
   - The report MUST follow this structure:
     - **# [Topic Name]**
     - **Executive Summary**: A brief paragraph summarizing the core answer or finding.
     - **Key Concepts / Core Details**: Bullet points or sub-sections explaining the mechanics, history, or specifics.
     - **Examples / Code Snippets** (if applicable): Practical demonstrations of the topic.
     - **References**: A bulleted list of the URLs used to gather the information, formatted as markdown links.

4. **Completion**:
   - Notify the user that the research is complete and provide a link to the generated Markdown report.
