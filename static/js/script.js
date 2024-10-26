// Reset the progress when the page loads
window.addEventListener('DOMContentLoaded', (event) => {
    // Reset the progress bar
    const progressBar = document.getElementById('progressBar');
    const messageElement = document.getElementById('progressMessage');

    progressBar.style.width = '0%';
    progressBar.setAttribute('aria-valuenow', 0);
    progressBar.textContent = '0%';

    // Optionally reset the backend status
    resetProgressStatus();
});

function resetProgressStatus() {
    fetch('https://subtranscribe.koyeb.app/reset-progress', { method: 'POST' })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok.');
            }
            return response.json();
        })
        .then(data => {
            console.log('Progress reset:', data);
        })
        .catch(error => {
            console.error('Error resetting progress:', error);
        });
}


// Continue with your interval function
const intervalId = setInterval(function() {
    fetch('https://subtranscribe.koyeb.app/progress', { method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        } })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok.');
            }
            return response.json();
        })
        .then(data => {
            console.log(data);

            const progressPercentage = typeof data.status === 'number' ? data.status : parseFloat(data.status) || 0;

            // Update the progress bar.
            const progressBar = document.getElementById('progressBar');
            progressBar.style.width = `${progressPercentage}%`;
            progressBar.style.transition = 'width 0.5s ease';
            progressBar.setAttribute('aria-valuenow', progressPercentage);
            progressBar.textContent = `${progressPercentage.toFixed(2)}%`;

            const messageElement = document.getElementById('progressMessage');
            messageElement.innerText = data.message;

            // Change color based on progress.
            if (progressPercentage === 100) {
                progressBar.style.backgroundColor = 'green'; // Success color
                messageElement.textContent = "Please wait for a few seconds...";
                clearInterval(intervalId);
            } else if (progressPercentage >= 50) {
                progressBar.style.backgroundColor = 'orange'; // Warning color
            } else {
                progressBar.style.backgroundColor = ''; // Default color
            }
        })
        .catch(error => {
            console.error('Error fetching progress:', error);
            document.getElementById('progressMessage').innerText = "fetching progress. Please try again.";
        });
}, 500); // Poll every 0.5 seconds

// Display selected file name dynamically
function showFileName() {
    const fileInput = document.getElementById("file");
    const fileName = document.getElementById("fileName");
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);  
        fileName.style.display = 'block';
        fileName.innerText = `File Selected: ${file.name} (${fileSizeMB} MB)`;
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
