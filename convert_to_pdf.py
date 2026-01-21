"""
PDF Converter for ASHA AI Project Report
Converts markdown report to PDF using markdown2 and weasyprint
"""

import markdown
from weasyprint import HTML, CSS
from pathlib import Path

def convert_markdown_to_pdf(markdown_file, pdf_file):
    """Convert markdown file to PDF with styling"""
    
    # Read markdown content
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(
        markdown_content,
        extensions=['tables', 'fenced_code', 'codehilite']
    )
    
    # Add CSS styling for professional appearance
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 2cm;
                @top-center {{
                    content: "ASHA AI Project Report";
                    font-size: 10pt;
                    color: #666;
                }}
                @bottom-center {{
                    content: counter(page);
                    font-size: 10pt;
                }}
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
            }}
            
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-top: 30px;
                page-break-before: always;
            }}
            
            h1:first-of-type {{
                page-break-before: avoid;
                font-size: 2.5em;
                text-align: center;
                border-bottom: none;
            }}
            
            h2 {{
                color: #34495e;
                margin-top: 25px;
                border-left: 4px solid #3498db;
                padding-left: 15px;
            }}
            
            h3 {{
                color: #7f8c8d;
                margin-top: 20px;
            }}
            
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                font-size: 0.9em;
            }}
            
            th {{
                background-color: #3498db;
                color: white;
                padding: 12px;
                text-align: left;
            }}
            
            td {{
                border: 1px solid #ddd;
                padding: 10px;
            }}
            
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            
            code {{
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
            }}
            
            pre {{
                background-color: #2c3e50;
                color: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
                page-break-inside: avoid;
            }}
            
            pre code {{
                background-color: transparent;
                color: #ecf0f1;
                padding: 0;
            }}
            
            blockquote {{
                border-left: 4px solid #3498db;
                margin: 20px 0;
                padding-left: 20px;
                font-style: italic;
                color: #555;
            }}
            
            ul, ol {{
                margin: 15px 0;
                padding-left: 30px;
            }}
            
            li {{
                margin: 8px 0;
            }}
            
            .toc {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin: 30px 0;
            }}
            
            hr {{
                border: none;
                border-top: 2px solid #ecf0f1;
                margin: 30px 0;
            }}
            
            strong {{
                color: #2c3e50;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Convert HTML to PDF
    HTML(string=styled_html).write_pdf(pdf_file)
    print(f"✅ PDF created successfully: {pdf_file}")

if __name__ == "__main__":
    markdown_file = Path("ASHA_AI_Project_Report.md")
    pdf_file = Path("ASHA_AI_Project_Report.pdf")
    
    try:
        convert_markdown_to_pdf(markdown_file, pdf_file)
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\\nTrying alternative method...")
        
        # Fallback: Simple HTML to PDF
        import markdown as md
        
        with open(markdown_file, 'r', encoding='utf-8') as f:
            html = md.markdown(f.read(), extensions=['tables'])
        
        with open("ASHA_AI_Project_Report.html", 'w', encoding='utf-8') as f:
            f.write(f"<html><body style='font-family:Arial; max-width:800px; margin:auto;'>{html}</body></html>")
        
        print("✅ HTML version created: ASHA_AI_Project_Report.html")
        print("Please use your browser to print this as PDF (Ctrl+P)")
