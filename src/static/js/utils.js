// Copy functionality
function copyText(className) {
    let textToCopy;

    if (className === 'directory-structure') {
        // For directory structure, get the hidden input value
        const hiddenInput = document.getElementById('directory-structure-content');
        if (!hiddenInput) return;
        textToCopy = hiddenInput.value;
    } else {
        // For other elements, get the textarea value
        const textarea = document.querySelector('.' + className);
        if (!textarea) return;
        textToCopy = textarea.value;
    }

    const button = document.querySelector(`button[onclick="copyText('${className}')"]`);
    if (!button) return;

    // Copy text
    navigator.clipboard.writeText(textToCopy)
        .then(() => {
            // Store original content
            const originalContent = button.innerHTML;

            // Change button content
            button.innerHTML = 'Copied!';

            // Reset after 1 second
            setTimeout(() => {
                button.innerHTML = originalContent;
            }, 1000);
        })
        .catch(err => {
            // Show error in button
            const originalContent = button.innerHTML;
            button.innerHTML = 'Failed to copy';
            setTimeout(() => {
                button.innerHTML = originalContent;
            }, 1000);
        });
}

// Helper functions for toggling result blocks
function showLoading() {
    document.getElementById('results-loading').style.display = 'block';
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('results-error').style.display = 'none';
}
function showResults() {
    document.getElementById('results-loading').style.display = 'none';
    document.getElementById('results-section').style.display = 'block';
    document.getElementById('results-error').style.display = 'none';
}
function showError(msg) {
    document.getElementById('results-loading').style.display = 'none';
    document.getElementById('results-section').style.display = 'none';
    const errorDiv = document.getElementById('results-error');
    errorDiv.innerHTML = msg;
    errorDiv.style.display = 'block';
}

function handleSubmit(event, showLoadingSpinner = false) {
    event.preventDefault();
    const form = event.target || document.getElementById('ingestForm');
    if (!form) return;

    if (showLoadingSpinner) {
        showLoading();
    }

    const submitButton = form.querySelector('button[type="submit"]');
    if (!submitButton) return;

    // Collect form values into a plain object
    let data = {};
    const inputText = form.querySelector('[name="input_text"]');
    const token = form.querySelector('[name="token"]');
    const slider = document.getElementById('file_size');
    const patternType = document.getElementById('pattern_type');
    const pattern = document.getElementById('pattern');

    if (inputText) data.input_text = inputText.value;
    if (token) data.token = token.value;
    if (slider) data.max_file_size = slider.value;
    if (patternType) data.pattern_type = patternType.value;
    if (pattern) data.pattern = pattern.value;

    const originalContent = submitButton.innerHTML;

    if (showLoadingSpinner) {
        submitButton.disabled = true;
        submitButton.innerHTML = `
            <div class="flex items-center justify-center">
                <svg class="animate-spin h-5 w-5 text-gray-900" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span class="ml-2">Processing...</span>
            </div>
        `;
        submitButton.classList.add('bg-[#ffb14d]');
    }

    // Submit the form to /api/ingest as JSON
    fetch('/api/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            // Hide loading overlay
            submitButton.disabled = false;
            submitButton.innerHTML = originalContent;

            // Handle error
            if (data.error) {
                showError(`<div class='mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700'>${data.error}</div>`);
                return;
            }

            // Show results section
            showResults();

            // Set plain text content for summary, tree, and content
            document.getElementById('result-summary').value = data.summary || '';
            document.getElementById('directory-structure-content').value = data.tree || '';
            document.getElementById('result-content').value = data.content || '';

            // Populate directory structure lines as clickable <pre> elements
            const dirPre = document.getElementById('directory-structure-pre');
            if (dirPre && data.tree) {
                dirPre.innerHTML = '';
                data.tree.split('\n').forEach(line => {
                    const pre = document.createElement('pre');
                    pre.setAttribute('name', 'tree-line');
                    pre.className = 'cursor-pointer hover:line-through hover:text-gray-500';
                    pre.textContent = line;
                    pre.onclick = function() { toggleFile(this); };
                    dirPre.appendChild(pre);
                });
            }

            // Scroll to results
            document.getElementById('results-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
        })
        .catch(error => {
            submitButton.disabled = false;
            submitButton.innerHTML = originalContent;
            showError(`<div class='mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700'>${error}</div>`);
        });
}

function copyFullDigest() {
    const directoryStructure = document.getElementById('directory-structure-content').value;
    const filesContent = document.querySelector('.result-text').value;
    const fullDigest = `${directoryStructure}\n\nFiles Content:\n\n${filesContent}`;
    const button = document.querySelector('[onclick="copyFullDigest()"]');
    const originalText = button.innerHTML;

    navigator.clipboard.writeText(fullDigest).then(() => {
        button.innerHTML = `
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            Copied!
        `;

        setTimeout(() => {
            button.innerHTML = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}

function downloadFullDigest() {
    const summary = document.getElementById('result-summary').value;
    const directoryStructure = document.getElementById('directory-structure-content').value;
    const filesContent = document.querySelector('.result-text').value;

    // Create the full content with all three sections
    const fullContent = `${summary}\n${directoryStructure}\n${filesContent}`;

    // Create a blob with the content
    const blob = new Blob([fullContent], { type: 'text/plain' });

    // Create a download link
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'codebase-digest.txt';
    document.body.appendChild(a);
    a.click();

    // Clean up
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    // Show feedback on the button
    const button = document.querySelector('[onclick="downloadFullDigest()"]');
    const originalText = button.innerHTML;

    button.innerHTML = `
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
        </svg>
        Downloaded!
    `;

    setTimeout(() => {
        button.innerHTML = originalText;
    }, 2000);
}

// Add the logSliderToSize helper function
function logSliderToSize(position) {
    const maxPosition = 500;
    const maxValue = Math.log(102400); // 100 MB

    const value = Math.exp(maxValue * Math.pow(position / maxPosition, 1.5));
    return Math.round(value);
}

// Move slider initialization to a separate function
function initializeSlider() {
    const slider = document.getElementById('file_size');
    const sizeValue = document.getElementById('size_value');

    if (!slider || !sizeValue) return;

    function updateSlider() {
        const value = logSliderToSize(slider.value);
        sizeValue.textContent = formatSize(value);
        slider.style.backgroundSize = `${(slider.value / slider.max) * 100}% 100%`;
    }

    // Update on slider change
    slider.addEventListener('input', updateSlider);

    // Initialize slider position
    updateSlider();
}

// Add helper function for formatting size
function formatSize(sizeInKB) {
    if (sizeInKB >= 1024) {
        return Math.round(sizeInKB / 1024) + 'MB';
    }
    return Math.round(sizeInKB) + 'kB';
}

// Make sure these are available globally
window.copyText = copyText;

window.handleSubmit = handleSubmit;
window.initializeSlider = initializeSlider;
window.formatSize = formatSize;
window.downloadFullDigest = downloadFullDigest;

// Add this new function
function setupGlobalEnterHandler() {
    document.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' && !event.target.matches('textarea')) {
            const form = document.getElementById('ingestForm');
            if (form) {
                handleSubmit(new Event('submit'), true);
            }
        }
    });
}

// Add to the DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', () => {
    initializeSlider();
    setupGlobalEnterHandler();
});
