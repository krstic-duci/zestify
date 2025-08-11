document.addEventListener('DOMContentLoaded', function () {
    const mealSections = document.querySelectorAll('.sortable-meal');

    /**
     * Initializes Sortable.js on all meal sections for drag-and-drop functionality.
     */
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

    /**
     * Calculate the position index for a given day and meal type.
     * Based on the POSITION_MAP from backend constants.
     */
    function calculatePosition(dayName, mealType) {
        const dayMapping = {
            'Monday': 0, 'Tuesday': 2, 'Wednesday': 4, 'Thursday': 6,
            'Friday': 8, 'Saturday': 10, 'Sunday': 12
        };
        
        const basePosition = dayMapping[dayName];
        if (basePosition === undefined) {
            throw new Error(`Invalid day: ${dayName}`);
        }
        
        const mealOffset = mealType === 'Lunch' ? 0 : 1;
        return basePosition + mealOffset;
    }

    /**
     * Handles drag-and-drop meal swapping in the weekly planner.
     * Allows swapping between ANY positions: Lunch, Dinner, or empty placeholders.
     * Uses Sortable.js for UI interactions and calls the backend API to swap meals.
     * On error, shows a notification and reverts the drag operation.
     */
    async function handleMealSwap(evt) {
        const draggedItem = evt.item;
        const fromContainer = evt.from;
        const toContainer = evt.to;
        const meal1_id = draggedItem.dataset.mealId;
        let meal2_id = null;
        
    // Extract day and meal type correctly from DOM structure
    const fromDayCard = fromContainer.closest('.day-card');
    const toDayCard = toContainer.closest('.day-card');
    const fromDay = fromDayCard ? fromDayCard.dataset.day : undefined;
    const toDay = toDayCard ? toDayCard.dataset.day : undefined;
    const fromMealType = fromContainer.dataset.meal;
    const toMealType = toContainer.dataset.meal;

        // Skip invalid meal IDs (but allow dragging placeholders!)
        if (!meal1_id) {
            return;
        }

        // If dragging within the same container
        if (fromContainer === toContainer) {
            // If we're not actually moving (same position), skip
            if (evt.oldIndex === evt.newIndex) {
                return;
            }
            // For same container swaps, find ANY other item to swap with
            const allItems = Array.from(toContainer.children).filter(child => 
                child.dataset && child.dataset.mealId && child.dataset.mealId !== meal1_id
            );
            // Just take the first available item (meal or placeholder)
            if (allItems.length > 0) {
                meal2_id = allItems[0].dataset.mealId;
            }
        } else {
            // Cross-container move - find ANY item in the target container
            const targetItems = Array.from(toContainer.children).filter(child => 
                child.dataset && child.dataset.mealId && child.dataset.mealId !== meal1_id
            );
            // Take the first available item (meal or placeholder)
            if (targetItems.length > 0) {
                meal2_id = targetItems[0].dataset.mealId;
            }
        }

        // Skip if trying to swap with itself
        if (meal1_id === meal2_id) {
            return;
        }

        try {
            let response;
            
            if (meal2_id) {
                // Both meals exist - use swap endpoint
                response = await apiClient('/swap-meals', {
                    body: { meal1_id, meal2_id }
                });
            } else {
                // Moving to empty position - calculate target position and move
                const targetPosition = calculatePosition(toDay, toMealType);
                response = await apiClient('/move-meal', {
                    body: { meal_id: meal1_id, target_position: targetPosition }
                });
            }
            
            if (response.status === 'error') {
                const errorMsg = response?.error?.message || response?.message || 'Meal swap failed.';
                showGlobalNotification(`Meal swap failed: ${errorMsg}`);
                revertSwap(draggedItem, fromContainer, evt.oldIndex);
                return;
            }
            
            if (response.status === 'success') {
                // Reload to reflect the changes
                location.reload();
            }
        } catch (error) {
            console.error('Error during meal swap:', error);
            showGlobalNotification(error?.message || 'Error during meal swap');
            revertSwap(draggedItem, fromContainer, evt.oldIndex);
        }
    }

    /**
     * Reverts a failed drag-and-drop swap by moving the dragged item back to its original position.
     */
    function revertSwap(draggedItem, fromContainer, oldIndex) {
        // Remove from current position
        if (draggedItem.parentNode) {
            draggedItem.parentNode.removeChild(draggedItem);
        }
        
        // Insert back at the original position
        const children = Array.from(fromContainer.children);
        if (oldIndex >= children.length) {
            fromContainer.appendChild(draggedItem);
        } else {
            fromContainer.insertBefore(draggedItem, children[oldIndex]);
        }
    }

    /**
     * Entry point for weekly planner JS logic.
     */
    function init() {
        initializeSortable();
    }

    init();
});