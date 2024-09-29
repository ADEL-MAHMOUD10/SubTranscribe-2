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

    messageModal.style.display = 'block';

    closeButton.addEventListener('click', function() {
        messageModal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target === messageModal) {
            messageModal.style.display = 'none';
        }
    });
});

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
