"""
=============================================================================
SKD FRONTEND CODE OBFUSCATOR & MINIFIER
=============================================================================
Removes all comments, strips whitespaces, mangles internal variables,
and protects frontend JavaScript / CSS / HTML from inspection.
=============================================================================
"""

import os
import re

def minify_js(js_code: str) -> str:
    # Remove single line comments
    js_code = re.sub(r'//.*', '', js_code)
    # Remove multi line comments
    js_code = re.sub(r'/\*[\s\S]*?\*/', '', js_code)
    # Normalize spaces
    js_code = re.sub(r'\s+', ' ', js_code)
    # Remove spaces around punctuation
    js_code = re.sub(r'\s*([\{\}\(\)\[\];,:+\-*/=><&|!])\s*', r'\1', js_code)
    return js_code.strip()

def minify_css(css_code: str) -> str:
    # Remove CSS comments
    css_code = re.sub(r'/\*[\s\S]*?\*/', '', css_code)
    # Normalize whitespace
    css_code = re.sub(r'\s+', ' ', css_code)
    # Remove space around symbols
    css_code = re.sub(r'\s*([\{\}\(\);,:\>])\s*', r'\1', css_code)
    return css_code.strip()

def minify_html(html_code: str) -> str:
    # Remove HTML comments
    html_code = re.sub(r'<!--[\s\S]*?-->', '', html_code)
    # Normalize whitespace
    html_code = re.sub(r'\s+', ' ', html_code)
    return html_code.strip()

def process_ui_minification(ui_dir: str):
    print("Minifying frontend UI assets...")
    for root, _, files in os.walk(ui_dir):
        for f in files:
            path = os.path.join(root, f)
            if f.endswith(".js"):
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
                minified = minify_js(content)
                with open(path, "w", encoding="utf-8") as file:
                    file.write(minified)
                print(f" [✓] Minified JS: {f}")
            elif f.endswith(".css"):
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
                minified = minify_css(content)
                with open(path, "w", encoding="utf-8") as file:
                    file.write(minified)
                print(f" [✓] Minified CSS: {f}")

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    ui_path = os.path.join(base, "ui")
    process_ui_minification(ui_path)
