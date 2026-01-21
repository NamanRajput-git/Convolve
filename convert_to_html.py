"""
Enhanced Markdown to HTML converter with Mermaid diagram support
"""

import markdown
from pathlib import Path
import re

def convert_to_html_with_diagrams():
    """Convert markdown report to styled HTML with Mermaid diagrams"""
    
    # Read markdown content
    markdown_file = Path("ASHA_AI_Project_Report.md")
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML
    html_body = markdown.markdown(
        markdown_content,
        extensions=['tables', 'fenced_code', 'nl2br']
    )
    
    # Replace ```mermaid code blocks with proper mermaid divs
    html_body = re.sub(
        r'<code>mermaid\n(.*?)</code>',
        r'<div class="mermaid">\1</div>',
        html_body,
        flags=re.DOTALL
    )
    
    # Create complete HTML with professional styling AND Mermaid support
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASHA AI - Comprehensive Project Report</title>
    
    <!-- Mermaid JS for diagram rendering -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                primaryColor: '#3498db',
                primaryTextColor: '#fff',
                primaryBorderColor: '#2980b9',
                lineColor: '#34495e',
                secondaryColor: '#ecf0f1',
                tertiaryColor: '#f39c12'
            }}
        }});
    </script>
    
    <style>
        @media print {{
            @page {{
                size: A4;
                margin: 2cm;
            }}
            
            h1 {{
                page-break-before: always;
            }}
            
            h1:first-of-type {{
                page-break-before: avoid;
            }}
            
            table, pre, blockquote, .mermaid {{
                page-break-inside: avoid;
            }}
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.8;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: #fff;
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 4px solid #3498db;
            padding-bottom: 15px;
            margin-top: 50px;
            margin-bottom: 30px;
            font-size: 2.2em;
        }}
        
        h1:first-of-type {{
            font-size: 3em;
            text-align: center;
            border-bottom: none;
            color: #3498db;
            margin-top: 0;
        }}
        
        h2 {{
            color: #34495e;
            margin-top: 35px;
            margin-bottom: 20px;
            border-left: 5px solid #3498db;
            padding-left: 20px;
            font-size: 1.8em;
        }}
        
        h3 {{
            color: #7f8c8d;
            margin-top: 25px;
            margin-bottom: 15px;
            font-size: 1.4em;
        }}
        
        h4 {{
            color: #95a5a6;
            margin-top: 20px;
            font-size: 1.2em;
        }}
        
        p {{
            margin: 15px 0;
            text-align: justify;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 25px 0;
            font-size: 0.95em;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        thead tr {{
            background-color: #3498db;
            color: white;
            text-align: left;
        }}
        
        th, td {{
            padding: 14px 18px;
            border: 1px solid #ddd;
        }}
        
        tbody tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        tbody tr:hover {{
            background-color: #e8f4f8;
        }}
        
        code {{
            background-color: #f4f4f4;
            padding: 3px 8px;
            border-radius: 4px;
            font-family: 'Courier New', 'Consolas', monospace;
            font-size: 0.9em;
            color: #c7254e;
        }}
        
        pre {{
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 25px 0;
            line-height: 1.5;
        }}
        
        pre code {{
            background-color: transparent;
            color: #ecf0f1;
            padding: 0;
        }}
        
        blockquote {{
            border-left: 5px solid #3498db;
            margin: 25px 0;
            padding: 15px 25px;
            background-color: #f8f9fa;
            font-style: italic;
            color: #555;
        }}
        
        ul, ol {{
            margin: 20px 0;
            padding-left: 35px;
        }}
        
        li {{
            margin: 10px 0;
        }}
        
        hr {{
            border: none;
            border-top: 3px solid #ecf0f1;
            margin: 40px 0;
        }}
        
        strong {{
            color: #2c3e50;
            font-weight: 600;
        }}
        
        em {{
            color: #555;
        }}
        
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        /* Mermaid diagram styling */
        .mermaid {{
            background-color: #f8f9fa;
            border: 2px solid #3498db;
            border-radius: 8px;
            padding: 30px;
            margin: 30px 0;
            text-align: center;
        }}
        
        .cover-page {{
            text-align: center;
            padding: 100px 0;
        }}
        
        .cover-title {{
            font-size: 3.5em;
            color: #3498db;
            margin-bottom: 20px;
        }}
        
        .cover-subtitle {{
            font-size: 1.8em;
            color: #7f8c8d;
            margin-bottom: 40px;
        }}
        
        .cover-info {{
            font-size: 1.2em;
            color: #95a5a6;
            margin: 10px 0;
        }}
        
        @media print {{
            .no-print {{
                display: none;
            }}
        }}
        
        .instruction-box {{
            background-color: #d4edda;
            border: 2px solid #28a745;
            padding: 20px;
            margin: 30px 0;
            border-radius: 6px;
        }}
        
        .instruction-box h3 {{
            color: #155724;
            margin-top: 0;
        }}
        
        .instruction-box ol {{
            color: #155724;
        }}
    </style>
</head>
<body>
    <div class="cover-page">
        <div class="cover-title">ASHA AI</div>
        <div class="cover-subtitle">Intelligent Healthcare Memory System</div>
        <div class="cover-info">Comprehensive Project Report</div>
        <div class="cover-info">January 2026</div>
        <hr style="width: 50%; margin: 50px auto;">
        <div class="cover-info">Voice-First Healthcare Platform for Rural India</div>
        <div class="cover-info">Powered by Qdrant Vector Database</div>
    </div>
    
    <div class="instruction-box no-print">
        <h3>📄 How to Convert to PDF</h3>
        <ol>
            <li>Press <strong>Ctrl + P</strong> (or Cmd + P on Mac)</li>
            <li>Select "Save as PDF" as the destination</li>
            <li>Choose "More settings" and enable "Background graphics"</li>
            <li>Set scale to 90-95% if diagrams are cut off</li>
            <li>Click "Save" and choose filename: <strong>ASHA_AI_Project_Report.pdf</strong></li>
        </ol>
        <p><strong>Note:</strong> All diagrams are now rendered with Mermaid.js!</p>
    </div>
    
    {html_body}
    
    <hr>
    <div style="text-align: center; color: #95a5a6; margin: 50px 0 30px 0; font-size: 0.9em;">
        <p><strong>ASHA AI Project Report</strong></p>
        <p>Built with ❤️ for rural healthcare workers and mothers</p>
        <p>For more information, see the project README.md</p>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    html_file = Path("ASHA_AI_Project_Report.html")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"✅ Enhanced HTML report created with diagram support!")
    print(f"   File: {html_file.absolute()}")
    print()
    print("📊 Features:")
    print("   ✅ Mermaid diagrams rendered")
    print("   ✅ Professional styling")
    print("   ✅ Print-optimized layout")
    print()
    print("📄 To convert to PDF:")
    print("   1. Open ASHA_AI_Project_Report.html in your browser")
    print("   2. Wait for diagrams to load (2-3 seconds)")
    print("   3. Press Ctrl+P")
    print("   4. Select 'Save as PDF'")
    print("   5. Enable 'Background graphics'")
    print("   6. Save the PDF")

if __name__ == "__main__":
    try:
        convert_to_html_with_diagrams()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
