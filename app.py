import streamlit as st
import os
import io
import zipfile
import fitz
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image
from fpdf import FPDF
from docx2pdf import convert as convert_docx
from pptx import Presentation
import datetime

st.set_page_config(page_title="All-in-One PDF Converter", layout="centered")

if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = None
if 'selected_operation' not in st.session_state:
    st.session_state.selected_operation = None

st.title("All-in-One PDF Converter")

if st.session_state.uploaded_files:
    st.warning("Files uploaded. Remove them before changing operation.")

if st.session_state.uploaded_files is None:
    selected_operation = st.selectbox("Select Operation", [
        "Generate Empty PDF",
        "Any File to PDF",
        "Images to PDF (Multiple images into single PDF)",
        "Extract Pages from PDF",
        "Merge PDFs",
        "Split PDF (Choose Option A or B)",
        "Compress PDF",
        "Insert Page Numbers"
    ])
    st.session_state.selected_operation = selected_operation
else:
    st.info(f"Operation: {st.session_state.selected_operation}")

if st.session_state.selected_operation:
    operation = st.session_state.selected_operation

    allowed_files = {
        "Generate Empty PDF": "No files required",
        "Any File to PDF": "Allowed: PNG, JPG, JPEG, DOCX, PPTX, TXT",
        "Images to PDF (Multiple images into single PDF)": "Allowed: PNG, JPG, JPEG",
        "Extract Pages from PDF": "Allowed: PDF",
        "Merge PDFs": "Allowed: PDF",
        "Split PDF (Choose Option A or B)": "Allowed: PDF",
        "Compress PDF": "Allowed: PDF",
        "Insert Page Numbers": "Allowed: PDF",
    }
    st.markdown(f"**Allowed files: {allowed_files[operation]}**")

    if operation != "Generate Empty PDF" and st.session_state.uploaded_files is None:
        uploaded_files = st.file_uploader("Upload File(s)", accept_multiple_files=True)
        if uploaded_files:
            st.session_state.uploaded_files = uploaded_files

    if st.session_state.uploaded_files or operation == "Generate Empty PDF":
        try:
            if operation == "Generate Empty PDF":
                num_pages = st.number_input("Number of pages", min_value=1, step=1)
                file_name = st.text_input("File name", "empty_pdf")
                if st.button("Generate"):
                    pdf = FPDF()
                    for i in range(1, num_pages + 1):
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
                        pdf.cell(200, 10, txt=f"Page {i}", ln=1, align="C")
                    output = pdf.output(dest="S").encode("latin1")
                    st.download_button("Download Empty PDF", output, f"{file_name}.pdf", mime="application/pdf")

            if operation == "Any File to PDF":
                file_name = st.text_input("Zip file name for converted PDFs", "converted_pdfs")
                if st.button("Convert to PDF"):
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "a") as zipf:
                        for file in st.session_state.uploaded_files:
                            ext = file.name.split(".")[-1].lower()
                            if ext in ['png', 'jpg', 'jpeg']:
                                image = Image.open(file)
                                pdf_bytes = io.BytesIO()
                                image.convert("RGB").save(pdf_bytes, format="PDF")
                                zipf.writestr(f"{os.path.splitext(file.name)[0]}.pdf", pdf_bytes.getvalue())
                            elif ext == 'txt':
                                text = file.read().decode('utf-8')
                                pdf = FPDF()
                                pdf.add_page()
                                pdf.set_font("Arial", size=12)
                                for line in text.split("\n"):
                                    pdf.cell(200, 10, txt=line, ln=1)
                                pdf_bytes = pdf.output(dest="S").encode("latin1")
                                zipf.writestr(f"{os.path.splitext(file.name)[0]}.pdf", pdf_bytes)
                            elif ext == 'docx':
                                with open(file.name, 'wb') as f:
                                    f.write(file.getbuffer())
                                convert_docx(file.name)
                                pdf_path = file.name.replace('.docx', '.pdf')
                                with open(pdf_path, 'rb') as f:
                                    zipf.writestr(f"{os.path.splitext(file.name)[0]}.pdf", f.read())
                                os.remove(pdf_path)
                                os.remove(file.name)
                            elif ext == 'pptx':
                                prs = Presentation(file)
                                pdf = FPDF()
                                for slide in prs.slides:
                                    pdf.add_page()
                                    for shape in slide.shapes:
                                        if hasattr(shape, "text"):
                                            pdf.multi_cell(200, 10, txt=shape.text, align="L")
                                pdf_bytes = pdf.output(dest="S").encode("latin1")
                                zipf.writestr(f"{os.path.splitext(file.name)[0]}.pdf", pdf_bytes)
                    zip_buffer.seek(0)
                    st.download_button("Download All PDFs (ZIP)", zip_buffer, f"{file_name}.zip")

            if operation == "Images to PDF (Multiple images into single PDF)":
                file_name = st.text_input("PDF file name", "images_combined")
                if st.button("Convert"):
                    pdf = FPDF()
                    for file in st.session_state.uploaded_files:
                        img = Image.open(file)
                        img_path = f"temp_{file.name}"
                        img.save(img_path)
                        pdf.add_page()
                        pdf.image(img_path, x=0, y=0, w=210, h=297)
                        os.remove(img_path)
                    pdf_bytes = pdf.output(dest="S").encode("latin1")
                    st.download_button("Download Combined PDF", pdf_bytes, f"{file_name}.pdf", mime="application/pdf")

            if operation == "Extract Pages from PDF":
                file = st.session_state.uploaded_files[0]
                pages = st.text_input("Enter pages (e.g., 1,3,5-7):")
                file_name = st.text_input("Extracted PDF name", "extracted_pages")
                if st.button("Extract"):
                    reader = PdfReader(file)
                    writer = PdfWriter()
                    page_numbers = []
                    for part in pages.split(","):
                        if "-" in part:
                            start, end = part.split("-")
                            page_numbers.extend(range(int(start)-1, int(end)))
                        else:
                            page_numbers.append(int(part)-1)
                    for p in page_numbers:
                        writer.add_page(reader.pages[p])
                    output = io.BytesIO()
                    writer.write(output)
                    st.download_button("Download Extracted PDF", output.getvalue(), f"{file_name}.pdf", mime="application/pdf")

            if operation == "Merge PDFs":
                merger = PdfMerger()
                file_name = st.text_input("Merged PDF name", "merged_pdf")
                if st.button("Merge"):
                    for file in st.session_state.uploaded_files:
                        merger.append(file)
                    output = io.BytesIO()
                    merger.write(output)
                    merger.close()
                    st.download_button("Download Merged PDF", output.getvalue(), f"{file_name}.pdf", mime="application/pdf")

            if operation == "Split PDF (Choose Option A or B)":
                file = st.session_state.uploaded_files[0]
                split_option = st.radio("Select Split Option", ["A) Split by page range", "B) Each page as PDF"])
                if split_option == "A) Split by page range":
                    range_pages = st.number_input("Split every N pages", min_value=1, step=1)
                    file_name = st.text_input("Base name for split PDFs", "split_pdf")
                    if st.button("Split PDF (Option A)"):
                        reader = PdfReader(file)
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "a") as zipf:
                            for i in range(0, len(reader.pages), range_pages):
                                writer = PdfWriter()
                                for page in range(i, min(i+range_pages, len(reader.pages))):
                                    writer.add_page(reader.pages[page])
                                output = io.BytesIO()
                                writer.write(output)
                                zipf.writestr(f"{file_name}_{i//range_pages+1}.pdf", output.getvalue())
                        zip_buffer.seek(0)
                        st.download_button("Download Split PDFs (ZIP)", zip_buffer, f"{file_name}.zip")

                if split_option == "B) Each page as PDF":
                    file_name = st.text_input("ZIP name for single-page PDFs", "single_page_pdfs")
                    if st.button("Split PDF (Option B)"):
                        reader = PdfReader(file)
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "a") as zipf:
                            for i, page in enumerate(reader.pages):
                                writer = PdfWriter()
                                writer.add_page(page)
                                output = io.BytesIO()
                                writer.write(output)
                                zipf.writestr(f"page_{i+1}.pdf", output.getvalue())
                        zip_buffer.seek(0)
                        st.download_button("Download ZIP", zip_buffer, f"{file_name}.zip")

            if operation == "Compress PDF":
                file = st.session_state.uploaded_files[0]
                file_name = st.text_input("Compressed PDF name", "compressed_pdf")
                if st.button("Compress"):
                    doc = fitz.open(stream=file.read(), filetype="pdf")
                    output = io.BytesIO()
                    doc.save(output, deflate=True)
                    st.download_button("Download Compressed PDF", output.getvalue(), f"{file_name}.pdf", mime="application/pdf")

            if operation == "Insert Page Numbers":
                file = st.session_state.uploaded_files[0]
                file_name = st.text_input("PDF name with page numbers", "numbered_pdf")
                if st.button("Add Page Numbers"):
                    doc = fitz.open(stream=file.read(), filetype="pdf")
                    for page in doc:
                        page.insert_text((30, 30), f"Page {page.number + 1}", fontsize=12)
                    output = io.BytesIO()
                    doc.save(output)
                    st.download_button("Download PDF with Page Numbers", output.getvalue(), f"{file_name}.pdf", mime="application/pdf")
        except Exception:
            st.info("An error occurred while processing. Please check file format or input and try again.")

if st.button("Remove Uploaded Files"):
    st.session_state.uploaded_files = None
    st.session_state.selected_operation = None
    st.experimental_rerun()

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<small>Copyright © Pavan Sri Sai Mondem, Siva Satyamsetti, "
            "Uma Satyam Mounika Sapireddy, Bhuvaneswari Devi Seru, Chandu Meela</small>",
            unsafe_allow_html=True)
