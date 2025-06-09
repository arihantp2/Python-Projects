import sys
import os
import argparse
import camelot


def create_html_file(html_tables, output_path, pdf_filename):
    html_template = """
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>Extracted Tables from {pdf_filename}</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{ max-width: 95%; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #0056b3; }}
            hr {{ border: 0; height: 1px; background: #ddd; margin: 40px 0; }}
            table {{ border-collapse: collapse; width: 100%; font-size: 0.9em; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .table-container {{ overflow-x: auto; margin-bottom: 40px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Extracted Tables from <em>{pdf_filename}</em></h1>
            <p>Found {num_tables} table(s). The first row of each table was promoted to headers.</p>
            <hr>
            {tables_content}
        </div>
    </body>
    </html>
    """
    tables_content = "".join(f'<div class="table-container">{table}</div><hr>' for table in html_tables)
    full_html = html_template.format(
        pdf_filename=pdf_filename,
        num_tables=len(html_tables),
        tables_content=tables_content
    )
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)


def main():
    parser = argparse.ArgumentParser(description="Extract tables from a PDF and export to styled HTML.")
    parser.add_argument("pdf_file", help="Path to the input PDF file.")
    parser.add_argument("-o", "--output", default="tables_output.html", help="Output HTML file path.")
    args = parser.parse_args()

    input_pdf = args.pdf_file
    output_html = args.output

    if not os.path.exists(input_pdf):
        print(f"Error: File not found: {input_pdf}")
        sys.exit(1)

    print(f"Processing PDF: {input_pdf}")

    try:
        tables = camelot.read_pdf(input_pdf, pages='all', flavor='lattice')

        if tables.n == 0:
            print("No tables found in the PDF.")
            return

        html_tables = []
        for i, table in enumerate(tables):
            df = table.df

            if df.empty:
                continue

            # Promote first row to column headers
            df.columns = df.iloc[0]
            df = df[1:].copy()

            # Remove columns with empty or whitespace headers
            df = df.loc[:, df.columns.str.strip() != ""]

            # Remove unnamed columns (like 'Unnamed: 0')
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

            # Reset index to clean row index
            df.reset_index(drop=True, inplace=True)
            
             # Replace \n with <br> for HTML line breaks
            df = df.applymap(lambda x: str(x).replace('\n', ''))

            # Generate HTML without index column
            html = df.to_html(index=False, border=0, classes="data-table")
            html = html.replace("<th></th>", "")
            html_tables.append(html)

            print(f"✓ Table {i+1}: Extracted {df.shape[0]} rows x {df.shape[1]} columns")

        create_html_file(html_tables, output_html, os.path.basename(input_pdf))
        print(f"\n✅ Successfully saved HTML to: {output_html}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
