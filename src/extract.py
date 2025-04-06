import pymupdf
from collections import defaultdict
from constants import *


# Helper function to extract images and save
def extract_images_from_page(doc, page_no):
    images = []
    for img_index, img in enumerate(doc.get_page_images(page_no, full=True)):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        image_filename = f"page_{page_no + 1}_img_{img_index + 1}.{image_ext}"
        image_filepath = OUTPUT_IMG_DIR / image_filename
        with open(image_filepath, "wb") as img_file:
            img_file.write(image_bytes)
        images.append({
            "xref": xref,
            "image_file": str(image_filepath),
            "width": base_image["width"],
            "height": base_image["height"]
        })
    return images


def create_document_struct(doc: pymupdf.Document):

    metadata = doc.metadata
    toc = doc.get_toc()
    if not toc:
        print("Table of Contents not present.")

    toc_dict = defaultdict(list)
    for entry in toc:
        depth, title, page_no = entry
        toc_dict[page_no - 1].append({'depth': depth, 'title': title})


    # Build structured representation
    document_structure = {
        "metadata": metadata,
        # "toc": toc,
        "pages": []
    }

    return document_structure, toc_dict

def is_valid_sentence(text: str) -> bool:
    text = text.strip()

    # Reject if too short
    if len(text.split()) < 4:
        return False

    # Reject if it has >50% numeric content
    num_tokens = len(re.findall(r'\b\d+(\.\d+)?%?\b', text))
    total_tokens = len(text.split())
    if total_tokens > 0 and num_tokens / total_tokens > 0.4:
        return False

    # Must start with a capital letter and end with proper punctuation
    if not re.match(r"^[A-Z].*[\.\?!]$", text):
        return False

    return True


def pdf_to_json(filepath: str,
                extract_text: bool = True,
                extract_images: bool = False,
                extract_tables: bool = False,):

    document = pymupdf.open(filepath)
    document_structure, toc_dict = create_document_struct(doc=document)


    # Scan all pages and extract content
    for pno in range(len(document)):

        content_blocks = []

        if extract_text:
            page = document.load_page(pno)
            text_blocks = page.get_text("blocks")


            for block in text_blocks:
                x0, y0, x1, y1, text, block_no, block_type = block
                cleaned_text = text.strip()

                # Postprocessing to skip single-line texts
                if "\n" not in cleaned_text:
                    continue

                if len(cleaned_text) < 100:
                    continue

                content_blocks.append({
                    "type": "text",
                    # "bbox": [x0, y0, x1, y1],
                    "text": cleaned_text
                })

        if extract_images:
            images = extract_images_from_page(document, pno)
            for img in images:
                content_blocks.append({
                    "type": "image",
                    "image_file": img["image_file"],
                    "size": [img["width"], img["height"]]
                })

        page_data = {
            "page_number": pno + 1,
            "toc_titles": toc_dict.get(pno, []),
            "content": content_blocks
        }

        document_structure["pages"].append(page_data)

    return document_structure






# # Optionally detect and flag "References" section
# for page_data in document_structure["pages"]:
#     for block in page_data["content"]:
#         if block["type"] == "text" and "references" in block["text"].lower():
#             page_data["is_reference_section"] = True
#             break
