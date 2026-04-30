
        // Global function for tab switching - define immediately at the top
        window.switchTab = function(tab, element) {
            console.log(`[switchTab] Switching to tab: ${tab}, element:`, element);
            
            try {
                // Remove active class from all tabs
                const allTabs = document.querySelectorAll('.nav-tab');
                console.log(`[switchTab] Found ${allTabs.length} tab elements`);
                allTabs.forEach(t => {
                    t.classList.remove('active');
                    console.log(`[switchTab] Removed active from tab: ${t.textContent}`);
                });
                
                // Remove active class from all tab contents
                const allContents = document.querySelectorAll('.tab-content');
                console.log(`[switchTab] Found ${allContents.length} content elements`);
                allContents.forEach(t => {
                    t.classList.remove('active');
                    console.log(`[switchTab] Removed active from content: ${t.id}`);
                });
                
                // Add active class to clicked tab element
                if (element) {
                    element.classList.add('active');
                    console.log(`[switchTab] Added active to clicked tab: ${element.textContent}`);
                } else {
                    console.warn(`[switchTab] Element is null, trying to find by onclick`);
                    // Fallback: find tab by onclick attribute
                    allTabs.forEach(t => {
                        if (t.getAttribute('onclick') && t.getAttribute('onclick').includes(tab)) {
                            t.classList.add('active');
                            console.log(`[switchTab] Added active to tab by onclick: ${t.textContent}`);
                        }
                    });
                }
                
                // Add active class to tab content
                const tabContent = document.getElementById(tab);
                if (tabContent) {
                    tabContent.classList.add('active');
                    console.log(`[switchTab] Tab content found and activated: ${tab}`);
                } else {
                    console.error(`[switchTab] Tab content NOT found: ${tab}`);
                    console.log(`[switchTab] Available content IDs:`, Array.from(allContents).map(c => c.id));
                }
            } catch (e) {
                console.error(`[switchTab] Error: ${e}`, e.stack);
            }
        };
        
        let ws = null;
        let reconnectAttempts = 0;
        let pollInterval = null;
        
        // Refresh intervals in milliseconds
        const refreshIntervals = [
            2000,   // 0: 2s (online)
            5000,   // 1: 5s (default - online)
            8000,   // 2: 8s (online)
            15000,  // 3: 15s
            30000,  // 4: 30s
            60000,  // 5: 1min
            300000, // 6: 5min
            900000, // 7: 15min
            1800000 // 8: 30min
        ];
        const refreshLabels = [
            '2s', '5s', '8s', '15s', '30s', '1min', '5min', '15min', '30min'
        ];
        
        // Initialize refresh slider
        function initDashboard() {
            console.log('[Init] Dashboard initialization');
            
            const slider = document.getElementById('refresh-slider');
            const label = document.getElementById('refresh-label');
            
            if (!slider) {
                console.error('[Init] Slider not found!');
                return;
            }
            
            console.log('[Init] Slider found, initializing');
            
            // Set initial label
            const initialIdx = parseInt(slider.value);
            label.textContent = refreshLabels[initialIdx];
            
            // Start polling with initial interval
            startPolling(refreshIntervals[initialIdx]);
            
            slider.addEventListener('input', (e) => {
                const idx = parseInt(e.target.value);
                const interval = refreshIntervals[idx];
                label.textContent = refreshLabels[idx];
                console.log(`[Slider] Changed to index ${idx}, interval ${interval}ms`);
                
                // Restart polling with new interval
                if (pollInterval) {
                    clearInterval(pollInterval);
                }
                startPolling(interval);
            });
        }
        
        // Try DOMContentLoaded, fallback to immediate execution
        let dashboardInitialized = false;
        function safeInitDashboard() {
            if (dashboardInitialized) {
                console.log('[Init] Dashboard already initialized, skipping');
                return;
            }
            dashboardInitialized = true;
            initDashboard();
        }
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', safeInitDashboard);
        } else {
            safeInitDashboard();
        }
        
        function startPolling(interval) {
            // Clear existing interval if any
            if (pollInterval) {
                clearInterval(pollInterval);
            }
            
            pollInterval = setInterval(async () => {
                try {
                    console.log(`[Polling] Fetching metrics (interval: ${interval}ms)`);
                    const res = await fetch('/api/v1/health');
                    
                    if (!res.ok) {
                        console.error(`[Polling] HTTP error: ${res.status} ${res.statusText}`);
                        return;
                    }
                    
                    const data = await res.json();
                    console.log('[Polling] Metrics received:', data);
                    
                    updateDashboard({
                        type: 'metrics',
                        timestamp: new Date().toISOString(),
                        metrics: data.metrics,
                        alerts: data.alerts,
                        recommendations: data.recommendations,
                    });
                } catch (e) {
                    console.error('[Polling] Error:', e);
                    document.getElementById('last-update').textContent = 'Error: ' + e.message;
                }
            }, interval);
            
            console.log(`[Polling] Started with interval: ${interval}ms`);
        }
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
            
            ws.onopen = () => {
                console.log('WebSocket connected');
                reconnectAttempts = 0;
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'metrics') {
                    updateDashboard(data);
                }
            };
            
            ws.onclose = () => {
                console.log('WebSocket disconnected, reconnecting...');
                reconnectAttempts++;
                setTimeout(connectWebSocket, Math.min(reconnectAttempts * 1000, 10000));
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        }
        
        function updateDashboard(data) {
            const { metrics, alerts, recommendations } = data;
            const timestamp = new Date(data.timestamp);
            
            document.getElementById('last-update').textContent = timestamp.toLocaleTimeString();
            
            // Uptime
            if (document.getElementById('uptime')) {
                const uptimeSeconds = metrics.uptime_seconds || 0;
                const uptimeMinutes = Math.floor(uptimeSeconds / 60);
                const uptimeHours = Math.floor(uptimeMinutes / 60);
                const uptimeDays = Math.floor(uptimeHours / 24);
                
                let uptimeText = '';
                if (uptimeDays > 0) {
                    uptimeText = `${uptimeDays}d ${uptimeHours % 24}h`;
                } else if (uptimeHours > 0) {
                    uptimeText = `${uptimeHours}h ${uptimeMinutes % 60}m`;
                } else if (uptimeMinutes > 0) {
                    uptimeText = `${uptimeMinutes}m ${Math.floor(uptimeSeconds % 60)}s`;
                } else {
                    uptimeText = `${Math.floor(uptimeSeconds)}s`;
                }
                document.getElementById('uptime').textContent = uptimeText;
            }
            
            // HTTP
            if (document.getElementById('http-requests')) {
                document.getElementById('http-requests').textContent = 
                    (metrics.http_requests_total || 0).toLocaleString();
            }
            if (document.getElementById('http-errors')) {
                document.getElementById('http-errors').textContent = 
                    (metrics.http_errors_5xx || 0) + '%';
            }
            
            // Database
            if (document.getElementById('db-pool')) {
                const poolUsed = metrics.db_pool_size - metrics.db_pool_available;
                document.getElementById('db-pool').textContent = 
                    `${metrics.db_pool_available || 0}/${metrics.db_pool_size || 0}`;
            }
            if (document.getElementById('db-overflow')) {
                document.getElementById('db-overflow').textContent = metrics.db_pool_overflow || 0;
            }
            
            // Cache
            if (document.getElementById('cache-ratio')) {
                document.getElementById('cache-ratio').textContent = 
                    ((metrics.cache_hit_ratio || 0) * 100).toFixed(1) + '%';
            }
            
            // PgBouncer
            if (document.getElementById('pgbouncer-status')) {
                const pgbStatus = document.getElementById('pgbouncer-status');
                if (metrics.pgbouncer_in_use) {
                    pgbStatus.textContent = 'ON';
                    pgbStatus.className = 'metric metric-good';
                } else {
                    pgbStatus.textContent = 'OFF';
                    pgbStatus.className = 'metric metric-warning';
                }
            }
            
            // Redis
            if (document.getElementById('redis-status')) {
                document.getElementById('redis-status').textContent = 
                    metrics.redis_healthy ? 'OK' : 'DOWN';
                document.getElementById('redis-status').className = 
                    'metric ' + (metrics.redis_healthy ? 'metric-good' : 'metric-danger');
            }
            
            // Alerts
            if (document.getElementById('alert-count')) {
                document.getElementById('alert-count').textContent = alerts.length;
            }
            updateAlertList(alerts);
            
            // Recommendations
            updateRecommendations(recommendations);
            
            // Circuit Breakers
            updateCircuitBreakers(metrics.circuit_breakers);
            
            // Global status
            updateGlobalStatus(alerts);
        }
        
        function updateAlertList(alerts) {
            const container = document.getElementById('alert-list');
            if (!alerts || alerts.length === 0) {
                container.innerHTML = '<div class="rec-item rec-ok">No active alerts</div>';
                return;
            }
            
            container.innerHTML = alerts.map(alert => `
                <div class="alert-item alert-${alert.severity}">
                    <div class="alert-title">${alert.name}</div>
                    <div class="alert-message">${alert.message}</div>
                    <div class="alert-time">${new Date(alert.timestamp).toLocaleString()}</div>
                </div>
            `).join('');
        }
        
        function updateRecommendations(recs) {
            const container = document.getElementById('recommendations');
            container.innerHTML = recs.map(rec => {
                let cls = 'rec-ok';
                if (rec.includes('URGENTE')) cls = 'rec-urgent';
                else if (rec.includes('WARN') || rec.includes('WARNING')) cls = 'rec-warning';
                return `<div class="rec-item ${cls}">${rec}</div>`;
            }).join('');
        }
        
        function updateCircuitBreakers(cbs) {
            const container = document.getElementById('circuit-list');
            if (!cbs || Object.keys(cbs).length === 0) {
                container.innerHTML = '<div style="color: var(--text-secondary);">No circuit breakers</div>';
                return;
            }
            
            container.innerHTML = Object.entries(cbs).map(([name, status]) => {
                const state = status.state || 'unknown';
                let cls = 'cb-closed';
                if (state === 'open') cls = 'cb-open';
                else if (state === 'half_open') cls = 'cb-half';
                
                return `
                    <div style="padding: 10px; margin-bottom: 8px; background: var(--bg-card-hover); border-radius: 6px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 600;">${name}</span>
                            <span class="cb-indicator ${cls}">${state.toUpperCase()}</span>
                        </div>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-top: 6px;">
                            Failures: ${status.failures} | Successes: ${status.successes}
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function updateGlobalStatus(alerts) {
            const badge = document.getElementById('global-status');
            const hasCritical = alerts.some(a => a.severity === 'critical');
            const hasWarning = alerts.some(a => a.severity === 'warning');
            
            if (hasCritical) {
                badge.className = 'status-badge status-critical';
                badge.innerHTML = '<span class="status-indicator status-dot-red"></span>CRITICAL';
            } else if (hasWarning) {
                badge.className = 'status-badge status-warning';
                badge.innerHTML = '<span class="status-indicator status-dot-yellow"></span>WARNING';
            } else {
                badge.className = 'status-badge status-healthy';
                badge.innerHTML = '<span class="status-indicator status-dot-green"></span>HEALTHY';
            }
            
            // Update Usability Tab
            if (document.getElementById('user-online')) {
                document.getElementById('user-online').textContent = metrics.user_online || 0;
            }
            if (document.getElementById('user-offline')) {
                document.getElementById('user-offline').textContent = metrics.user_offline || 0;
            }
            if (document.getElementById('user-wifi')) {
                document.getElementById('user-wifi').textContent = metrics.user_wifi || 0;
            }
            if (document.getElementById('user-4g')) {
                document.getElementById('user-4g').textContent = metrics.user_4g || 0;
            }
            if (document.getElementById('user-3g')) {
                document.getElementById('user-3g').textContent = metrics.user_3g || 0;
            }
            if (document.getElementById('network-quality')) {
                document.getElementById('network-quality').textContent = (metrics.network_quality_avg || 0).toFixed(1);
            }
            
            // Update Analytics Tab
            if (document.getElementById('ocr-mobile-rate')) {
                document.getElementById('ocr-mobile-rate').textContent = ((metrics.ocr_mobile_success_rate || 0) * 100).toFixed(0) + '%';
            }
            if (document.getElementById('ocr-server-rate')) {
                document.getElementById('ocr-server-rate').textContent = ((metrics.ocr_server_success_rate || 0) * 100).toFixed(0) + '%';
            }
            if (document.getElementById('alerts-today')) {
                document.getElementById('alerts-today').textContent = metrics.alerts_today || 0;
            }
            if (document.getElementById('alerts-by-algo')) {
                document.getElementById('alerts-by-algo').textContent = metrics.algo_watchlist || 0;
            }
            if (document.getElementById('suspicion-confirmed')) {
                document.getElementById('suspicion-confirmed').textContent = metrics.suspicion_confirmed || 0;
            }
            if (document.getElementById('suspicion-rejected')) {
                document.getElementById('suspicion-rejected').textContent = metrics.suspicion_rejected || 0;
            }
            if (document.getElementById('suspicion-accuracy')) {
                document.getElementById('suspicion-accuracy').textContent = ((metrics.suspicion_accuracy || 0) * 100).toFixed(0) + '%';
            }
            if (document.getElementById('suspicion-recurrence')) {
                document.getElementById('suspicion-recurrence').textContent = metrics.suspicion_recurrence || 0;
            }
            
            // Severity distribution
            if (document.getElementById('severity-critical')) {
                document.getElementById('severity-critical').textContent = metrics.suspicion_critical || 0;
            }
            if (document.getElementById('severity-high')) {
                document.getElementById('severity-high').textContent = metrics.suspicion_high || 0;
            }
            if (document.getElementById('severity-medium')) {
                document.getElementById('severity-medium').textContent = metrics.suspicion_medium || 0;
            }
            if (document.getElementById('severity-low')) {
                document.getElementById('severity-low').textContent = metrics.suspicion_low || 0;
            }
            
            // Alerts per algorithm
            if (document.getElementById('algo-watchlist')) {
                document.getElementById('algo-watchlist').textContent = metrics.algo_watchlist || 0;
            }
            if (document.getElementById('algo-impossible')) {
                document.getElementById('algo-impossible').textContent = metrics.algo_impossible_travel || 0;
            }
            if (document.getElementById('algo-route')) {
                document.getElementById('algo-route').textContent = metrics.algo_route_anomaly || 0;
            }
            if (document.getElementById('algo-convoy')) {
                document.getElementById('algo-convoy').textContent = metrics.algo_convoy || 0;
            }
            if (document.getElementById('algo-roaming')) {
                document.getElementById('algo-roaming').textContent = metrics.algo_roaming || 0;
            }
        }
        
        // Audit tab functionality
        let auditData = [];
        let auditPage = 1;
        const auditPageSize = 50;
        
        async function loadAuditLogs() {
            const group = document.getElementById('audit-group-filter').value;
            const startDate = document.getElementById('audit-start-date').value;
            const endDate = document.getElementById('audit-end-date').value;
            const ttl = document.getElementById('audit-ttl').value;
            
            const params = new URLSearchParams();
            if (group) params.append('resource_type', group);
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', end_date);
            params.append('ttl_days', ttl);
            params.append('page', '1');
            params.append('page_size', '500'); // Get more for export
            
            try {
                const res = await fetch(`/api/v1/audit/logs?${params.toString()}`);
                const data = await res.json();
                
                // Check if server is available
                if (data.error === 'server_unavailable') {
                    // Show server unavailable warning
                    showServerStatus('audit', false, data.message);
                    auditData = [];
                } else {
                    showServerStatus('audit', true, 'Conectado ao servidor');
                    auditData = Array.isArray(data) ? data : (data.data || []);
                }
                
                auditPage = 1;
                renderAuditTable();
            } catch (e) {
                console.error('Audit load error:', e);
                showServerStatus('audit', false, 'Erro de conexão: ' + e.message);
                auditData = [];
                renderAuditTable();
            }
        }
        
        function renderAuditTable() {
            const tbody = document.getElementById('audit-tbody');
            const start = (auditPage - 1) * auditPageSize;
            const end = start + auditPageSize;
            const pageData = auditData.slice(start, end);
            
            if (pageData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="padding: 40px; text-align: center; color: var(--text-secondary);">Nenhum registro encontrado</td></tr>';
            } else {
                tbody.innerHTML = pageData.map(log => `
                    <tr style="border-bottom: 1px solid var(--border);">
                        <td style="padding: 10px 8px;">${log.created_at ? new Date(log.created_at).toLocaleString('pt-BR') : '-'}</td>
                        <td style="padding: 10px 8px;">${log.actor_name || log.actor_user_id || '-'}</td>
                        <td style="padding: 10px 8px;"><span style="background: var(--accent); padding: 2px 8px; border-radius: 4px; font-size: 11px;">${log.action || '-'}</span></td>
                        <td style="padding: 10px 8px;">${log.entity_type || '-'}</td>
                        <td style="padding: 10px 8px; font-family: monospace; font-size: 11px;">${log.entity_id ? String(log.entity_id).substring(0, 8) + '...' : '-'}</td>
                        <td style="padding: 10px 8px; max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${log.justification || (log.details ? JSON.stringify(log.details).substring(0, 50) : '-')}</td>
                    </tr>
                `).join('');
            }
            
            // Update pagination info
            document.getElementById('audit-total').textContent = auditData.length;
            document.getElementById('audit-page').textContent = `Página ${auditPage}`;
            document.getElementById('audit-prev').disabled = auditPage <= 1;
            document.getElementById('audit-next').disabled = end >= auditData.length;
        }
        
        function prevAuditPage() {
            if (auditPage > 1) {
                auditPage--;
                renderAuditTable();
            }
        }
        
        function nextAuditPage() {
            if (auditPage * auditPageSize < auditData.length) {
                auditPage++;
                renderAuditTable();
            }
        }
        
        function exportAudit(format) {
            if (auditData.length === 0) {
                alert('Nenhum dado para exportar. Execute uma busca primeiro.');
                return;
            }
            
            if (format === 'csv') {
                const headers = ['Data/Hora', 'Usuário', 'Ação', 'Tipo', 'Recurso', 'Justificação'];
                const rows = auditData.map(log => [
                    log.created_at || '',
                    log.actor_name || log.actor_user_id || '',
                    log.action || '',
                    log.entity_type || '',
                    log.entity_id || '',
                    log.justification || ''
                ]);
                
                const csv = [headers, ...rows].map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(';')).join('\n');
                downloadFile(csv, 'faro_audit_log.csv', 'text/csv');
            } else {
                const json = JSON.stringify(auditData, null, 2);
                downloadFile(json, 'faro_audit_log.json', 'application/json');
            }
        }
        
        function downloadFile(content, filename, mimeType) {
            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
        
        function resetAuditFilters() {
            document.getElementById('audit-group-filter').value = '';
            document.getElementById('audit-start-date').value = '';
            document.getElementById('audit-end-date').value = '';
            document.getElementById('audit-ttl').value = '30';
            auditData = [];
            auditPage = 1;
            document.getElementById('audit-tbody').innerHTML = '<tr><td colspan="6" style="padding: 40px; text-align: center; color: var(--text-secondary);">Clique em "Buscar" para carregar registros</td></tr>';
            document.getElementById('audit-total').textContent = '0';
        }
        
        // Alert History functionality
        let alertHistoryData = [];
        let alertHistoryPage = 1;
        const alertHistoryPageSize = 50;
        
        async function loadAlertHistory() {
            const alertGroup = document.getElementById('alert-group-filter').value;
            const severity = document.getElementById('alert-severity-filter').value;
            const startDate = document.getElementById('alert-start-date').value;
            const endDate = document.getElementById('alert-end-date').value;
            const ttl = document.getElementById('alert-ttl').value;
            
            const params = new URLSearchParams();
            if (alertGroup) params.append('alert_group', alertGroup);
            if (severity) params.append('severity', severity);
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', end_date);
            if (ttl) params.append('ttl_days', ttl);
            params.append('limit', '500');
            
            try {
                const res = await fetch(`/api/v1/monitoring/history?${params.toString()}`);
                const data = await res.json();
                
                // Check if server is available
                if (data.error === 'server_unavailable') {
                    showServerStatus('alert-history', false, data.message);
                    alertHistoryData = [];
                    updateAlertHistoryStats();
                } else {
                    showServerStatus('alert-history', true, 'Conectado ao servidor');
                    alertHistoryData = Array.isArray(data) ? data : (data.data || []);
                    updateAlertHistoryStats();
                }
                
                alertHistoryPage = 1;
                renderAlertHistoryTable();
            } catch (e) {
                console.error('Alert history load error:', e);
                showServerStatus('alert-history', false, 'Erro de conexão: ' + e.message);
                alertHistoryData = [];
                renderAlertHistoryTable();
            }
        }
        
        function renderAlertHistoryTable() {
            const tbody = document.getElementById('alert-history-tbody');
            const start = (alertHistoryPage - 1) * alertHistoryPageSize;
            const end = start + alertHistoryPageSize;
            const pageData = alertHistoryData.slice(start, end);
            
            if (pageData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="padding: 40px; text-align: center; color: var(--text-secondary);">Nenhum registro encontrado</td></tr>';
            } else {
                tbody.innerHTML = pageData.map(alert => `
                    <tr style="border-bottom: 1px solid var(--border);">
                        <td style="padding: 10px 8px;">${alert.fired_at ? new Date(alert.fired_at).toLocaleString('pt-BR') : '-'}</td>
                        <td style="padding: 10px 8px; font-weight: 600;">${alert.alert_name || '-'}</td>
                        <td style="padding: 10px 8px;">${alert.alert_group || '-'}</td>
                        <td style="padding: 10px 8px;"><span class="severity-${alert.severity}" style="padding: 2px 8px; border-radius: 4px; font-size: 11px;">${alert.severity || '-'}</span></td>
                        <td style="padding: 10px 8px;">${alert.acknowledged ? 'Ack' : (alert.resolved_at ? 'Resolved' : 'Firing')}</td>
                        <td style="padding: 10px 8px; max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${alert.message || alert.insight || '-'}</td>
                    </tr>
                `).join('');
            }
            
            // Update pagination info
            document.getElementById('alert-history-total').textContent = alertHistoryData.length;
            document.getElementById('alert-history-page').textContent = `Página ${alertHistoryPage}`;
            document.getElementById('alert-history-prev').disabled = alertHistoryPage <= 1;
            document.getElementById('alert-history-next').disabled = end >= alertHistoryData.length;
        }
        
        function updateAlertHistoryStats() {
            const total = alertHistoryData.length;
            const critical = alertHistoryData.filter(a => a.severity === 'critical').length;
            const warning = alertHistoryData.filter(a => a.severity === 'warning').length;
            const acknowledged = alertHistoryData.filter(a => a.acknowledged).length;
            
            document.getElementById('stat-total').textContent = total;
            document.getElementById('stat-critical').textContent = critical;
            document.getElementById('stat-warning').textContent = warning;
            document.getElementById('stat-acknowledged').textContent = acknowledged;
        }
        
        function prevAlertHistoryPage() {
            if (alertHistoryPage > 1) {
                alertHistoryPage--;
                renderAlertHistoryTable();
            }
        }
        
        function nextAlertHistoryPage() {
            if (alertHistoryPage * alertHistoryPageSize < alertHistoryData.length) {
                alertHistoryPage++;
                renderAlertHistoryTable();
            }
        }
        
        function exportAlertHistory(format) {
            if (alertHistoryData.length === 0) {
                alert('Nenhum dado para exportar. Execute uma busca primeiro.');
                return;
            }
            
            if (format === 'csv') {
                const headers = ['Data/Hora', 'Alerta', 'Grupo', 'Severidade', 'Status', 'Mensagem'];
                const rows = alertHistoryData.map(alert => [
                    alert.fired_at || '',
                    alert.alert_name || '',
                    alert.alert_group || '',
                    alert.severity || '',
                    alert.acknowledged ? 'Acknowledged' : (alert.resolved_at ? 'Resolved' : 'Firing'),
                    (alert.message || alert.insight || '').replace(/"/g, '""'),
                ]);
                
                const csv = [headers, ...rows].map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(';')).join('\n');
                downloadFile(csv, 'faro_alert_history.csv', 'text/csv');
            } else {
                const json = JSON.stringify(alertHistoryData, null, 2);
                downloadFile(json, 'faro_alert_history.json', 'application/json');
            }
        }
        
        function resetAlertHistoryFilters() {
            document.getElementById('alert-group-filter').value = '';
            document.getElementById('alert-severity-filter').value = '';
            document.getElementById('alert-start-date').value = '';
            document.getElementById('alert-end-date').value = '';
            document.getElementById('alert-ttl').value = '30';
            alertHistoryData = [];
            alertHistoryPage = 1;
            document.getElementById('alert-history-tbody').innerHTML = '<tr><td colspan="6" style="padding: 40px; text-align: center; color: var(--text-secondary);">Clique em "Buscar" para carregar registros</td></tr>';
            document.getElementById('alert-history-total').textContent = '0';
            document.getElementById('stat-total').textContent = '0';
            document.getElementById('stat-critical').textContent = '0';
            document.getElementById('stat-warning').textContent = '0';
            document.getElementById('stat-acknowledged').textContent = '0';
        }
        
        // Server status indicator function
        function showServerStatus(tab, available, message) {
            // Create or update status indicator
            let statusId = tab + '-status';
            let existing = document.getElementById(statusId);
            
            const statusHtml = available 
                ? `<span style="color: var(--success);">●</span> ${message}`
                : `<span style="color: var(--danger);">●</span> ${message}`;
            
            if (existing) {
                existing.innerHTML = statusHtml;
            } else {
                // Add status div to the tab header
                let tabContent = document.getElementById(tab);
                if (tabContent) {
                    let statusDiv = document.createElement('div');
                    statusDiv.id = statusId;
                    statusDiv.style.cssText = 'padding: 10px; margin-bottom: 10px; border-radius: 6px; background: var(--bg-card-hover); font-size: 13px; text-align: center;';
                    statusDiv.innerHTML = statusHtml;
                    tabContent.insertBefore(statusDiv, tabContent.firstChild);
                }
            }
        }
        
        // Start polling and WebSocket immediately (already done in DOMContentLoaded)
        // This is kept as fallback in case DOMContentLoaded already fired
        if (document.readyState === 'complete') {
            // DOMContentLoaded already fired, start manually
            const slider = document.getElementById('refresh-slider');
            if (slider) {
                const idx = parseInt(slider.value);
                startPolling(refreshIntervals[idx]);
                connectWebSocket();
            }
        }
    