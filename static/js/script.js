function updateProgress() {
    const timeout = 1000; // Set a timeout for fetch requests.

    // Reset progress bar on page load
    const progressBar = document.getElementById('progressBar');
    const progressMessage = document.getElementById('progressMessage');
    progressBar.style.width = '0%'; // Reset progress bar to 0
    progressBar.setAttribute('aria-valuenow', 0);
    // Use Promise.race to implement a timeout for the fetch request.
    Promise.race([
        fetch('/progress').then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        }),
        new Promise((_, reject) => setTimeout(() => reject(new Error('Request timed out')), timeout))
    ])
    .then(data => {
        const progressPercentage = data.status || 0;

        // Update the progress bar.
        progressBar.style.width = `${progressPercentage}%`;
        progressBar.setAttribute('aria-valuenow', progressPercentage);
        progressBar.textContent = `${progressPercentage.toFixed(2)}%`;

        // Change color based on progress.
        if (progressPercentage === 100) {
            progressBar.style.backgroundColor = 'green'; // Success color
            progressMessage.textContent = "Please wait for a few seconds...";
            return; // Stop further updates
        } else if (progressPercentage < 100) {
            progressBar.style.backgroundColor = ''; // Default color
        }

        // Update the progress message.
        progressMessage.textContent = data.message;

        setTimeout(updateProgress, 1000); // Schedule the next update.
    })
    .catch(error => {
        console.error('Error fetching progress:', error);
        
        setTimeout(updateProgress, 1000); // Retry after a delay.
    });
}

// Call the updateProgress function when the page loads.
updateProgress();

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

