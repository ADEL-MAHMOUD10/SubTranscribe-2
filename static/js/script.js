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
}, 10000);

setInterval(() => {
    fetch('/download/transcript_id') 
}, 10000);

// Display selected file name dynamically
function showFileName() {
    const fileInput = document.getElementById('file');
    const fileNameDisplay = document.getElementById('fileName');
    const selectedFile = fileInput.files[0];
    fileNameDisplay.textContent = selectedFile ? "Selected file: " + selectedFile.name : '';
    fileNameDisplay.style.display = 'block'; // Show the file name display
}

document.addEventListener('DOMContentLoaded', function() {
    const messageModal = document.getElementById('messageModal');
    const closeButton = document.querySelector('.close-button');

    // إظهار النافذة المنبثقة
    messageModal.style.display = 'block';

    // إغلاق النافذة المنبثقة عند الضغط على زر الإغلاق
    closeButton.addEventListener('click', function() {
        messageModal.style.display = 'none';
    });

    // إغلاق النافذة عند الضغط في أي مكان خارج النافذة
    window.addEventListener('click', function(event) {
        if (event.target === messageModal) {
            messageModal.style.display = 'none';
        }
    });
});
