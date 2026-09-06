document.addEventListener('DOMContentLoaded', () => {
    // API endpoint base path
    const API_BASE = '/api';

    // State Variables
    let currentDomain = null;
    let currentResults = [];
    let chartInstance = null;
    let currentMode = 'agent'; // 'agent' or 'sql'

    // Icon lookup for domain tabs
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

    // Mode Buttons
    const modeAgentBtn = document.getElementById('mode-agent');
    const modeSqlBtn = document.getElementById('mode-sql');
    const nodeAgentTrajectory = document.getElementById('node-agent-trajectory');
    const contentAgentTrajectory = document.getElementById('content-agent-trajectory');
    const agentTrajectoryContainer = document.getElementById('agent-trajectory-container');
    const directSqlNodes = document.getElementById('direct-sql-nodes');

    // Pipeline elements for Direct SQL Mode
    const contentRetrieval = document.getElementById('content-retrieval');
    const retrievalScoresList = document.getElementById('retrieval-scores-list');
    const contentPrompt = document.getElementById('content-prompt');
    const promptPreview = document.getElementById('prompt-preview');
    const contentGeneration = document.getElementById('content-generation');
    const generatedSqlTextarea = document.getElementById('generated-sql-textarea');
    const btnEditSql = document.getElementById('btn-edit-sql');
    const btnRunSql = document.getElementById('btn-run-sql');
    const contentValidation = document.getElementById('content-validation');
    const validationStatusBox = document.getElementById('validation-status-box');

    // Results elements
    const resultsTable = document.getElementById('results-table');
    const resultsTableContainer = document.getElementById('results-table-container');
    const resultsChartContainer = document.getElementById('results-chart-container');
    const btnViewTable = document.getElementById('btn-view-table');
    const btnViewChart = document.getElementById('btn-view-chart');

    // Sidebar Resizer Drag Logic (Pointer Events + Pointer Capture)
    const sidebarPanel = document.querySelector('.sidebar-panel');
    const resizerHandle = document.getElementById('resizer-handle');

    if (resizerHandle && sidebarPanel) {
        let isResizing = false;

        resizerHandle.addEventListener('pointerdown', (e) => {
            isResizing = true;
            resizerHandle.classList.add('resizing');
            try { resizerHandle.setPointerCapture(e.pointerId); } catch (_) {}
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });

        resizerHandle.addEventListener('pointermove', (e) => {
            if (!isResizing) return;
            const sidebarLeft = sidebarPanel.getBoundingClientRect().left;
            const newWidth = e.clientX - sidebarLeft;
            if (newWidth >= 180 && newWidth <= 850) {
                sidebarPanel.style.width = `${newWidth}px`;
                sidebarPanel.style.flexBasis = `${newWidth}px`;
            }
        });

        const stopResize = (e) => {
            if (isResizing) {
                isResizing = false;
                resizerHandle.classList.remove('resizing');
                try { resizerHandle.releasePointerCapture(e.pointerId); } catch (_) {}
                document.body.style.cursor = 'default';
                document.body.style.userSelect = 'auto';
            }
        };

        resizerHandle.addEventListener('pointerup', stopResize);
        resizerHandle.addEventListener('pointercancel', stopResize);
    }

    /* --- MODE SWITCHING --- */
    modeAgentBtn.addEventListener('click', () => {
        currentMode = 'agent';
        modeAgentBtn.classList.add('active');
        modeSqlBtn.classList.remove('active');
        nodeAgentTrajectory.classList.remove('hidden');
        directSqlNodes.classList.add('hidden');
        btnSubmitQuery.querySelector('span').textContent = 'Execute Agent';
        showToast('Switched to Python Sandbox Agent Mode', 'info');
    });

    modeSqlBtn.addEventListener('click', () => {
        currentMode = 'sql';
        modeSqlBtn.classList.add('active');
        modeAgentBtn.classList.remove('active');
        nodeAgentTrajectory.classList.add('hidden');
        directSqlNodes.classList.remove('hidden');
        btnSubmitQuery.querySelector('span').textContent = 'Execute SQL';
        showToast('Switched to Direct SQL Mode', 'info');
    });

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
    async function loadDomainConfig(domainName) {
        try {
            const res = await fetch(`${API_BASE}/domain/${domainName}`);
            if (!res.ok) throw new Error('Failed to fetch domain config');
            const data = await res.json();
            yamlTextarea.value = data.yaml;
            renderWhitelistBrowser(data.tables || []);
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

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

            if (idx === 0) {
                tab.classList.add('active');
                currentDomain = domain.name;
            }
            domainSelector.appendChild(tab);
        });

        if (currentDomain) loadDomainConfig(currentDomain);
    }

    btnSaveYaml.addEventListener('click', async () => {
        try {
            const res = await fetch(`${API_BASE}/domain/${currentDomain}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml: yamlTextarea.value })
            });
            if (!res.ok) throw new Error('Failed to save YAML model');
            showToast('Semantic model saved successfully!', 'success');
            reindexModel();
        } catch (err) {
            showToast(err.message, 'error');
        }
    });

    async function reindexModel() {
        showToast('Updating vector index...', 'info');
        try {
            const res = await fetch(`${API_BASE}/index`, { method: 'POST' });
            if (!res.ok) throw new Error('Indexing failed');
            const data = await res.json();
            showToast(`Re-indexed ${data.indexed_tables} tables successfully!`, 'success');
            loadDomainConfig(currentDomain);
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    btnReindex.addEventListener('click', reindexModel);

    /* --- PIPELINE COLLAPSE / EXPAND --- */
    document.querySelectorAll('.node-header').forEach(header => {
        header.addEventListener('click', () => {
            const content = header.nextElementSibling;
            if (content) content.classList.toggle('collapsed');
        });
    });

    /* --- EXECUTE QUERY SWITCHER --- */
    async function submitNaturalLanguageQuery(question) {
        if (!question.trim()) return;

        btnSubmitQuery.disabled = true;
        btnSubmitQuery.querySelector('span').textContent = 'Processing...';

        if (currentMode === 'agent') {
            await executeAgentQuery(question);
        } else {
            await executeDirectSqlQuery(question);
        }

        btnSubmitQuery.disabled = false;
        btnSubmitQuery.querySelector('span').textContent = currentMode === 'agent' ? 'Execute Agent' : 'Execute SQL';
    }

    /* --- EXECUTE AGENT QUERY (/api/agent_query) --- */
    async function executeAgentQuery(question) {
        showToast('Agent reasoning & code execution in progress...', 'info');
        agentTrajectoryContainer.innerHTML = '<div class="empty-state">Running Agent execution & self-repair reasoning loop...</div>';
        contentAgentTrajectory.classList.remove('collapsed');

        try {
            const res = await fetch(`${API_BASE}/agent_query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Agent execution failed');
            }

            const data = await res.json();
            renderAgentTrajectoryTimeline(data);

            // Handle Agent Results
            let results = [];
            if (Array.isArray(data.result)) {
                results = data.result;
            } else if (data.result && typeof data.result === 'object') {
                results = [data.result];
            } else if (data.result !== null && data.result !== undefined) {
                results = [{ "Result": String(data.result) }];
            }

            const columns = results.length > 0 ? Object.keys(results[0]) : [];
            renderResults(results, columns);

            if (data.status === 'success') {
                showToast(`Agent completed task in ${data.iterations} iteration(s)!`, 'success');
            } else {
                showToast(`Agent finished with status: ${data.status}`, 'error');
            }
        } catch (err) {
            showToast(err.message, 'error');
            agentTrajectoryContainer.innerHTML = `
                <div class="trajectory-card failed-border">
                    <div class="trajectory-header">
                        <span class="attempt-badge failed"><i class="fa-solid fa-circle-xmark"></i> Execution Error</span>
                    </div>
                    <div class="trajectory-repair-box">${err.message}</div>
                </div>
            `;
        }
    }

    // Render interactive LLM Agent trajectory timeline
    function renderAgentTrajectoryTimeline(data) {
        agentTrajectoryContainer.innerHTML = '';

        const timeline = document.createElement('div');
        timeline.className = 'trajectory-timeline';

        // 1. Render Initial Schema RAG Retrieval Context
        if (data.initial_retrieval && data.initial_retrieval.length > 0) {
            const ragCard = document.createElement('div');
            ragCard.className = 'rag-context-card';
            
            let matchesHtml = data.initial_retrieval.map(m => `
                <div style="font-size: 0.8rem; font-family: monospace; color: #a7f3d0; margin-top: 0.25rem;">
                    🔹 <strong>${escapeHtml(m.domain)}.${escapeHtml(m.table)}</strong> (similarity: ${(m.similarity * 100).toFixed(1)}%)
                </div>
            `).join('');

            ragCard.innerHTML = `
                <div class="rag-context-header">
                    <span><i class="fa-solid fa-database"></i> Phase 1: Semantic RAG Schema Retrieval</span>
                    <span style="font-size: 0.75rem; opacity: 0.8;">Retrieved ${data.initial_retrieval.length} Table Candidates</span>
                </div>
                ${matchesHtml}
            `;
            timeline.appendChild(ragCard);
        }

        // 2. Render Trajectory per Attempt
        const trajectory = data.trajectory || [];
        if (trajectory.length === 0) {
            agentTrajectoryContainer.innerHTML = '<div class="empty-state">No execution trace recorded.</div>';
            return;
        }

        trajectory.forEach((step) => {
            const card = document.createElement('div');
            card.className = `trajectory-card ${step.success ? 'success-border' : 'failed-border'}`;

            const isSuccess = step.success;
            const badgeClass = isSuccess ? 'success' : 'failed';
            const badgeIcon = isSuccess ? 'fa-circle-check' : 'fa-triangle-exclamation';

            let html = `
                <div class="trajectory-header">
                    <span class="attempt-badge ${badgeClass}">
                        <i class="fa-solid ${badgeIcon}"></i> Attempt #${step.attempt} — ${isSuccess ? 'Success' : 'Execution Error'}
                    </span>
                    <span style="font-size: 0.75rem; color: #9ca3af;"><i class="fa-solid fa-wrench"></i> ${step.tool_calls ? step.tool_calls.length : 0} Tool Call(s)</span>
                </div>

                <div>
                    <div class="trajectory-label"><i class="fa-brands fa-python"></i> Generated Python Code</div>
                    <pre class="code-preview">${escapeHtml(step.code || '# No code generated')}</pre>
                </div>
            `;

            // Structured Tool Calls Section
            if (step.tool_calls && step.tool_calls.length > 0) {
                html += `
                    <div>
                        <div class="trajectory-label"><i class="fa-solid fa-gears"></i> Tools Invoked by Agent</div>
                        <div class="tool-calls-container">
                `;

                step.tool_calls.forEach(tc => {
                    const isToolOk = tc.status === 'success';
                    const toolIcon = tc.tool === 'query_sql' ? 'fa-database' : (tc.tool === 'inspect_table' ? 'fa-table-list' : 'fa-magnifying-glass');
                    const argsStr = JSON.stringify(tc.args || {});

                    html += `
                        <div class="tool-call-card ${isToolOk ? 'success-tool' : 'error-tool'}">
                            <div class="tool-call-header">
                                <span class="tool-name-badge"><i class="fa-solid ${toolIcon}"></i> ${escapeHtml(tc.tool)}</span>
                                <span style="font-size: 0.7rem; font-weight: 700; color: ${isToolOk ? '#06d6a0' : '#ef476f'};">${tc.status.toUpperCase()}</span>
                            </div>
                            <div class="tool-args-preview">Args: ${escapeHtml(argsStr)}</div>
                            <div class="tool-output-summary">↳ Output: ${escapeHtml(tc.output_summary)}</div>
                        </div>
                    `;
                });

                html += `
                        </div>
                    </div>
                `;
            }

            // Stdout Output Section
            if (step.stdout && step.stdout.trim()) {
                html += `
                    <div>
                        <div class="trajectory-label"><i class="fa-solid fa-terminal"></i> Standard Output (stdout)</div>
                        <div class="trajectory-log-box">${escapeHtml(step.stdout)}</div>
                    </div>
                `;
            }

            // Error & Self-Repair Section
            if (!isSuccess && (step.error || step.stderr)) {
                const errText = step.error || step.stderr;
                html += `
                    <div>
                        <div class="trajectory-label" style="color: #ef476f;"><i class="fa-solid fa-bug"></i> Error Traceback Feedback (Passed to Gemini for Self-Repair)</div>
                        <div class="trajectory-repair-box">${escapeHtml(errText)}</div>
                    </div>
                `;
            }

            card.innerHTML = html;
            timeline.appendChild(card);
        });

        agentTrajectoryContainer.appendChild(timeline);
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    /* --- EXECUTE DIRECT SQL QUERY (/api/query) --- */
    async function executeDirectSqlQuery(question) {
        showToast('Analyzing schema & building query...', 'info');
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

            renderRetrievalStep(data.retrieved_context);
            contentRetrieval.classList.remove('collapsed');

            promptPreview.textContent = data.prompt || 'Prompt not returned';
            contentPrompt.classList.remove('collapsed');

            generatedSqlTextarea.value = data.generated_sql || '';
            contentGeneration.classList.remove('collapsed');

            renderValidationStep(data);
            contentValidation.classList.remove('collapsed');

            renderResults(data.results || [], data.columns || []);
            showToast('Direct SQL processed successfully!', 'success');
        } catch (err) {
            showToast(err.message, 'error');
            validationStatusBox.className = 'info-box error';
            validationStatusBox.innerHTML = `
                <h4><i class="fa-solid fa-circle-xmark"></i> Pipeline Error</h4>
                <p>${err.message}</p>
            `;
            contentValidation.classList.remove('collapsed');
        }
    }

    function renderRetrievalStep(retrievedContext) {
        if (!retrievedContext) {
            retrievalScoresList.innerHTML = '<div class="empty-state">No tables retrieved.</div>';
            return;
        }
        retrievalScoresList.innerHTML = `
            <div class="score-row" style="grid-template-columns: 1fr;">
                <pre class="code-preview" style="max-height: 200px;">${escapeHtml(retrievedContext)}</pre>
            </div>
        `;
    }

    function renderValidationStep(data) {
        if (data.validation_error) {
            validationStatusBox.className = 'info-box error';
            validationStatusBox.innerHTML = `
                <h4><i class="fa-solid fa-triangle-exclamation"></i> SQL Validation Failed</h4>
                <p>${escapeHtml(data.validation_error)}</p>
            `;
        } else {
            validationStatusBox.className = 'info-box success';
            validationStatusBox.innerHTML = `
                <h4><i class="fa-solid fa-circle-check"></i> SQL Validation Passed</h4>
                <p>Query is read-only. Whitelisted tables verified. Enforced row LIMIT.</p>
                <div style="margin-top: 0.5rem; font-size: 0.8rem;">
                    <strong>Validated Query:</strong> <code style="color: #a7f3d0; font-family: monospace;">${escapeHtml(data.validated_sql)}</code>
                </div>
            `;
        }
    }

    /* --- TRIGGER QUERY & SUGGESTIONS --- */
    btnSubmitQuery.addEventListener('click', () => {
        submitNaturalLanguageQuery(queryInput.value);
    });

    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') submitNaturalLanguageQuery(queryInput.value);
    });

    suggButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            queryInput.value = btn.textContent;
            submitNaturalLanguageQuery(btn.textContent);
        });
    });

    /* --- EDIT AND RE-RUN DIRECT SQL --- */
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
            validationStatusBox.className = 'info-box success';
            validationStatusBox.innerHTML = `
                <h4><i class="fa-solid fa-circle-check"></i> SQL Execution OK</h4>
                <p>Executed manually edited query safely.</p>
                <div style="margin-top: 0.5rem; font-size: 0.8rem;">
                    <strong>SQL:</strong> <code style="color: #a7f3d0; font-family: monospace;">${escapeHtml(data.executed_sql)}</code>
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
                <p>${escapeHtml(err.message)}</p>
            `;
        }
    });

    /* --- RESULTS TAB / RENDERING --- */
    function renderResults(results, columns) {
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
            setupChart(null);
            return;
        }

        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        resultsTable.appendChild(thead);

        const tbody = document.createElement('tbody');
        results.forEach(row => {
            const tr = document.createElement('tr');
            columns.forEach(col => {
                const td = document.createElement('td');
                td.textContent = row[col] !== null && row[col] !== undefined ? row[col] : 'NULL';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        resultsTable.appendChild(tbody);

        setupChart(results, columns);
    }

    function setupChart(results, columns) {
        if (chartInstance) {
            chartInstance.destroy();
            chartInstance = null;
        }

        if (!results || results.length === 0) return;

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

    loadDomainTabs();
});
