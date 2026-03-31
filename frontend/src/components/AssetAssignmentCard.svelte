<!-- components/AssetAssignmentCard.svelte -->
<script>
    export let assignment;
    export let showActions = true;
    
    let showPickupModal = false;
    let showReturnModal = false;
    let pickupFile = null;
    let returnFile = null;
    
    import { onMount } from 'svelte';
    import { showToast } from '../stores/toast.js';
    
    function getStatusColor(status) {
        switch (status) {
            case 'REQUESTED':
                return 'bg-yellow-100 text-yellow-800';
            case 'ASSIGNED':
                return 'bg-blue-100 text-blue-800';
            case 'RETURNED':
                return 'bg-green-100 text-green-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }
    
    function getStatusText(status) {
        switch (status) {
            case 'REQUESTED':
                return 'Awaiting Pickup';
            case 'ASSIGNED':
                return 'In My Possession';
            case 'RETURNED':
                return 'Returned';
            default:
                return status;
        }
    }
    
    function openPickupModal() {
        showPickupModal = true;
    }
    
    function closePickupModal() {
        showPickupModal = false;
        pickupFile = null;
    }
    
    function openReturnModal() {
        showReturnModal = true;
    }
    
    function closeReturnModal() {
        showReturnModal = false;
        returnFile = null;
    }
    
    async function confirmPickup() {
        try {
            const formData = new FormData();
            if (pickupFile) {
                formData.append('file', pickupFile);
            }
            
            const response = await fetch(`/api/asset-assignments/${assignment.id}/pickup`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            });
            
            if (response.ok) {
                // Refresh the assignment data
                window.location.reload();
            } else {
                showToast('Failed to confirm pickup', 'error');
            }
        } catch (error) {
            console.error('Pickup confirmation error:', error);
            showToast('Failed to confirm pickup', 'error');
        }
        
        closePickupModal();
    }
    
    async function confirmReturn() {
        try {
            const formData = new FormData();
            if (returnFile) {
                formData.append('file', returnFile);
            }
            
            const response = await fetch(`/api/asset-assignments/${assignment.id}/return`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            });
            
            if (response.ok) {
                // Refresh the assignment data
                window.location.reload();
            } else {
                showToast('Failed to confirm return', 'error');
            }
        } catch (error) {
            console.error('Return confirmation error:', error);
            showToast('Failed to confirm return', 'error');
        }
        
        closeReturnModal();
    }
</script>

<div class="bg-white p-6 rounded-lg shadow border border-gray-200">
    <!-- Asset Information -->
    <div class="flex items-start space-x-4">
        <div class="flex-shrink-0">
            {#if assignment.asset}
                <div class="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center">
                    <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2v-4a2 2 0 012-2h6a2 2 0 012 2v4a2 2 0 01-2 2h6a2 2 0 002-2v-4a2 2 0 00-2-2z"/>
                    </svg>
                </div>
            {/if}
        </div>
        
        <div class="flex-1 min-w-0">
            {#if assignment.asset}
                <h3 class="text-lg font-medium text-gray-900">{assignment.asset.name}</h3>
                    <div class="mt-1 flex items-center space-x-2">
                            <span class="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">
                                    {assignment.asset.category}
                            </span>
                            <span class="text-sm text-gray-500">
                                    Tag: {assignment.asset.asset_tag}
                            </span>
                    </div>
            {/if}
            
            <!-- Assignment Status -->
            <div class="mt-3 flex items-center space-x-2">
                    <span class="px-3 py-1 text-sm font-medium rounded-full {getStatusColor(assignment.status)}">
                            {getStatusText(assignment.status)}
                    </span>
                    
                    {#if assignment.assigned_at}
                        <span class="text-sm text-gray-500">
                                Assigned on {new Date(assignment.assigned_at).toLocaleDateString()}
                        </span>
                    {/if}
            </div>
        </div>
    </div>
    
    <!-- Assignment Details -->
    {#if assignment.task}
        <div class="mt-4 pt-4 border-t border-gray-200">
                <div class="text-sm text-gray-600">
                        <div class="flex justify-between">
                                <span>Task:</span>
                                <span class="font-medium text-gray-900">{assignment.task.title}</span>
                        </div>
                        {#if assignment.assigned_user}
                                <div class="flex justify-between mt-1">
                                        <span>Assigned to:</span>
                                        <span class="font-medium text-gray-900">{assignment.assigned_user.name}</span>
                                </div>
                        {/if}
                        {#if assignment.notes}
                                <div class="mt-2">
                                        <span class="font-medium">Notes:</span>
                                        <p class="mt-1 text-gray-700">{assignment.notes}</p>
                                </div>
                        {/if}
                </div>
        </div>
    {/if}
    
    <!-- Action Buttons -->
    {#if showActions}
        <div class="mt-6 flex space-x-3">
                {#if assignment.status === 'REQUESTED'}
                        <button
                                type="button"
                                on:click={openPickupModal}
                                class="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M8 11V7a4 4 0 00-8 0v4m16 0v4a2 2 0 01-2 2H6a2 2 0 01-2-2V7a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2z"/>
                                </svg>
                                Confirm Pickup
                        </button>
                {/if}
                
                {#if assignment.status === 'ASSIGNED'}
                        <button
                                type="button"
                                on:click={openReturnModal}
                                class="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                        >
                                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4a1 1 0 110-2H7a1 1 0 110 2v8a1 1 0 110 2h8a1 1 0 110-2V7a1 1 0 00-1-1z"/>
                                </svg>
                                Confirm Return
                        </button>
                {/if}
        </div>
    {/if}
    
    <!-- Evidence Upload Modals -->
    
    <!-- Pickup Confirmation Modal -->
    {#if showPickupModal}
        <div class="fixed inset-0 z-50 overflow-y-auto">
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
                                                                        Please confirm you have picked up the equipment and optionally upload evidence (photo or QR scan).
                                                                </p>
                                                        </div>
                                                        
                                                        <!-- File Upload -->
                                                        <div class="mt-4">
                                                                <label class="block text-sm font-medium text-gray-700">
                                                                        Pickup Evidence (Optional)
                                                                </label>
                                                                <div class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                                                                        <div class="space-y-1 text-center">
                                                                                <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                                                                                        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                                                                </svg>
                                                                                <div class="flex text-sm text-gray-600">
                                                                                        <label for="pickup-file-upload" class="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
                                                                                                <span>Upload a file</span>
                                                                                                <input id="pickup-file-upload" name="pickup-file-upload" type="file" class="sr-only" accept="image/*,.pdf" on:change={(e) => pickupFile = e.target.files[0]} />
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
                                                                        on:click={closePickupModal}
                                                                        class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm"
                                                        >
                                                                Cancel
                                                        </button>
                                                        <button
                                                                        type="button"
                                                                        on:click={confirmPickup}
                                                                        class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:w-auto sm:text-sm"
                                                        >
                                                                Confirm Pickup
                                                        </button>
                                                </div>
                                        </div>
                                </div>
                        </div>
                </div>
        </div>
    {/if}
    
    <!-- Return Confirmation Modal -->
    {#if showReturnModal}
        <div class="fixed inset-0 z-50 overflow-y-auto">
                <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                        <div class="relative inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                                <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                                        <div class="sm:flex sm:items-start">
                                                <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                                                        <h3 class="text-lg leading-6 font-medium text-gray-900">
                                                                Confirm Equipment Return
                                                        </h3>
                                                        <div class="mt-2">
                                                                <p class="text-sm text-gray-500">
                                                                        Please confirm you have returned the equipment and upload evidence (photo or handover proof).
                                                                </p>
                                                        </div>
                                                        
                                                        <!-- File Upload -->
                                                        <div class="mt-4">
                                                                <label class="block text-sm font-medium text-gray-700">
                                                                        Return Evidence (Optional)
                                                                </label>
                                                                <div class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                                                                        <div class="space-y-1 text-center">
                                                                                <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                                                                                        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                                                                </svg>
                                                                                <div class="flex text-sm text-gray-600">
                                                                                        <label for="return-file-upload" class="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
                                                                                                <span>Upload a file</span>
                                                                                                <input id="return-file-upload" name="return-file-upload" type="file" class="sr-only" accept="image/*,.pdf" on:change={(e) => returnFile = e.target.files[0]} />
                                                                                        </label>
                                                                                        <p class="pl-1">PNG, JPG, GIF up to 10MB</p>
                                                                                </div>
                                                                        </div>
                                                                </div>
                                                                
                                                                {#if returnFile}
                                                                        <div class="mt-2 text-sm text-gray-600">
                                                                                Selected: {returnFile.name}
                                                                        </div>
                                                                {/if}
                                                        </div>
                                                </div>
                                                
                                                <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                                                        <button
                                                                        type="button"
                                                                        on:click={closeReturnModal}
                                                                        class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm"
                                                        >
                                                                Cancel
                                                        </button>
                                                        <button
                                                                        type="button"
                                                                        on:click={confirmReturn}
                                                                        class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 sm:w-auto sm:text-sm"
                                                        >
                                                                Confirm Return
                                                        </button>
                                                </div>
                                        </div>
                                </div>
                        </div>
                </div>
        </div>
    {/if}
</div>
