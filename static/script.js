document.getElementById("upload-form").addEventListener("submit", async function (e) {
    e.preventDefault();

    const statusDiv = document.getElementById("status");
    statusDiv.innerHTML = "Compactando...";

    const formData = new FormData();
    const files = e.target.files.files;

    for (let file of files) {
        formData.append("files", file);
    }

    const response = await fetch("/upload/", {
        method: "POST",
        body: formData
    });

    if (!response.ok) {
        statusDiv.innerHTML = "Erro ao compactar os PDFs.";
        return;
    }

    const blob = await response.blob();
    const contentDisposition = response.headers.get("content-disposition");
    const filename = contentDisposition
        ? contentDisposition.split("filename=")[1].replace(/["']/g, "")
        : "arquivo_compactado";

    const link = document.createElement("a");
    link.href = window.URL.createObjectURL(blob);
    link.download = filename;
    link.click();

    statusDiv.innerHTML = "Download iniciado: " + filename;
});
