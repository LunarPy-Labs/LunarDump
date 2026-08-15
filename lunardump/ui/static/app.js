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
    migration: { title: 'Live Database Migration', desc: 'Direct Server-A to Server-B zero-disk RAM streaming migration' }
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
    if (!healthBody) return;
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

  if (btnRunCheck) {
    btnRunCheck.addEventListener('click', runHealthCheck);
  }


  // 3. Command Builder & Dynamic Parameters Handler
  const cmdUseConfigFile = document.getElementById('cmd-use-config-file');
  const configFileContainer = document.getElementById('config-file-container');
  const directParamContainer = document.getElementById('direct-param-container');
  const secStgContainer = document.getElementById('sec-stg-container');
  const cliPreview = document.getElementById('cli-command-preview');
  const btnCopyCmd = document.getElementById('btn-copy-cmd');
  const btnGenKeyCmd = document.getElementById('btn-gen-key-cmd');
  const cmdSecKey = document.getElementById('cmd-sec-key');

  function updateCLICommandPreview() {
    if (!cliPreview) return;
    const useConfig = cmdUseConfigFile ? cmdUseConfigFile.checked : false;

    if (useConfig) {
      const pathEl = document.getElementById('backup-config-path');
      const path = pathEl ? pathEl.value || 'config.yaml' : 'config.yaml';
      cliPreview.textContent = `lunardump run --config ${path}`;
      return;
    }

    const dbTypeEl = document.getElementById('cmd-db-type');
    const hostEl = document.getElementById('cmd-db-host');
    const nameEl = document.getElementById('cmd-db-name');
    const userEl = document.getElementById('cmd-db-user');
    const portEl = document.getElementById('cmd-db-port');
    const providerEl = document.getElementById('cmd-stg-provider');
    const bucketEl = document.getElementById('cmd-stg-bucket');
    const encryptEl = document.getElementById('cmd-sec-encrypt');

    const dbType = dbTypeEl ? dbTypeEl.value : 'postgres';
    const host = hostEl ? hostEl.value : 'localhost';
    const name = nameEl ? nameEl.value : 'production_db';
    const user = userEl ? userEl.value : 'postgres';
    const port = portEl ? portEl.value : '';
    const provider = providerEl ? providerEl.value : 'local';
    const bucket = bucketEl ? bucketEl.value : './backups';
    const encrypt = encryptEl ? encryptEl.checked : true;
    const key = cmdSecKey ? cmdSecKey.value : '';

    let cmdStr = `lunardump run --db-type ${dbType} --host ${host} --name ${name} --user ${user}`;
    if (port) cmdStr += ` --port ${port}`;
    cmdStr += ` --storage-provider ${provider} --bucket ${bucket}`;
    if (encrypt) {
      cmdStr += ` --encrypt`;
      if (key) cmdStr += ` --key ${key.substring(0, 8)}...`;
    }

    cliPreview.textContent = cmdStr;
  }

  if (cmdUseConfigFile) {
    cmdUseConfigFile.addEventListener('change', (e) => {
      const isChecked = e.target.checked;
      if (isChecked) {
        if (configFileContainer) configFileContainer.classList.remove('hidden');
        if (directParamContainer) directParamContainer.classList.add('hidden');
        if (secStgContainer) secStgContainer.classList.add('hidden');
      } else {
        if (configFileContainer) configFileContainer.classList.add('hidden');
        if (directParamContainer) directParamContainer.classList.remove('hidden');
        if (secStgContainer) secStgContainer.classList.remove('hidden');
      }
      updateCLICommandPreview();
    });
  }

  // Attach live update listeners to all input elements
  const inputsToWatch = [
    'cmd-db-type', 'cmd-db-host', 'cmd-db-name', 'cmd-db-user', 'cmd-db-port',
    'cmd-stg-provider', 'cmd-stg-bucket', 'cmd-sec-encrypt', 'cmd-sec-key', 'backup-config-path'
  ];
  inputsToWatch.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('input', updateCLICommandPreview);
      el.addEventListener('change', updateCLICommandPreview);
    }
  });

  if (btnGenKeyCmd && cmdSecKey) {
    btnGenKeyCmd.addEventListener('click', () => {
      const randomHex = Array.from(window.crypto.getRandomValues(new Uint8Array(32)))
        .map(b => b.toString(16).padStart(2, '0')).join('');
      cmdSecKey.value = randomHex;
      updateCLICommandPreview();
    });
  }

  if (btnCopyCmd && cliPreview) {
    btnCopyCmd.addEventListener('click', () => {
      navigator.clipboard.writeText(cliPreview.textContent);
      btnCopyCmd.textContent = '✓ Copied!';
      setTimeout(() => { btnCopyCmd.textContent = '📋 Copy Command'; }, 2000);
    });
  }

  // 4. WebSocket Live Terminal Connection & Backup Runner
  const backupTerminal = document.getElementById('backup-terminal');
  const migrationTerminal = document.getElementById('migration-terminal');
  const btnStartBackup = document.getElementById('btn-start-backup');
  const btnDryrunBackup = document.getElementById('btn-dryrun-backup');
  const formCmdRunner = document.getElementById('form-cmd-runner');
  let socket = null;

  function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/logs`;

    socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
      if (backupTerminal) {
        backupTerminal.textContent += '\n' + event.data;
        backupTerminal.scrollTop = backupTerminal.scrollHeight;
      }
      if (migrationTerminal) {
        migrationTerminal.textContent += '\n' + event.data;
        migrationTerminal.scrollTop = migrationTerminal.scrollHeight;
      }
    };

    socket.onclose = () => {
      setTimeout(connectWebSocket, 3000);
    };
  }

  connectWebSocket();

  async function triggerBackup(dryRun = false) {
    if (!backupTerminal) return;
    const useConfigFile = cmdUseConfigFile ? cmdUseConfigFile.checked : false;
    const modeName = dryRun ? 'DRY-RUN' : 'FULL BACKUP';
    let payload = { dry_run: dryRun };

    if (useConfigFile) {
      const pathEl = document.getElementById('backup-config-path');
      const configPath = pathEl ? pathEl.value || 'config.yaml' : 'config.yaml';
      payload.config_path = configPath;
      backupTerminal.textContent += `\n[${new Date().toLocaleTimeString()}] 🚀 Triggering ${modeName} (Config: ${configPath})...`;
    } else {
      const dbTypeEl = document.getElementById('cmd-db-type');
      const dbHostEl = document.getElementById('cmd-db-host');
      const dbNameEl = document.getElementById('cmd-db-name');
      const dbUserEl = document.getElementById('cmd-db-user');
      const dbPassEl = document.getElementById('cmd-db-pass');
      const dbPortEl = document.getElementById('cmd-db-port');
      const stgProvEl = document.getElementById('cmd-stg-provider');
      const stgBuckEl = document.getElementById('cmd-stg-bucket');
      const secEncEl = document.getElementById('cmd-sec-encrypt');

      payload.db_type = dbTypeEl ? dbTypeEl.value : 'postgres';
      payload.db_host = dbHostEl ? dbHostEl.value : 'localhost';
      payload.db_name = dbNameEl ? dbNameEl.value : 'production_db';
      payload.db_user = dbUserEl ? dbUserEl.value : 'postgres';
      payload.db_password = dbPassEl ? dbPassEl.value || null : null;
      
      const portVal = dbPortEl ? dbPortEl.value : '';
      payload.db_port = portVal ? parseInt(portVal, 10) : null;

      payload.storage_provider = stgProvEl ? stgProvEl.value : 'local';
      payload.storage_bucket = stgBuckEl ? stgBuckEl.value : './backups';
      payload.encrypt = secEncEl ? secEncEl.checked : true;
      payload.encryption_key = cmdSecKey ? cmdSecKey.value || null : null;

      backupTerminal.textContent += `\n[${new Date().toLocaleTimeString()}] 🚀 Triggering ${modeName} for Engine [${payload.db_type.toUpperCase()}] DB: ${payload.db_name}...`;
    }

    backupTerminal.scrollTop = backupTerminal.scrollHeight;

    try {
      const res = await fetch('/api/backup/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        backupTerminal.textContent += `\n[${new Date().toLocaleTimeString()}] ✓ ${data.message}`;
      } else {
        backupTerminal.textContent += `\n[${new Date().toLocaleTimeString()}] ⚠️ Warning/Error: ${data.message || data.detail || 'Backup execution failed'}`;
      }
    } catch (err) {
      backupTerminal.textContent += `\n[${new Date().toLocaleTimeString()}] ❌ Network Error: ${err.message}`;
    }
    backupTerminal.scrollTop = backupTerminal.scrollHeight;
  }

  if (formCmdRunner) {
    formCmdRunner.addEventListener('submit', (e) => {
      e.preventDefault();
      triggerBackup(false);
    });
  }

  if (btnDryrunBackup) {
    btnDryrunBackup.addEventListener('click', (e) => {
      e.preventDefault();
      triggerBackup(true);
    });
  }

  // 5. Template Generator Form Handler
  const formGenerate = document.getElementById('form-generate');
  const genResult = document.getElementById('gen-result');
  const genKeyDisplay = document.getElementById('gen-key-display');

  if (formGenerate) {
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
          if (genKeyDisplay) genKeyDisplay.textContent = data.generated_key;
          if (genResult) genResult.classList.remove('hidden');
        } else {
          alert(`Generator Error: ${data.detail || 'Failed to generate templates'}`);
        }
      } catch (err) {
        alert(`Network Error: ${err.message}`);
      }
    });
  }

  // 6. Live Migration Form Handler
  async function triggerMigration(dryRun = false) {
    const term = document.getElementById('migration-terminal');

    const srcType = document.getElementById('mig-src-type')?.value || 'postgres';
    const srcHost = document.getElementById('mig-src-host')?.value || 'localhost';
    const srcPortVal = document.getElementById('mig-src-port')?.value;
    const srcName = document.getElementById('mig-src-name')?.value || 'production_db';
    const srcUser = document.getElementById('mig-src-user')?.value || 'postgres';
    const srcPass = document.getElementById('mig-src-pass')?.value || null;

    const tgtType = document.getElementById('mig-tgt-type')?.value || 'postgres';
    const tgtHost = document.getElementById('mig-tgt-host')?.value || 'localhost';
    const tgtPortVal = document.getElementById('mig-tgt-port')?.value;
    const tgtName = document.getElementById('mig-tgt-name')?.value || 'destination_db';
    const tgtUser = document.getElementById('mig-tgt-user')?.value || 'postgres';
    const tgtPass = document.getElementById('mig-tgt-pass')?.value || null;

    const payload = {
      source_type: srcType,
      source_host: srcHost,
      source_port: srcPortVal ? parseInt(srcPortVal, 10) : null,
      source_name: srcName,
      source_user: srcUser,
      source_password: srcPass,
      target_type: tgtType,
      target_host: tgtHost,
      target_port: tgtPortVal ? parseInt(tgtPortVal, 10) : null,
      target_name: tgtName,
      target_user: tgtUser,
      target_password: tgtPass,
      dry_run: dryRun,
    };

    const modeName = dryRun ? 'DRY-RUN' : 'LIVE MIGRATION';

    if (term) {
      term.textContent += `\n[${new Date().toLocaleTimeString()}] 🚀 Initiating ${modeName} Stream...`;
      term.textContent += `\n[${new Date().toLocaleTimeString()}] 📤 Source DB (${srcType.toUpperCase()}): ${srcUser}@${srcHost}:${srcPortVal || 'default'}/${srcName}`;
      term.textContent += `\n[${new Date().toLocaleTimeString()}] 📥 Target DB (${tgtType.toUpperCase()}): ${tgtUser}@${tgtHost}:${tgtPortVal || 'default'}/${tgtName}`;
      term.scrollTop = term.scrollHeight;
    }

    try {
      const res = await fetch('/api/migration/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        if (term) {
          term.textContent += `\n[${new Date().toLocaleTimeString()}] ✓ ${data.message || 'Live DB Migration executed successfully!'}`;
          term.scrollTop = term.scrollHeight;
        } else {
          alert(`✓ Migration Success: ${data.message}`);
        }
      } else {
        const errMsg = data.message || data.detail || 'Execution failure';
        if (term) {
          term.textContent += `\n[${new Date().toLocaleTimeString()}] ⚠️ Migration Result (${(data.status || 'ERROR').toUpperCase()}): ${errMsg}`;
          term.scrollTop = term.scrollHeight;
        } else {
          alert(`⚠️ Migration Result: ${errMsg}`);
        }
      }
    } catch (err) {
      if (term) {
        term.textContent += `\n[${new Date().toLocaleTimeString()}] ❌ Network Error: ${err.message}`;
        term.scrollTop = term.scrollHeight;
      } else {
        alert(`❌ Network Error: ${err.message}`);
      }
    }
  }

  const formMigrate = document.getElementById('form-migrate');
  if (formMigrate) {
    formMigrate.addEventListener('submit', (e) => {
      e.preventDefault();
      triggerMigration(false);
    });
  }

  const btnDryrunMigrate = document.getElementById('btn-dryrun-migrate');
  if (btnDryrunMigrate) {
    btnDryrunMigrate.addEventListener('click', (e) => {
      e.preventDefault();
      triggerMigration(true);
    });
  }




  // 7. Cloud Storage File List
  const btnLoadStorage = document.getElementById('btn-load-storage');
  const storageBody = document.getElementById('storage-body');

  async function loadStorageFiles() {
    if (!storageBody) return;
    storageBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Fetching cloud storage archives...</td></tr>';
    try {
      const provider = document.getElementById('cmd-stg-provider')?.value || 'local';
      const bucket = document.getElementById('cmd-stg-bucket')?.value || './backups';
      const url = `/api/storage/files?provider=${encodeURIComponent(provider)}&bucket=${encodeURIComponent(bucket)}`;

      const res = await fetch(url);
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
        storageBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No backup archives found in target location.</td></tr>';
      }
    } catch (err) {
      storageBody.innerHTML = `<tr><td colspan="4" class="text-center text-error">Network Error: ${err.message}</td></tr>`;
    }
  }

  if (btnLoadStorage) {
    btnLoadStorage.addEventListener('click', loadStorageFiles);
  }

  // 8. Daemon & Cron Schedule Expression Parser
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
        if (resCronSyntax) resCronSyntax.textContent = data.cron_expr;
        if (resCronDesc) resCronDesc.textContent = data.description;
        if (resCronRuns) resCronRuns.innerHTML = data.next_runs.map(run => `<li>🕒 ${run}</li>`).join('');
        if (cronResultCard) cronResultCard.style.display = 'block';
      } else {
        if (resCronSyntax) resCronSyntax.textContent = 'ERROR';
        if (resCronDesc) resCronDesc.textContent = data.message || 'Failed to parse expression';
        if (resCronRuns) resCronRuns.innerHTML = '';
        if (cronResultCard) cronResultCard.style.display = 'block';
      }
    } catch (err) {
      alert(`Error parsing cron: ${err.message}`);
    }
  }

  cronBadges.forEach(badge => {
    badge.addEventListener('click', () => {
      const expr = badge.getAttribute('data-expr');
      if (cronExpressionInput) cronExpressionInput.value = expr;
      parseCron(expr);
    });
  });

  if (btnParseCron) {
    btnParseCron.addEventListener('click', () => {
      if (cronExpressionInput) parseCron(cronExpressionInput.value);
    });
  }

  // Initialize defaults on page load
  if (healthBody) runHealthCheck();
  updateCLICommandPreview();

});

