document.addEventListener('DOMContentLoaded', () => {
    const scanBtn = document.getElementById('scanBtn');
    const urlInput = document.getElementById('urlInput');
    const btnText = document.querySelector('.btn-text');
    const btnLoader = document.querySelector('.btn-loader');
    const resultSection = document.getElementById('resultSection');
    const statusBadge = document.getElementById('statusBadge');
    const confidenceFill = document.getElementById('confidenceFill');
    const confidenceValue = document.getElementById('confidenceValue');
    const riskScore = document.getElementById('riskScore');
    const featuresCount = document.getElementById('featuresCount');
    const resultTitle = document.getElementById('resultTitle');
    const resultDesc = document.getElementById('resultDesc');

    const API_URL = 'http://127.0.0.1:8002';

    scanBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) {
            urlInput.classList.add('error');
            setTimeout(() => urlInput.classList.remove('error'), 400);
            return;
        }

        // UI State: Loading
        scanBtn.disabled = true;
        btnText.classList.add('hidden');
        btnLoader.classList.remove('hidden');
        resultSection.classList.add('hidden');

        try {
            const response = await fetch(`${API_URL}/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });

            if (!response.ok) throw new Error('API Response Error');

            const data = await response.json();
            displayResults(data);
        } catch (error) {
            console.error('Connection Error:', error);
            showError('Server Connection Failed', 'Ensure the ML Engine is running on Port 8002.');
        } finally {
            scanBtn.disabled = false;
            btnText.classList.remove('hidden');
            btnLoader.classList.add('hidden');
        }
    });

    function displayResults(data) {
        resultSection.classList.remove('hidden');
        
        // Map API response to UI
        const isPhishing = data.prediction === 'Phishing' || data.label === 1 || data.risk_score === 'CRITICAL';
        const isCritical = data.risk_score === 'CRITICAL';
        const confidence = (data.confidence * 100).toFixed(1);
        
        statusBadge.textContent = isCritical ? 'Critical Risk' : (isPhishing ? 'Phishing Detected' : 'Legitimate URL');
        statusBadge.className = `status-badge ${isCritical ? 'critical' : (isPhishing ? 'danger' : 'safe')}`;
        
        resultTitle.textContent = isCritical ? '🚨 High-Level Threat' : (isPhishing ? '⚠️ Potential Security Risk' : '✅ URL Appears Safe');
        resultDesc.textContent = isCritical
            ? `WARNING: This URL is using a known brand impersonation trick (${data.reason}). Do not enter any credentials.`
            : (isPhishing 
                ? 'Our ML model identified characteristics typical of phishing sites. Proceed with extreme caution.'
                : 'No significant phishing markers were detected. This URL matches our safe site patterns.');

        riskScore.textContent = data.risk_score;
        riskScore.style.color = isCritical ? 'var(--danger)' : (isPhishing ? 'var(--danger)' : 'var(--safe)');
        
        featuresCount.textContent = `${data.features_used || 24} Features`;

        // Animate Confidence Meter
        confidenceFill.style.width = '0%';
        confidenceFill.style.backgroundColor = isCritical ? '#ff0000' : (isPhishing ? 'var(--danger)' : 'var(--safe)');
        
        setTimeout(() => {
            confidenceFill.style.width = `${confidence}%`;
            confidenceValue.textContent = `${confidence}%`;
        }, 150);
    }

    function showError(title, desc) {
        resultSection.classList.remove('hidden');
        statusBadge.textContent = 'Error';
        statusBadge.className = 'status-badge danger';
        resultTitle.textContent = title;
        resultDesc.textContent = desc;
        confidenceFill.style.width = '0%';
        confidenceValue.textContent = 'N/A';
    }

    window.resetScanner = () => {
        urlInput.value = '';
        resultSection.classList.add('hidden');
        urlInput.focus();
    };
});
