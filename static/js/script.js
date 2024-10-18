function updateProgress() {
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
            const progressStatus = data.status || 0;

            progressBar.style.width = progressStatus + '%';
            progressBar.textContent = progressStatus.toFixed(2) + '%';
            progressMessage.textContent = data.message;
        })
        .catch(error => {
            console.error('Error fetching progress:', error);
            const progressBar = document.getElementById('progressBar');
            progressBar.style.width = '0%';
            progressBar.textContent = 'Error';
            const progressMessage = document.getElementById('progressMessage');
            progressMessage.textContent = 'Failed to retrieve progress.';
        });
}

// Poll the progress every second
setInterval(updateProgress, 2000);



// Display selected file name dynamically
function showFileName() {
    const fileInput = document.getElementById("file");
    const fileName = document.getElementById("fileName");
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);  
        fileName.style.display = 'block';
        // استخدام innerHTML لإضافة span وتغيير لون حجم الملف
        fileName.innerHTML = `File Selected: ${file.name} (<span style="color: #007bff;">${fileSizeMB} MB</span>)`;
    }
}


function showWarningMessage() {
    const linkInput = document.getElementById('link').value;
    if (linkInput) {
        const warningModal = document.getElementById('messageModal');
        const warningText = `
            Some links (like YouTube and Twitter) may not work at the moment.
            Please ensure the link points directly to an audio or video file.
        `;
        warningModal.querySelector('p').innerText = warningText;
        warningModal.style.display = 'block';
    }
}

// Close modal functionality
document.querySelector('.close-button').addEventListener('click', function() {
    document.getElementById('messageModal').style.display = 'none';
});

window.onclick = function(event) {
    const modal = document.getElementById('messageModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
};
