document.addEventListener('DOMContentLoaded', () => {
    // API endpoint base path
    const API_BASE = '/api';

    // State Variables
    let currentDomain = null;
    let currentResults = [];
    let chartInstance = null;

    // Icon lookup for domain tabs; falls back to a generic database icon.
    const DOMAIN_ICONS = {
        healthcare_claims: 'fa-kit-medical',
        retail_sales: 'fa-cart-shopping',
        ecommerce: 'fa-bag-shopping',
        finance_banking: 'fa-building-columns',
        logistics: 'fa-truck-fast',
        hr_payroll: 'fa-users-gear',
        education: 'fa-graduation-cap',
    };
    const domainIcon = (name) => DOMAIN_ICONS[name] || 'fa-database';

    // DOM Elements
    const domainSelector = document.getElementById('domain-selector');
    const yamlTextarea = document.getElementById('yaml-textarea');
    const btnSaveYaml = document.getElementById('btn-save-yaml');
    const btnReindex = document.getElementById('btn-reindex');
    const whitelistTablesList = document.getElementById('whitelist-tables-list');
    
    const queryInput = document.getElementById('query-input');
    const btnSubmitQuery = document.getElementById('btn-submit-query');
    const suggButtons = document.querySelectorAll('.sugg-btn');

    // Pipeline elements
    const nodeRetrieval = document.getElementById('node-retrieval');
    const contentRetrieval = document.getElementById('content-retrieval');
    const retrievalScoresList = document.getElementById('retrieval-scores-list');

    const nodePrompt = document.getElementById('node-prompt');
    const contentPrompt = document.getElementById('content-prompt');
    const promptPreview = document.getElementById('prompt-preview');

    const nodeGeneration = document.getElementById('node-generation');
    const contentGeneration = document.getElementById('content-generation');
    const generatedSqlTextarea = document.getElementById('generated-sql-textarea');
    const btnEditSql = document.getElementById('btn-edit-sql');
    const btnRunSql = document.getElementById('btn-run-sql');

    const nodeValidation = document.getElementById('node-validation');
    const contentValidation = document.getElementById('content-validation');
    const validationStatusBox = document.getElementById('validation-status-box');

    // Results elements
    const resultsCard = document.getElementById('results-card');
    const resultsTable = document.getElementById('results-table');
    const resultsTableContainer = document.getElementById('results-table-container');
    const resultsChartContainer = document.getElementById('results-chart-container');
    const btnViewTable = document.getElementById('btn-view-table');
    const btnViewChart = document.getElementById('btn-view-chart');

    /* --- TOAST NOTIFICATIONS --- */
    function showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        let icon = 'fa-circle-info';
        if (type === 'success') icon = 'fa-circle-check';
        if (type === 'error') icon = 'fa-circle-exclamation';
        
        toast.innerHTML = `
            <i class="fa-solid ${icon}"></i>
            <span>${message}</span>
        `;
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-20px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /* --- DOMAIN & SCHEMA MANAGEMENT --- */
    // Fetch and load active domain YAML
    async function loadDomainConfig(domainName) {
        try {
            const res = await fetch(`${API_BASE}/domain/${domainName}`);
            if (!res.ok) throw new Error('Failed to fetch domain config');
            const data = await res.json();
            yamlTextarea.value = data.yaml;
            
            // Populate whitelist browser
            renderWhitelistBrowser(data.tables || []);
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    // Populate Whitelisted Tables list in Sidebar
    function renderWhitelistBrowser(tables) {
        whitelistTablesList.innerHTML = '';
        if (tables.length === 0) {
            whitelistTablesList.innerHTML = '<div class="empty-state">No tables in model</div>';
            return;
        }
        tables.forEach(table => {
            const item = document.createElement('div');
            item.className = 'whitelist-item';
            item.innerHTML = `
                <span>${table}</span>
                <span class="col-count"><i class="fa-solid fa-table-list"></i></span>
            `;
            whitelistTablesList.appendChild(item);
        });
    }

    // Fetch the list of domains and render a tab per domain.
    async function loadDomainTabs() {
        try {
            const res = await fetch(`${API_BASE}/domains`);
            if (!res.ok) throw new Error('Failed to fetch domain list');
            const data = await res.json();
            renderDomainTabs(data.domains || []);
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    // Build the domain tab buttons and wire up switching.
    function renderDomainTabs(domains) {
        domainSelector.innerHTML = '';
        if (domains.length === 0) {
            domainSelector.innerHTML = '<div class="empty-state">No domains found</div>';
            return;
        }

        domains.forEach((domain, idx) => {
            const tab = document.createElement('button');
            tab.className = 'domain-tab';
            tab.setAttribute('data-domain', domain.name);
            if (domain.description) tab.title = domain.description;
            tab.innerHTML = `<i class="fa-solid ${domainIcon(domain.name)}"></i> ${domain.name}`;

            tab.addEventListener('click', () => {
                domainSelector.querySelectorAll('.domain-tab')
                    .forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                currentDomain = domain.name;
                loadDomainConfig(currentDomain);
            });

            // Activate the first domain by default.
            if (idx === 0) {
                tab.classList.add('active');
                currentDomain = domain.name;
            }
            domainSelector.appendChild(tab);
        });

        // Load the initially-active domain's config.
        if (currentDomain) loadDomainConfig(currentDomain);
    }

    // Save YAML config
    btnSaveYaml.addEventListener('click', async () => {
        try {
            const res = await fetch(`${API_BASE}/domain/${currentDomain}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml: yamlTextarea.value })
            });
            if (!res.ok) throw new Error('Failed to save YAML model');
            showToast('Semantic model saved successfully!', 'success');
            
            // Auto re-index
            reindexModel();
        } catch (err) {
            showToast(err.message, 'error');
        }
    });

    // Reindex backend vector cache
    async function reindexModel() {
        showToast('Updating vector index...', 'info');
        try {
            const res = await fetch(`${API_BASE}/index`, { method: 'POST' });
            if (!res.ok) throw new Error('Indexing failed');
            const data = await res.json();
            showToast(`Re-indexed ${data.indexed_tables} tables successfully!`, 'success');
            
            // Reload domain info
            loadDomainConfig(currentDomain);
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    btnReindex.addEventListener('click', reindexModel);

    /* --- PIPELINE COLLAPSE / EXPAND --- */
    const headers = document.querySelectorAll('.node-header');
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const content = header.nextElementSibling;
            content.classList.toggle('collapsed');
        });
    });

    function expandNode(nodeContentElement) {
        nodeContentElement.classList.remove('collapsed');
    }

    function collapseAllNodes() {
        contentRetrieval.classList.add('collapsed');
        contentPrompt.classList.add('collapsed');
        contentGeneration.classList.add('collapsed');
        contentValidation.classList.add('collapsed');
    }

    /* --- EXECUTE QUERY & PIPELINE --- */
    async function submitNaturalLanguageQuery(question) {
        if (!question.trim()) return;

        collapseAllNodes();
        showToast('Analyzing schema & building query...', 'info');
        
        btnSubmitQuery.disabled = true;
        btnSubmitQuery.querySelector('span').textContent = 'Processing...';

        try {
            const res = await fetch(`${API_BASE}/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Query execution failed');
            }

            const data = await res.json();
            currentResults = data.results || [];

            // Update Step 1: Retrieval
            renderRetrievalStep(data.retrieved_context);
            expandNode(contentRetrieval);

            // Update Step 2: Prompt
            promptPreview.textContent = data.prompt || 'Prompt not returned';
            expandNode(contentPrompt);

            // Update Step 3: Generation
            generatedSqlTextarea.value = data.generated_sql || '';
            expandNode(contentGeneration);

            // Update Step 4: Validation
            renderValidationStep(data);
            expandNode(contentValidation);

            // Render Results
            renderResults(data.results || [], data.columns || []);
            showToast('Query processed successfully!', 'success');

        } catch (err) {
            showToast(err.message, 'error');
            validationStatusBox.className = 'info-box error';
            validationStatusBox.innerHTML = `
                <h4><i class="fa-solid fa-circle-xmark"></i> Pipeline Error</h4>
                <p>${err.message}</p>
            `;
            expandNode(contentValidation);
        } finally {
            btnSubmitQuery.disabled = false;
            btnSubmitQuery.querySelector('span').textContent = 'Execute';
        }
    }

    // Render step 1 (retrieval scores / tables matched)
    function renderRetrievalStep(retrievedContext) {
        if (!retrievedContext) {
            retrievalScoresList.innerHTML = '<div class="empty-state">No tables retrieved.</div>';
            return;
        }
        retrievalScoresList.innerHTML = `
            <div class="score-row" style="grid-template-columns: 1fr;">
                <pre class="code-preview" style="max-height: 200px;">${retrievedContext}</pre>
            </div>
        `;
    }

    // Render step 4 (validation result)
    function renderValidationStep(data) {
        if (data.validation_error) {
            validationStatusBox.className = 'info-box error';
            validationStatusBox.innerHTML = `
                <h4><i class="fa-solid fa-triangle-exclamation"></i> SQL Validation Failed</h4>
                <p>${data.validation_error}</p>
                <div style="margin-top: 0.5rem; font-size: 0.75rem; font-family: monospace; color: rgba(255,255,255,0.7)">
                    Executed SQL fallback check: Denied.
                </div>
            `;
        } else {
            validationStatusBox.className = 'info-box success';
            validationStatusBox.innerHTML = `
                <h4><i class="fa-solid fa-circle-check"></i> SQL Validation Passed</h4>
                <p>Query is read-only. Whitelisted tables verified. Enforced row LIMIT.</p>
                <div style="margin-top: 0.5rem; font-size: 0.8rem;">
                    <strong>Validated Query:</strong> <code style="color: #a7f3d0; font-family: monospace;">${data.validated_sql}</code>
                </div>
            `;
        }
    }

    // Trigger Query from main input
    btnSubmitQuery.addEventListener('click', () => {
        submitNaturalLanguageQuery(queryInput.value);
    });

    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') submitNaturalLanguageQuery(queryInput.value);
    });

    // Suggestion Buttons
    suggButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            queryInput.value = btn.textContent;
            submitNaturalLanguageQuery(btn.textContent);
        });
    });

    /* --- EDIT AND RE-RUN SQL --- */
    btnEditSql.addEventListener('click', () => {
        showToast('You can now edit the generated SQL query in the text area.', 'info');
        generatedSqlTextarea.focus();
    });

    btnRunSql.addEventListener('click', async () => {
        const sql = generatedSqlTextarea.value.trim();
        if (!sql) return;

        showToast('Running validated query...', 'info');
        try {
            const res = await fetch(`${API_BASE}/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sql })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'SQL Execution failed');
            }

            const data = await res.json();
            
            // Update Validation block manually
            validationStatusBox.className = 'info-box success';
            validationStatusBox.innerHTML = `
                <h4><i class="fa-solid fa-circle-check"></i> SQL Execution OK</h4>
                <p>Executed manually edited query safely.</p>
                <div style="margin-top: 0.5rem; font-size: 0.8rem;">
                    <strong>SQL:</strong> <code style="color: #a7f3d0; font-family: monospace;">${data.executed_sql}</code>
                </div>
            `;
            
            const cols = data.results && data.results.length > 0 ? Object.keys(data.results[0]) : [];
            renderResults(data.results, cols);
            showToast('Manual SQL executed!', 'success');

        } catch (err) {
            showToast(err.message, 'error');
            validationStatusBox.className = 'info-box error';
            validationStatusBox.innerHTML = `
                <h4><i class="fa-solid fa-circle-xmark"></i> Execution Error</h4>
                <p>${err.message}</p>
            `;
        }
    });

    /* --- RESULTS TAB / RENDERING --- */
    function renderResults(results, columns) {
        // Clear old results
        resultsTable.innerHTML = '';
        
        if (!results || results.length === 0) {
            resultsTable.innerHTML = `
                <tbody>
                    <tr>
                        <td class="empty-table-state">
                            <i class="fa-solid fa-inbox"></i>
                            <p>Query returned 0 rows or empty set.</p>
                        </td>
                    </tr>
                </tbody>
            `;
            setupChart(null); // Clear chart
            return;
        }

        // 1. Create table header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        resultsTable.appendChild(thead);

        // 2. Create table body
        const tbody = document.createElement('tbody');
        results.forEach(row => {
            const tr = document.createElement('tr');
            columns.forEach(col => {
                const td = document.createElement('td');
                td.textContent = row[col] !== null ? row[col] : 'NULL';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        resultsTable.appendChild(tbody);

        // 3. Try to configure chart if numbers are present
        setupChart(results, columns);
    }

    function setupChart(results, columns) {
        // Clear previous chart
        if (chartInstance) {
            chartInstance.destroy();
            chartInstance = null;
        }

        if (!results || results.length === 0) return;

        // Try to identify a label column (non-numeric, typically name, date, id) and a value column (numeric)
        let labelCol = null;
        let valueCol = null;

        columns.forEach(col => {
            const val = results[0][col];
            if (typeof val === 'number') {
                if (!valueCol) valueCol = col;
            } else if (typeof val === 'string' || typeof val === 'boolean') {
                if (!labelCol) labelCol = col;
            }
        });

        // If no explicit labels or values found, fallback
        if (!valueCol) {
            btnViewChart.classList.add('hidden');
            return;
        }
        btnViewChart.classList.remove('hidden');

        if (!labelCol) labelCol = columns.find(c => c !== valueCol) || valueCol;

        const labels = results.map(row => String(row[labelCol]));
        const dataVals = results.map(row => Number(row[valueCol]));

        const ctx = document.getElementById('results-chart').getContext('2d');
        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: valueCol,
                    data: dataVals,
                    backgroundColor: 'rgba(0, 180, 216, 0.5)',
                    borderColor: '#00b4d8',
                    borderWidth: 2,
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#9ca3af' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#9ca3af' }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#f3f4f6' } }
                }
            }
        });
    }

    // Toggle Table vs Chart Views
    btnViewTable.addEventListener('click', () => {
        btnViewTable.classList.add('active');
        btnViewChart.classList.remove('active');
        resultsTableContainer.classList.remove('hidden');
        resultsChartContainer.classList.add('hidden');
    });

    btnViewChart.addEventListener('click', () => {
        btnViewChart.classList.add('active');
        btnViewTable.classList.remove('active');
        resultsTableContainer.classList.add('hidden');
        resultsChartContainer.classList.remove('hidden');
    });

    /* --- INITIALIZATION --- */
    loadDomainTabs();
});
