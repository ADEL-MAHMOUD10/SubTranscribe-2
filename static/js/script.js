// Update progress every 10 seconds with proper error handling.
function updateProgress() {
    const timeout = 10000; // Set a timeout for fetch requests.

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

        // Call the function again after 1 seconds to continue updating.
        setTimeout(updateProgress, 5000);
    })
    .catch(error => {
        console.error('Error fetching progress:', error);
        
        // Retry updating the progress after 1 seconds in case of an error.
        setTimeout(updateProgress, 5000);
    });
}

// Call the updateProgress function when the page loads.
updateProgress();

// Upload file function
function uploadFile() {
    var fileInput = document.getElementById('file');
    var file = fileInput.files[0];  // Get the selected file
    if (!file) return;  // If no file is selected, stop execution

    var formData = new FormData();
    formData.append('file', file);

    var xhr = new XMLHttpRequest();

    // Event listener to track upload progress
    xhr.upload.addEventListener('progress', function(event) {
        if (event.lengthComputable) {
            var loadedMB = (event.loaded / (1024 * 1024)).toFixed(2);  // Convert to MB
            var totalMB = (event.total / (1024 * 1024)).toFixed(2);  // Total file size in MB

            // Update the progress bar
            var progressPercent = (event.loaded / event.total) * 100;
            var progressBar = document.getElementById('progressBar');
            if (progressBar) {
                progressBar.style.width = progressPercent + '%';
                progressBar.innerText = progressPercent.toFixed(2) + '%';
            }

            // Update the uploaded size text
            var uploadedSize = document.getElementById('uploadedSize');
            if (uploadedSize) {
                uploadedSize.innerText = `Uploaded: ${loadedMB} MB / ${totalMB} MB`;
            }

            // Update the progress message
            var progressMessage = document.getElementById('progressMessage');
            if (progressMessage) {
                progressMessage.innerText = `Uploading: ${loadedMB} MB of ${totalMB} MB`;
            }
        }
    });

    // Handling server response
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                console.log('File uploaded successfully:', xhr.responseText);
                // Any additional handling after a successful upload
            } else {
                console.error('Error uploading file:', xhr.statusText);
            }
        }
    };

    xhr.open('POST', '/', true);  // Replace '/' with the actual upload URL
    xhr.send(formData);  // Send the file data
}


// Display selected file name dynamically
function showFileName() {
    const fileInput = document.getElementById("file");
    const fileName = document.getElementById("fileName");
    const uploadedSize = document.getElementById("uploadedSize");
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);  
        fileName.style.display = 'block';
        fileName.innerText = `File Selected: ${file.name} (${fileSizeMB} MB)`;
        uploadedSize.innerText = `Uploaded: 0 MB / ${fileSizeMB} MB`; 
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

// document.addEventListener('DOMContentLoaded', function() {
//     const messageModal = document.getElementById('messageModal');
//     const closeButton = document.querySelector('.close-button');

//     messageModal.style.display = 'block';

//     closeButton.addEventListener('click', function() {
//         messageModal.style.display = 'none';
//     });

//     window.addEventListener('click', function(event) {
//         if (event.target === messageModal) {
//             messageModal.style.display = 'none';
//         }
//     });
// });
