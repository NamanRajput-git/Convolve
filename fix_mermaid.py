"""
Fix Mermaid diagrams in HTML report
Converts code blocks to proper mermaid divs
"""

from pathlib import Path
import re

def fix_mermaid_diagrams():
    """Fix Mermaid diagram rendering in HTML"""
    
    html_file = Path("ASHA_AI_Project_Report.html")
    
    # Read current HTML
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Fix pattern 1: <pre><code class="language-mermaid">...</code></pre> -> <div class="mermaid">...</div>
    html_content = re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        r'<div class="mermaid">\1</div>',
        html_content,
        flags=re.DOTALL
    )
    
    # Fix pattern 2: &gt; and &lt; HTML entities back to > and <
    # Only within mermaid divs
    def unescape_mermaid(match):
        mermaid_code = match.group(1)
        mermaid_code = mermaid_code.replace('&gt;', '>')
        mermaid_code = mermaid_code.replace('&lt;', '<')
        mermaid_code = mermaid_code.replace('&quot;', '"')
        mermaid_code = mermaid_code.replace('&amp;', '&')
        return f'<div class="mermaid">{mermaid_code}</div>'
    
    html_content = re.sub(
        r'<div class="mermaid">(.*?)</div>',
        unescape_mermaid,
        html_content,
        flags=re.DOTALL
    )
    
    # Write fixed HTML
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Fixed Mermaid diagrams in HTML!")
    print(f"   File: {html_file.absolute()}")
    print()
    print("📊 Changes made:")
    print("   - Converted <code> blocks to <div class='mermaid'>")
    print("   - Un escaped HTML entities in diagrams")
    print()
    print("🌐 Open ASHA_AI_Project_Report.html in your browser to see diagrams!")

if __name__ == "__main__":
    try:
        fix_mermaid_diagrams()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
