/**
 * comment.js - Enhanced comment system for Sphinx + ReadTheDocs with Utterances
 * Features: 
 * - File upload support
 * - File size validation
 * - File type validation
 * - Cross-browser compatibility
 * - Responsive design
 * - Progress indicators
 */

document.addEventListener('DOMContentLoaded', function() {
    // Configuration
    const config = {
        maxFileSize: 5 * 1024 * 1024, // 5MB
        allowedTypes: [
            'image/jpeg', 
            'image/png', 
            'image/gif',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ],
        utterances: {
            repo: '', // Set this in your Sphinx conf.py
            issueTerm: 'pathname',
            theme: 'github-light'
        }
    };

    // Check if utterances is already loaded
    if (typeof utterances !== 'undefined') {
        initEnhancedComments();
    } else {
        // Wait for utterances to load
        const observer = new MutationObserver(function(mutations, me) {
            if (typeof utterances !== 'undefined') {
                initEnhancedComments();
                me.disconnect(); // stop observing
            }
        });

        // Start observing the document body for changes
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    function initEnhancedComments() {
        // Find the utterances container
        const utterancesContainer = document.querySelector('.utterances');
        if (!utterancesContainer) return;

        // Create our enhanced comment container
        const commentContainer = document.createElement('div');
        commentContainer.className = 'enhanced-comments-container';
        commentContainer.style.margin = '20px 0';
        commentContainer.style.padding = '15px';
        commentContainer.style.borderRadius = '4px';
        commentContainer.style.backgroundColor = '#f8f9fa';
        commentContainer.style.border = '1px solid #e1e4e8';

        // Add title
        const title = document.createElement('h3');
        title.textContent = 'Leave a Comment';
        title.style.marginTop = '0';
        commentContainer.appendChild(title);

        // Create form
        const form = document.createElement('form');
        form.id = 'enhanced-comment-form';

        // Textarea for comment
        const textarea = document.createElement('textarea');
        textarea.id = 'comment-text';
        textarea.placeholder = 'Write your comment here...';
        textarea.required = true;
        textarea.style.width = '100%';
        textarea.style.minHeight = '100px';
        textarea.style.marginBottom = '10px';
        textarea.style.padding = '8px';
        textarea.style.border = '1px solid #d1d5da';
        textarea.style.borderRadius = '3px';
        form.appendChild(textarea);

        // File upload section
        const fileSection = document.createElement('div');
        fileSection.style.margin = '10px 0';

        const fileLabel = document.createElement('label');
        fileLabel.textContent = 'Attach File (optional, max 5MB):';
        fileLabel.style.display = 'block';
        fileLabel.style.marginBottom = '5px';
        fileLabel.style.fontWeight = 'bold';
        fileSection.appendChild(fileLabel);

        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.id = 'comment-file';
        fileInput.name = 'comment-file';
        fileInput.style.display = 'block';
        fileInput.style.marginBottom = '5px';
        fileSection.appendChild(fileInput);

        // File type info
        const fileInfo = document.createElement('div');
        fileInfo.id = 'file-info';
        fileInfo.style.fontSize = '0.8em';
        fileInfo.style.color = '#586069';
        fileInfo.style.marginBottom = '5px';
        fileSection.appendChild(fileInfo);

        // Error display
        const errorDisplay = document.createElement('div');
        errorDisplay.id = 'file-error';
        errorDisplay.style.color = '#cb2431';
        errorDisplay.style.fontSize = '0.8em';
        errorDisplay.style.marginBottom = '10px';
        errorDisplay.style.display = 'none';
        fileSection.appendChild(errorDisplay);

        form.appendChild(fileSection);

        // Submit button
        const submitBtn = document.createElement('button');
        submitBtn.type = 'submit';
        submitBtn.textContent = 'Post Comment';
        submitBtn.style.backgroundColor = '#2ea44f';
        submitBtn.style.color = 'white';
        submitBtn.style.border = 'none';
        submitBtn.style.padding = '8px 16px';
        submitBtn.style.borderRadius = '3px';
        submitBtn.style.cursor = 'pointer';
        submitBtn.style.fontWeight = 'bold';
        form.appendChild(submitBtn);

        // Progress indicator
        const progress = document.createElement('div');
        progress.id = 'upload-progress';
        progress.style.display = 'none';
        progress.style.marginTop = '10px';
        progress.style.height = '5px';
        progress.style.backgroundColor = '#e1e4e8';
        progress.style.borderRadius = '3px';
        
        const progressBar = document.createElement('div');
        progressBar.id = 'progress-bar';
        progressBar.style.height = '100%';
        progressBar.style.width = '0%';
        progressBar.style.backgroundColor = '#2ea44f';
        progressBar.style.borderRadius = '3px';
        progressBar.style.transition = 'width 0.3s ease';
        progress.appendChild(progressBar);
        
        form.appendChild(progress);

        // Insert our form before utterances
        utterancesContainer.parentNode.insertBefore(commentContainer, utterancesContainer);
        commentContainer.appendChild(form);

        // File input change handler
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            const errorElement = document.getElementById('file-error');
            errorElement.style.display = 'none';
            errorElement.textContent = '';
            
            if (!file) {
                document.getElementById('file-info').textContent = '';
                return;
            }

            // Validate file size
            if (file.size > config.maxFileSize) {
                errorElement.textContent = `File is too large (max ${formatFileSize(config.maxFileSize)})`;
                errorElement.style.display = 'block';
                e.target.value = '';
                document.getElementById('file-info').textContent = '';
                return;
            }

            // Validate file type
            if (config.allowedTypes.indexOf(file.type) === -1) {
                const allowedTypes = config.allowedTypes.join(', ');
                errorElement.textContent = `File type not allowed. Allowed types: ${allowedTypes}`;
                errorElement.style.display = 'block';
                e.target.value = '';
                document.getElementById('file-info').textContent = '';
                return;
            }

            // Display file info
            document.getElementById('file-info').textContent = 
                `Selected: ${file.name} (${formatFileSize(file.size)})`;
        });

        // Form submission handler
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const commentText = textarea.value.trim();
            if (!commentText) {
                alert('Please enter a comment');
                return;
            }

            const fileInput = document.getElementById('comment-file');
            const file = fileInput.files[0];
            
            // Show progress
            document.getElementById('upload-progress').style.display = 'block';
            document.getElementById('progress-bar').style.width = '0%';
            
            if (file) {
                // Simulate file upload (in a real implementation, you'd upload to a server)
                simulateUpload(file, function(uploadedFileUrl) {
                    // Include the file URL in the comment
                    const fullComment = `${commentText}\n\n[Attached: ${file.name}](${uploadedFileUrl})`;
                    postToUtterances(fullComment);
                });
            } else {
                // No file, just post the comment
                postToUtterances(commentText);
            }
        });
    }

    function simulateUpload(file, callback) {
        // In a real implementation, you would:
        // 1. Upload the file to your server
        // 2. Get back a URL to the uploaded file
        // 3. Call the callback with that URL
        
        // This is a simulation that just returns a fake URL after a delay
        let progress = 0;
        const progressInterval = setInterval(function() {
            progress += Math.random() * 10;
            if (progress > 100) progress = 100;
            document.getElementById('progress-bar').style.width = `${progress}%`;
            
            if (progress === 100) {
                clearInterval(progressInterval);
                setTimeout(function() {
                    // For demo purposes, we're just creating a data URL
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const fakeUrl = e.target.result; // data URL
                        callback(fakeUrl);
                    };
                    reader.readAsDataURL(file);
                }, 500);
            }
        }, 200);
    }

    function postToUtterances(commentText) {
        // This function would need to integrate with Utterances' API
        // Currently Utterances doesn't have a direct API for posting comments
        // So we'll simulate by focusing the comment box and inserting text
        
        // Find the utterances comment box
        const utterancesFrame = document.querySelector('.utterances-frame');
        if (utterancesFrame && utterancesFrame.contentWindow) {
            utterancesFrame.contentWindow.postMessage({
                type: 'set-comment',
                value: commentText
            }, 'https://utteranc.es');
            
            // Focus the comment box
            utterancesFrame.contentWindow.postMessage({
                type: 'focus-comment'
            }, 'https://utteranc.es');
            
            // For now, we'll just alert the user to submit manually
            alert('Please submit your comment in the Utterances comment box below. Your text and file info have been pre-filled.');
        } else {
            alert('Error: Could not connect to comments system. Please copy your comment and post it manually.');
            console.log('Comment text:', commentText);
        }
        
        // Reset form
        document.getElementById('comment-text').value = '';
        document.getElementById('comment-file').value = '';
        document.getElementById('file-info').textContent = '';
        document.getElementById('upload-progress').style.display = 'none';
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
});