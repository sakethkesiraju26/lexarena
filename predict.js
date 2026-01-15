/**
 * LexArena Prediction System
 * 
 * Allows users to make predictions on SEC cases and compare against AI models.
 * Uses Firebase Firestore for storing community predictions.
 */

// Firebase Configuration - Replace with your own Firebase project credentials
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_PROJECT.firebaseapp.com",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_PROJECT.appspot.com",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID"
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
        
        // Get 5 settled cases with known outcomes
        const settledCases = data.predictions
            .filter(p => p.success && p.ground_truth)
            .slice(0, 5);
        
        predictionCases = settledCases;
        console.log(`Loaded ${predictionCases.length} cases for prediction`);
        
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
    const synopsis = meta.reducto_fields?.case_synopsis || meta.summary || 'No synopsis available.';
    
    document.getElementById('current-case-num').textContent = currentCaseIndex + 1;
    document.getElementById('total-cases').textContent = predictionCases.length;
    document.getElementById('case-title').textContent = `SEC v. ${meta.title || caseData.case_id}`;
    document.getElementById('case-synopsis').textContent = synopsis;
    
    // Reset inputs
    document.getElementById('resolution-slider').value = 50;
    document.getElementById('resolution-value').textContent = 50;
    document.getElementById('disgorgement-input').value = '';
    document.getElementById('penalty-input').value = '';
    document.getElementById('interest-input').value = '';
    document.getElementById('injunction-slider').value = 50;
    document.getElementById('injunction-value').textContent = 50;
    document.getElementById('officer-bar-slider').value = 50;
    document.getElementById('officer-bar-value').textContent = 50;
    document.getElementById('reasoning-input').value = '';
    
    // Load existing prediction if any
    const existing = userPredictions[caseData.case_id];
    if (existing) {
        document.getElementById('resolution-slider').value = existing.resolutionPct;
        document.getElementById('resolution-value').textContent = existing.resolutionPct;
        document.getElementById('disgorgement-input').value = existing.disgorgement || '';
        document.getElementById('penalty-input').value = existing.penalty || '';
        document.getElementById('interest-input').value = existing.interest || '';
        document.getElementById('injunction-slider').value = existing.injunctionPct;
        document.getElementById('injunction-value').textContent = existing.injunctionPct;
        document.getElementById('officer-bar-slider').value = existing.officerBarPct;
        document.getElementById('officer-bar-value').textContent = existing.officerBarPct;
        document.getElementById('reasoning-input').value = existing.reasoning || '';
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
    }
}

// Navigate to next case
function nextCase() {
    saveCurrent();
    
    if (currentCaseIndex < predictionCases.length - 1) {
        currentCaseIndex++;
        renderCurrentCase();
    } else {
        // Finish - show results
        showResults();
    }
}

// Skip current case
function skipCase() {
    if (currentCaseIndex < predictionCases.length - 1) {
        currentCaseIndex++;
        renderCurrentCase();
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
        disgorgement: parseFloat(document.getElementById('disgorgement-input').value) || null,
        penalty: parseFloat(document.getElementById('penalty-input').value) || null,
        interest: parseFloat(document.getElementById('interest-input').value) || null,
        injunctionPct: parseInt(document.getElementById('injunction-slider').value),
        officerBarPct: parseInt(document.getElementById('officer-bar-slider').value),
        reasoning: document.getElementById('reasoning-input').value,
        timestamp: new Date().toISOString()
    };
}

// Submit current prediction
async function submitPrediction() {
    saveCurrent();
    
    const caseData = predictionCases[currentCaseIndex];
    const prediction = userPredictions[caseData.case_id];
    
    if (!prediction) return;
    
    // Calculate accuracy for this prediction
    prediction.accuracy = calculateAccuracy(prediction, caseData.ground_truth);
    
    // Save to Firebase if available
    if (firebaseInitialized && db) {
        try {
            await db.collection('predictions').add({
                ...prediction,
                odId: userId,
                caseId: caseData.case_id
            });
            console.log('Prediction saved to Firebase');
        } catch (e) {
            console.warn('Failed to save to Firebase:', e);
        }
    }
    
    // Save to localStorage as backup
    const localPredictions = JSON.parse(localStorage.getItem('lexarena_predictions') || '[]');
    localPredictions.push({ ...prediction, odId: userId });
    localStorage.setItem('lexarena_predictions', JSON.stringify(localPredictions));
    
    // Move to next case
    nextCase();
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
    
    // Disgorgement (10% tolerance)
    if (groundTruth.disgorgement_amount !== null && prediction.disgorgement !== null) {
        const tolerance = groundTruth.disgorgement_amount * 0.1;
        if (Math.abs(prediction.disgorgement - groundTruth.disgorgement_amount) <= tolerance) {
            correct++;
        }
        total++;
    }
    
    // Penalty (10% tolerance)
    if (groundTruth.penalty_amount !== null && prediction.penalty !== null) {
        const tolerance = groundTruth.penalty_amount * 0.1;
        if (Math.abs(prediction.penalty - groundTruth.penalty_amount) <= tolerance) {
            correct++;
        }
        total++;
    }
    
    // Interest (10% tolerance)
    if (groundTruth.prejudgment_interest !== null && prediction.interest !== null) {
        const tolerance = groundTruth.prejudgment_interest * 0.1;
        if (Math.abs(prediction.interest - groundTruth.prejudgment_interest) <= tolerance) {
            correct++;
        }
        total++;
    }
    
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
    
    // Update results modal
    document.getElementById('user-score').textContent = userAvgAccuracy + '%';
    
    // Get community average (from Firebase or localStorage)
    const communityAvg = await getCommunityAverage();
    document.getElementById('community-score').textContent = communityAvg + '%';
    
    // Get total prediction count
    const totalPredictions = await getTotalPredictionCount();
    document.getElementById('total-prediction-count').textContent = totalPredictions;
    
    // Build detailed breakdown
    let detailHtml = '<div class="results-breakdown"><h3>Your Predictions</h3>';
    predictionCases.forEach((caseData, idx) => {
        const prediction = userPredictions[caseData.case_id];
        if (prediction) {
            const accuracy = calculateAccuracy(prediction, caseData.ground_truth);
            detailHtml += `
                <div class="result-case">
                    <strong>Case ${idx + 1}:</strong> ${caseData.metadata?.title || caseData.case_id}
                    <span class="result-accuracy ${accuracy >= 50 ? 'good' : 'poor'}">${accuracy}%</span>
                </div>
            `;
        }
    });
    detailHtml += '</div>';
    document.getElementById('results-detail').innerHTML = detailHtml;
    
    // Show results modal
    document.getElementById('results-modal').style.display = 'flex';
    document.body.style.overflow = 'hidden';
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
