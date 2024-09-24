// Fetch and update progress every 2 seconds
setInterval(() => {
    fetch('/progress')
        .then(response => response.json())
        .then(data => {
            // Update progress bar width and text
            const progressBar = document.getElementById('progressBar');
            const progressMessage = document.getElementById('progressMessage');
            progressBar.style.width = data.status + '%';
            progressBar.setAttribute('aria-valuenow', data.status);
            progressBar.textContent = data.status + '%';
            progressMessage.textContent = data.message;
        });
}, 2000);

// Display selected file name dynamically
function showFileName() {
    const fileInput = document.getElementById('file');
    const fileNameDisplay = document.getElementById('fileName');
    const selectedFile = fileInput.files[0];
    fileNameDisplay.textContent = selectedFile ? "Selected file: " + selectedFile.name : '';
    fileNameDisplay.style.display = 'block'; // Show the file name display
}
