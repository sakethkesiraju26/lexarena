#!/usr/bin/env python3
"""
Update cases.html to display Gemini reasoning when cases expand.
This updates the renderCases JavaScript function to use geminiPredictions.
"""

import re

def update_gemini_reasoning():
    with open('cases.html', 'r') as f:
        html = f.read()
    
    # Step 1: Update the renderCases function to look up Gemini predictions
    # Find where Claude prediction is looked up and add Gemini lookup after it
    claude_lookup_pattern = r'(// Look up Claude prediction for this case\s+const claudePred = claudePredictions\[pred\.case_id\];\s+const claudeComp = claudePred \? claudePred\.comparison : null;)'
    
    if re.search(claude_lookup_pattern, html):
        # Add Gemini lookup after Claude lookup
        replacement = r'\1\n                \n                // Look up Gemini prediction for this case\n                const geminiPred = geminiPredictions[pred.case_id];\n                const geminiComp = geminiPred ? geminiPred.comparison : null;'
        html = re.sub(claude_lookup_pattern, replacement, html)
        print("✓ Added Gemini prediction lookup")
    else:
        print("⚠ Could not find Claude lookup pattern - Gemini lookup may already exist or pattern changed")
    
    # Step 2: Update fields array to include Gemini predictions
    # This is complex, so we'll need to find the fields definition and add geminiPred/geminiCorrect
    # For now, let's focus on the reasoning display which is simpler
    
    # Step 3: Update Gemini reasoning content to show actual reasoning
    # Find the Gemini reasoning div that shows "coming soon"
    gemini_reasoning_pattern = r'(<div id="reasoning-gemini-\$\{idx\}" class="reasoning-content \$\{activeModel === \'gemini\' \? \'active\' : \'\'\}">\s*<p class="coming-soon">Gemini evaluation coming soon</p>\s*</div>)'
    
    replacement_reasoning = r'''<div id="reasoning-gemini-${idx}" class="reasoning-content ${activeModel === 'gemini' ? 'active' : ''}">
                                ${geminiPred && geminiPred.predicted.reasoning ? `
                                    <p><strong>Resolution:</strong> ${geminiPred.predicted.reasoning.resolution_type || '—'}</p>
                                    <p><strong>Monetary:</strong> ${geminiPred.predicted.reasoning.monetary || '—'}</p>
                                    <p><strong>Remedial:</strong> ${geminiPred.predicted.reasoning.remedial_measures || '—'}</p>
                                ` : '<p class="coming-soon">Gemini evaluation not available for this case</p>'}
                            </div>'''
    
    if re.search(gemini_reasoning_pattern, html):
        html = re.sub(gemini_reasoning_pattern, replacement_reasoning, html)
        print("✓ Updated Gemini reasoning display")
    else:
        # Try alternative pattern
        alt_pattern = r'(<div id="reasoning-gemini-\$\{idx\}"[^>]*>[\s\S]*?coming soon[\s\S]*?</div>)'
        if re.search(alt_pattern, html):
            html = re.sub(alt_pattern, replacement_reasoning, html)
            print("✓ Updated Gemini reasoning display (alternative pattern)")
        else:
            print("⚠ Could not find Gemini reasoning placeholder - may already be updated")
    
    # Step 4: Update comparison table to show Gemini predictions
    # Find the Gemini column in the comparison table (currently shows "—")
    gemini_table_cell_pattern = r'(<td class="model-cell"><span class="cell-value na">—</span></td>\s*</tr>)'
    
    # This needs to be more sophisticated - we need to match the last cell before </tr>
    # Let's use a different approach - find the table row structure
    # Actually, this is complex because we need to inject geminiPred/geminiCorrect into the fields array
    # For now, let's just fix the reasoning display which is the main request
    
    # Write updated HTML
    with open('cases.html', 'w') as f:
        f.write(html)
    
    print("✓ Updated cases.html")
    print("\nNote: Full integration (comparison table) may require manual JavaScript updates")
    print("  The reasoning display should now work when cases expand!")

if __name__ == '__main__':
    update_gemini_reasoning()
