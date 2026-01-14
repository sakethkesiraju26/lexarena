#!/usr/bin/env python3
"""
Update cases.html to add Gemini metrics to the comparison table.
This updates the fields array and the table rendering.
"""

import re

def update_gemini_table():
    with open('cases.html', 'r') as f:
        html = f.read()
    
    # Step 1: Add geminiPred and geminiCorrect to each field in the fields array
    # Pattern: Find each field object and add Gemini data after Claude data
    
    # Resolution field
    resolution_pattern = r"(name: 'Resolution',\s+pred: pred\.predicted\.resolution_type,\s+actual: gt\.resolution_type,\s+correct: comp\.resolution_type_correct,\s+claudePred: claudePred \? claudePred\.predicted\.resolution_type : null,\s+claudeCorrect: claudeComp \? claudeComp\.resolution_type_correct : null)"
    resolution_replacement = r"\1,\n                        geminiPred: geminiPred ? geminiPred.predicted.resolution_type : null,\n                        geminiCorrect: geminiComp ? geminiComp.resolution_type_correct : null"
    
    html = re.sub(resolution_pattern, resolution_replacement, html)
    
    # Disgorgement field
    disgorgement_pattern = r"(name: 'Disgorgement',\s+pred: formatMoney\(pred\.predicted\.disgorgement_amount\),\s+actual: formatMoney\(gt\.disgorgement_amount\),\s+correct: comp\.disgorgement_correct,\s+claudePred: claudePred \? formatMoney\(claudePred\.predicted\.disgorgement_amount\) : null,\s+claudeCorrect: claudeComp \? claudeComp\.disgorgement_correct : null)"
    disgorgement_replacement = r"\1,\n                        geminiPred: geminiPred ? formatMoney(geminiPred.predicted.disgorgement_amount) : null,\n                        geminiCorrect: geminiComp ? geminiComp.disgorgement_correct : null"
    
    html = re.sub(disgorgement_pattern, disgorgement_replacement, html)
    
    # Penalty field
    penalty_pattern = r"(name: 'Penalty',\s+pred: formatMoney\(pred\.predicted\.penalty_amount\),\s+actual: formatMoney\(gt\.penalty_amount\),\s+correct: comp\.penalty_correct,\s+claudePred: claudePred \? formatMoney\(claudePred\.predicted\.penalty_amount\) : null,\s+claudeCorrect: claudeComp \? claudeComp\.penalty_correct : null)"
    penalty_replacement = r"\1,\n                        geminiPred: geminiPred ? formatMoney(geminiPred.predicted.penalty_amount) : null,\n                        geminiCorrect: geminiComp ? geminiComp.penalty_correct : null"
    
    html = re.sub(penalty_pattern, penalty_replacement, html)
    
    # Interest field
    interest_pattern = r"(name: 'Interest',\s+pred: formatMoney\(pred\.predicted\.prejudgment_interest\),\s+actual: formatMoney\(gt\.prejudgment_interest\),\s+correct: comp\.interest_correct,\s+claudePred: claudePred \? formatMoney\(claudePred\.predicted\.prejudgment_interest\) : null,\s+claudeCorrect: claudeComp \? claudeComp\.interest_correct : null)"
    interest_replacement = r"\1,\n                        geminiPred: geminiPred ? formatMoney(geminiPred.predicted.prejudgment_interest) : null,\n                        geminiCorrect: geminiComp ? geminiComp.interest_correct : null"
    
    html = re.sub(interest_pattern, interest_replacement, html)
    
    # Injunction field
    injunction_pattern = r"(name: 'Injunction',\s+pred: formatBoolean\(pred\.predicted\.has_injunction\),\s+actual: formatBoolean\(gt\.has_injunction\),\s+correct: comp\.injunction_correct,\s+claudePred: claudePred \? formatBoolean\(claudePred\.predicted\.has_injunction\) : null,\s+claudeCorrect: claudeComp \? claudeComp\.injunction_correct : null)"
    injunction_replacement = r"\1,\n                        geminiPred: geminiPred ? formatBoolean(geminiPred.predicted.has_injunction) : null,\n                        geminiCorrect: geminiComp ? geminiComp.injunction_correct : null"
    
    html = re.sub(injunction_pattern, injunction_replacement, html)
    
    # Officer Bar field
    officer_pattern = r"(name: 'Officer Bar',\s+pred: formatBoolean\(pred\.predicted\.has_officer_director_bar\),\s+actual: formatBoolean\(gt\.has_officer_director_bar\),\s+correct: comp\.officer_bar_correct,\s+claudePred: claudePred \? formatBoolean\(claudePred\.predicted\.has_officer_director_bar\) : null,\s+claudeCorrect: claudeComp \? claudeComp\.officer_bar_correct : null)"
    officer_replacement = r"\1,\n                        geminiPred: geminiPred ? formatBoolean(geminiPred.predicted.has_officer_director_bar) : null,\n                        geminiCorrect: geminiComp ? geminiComp.officer_bar_correct : null"
    
    html = re.sub(officer_pattern, officer_replacement, html)
    
    # Conduct field
    conduct_pattern = r"(name: 'Conduct',\s+pred: formatBoolean\(pred\.predicted\.has_conduct_restriction\),\s+actual: formatBoolean\(gt\.has_conduct_restriction\),\s+correct: comp\.conduct_restriction_correct,\s+claudePred: claudePred \? formatBoolean\(claudePred\.predicted\.has_conduct_restriction\) : null,\s+claudeCorrect: claudeComp \? claudeComp\.conduct_restriction_correct : null)"
    conduct_replacement = r"\1,\n                        geminiPred: geminiPred ? formatBoolean(geminiPred.predicted.has_conduct_restriction) : null,\n                        geminiCorrect: geminiComp ? geminiComp.conduct_restriction_correct : null"
    
    html = re.sub(conduct_pattern, conduct_replacement, html)
    
    # Step 2: Update the Gemini table cell to show actual data
    gemini_cell_pattern = r'<td class="model-cell"><span class="cell-value na">—</span></td>\s*</tr>'
    gemini_cell_replacement = r'''<td class="model-cell">
                                                ${f.geminiPred !== null ? `
                                                    <span class="cell-value ${f.geminiCorrect === true ? 'correct' : f.geminiCorrect === false ? 'incorrect' : 'na'}">
                                                        ${f.geminiPred}
                                                        ${f.geminiCorrect === true ? '<span class="check-icon">✓</span>' : ''}
                                                        ${f.geminiCorrect === false ? '<span class="x-icon">✗</span>' : ''}
                                                    </span>
                                                ` : '<span class="cell-value na">—</span>'}
                                            </td>
                                        </tr>'''
    
    html = re.sub(gemini_cell_pattern, gemini_cell_replacement, html)
    
    # Step 3: Update Gemini header badge (remove placeholder class if needed)
    gemini_header_pattern = r'<th class="model-header"><span class="model-badge placeholder">Gemini</span></th>'
    gemini_header_replacement = r'<th class="model-header"><span class="model-badge gemini">Gemini</span></th>'
    
    html = re.sub(gemini_header_pattern, gemini_header_replacement, html)
    
    # Write updated HTML
    with open('cases.html', 'w') as f:
        f.write(html)
    
    print("✓ Updated fields array to include Gemini predictions")
    print("✓ Updated comparison table to display Gemini metrics")
    print("✓ Updated Gemini header badge")

if __name__ == '__main__':
    update_gemini_table()
