import sys
from pathlib import Path
from datetime import datetime


def find_duplicates_within_file(filepath):
    """Find duplicate entries within a single file."""
    seen = {}
    duplicates = []
    
    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                if line in seen:
                    duplicates.append((line, seen[line], line_num))
                else:
                    seen[line] = line_num
    
    return duplicates


def find_duplicates_between_files(file1, file2):
    """Find entries that appear in both files."""
    entries1 = {}
    entries2 = {}
    
    with open(file1, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                if line not in entries1:
                    entries1[line] = []
                entries1[line].append(line_num)
    
    with open(file2, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                if line not in entries2:
                    entries2[line] = []
                entries2[line].append(line_num)
    
    common_entries = set(entries1.keys()) & set(entries2.keys())
    duplicates = []
    for entry in common_entries:
        duplicates.append((entry, entries1[entry], entries2[entry]))
    
    return duplicates


def generate_html_report(file1, file2, dups1, dups2, common):
    """Generate an HTML report with tables."""
    total_issues = len(dups1) + len(dups2) + len(common)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Comparison Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .header h1 {{
            color: #333;
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        .header .meta {{
            color: #666;
            font-size: 0.9rem;
        }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .card .number {{
            font-size: 3rem;
            font-weight: bold;
            color: #667eea;
        }}
        .card .label {{
            color: #666;
            font-size: 0.9rem;
            margin-top: 5px;
        }}
        .card.warning .number {{
            color: #f59e0b;
        }}
        .card.danger .number {{
            color: #ef4444;
        }}
        .card.success .number {{
            color: #10b981;
        }}
        .section {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .section h2 {{
            color: #333;
            font-size: 1.4rem;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
            color: #444;
        }}
        tr:hover {{
            background: #f8f9ff;
        }}
        .no-data {{
            text-align: center;
            padding: 30px;
            color: #10b981;
            font-size: 1.1rem;
        }}
        .entry-data {{
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            background: #f5f5f5;
            padding: 8px 12px;
            border-radius: 6px;
            word-break: break-all;
        }}
        .file-info {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            margin: 2px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>File Comparison Report</h1>
            <p class="meta">Generated: {timestamp}</p>
            <p class="meta">File 1: <strong>{file1}</strong></p>
            <p class="meta">File 2: <strong>{file2}</strong></p>
        </div>
        
        <div class="summary-cards">
            <div class="card {'success' if len(dups1) == 0 else 'warning'}">
                <div class="number">{len(dups1)}</div>
                <div class="label">Duplicates in File 1</div>
            </div>
            <div class="card {'success' if len(dups2) == 0 else 'warning'}">
                <div class="number">{len(dups2)}</div>
                <div class="label">Duplicates in File 2</div>
            </div>
            <div class="card {'success' if len(common) == 0 else 'danger'}">
                <div class="number">{len(common)}</div>
                <div class="label">Common Entries</div>
            </div>
            <div class="card {'success' if total_issues == 0 else 'danger'}">
                <div class="number">{total_issues}</div>
                <div class="label">Total Issues</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Duplicates within {file1.name}</h2>
'''
    
    if dups1:
        html += '''            <table>
                <thead>
                    <tr>
                        <th>Original Line</th>
                        <th>Duplicate Line</th>
                        <th>Entry Data</th>
                    </tr>
                </thead>
                <tbody>
'''
        for entry, first_line, dup_line in dups1:
            html += f'''                    <tr>
                        <td>{first_line}</td>
                        <td>{dup_line}</td>
                        <td><div class="entry-data">{entry}</div></td>
                    </tr>
'''
        html += '''                </tbody>
            </table>
'''
    else:
        html += '''            <div class="no-data">No duplicates found</div>
'''
    
    html += f'''        </div>
        
        <div class="section">
            <h2>Duplicates within {file2.name}</h2>
'''
    
    if dups2:
        html += '''            <table>
                <thead>
                    <tr>
                        <th>Original Line</th>
                        <th>Duplicate Line</th>
                        <th>Entry Data</th>
                    </tr>
                </thead>
                <tbody>
'''
        for entry, first_line, dup_line in dups2:
            html += f'''                    <tr>
                        <td>{first_line}</td>
                        <td>{dup_line}</td>
                        <td><div class="entry-data">{entry}</div></td>
                    </tr>
'''
        html += '''                </tbody>
            </table>
'''
    else:
        html += '''            <div class="no-data">No duplicates found</div>
'''
    
    html += '''        </div>
        
        <div class="section">
            <h2>Entries Appearing in Both Files</h2>
'''
    
    if common:
        html += f'''            <table>
                <thead>
                    <tr>
                        <th>Lines in {file1.name}</th>
                        <th>Lines in {file2.name}</th>
                        <th>Entry Data</th>
                    </tr>
                </thead>
                <tbody>
'''
        for entry, lines1, lines2 in common:
            html += f'''                    <tr>
                        <td>{', '.join(map(str, lines1))}</td>
                        <td>{', '.join(map(str, lines2))}</td>
                        <td><div class="entry-data">{entry}</div></td>
                    </tr>
'''
        html += '''                </tbody>
            </table>
'''
    else:
        html += '''            <div class="no-data">No common entries found between files</div>
'''
    
    html += '''        </div>
    </div>
</body>
</html>
'''
    
    return html


def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_files.py <file1> <file2> [output_file.html]")
        print("\nThis utility compares two text files and finds duplicate entries.")
        print("It checks for:")
        print("  1. Duplicates within each file")
        print("  2. Entries that appear in both files")
        print("\nIf output_file is not specified, results are saved to 'duplicate_report.html'")
        sys.exit(1)
    
    file1 = Path(sys.argv[1])
    file2 = Path(sys.argv[2])
    output_file = sys.argv[3] if len(sys.argv) > 3 else "duplicate_report.html"
    
    if not file1.exists():
        print(f"Error: File '{file1}' not found.")
        sys.exit(1)
    
    if not file2.exists():
        print(f"Error: File '{file2}' not found.")
        sys.exit(1)
    
    dups1 = find_duplicates_within_file(file1)
    dups2 = find_duplicates_within_file(file2)
    common = find_duplicates_between_files(file1, file2)
    
    html_report = generate_html_report(file1, file2, dups1, dups2, common)
    
    with open(output_file, 'w') as f:
        f.write(html_report)
    
    total_issues = len(dups1) + len(dups2) + len(common)
    print(f"Comparison complete!")
    print(f"  - Duplicates in {file1.name}: {len(dups1)}")
    print(f"  - Duplicates in {file2.name}: {len(dups2)}")
    print(f"  - Common entries: {len(common)}")
    print(f"  - Total issues: {total_issues}")
    print(f"\nHTML Report saved to: {output_file}")


if __name__ == "__main__":
    main()
