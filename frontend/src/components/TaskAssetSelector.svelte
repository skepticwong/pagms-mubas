<!-- components/TaskAssetSelector.svelte -->
<script>
    export let task;
    export let availableAssets = [];
    export let selectedAssets = [];
    export let onAssetsChange;
    
    let showAssetRequest = false;
    let searchTerm = '';
    let filteredAssets = [];
    
    $: filteredAssets = availableAssets.filter(asset => 
        asset.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
        !selectedAssets.some(selected => selected.asset_id === asset.id)
    );
    
    function addAssetRequirement(asset) {
        const newAsset = {
            asset_id: asset.id,
            asset_name: asset.name,
            asset_tag: asset.asset_tag,
            category: asset.category,
            quantity: 1,
            notes: ''
        };
        
        selectedAssets = [...selectedAssets, newAsset];
        onAssetsChange(selectedAssets);
        searchTerm = '';
    }
    
    function removeAssetRequirement(index) {
        selectedAssets = selectedAssets.filter((_, i) => i !== index);
        onAssetsChange(selectedAssets);
    }
    
    function updateAssetRequirement(index, field, value) {
        selectedAssets = selectedAssets.map((asset, i) => 
            i === index ? { ...asset, [field]: value } : asset
        );
        onAssetsChange(selectedAssets);
    }
    
    function openAssetRequest() {
        showAssetRequest = true;
    }
    
    function closeAssetRequest() {
        showAssetRequest = false;
    }
</script>

<div class="space-y-4">
    <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900">Required Equipment</h3>
        <button
            type="button"
            on:click={openAssetRequest}
            class="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0 0v6m0 0v6m0 0v6m9-3V9a3 3 0 00-3-3H9a3 3 0 00-3 3v12a3 3 0 003 3h12a3 3 0 003-3V9a3 3 0 00-3-3h-2zm-1 2a1 1 0 110-2H7a1 1 0 110 2v8a1 1 0 110 2h8a1 1 0 110-2V7a1 1 0 00-1-1z"/>
            </svg>
            Request New Asset
        </button>
    </div>
    
    <!-- Search and Add Assets -->
    <div class="space-y-3">
        <div class="relative">
            <input
                type="text"
                bind:value={searchTerm}
                placeholder="Search for equipment..."
                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <svg class="absolute right-3 top-2.5 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
        </div>
        
        <!-- Available Assets List -->
        {#if filteredAssets.length > 0}
            <div class="max-h-40 overflow-y-auto border border-gray-200 rounded-md">
                {#each filteredAssets as asset}
                    <div 
                        class="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-200 last:border-b-0"
                        on:click={() => addAssetRequirement(asset)}
                    >
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="font-medium text-gray-900">{asset.name}</div>
                                    <div class="text-sm text-gray-500">
                                            Tag: {asset.asset_tag} | Category: {asset.category}
                                    </div>
                            </div>
                            <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0 0v6m9-3V9a3 3 0 00-3-3H9a3 3 0 00-3 3v12a3 3 0 003 3h12a3 3 0 003-3V9a3 3 0 00-3-3h-2zm-1 2a1 1 0 110-2H7a1 1 0 110 2v8a1 1 0 110 2h8a1 1 0 110-2V7a1 1 0 00-1-1z"/>
                            </svg>
                        </div>
                    </div>
                {/each}
            </div>
        {:else if searchTerm && availableAssets.length === 0}
            <div class="text-center py-4 text-gray-500">
                No equipment found matching "{searchTerm}"
            </div>
        {/if}
    </div>
    
    <!-- Selected Assets -->
    {#if selectedAssets.length > 0}
        <div class="mt-6 space-y-3">
            <h4 class="text-md font-medium text-gray-900">Selected Equipment ({selectedAssets.length})</h4>
            
            {#each selectedAssets as selectedAsset, index}
                <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <div class="flex items-start justify-between">
                        <div class="flex-1 space-y-2">
                                <div class="flex items-center">
                                        <div class="font-medium text-gray-900">{selectedAsset.asset_name}</div>
                                                <span class="ml-2 px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                                                        {selectedAsset.category}
                                                </span>
                                </div>
                                <div class="text-sm text-gray-600">
                                        Tag: {selectedAsset.asset_tag}
                                </div>
                                
                                <div class="grid grid-cols-2 gap-3">
                                        <div>
                                                <label class="block text-sm font-medium text-gray-700">Quantity</label>
                                                <input
                                                                type="number"
                                                                min="1"
                                                                bind:value={selectedAsset.quantity}
                                                                on:change={(e) => updateAssetRequirement(index, 'quantity', parseInt(e.target.value))}
                                                                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                                                />
                                        </div>
                                        <div class="flex-1">
                                                <label class="block text-sm font-medium text-gray-700">Notes</label>
                                                <textarea
                                                                bind:value={selectedAsset.notes}
                                                                on:change={(e) => updateAssetRequirement(index, 'notes', e.target.value)}
                                                                rows="2"
                                                                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                                                />
                                        </div>
                                </div>
                        </div>
                        
                        <button
                            type="button"
                            on:click={() => removeAssetRequirement(index)}
                            class="ml-4 text-red-600 hover:text-red-900"
                        >
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116 21H8a2 2 0 01-2-2V5a2 2 0 012-2h8a2 2 0 012 2v9.142A2 2 0 0119 7z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            {/each}
        </div>
    {/if}
    
    <!-- Asset Request Modal -->
    {#if showAssetRequest}
        <div class="fixed inset-0 z-50 overflow-y-auto">
            <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div class="relative inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                    <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                                <div class="sm:flex sm:items-start">
                                        <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                                                <h3 class="text-lg leading-6 font-medium text-gray-900">
                                                        Request New Equipment
                                                </h3>
                                                <div class="mt-2">
                                                        <p class="text-sm text-gray-500">
                                                                If the required equipment is not available, you can request a new purchase or rental.
                                                        </p>
                                                </div>
                                        </div>
                                        
                                        <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                                                <button
                                                        type="button"
                                                        on:click={closeAssetRequest}
                                                        class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm"
                                                >
                                                        Cancel
                                                </button>
                                                <button
                                                        type="button"
                                                        class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:w-auto sm:text-sm"
                                                >
                                                        Open Asset Request Form
                                                </button>
                                        </div>
                                </div>
                    </div>
                </div>
            </div>
        </div>
    {/if}
</div>
