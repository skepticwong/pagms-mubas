# ✅ Expense Icons Added to Icon Component!

## 🎨 **New Icons Added:**

### **1. expense Icon**
- **Purpose:** General expense/cost representation
- **Usage:** `<Icon name="expense" size={20} />`
- **Style:** Currency symbol with payment lines

### **2. money Icon** 
- **Purpose:** Money/cash/dollar amount
- **Usage:** `<Icon name="money" size={20} />`
- **Style:** Dollar sign in circle

### **3. receipt Icon**
- **Purpose:** Receipts, transactions, documentation
- **Usage:** `<Icon name="receipt" size={20} />`
- **Style:** Document/receipt shape

## 🚀 **How to Use:**

```svelte
<!-- Basic usage -->
<Icon name="expense" size={16} />
<Icon name="money" size={20} />
<Icon name="receipt" size={24} />

<!-- With custom styling -->
<Icon name="expense" size={18} class="text-green-600" />
<Icon name="money" size={16} class="text-blue-500" />

<!-- In buttons -->
<button class="flex items-center gap-2">
  <Icon name="expense" size={16} />
  Add Expense
</button>
```

## 📋 **Available Sizes:**
- `size={12}` - Extra small
- `size={16}` - Small (default for buttons)
- `size={20}` - Medium
- `size={24}` - Large
- `size={32}` - Extra large

## 🎯 **Perfect For:**
- **Expense forms** - Use `expense` icon
- **Budget displays** - Use `money` icon  
- **Transaction lists** - Use `receipt` icon
- **Financial summaries** - Mix of all three

## 🔧 **Complete Icon Library:**
Now the Icon component includes:
- ✅ `edit` - Edit/pencil
- ✅ `delete`/`trash` - Delete/trash
- ✅ `setting` - Settings/gear
- ✅ `expense` - Expense/currency (NEW)
- ✅ `money` - Money/dollar (NEW)
- ✅ `receipt` - Receipt/document (NEW)

**All financial icons are now available for use throughout the application!** 🎉
