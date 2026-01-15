/**
 * LexArena Prediction System
 * 
 * Allows users to make predictions on SEC cases and compare against AI models.
 * Uses Firebase Firestore for storing community predictions.
 */

// reCAPTCHA v3 Site Key
const RECAPTCHA_SITE_KEY = '6LedAUwsAAAAANi0RBfXLM074heqcW6wK57g6wBP';

// Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyCb9ZY9I5w5YjEXkxOR_EBHLesxCXFXUPo",
    authDomain: "lexarena-99c05.firebaseapp.com",
    projectId: "lexarena-99c05",
    storageBucket: "lexarena-99c05.firebasestorage.app",
    messagingSenderId: "301349897682",
    appId: "1:301349897682:web:f6d343522e3ccd10f3740b",
    measurementId: "G-NCX9L1QXZ0"
};

// Initialize Firebase (only if config is set)
let db = null;
let firebaseInitialized = false;

try {
    if (firebaseConfig.apiKey !== "YOUR_API_KEY" && typeof firebase !== 'undefined') {
        firebase.initializeApp(firebaseConfig);
        db = firebase.firestore();
        firebaseInitialized = true;
        console.log('Firebase initialized');
    } else {
        console.log('Firebase not configured - using localStorage fallback');
    }
} catch (e) {
    console.warn('Firebase initialization failed:', e);
}

// State
let predictionCases = [];
let currentCaseIndex = 0;
let userPredictions = {};
let userId = localStorage.getItem('lexarena_user_id');

// Truncate synopsis before outcome-revealing phrases
function truncateBeforeOutcome(synopsis) {
    if (!synopsis) return 'No details available.';
    
    const outcomeIndicators = [
        "without admitting or denying",
        "consented to",
        "agreed to pay",
        "final judgment",
        "ordered to pay",
        "the court ordered",
        "has agreed",
        "will pay",
        "was ordered",
        "the sec obtained",
        "defendant agreed",
        "defendants agreed",
        "judgment was entered"
    ];
    
    const lowerSynopsis = synopsis.toLowerCase();
    let earliestIndex = synopsis.length;
    
    for (const indicator of outcomeIndicators) {
        const index = lowerSynopsis.indexOf(indicator);
        if (index > 100 && index < earliestIndex) {
            earliestIndex = index;
        }
    }
    
    // Truncate to max 400 chars for conciseness
    let truncated = synopsis.substring(0, Math.min(earliestIndex, 400)).trim();
    
    // End at sentence boundary if possible
    const lastPeriod = truncated.lastIndexOf('.');
    if (lastPeriod > 200) {
        truncated = truncated.substring(0, lastPeriod + 1);
    } else {
        truncated += '...';
    }
    
    return truncated;
}

// Generate anonymous user ID if not exists
if (!userId) {
    userId = 'user_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('lexarena_user_id', userId);
}

// Load sample cases for prediction
async function loadPredictionCases() {
    try {
        const response = await fetch('data/processed/combined_results.json');
        const data = await response.json();
        
        // Get 5 cases with most metrics populated (prefer complete data)
        const completeCases = data.predictions
            .filter(p => {
                if (!p.success || !p.ground_truth) return false;
                const gt = p.ground_truth;
                // Require at least resolution type and one monetary value
                return gt.resolution_type !== null && gt.resolution_type !== undefined;
            })
            .sort((a, b) => {
                // Sort by completeness - cases with more metrics first
                const countMetrics = (gt) => {
                    let count = 0;
                    if (gt.disgorgement_amount != null) count++;
                    if (gt.penalty_amount != null) count++;
                    if (gt.prejudgment_interest != null) count++;
                    if (gt.has_injunction != null) count++;
                    if (gt.has_officer_director_bar != null) count++;
                    return count;
                };
                return countMetrics(b.ground_truth) - countMetrics(a.ground_truth);
            })
            .slice(0, 5);
        
        predictionCases = completeCases;
        console.log(`Loaded ${predictionCases.length} complete cases for prediction`);
        
        return predictionCases;
    } catch (e) {
        console.error('Failed to load cases:', e);
        return [];
    }
}

// Open prediction modal (show start screen first)
async function openPredictionModal() {
    if (predictionCases.length === 0) {
        await loadPredictionCases();
    }
    
    if (predictionCases.length === 0) {
        alert('Unable to load cases. Please try again later.');
        return;
    }
    
    currentCaseIndex = 0;
    userPredictions = {};
    
    // Show start screen, hide questions
    document.getElementById('prediction-start').style.display = 'block';
    document.getElementById('prediction-questions-screen').style.display = 'none';
    
    // Update prediction count on start screen
    getTotalPredictionCount().then(count => {
        const counter = document.getElementById('start-prediction-count');
        if (counter) counter.textContent = count;
    });
    
    document.getElementById('prediction-modal').style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// Start predictions (from start screen)
function startPredictions() {
    // Hide start screen, show questions
    document.getElementById('prediction-start').style.display = 'none';
    document.getElementById('prediction-questions-screen').style.display = 'block';
    
    renderCurrentCase();
    loadCommunityPredictions();
}

// Close prediction modal
function closePredictionModal() {
    document.getElementById('prediction-modal').style.display = 'none';
    document.body.style.overflow = '';
}

// Close results modal
function closeResultsModal() {
    document.getElementById('results-modal').style.display = 'none';
    document.body.style.overflow = '';
}

// Render current case
function renderCurrentCase() {
    const caseData = predictionCases[currentCaseIndex];
    if (!caseData) return;
    
    const meta = caseData.metadata || {};
    const rawSynopsis = meta.reducto_fields?.case_synopsis || meta.summary || '';
    const blindSynopsis = truncateBeforeOutcome(rawSynopsis);
    
    document.getElementById('current-case-num').textContent = currentCaseIndex + 1;
    document.getElementById('total-cases').textContent = predictionCases.length;
    document.getElementById('case-title').textContent = `SEC v. ${meta.title || caseData.case_id}`;
    
    // Populate structured case facts
    document.getElementById('fact-defendant').textContent = meta.title || caseData.case_id;
    document.getElementById('fact-charges').textContent = meta.charges || 'Securities violations';
    document.getElementById('fact-court').textContent = meta.court || 'Federal Court';
    document.getElementById('fact-filed').textContent = meta.release_date || 'Unknown';
    document.getElementById('allegations-text').textContent = blindSynopsis;
    
    // Reset inputs
    document.getElementById('resolution-slider').value = 50;
    document.getElementById('resolution-value').textContent = 50;
    document.getElementById('injunction-slider').value = 50;
    document.getElementById('injunction-value').textContent = 50;
    document.getElementById('officer-bar-slider').value = 50;
    document.getElementById('officer-bar-value').textContent = 50;
    
    // Load existing prediction if any
    const existing = userPredictions[caseData.case_id];
    if (existing) {
        document.getElementById('resolution-slider').value = existing.resolutionPct;
        document.getElementById('resolution-value').textContent = existing.resolutionPct;
        document.getElementById('injunction-slider').value = existing.injunctionPct;
        document.getElementById('injunction-value').textContent = existing.injunctionPct;
        document.getElementById('officer-bar-slider').value = existing.officerBarPct;
        document.getElementById('officer-bar-value').textContent = existing.officerBarPct;
    }
    
    // Update nav buttons
    document.getElementById('btn-prev').disabled = currentCaseIndex === 0;
    document.getElementById('btn-next').textContent = 
        currentCaseIndex === predictionCases.length - 1 ? 'Finish' : 'Next →';
    
    // Load community predictions for this case
    loadCommunityPredictions();
}

// Slider value updates
document.addEventListener('DOMContentLoaded', function() {
    const sliders = [
        { id: 'resolution-slider', valueId: 'resolution-value' },
        { id: 'injunction-slider', valueId: 'injunction-value' },
        { id: 'officer-bar-slider', valueId: 'officer-bar-value' }
    ];
    
    sliders.forEach(({ id, valueId }) => {
        const slider = document.getElementById(id);
        const value = document.getElementById(valueId);
        if (slider && value) {
            slider.addEventListener('input', () => {
                value.textContent = slider.value;
            });
        }
    });
    
    // Load prediction count on page load
    loadPredictionCount();
});

// Navigate to previous case
function prevCase() {
    if (currentCaseIndex > 0) {
        saveCurrent();
        currentCaseIndex--;
        renderCurrentCase();
        scrollModalToTop();
    }
}

// Navigate to next case
function nextCase() {
    saveCurrent();
    
    if (currentCaseIndex < predictionCases.length - 1) {
        currentCaseIndex++;
        renderCurrentCase();
        scrollModalToTop();
    } else {
        // Finish - show results
        showResults();
    }
}

// Scroll modal content to top
function scrollModalToTop() {
    // Try multiple approaches to ensure scroll works
    const modalContent = document.querySelector('#prediction-modal .prediction-modal-content');
    if (modalContent) {
        modalContent.scrollTop = 0;
        modalContent.scrollTo({ top: 0, behavior: 'instant' });
    }
    
    // Also scroll to case title element
    const caseTitle = document.getElementById('case-title');
    if (caseTitle) {
        caseTitle.scrollIntoView({ behavior: 'instant', block: 'start' });
    }
}

// Skip current case
function skipCase() {
    if (currentCaseIndex < predictionCases.length - 1) {
        currentCaseIndex++;
        renderCurrentCase();
        scrollModalToTop();
    } else {
        showResults();
    }
}

// Save current prediction
function saveCurrent() {
    const caseData = predictionCases[currentCaseIndex];
    if (!caseData) return;
    
    userPredictions[caseData.case_id] = {
        caseId: caseData.case_id,
        resolutionPct: parseInt(document.getElementById('resolution-slider').value),
        injunctionPct: parseInt(document.getElementById('injunction-slider').value),
        officerBarPct: parseInt(document.getElementById('officer-bar-slider').value),
        timestamp: new Date().toISOString()
    };
}

// Submit current prediction
async function submitPrediction() {
    console.log('Submit prediction clicked');
    saveCurrent();
    
    const caseData = predictionCases[currentCaseIndex];
    const prediction = userPredictions[caseData.case_id];
    
    if (!prediction) {
        console.warn('No prediction to submit');
        return;
    }
    
    // Verify human with reCAPTCHA v3 (non-blocking)
    let recaptchaToken = null;
    try {
        if (typeof grecaptcha !== 'undefined' && grecaptcha.execute) {
            await new Promise((resolve) => grecaptcha.ready(resolve));
            recaptchaToken = await grecaptcha.execute(RECAPTCHA_SITE_KEY, { action: 'submit_prediction' });
            prediction.recaptchaToken = recaptchaToken;
            console.log('reCAPTCHA token obtained');
        }
    } catch (e) {
        console.warn('reCAPTCHA failed (continuing anyway):', e);
    }
    
    // Calculate accuracy for this prediction
    prediction.accuracy = calculateAccuracy(prediction, caseData.ground_truth);
    
    // Save to Firebase if available (don't block on failure)
    if (firebaseInitialized && db) {
        db.collection('predictions').add({
            ...prediction,
            odId: userId,
            caseId: caseData.case_id,
            recaptchaToken: recaptchaToken,
            isHumanVerified: recaptchaToken !== null
        }).then(() => {
            console.log('Prediction saved to Firebase');
        }).catch(e => {
            console.warn('Failed to save to Firebase:', e);
        });
    }
    
    // Save to localStorage as backup
    const localPredictions = JSON.parse(localStorage.getItem('lexarena_predictions') || '[]');
    localPredictions.push({ ...prediction, odId: userId, isHumanVerified: recaptchaToken !== null });
    localStorage.setItem('lexarena_predictions', JSON.stringify(localPredictions));
    
    console.log('Prediction submitted, moving to next case');
    
    // Move to next case
    nextCase();
    
    // Ensure scroll to top after submit
    scrollModalToTop();
}

// Calculate accuracy for a prediction
function calculateAccuracy(prediction, groundTruth) {
    if (!groundTruth) return 0;
    
    let correct = 0;
    let total = 0;
    
    // Resolution type (50% threshold for settled)
    const predictedSettled = prediction.resolutionPct >= 50;
    const actualSettled = groundTruth.resolution_type?.toLowerCase().includes('settled');
    if (predictedSettled === actualSettled) correct++;
    total++;
    
    // Injunction (50% threshold)
    if (groundTruth.has_injunction !== null) {
        const predictedInjunction = prediction.injunctionPct >= 50;
        if (predictedInjunction === groundTruth.has_injunction) correct++;
        total++;
    }
    
    // Officer bar (50% threshold)
    if (groundTruth.has_officer_director_bar !== null) {
        const predictedBar = prediction.officerBarPct >= 50;
        if (predictedBar === groundTruth.has_officer_director_bar) correct++;
        total++;
    }
    
    return total > 0 ? Math.round((correct / total) * 100) : 0;
}

// Show results
async function showResults() {
    console.log('Showing results...');
    closePredictionModal();
    
    // Calculate overall accuracy
    let totalAccuracy = 0;
    let predictionCount = 0;
    
    predictionCases.forEach(caseData => {
        const prediction = userPredictions[caseData.case_id];
        if (prediction) {
            const accuracy = calculateAccuracy(prediction, caseData.ground_truth);
            totalAccuracy += accuracy;
            predictionCount++;
        }
    });
    
    const userAvgAccuracy = predictionCount > 0 ? Math.round(totalAccuracy / predictionCount) : 0;
    
    // Update results modal immediately with user score
    document.getElementById('user-score').textContent = userAvgAccuracy + '%';
    
    // Show placeholder for community data (load in background)
    document.getElementById('community-score').textContent = '—%';
    document.getElementById('total-prediction-count').textContent = '...';
    
    // Show results modal immediately
    document.getElementById('results-modal').style.display = 'flex';
    document.body.style.overflow = 'hidden';
    console.log('Results modal opened');
    
    // Load community data in background (non-blocking)
    getCommunityAverage().then(avg => {
        document.getElementById('community-score').textContent = avg + '%';
    }).catch(() => {
        document.getElementById('community-score').textContent = '50%';
    });
    
    getTotalPredictionCount().then(count => {
        document.getElementById('total-prediction-count').textContent = count;
    }).catch(() => {
        document.getElementById('total-prediction-count').textContent = '—';
    });
    
    // Build detailed breakdown with actual outcomes
    let detailHtml = '<div class="results-breakdown"><h3>Your Predictions vs Actual Outcomes</h3>';
    predictionCases.forEach((caseData, idx) => {
        const prediction = userPredictions[caseData.case_id];
        if (prediction) {
            const gt = caseData.ground_truth || {};
            const accuracy = calculateAccuracy(prediction, gt);
            
            // Determine correct/incorrect for each metric
            const userResolution = prediction.resolutionPct >= 50 ? 'Settled' : 'Litigated';
            const actualResolution = gt.resolution_type ? (gt.resolution_type.toLowerCase().includes('settled') ? 'Settled' : 'Litigated') : '—';
            const resCorrect = userResolution === actualResolution;
            
            const userInjunction = prediction.injunctionPct >= 50 ? 'Yes' : 'No';
            const actualInjunction = gt.has_injunction !== null ? (gt.has_injunction ? 'Yes' : 'No') : '—';
            const injCorrect = gt.has_injunction !== null && (prediction.injunctionPct >= 50) === gt.has_injunction;
            
            const userBar = prediction.officerBarPct >= 50 ? 'Yes' : 'No';
            const actualBar = gt.has_officer_director_bar !== null ? (gt.has_officer_director_bar ? 'Yes' : 'No') : '—';
            const barCorrect = gt.has_officer_director_bar !== null && (prediction.officerBarPct >= 50) === gt.has_officer_director_bar;
            
            detailHtml += `
                <div class="result-case-card">
                    <div class="result-case-header">
                        <strong>Case ${idx + 1}: SEC v. ${caseData.metadata?.title || caseData.case_id}</strong>
                        <span class="result-accuracy ${accuracy >= 50 ? 'good' : 'poor'}">${accuracy}% correct</span>
                    </div>
                    <table class="outcome-table">
                        <thead>
                            <tr>
                                <th>Metric</th>
                                <th>You</th>
                                <th>Actual</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Resolution</td>
                                <td>${userResolution}</td>
                                <td>${actualResolution}</td>
                                <td class="${resCorrect ? 'correct' : 'incorrect'}">${resCorrect ? '✓' : '✗'}</td>
                            </tr>
                            <tr>
                                <td>Injunction</td>
                                <td>${userInjunction}</td>
                                <td>${actualInjunction}</td>
                                <td class="${gt.has_injunction === null ? '' : (injCorrect ? 'correct' : 'incorrect')}">${gt.has_injunction === null ? '—' : (injCorrect ? '✓' : '✗')}</td>
                            </tr>
                            <tr>
                                <td>Officer Bar</td>
                                <td>${userBar}</td>
                                <td>${actualBar}</td>
                                <td class="${gt.has_officer_director_bar === null ? '' : (barCorrect ? 'correct' : 'incorrect')}">${gt.has_officer_director_bar === null ? '—' : (barCorrect ? '✓' : '✗')}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            `;
        }
    });
    detailHtml += '</div>';
    document.getElementById('results-detail').innerHTML = detailHtml;
}

// Load community predictions for current case
async function loadCommunityPredictions() {
    const container = document.getElementById('community-comments');
    const caseData = predictionCases[currentCaseIndex];
    
    if (!caseData) {
        container.innerHTML = '<p class="loading-comments">No case selected</p>';
        return;
    }
    
    let predictions = [];
    
    // Try Firebase first
    if (firebaseInitialized && db) {
        try {
            const snapshot = await db.collection('predictions')
                .where('caseId', '==', caseData.case_id)
                .orderBy('timestamp', 'desc')
                .limit(10)
                .get();
            
            predictions = snapshot.docs.map(doc => doc.data());
        } catch (e) {
            console.warn('Firebase query failed:', e);
        }
    }
    
    // Fallback to localStorage
    if (predictions.length === 0) {
        const localPredictions = JSON.parse(localStorage.getItem('lexarena_predictions') || '[]');
        predictions = localPredictions.filter(p => p.caseId === caseData.case_id);
    }
    
    if (predictions.length === 0) {
        container.innerHTML = '<p class="loading-comments">No predictions yet. Be the first!</p>';
        return;
    }
    
    let html = '';
    predictions.forEach(p => {
        const resolutionText = p.resolutionPct >= 50 ? 'Settled' : 'Litigated';
        html += `
            <div class="community-comment">
                <span class="comment-user">Forecaster</span>
                <div class="comment-prediction">
                    ${resolutionText} (${p.resolutionPct}%)
                    ${p.disgorgement ? `, $${p.disgorgement.toLocaleString()} disgorgement` : ''}
                </div>
                ${p.reasoning ? `<div class="comment-reasoning">"${p.reasoning}"</div>` : ''}
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Get community average accuracy
async function getCommunityAverage() {
    let predictions = [];
    
    if (firebaseInitialized && db) {
        try {
            const snapshot = await db.collection('predictions')
                .where('accuracy', '>', 0)
                .limit(100)
                .get();
            predictions = snapshot.docs.map(doc => doc.data());
        } catch (e) {
            console.warn('Firebase query failed:', e);
        }
    }
    
    // Fallback to localStorage
    if (predictions.length === 0) {
        predictions = JSON.parse(localStorage.getItem('lexarena_predictions') || '[]');
    }
    
    if (predictions.length === 0) return 50;
    
    const totalAccuracy = predictions.reduce((sum, p) => sum + (p.accuracy || 0), 0);
    return Math.round(totalAccuracy / predictions.length);
}

// Get total prediction count
async function getTotalPredictionCount() {
    let count = 0;
    
    if (firebaseInitialized && db) {
        try {
            const snapshot = await db.collection('predictions').get();
            count = snapshot.size;
        } catch (e) {
            console.warn('Firebase query failed:', e);
        }
    }
    
    // Add localStorage count
    const localPredictions = JSON.parse(localStorage.getItem('lexarena_predictions') || '[]');
    count = Math.max(count, localPredictions.length);
    
    return count;
}

// Load prediction count on page load
async function loadPredictionCount() {
    const counter = document.getElementById('prediction-counter');
    if (counter) {
        const count = await getTotalPredictionCount();
        counter.textContent = count;
    }
}

// Share results
function shareResults() {
    const userScore = document.getElementById('user-score').textContent;
    const text = `I scored ${userScore} predicting SEC case outcomes on LexArena! Can you beat my accuracy? Try it: ${window.location.href}`;
    
    if (navigator.share) {
        navigator.share({
            title: 'My LexArena Results',
            text: text,
            url: window.location.href
        });
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(text).then(() => {
            alert('Results copied to clipboard!');
        });
    }
}
