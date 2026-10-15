/**
 * Multi-Agent Code Helper Studio - Client Application
 * Handles:
 * - Dynamic Canvas Routing Visualizer with glowing Bézier curves & pulse particles
 * - Live Architecture Graph with Mermaid.js, SVG pan/zoom controls
 * - Interactive Dialogue Console with agent attribution & tool telemetry
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

    // Highlight target worker card
    const target = this.workerNodes[agentName];
    if (target && target.el) {
      target.el.classList.add('active-worker');
    }

    // Spawn a burst of fast particles toward the active worker
    for (let i = 0; i < 20; i++) {
      this.particles.push({
        agent: agentName,
        t: Math.random() * 0.2, // start near boss
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

      // Draw Bézier curves from Boss Coordinator to each Worker
      for (const [key, target] of Object.entries(workers)) {
        const isActive = this.activeAgent === key;
        const dy = target.y - boss.y;

        const cp1x = boss.x;
        const cp1y = boss.y + dy * 0.45;
        const cp2x = target.x;
        const cp2y = target.y - dy * 0.45;

        // Background subtle pathway
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

        // Idle slow particle drifting down
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

      // Update and draw traveling particles
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

        // Cubic Bézier formula
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

    this.initMermaid();
    this.bindEvents();
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
      this.btnRefresh.addEventListener('click', () => this.fetchDiagram());
    }

    // Viewport mouse drag to pan
    if (this.viewport) {
      this.viewport.addEventListener('mousedown', (e) => {
        if (e.target.closest('button')) return;
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

      // Mouse wheel zoom
      this.viewport.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY < 0 ? 0.1 : -0.1;
        this.zoom(delta);
      }, { passive: false });
    }
  }

  zoom(delta) {
    this.zoomLevel = Math.min(Math.max(0.4, this.zoomLevel + delta), 2.5);
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

  async fetchDiagram() {
    if (!this.container) return;
    this.container.innerHTML = `
      <div class="diagram-loading">
        <i class="fa-solid fa-circle-notch fa-spin"></i>
        <span>Generating live dependency flowchart...</span>
      </div>
    `;

    try {
      const res = await fetch('/api/diagram');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const rawDiagram = data.diagram || '';

      // Clean diagram fences
      let diagramCode = rawDiagram.trim();
      if (diagramCode.startsWith('```mermaid')) {
        diagramCode = diagramCode.replace(/^```mermaid\s*/, '').replace(/```$/, '').trim();
      } else if (diagramCode.startsWith('```')) {
        diagramCode = diagramCode.replace(/^```\s*/, '').replace(/```$/, '').trim();
      }

      if (!diagramCode) {
        diagramCode = 'graph TD\n  A[App] --> B[RAG Pipeline]';
      }

      const id = 'mermaid-svg-' + Date.now();
      const { svg } = await window.mermaid.render(id, diagramCode);
      this.container.innerHTML = svg;
      this.resetTransform();
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
}

// ===================================================================
// 3. CHAT CONTROLLER (Agent Dialogue, Telemetry, and Markdown)
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
        type: 'MCP Filesystem Agent',
        icon: 'fa-solid fa-book-open',
        avatarClass: 'explainer-avatar'
      }
    };

    this.bindEvents();
  }

  bindEvents() {
    // Form submit
    if (this.form) {
      this.form.addEventListener('submit', (e) => {
        e.preventDefault();
        this.submitMessage();
      });
    }

    // Auto-expand textarea & submit on Enter (Shift+Enter for newline)
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

    // Clear chat
    if (this.clearBtn) {
      this.clearBtn.addEventListener('click', () => {
        if (!this.stream) return;
        const welcome = document.getElementById('welcome-message');
        this.stream.innerHTML = '';
        if (welcome) this.stream.appendChild(welcome);
      });
    }

    // Quick prompt pills
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

    // Render user message card
    this.renderUserMessage(message);
    this.input.value = '';
    this.input.style.height = 'auto';

    // Set UI busy state
    this.setBusy(true);

    // Initial pulse from Boss Coordinator
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
      const author = data.author || 'coordinator';
      const responseText = data.response || 'No response returned from agent.';
      const toolCalls = data.tool_calls || [];

      // Highlight the worker who handled this
      if (this.routingVisualizer && author !== 'coordinator') {
        this.routingVisualizer.triggerDelegation(author);
      }

      // Render agent response card
      this.renderAgentMessage(author, responseText, toolCalls);

      // If user requested architecture diagram or mapper answered, refresh live diagram
      if (
        author === 'architecture_mapper' ||
        message.toLowerCase().includes('diagram') ||
        message.toLowerCase().includes('architecture')
      ) {
        if (this.diagramViewer) {
          this.diagramViewer.fetchDiagram();
        }
      }
    } catch (err) {
      console.error('Chat error:', err);
      this.renderAgentMessage(
        'coordinator',
        `⚠️ **Error communicating with agent engine:** ${err.message}. Please verify the backend server is running.`,
        []
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

  renderAgentMessage(author, content, toolCalls) {
    if (!this.stream) return;
    const meta = this.agentMeta[author] || this.agentMeta['coordinator'];

    const msgCard = document.createElement('div');
    msgCard.className = 'message-card agent-message';

    let telemetryHtml = '';
    if (toolCalls && toolCalls.length > 0) {
      const toolPills = toolCalls
        .map((tc) => {
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
      </div>
      ${telemetryHtml}
    `;

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

    // First preserve code blocks
    const codeBlocks = [];
    let formatted = text.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`;
      codeBlocks.push({ lang, code });
      return placeholder;
    });

    // Inline code `code`
    const inlineCodes = [];
    formatted = formatted.replace(/`([^`]+)`/g, (match, code) => {
      const placeholder = `__INLINE_CODE_${inlineCodes.length}__`;
      inlineCodes.push(code);
      return placeholder;
    });

    // Escape remaining HTML to prevent XSS
    formatted = this.escapeHtml(formatted);

    // Headers (###, ##, #)
    formatted = formatted.replace(/^### (.*$)/gim, '<h4>$1</h4>');
    formatted = formatted.replace(/^## (.*$)/gim, '<h3>$1</h3>');
    formatted = formatted.replace(/^# (.*$)/gim, '<h3>$1</h3>');

    // Bold **text**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic *text*
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Bullet list items
    formatted = formatted.replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');
    formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Paragraph breaks
    formatted = formatted.replace(/\n\n+/g, '</p><p>');
    formatted = `<p>${formatted}</p>`;
    formatted = formatted.replace(/<p>\s*<\/p>/g, '');

    // Restore inline code
    inlineCodes.forEach((code, i) => {
      formatted = formatted.replace(
        `__INLINE_CODE_${i}__`,
        `<code>${this.escapeHtml(code)}</code>`
      );
    });

    // Restore fenced code blocks
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
// 4. SYSTEM STATUS & HEALTH DIAGNOSTIC MODAL
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
        this.codeOutput.textContent = data.health || JSON.stringify(data, null, 2);
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
      if (pineconePill && data.pinecone_connected) {
        pineconePill.style.borderColor = 'rgba(16, 185, 129, 0.5)';
        pineconePill.style.color = '#34D399';
      }

      const nvidiaPill = document.getElementById('nvidia-pill');
      if (nvidiaPill && data.nvidia_configured) {
        nvidiaPill.style.borderColor = 'rgba(16, 185, 129, 0.5)';
        nvidiaPill.style.color = '#34D399';
      }
    } catch (err) {
      console.warn('Backend status check deferred:', err.message);
    }
  }
}

// ===================================================================
// 5. APPLICATION BOOTSTRAPPER
// ===================================================================
document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize canvas routing map
  const routingVisualizer = new RoutingVisualizer('routing-canvas', 'routing-container');

  // 2. Initialize Mermaid architecture diagram viewer
  const diagramViewer = new DiagramViewer();

  // 3. Initialize dialogue chat console
  new ChatController(routingVisualizer, diagramViewer);

  // 4. Initialize health modal and status polling
  new HealthModalController();

  console.log('⚡ Multi-Agent Code Helper Studio initialized successfully.');
});
