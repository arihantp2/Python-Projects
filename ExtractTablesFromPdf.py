import sys
import os
import argparse
import re
import camelot
import fitz  # PyMuPDF library


def find_table_caption(table, pdf_doc, search_margin=75):
    """
    Tries to find a caption for a table by searching for text
    in a rectangular area directly above the table's location.

    Args:
        table (camelot.Table): The table object found by Camelot.
        pdf_doc (fitz.Document): The PDF document object from PyMuPDF.
        search_margin (int): How many points above the table to search for a caption.

    Returns:
        str: The found caption text or a default message.
    """
    # Camelot's coordinate system has (0,0) at the bottom-left.
    # PyMuPDF's coordinate system has (0,0) at the top-left.
    # We need to convert coordinates.
    tbl_x0, tbl_y1, tbl_x1, tbl_y0 = table._bbox

    page = pdf_doc[table.page - 1]
    page_height = page.rect.height

    # Define the search area (a rectangle above the table) in PyMuPDF coordinates
    # y0 for PyMuPDF is page_height - tbl_y0 (camelot's top)
    # We search from (y0 - search_margin) to y0.
    search_rect = fitz.Rect(
        tbl_x0 - 20, # Widen search area slightly for captions that are not perfectly aligned
        (page_height - tbl_y0) - search_margin,
        tbl_x1 + 20, # Widen search area slightly
        page_height - tbl_y0
    )

    # Get all text blocks within our defined search area, sorted by vertical position
    text_blocks = page.get_text("blocks", clip=search_rect, sort=True)

    # More flexible regex: Looks for "Table" not necessarily at the start of a line.
    caption_pattern = re.compile(r'Table\s*[\d\.:]+', re.IGNORECASE)

    for block in reversed(text_blocks): # Search from bottom-up, closer to the table first
        block_text = block[4]
        match = caption_pattern.search(block_text)
        if match:
            # Return the entire block of text where the match was found
            return block_text.strip().replace('\n', ' ')

    return ""


def create_html_file(tables_data, output_path, pdf_filename):
    """
    Generates a single HTML file containing all extracted tables with their captions.
    """
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
    h3.table-caption {{ color: #333; margin-top: 40px; border-bottom: 2px solid #0056b3; padding-bottom: 5px; text-align: center; }}
    hr {{ border: 0; height: 1px; background: #ddd; margin-top: 40px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 0.9em; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
    th {{ background-color: #f2f2f2; font-weight: bold; text-align: center; }}
    tr:nth-child(even) {{ background-color: #f9f9f9; }}
    .table-container {{ overflow-x: auto; margin-bottom: 20px; }}
</style>

    </head>
    <body>
        <div class="container">
            <h1>Extracted Tables from <em>{pdf_filename}</em></h1>
            <p>Found {num_tables} table(s).</p>
            {tables_content}
        </div>
    </body>
    </html>
    """
    tables_content = ""
    for item in tables_data:
        # For each table, add its caption and then the HTML table itself.
        tables_content += f'<h3 style="text-align: center; font-weight: bold; margin-top: 40px; padding-bottom: 5px;">{item["caption"]}</h3>\n'
        tables_content += f'<div class="table-container">{item["html"]}</div>\n'

    full_html = html_template.format(
        pdf_filename=pdf_filename,
        num_tables=len(tables_data),
        tables_content=tables_content
    )
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)


def main():
    parser = argparse.ArgumentParser(description="Extract tables and their captions from a PDF and export to styled HTML.")
    parser.add_argument("pdf_file", help="Path to the input PDF file.")
    parser.add_argument("-o", "--output", default="tables_output.html", help="Output HTML file path.")
    parser.add_argument("-m", "--margin", type=int, default=30, help="Distance (in points) above a table to search for a caption. Default: 30")
    args = parser.parse_args()

    input_pdf = args.pdf_file
    output_html = args.output
    search_margin = args.margin

    if not os.path.exists(input_pdf):
        print(f"Error: File not found: {input_pdf}")
        sys.exit(1)

    print(f"Processing PDF: {input_pdf}")
    print(f"Using caption search margin of: {search_margin} points")

    try:
        pdf_document = fitz.open(input_pdf)
        tables = camelot.read_pdf(input_pdf, pages='all', flavor='lattice')

        if tables.n == 0:
            print("No tables found in the PDF.")
            pdf_document.close()
            return

        extracted_data = []
        for i, table in enumerate(tables):
            df = table.df
            if df.empty:
                continue

            caption = find_table_caption(table, pdf_document, search_margin)
            #print(f"-> Processing Table {i+1} on page {table.page}...")
            #print(f"   Caption found: '{caption}'")

            # Promote first row to column headers
            df.columns = df.iloc[0]
            df = df[1:].copy()
            # Clean up column names by stripping whitespace
            df.columns = df.columns.astype(str).str.strip()
            df = df.loc[:, df.columns != ""]
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df.reset_index(drop=True, inplace=True)
            
            df = df.applymap(lambda x: str(x).replace('\n', '<br>'))
            html = df.to_html(index=False, border=0, classes="data-table", escape=False)
            html = html.replace("<th></th>", "")
            html = html.replace('<table class="dataframe data-table">', '<table style="border-collapse: collapse; font-size: 0.9em; margin-bottom: 20px;">')
            html = html.replace('<th>', '<th style="border: 1px solid #ddd; padding: 8px; text-align: center; background-color: #f2f2f2; font-weight: bold;">')
            html = html.replace('<td>', '<td style="border: 1px solid #ddd; padding: 8px; text-align: center;">')
            extracted_data.append({"caption": caption, "html": html})
            #print(f"✓ Extracted {df.shape[0]} rows x {df.shape[1]} columns")

        pdf_document.close()
        
        create_html_file(extracted_data, output_html, os.path.basename(input_pdf))
        print(f"\n✅ Successfully saved HTML to: {output_html}")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        if 'pdf_document' in locals() and pdf_document and not pdf_document.is_closed:
            pdf_document.close()
        sys.exit(1)


if __name__ == "__main__":
    main()