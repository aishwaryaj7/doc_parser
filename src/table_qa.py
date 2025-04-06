from openai import OpenAI
import pymupdf


# Utility to extract tables as text
def extract_text_from_pdf(pdf_path):
    doc = pymupdf.open(pdf_path)
    text = ""
    row_count = 0
    header = ""

    for page in doc:
        tables = page.find_tables()
        for table in tables:
            if page.number == 0 and table.header.external:
                header = (
                    ";".join(
                        [name if name is not None else "" for name in table.header.names]
                    ) + "\n"
                )
                text += header
                row_count += 1

            for row in table.extract():
                row_text = (
                    ";".join([cell if cell is not None else "" for cell in row]) + "\n"
                )
                if row_text != header:
                    text += row_text
                    row_count += 1
    doc.close()
    return text

# Wrapper to call OpenAI completion
def generate_response_with_chatgpt(client, prompt):
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7
    )
    return response.choices[0].text.strip()
