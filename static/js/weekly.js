document.addEventListener('DOMContentLoaded', function () {
    const mealSections = document.querySelectorAll('.sortable-meal');

    function initializeSortable() {
        mealSections.forEach(section => {
            Sortable.create(section, {
                group: 'recipes',
                handle: '.drag-handle',
                animation: 150,
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                dragClass: 'sortable-drag',
                filter: 'h4, .no-recipe, .meal-selector',
                onEnd: function (evt) {
                    handleMealSwap(evt);
                }
            });
        });
    }

    async function handleMealSwap(evt) {
        const draggedItem = evt.item;
        const fromContainer = evt.from;
        const toContainer = evt.to;
        
        // Get meal IDs from the dragged elements
        const meal1_id = draggedItem.dataset.mealId;
        
        // Find the target position
        let meal2_id = null;
        const targetIndex = evt.newIndex;
        
        // Get all items in the target container, excluding the dragged item
        const targetItems = Array.from(toContainer.children).filter(child => 
            child.dataset && child.dataset.mealId && child !== draggedItem
        );
        
        // Determine meal2_id based on the drop position
        if (targetItems.length > 0) {
            if (targetIndex === 0) {
                // If dropped at the beginning, use the first item in the target container
                meal2_id = targetItems[0].dataset.mealId;
            } else if (targetIndex >= targetItems.length) {
                // If dropped at the end, use the last item in the target container
                meal2_id = targetItems[targetItems.length - 1].dataset.mealId;
            } else {
                // If dropped in the middle, use the item at the target index
                meal2_id = targetItems[targetIndex].dataset.mealId;
            }
        } else {
            // If no valid target items are found, log an error and exit
            handleError(null, "No valid meal found at the target position. Please try again.");
            return;
        }
        
        // Validate that both meal1_id and meal2_id are present
        if (!meal1_id || !meal2_id) {
            handleError(null, "Unable to swap meals. Please ensure both meals are valid.");
            return;
        }
        
        try {
            const response = await fetch('/swap-meals', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    meal1_id: meal1_id,
                    meal2_id: meal2_id
                })
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                // Optionally refresh the page to show updated positions
                location.reload();
            } else {
                handleError(null, `Meal swap failed: ${result.message}`);
                // Revert the drag operation
                revertSwap(draggedItem, fromContainer, toContainer);
            }
        } catch (error) {
            handleError(error, 'Error during meal swap');
            // Revert the drag operation
            revertSwap(draggedItem, fromContainer, toContainer);
        }
    }

    function revertSwap(draggedItem, fromContainer, toContainer) {
        if (fromContainer !== toContainer) {
            fromContainer.appendChild(draggedItem);
        }
    }

    function handleError(error, userMessage = 'An error occurred') {
        console.error('Error:', error);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-notification';
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #dc3545;
            color: white;
            padding: 12px 20px;
            border-radius: 4px;
            z-index: 1000;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        `;
        errorDiv.textContent = userMessage;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }

    function init() {
        initializeSortable();
    }

    init();
});