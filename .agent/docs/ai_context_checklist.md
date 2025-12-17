# Antigravity Context Checklist

Checklist này giúp bạn verify những gì Antigravity AI đọc/hiểu khi code.

## 📋 Context Sources

### 1. **Workflows** (Explicit Instructions)
Khi bạn nói "follow workflow X", tôi sẽ đọc:

- [ ] `custom_addons/.agent/workflows/create_new_module.md`
- [ ] `custom_addons/.agent/workflows/create_adk_agent.md`

**Verify:**
```bash
# Check workflow exists
ls -lh custom_addons/.agent/workflows/

# Check file size (should be < 12000 chars for optimal AI reading)
wc -c custom_addons/.agent/workflows/*.md
```

### 2. **Documentation** (Reference Material)
Tôi reference khi cần specific info:

- [ ] `custom_addons/.agent/docs/naming_conventions.md` - Naming rules
- [ ] `custom_addons/.agent/docs/google_adk_reference.md` - ADK patterns
- [ ] `custom_addons/.agent/docs/cython_compilation.md` - Compilation
- [ ] `custom_addons/.agent/docs/google_adk_llms.txt` - Full ADK docs

**Verify:**
```bash
# List all docs
ls -lh custom_addons/.agent/docs/

# Check if readable
head -20 custom_addons/.agent/docs/naming_conventions.md
```

### 3. **Existing Codebase** (Learning Patterns)
Tôi scan existing modules để học:

- [ ] Module structure patterns
- [ ] Naming conventions in practice
- [ ] Code style and formatting
- [ ] Common patterns (models, views, controllers)

**Verify:**
```bash
# List existing modules
ls -d custom_addons/trcf_*/

# Check a reference module structure
tree -L 2 custom_addons/trcf_kitchen_screen/
```

### 4. **Conversation History**
Tôi nhớ:

- [ ] Previous discussions in this conversation
- [ ] Files viewed/created
- [ ] Decisions made
- [ ] Requirements clarified

**Verify:** Scroll up conversation history

### 5. **Current State** (Metadata)
Tôi nhận:

- [ ] Files you have open
- [ ] Cursor position
- [ ] Recent file edits
- [ ] Current directory

**Verify:** Check "ADDITIONAL_METADATA" in conversation

---

## 🎯 **Cách cải thiện Context cho AI:**

### A. **Explicit Instructions**
✅ **Good:**
```
"Hãy follow workflow trong custom_addons/.agent/workflows/create_new_module.md
và tạo module trcf_inventory_manager"
```

❌ **Less Clear:**
```
"Tạo module inventory manager"
```

### B. **Reference Docs**
✅ **Good:**
```
"Follow naming conventions trong custom_addons/.agent/docs/naming_conventions.md"
```

### C. **Point to Examples**
✅ **Good:**
```
"Tạo module tương tự trcf_kitchen_screen nhưng cho inventory"
```

### D. **Provide Context**
✅ **Good:**
```
"Tạo module quản lý inventory với:
- Model: trcf.inventory.check
- Fields: product_id, quantity, location_id
- Views: tree, form, kanban
- Tích hợp với stock module"
```

---

## 🔍 **Test: Verify AI Context**

### Test 1: Check Workflows
```bash
# Workflows should be concise (< 12000 chars)
wc -c custom_addons/.agent/workflows/*.md

# Should output:
# ~10000 create_new_module.md
# ~11000 create_adk_agent.md
```

### Test 2: Check Docs Readability
```bash
# Docs should be well-structured markdown
head -50 custom_addons/.agent/docs/naming_conventions.md
```

### Test 3: Check Example Modules
```bash
# AI learns from these
ls -la custom_addons/trcf_kitchen_screen/
ls -la custom_addons/trcf_payment_momo/
```

### Test 4: Verify File Sizes
```bash
# All files should be reasonable size
find custom_addons/.agent -type f -name "*.md" -exec wc -c {} \;
```

---

## 📊 **Context Priority**

Khi tôi code, tôi ưu tiên theo thứ tự:

1. **Explicit user instructions** (highest priority)
2. **Workflows** (if referenced)
3. **Conversation history** (recent context)
4. **Documentation** (reference material)
5. **Existing code patterns** (learning)
6. **Built-in knowledge** (fallback)

---

## 💡 **Tips để AI code tốt hơn:**

### 1. **Be Specific**
```
❌ "Tạo module mới"
✅ "Follow workflow create_new_module.md, tạo module trcf_product_manager 
    với model trcf.product.manager, fields: name, category_id, price"
```

### 2. **Reference Workflows**
```
✅ "Hãy đọc custom_addons/.agent/workflows/create_adk_agent.md 
    trước khi tạo module"
```

### 3. **Point to Examples**
```
✅ "Tạo views tương tự trcf_kitchen_screen/views/trcf_kitchen_screen_views.xml"
```

### 4. **Provide Context Files**
```
✅ "Xem file custom_addons/trcf_payment_momo/models/trcf_pos_payment_method.py
    để hiểu pattern, rồi tạo tương tự"
```

### 5. **Iterative Refinement**
```
✅ "Tạo basic structure trước, sau đó tôi sẽ review và bổ sung"
```

---

## 🧪 **Experiment: Test AI Understanding**

Try these commands to see what AI reads:

```bash
# 1. Show what workflows exist
ls -lh custom_addons/.agent/workflows/

# 2. Show what docs exist
ls -lh custom_addons/.agent/docs/

# 3. Show example modules
ls -d custom_addons/trcf_*/

# 4. Check workflow content
head -100 custom_addons/.agent/workflows/create_new_module.md

# 5. Check naming conventions
grep "^##" custom_addons/.agent/docs/naming_conventions.md
```

---

## ✅ **Verification Checklist**

Before asking AI to code:

- [ ] Workflows exist and are < 12000 chars
- [ ] Docs are well-structured and readable
- [ ] Example modules are available
- [ ] Instructions are clear and specific
- [ ] Context is provided (requirements, examples)

---

## 📚 **Files to Check**

Essential files for AI context:

```
custom_addons/.agent/
├── README.md                       # Overview
├── workflows/
│   ├── create_new_module.md       # Standard module workflow
│   └── create_adk_agent.md        # ADK agent workflow
├── docs/
│   ├── naming_conventions.md      # Naming rules
│   ├── google_adk_reference.md    # ADK guide
│   └── cython_compilation.md      # Compilation strategy
└── (future)
    ├── templates/                  # Code templates
    └── scripts/                    # Automation scripts
```

**Verify all exist:**
```bash
find custom_addons/.agent -type f -name "*.md" | sort
```
