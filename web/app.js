/**
 * Multi-Agent Code Helper Studio - Client Application
 * Handles:
 * - Codebase Upload (.zip and .py) with AST indexing & live flowchart rendering
 * - Dynamic Canvas Routing Visualizer with 2x2 spacious agent nodes & Bézier particle physics
 * - Live Architecture Graph with Mermaid.js, SVG pan/zoom controls
 * - Interactive Dialogue Console with agent attribution & tool telemetry
 * - Stage View Tabs (Architecture Diagram / Multi-Agent Team / Split View / Files Explorer)
 * - Health Check Diagnostic modal & live backend status
 */

// ===================================================================
// 1. ROUTING VISUALIZER (Canvas Bézier Curves & Particle Physics)
// ===================================================================
class RoutingVisualizer {
  constructor(canvasId, containerId) {
    this.canvas = document.getElementById(canvasId);
    this.container = document.getElementById(containerId);
    if (!this.canvas || !this.container) return;

    this.ctx = this.canvas.getContext('2d');
    this.bossNode = document.getElementById('node-coordinator');
    this.workerNodes = {
      code_searcher: {
        el: document.getElementById('node-code_searcher'),
        color: '#06B6D4',
        glow: 'rgba(6, 182, 212, 0.6)'
      },
      architecture_mapper: {
        el: document.getElementById('node-architecture_mapper'),
        color: '#10B981',
        glow: 'rgba(16, 185, 129, 0.6)'
      },
      onboarding_guide: {
        el: document.getElementById('node-onboarding_guide'),
        color: '#8B5CF6',
        glow: 'rgba(139, 92, 246, 0.6)'
      },
      code_explainer: {
        el: document.getElementById('node-code_explainer'),
        color: '#3B82F6',
        glow: 'rgba(59, 130, 246, 0.6)'
      }
    };

    this.particles = [];
    this.activeAgent = null;
    this.activeTimeout = null;

    this.initCanvas();
    window.addEventListener('resize', () => this.initCanvas());
    this.startAnimation();
  }

  initCanvas() {
    if (!this.canvas || !this.container) return;
    const rect = this.container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    this.ctx.scale(dpr, dpr);
    this.width = rect.width;
    this.height = rect.height;
  }

  getNodeAnchors() {
    if (!this.container || !this.bossNode) return null;
    const containerRect = this.container.getBoundingClientRect();
    const bossRect = this.bossNode.getBoundingClientRect();

    const bossAnchor = {
      x: bossRect.left + bossRect.width / 2 - containerRect.left,
      y: bossRect.bottom - containerRect.top
    };

    const workerAnchors = {};
    for (const [key, worker] of Object.entries(this.workerNodes)) {
      if (worker.el) {
        const wRect = worker.el.getBoundingClientRect();
        workerAnchors[key] = {
          x: wRect.left + wRect.width / 2 - containerRect.left,
          y: wRect.top - containerRect.top,
          color: worker.color,
          glow: worker.glow
        };
      }
    }

    return { boss: bossAnchor, workers: workerAnchors };
  }

  triggerDelegation(agentName) {
    this.clearActive();
    this.activeAgent = agentName;

    const target = this.workerNodes[agentName];
    if (target && target.el) {
      target.el.classList.add('active-worker');
    }

    for (let i = 0; i < 20; i++) {
      this.particles.push({
        agent: agentName,
        t: Math.random() * 0.2,
        speed: 0.015 + Math.random() * 0.012,
        size: 3.5 + Math.random() * 2,
        color: target ? target.color : '#F59E0B'
      });
    }

    if (this.activeTimeout) clearTimeout(this.activeTimeout);
    this.activeTimeout = setTimeout(() => {
      this.clearActive();
    }, 4500);
  }

  clearActive() {
    this.activeAgent = null;
    for (const worker of Object.values(this.workerNodes)) {
      if (worker.el) worker.el.classList.remove('active-worker');
    }
  }

  startAnimation() {
    let tick = 0;

    const render = () => {
      tick++;
      this.ctx.clearRect(0, 0, this.width, this.height);

      const anchors = this.getNodeAnchors();
      if (!anchors) {
        requestAnimationFrame(render);
        return;
      }

      const { boss, workers } = anchors;

      for (const [key, target] of Object.entries(workers)) {
        const isActive = this.activeAgent === key;
        const dy = target.y - boss.y;

        const cp1x = boss.x;
        const cp1y = boss.y + dy * 0.45;
        const cp2x = target.x;
        const cp2y = target.y - dy * 0.45;

        this.ctx.beginPath();
        this.ctx.moveTo(boss.x, boss.y);
        this.ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, target.x, target.y);
        this.ctx.strokeStyle = isActive
          ? target.color
          : 'rgba(255, 255, 255, 0.09)';
        this.ctx.lineWidth = isActive ? 3 : 1.5;
        if (isActive) {
          this.ctx.shadowColor = target.glow;
          this.ctx.shadowBlur = 12;
        } else {
          this.ctx.shadowBlur = 0;
        }
        this.ctx.stroke();
        this.ctx.shadowBlur = 0;

        if (tick % 70 === 0 && !this.activeAgent) {
          this.particles.push({
            agent: key,
            t: 0,
            speed: 0.005 + Math.random() * 0.003,
            size: 2,
            color: target.color
          });
        }
      }

      for (let i = this.particles.length - 1; i >= 0; i--) {
        const p = this.particles[i];
        p.t += p.speed;

        if (p.t >= 1) {
          this.particles.splice(i, 1);
          continue;
        }

        const target = workers[p.agent];
        if (!target) {
          this.particles.splice(i, 1);
          continue;
        }

        const dy = target.y - boss.y;
        const cp1x = boss.x;
        const cp1y = boss.y + dy * 0.45;
        const cp2x = target.x;
        const cp2y = target.y - dy * 0.45;

        const u = 1 - p.t;
        const px =
          u * u * u * boss.x +
          3 * u * u * p.t * cp1x +
          3 * u * p.t * p.t * cp2x +
          p.t * p.t * p.t * target.x;
        const py =
          u * u * u * boss.y +
          3 * u * u * p.t * cp1y +
          3 * u * p.t * p.t * cp2y +
          p.t * p.t * p.t * target.y;

        this.ctx.beginPath();
        this.ctx.arc(px, py, p.size, 0, Math.PI * 2);
        this.ctx.fillStyle = p.color;
        this.ctx.shadowColor = p.color;
        this.ctx.shadowBlur = 8;
        this.ctx.fill();
        this.ctx.shadowBlur = 0;
      }

      requestAnimationFrame(render);
    };

    requestAnimationFrame(render);
  }
}

// ===================================================================
// 2. DIAGRAM VIEWER (Mermaid Live Flowchart & Pan / Zoom Engine)
// ===================================================================
class DiagramViewer {
  constructor() {
    this.container = document.getElementById('diagram-container');
    this.viewport = document.getElementById('diagram-viewport');
    this.fileSelect = document.getElementById('arch-file-select');
    this.btnZoomIn = document.getElementById('btn-zoom-in');
    this.btnZoomOut = document.getElementById('btn-zoom-out');
    this.btnZoomReset = document.getElementById('btn-zoom-reset');
    this.btnRefresh = document.getElementById('btn-refresh-diagram');

    this.zoomLevel = 1.0;
    this.panX = 0;
    this.panY = 0;
    this.isDragging = false;
    this.dragStartX = 0;
    this.dragStartY = 0;
    this.hasLoaded = false;
    this.currentMermaidCode = null;
    this.currentFile = '';

    this.initMermaid();
    this.bindEvents();
    // Pre-fetch diagram in background so switching to Diagram view is instant
    this.fetchDiagram();
  }

  initMermaid() {
    if (window.mermaid) {
      window.mermaid.initialize({
        startOnLoad: false,
        theme: 'dark',
        themeVariables: {
          darkMode: true,
          background: '#0B0F19',
          primaryColor: '#1E293B',
          primaryTextColor: '#F8FAFC',
          primaryBorderColor: '#6366F1',
          lineColor: '#38BDF8',
          secondaryColor: '#0F172A',
          tertiaryColor: '#1E1B4B'
        },
        flowchart: {
          curve: 'basis',
          htmlLabels: true
        }
      });
    }
  }

  bindEvents() {
    if (this.fileSelect) {
      this.fileSelect.addEventListener('change', (e) => {
        this.fetchDiagram(e.target.value);
      });
    }

    if (this.btnZoomIn) {
      this.btnZoomIn.addEventListener('click', () => this.zoom(0.2));
    }
    if (this.btnZoomOut) {
      this.btnZoomOut.addEventListener('click', () => this.zoom(-0.2));
    }
    if (this.btnZoomReset) {
      this.btnZoomReset.addEventListener('click', () => this.resetTransform());
    }
    if (this.btnRefresh) {
      this.btnRefresh.addEventListener('click', () => this.fetchDiagram(this.currentFile));
    }

    if (this.viewport) {
      this.viewport.addEventListener('mousedown', (e) => {
        if (e.target.closest('button') || e.target.closest('select')) return;
        this.isDragging = true;
        this.dragStartX = e.clientX - this.panX;
        this.dragStartY = e.clientY - this.panY;
        this.viewport.style.cursor = 'grabbing';
      });

      window.addEventListener('mousemove', (e) => {
        if (!this.isDragging) return;
        this.panX = e.clientX - this.dragStartX;
        this.panY = e.clientY - this.dragStartY;
        this.applyTransform();
      });

      window.addEventListener('mouseup', () => {
        this.isDragging = false;
        if (this.viewport) this.viewport.style.cursor = 'grab';
      });

      this.viewport.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY < 0 ? 0.1 : -0.1;
        this.zoom(delta);
      }, { passive: false });
    }
  }

  zoom(delta) {
    this.zoomLevel = Math.min(Math.max(0.3, this.zoomLevel + delta), 3.0);
    this.applyTransform();
  }

  resetTransform() {
    this.zoomLevel = 1.0;
    this.panX = 0;
    this.panY = 0;
    this.applyTransform();
  }

  applyTransform() {
    if (this.container) {
      this.container.style.transform = `translate(${this.panX}px, ${this.panY}px) scale(${this.zoomLevel})`;
    }
  }

  async renderMermaidCode(mermaidCode) {
    if (!this.container || !mermaidCode) return;
    try {
      let diagramCode = mermaidCode.trim();
      if (diagramCode.startsWith('```mermaid')) {
        diagramCode = diagramCode.replace(/^```mermaid\s*/, '').replace(/```$/, '').trim();
      } else if (diagramCode.startsWith('```')) {
        diagramCode = diagramCode.replace(/^```\s*/, '').replace(/```$/, '').trim();
      }

      this.currentMermaidCode = diagramCode;
      const id = 'mermaid-svg-' + Date.now();
      const { svg } = await window.mermaid.render(id, diagramCode);
      this.container.innerHTML = svg;
      this.hasLoaded = true;
      this.resetTransform();
    } catch (err) {
      console.warn('Direct Mermaid rendering warning:', err);
      this.fetchDiagram(this.currentFile);
    }
  }

  async fetchDiagram(fileName = null) {
    if (!this.container) return;
    const target = fileName !== null ? fileName : (this.fileSelect ? this.fileSelect.value : '');
    this.currentFile = target;

    if (this.fileSelect && this.fileSelect.value !== target) {
      this.fileSelect.value = target;
    }

    const loadMsg = target
      ? `Generating dedicated architecture diagram for ${target}...`
      : 'Generating live project dependency flowchart...';

    this.container.innerHTML = `
      <div class="diagram-loading">
        <i class="fa-solid fa-circle-notch fa-spin"></i>
        <span>${loadMsg}</span>
      </div>
    `;

    try {
      const url = target ? `/api/diagram?file=${encodeURIComponent(target)}` : '/api/diagram';
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const rawDiagram = data.mermaid || data.diagram || '';

      await this.renderMermaidCode(rawDiagram);
      this.hasLoaded = true;
    } catch (err) {
      console.error('Failed to load diagram:', err);
      this.container.innerHTML = `
        <div style="color: #F87171; font-size: 0.85rem; text-align: center; padding: 20px;">
          <i class="fa-solid fa-triangle-exclamation" style="font-size: 1.5rem; margin-bottom: 8px;"></i>
          <p>Failed to generate architecture flowchart.</p>
          <span style="font-size: 0.75rem; color: var(--text-muted);">${err.message}</span>
        </div>
      `;
    }
  }

  updateFileList(files = []) {
    if (!this.fileSelect || !files) return;
    const currentVal = this.fileSelect.value;
    let html = '<option value="">🌐 Entire Project (Dependencies)</option>';
    html += '<option value="__orchestration__">⚡ Multi-Agent System Architecture</option>';
    files.forEach((f) => {
      const name = typeof f === 'string' ? f : (f.name || f.path || '');
      if (name && name.endsWith('.py')) {
        const isSel = name === currentVal ? 'selected' : '';
        html += `<option value="${name}" ${isSel}>📄 ${name}</option>`;
      }
    });
    this.fileSelect.innerHTML = html;
    if (currentVal) this.fileSelect.value = currentVal;
  }
}

// ===================================================================
// 3. TOP VIEW SWITCHER (Studio Chat vs Full-Screen Architecture Diagram)
// ===================================================================
class TopViewSwitcher {
  constructor(routingVisualizer, diagramViewer) {
    this.routingVisualizer = routingVisualizer;
    this.diagramViewer = diagramViewer;

    this.btnChat = document.getElementById('nav-btn-chat');
    this.btnDiagram = document.getElementById('nav-btn-diagram');
    this.viewChat = document.getElementById('view-studio-chat');
    this.viewDiagram = document.getElementById('view-architecture-diagram');
    this.btnBackToChat = document.getElementById('btn-back-to-chat');
    this.btnQuickOpen = document.getElementById('btn-quick-open-diagram');
    this.archCodebaseTag = document.getElementById('arch-codebase-tag');

    this.activeView = 'chat';
    this.bindEvents();
  }

  bindEvents() {
    if (this.btnChat) {
      this.btnChat.addEventListener('click', () => this.switchView('chat'));
    }
    if (this.btnDiagram) {
      this.btnDiagram.addEventListener('click', () => this.switchView('diagram'));
    }
    if (this.btnBackToChat) {
      this.btnBackToChat.addEventListener('click', () => this.switchView('chat'));
    }
    if (this.btnQuickOpen) {
      this.btnQuickOpen.addEventListener('click', () => this.switchView('diagram'));
    }
  }

  switchView(viewName) {
    this.activeView = viewName;

    if (viewName === 'chat') {
      if (this.btnChat) this.btnChat.classList.add('active');
      if (this.btnDiagram) this.btnDiagram.classList.remove('active');

      if (this.viewChat) this.viewChat.style.display = 'grid';
      if (this.viewDiagram) this.viewDiagram.style.display = 'none';

      // Re-anchor routing canvas particles
      setTimeout(() => {
        if (this.routingVisualizer) this.routingVisualizer.initCanvas();
      }, 50);
    } else if (viewName === 'diagram') {
      if (this.btnChat) this.btnChat.classList.remove('active');
      if (this.btnDiagram) this.btnDiagram.classList.add('active');

      if (this.viewChat) this.viewChat.style.display = 'none';
      if (this.viewDiagram) this.viewDiagram.style.display = 'flex';

      // Update codebase tag in diagram view header
      const activeRepoName = document.getElementById('active-repo-name');
      if (this.archCodebaseTag && activeRepoName) {
        this.archCodebaseTag.textContent = activeRepoName.textContent;
      }

      if (this.diagramViewer) {
        if (!this.diagramViewer.hasLoaded) {
          this.diagramViewer.fetchDiagram();
        } else {
          this.diagramViewer.resetTransform();
        }
      }
    }
  }
}

// ===================================================================
// 4. STAGE SUBTAB CONTROLLER (Multi-Agent Team vs Codebase Files)
// ===================================================================
class StageTabController {
  constructor(routingVisualizer) {
    this.routingVisualizer = routingVisualizer;

    this.tabButtons = document.querySelectorAll('.stage-tab-btn');
    this.panelTeam = document.getElementById('panel-team-map');
    this.panelFiles = document.getElementById('panel-files-browser');

    this.activeSubtab = 'team';
    this.bindEvents();
    this.applySubtab('team');
  }

  bindEvents() {
    this.tabButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const subtab = btn.getAttribute('data-subtab');
        if (subtab) this.applySubtab(subtab);
      });
    });
  }

  applySubtab(subtabName) {
    this.activeSubtab = subtabName;

    this.tabButtons.forEach((btn) => {
      if (btn.getAttribute('data-subtab') === subtabName) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    if (subtabName === 'team') {
      if (this.panelTeam) this.panelTeam.style.display = 'flex';
      if (this.panelFiles) this.panelFiles.style.display = 'none';
      setTimeout(() => {
        if (this.routingVisualizer) this.routingVisualizer.initCanvas();
      }, 50);
    } else if (subtabName === 'files') {
      if (this.panelTeam) this.panelTeam.style.display = 'none';
      if (this.panelFiles) this.panelFiles.style.display = 'flex';
      window.filesExplorerController?.loadFiles();
    }
  }
}

// ===================================================================
// 4. CODEBASE UPLOAD & REPO MANAGER
// ===================================================================
class CodeUploadController {
  constructor(diagramViewer, stageTabController, chatController) {
    this.diagramViewer = diagramViewer;
    this.stageTabController = stageTabController;
    this.chatController = chatController;

    this.modal = document.getElementById('modal-upload');
    this.btnOpen = document.getElementById('btn-open-upload');
    this.btnClose = document.getElementById('btn-close-upload-modal');
    this.dropzone = document.getElementById('dropzone');
    this.fileInput = document.getElementById('file-input');
    this.btnBrowse = document.getElementById('btn-browse-files');
    this.statusBox = document.getElementById('upload-status');
    this.statusText = document.getElementById('upload-status-text');
    this.resultBox = document.getElementById('upload-result-box');
    this.resultTitle = document.getElementById('result-title');
    this.resultDetails = document.getElementById('result-details');
    this.btnViewDiagramNow = document.getElementById('btn-view-diagram-now');
    this.btnAskQuestionNow = document.getElementById('btn-ask-question-now');

    this.activeRepoName = document.getElementById('active-repo-name');
    this.btnResetCodebase = document.getElementById('btn-reset-codebase');
    this.stageCodebaseLabel = document.getElementById('stage-codebase-label');
    this.filesBadgeCount = document.getElementById('files-badge-count');

    this.bindEvents();
    this.fetchInitialStatus();
  }

  bindEvents() {
    if (this.btnOpen) this.btnOpen.addEventListener('click', () => this.openModal());
    if (this.btnClose) this.btnClose.addEventListener('click', () => this.closeModal());

    if (this.modal) {
      this.modal.addEventListener('click', (e) => {
        if (e.target === this.modal) this.closeModal();
      });
    }

    if (this.btnBrowse && this.fileInput) {
      this.btnBrowse.addEventListener('click', (e) => {
        e.stopPropagation();
        this.fileInput.click();
      });
    }

    if (this.dropzone && this.fileInput) {
      this.dropzone.addEventListener('click', () => this.fileInput.click());

      this.dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        this.dropzone.classList.add('dragover');
      });

      this.dropzone.addEventListener('dragleave', () => {
        this.dropzone.classList.remove('dragover');
      });

      this.dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        this.dropzone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          this.handleFiles(e.dataTransfer.files);
        }
      });

      this.fileInput.addEventListener('change', () => {
        if (this.fileInput.files && this.fileInput.files.length > 0) {
          this.handleFiles(this.fileInput.files);
        }
      });
    }

    if (this.btnResetCodebase) {
      this.btnResetCodebase.addEventListener('click', (e) => {
        e.stopPropagation();
        this.resetCodebase();
      });
    }

    if (this.btnViewDiagramNow) {
      this.btnViewDiagramNow.addEventListener('click', () => {
        this.closeModal();
        window.topViewSwitcher?.switchView('diagram');
      });
    }

    if (this.btnAskQuestionNow) {
      this.btnAskQuestionNow.addEventListener('click', () => {
        this.closeModal();
        window.topViewSwitcher?.switchView('chat');
        const userInput = document.getElementById('user-input');
        if (userInput) userInput.focus();
      });
    }
  }

  openModal() {
    if (this.modal) {
      this.modal.style.display = 'flex';
      if (this.statusBox) this.statusBox.style.display = 'none';
      if (this.resultBox) this.resultBox.style.display = 'none';
    }
  }

  closeModal() {
    if (this.modal) this.modal.style.display = 'none';
  }

  async fetchInitialStatus() {
    try {
      const res = await fetch('/api/status');
      if (!res.ok) return;
      const data = await res.json();
      if (data.active_codebase) {
        this.updateCodebaseUI(data.active_codebase);
        if (data.active_codebase.files && window.diagramViewer) {
          window.diagramViewer.updateFileList(data.active_codebase.files);
        }
      }
    } catch (e) {
      console.warn('Initial codebase status check deferred:', e);
    }
  }

  updateCodebaseUI(info) {
    const name = info.name || 'Workspace';
    const count = info.files_count || 0;
    const isUploaded = info.is_uploaded || false;

    if (this.activeRepoName) this.activeRepoName.textContent = name;
    if (this.stageCodebaseLabel) this.stageCodebaseLabel.textContent = `${name} (${count} files)`;
    if (this.filesBadgeCount) this.filesBadgeCount.textContent = count;
    const archTag = document.getElementById('arch-codebase-tag');
    if (archTag) archTag.textContent = name;
    if (this.btnResetCodebase) {
      this.btnResetCodebase.style.display = isUploaded ? 'inline-flex' : 'none';
    }
  }

  async handleFiles(files) {
    if (!files || files.length === 0) return;

    if (this.statusBox) this.statusBox.style.display = 'flex';
    if (this.resultBox) this.resultBox.style.display = 'none';
    if (this.statusText) this.statusText.textContent = 'Uploading and analyzing codebase...';

    const firstFile = files[0];

    try {
      let data = null;

      // Multipart upload
      const formData = new FormData();
      if (files.length === 1 && firstFile.name.endsWith('.zip')) {
        formData.append('file', firstFile);
      } else {
        // Upload first .py or zip
        formData.append('file', firstFile);
      }

      try {
        const res = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        });
        if (res.ok) {
          data = await res.json();
        }
      } catch (uploadErr) {
        console.warn('Multipart upload fallback to base64 JSON:', uploadErr);
      }

      // JSON base64 fallback if multipart fails
      if (!data) {
        if (firstFile.name.endsWith('.zip')) {
          const base64 = await this.fileToBase64(firstFile);
          const res = await fetch('/api/upload-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              filename: firstFile.name,
              content_base64: base64
            })
          });
          if (!res.ok) throw new Error(`Upload failed HTTP ${res.status}`);
          data = await res.json();
        } else {
          // Read .py files text
          const fileDict = {};
          for (const f of files) {
            if (f.name.endsWith('.py')) {
              fileDict[f.name] = await f.text();
            }
          }
          const res = await fetch('/api/upload-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              filename: 'Uploaded Python Files',
              files: fileDict
            })
          });
          if (!res.ok) throw new Error(`Upload failed HTTP ${res.status}`);
          data = await res.json();
        }
      }

      const info = data.info || {};
      if (this.statusBox) this.statusBox.style.display = 'none';
      if (this.resultBox) this.resultBox.style.display = 'block';

      if (this.resultTitle) {
        this.resultTitle.textContent = `Codebase '${info.name}' Ingested!`;
      }
      if (this.resultDetails) {
        this.resultDetails.textContent = `Analyzed ${info.files_count} Python files (${info.total_loc} lines of code). Ready for Q&A and architecture diagrams.`;
      }

      this.updateCodebaseUI(info);
      if (info.files && window.diagramViewer) {
        window.diagramViewer.updateFileList(info.files);
      }

      // Refresh diagram
      if (data.mermaid) {
        this.diagramViewer.renderMermaidCode(data.mermaid);
      } else {
        this.diagramViewer.fetchDiagram();
      }

      // Update prompt pills with dynamic questions about the uploaded files
      this.updateDynamicPrompts(info);

      // Post welcome message in chat stream
      if (this.chatController) {
        this.chatController.renderAgentMessage(
          'coordinator',
          `### 🚀 Codebase \`${info.name}\` Uploaded Successfully!\n\n` +
          `I have ingested **${info.files_count} Python source files** (${info.total_loc} total lines of code).\n\n` +
          `• **Architecture Flowchart:** The dependency diagram has been generated and is ready in the **Architecture Diagram** tab.\n` +
          `• **Multi-Agent RAG:** You can now ask questions about functions, imports, logic, or request architecture diagrams!`,
          ['codebase_manager.ingest', 'generate_architecture_diagram'],
          true
        );
      }

    } catch (err) {
      console.error('Upload failed:', err);
      if (this.statusBox) {
        this.statusBox.style.display = 'flex';
        this.statusText.textContent = `Upload failed: ${err.message}`;
      }
    }
  }

  fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = (error) => reject(error);
    });
  }

  updateDynamicPrompts(info) {
    const container = document.getElementById('prompts-container');
    if (!container || !info.files || info.files.length === 0) return;

    const firstFile = info.files[0].name;
    const secondFile = info.files.length > 1 ? info.files[1].name : firstFile;

    container.innerHTML = `
      <button class="prompt-pill" data-prompt="Generate an architecture diagram of this project.">
        <i class="fa-solid fa-diagram-project"></i> Draw Architecture Diagram
      </button>
      <button class="prompt-pill" data-prompt="Explain the structure and main logic of ${firstFile}">
        <i class="fa-solid fa-book-open"></i> Explain ${firstFile}
      </button>
      <button class="prompt-pill" data-prompt="Which files import modules in this project?">
        <i class="fa-solid fa-sitemap"></i> Project Imports
      </button>
      <button class="prompt-pill" data-prompt="Show code metrics and lines of code for this project.">
        <i class="fa-solid fa-chart-simple"></i> Code Metrics
      </button>
    `;

    // Re-bind prompt click events
    container.querySelectorAll('.prompt-pill').forEach((pill) => {
      pill.addEventListener('click', () => {
        const prompt = pill.getAttribute('data-prompt');
        const input = document.getElementById('user-input');
        if (prompt && input && this.chatController) {
          input.value = prompt;
          this.chatController.submitMessage();
        }
      });
    });
  }

  async resetCodebase() {
    try {
      const res = await fetch('/api/reset-codebase', { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const info = data.info || {};

      this.updateCodebaseUI(info);
      if (info.files && window.diagramViewer) {
        window.diagramViewer.updateFileList(info.files);
      }
      this.diagramViewer.fetchDiagram();

      if (this.chatController) {
        this.chatController.renderAgentMessage(
          'coordinator',
          `🔄 Switched back to **Default Workspace** (${info.files_count} files).`,
          ['codebase_manager.reset']
        );
      }
    } catch (e) {
      console.error('Reset codebase failed:', e);
    }
  }
}

// ===================================================================
// 5. ACTIVE CODEBASE FILES EXPLORER
// ===================================================================
class FilesExplorerController {
  constructor(chatController) {
    this.chatController = chatController;
    this.container = document.getElementById('files-list-container');
    this.summaryText = document.getElementById('files-summary-text');
  }

  async loadFiles() {
    if (!this.container) return;
    this.container.innerHTML = `
      <div class="files-loading">
        <i class="fa-solid fa-circle-notch fa-spin"></i>
        <span>Scanning active codebase files...</span>
      </div>
    `;

    try {
      const res = await fetch('/api/codebase');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const files = data.files || [];

      if (window.diagramViewer) {
        window.diagramViewer.updateFileList(files);
      }

      if (this.summaryText) {
        this.summaryText.textContent = `${files.length} Python files • ${data.total_loc} LOC`;
      }

      if (files.length === 0) {
        this.container.innerHTML = `
          <div style="text-align:center; padding: 30px; color: var(--text-muted);">
            <i class="fa-solid fa-folder-open" style="font-size:2rem; margin-bottom:8px;"></i>
            <p>No Python files found in active codebase.</p>
          </div>
        `;
        return;
      }

      let html = '';
      files.forEach((f) => {
        html += `
          <div class="file-row">
            <div class="file-info">
              <i class="fa-brands fa-python file-icon"></i>
              <div>
                <div class="file-name">${f.path || f.name}</div>
                <div style="font-size:0.68rem; color:var(--text-muted);">${f.loc} lines</div>
              </div>
            </div>
            <div class="file-badges">
              ${f.classes ? `<span class="file-badge">${f.classes} classes</span>` : ''}
              ${f.functions ? `<span class="file-badge">${f.functions} funcs</span>` : ''}
              <button class="btn-ghost-sm btn-diagram-file" data-file="${f.name || f.path}" title="View dedicated architecture diagram for ${f.name}">
                <i class="fa-solid fa-diagram-project"></i> Diagram
              </button>
              <button class="btn-ghost-sm btn-inspect-file" data-file="${f.name}" title="Ask agent to explain this file">
                <i class="fa-solid fa-bolt"></i> Explain
              </button>
            </div>
          </div>
        `;
      });

      this.container.innerHTML = html;

      this.container.querySelectorAll('.btn-diagram-file').forEach((btn) => {
        btn.addEventListener('click', () => {
          const fname = btn.getAttribute('data-file');
          if (fname && window.diagramViewer) {
            window.diagramViewer.fetchDiagram(fname);
            window.topViewSwitcher?.switchView('diagram');
          }
        });
      });

      this.container.querySelectorAll('.btn-inspect-file').forEach((btn) => {
        btn.addEventListener('click', () => {
          const fname = btn.getAttribute('data-file');
          const input = document.getElementById('user-input');
          if (fname && input && this.chatController) {
            input.value = `Explain the logic, functions, and architecture of ${fname}`;
            this.chatController.submitMessage();
          }
        });
      });

    } catch (e) {
      this.container.innerHTML = `<div style="color:#F87171; padding:20px;">Failed to scan files: ${e.message}</div>`;
    }
  }
}

// ===================================================================
// 6. CHAT CONTROLLER (Agent Dialogue, Telemetry, and Markdown)
// ===================================================================
class ChatController {
  constructor(routingVisualizer, diagramViewer) {
    this.routingVisualizer = routingVisualizer;
    this.diagramViewer = diagramViewer;

    this.stream = document.getElementById('chat-stream');
    this.form = document.getElementById('chat-form');
    this.input = document.getElementById('user-input');
    this.sendBtn = document.getElementById('btn-send');
    this.clearBtn = document.getElementById('btn-clear-chat');
    this.activeIndicator = document.getElementById('active-worker-indicator');
    this.promptPills = document.querySelectorAll('.prompt-pill');

    this.agentMeta = {
      coordinator: {
        name: 'Boss Coordinator',
        type: 'Router (AI)',
        icon: 'fa-solid fa-crown',
        avatarClass: 'coordinator-avatar'
      },
      code_searcher: {
        name: 'Code Searcher',
        type: 'RAG Agent (AI)',
        icon: 'fa-solid fa-magnifying-glass',
        avatarClass: 'searcher-avatar'
      },
      architecture_mapper: {
        name: 'Architecture Mapper',
        type: '0 AI • AST Engine',
        icon: 'fa-solid fa-sitemap',
        avatarClass: 'mapper-avatar'
      },
      onboarding_guide: {
        name: 'Onboarding Guide',
        type: 'Orientation Agent (AI)',
        icon: 'fa-solid fa-compass',
        avatarClass: 'guide-avatar'
      },
      code_explainer: {
        name: 'Code Explainer',
        type: 'AI Code Analyst',
        icon: 'fa-solid fa-book-open',
        avatarClass: 'explainer-avatar'
      }
    };

    this.bindEvents();
  }

  bindEvents() {
    if (this.form) {
      this.form.addEventListener('submit', (e) => {
        e.preventDefault();
        this.submitMessage();
      });
    }

    if (this.input) {
      this.input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.submitMessage();
        }
      });

      this.input.addEventListener('input', () => {
        this.input.style.height = 'auto';
        this.input.style.height = Math.min(this.input.scrollHeight, 120) + 'px';
      });
    }

    if (this.clearBtn) {
      this.clearBtn.addEventListener('click', () => {
        if (!this.stream) return;
        const welcome = document.getElementById('welcome-message');
        this.stream.innerHTML = '';
        if (welcome) this.stream.appendChild(welcome);
      });
    }

    this.promptPills.forEach((pill) => {
      pill.addEventListener('click', () => {
        const prompt = pill.getAttribute('data-prompt');
        if (prompt && this.input) {
          this.input.value = prompt;
          this.submitMessage();
        }
      });
    });
  }

  async submitMessage() {
    if (!this.input) return;
    const message = this.input.value.trim();
    if (!message) return;

    this.renderUserMessage(message);
    this.input.value = '';
    this.input.style.height = 'auto';

    this.setBusy(true);

    if (this.routingVisualizer) {
      this.routingVisualizer.clearActive();
    }

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      });

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data = await res.json();
      const author = data.worker || data.author || 'coordinator';
      const responseText = data.message || data.response || 'No response returned from agent.';
      const toolCalls = data.tools_used || data.tool_calls || [];

      if (this.routingVisualizer && author !== 'coordinator') {
        this.routingVisualizer.triggerDelegation(author);
      }

      const isDiagramRequest = 
        author === 'architecture_mapper' ||
        Boolean(data.mermaid) ||
        message.toLowerCase().includes('diagram') ||
        message.toLowerCase().includes('architecture') ||
        message.toLowerCase().includes('flowchart');

      const targetFile = data.target_file || null;

      // Pre-render diagram in viewer so it's ready when user opens Architecture view
      if (data.mermaid) {
        if (this.diagramViewer) {
          if (targetFile && this.diagramViewer.fileSelect) {
            this.diagramViewer.fileSelect.value = targetFile;
            this.diagramViewer.currentFile = targetFile;
          }
          this.diagramViewer.renderMermaidCode(data.mermaid);
        }
      } else if (isDiagramRequest) {
        if (this.diagramViewer) {
          this.diagramViewer.fetchDiagram(targetFile);
        }
      }

      this.renderAgentMessage(author, responseText, toolCalls, isDiagramRequest, targetFile);
    } catch (err) {
      console.error('Chat error:', err);
      this.renderAgentMessage(
        'coordinator',
        `⚠️ **Error communicating with agent engine:** ${err.message}. Please verify the backend server is running.`,
        [],
        false
      );
    } finally {
      this.setBusy(false);
      this.scrollToBottom();
    }
  }

  setBusy(isBusy) {
    if (this.sendBtn) this.sendBtn.disabled = isBusy;
    if (this.activeIndicator) {
      this.activeIndicator.style.display = isBusy ? 'inline-flex' : 'none';
    }
  }

  renderUserMessage(text) {
    if (!this.stream) return;
    const msgCard = document.createElement('div');
    msgCard.className = 'message-card user-message';
    msgCard.innerHTML = `
      <div class="message-header">
        <div class="avatar user-avatar"><i class="fa-solid fa-user"></i></div>
        <div class="meta">
          <span class="agent-title">You</span>
        </div>
        <span class="message-time">${this.formatCurrentTime()}</span>
      </div>
      <div class="message-body">
        <p>${this.escapeHtml(text)}</p>
      </div>
    `;
    this.stream.appendChild(msgCard);
    this.scrollToBottom();
  }

  renderAgentMessage(author, content, toolCalls, hasDiagram = false, targetFile = null) {
    if (!this.stream) return;
    const meta = this.agentMeta[author] || this.agentMeta['coordinator'];

    const msgCard = document.createElement('div');
    msgCard.className = 'message-card agent-message';

    let diagramBannerHtml = '';
    if (hasDiagram || author === 'architecture_mapper') {
      const bannerTitle = targetFile
        ? `Dedicated Flowchart: ${this.escapeHtml(targetFile)}`
        : 'Architecture Flowchart Ready';
      const bannerDesc = targetFile
        ? `AST dependency analysis for ${this.escapeHtml(targetFile)} (call graph, upstream callers & imports)`
        : 'Interactive dependency flowchart generated from Python AST';

      diagramBannerHtml = `
        <div class="chat-diagram-banner">
          <div class="cdb-left">
            <i class="fa-solid fa-diagram-project"></i>
            <div class="cdb-text">
              <strong>${bannerTitle}</strong>
              <span>${bannerDesc}</span>
            </div>
          </div>
          <button class="btn-primary-sm btn-open-arch-view" data-file="${this.escapeHtml(targetFile || '')}" type="button">
            <i class="fa-solid fa-arrow-up-right-from-square"></i> Open Diagram View
          </button>
        </div>
      `;
    }

    let telemetryHtml = '';
    if (toolCalls && toolCalls.length > 0) {
      const toolPills = toolCalls
        .map((tc) => {
          if (typeof tc === 'string') {
            return `<div><span style="color: #38BDF8;">⚡ tool:</span> ${this.escapeHtml(tc)}</div>`;
          }
          const name = tc.tool || 'custom_tool';
          const args = tc.args ? JSON.stringify(tc.args) : '';
          return `<div><span style="color: #38BDF8;">⚡ ${name}</span> ${this.escapeHtml(args)}</div>`;
        })
        .join('');

      telemetryHtml = `
        <details class="tool-telemetry">
          <summary>
            <i class="fa-solid fa-screwdriver-wrench"></i>
            <span>Tool Executions (${toolCalls.length})</span>
          </summary>
          <div class="tool-telemetry-content">
            ${toolPills}
          </div>
        </details>
      `;
    }

    msgCard.innerHTML = `
      <div class="message-header">
        <div class="avatar ${meta.avatarClass}"><i class="${meta.icon}"></i></div>
        <div class="meta">
          <span class="agent-title">${meta.name}</span>
          <span class="agent-type-pill">${meta.type}</span>
        </div>
        <span class="message-time">${this.formatCurrentTime()}</span>
      </div>
      <div class="message-body">
        ${this.parseMarkdown(content)}
        ${diagramBannerHtml}
      </div>
      ${telemetryHtml}
    `;

    msgCard.querySelectorAll('.btn-open-arch-view').forEach((btn) => {
      btn.addEventListener('click', () => {
        const file = btn.getAttribute('data-file');
        if (file && window.diagramViewer) {
          window.diagramViewer.fetchDiagram(file);
        }
        window.topViewSwitcher?.switchView('diagram');
      });
    });

    this.stream.appendChild(msgCard);
    this.scrollToBottom();
  }

  scrollToBottom() {
    if (this.stream) {
      this.stream.scrollTop = this.stream.scrollHeight;
    }
  }

  formatCurrentTime() {
    const d = new Date();
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  parseMarkdown(text) {
    if (!text) return '';

    const codeBlocks = [];
    let formatted = text.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`;
      codeBlocks.push({ lang, code });
      return placeholder;
    });

    const inlineCodes = [];
    formatted = formatted.replace(/`([^`]+)`/g, (match, code) => {
      const placeholder = `__INLINE_CODE_${inlineCodes.length}__`;
      inlineCodes.push(code);
      return placeholder;
    });

    formatted = this.escapeHtml(formatted);

    formatted = formatted.replace(/^### (.*$)/gim, '<h4>$1</h4>');
    formatted = formatted.replace(/^## (.*$)/gim, '<h3>$1</h3>');
    formatted = formatted.replace(/^# (.*$)/gim, '<h3>$1</h3>');

    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

    formatted = formatted.replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    formatted = formatted.replace(/\n\n+/g, '</p><p>');
    formatted = `<p>${formatted}</p>`;
    formatted = formatted.replace(/<p>\s*<\/p>/g, '');

    inlineCodes.forEach((code, i) => {
      formatted = formatted.replace(
        `__INLINE_CODE_${i}__`,
        `<code>${this.escapeHtml(code)}</code>`
      );
    });

    codeBlocks.forEach((block, i) => {
      const escapedCode = this.escapeHtml(block.code.trim());
      const langLabel = block.lang ? `<div style="font-size:0.7rem; color:var(--text-muted); margin-bottom:4px; text-transform:uppercase;">${block.lang}</div>` : '';
      formatted = formatted.replace(
        `__CODE_BLOCK_${i}__`,
        `<pre>${langLabel}<code>${escapedCode}</code></pre>`
      );
    });

    return formatted;
  }
}

// ===================================================================
// 7. SYSTEM STATUS & HEALTH DIAGNOSTIC MODAL
// ===================================================================
class HealthModalController {
  constructor() {
    this.modal = document.getElementById('modal-health');
    this.btnOpen = document.getElementById('btn-health-check');
    this.btnClose = document.getElementById('btn-close-modal');
    this.codeOutput = document.getElementById('health-report-code');

    this.bindEvents();
    this.checkLiveStatus();
  }

  bindEvents() {
    if (this.btnOpen) {
      this.btnOpen.addEventListener('click', () => this.openModal());
    }
    if (this.btnClose) {
      this.btnClose.addEventListener('click', () => this.closeModal());
    }
    if (this.modal) {
      this.modal.addEventListener('click', (e) => {
        if (e.target === this.modal) this.closeModal();
      });
    }
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.modal && this.modal.style.display !== 'none') {
        this.closeModal();
      }
    });
  }

  async openModal() {
    if (!this.modal) return;
    this.modal.style.display = 'flex';
    if (this.codeOutput) {
      this.codeOutput.textContent = 'Running system health check diagnostics...';
    }

    try {
      const res = await fetch('/api/health');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (this.codeOutput) {
        this.codeOutput.textContent = data.report || data.health || JSON.stringify(data, null, 2);
      }
    } catch (err) {
      if (this.codeOutput) {
        this.codeOutput.textContent = `Diagnostic error: ${err.message}`;
      }
    }
  }

  closeModal() {
    if (this.modal) {
      this.modal.style.display = 'none';
    }
  }

  async checkLiveStatus() {
    try {
      const res = await fetch('/api/status');
      if (!res.ok) return;
      const data = await res.json();

      const pineconePill = document.getElementById('pinecone-pill');
      if (pineconePill && (data.vector_db || data.pinecone_connected)) {
        pineconePill.style.borderColor = 'rgba(16, 185, 129, 0.5)';
        pineconePill.style.color = '#34D399';
      }

      const nvidiaPill = document.getElementById('nvidia-pill');
      if (nvidiaPill && (data.model || data.nvidia_configured)) {
        nvidiaPill.style.borderColor = 'rgba(16, 185, 129, 0.5)';
        nvidiaPill.style.color = '#34D399';
      }
    } catch (err) {
      console.warn('Backend status check deferred:', err.message);
    }
  }
}

// ===================================================================
// 8. APPLICATION BOOTSTRAPPER
// ===================================================================
document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize Canvas Routing Visualizer
  const routingVisualizer = new RoutingVisualizer('routing-canvas', 'routing-container');

  // 2. Initialize Mermaid Diagram Viewer
  const diagramViewer = new DiagramViewer();
  window.diagramViewer = diagramViewer;

  // 3. Initialize Top View Switcher (Studio Chat vs Full-Screen Architecture Diagram)
  const topViewSwitcher = new TopViewSwitcher(routingVisualizer, diagramViewer);
  window.topViewSwitcher = topViewSwitcher;

  // 4. Initialize Stage Subtab Controller (Multi-Agent Team vs Codebase Files)
  const stageTabController = new StageTabController(routingVisualizer);
  window.stageTabController = stageTabController;

  // 5. Initialize Multi-Agent Dialogue Chat Console
  const chatController = new ChatController(routingVisualizer, diagramViewer);

  // 6. Initialize Files Explorer
  const filesExplorerController = new FilesExplorerController(chatController);
  window.filesExplorerController = filesExplorerController;

  // 7. Initialize Codebase Upload Controller
  new CodeUploadController(diagramViewer, stageTabController, chatController);

  // 8. Initialize Health Check Modal
  new HealthModalController();

  console.log('⚡ Modern AI Agent Studio with Codebase Ingestion & Dedicated Diagram View initialized.');
});
