from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTask

import fitz  # PyMuPDF
import os
import uuid
import zipfile
from pathlib import Path
from PIL import Image
from io import BytesIO

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Define a qualidade da imagem quality=40
# Quanto menor, maior a compressão e menor o tamanho do arquivo
def compress_pdf(input_path, output_path, quality=40):
    doc = fitz.open(input_path)
    for page in doc:
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            img_pil = Image.open(BytesIO(image_bytes))
            buf = BytesIO()
            img_pil.save(buf, format="JPEG", quality=quality)

            page.replace_image(xref, stream=buf.getvalue())

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()


def clear_upload_folder():
    """Remove todos os arquivos da pasta de upload."""
    for file in Path(UPLOAD_FOLDER).glob("*"):
        try:
            file.unlink()
        except Exception as e:
            print(f"Erro ao remover {file}: {e}")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload/")
async def upload(files: list[UploadFile] = File(...)):
    compressed_files = []
    temp_files = []

    for uploaded_file in files:
        original_name = uploaded_file.filename
        unique_id = uuid.uuid4().hex[:8]

        input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_original.pdf")
        output_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_compressed.pdf")

        with open(input_path, "wb") as f:
            f.write(await uploaded_file.read())

        compress_pdf(input_path, output_path)

        compressed_files.append({
            "path": output_path,
            "original_name": original_name
        })

        temp_files.extend([input_path, output_path])

    if len(compressed_files) == 1:
        file_info = compressed_files[0]
        return FileResponse(
            file_info["path"],
            media_type="application/pdf",
            filename=file_info["original_name"],
            background=BackgroundTask(clear_upload_folder)
        )

    # Mais de um arquivo? Cria ZIP
    zip_name = os.path.join(UPLOAD_FOLDER, f"compressed_{uuid.uuid4().hex[:6]}.zip")
    with zipfile.ZipFile(zip_name, "w") as zipf:
        for file in compressed_files:
            zipf.write(file["path"], arcname=file["original_name"])

    return FileResponse(
        zip_name,
        media_type="application/zip",
        filename=os.path.basename(zip_name),
        background=BackgroundTask(clear_upload_folder)
    )
