document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('query-input');
    const searchBtn = document.getElementById('search-btn');
    const tryBtn = document.getElementById('try-btn');
    const btnText = document.getElementById('btn-text');
    const btnLoader = document.getElementById('btn-loader');
    
    const resultsSection = document.getElementById('results-section');
    const sqlOutput = document.getElementById('sql-output');
    const assistantMessage = document.getElementById('assistant-message');
    const tableCard = document.getElementById('table-card');
    const tableHead = document.getElementById('table-head');
    const tableBody = document.getElementById('table-body');
    const errorContainer = document.getElementById('error-container');

    const EXAMPLES = [
        "Show me the top 5 companies by total assets",
        "Show Microsoft's annual net income over the last 5 fiscal years",
        "Compare accounts receivable for Amazon and Alphabet in fiscal year 2025 quarter 1",
        "Which companies have the most balance sheet rows in the database?"
    ];

    // Health Check Mechanism
    const checkHealth = async () => {
        try {
            const res = await fetch('/health');
            const data = await res.json();
            const indicator = document.querySelector('.pulse');
            const statusText = document.getElementById('health-text');
            if (data.status === 'ok') {
                indicator.classList.add('online');
                // Format system status
                statusText.innerText = `Connected (${data.agent_memory_items} Memory Intents)`;
            } else {
                statusText.innerText = 'System degraded';
                indicator.style.backgroundColor = 'var(--error)';
            }
        } catch (e) {
            document.getElementById('health-text').innerText = 'System Offline';
            document.querySelector('.pulse').style.backgroundColor = 'var(--error)';
        }
    };

    checkHealth();

    // Fill example
    tryBtn.addEventListener('click', () => {
        const randomExample = EXAMPLES[Math.floor(Math.random() * EXAMPLES.length)];
        input.value = randomExample;
    });

    // Execute Search
    const executeQuery = async () => {
        const query = input.value.trim();
        if (!query) return;

        // UI Loading State
        btnText.classList.add('hidden');
        btnLoader.classList.remove('hidden');
        searchBtn.disabled = true;
        errorContainer.classList.add('hidden');
        resultsSection.classList.add('hidden');

        try {
            const res = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: query })
            });

            if (!res.ok) throw new Error('API Error - Failed to parse request.');
            
            const data = await res.json();
            
            // Populate Results
            sqlOutput.textContent = data.sql_query || '-- No SQL generated';
            assistantMessage.textContent = data.message;
            
            if (data.rows && data.rows.length > 0) {
                // Build Table
                tableHead.innerHTML = `<tr>${data.columns.map(col => `<th>${col}</th>`).join('')}</tr>`;
                tableBody.innerHTML = data.rows.map(row => 
                    `<tr>${row.map(cell => `<td>${cell !== null ? cell : '-'}</td>`).join('')}</tr>`
                ).join('');
                tableCard.classList.remove('hidden');
            } else {
                tableCard.classList.add('hidden');
            }
            
            resultsSection.classList.remove('hidden');

        } catch (e) {
            errorContainer.textContent = e.message || 'An unexpected error occurred connecting to the pipeline.';
            errorContainer.classList.remove('hidden');
        } finally {
            // Restore UI
            btnText.classList.remove('hidden');
            btnLoader.classList.add('hidden');
            searchBtn.disabled = false;
        }
    };

    searchBtn.addEventListener('click', executeQuery);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') executeQuery();
    });
});
