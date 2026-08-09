document.addEventListener('DOMContentLoaded', () => {
  // 1. Tab Switching Logic
  const navItems = document.querySelectorAll('.nav-item');
  const tabContents = document.querySelectorAll('.tab-content');
  const pageTitle = document.getElementById('page-title');
  const pageDesc = document.getElementById('page-desc');

  const tabTitles = {
    dashboard: { title: 'Dashboard Overview', desc: 'System health, engine metrics, and active backup status' },
    generator: { title: 'Template Generator', desc: 'Instant 1-click generator for config.yaml, migration.yaml, and .env' },
    backup: { title: 'Backup Runner', desc: 'Execute on-demand backup pipeline with live log output' },
    migration: { title: 'Live Database Migration', desc: 'Direct Server-A to Server-B zero-disk RAM streaming migration' },
    restore: { title: 'Cloud Restore Archives', desc: 'Inspect remote backup archives and trigger direct database injection' },
    cron: { title: 'Daemon & Schedule Manager', desc: 'Configure and monitor continuous background backup schedules (--cron)' }
  };

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      const btn = e.currentTarget;
      const targetTab = btn.getAttribute('data-tab');

      navItems.forEach(i => i.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const targetContent = document.getElementById(`tab-${targetTab}`);
      if (targetContent) {
        targetContent.classList.add('active');
      }

      if (tabTitles[targetTab]) {
        pageTitle.textContent = tabTitles[targetTab].title;
        pageDesc.textContent = tabTitles[targetTab].desc;
      }
    });
  });

  // 2. Health Diagnostic Check
  const btnRunCheck = document.getElementById('btn-run-check');
  const healthBody = document.getElementById('health-body');

  async function runHealthCheck() {
    healthBody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Running system diagnostics...</td></tr>';
    try {
      const res = await fetch('/api/health');
      const data = await res.json();

      if (data.components && data.components.length > 0) {
        healthBody.innerHTML = data.components.map(c => `
          <tr>
            <td><strong>${c.name}</strong></td>
            <td class="text-muted">${c.details}</td>
            <td><span class="badge ${c.status.includes('VALID') || c.status.includes('INSTALLED') || c.status.includes('CONNECTED') || c.status.includes('REACHABLE') ? 'badge-primary' : 'badge-secondary'}">${c.status}</span></td>
          </tr>
        `).join('');
      } else {
        healthBody.innerHTML = `<tr><td colspan="3" class="text-center text-muted">${data.message || 'No health data available'}</td></tr>`;
      }
    } catch (err) {
      healthBody.innerHTML = `<tr><td colspan="3" class="text-center text-error">Error connecting to health API: ${err.message}</td></tr>`;
    }
  }

  btnRunCheck.addEventListener('click', runHealthCheck);

  // 3. Template Generator Form Handler
  const formGenerate = document.getElementById('form-generate');
  const genResult = document.getElementById('gen-result');
  const genKeyDisplay = document.getElementById('gen-key-display');

  formGenerate.addEventListener('submit', async (e) => {
    e.preventDefault();
    const dbType = document.getElementById('gen-db-type').value;
    const storage = document.getElementById('gen-storage').value;
    const force = document.getElementById('gen-force').checked;

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ db_type: dbType, storage: storage, force: force })
      });

      const data = await res.json();
      if (res.ok) {
        genKeyDisplay.textContent = data.generated_key;
        genResult.classList.remove('hidden');
      } else {
        alert(`Generator Error: ${data.detail || 'Failed to generate templates'}`);
      }
    } catch (err) {
      alert(`Network Error: ${err.message}`);
    }
  });

  // 4. WebSocket Live Terminal Connection & Backup Runner
  const backupTerminal = document.getElementById('backup-terminal');
  const btnStartBackup = document.getElementById('btn-start-backup');
  const btnDryrunBackup = document.getElementById('btn-dryrun-backup');
  const backupConfigPath = document.getElementById('backup-config-path');
  let socket = null;

  function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/logs`;

    socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
      backupTerminal.textContent += '\n' + event.data;
      backupTerminal.scrollTop = backupTerminal.scrollHeight;
    };

    socket.onclose = () => {
      setTimeout(connectWebSocket, 3000);
    };
  }

  connectWebSocket();

  async function triggerBackup(dryRun = false) {
    const configPath = backupConfigPath ? backupConfigPath.value : 'config.yaml';
    const modeName = dryRun ? 'DRY-RUN' : 'FULL BACKUP';

    backupTerminal.textContent += `\n[${new Date().toLocaleTimeString()}] 🚀 Triggering ${modeName} (Profile: ${configPath})...`;
    backupTerminal.scrollTop = backupTerminal.scrollHeight;

    try {
      const res = await fetch('/api/backup/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config_path: configPath, dry_run: dryRun })
      });
      const data = await res.json();
      if (res.ok) {
        backupTerminal.textContent += `\n[${new Date().toLocaleTimeString()}] ✓ ${data.message}`;
      } else {
        backupTerminal.textContent += `\n[${new Date().toLocaleTimeString()}] ❌ Error: ${data.detail || 'Backup execution failed'}`;
      }
    } catch (err) {
      backupTerminal.textContent += `\n[${new Date().toLocaleTimeString()}] ❌ Network Error: ${err.message}`;
    }
    backupTerminal.scrollTop = backupTerminal.scrollHeight;
  }

  if (btnStartBackup) {
    btnStartBackup.addEventListener('click', () => triggerBackup(false));
  }
  if (btnDryrunBackup) {
    btnDryrunBackup.addEventListener('click', () => triggerBackup(true));
  }

  // 5. Live Migration Form Handler
  const formMigrate = document.getElementById('form-migrate');
  formMigrate.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      source_type: document.getElementById('mig-src-type').value,
      source_host: document.getElementById('mig-src-host').value,
      source_name: document.getElementById('mig-src-name').value,
      source_password: document.getElementById('mig-src-pass').value,
      target_type: document.getElementById('mig-tgt-type').value,
      target_host: document.getElementById('mig-tgt-host').value,
      target_name: document.getElementById('mig-tgt-name').value,
      target_password: document.getElementById('mig-tgt-pass').value,
    };

    try {
      const res = await fetch('/api/migration/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        alert('🚀 Live DB Migration Launched Successfully!');
      } else {
        alert(`Migration Error: ${data.detail || 'Migration execution failed'}`);
      }
    } catch (err) {
      alert(`Network Error: ${err.message}`);
    }
  });

  // 6. Cloud Storage File List
  const btnLoadStorage = document.getElementById('btn-load-storage');
  const storageBody = document.getElementById('storage-body');

  async function loadStorageFiles() {
    storageBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Fetching cloud storage archives...</td></tr>';
    try {
      const res = await fetch('/api/storage/files');
      const data = await res.json();

      if (data.status === 'success' && data.files && data.files.length > 0) {
        storageBody.innerHTML = data.files.map(f => `
          <tr>
            <td><code>${f.key || f.path || f}</code></td>
            <td>${f.size || 'N/A'}</td>
            <td>${f.last_modified || 'N/A'}</td>
            <td><button class="btn btn-secondary btn-sm">Restore</button></td>
          </tr>
        `).join('');
      } else if (data.status === 'error' || data.status === 'warning') {
        storageBody.innerHTML = `<tr><td colspan="4" class="text-center text-error">⚠️ ${data.message}</td></tr>`;
      } else {
        storageBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No backup archives found in cloud bucket.</td></tr>';
      }
    } catch (err) {
      storageBody.innerHTML = `<tr><td colspan="4" class="text-center text-error">Network Error: ${err.message}</td></tr>`;
    }
  }

  if (btnLoadStorage) {
    btnLoadStorage.addEventListener('click', loadStorageFiles);
  }

  // 7. Daemon & Cron Schedule Expression Parser
  const cronBadges = document.querySelectorAll('.cron-badge');
  const cronExpressionInput = document.getElementById('cron-expression');
  const btnParseCron = document.getElementById('btn-parse-cron');
  const cronResultCard = document.getElementById('cron-result-card');
  const resCronSyntax = document.getElementById('res-cron-syntax');
  const resCronDesc = document.getElementById('res-cron-desc');
  const resCronRuns = document.getElementById('res-cron-runs');

  async function parseCron(expr) {
    if (!expr) return;
    try {
      const res = await fetch(`/api/cron/parse?expression=${encodeURIComponent(expr)}`);
      const data = await res.json();
      
      if (data.status === 'success') {
        resCronSyntax.textContent = data.cron_expr;
        resCronDesc.textContent = data.description;
        resCronRuns.innerHTML = data.next_runs.map(run => `<li>🕒 ${run}</li>`).join('');
        cronResultCard.style.display = 'block';
      } else {
        resCronSyntax.textContent = 'ERROR';
        resCronDesc.textContent = data.message || 'Failed to parse expression';
        resCronRuns.innerHTML = '';
        cronResultCard.style.display = 'block';
      }
    } catch (err) {
      alert(`Error parsing cron: ${err.message}`);
    }
  }

  cronBadges.forEach(badge => {
    badge.addEventListener('click', () => {
      const expr = badge.getAttribute('data-expr');
      cronExpressionInput.value = expr;
      parseCron(expr);
    });
  });

  if (btnParseCron) {
    btnParseCron.addEventListener('click', () => {
      parseCron(cronExpressionInput.value);
    });
  }
});
