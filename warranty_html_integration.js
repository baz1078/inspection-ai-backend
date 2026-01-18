/*
WARRANTY FEATURE - HTML/JS ADDITION FOR index.html

This adds warranty upload and claims checking functionality.
It integrates with existing interface without breaking changes.

INTEGRATION POINTS:
1. After summary display - show option to upload warranty
2. In Q&A section - add "Check Warranty Claim" button
3. New screen state: 'warranty' for warranty analysis
4. New state variables for warranty tracking
*/

// ADD THESE TO STATE OBJECT (around line 150 in original index.html):

const state = {
    screen: 'upload',
    reportId: null,
    customerId: null,
    
    // === NEW WARRANTY FIELDS ===
    warrantyId: null,
    warrantyBuilderName: null,
    warrantyType: null,
    warranties: [],  // Array of linked warranties for report
    
    // Q&A state (existing)
    questions: [],
    currentQuestion: '',
    
    // ... rest of existing state
};

// ============================================================================
// WARRANTY UPLOAD SECTION - Add after summary screen
// ============================================================================

// In the renderSummaryScreen() function, add this after the summary display:

async function renderWarrantyUploadSection() {
    return `
    <div class="warranty-upload-section" style="margin-top: 40px; padding: 24px; background: linear-gradient(135deg, #fef3c7 0%, #fef08a 100%); border-radius: 12px; border-left: 4px solid #f59e0b;">
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
            <span style="font-size: 24px;">📋</span>
            <div>
                <h3 style="margin: 0; color: #92400e; font-weight: 600;">Have a Warranty Certificate?</h3>
                <p style="margin: 4px 0 0 0; color: #b45309; font-size: 14px;">Upload to check if findings are covered</p>
            </div>
        </div>
        
        <div id="warranty-upload-zone" style="
            border: 2px dashed #f59e0b;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
            cursor: pointer;
            background: rgba(255, 255, 255, 0.7);
            transition: all 0.3s ease;
        " 
        ondragover="this.style.backgroundColor='rgba(245, 158, 11, 0.1)'; this.style.borderColor='#d97706';"
        ondragleave="this.style.backgroundColor='rgba(255, 255, 255, 0.7)'; this.style.borderColor='#f59e0b';">
            <input type="file" id="warranty-file-input" accept=".pdf" style="display: none;">
            <label for="warranty-file-input" style="cursor: pointer;">
                <p style="margin: 0; color: #92400e; font-weight: 500;">Drag warranty PDF here or click to browse</p>
                <p style="margin: 8px 0 0 0; font-size: 13px; color: #b45309;">Supports Travelers, National Home Warranty, Dweller, and other builders</p>
            </label>
        </div>
        
        <div id="warranty-builder-select" style="margin-top: 12px; display: none;">
            <label style="display: block; margin-bottom: 6px; font-weight: 500; color: #92400e;">Builder/Warranty Company:</label>
            <input type="text" id="warranty-builder-name" placeholder="e.g., Travelers, National Home Warranty, Dweller" 
                   style="width: 100%; padding: 8px; border: 1px solid #d97706; border-radius: 6px; font-size: 14px;">
            
            <label style="display: block; margin-top: 12px; margin-bottom: 6px; font-weight: 500; color: #92400e;">Warranty Type:</label>
            <input type="text" id="warranty-type" placeholder="e.g., 2-5-10, 10-year, Standard" 
                   style="width: 100%; padding: 8px; border: 1px solid #d97706; border-radius: 6px; font-size: 14px;">
            
            <button id="warranty-upload-btn" 
                    style="margin-top: 12px; background: #d97706; color: white; padding: 10px 16px; border: none; border-radius: 6px; cursor: pointer; font-weight: 500; width: 100%;">
                Upload Warranty
            </button>
        </div>
    </div>
    `;
}

// ============================================================================
// WARRANTY Q&A INTERFACE
// ============================================================================

async function renderWarrantyQASection() {
    if (!state.warrantyId) return '';
    
    return `
    <div class="warranty-qa-section" style="margin-top: 24px; padding: 16px; background: #f0f9ff; border-radius: 12px; border-left: 4px solid #0ea5e9;">
        <h4 style="margin-top: 0; color: #0c4a6e;">Warranty Claims Check</h4>
        
        <div style="background: white; padding: 12px; border-radius: 8px; margin-bottom: 12px; border: 1px solid #e0f2fe;">
            <strong>📋 ${state.warrantyBuilderName} - ${state.warrantyType}</strong>
        </div>
        
        <textarea id="warranty-question-input" 
                  placeholder="Ask about warranty coverage. Example: 'Is the electrical issue covered?'"
                  style="width: 100%; padding: 12px; border: 1px solid #0ea5e9; border-radius: 8px; font-size: 14px; min-height: 80px; resize: none;"></textarea>
        
        <button id="warranty-ask-btn" 
                style="margin-top: 12px; background: #0ea5e9; color: white; padding: 10px 16px; border: none; border-radius: 6px; cursor: pointer; font-weight: 500; width: 100%;">
            Check Coverage
        </button>
        
        <div id="warranty-results" style="margin-top: 16px;"></div>
    </div>
    `;
}

// ============================================================================
// WARRANTY CLAIM ANALYSIS CARD
// ============================================================================

function renderClaimAnalysis(analysis) {
    const statusColor = {
        'COVERED': '#10b981',
        'NOT_COVERED': '#ef4444',
        'PARTIAL': '#f59e0b',
        'REQUIRES_SPECIALIST': '#8b5cf6'
    };
    
    const color = statusColor[analysis.claimability] || '#6b7280';
    
    return `
    <div style="
        background: white;
        border-left: 4px solid ${color};
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        border: 1px solid #e5e7eb;
    ">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span style="
                background: ${color};
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
            ">
                ${analysis.claimability}
            </span>
            ${analysis.coverage_period ? `<span style="font-size: 13px; color: #6b7280;">${analysis.coverage_period}</span>` : ''}
        </div>
        
        ${analysis.warranty_section ? `
            <div style="margin-bottom: 8px;">
                <strong style="color: #1f2937;">Warranty Section:</strong>
                <p style="margin: 4px 0 0 0; color: #4b5563; font-size: 13px;">${analysis.warranty_section}</p>
            </div>
        ` : ''}
        
        <div style="margin-bottom: 8px;">
            <strong style="color: #1f2937;">Why:</strong>
            <p style="margin: 4px 0 0 0; color: #4b5563; font-size: 13px; line-height: 1.5;">${analysis.reasoning}</p>
        </div>
        
        ${analysis.next_steps && analysis.next_steps.length > 0 ? `
            <div>
                <strong style="color: #1f2937;">Next Steps:</strong>
                <ol style="margin: 6px 0 0 20px; padding: 0; color: #4b5563; font-size: 13px;">
                    ${analysis.next_steps.map(step => `<li style="margin-bottom: 4px;">${step}</li>`).join('')}
                </ol>
            </div>
        ` : ''}
    </div>
    `;
}

// ============================================================================
// EVENT LISTENERS - Add these to initialization
// ============================================================================

function initWarrantyListeners() {
    // Warranty file input
    const warrantyFileInput = document.getElementById('warranty-file-input');
    const warrantyUploadZone = document.getElementById('warranty-upload-zone');
    
    if (warrantyFileInput && warrantyUploadZone) {
        warrantyUploadZone.addEventListener('click', () => warrantyFileInput.click());
        
        warrantyFileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                const builderSelect = document.getElementById('warranty-builder-select');
                if (builderSelect) builderSelect.style.display = 'block';
            }
        });
        
        // Drag and drop
        warrantyUploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            warrantyFileInput.files = e.dataTransfer.files;
            const builderSelect = document.getElementById('warranty-builder-select');
            if (builderSelect) builderSelect.style.display = 'block';
        });
    }
    
    // Warranty upload button
    const warrantyUploadBtn = document.getElementById('warranty-upload-btn');
    if (warrantyUploadBtn) {
        warrantyUploadBtn.addEventListener('click', uploadWarrantyFile);
    }
    
    // Warranty Q&A button
    const warrantyAskBtn = document.getElementById('warranty-ask-btn');
    if (warrantyAskBtn) {
        warrantyAskBtn.addEventListener('click', askWarrantyQuestion);
    }
}

async function uploadWarrantyFile() {
    const fileInput = document.getElementById('warranty-file-input');
    const builderName = document.getElementById('warranty-builder-name').value;
    const warrantyType = document.getElementById('warranty-type').value;
    
    if (!fileInput.files[0]) {
        alert('Please select a warranty PDF');
        return;
    }
    
    if (!builderName || !warrantyType) {
        alert('Please enter builder name and warranty type');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('builder_name', builderName);
    formData.append('warranty_type', warrantyType);
    formData.append('jurisdiction', 'USA');  // Could be dynamic
    
    try {
        const uploadBtn = document.getElementById('warranty-upload-btn');
        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Uploading and parsing...';
        
        const response = await fetch(`${API_URL}/api/upload-warranty/${state.reportId}`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Upload failed');
        
        const result = await response.json();
        
        state.warrantyId = result.warranty_id;
        state.warrantyBuilderName = result.builder_name;
        state.warrantyType = result.warranty_type;
        
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Upload Warranty';
        
        // Hide upload section, show Q&A section
        const uploadZone = document.getElementById('warranty-upload-zone');
        const builderSelect = document.getElementById('warranty-builder-select');
        if (uploadZone) uploadZone.style.display = 'none';
        if (builderSelect) builderSelect.style.display = 'none';
        
        render();  // Re-render to show warranty Q&A
        
    } catch (error) {
        console.error('Error uploading warranty:', error);
        alert('Error uploading warranty: ' + error.message);
        const uploadBtn = document.getElementById('warranty-upload-btn');
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Upload Warranty';
    }
}

async function askWarrantyQuestion() {
    const question = document.getElementById('warranty-question-input').value.trim();
    
    if (!question) {
        alert('Please enter a question');
        return;
    }
    
    if (!state.warrantyId) {
        alert('Please upload a warranty first');
        return;
    }
    
    try {
        const btn = document.getElementById('warranty-ask-btn');
        btn.disabled = true;
        btn.textContent = 'Analyzing...';
        
        const response = await fetch(`${API_URL}/api/warranty-ask/${state.reportId}/${state.warrantyId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        
        if (!response.ok) throw new Error('Analysis failed');
        
        const result = await response.json();
        const resultsDiv = document.getElementById('warranty-results');
        
        if (resultsDiv) {
            resultsDiv.innerHTML += `
                <div style="margin-bottom: 16px;">
                    <div style="background: #f3f4f6; padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                        <strong>${question}</strong>
                    </div>
                    <div style="background: white; padding: 12px; border-radius: 8px; border: 1px solid #e5e7eb; line-height: 1.6; color: #374151;">
                        ${result.answer.replace(/\n/g, '<br>')}
                    </div>
                </div>
            `;
        }
        
        document.getElementById('warranty-question-input').value = '';
        btn.disabled = false;
        btn.textContent = 'Check Coverage';
        
    } catch (error) {
        console.error('Error asking warranty question:', error);
        alert('Error: ' + error.message);
        const btn = document.getElementById('warranty-ask-btn');
        btn.disabled = false;
        btn.textContent = 'Check Coverage';
    }
}

// ============================================================================
// INTEGRATION NOTE
// ============================================================================

/*
TO INTEGRATE INTO index.html:

1. Add state variables (lines marked === NEW WARRANTY FIELDS ===)

2. In the render() function, after renderSummaryScreen():
   - Add await renderWarrantyUploadSection() to show warranty upload UI
   - Add await renderWarrantyQASection() to show warranty Q&A after upload

3. In the render() initialization, add:
   - initWarrantyListeners() to attach event listeners

4. That's it! Everything else is non-breaking.
*/
