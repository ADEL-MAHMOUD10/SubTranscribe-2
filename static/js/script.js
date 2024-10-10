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

        // Update the progress bar width and text.
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

setInterval(function() {
    fetch('/progress')
        .then(response => response.json())
        .then(data => {
            console.log(data); // Log the received data
            // Update your UI with the progress data here
        })
        .catch(error => console.error('Error fetching progress:', error));
}, 2000); // Fetch progress every 2 seconds

// Function to upload the file
function uploadFile() {
    var fileInput = document.getElementById('file');
    var file = fileInput.files[0];  // Get the selected file
    var formData = new FormData();
    formData.append('file', file);  // Append the file to the FormData object

    var xhr = new XMLHttpRequest();

    // Event to monitor upload progress
    xhr.upload.addEventListener('progress', function(event) {
        if (event.lengthComputable) {
            // Calculate the size of the uploaded and total file in MB
            var loadedMB = (event.loaded / (1024 * 1024)).toFixed(2);  
            var totalMB = (event.total / (1024 * 1024)).toFixed(2);  

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

    // Handle the server response
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                console.log('File uploaded successfully:', xhr.responseText);
                // Additional processing can be added here
            } else {
                console.error('Error uploading file:', xhr.statusText);
            }
        }
    };

    xhr.open('POST', '/', true);  // Replace '/' with the actual upload endpoint
    xhr.send(formData);  // Send the FormData object
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

// Show warning message for link form
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
