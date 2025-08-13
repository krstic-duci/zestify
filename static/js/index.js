document.addEventListener('DOMContentLoaded', function () {
    const textarea = document.getElementById('recipes_text');
    const formatStatus = document.getElementById('formatStatus');
    const autoFormatBtn = document.getElementById('autoFormatBtn');
    const clearBtn = document.getElementById('clearBtn');
    const addUrlBtn = document.getElementById('addUrlBtn');

    // Auto-format function
    function autoFormatContent(content) {
        if (!content.trim()) return content;

        const lines = content.split('\n').map(line => line.trim()).filter(line => line);
        const formatted = [];

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];

            // Check if line is a URL
            if (line.match(/^https?:\/\//)) {
                formatted.push(`# ${line}`);
            }
            // Check if line looks like an ingredient (not a URL and has content)
            else if (line && !line.startsWith('#')) {
                formatted.push(`## ${line}`);
            }
            // If it's already formatted, keep it as is
            else {
                formatted.push(line);
            }
        }

        return formatted.join('\n');
    }

    // Show status message
    function showStatus(message, duration = 2000) {
        formatStatus.textContent = message;
        formatStatus.classList.add('show');
        setTimeout(() => {
            formatStatus.classList.remove('show');
        }, duration);
    }

    // TODO: this never goes away
    // Auto-format on paste
    textarea.addEventListener('paste', function (e) {
        setTimeout(() => {
            const currentContent = textarea.value;
            const formatted = autoFormatContent(currentContent);

            if (formatted !== currentContent) {
                textarea.value = formatted;
                showStatus('✅ Content auto-formatted!');
            }
        }, 100);
    });

    // Manual format button
    autoFormatBtn.addEventListener('click', function () {
        const currentContent = textarea.value;
        const formatted = autoFormatContent(currentContent);
        textarea.value = formatted;
        showStatus('Content formatted!');
        textarea.focus();
    });

    // Clear button
    clearBtn.addEventListener('click', function () {
        textarea.value = '';
        showStatus('Content cleared!');
        textarea.focus();
    });

    // Add URL button
    addUrlBtn.addEventListener('click', function () {
        const url = prompt('Enter recipe URL:');
        if (url && url.trim()) {
            const currentContent = textarea.value;
            const newContent = currentContent ? `${currentContent}\n\n# ${url.trim()}\n## ` : `# ${url.trim()}\n## `;
            textarea.value = newContent;
            showStatus('URL added!');
            textarea.focus();
            // Position cursor after the "## " for easy ingredient entry
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
        }
    });

    function initializeResults(container) {
        const quantityUnitPattern = /^[\d½¼¾.,]+\s*(g|kg|ml|l|st|dl|cl|tsk|msk|krm|stk|styck|gram|kilo|liter|matsked|tesked|krm|burk|påse|förpackning)\s+/i;
        let copiedCount = 0;
        const listItems = container.querySelectorAll('li');
        const totalItemsEl = container.querySelector('#totalItems');
        const copiedItemsEl = container.querySelector('#copiedItems');
        const statsBar = container.querySelector('#statsBar');
        const clearResultsBtn = container.querySelector('#clearResultsBtn');
        const resultsContent = container.querySelector('#resultsContent');

        const extractIngredientName = (text) => {
            const cleanText = text.trim();
            const match = cleanText.match(quantityUnitPattern);
            if (match) {
                return cleanText.substring(match[0].length).trim();
            }
            const parts = cleanText.split(' ');
            if (parts.length >= 3) {
                return parts.slice(2).join(' ');
            } else if (parts.length === 2) {
                return parts[1];
            }
            return cleanText;
        };

        if (clearResultsBtn) {
            clearResultsBtn.addEventListener('click', () => {
                container.innerHTML = '';
                container.classList.remove('has-results');
            });
        }

        if (listItems.length > 0) {
            statsBar.style.display = 'flex';
            totalItemsEl.textContent = listItems.length;

            listItems.forEach(function (li) {
                const originalText = li.textContent;
                const ingredientName = extractIngredientName(originalText);
                const wrapper = document.createElement('div');
                wrapper.className = 'ingredient-item';
                const textSpan = document.createElement('span');
                textSpan.className = 'ingredient-text';
                textSpan.textContent = originalText;
                const copyBtn = document.createElement('button');
                copyBtn.className = 'copy-btn';
                copyBtn.textContent = 'Copy';
                copyBtn.setAttribute('aria-label', `Copy ${ingredientName}`);
                
                wrapper.appendChild(textSpan);
                wrapper.appendChild(copyBtn);
                li.innerHTML = '';
                li.appendChild(wrapper);
            });

            resultsContent.addEventListener('click', function (event) {
                const copyBtn = event.target.closest('.copy-btn');
                if (!copyBtn) return;

                const wrapper = copyBtn.closest('.ingredient-item');
                const textSpan = wrapper.querySelector('.ingredient-text');
                const ingredientName = extractIngredientName(textSpan.textContent);

                navigator.clipboard.writeText(ingredientName).then(function () {
                    const isAlreadyCopied = wrapper.dataset.copied === 'true';

                    if (!isAlreadyCopied) {
                        copyBtn.textContent = '✓ Copied!';
                        copyBtn.classList.add('copied');
                        textSpan.style.textDecoration = 'line-through';
                        textSpan.style.opacity = '0.6';
                        textSpan.style.color = 'var(--text-secondary)';
                        wrapper.dataset.copied = 'true';
                        wrapper.classList.add('item-copied');
                        copiedCount++;
                        copiedItemsEl.textContent = copiedCount;
                        setTimeout(function () {
                            copyBtn.textContent = '↩Undo';
                            copyBtn.classList.remove('copied');
                            copyBtn.classList.add('undo-btn');
                        }, 1500);
                    } else {
                        copyBtn.textContent = 'Copy';
                        copyBtn.classList.remove('undo-btn');
                        textSpan.style.textDecoration = 'none';
                        textSpan.style.opacity = '1';
                        textSpan.style.color = 'var(--text-primary)';
                        wrapper.dataset.copied = 'false';
                        wrapper.classList.remove('item-copied');
                        copiedCount--;
                        copiedItemsEl.textContent = copiedCount;
                    }
                }).catch(function (err) {
                    console.error('Failed to copy text: ', err);
                    copyBtn.textContent = 'Error';
                    setTimeout(function () {
                        copyBtn.textContent = 'Copy';
                    }, 1500);
                });
            });

        } else {
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            emptyState.innerHTML = `
                <h3>No ingredients processed yet</h3>
                <p>Go back and add some ingredients to see your shopping list here.</p>
            `;
            resultsContent.appendChild(emptyState);
        }
    }

    document.getElementById('recipeForm').addEventListener('submit', async function (event) {
        /**
         * Handles form submission for ingredient processing.
         * Calls the backend API and displays results or error banners.
         * On error, preserves textarea contents and shows a notification.
         */
        event.preventDefault();
        const button = document.querySelector('.submit-btn');
        const resultsContainer = document.getElementById('results-container');
        const recipesTextarea = document.getElementById('recipes_text');
        const haveAtHomeTextarea = document.getElementById('have_at_home');

        button.disabled = true;
        resultsContainer.innerHTML = '';

        const formData = new FormData(this);
        const data = {
            recipes_text: formData.get('recipes_text'),
            have_at_home: formData.get('have_at_home'),
        };

        const response = await apiClient('/ingredients', { body: data });

        if (response.status === 'error') {
            // Show error banner, preserve textarea contents
            const errorMsg = response?.error?.message || response?.message || 'An error occurred.';
            showGlobalNotification(errorMsg);
            button.disabled = false;
            return;
        }

        if (response.status === 'success') {
            resultsContainer.innerHTML = response.data?.ingredients_html || '';
            initializeResults(resultsContainer);
            recipesTextarea.value = '';
            haveAtHomeTextarea.value = '';
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        button.disabled = false;
    });

    // Live formatting hints
    textarea.addEventListener('input', function () {
        const content = textarea.value;
        const lines = content.split('\n');
        let hasUrls = false;
        let hasIngredients = false;

        lines.forEach(line => {
            if (line.match(/^https?:\/\//)) hasUrls = true;
            if (line.trim() && !line.startsWith('#') && !line.match(/^https?:\/\//)) hasIngredients = true;
        });

        if (hasUrls && hasIngredients && content.length > 50) {
            autoFormatBtn.style.background = 'var(--accent-green)';
            autoFormatBtn.style.color = 'var(--text-primary)';
            autoFormatBtn.style.borderColor = 'var(--accent-green)';
        } else {
            autoFormatBtn.style.background = 'var(--elevated-bg)';
            autoFormatBtn.style.color = 'var(--text-secondary)';
            autoFormatBtn.style.borderColor = 'var(--border-color)';
        }
    });
});