// Fetch and update progress every 2 seconds
setInterval(() => {
    fetch('/progress')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const progressBar = document.getElementById('progressBar');
            const progressMessage = document.getElementById('progressMessage');
            progressBar.style.width = data.status + '%';
            progressBar.setAttribute('aria-valuenow', data.status);
            progressBar.textContent = data.status + '%';
            progressMessage.textContent = data.message;
        })
        .catch(error => {
            console.error('Error fetching progress:', error);
        });
}, 11000);

setInterval(() => {
    fetch('/download/transcript_id') 
}, 11000);

// Display selected file name dynamically
function showFileName() {
    const fileInput = document.getElementById('file');
    const fileNameDisplay = document.getElementById('fileName');
    const selectedFile = fileInput.files[0];
    fileNameDisplay.textContent = selectedFile ? "Selected file: " + selectedFile.name : '';
    fileNameDisplay.style.display = 'block'; // Show the file name display
}
