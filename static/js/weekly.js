// Weekly meal planning functionality

document.addEventListener('DOMContentLoaded', function () {
    // DOM elements
    const mealSections = document.querySelectorAll('.sortable-meal');

    // Initialize SortableJS for drag and drop
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

    // Handle the meal swap
    async function handleMealSwap(evt) {
        const draggedItem = evt.item;
        const fromContainer = evt.from;
        const toContainer = evt.to;
        
        // Get meal IDs from the dragged elements
        const meal1_id = draggedItem.dataset.mealId;
        
        // Find the target position
        let meal2_id = null;
        const targetIndex = evt.newIndex;
        
        // Get all items in the target container
        const targetItems = Array.from(toContainer.children).filter(child => 
            child.dataset && child.dataset.mealId
        );
        
        if (targetItems.length > 1) {
            if (targetIndex === 0) {
                // If dropped at the beginning, use the second item
                meal2_id = targetItems[1].dataset.mealId;
            } else if (targetIndex >= targetItems.length - 1) {
                // If dropped at the end, use the second-to-last item
                meal2_id = targetItems[targetItems.length - 2].dataset.mealId;
            } else {
                // If dropped in the middle, use the item after
                meal2_id = targetItems[targetIndex + 1].dataset.mealId;
            }
        } else if (targetItems.length === 1) {
            // If only one item, we'll set it as empty position
            meal2_id = null;
        }
        
        if (!meal1_id) {
            console.error('No meal ID found for dragged item');
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
                console.error('Meal swap failed:', result.message);
                // Revert the drag operation
                revertSwap(draggedItem, fromContainer, toContainer);
            }
        } catch (error) {
            console.error('Error during meal swap:', error);
            // Revert the drag operation
            revertSwap(draggedItem, fromContainer, toContainer);
        }
    }

    // Revert a failed swap operation
    function revertSwap(draggedItem, fromContainer, toContainer) {
        if (fromContainer !== toContainer) {
            fromContainer.appendChild(draggedItem);
        }
    }

    // Error handling utility
    function handleError(error, userMessage = 'An error occurred') {
        console.error('Error:', error);
        
        // Show user-friendly error message
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
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }

    // Initialize all functionality
    function init() {
        initializeSortable();
    }

    // Start the application
    init();
});