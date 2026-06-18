// script.js

document.addEventListener('DOMContentLoaded', () => {
  // ------ DOM elements ------
  const sidebar = document.getElementById('sidebar');
  const hamburger = document.getElementById('hamburgerBtn');
  const themeToggle = document.getElementById('themeToggle');
  const body = document.body;
  const newChatBtn = document.getElementById('newChatBtn');
  const chatList = document.getElementById('chatList');
  const sendButton = document.getElementById('sendButton');
  const messageInput = document.getElementById('messageInput');
  const messagesContainer = document.getElementById('messagesContainer');
  const fileInput = document.getElementById('fileInput');
  const uploadButton = document.getElementById('uploadButton');
  const dragOverlay = document.getElementById('dragOverlay');
  const loadingIndicator = document.getElementById('loadingIndicator');

  // ------ state ------
  let chatCounter = 5; // for demo new chat names
  let currentFileName = ''; // Track the currently uploaded file for API calls

  // ------ theme toggle (sun logic) ------
  const setTheme = (isDark) => {
    if (isDark) {
      body.classList.add('dark');
      themeToggle.textContent = '☀️';   // sun icon (white in dark mode)
      themeToggle.style.color = 'var(--sun-color)'; // white via css variable
    } else {
      body.classList.remove('dark');
      themeToggle.textContent = '☀️';
      themeToggle.style.color = 'var(--sun-color)'; // yellow
    }
  };

  // initial: light mode (sun yellow already via css)
  themeToggle.addEventListener('click', () => {
    const isDark = !body.classList.contains('dark');
    setTheme(isDark);
  });

  // ------ hamburger / sidebar collapse ------
  hamburger.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });

  // close sidebar if click outside on mobile (simple)
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768) {
      if (!sidebar.contains(e.target) && !hamburger.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    }
  });

  // ------ new chat button (adds a dummy chat to list) ------
  newChatBtn.addEventListener('click', () => {
    chatCounter++;
    const newChatDiv = document.createElement('div');
    newChatDiv.className = 'chat-item';
    newChatDiv.dataset.chatId = `chat-${chatCounter}`;
    newChatDiv.innerHTML = `
      <span class="chat-name">New conversation ${chatCounter}</span>
      <div class="chat-actions">
        <button class="rename-chat" title="Rename chat">✏️</button>
        <button class="delete-chat" title="Delete chat">🗑️</button>
      </div>
    `;
    chatList.appendChild(newChatDiv);
    attachChatItemListeners(newChatDiv); // enable rename/delete
    // optional: auto close sidebar on mobile after new chat
    if (window.innerWidth <= 768) sidebar.classList.remove('open');
  });

  // ------ rename & delete functionality for chat items (delegation + per-item) ------
  function attachChatItemListeners(chatItem) {
    const renameBtn = chatItem.querySelector('.rename-chat');
    const deleteBtn = chatItem.querySelector('.delete-chat');
    const nameSpan = chatItem.querySelector('.chat-name');

    renameBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const newName = prompt('Rename chat:', nameSpan.textContent);
      if (newName && newName.trim()) nameSpan.textContent = newName.trim();
    });

    deleteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (confirm('Delete this chat?')) chatItem.remove();
    });
  }

  // attach to existing static chat items
  document.querySelectorAll('.chat-item').forEach(item => attachChatItemListeners(item));

  // also handle dynamically via event delegation for any future?
  // but we already attach on creation.

  // ------ send message (dumb echo, but adds user message and mock AI with loading) ------
  function addUserMessage(text) {
    if (!text.trim()) return;
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message user-message';
    msgDiv.innerHTML = `<div class="bubble">${escapeHTML(text)}</div>`;
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  async function handleFileUpload(file) {
    addUserMessage(`📎 Uploading: ${file.name}...`);
    loadingIndicator.classList.add('visible');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        let errorMsg = 'Upload failed';
        try {
          const errorData = await response.json();
          errorMsg = errorData.detail || errorMsg;
        } catch (e) { }
        throw new Error(errorMsg);
      }

      const data = await response.json();
      currentFileName = data.filename;

      const aiDiv = document.createElement('div');
      aiDiv.className = 'message ai-message';
      aiDiv.innerHTML = `<div class="bubble">File <strong>${currentFileName}</strong> uploaded successfully. You can now ask questions about it!</div>`;
      messagesContainer.appendChild(aiDiv);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } catch (error) {
      console.error('Upload Error:', error);
      const aiDiv = document.createElement('div');
      aiDiv.className = 'message ai-message';
      aiDiv.innerHTML = `<div class="bubble" style="color: var(--error-color, #ff4c4c);">Error uploading file: ${error.message}</div>`;
      messagesContainer.appendChild(aiDiv);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } finally {
      loadingIndicator.classList.remove('visible');
    }
  }

  function escapeHTML(str) {
    return str.replace(/[&<>"]/g, function (m) {
      if (m === '&') return '&amp;';
      if (m === '<') return '&lt;';
      if (m === '>') return '&gt;';
      if (m === '"') return '&quot;';
      return m;
    });
  }

  sendButton.addEventListener('click', async () => {
    const text = messageInput.value.trim();
    if (text === '') return;
    addUserMessage(text);
    messageInput.value = '';

    if (!currentFileName) {
      const aiDiv = document.createElement('div');
      aiDiv.className = 'message ai-message';
      aiDiv.innerHTML = `<div class="bubble">Please upload a file first before asking questions.</div>`;
      messagesContainer.appendChild(aiDiv);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
      return;
    }

    // show loading
    loadingIndicator.classList.add('visible');

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_message: text,
          file_name: currentFileName
        })
      });

      if (!response.ok) {
        let errorMsg = 'Query failed';
        try {
          const errorData = await response.json();
          errorMsg = errorData.detail || errorMsg;
        } catch (e) { }
        throw new Error(errorMsg);
      }

      const data = await response.json();

      const formattedAnswer = data.answer.replace(/\\n/g, '<br>').replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
      let answerHtml = `<div class="bubble">${formattedAnswer}</div>`;

      const aiDiv = document.createElement('div');
      aiDiv.className = 'message ai-message';
      aiDiv.innerHTML = answerHtml;

      // If there is a valid chart configuration
      const isScatter = data.chart_type === 'scatter' && data.scatter_data && data.scatter_data.length > 0;
      const isRegular = data.chart_type && data.chart_type !== 'none' && data.chart_type !== 'scatter'
        && data.labels && data.values && data.values.length > 0;

      if (isScatter || isRegular) {
        const chartId = 'chart-' + Date.now();
        const isDark = document.body.classList.contains('dark');
        const textColor = isDark ? '#ECEFF4' : '#2E3440';
        const gridColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)';

        const chartContainer = document.createElement('div');
        chartContainer.className = 'chart-container';
        chartContainer.style.marginTop = '8px';
        chartContainer.style.height = '320px';
        chartContainer.innerHTML = `<canvas id="${chartId}"></canvas>`;
        aiDiv.appendChild(chartContainer);
        messagesContainer.appendChild(aiDiv);

        setTimeout(() => {
          const ctx = document.getElementById(chartId).getContext('2d');

          let chartConfig;

          if (isScatter) {
            // ---- Scatter Plot ----
            chartConfig = {
              type: 'scatter',
              data: {
                datasets: [{
                  label: data.chart_title || 'Data Points',
                  data: data.scatter_data,
                  backgroundColor: 'rgba(99,179,237,0.7)',
                  borderColor: 'rgba(99,179,237,1)',
                  pointRadius: 6,
                  pointHoverRadius: 9,
                  pointBorderWidth: 1.5,
                }]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 700, easing: 'easeOutQuart' },
                plugins: {
                  legend: {
                    display: true, position: 'top',
                    labels: { color: textColor, font: { size: 12, family: 'Inter, sans-serif' }, usePointStyle: true }
                  },
                  title: {
                    display: true,
                    text: data.chart_title || text.slice(0, 60),
                    color: textColor,
                    font: { size: 13, weight: '600', family: 'Inter, sans-serif' },
                    padding: { bottom: 12 }
                  },
                  tooltip: {
                    backgroundColor: isDark ? '#1e1e2a' : '#fff',
                    titleColor: textColor, bodyColor: textColor,
                    borderColor: isDark ? '#2c2c3a' : '#e5e5e9',
                    borderWidth: 1, padding: 10,
                    callbacks: { label: c => ` (${c.parsed.x}, ${c.parsed.y})` }
                  }
                },
                scales: {
                  x: {
                    type: 'linear', position: 'bottom',
                    title: { display: true, text: data.x_label || 'X', color: textColor, font: { size: 11, family: 'Inter, sans-serif' } },
                    ticks: { color: textColor, font: { size: 11, family: 'Inter, sans-serif' } },
                    grid: { color: gridColor }, border: { color: gridColor }
                  },
                  y: {
                    title: { display: true, text: data.y_label || 'Y', color: textColor, font: { size: 11, family: 'Inter, sans-serif' } },
                    ticks: { color: textColor, font: { size: 11, family: 'Inter, sans-serif' } },
                    grid: { color: gridColor }, border: { color: gridColor }
                  }
                }
              }
            };

          } else {
            // ---- Bar / Line / Pie ----
            const PALETTE = [
              'rgba(99,179,237,0.85)', 'rgba(252,129,129,0.85)',
              'rgba(104,211,145,0.85)', 'rgba(246,224,94,0.85)',
              'rgba(183,148,244,0.85)', 'rgba(246,173,85,0.85)',
              'rgba(237,137,54,0.85)', 'rgba(72,187,120,0.85)',
            ];
            const BORDER = PALETTE.map(c => c.replace('0.85)', '1)'));
            const bg = data.values.map((_, i) => PALETTE[i % PALETTE.length]);
            const bd = data.values.map((_, i) => BORDER[i % BORDER.length]);
            const isPie = data.chart_type === 'pie';
            const isLine = data.chart_type === 'line';

            const dataLabelPlugin = {
              id: 'dataLabels',
              afterDatasetsDraw(chart) {
                if (isPie) return;
                const { ctx: c } = chart;
                c.save();
                chart.data.datasets.forEach((dataset, i) => {
                  chart.getDatasetMeta(i).data.forEach((bar, index) => {
                    const value = dataset.data[index];
                    c.fillStyle = textColor;
                    c.font = 'bold 11px Inter, sans-serif';
                    c.textAlign = 'center';
                    c.textBaseline = 'bottom';
                    const { x, y } = bar.tooltipPosition();
                    c.fillText(value.toLocaleString(), x, y - 4);
                  });
                });
                c.restore();
              }
            };

            chartConfig = {
              type: isPie ? 'pie' : isLine ? 'line' : 'bar',
              data: {
                labels: data.labels,
                datasets: [{
                  label: data.chart_title || 'Values',
                  data: data.values,
                  backgroundColor: isPie ? bg : (isLine ? 'rgba(99,179,237,0.15)' : bg),
                  borderColor: isPie ? bd : (isLine ? 'rgba(99,179,237,1)' : bd),
                  borderWidth: isLine ? 2.5 : 1.5,
                  borderRadius: isPie ? 0 : 6,
                  pointBackgroundColor: isLine ? 'rgba(99,179,237,1)' : undefined,
                  pointRadius: isLine ? 5 : undefined,
                  pointHoverRadius: isLine ? 7 : undefined,
                  fill: isLine ? true : false,
                  tension: isLine ? 0.4 : 0,
                }]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 700, easing: 'easeOutQuart' },
                plugins: {
                  legend: {
                    display: isPie,
                    position: 'bottom',
                    labels: {
                      color: textColor,
                      padding: 16,
                      font: { size: 12, family: 'Inter, sans-serif' },
                      usePointStyle: true,
                    }
                  },
                  title: {
                    display: true,
                    text: data.chart_title || text.slice(0, 60),
                    color: textColor,
                    font: { size: 13, weight: '600', family: 'Inter, sans-serif' },
                    padding: { bottom: 12 }
                  },
                  tooltip: {
                    backgroundColor: isDark ? '#1e1e2a' : '#fff',
                    titleColor: textColor,
                    bodyColor: textColor,
                    borderColor: isDark ? '#2c2c3a' : '#e5e5e9',
                    borderWidth: 1,
                    padding: 10,
                    callbacks: {
                      label: ctx => {
                        const v = ctx.parsed.y ?? ctx.parsed;
                        return ` ${ctx.dataset.label}: ${typeof v === 'number' ? v.toLocaleString() : v}`;
                      }
                    }
                  }
                },
                scales: isPie ? {} : {
                  y: {
                    beginAtZero: true,
                    ticks: {
                      color: textColor,
                      font: { size: 11, family: 'Inter, sans-serif' },
                      callback: v => typeof v === 'number' && v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v
                    },
                    grid: { color: gridColor },
                    border: { color: gridColor }
                  },
                  x: {
                    ticks: {
                      color: textColor,
                      font: { size: 11, family: 'Inter, sans-serif' },
                      maxRotation: 35
                    },
                    grid: { display: false },
                    border: { color: gridColor }
                  }
                }
              },
              plugins: isPie ? [] : [dataLabelPlugin]
            };
          } // end else (bar/line/pie)

          new Chart(ctx, chartConfig);
        }, 50); // end setTimeout

      } else {
        messagesContainer.appendChild(aiDiv);
      }

      messagesContainer.scrollTop = messagesContainer.scrollHeight;

    } catch (error) {
      console.error('Query Error:', error);
      const aiDiv = document.createElement('div');
      aiDiv.className = 'message ai-message';
      aiDiv.innerHTML = `<div class="bubble" style="color: var(--error-color, #ff4c4c);">Error: ${error.message}</div>`;
      messagesContainer.appendChild(aiDiv);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } finally {
      loadingIndicator.classList.remove('visible');
    }
  });

  messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendButton.click();
    }
  });

  // ------ file upload (trigger hidden input) ------
  uploadButton.addEventListener('click', () => {
    fileInput.click();
  });

  fileInput.addEventListener('change', async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    await handleFileUpload(files[0]);
    fileInput.value = ''; // reset
  });

  // ------ drag & drop functionality ------
  const mainChat = document.getElementById('mainChat');

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    mainChat.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ['dragenter', 'dragover'].forEach(eventName => {
    mainChat.addEventListener(eventName, () => {
      dragOverlay.classList.add('active');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    mainChat.addEventListener(eventName, () => {
      dragOverlay.classList.remove('active');
    });
  });

  mainChat.addEventListener('drop', async (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      await handleFileUpload(files[0]);
    }
  });

  // ------ extra: make sure sidebar doesn't stay open on resize ------
  window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
      sidebar.classList.remove('open'); // optional, but remove mobile state
    }
  });

  // initial theme consistency: set sun based on dark mode presence?
  const isDarkInit = body.classList.contains('dark');
  setTheme(isDarkInit);

  // ------ Init Demo Chart ------
  const demoCanvas = document.getElementById('demoChartCanvas');
  if (demoCanvas) {
    const demoCtx = demoCanvas.getContext('2d');
    const isDarkDemo = body.classList.contains('dark');
    const textCol = isDarkDemo ? '#ECEFF4' : '#2E3440';
    const gridCol = isDarkDemo ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)';

    // Gradient fill for the line
    const grad = demoCtx.createLinearGradient(0, 0, 0, 200);
    grad.addColorStop(0, 'rgba(99,179,237,0.5)');
    grad.addColorStop(1, 'rgba(99,179,237,0.0)');

    new Chart(demoCtx, {
      type: 'line',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
          label: 'Revenue ($k)',
          data: [12, 19, 15, 27, 22, 31],
          backgroundColor: grad,
          borderColor: 'rgba(99,179,237,1)',
          borderWidth: 2.5,
          pointBackgroundColor: 'rgba(99,179,237,1)',
          pointRadius: 5,
          pointHoverRadius: 7,
          fill: true,
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 900, easing: 'easeOutQuart' },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              color: textCol,
              font: { size: 11, family: 'Inter, sans-serif' },
              usePointStyle: true
            }
          },
          title: {
            display: true,
            text: '📊 Sample – Monthly Revenue',
            color: textCol,
            font: { size: 12, weight: '600', family: 'Inter, sans-serif' },
            padding: { bottom: 8 }
          },
          tooltip: {
            backgroundColor: isDarkDemo ? '#1e1e2a' : '#fff',
            titleColor: textCol,
            bodyColor: textCol,
            borderColor: isDarkDemo ? '#2c2c3a' : '#e5e5e9',
            borderWidth: 1,
            padding: 8,
            callbacks: {
              label: ctx => ` $${ctx.parsed.y}k`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              color: textCol,
              font: { size: 10, family: 'Inter, sans-serif' },
              callback: v => `$${v}k`
            },
            grid: { color: gridCol },
            border: { color: gridCol }
          },
          x: {
            ticks: { color: textCol, font: { size: 10, family: 'Inter, sans-serif' } },
            grid: { display: false },
            border: { color: gridCol }
          }
        }
      }
    });
  }
});

