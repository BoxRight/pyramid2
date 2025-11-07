# Non-Essential UI Elements for Lawyers

## 🔴 REMOVE - Technical/Developer Features

### ContractReview Component
1. **"📊 Structure" button** - Visualization view (technical, lawyers don't need)
2. **"⚙️ Technical" button** - Code view (completely technical)
3. **View mode toggle entire section** - Lawyers only need document view
4. **"Validate Contract" button** - Should be automatic on contract creation
5. **"Analyze Contract" button** - Should be automatic after validation
6. **Code textarea/editor** - Lawyers shouldn't edit code directly
7. **Syntax highlighting preview** - Technical detail

### ContractAnalysis Component
1. **"📈 Visualization" layer button** - Technical visualization layer
2. **"📋 Details" layer button** - Can be accessed via "View Full Analysis" instead
3. **Layer navigation buttons** - Lawyers only need summary view by default
4. **Entire visualization layer** - Technical feature

### QueryInterface Component
1. **"Clear" button** - Not essential, lawyers can just ask another question
2. **"Back to Summary" button** - Can navigate via sidebar instead
3. **Manual query builder** - If examples work well, manual input is less needed:
   - Query type selector (violation/fulfillment buttons)
   - Obligation dropdown selector
   - Manual text input for predicate name
4. **"Get Answer" button** - Could auto-execute when obligation selected

### NaturalLanguageInput Component
1. **"Clear" button** - Nice to have but not essential
2. **Contract Type dropdown** - Could be auto-detected from description
3. **Jurisdiction dropdown** - Could default to most common or auto-detect

### ContractSummary Component
1. **"View Full Analysis" button** - Could be automatic or accessed differently
2. **Expand button for issues** - Could show all issues by default (no collapse needed)

### Sidebar Component
1. **"Start Over" button** - Not essential, lawyers can create new contract
2. **Recent Contracts list** - Depends on use case, might not be needed
3. **Workflow step navigation** - Could be simplified to just show current step

## 🟡 CONSIDER REMOVING - Nice to Have But Not Essential

### ContractReview Component
- Section info (line count, character count) - Technical detail

### QueryInterface Component
- Input hint text ("Or type the name of the obligation") - If examples are sufficient

### NaturalLanguageInput Component
- Example queries section - Actually helpful, but could be simplified

### ContractSummary Component
- Expand/collapse for issues - Could show all by default
- Separate "View Full Analysis" - Could integrate into summary

## 🟢 KEEP - Essential for Lawyers

### Must Keep Elements:
1. **Create Contract** - Primary action
2. **Document View** - Legal document display
3. **Summary View** - Status and key metrics
4. **Ask a Question** - Query interface
5. **Example Questions** - Recognition over recall
6. **Contract Status** - Answer first (valid/invalid)
7. **Critical Issues** - Problems that need attention
8. **Automatic Consequences** - What happens when obligations are met/not met

## 📋 Summary of Removals

### High Priority (Remove Immediately):
- All technical/code views
- View mode toggles
- Manual validation/analysis buttons (make automatic)
- Visualization layers
- Layer navigation buttons
- Manual query builder (rely on examples)
- Clear buttons
- Back navigation buttons (use sidebar)

### Medium Priority (Consider Removing):
- Contract Type/Jurisdiction dropdowns (auto-detect)
- Expand/collapse buttons (show all by default)
- Recent Contracts list
- Start Over button
- Technical metadata (line counts, etc.)

### Result:
A much simpler interface with:
1. **Create Contract** (natural language)
2. **View Contract** (document only)
3. **See Summary** (status + metrics)
4. **Ask Questions** (via examples mainly)

