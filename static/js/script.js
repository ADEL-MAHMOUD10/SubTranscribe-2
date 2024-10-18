setInterval(function() {
    fetch('/progress',{ method: 'GET'})
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok.');
            }
            return response.json();
        })
        .then(data => {
            const progressPercentage = data.status || 0; // التأكد من أن المتغير يعرف هنا

            // Update the progress bar.
            const progressBar = document.getElementById('progressBar');
            progressBar.style.width = `${progressPercentage}%`;
            progressBar.setAttribute('aria-valuenow', progressPercentage);
            progressBar.textContent = `${progressPercentage.toFixed(2)}%`;
    
            document.getElementById('progressMessage').innerText = data.message;

            // Change color based on progress.
            if (progressPercentage === 100) {
                progressBar.style.backgroundColor = 'green'; // Success color
                document.getElementById('progressMessage').textContent = "Please wait for a few seconds...";
                return; // Stop further updates
            } else if (progressPercentage < 100) {
                progressBar.style.backgroundColor = ''; // Default color
            }
        })
        .catch(error => {
            console.error('Error fetching progress:', error); // طباعة الخطأ
        });
}, 1000);  // Poll every second


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
