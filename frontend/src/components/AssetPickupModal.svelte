<!-- components/AssetPickupModal.svelte -->
<script>
    export let isOpen = false;
    export let assignmentId = null;
    export let assetName = '';
    import { showToast } from '../stores/toast.js';
    export let onConfirm;
    
    let pickupFile = null;
    let isSubmitting = false;
    
    function handleFileChange(event) {
        pickupFile = event.target.files[0];
    }
    
    async function handleSubmit() {
        if (isSubmitting) return;
        
        isSubmitting = true;
        
        try {
            const formData = new FormData();
            if (pickupFile) {
                formData.append('file', pickupFile);
            }
            
            const response = await fetch(`/api/asset-assignments/${assignmentId}/pickup`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            });
            
            if (response.ok) {
                onConfirm();
                closeModal();
            } else {
                showToast('Failed to confirm pickup', 'error');
            }
        } catch (error) {
            console.error('Pickup error:', error);
            showToast('Failed to confirm pickup', 'error');
        } finally {
            isSubmitting = false;
        }
    }
    
    function closeModal() {
        isOpen = false;
        pickupFile = null;
        isSubmitting = false;
    }
    
    function handleKeydown(event) {
        if (event.key === 'Escape') {
            closeModal();
        }
    }
</script>

{#if isOpen}
    <div class="fixed inset-0 z-50 overflow-y-auto" on:keydown={handleKeydown}>
        <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div class="relative inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                    <div class="sm:flex sm:items-start">
                        <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                            <h3 class="text-lg leading-6 font-medium text-gray-900">
                                Confirm Equipment Pickup
                            </h3>
                            <div class="mt-2">
                                <p class="text-sm text-gray-500">
                                    Please confirm you have picked up <strong>{assetName}</strong> and optionally upload evidence.
                                </p>
                            </div>
                            
                            <!-- File Upload -->
                            <div class="mt-4">
                                <label for="pickup-file-upload" class="block text-sm font-medium text-gray-700">
                                    Pickup Evidence (Optional)
                                </label>
                                <div class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                                    <div class="space-y-1 text-center">
                                        <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                                            <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                        </svg>
                                        <div class="flex text-sm text-gray-600">
                                            <label 
                                                for="pickup-file-upload" 
                                                class="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                                            >
                                                <span>Upload a file</span>
                                                <input 
                                                    id="pickup-file-upload" 
                                                    name="pickup-file-upload" 
                                                    type="file" 
                                                    class="sr-only" 
                                                    accept="image/*,.pdf" 
                                                    on:change={handleFileChange} 
                                                />
                                            </label>
                                            <p class="pl-1">PNG, JPG, GIF up to 10MB</p>
                                        </div>
                                    </div>
                                </div>
                                
                                {#if pickupFile}
                                    <div class="mt-2 text-sm text-gray-600">
                                        Selected: {pickupFile.name}
                                    </div>
                                {/if}
                            </div>
                        </div>
                        
                        <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                            <button
                                type="button"
                                on:click={closeModal}
                                disabled={isSubmitting}
                                class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm"
                            >
                                Cancel
                            </button>
                            <button
                                type="button"
                                on:click={handleSubmit}
                                disabled={isSubmitting}
                                class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:w-auto sm:text-sm disabled:opacity-50"
                            >
                                {#if isSubmitting}
                                    <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a8 8 0 01-8 8H4a8 8 0 00-8-8v4a8 8 0 008 8z"></path>
                                    </svg>
                                    Confirming...
                                {:else}
                                    Confirm Pickup
                                {/if}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
{/if}
