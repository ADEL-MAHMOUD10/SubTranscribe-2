// Update progress every 10 seconds with proper error handling.
function updateProgress() {
    const timeout = 8000; // Set a timeout for fetch requests.

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
        const progressBar = document.getElementById('progressBar');
        const progressMessage = document.getElementById('progressMessage');
        
        // Update the progress bar.
        progressBar.style.width = data.status + '%';
        progressBar.setAttribute('aria-valuenow', data.status);
        progressBar.textContent = data.status + '%';
        
        // Update the progress message.
        progressMessage.textContent = data.message;

        // Call the function again after 10 seconds to continue updating.
        setTimeout(updateProgress, 10000);
    })
    .catch(error => {
        console.error('Error fetching progress:', error);
        
        // Retry updating the progress after 10 seconds in case of an error.
        setTimeout(updateProgress, 10000);
    });
}

// Call the updateProgress function when the page loads.
updateProgress();


// Display the selected file name dynamically when a file is chosen.
function showFileName() {
    const fileInput = document.getElementById('file');
    const fileNameDisplay = document.getElementById('fileName');
    const selectedFile = fileInput.files[0];

    // Show the file name only if a file is selected.
    if (selectedFile) {
        fileNameDisplay.textContent = "Selected file: " + selectedFile.name;
        fileNameDisplay.style.display = 'block';
    } else {
        fileNameDisplay.style.display = 'none';
    }
}

// Initialize modals and warning messages when the page loads.
document.addEventListener('DOMContentLoaded', function() {
    const messageModal = document.getElementById('messageModal');
    const closeButton = document.querySelector('.close-button');

    // Display the message modal on page load.
    messageModal.style.display = 'block';

    // Close the message modal when the close button is clicked.
    closeButton.addEventListener('click', function() {
        messageModal.style.display = 'none';
    });

    // Close the modal when clicking outside the modal box.
    window.addEventListener('click', function(event) {
        if (event.target === messageModal) {
            messageModal.style.display = 'none';
        }
    });
});

// Show a styled red warning message if an invalid link is entered.
function showWarningMessage() {
    const linkInput = document.getElementById('link').value;
    if (linkInput) {
        const warningModal = document.getElementById('messageModal');
        const warningContent = document.createElement('div');
        
        // Set up the content of the warning message with red styling.
        warningContent.innerHTML = `
            <div style="background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; font-family: Arial, sans-serif; margin-top: 10px;">
                <strong style="color: #721c24;">Warning:</strong> The link provided may not work correctly. <br><br>
                Some platforms like YouTube and Twitter may have restrictions. Please make sure the link points directly to an audio or video file. <br><br>
                <strong style="color: #721c24;">Tips:</strong> Check the link structure or try downloading the file first and then upload it for better results.
            </div>
        `;

        // Update the warning modal content and display it.
        warningModal.querySelector('p').innerText = ''; // Clear previous text content.
        warningModal.querySelector('p').appendChild(warningContent); // Append new warning content.
        warningModal.style.display = 'block';
    }
}

// Re-attach close button event listener for the modal if needed.
document.querySelector('.close-button').addEventListener('click', function() {
    document.getElementById('messageModal').style.display = 'none';
});

// Close the modal when clicking outside of it.
window.onclick = function(event) {
    const modal = document.getElementById('messageModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
};

