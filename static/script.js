// Helper Function to display error messages
function showError(message) {
    document.getElementById('error').style.display = 'block';
    document.getElementById('errorMessage').innerText = message;
}

// Helper Function to hide error messages
function hideError() {
    document.getElementById('error').style.display = 'none';
}

// Function to upload the file to the FastAPI backend
async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const fileTypeSelect = document.getElementById('fileType');
    // const qnoSelect = document.getElementById('qno');
    const file = fileInput.files[0];
    const fileType = fileTypeSelect.value;
    // const qno = qnoSelect.value;  // Get selected question number

    if (!file) {
        showError("Please select a file first.");
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    let uploadUrl = fileType === 'audio' ? '/file/upload/' : '/file/upload-video/';

    try {
        const response = await fetch(uploadUrl, { method: 'POST', body: formData });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'File upload failed');
        }

        const data = await response.json();
        const fileId = data.file_id;

        // Show file info and allow downloading
        displayFileInfo(file, fileId);

        // Clear any previous error messages
        hideError();

        // Refresh the file list
        showAllFiles();

        // Optionally, pass `qno` with the uploaded file if necessary for further actions like transcription
        await transcribeFile(fileId, qno);

    } catch (error) {
        showError(error.message);
    }
}

// Function to display file information after upload
function displayFileInfo(file, fileId) {
    document.getElementById('fileInfo').style.display = 'block';
    document.getElementById('fileName').innerText = file.name;
    document.getElementById('fileId').innerText = fileId;
}

// Function to transcribe the file by file_id and pass the question number (qno) as a query parameter
async function transcribeFile(fileId, qno = 3) {
    document.getElementById('transcriptionBox').style.display = 'none';
    let transcriptionText = document.getElementById('transcriptionText');
    let languageInfo = document.getElementById('languageInfo');
    let answerText = document.getElementById('answerText');

    console.log("Selected Question Number:", qno);
    try {
        const response = await fetch(`/model/transcribe/${fileId}?qno=${qno}`, { method: 'POST' });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Transcription failed');
        }

        const data = await response.json();
        console.log(data); // Check the structure of the data

        // Extract the transcription result and language prediction info
        const transcription = data.response;
        const predictedLanguage = data.language;
        const qna = data.output;
        const filename = data.file_name;
        const fname = document.getElementById("fileNameText");

        if (transcription) {
            document.getElementById('transcriptionBox').style.display = 'block';
            transcriptionText.innerHTML = `<p>${transcription}</p>`;
            fname.innerHTML = `<p><strong>File Name:</strong>${filename}</p>`;
            languageInfo.style.display = 'block';
            languageInfo.innerHTML = `<p><strong>Predicted Language:</strong> ${predictedLanguage}</p>`;
            answerText.innerText = `${qna}`;
        } else {
            throw new Error('Transcription result is undefined');
        }

    } catch (error) {
        showError(error.message);
    }
}

// Function to retrieve the uploaded file by its ID
async function getFile(fileId) {
    try {
        const response = await fetch(`/file/${fileId}`);
        if (!response.ok) throw new Error('File not found');

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        // Create a download link and trigger download
        const a = document.createElement('a');
        a.href = url;
        a.download = document.getElementById('fileName').innerText;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

    } catch (error) {
        showError(error.message);
    }
}

// Function to delete a file by file_id
async function deleteFile(fileId) {
    try {
        const response = await fetch(`/file/delete/${fileId}`, { method: 'DELETE' });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'File deletion failed');
        }

        // Success message after deletion
        alert("File deleted successfully!");

        // Refresh the file list after deletion
        showAllFiles();

    } catch (error) {
        showError(error.message);
    }
}

// Function to show all uploaded files
async function showAllFiles() {
    try {
        const response = await fetch('/file/all/');
        if (!response.ok) throw new Error('Could not fetch file list');

        const data = await response.json();
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = '';

        if (data.files.length === 0) {
            fileList.innerHTML = '<li>No files found.</li>';
        } else {
            data.files.forEach(file => {
                const li = document.createElement('li');
                const fileLink = `/file/${file.file_id}`;
                const qnoSelectId = `qno-${file.file_id}`; // Unique ID for each file's question number selector

                let fileHTML = `
                    <a href="${fileLink}" target="_blank">${file.filename}</a>
                    <button class="download-btn" onclick="getFile('${file.file_id}')">Download</button>
                    <button class="delete-btn" onclick="deleteFile('${file.file_id}')">Delete</button>
                    <button class="transcribe-btn" onclick="transcribeFile('${file.file_id}', document.getElementById('${qnoSelectId}').value)">Transcribe</button>
                    <label for="qno">Select Question Number:</label>
                    <select id="${qnoSelectId}" name="qno">
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                        <option value="4">4</option>
                    </select>
                `;

                li.innerHTML = fileHTML;
                fileList.appendChild(li);
            });
        }

    } catch (error) {
        showError(error.message);
    }
}

// Load the list of files when the page loads
window.onload = showAllFiles;
