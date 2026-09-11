// SKD Tool Desktop Web Client Application Script
// All-in-One Professional Media Suite & Converter

document.addEventListener("DOMContentLoaded", () => {
  // Keyboard Shortcut Filters
  document.addEventListener("keydown", (e) => {
    if (
      e.key === "F12" ||
      (e.ctrlKey && e.shiftKey && ["I", "i", "J", "j", "C", "c"].includes(e.key)) ||
      (e.ctrlKey && ["u", "U", "s", "S"].includes(e.key))
    ) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }
  });

  if (window.lucide) {
    lucide.createIcons();
  }

  // 5-Second Cinematic Intro Splash Animation
  const splashScreen = document.getElementById("splashScreen");
  const splashBar = document.getElementById("splashBar");
  const splashStatusText = document.getElementById("splashStatusText");
  const splashPct = document.getElementById("splashPct");

  if (splashScreen && splashBar) {
    const totalDurationMs = 5000;
    const intervalMs = 25;
    let elapsedMs = 0;

    const splashInterval = setInterval(() => {
      elapsedMs += intervalMs;
      const progress = Math.min((elapsedMs / totalDurationMs) * 100, 100);

      splashBar.style.width = `${progress}%`;
      if (splashPct) splashPct.innerText = `${Math.round(progress)}%`;

      if (splashStatusText) {
        if (progress < 20) {
          splashStatusText.innerText = "Initializing Turbo Multi-Stream Engine...";
        } else if (progress < 42) {
          splashStatusText.innerText = "Connecting High-Speed Media Decoders...";
        } else if (progress < 68) {
          splashStatusText.innerText = "Optimizing Multi-Thread 4K & MP3 Streams...";
        } else if (progress < 88) {
          splashStatusText.innerText = "Verifying VIP Security & Storage Vault...";
        } else {
          splashStatusText.innerText = "Ready! Launching Studio Workspace...";
        }
      }

      if (elapsedMs >= totalDurationMs) {
        clearInterval(splashInterval);
        splashScreen.classList.add("fade-out");
        setTimeout(() => {
          splashScreen.style.display = "none";
        }, 600);
      }
    }, intervalMs);
  }

  // =========================================================================
  // STATE MANAGEMENT
  // =========================================================================
  let activeTab = "instant";
  let activeInstantPreset = "1080p";
  let isDownloading = false;
  let isPaused = false;
  let lastDownloadedFile = null;
  let smartAnalyzedInfo = null;
  let currentPlaylistItems = [];
  let selectedConverterFile = "";
  let isAppLicensed = true;

  const workspaceTitles = {
    instant: "INSTANT DOWNLOADER WORKSPACE",
    queue: "DOWNLOAD QUEUE DASHBOARD",
    batch: "BATCH & PLAYLIST WORKSPACE",
    converter: "MEDIA CONVERTER & AUDIO EXTRACTOR",
    scheduler: "DOWNLOAD SCHEDULER & AUTOMATION",
    vault: "MEDIA VAULT & ARCHIVE",
    settings: "SYSTEM SETTINGS & PREFERENCES"
  };

  // Conditional Preset Section Visibility (Reveal only when link is pasted/typed)
  function updatePresetSectionVisibility() {
    const input = document.getElementById("urlInput");
    const section = document.getElementById("instantPresetSection");
    const val = input ? input.value.trim() : "";
    if (section) {
      if (val.length > 0) {
        section.style.display = "flex";
      } else {
        section.style.display = "none";
      }
    }
  }

  // Workspace Navigation
  function switchTab(tabId) {
    activeTab = tabId;
    document.querySelectorAll(".nav-item").forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
    });
    document.querySelectorAll(".tab-view").forEach(view => {
      view.classList.remove("active");
    });
    const target = document.getElementById(`view${tabId.charAt(0).toUpperCase() + tabId.slice(1)}`);
    if (target) {
      target.classList.add("active");
    }
    const titleEl = document.getElementById("currentWorkspaceTitle");
    if (titleEl && workspaceTitles[tabId]) {
      titleEl.innerText = workspaceTitles[tabId];
    }

    if (tabId === "instant") updatePresetSectionVisibility();
    if (tabId === "queue") loadQueueItems();
    if (tabId === "vault") loadVaultData();
    if (tabId === "scheduler") loadSchedulerData();

    if (window.lucide) lucide.createIcons();
  }

  document.querySelectorAll("[data-tab]").forEach(btn => {
    btn.addEventListener("click", () => {
      const tabId = btn.getAttribute("data-tab");
      switchTab(tabId);
    });
  });

  // =========================================================================
  // FEATURE 1 & 2: INSTANT DOWNLOADER & SMART LINK ANALYZER
  // =========================================================================
  let currentLanguage = "km";

  function resetDownloadButtonState() {
    if (btnDownloadNow) {
      btnDownloadNow.disabled = false;
      btnDownloadNow.innerHTML = `<i data-lucide="zap"></i> <span>DOWNLOAD NOW</span>`;
    }
    if (btnSmartDownload) {
      btnSmartDownload.disabled = false;
      const isKm = (currentLanguage === "km");
      btnSmartDownload.innerHTML = `<i data-lucide="download"></i> <span id="smartBtnDlText">${isKm ? "ទាញយកឥឡូវនេះ" : "Download Now"}</span>`;
    }
    if (window.lucide) lucide.createIcons();
  }

  const urlInput = document.getElementById("urlInput");
  const btnPaste = document.getElementById("btnPaste");
  const btnClearUrl = document.getElementById("btnClearUrl");
  const btnDownloadNow = document.getElementById("btnDownloadNow");
  const btnInstantAddToQueue = document.getElementById("btnInstantAddToQueue") || document.getElementById("btnAddToQueue");
  const platformDetectBadge = document.getElementById("platformDetectBadge");
  const smartAnalyzerCard = document.getElementById("smartAnalyzerCard");
  const smartThumbImg = document.getElementById("smartThumbImg");
  const smartPlatformPill = document.getElementById("smartPlatformPill");
  const smartDurationPill = document.getElementById("smartDurationPill");
  const smartTitleText = document.getElementById("smartTitleText");
  const smartCreatorText = document.getElementById("smartCreatorText");
  const smartDateText = document.getElementById("smartDateText");
  const smartSizeText = document.getElementById("smartSizeText");
  const btnSmartDownload = document.getElementById("btnSmartDownload");
  const btnSmartAddQueue = document.getElementById("btnSmartAddQueue");
  updatePresetSectionVisibility();

  const qualityCards = document.querySelectorAll(".quality-card");
  qualityCards.forEach(card => {
    card.addEventListener("click", () => {
      qualityCards.forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      activeInstantPreset = card.getAttribute("data-preset");
    });
  });

  // Studio Options Accordion
  const btnStudioOptionsToggle = document.getElementById("btnStudioOptionsToggle");
  const studioOptionsContent = document.getElementById("studioOptionsContent");
  const accordionArrow = document.getElementById("accordionArrow");
  if (btnStudioOptionsToggle) {
    btnStudioOptionsToggle.addEventListener("click", () => {
      const isOpen = studioOptionsContent.classList.toggle("open");
      accordionArrow.classList.toggle("open", isOpen);
    });
  }

  // Live URL Debounced Inspection
  let inspectTimeout = null;
  async function triggerUrlInspection() {
    updatePresetSectionVisibility();
    const url = urlInput ? urlInput.value.trim() : "";
    if (url && (url.startsWith("http://") || url.startsWith("https://"))) {
      if (platformDetectBadge) {
        platformDetectBadge.innerText = "ANALYZING...";
      }
      if (smartAnalyzerCard) {
        smartAnalyzerCard.style.display = "block";
      }
      clearTimeout(inspectTimeout);
      inspectTimeout = setTimeout(async () => {
        if (window.pywebview && window.pywebview.api) {
          try {
            const res = await window.pywebview.api.inspect_url(url);
            if (res && res.success && res.info) {
              smartAnalyzedInfo = res.info;
              renderSmartPreview(res.info);
            }
          } catch (e) {
            console.log("Inspection error:", e);
          }
        }
      }, 400);
    } else {
      if (smartAnalyzerCard) smartAnalyzerCard.style.display = "none";
      if (platformDetectBadge) platformDetectBadge.innerText = "AUTO-DETECT";
    }
  }

  function renderSmartPreview(info) {
    if (!smartAnalyzerCard) return;
    smartAnalyzerCard.style.display = "block";

    if (info.thumbnail) smartThumbImg.src = info.thumbnail;
    if (info.title) smartTitleText.innerText = info.title;
    if (info.duration_str) smartDurationPill.innerText = info.duration_str;
    if (info.uploader) smartCreatorText.innerText = info.uploader;
    if (info.upload_date) smartDateText.innerText = info.upload_date;
    if (info.estimated_size_str) smartSizeText.innerText = info.estimated_size_str;

    if (info.platform) {
      smartPlatformPill.innerText = info.platform.name || "Web Stream";
      smartPlatformPill.style.background = info.platform.badge_color || "#7C5CFF";
      if (platformDetectBadge) {
        platformDetectBadge.innerText = info.platform.name.toUpperCase();
        platformDetectBadge.style.borderColor = info.platform.badge_color || "var(--primary-cyan)";
      }
    }
    if (window.lucide) lucide.createIcons();
  }

  if (urlInput) {
    urlInput.addEventListener("input", () => {
      updatePresetSectionVisibility();
      triggerUrlInspection();
    });
    urlInput.addEventListener("paste", () => {
      setTimeout(() => {
        updatePresetSectionVisibility();
        triggerUrlInspection();
        if (typeof showToast === "function") showToast("✓ Link Pasted!");
      }, 60);
    });
    urlInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleInstantDownload();
      }
    });
  }

  async function performPasteToUrlInput() {
    let txt = "";
    
    // 1. Try PyWebView API
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_clipboard === "function") {
      try {
        txt = await window.pywebview.api.get_clipboard();
      } catch (err) {
        console.warn("PyWebView get_clipboard error:", err);
      }
    }
    
    // 2. Try Navigator Clipboard API
    if (!txt && navigator.clipboard && navigator.clipboard.readText) {
      try {
        txt = await navigator.clipboard.readText();
      } catch (err) {
        console.warn("Navigator clipboard read error:", err);
      }
    }

    // 3. Try document.execCommand paste
    if (!txt && urlInput) {
      try {
        urlInput.focus();
        document.execCommand("paste");
        if (urlInput.value && urlInput.value.trim()) {
          txt = urlInput.value.trim();
        }
      } catch (err) {
        console.warn("execCommand paste error:", err);
      }
    }

    if (txt && typeof txt === "string") {
      txt = txt.trim();
    }

    if (txt && urlInput) {
      urlInput.value = txt;
      urlInput.dispatchEvent(new Event("input", { bubbles: true }));
      urlInput.dispatchEvent(new Event("change", { bubbles: true }));
      updatePresetSectionVisibility();
      triggerUrlInspection();
      urlInput.focus();
      if (typeof showToast === "function") {
        showToast("✓ Link Pasted!");
      }
      return true;
    } else {
      if (urlInput) urlInput.focus();
      return false;
    }
  }

  if (btnPaste) {
    btnPaste.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      performPasteToUrlInput();
    });
  }

  if (btnClearUrl) {
    btnClearUrl.addEventListener("click", () => {
      urlInput.value = "";
      if (smartAnalyzerCard) smartAnalyzerCard.style.display = "none";
      if (platformDetectBadge) platformDetectBadge.innerText = "AUTO-DETECT";
      updatePresetSectionVisibility();
    });
  }

  // =========================================================================
  // CUSTOM CONTEXT MENU CONTROLLER (NATIVE-LIKE RIGHT-CLICK INTERFACE)
  // =========================================================================
  const customContextMenu = document.getElementById("customContextMenu");
  const ctxMenuPaste = document.getElementById("ctxMenuPaste");
  const ctxMenuCopy = document.getElementById("ctxMenuCopy");
  const ctxMenuCut = document.getElementById("ctxMenuCut");
  const ctxMenuSelectAll = document.getElementById("ctxMenuSelectAll");
  const ctxMenuClear = document.getElementById("ctxMenuClear");

  let activeContextTarget = null;

  function hideContextMenu() {
    if (customContextMenu) {
      customContextMenu.style.display = "none";
    }
  }

  function showContextMenu(e, targetEl) {
    if (!customContextMenu) return;
    e.preventDefault();
    e.stopPropagation();

    activeContextTarget = targetEl || e.target;

    // Update item active/disabled states
    const hasValue = activeContextTarget && activeContextTarget.value && activeContextTarget.value.length > 0;
    if (ctxMenuCopy) ctxMenuCopy.classList.toggle("disabled", !hasValue);
    if (ctxMenuCut) ctxMenuCut.classList.toggle("disabled", !hasValue);
    if (ctxMenuClear) ctxMenuClear.classList.toggle("disabled", !hasValue);
    if (ctxMenuSelectAll) ctxMenuSelectAll.classList.toggle("disabled", !hasValue);

    // Compute coordinates safely inside viewport
    const menuWidth = 220;
    const menuHeight = 220;
    let posX = e.clientX;
    let posY = e.clientY;

    if (posX + menuWidth > window.innerWidth) {
      posX = window.innerWidth - menuWidth - 12;
    }
    if (posY + menuHeight > window.innerHeight) {
      posY = window.innerHeight - menuHeight - 12;
    }
    if (posX < 8) posX = 8;
    if (posY < 8) posY = 8;

    customContextMenu.style.left = `${posX}px`;
    customContextMenu.style.top = `${posY}px`;
    customContextMenu.style.display = "flex";

    if (window.lucide) lucide.createIcons();
  }

  // Bind right-click across all input boxes and hero card
  document.addEventListener("contextmenu", (e) => {
    const inputEl = e.target.closest("input, textarea, .hero-input-box, .hero-input-card, .input-action-row");
    if (inputEl) {
      const realTarget = e.target.closest("input, textarea") || urlInput;
      showContextMenu(e, realTarget);
    }
  });

  // Close context menu on external click / keypress
  document.addEventListener("click", (e) => {
    if (customContextMenu && !customContextMenu.contains(e.target)) {
      hideContextMenu();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      hideContextMenu();
    }
  });

  window.addEventListener("blur", hideContextMenu);

  // Context Menu Item Action Handlers
  if (ctxMenuPaste) {
    ctxMenuPaste.addEventListener("click", async (e) => {
      e.stopPropagation();
      hideContextMenu();
      if (activeContextTarget === urlInput || !activeContextTarget) {
        await performPasteToUrlInput();
      } else if (activeContextTarget && typeof activeContextTarget.value !== "undefined") {
        let txt = "";
        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.get_clipboard === "function") {
          try { txt = await window.pywebview.api.get_clipboard(); } catch(_) {}
        }
        if (!txt && navigator.clipboard && navigator.clipboard.readText) {
          try { txt = await navigator.clipboard.readText(); } catch(_) {}
        }
        if (txt) {
          activeContextTarget.value = txt.trim();
          activeContextTarget.dispatchEvent(new Event("input", { bubbles: true }));
          activeContextTarget.focus();
          if (typeof showToast === "function") showToast("✓ Pasted!");
        }
      }
    });
  }

  if (ctxMenuCopy) {
    ctxMenuCopy.addEventListener("click", async (e) => {
      e.stopPropagation();
      hideContextMenu();
      if (!activeContextTarget) return;
      
      const sel = (typeof activeContextTarget.selectionStart === "number" && typeof activeContextTarget.selectionEnd === "number")
        ? activeContextTarget.value.substring(activeContextTarget.selectionStart, activeContextTarget.selectionEnd)
        : "";
      const textToCopy = sel || activeContextTarget.value || "";
      if (!textToCopy) return;

      if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.set_clipboard === "function") {
        try { await window.pywebview.api.set_clipboard(textToCopy); } catch(_) {}
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        try { await navigator.clipboard.writeText(textToCopy); } catch(_) {}
      }
      if (typeof showToast === "function") showToast("✓ Copied to clipboard!");
    });
  }

  if (ctxMenuCut) {
    ctxMenuCut.addEventListener("click", async (e) => {
      e.stopPropagation();
      hideContextMenu();
      if (!activeContextTarget) return;

      const val = activeContextTarget.value || "";
      if (!val) return;

      if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.set_clipboard === "function") {
        try { await window.pywebview.api.set_clipboard(val); } catch(_) {}
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        try { await navigator.clipboard.writeText(val); } catch(_) {}
      }
      activeContextTarget.value = "";
      activeContextTarget.dispatchEvent(new Event("input", { bubbles: true }));
      if (typeof showToast === "function") showToast("✓ Cut to clipboard!");
    });
  }

  if (ctxMenuSelectAll) {
    ctxMenuSelectAll.addEventListener("click", (e) => {
      e.stopPropagation();
      hideContextMenu();
      if (activeContextTarget && typeof activeContextTarget.select === "function") {
        activeContextTarget.focus();
        activeContextTarget.select();
      }
    });
  }

  if (ctxMenuClear) {
    ctxMenuClear.addEventListener("click", (e) => {
      e.stopPropagation();
      hideContextMenu();
      if (activeContextTarget) {
        activeContextTarget.value = "";
        activeContextTarget.dispatchEvent(new Event("input", { bubbles: true }));
        activeContextTarget.focus();
        if (activeContextTarget === urlInput) {
          if (smartAnalyzerCard) smartAnalyzerCard.style.display = "none";
          if (platformDetectBadge) platformDetectBadge.innerText = "AUTO-DETECT";
        }
      }
    });
  }

  // Instant Download Action
  async function handleInstantDownload() {
    const url = urlInput.value.trim();
    if (!url) {
      alert("Please enter or paste a valid media URL first!");
      return;
    }

    if (btnDownloadNow) {
      btnDownloadNow.disabled = true;
      btnDownloadNow.innerHTML = `<i data-lucide="loader"></i> <span>CONNECTING...</span>`;
    }
    if (btnSmartDownload) {
      btnSmartDownload.disabled = true;
      const connTxt = (currentLanguage === "km") ? "កំពុងភ្ជាប់..." : "CONNECTING...";
      btnSmartDownload.innerHTML = `<i data-lucide="loader" class="spin"></i> <span id="smartBtnDlText">${connTxt}</span>`;
      if (window.lucide) lucide.createIcons();
    }
    isDownloading = true;
    isPaused = false;
    updatePauseUI(false);

    const transferCard = document.getElementById("transferCard");
    const transferControlsActive = document.getElementById("transferControlsActive");
    const transferControlsCompleted = document.getElementById("transferControlsCompleted");
    if (transferCard) transferCard.style.display = "flex";
    if (transferControlsActive) transferControlsActive.style.display = "flex";
    if (transferControlsCompleted) transferControlsCompleted.style.display = "none";

    const btnPause = document.getElementById("btnPause");
    const btnStop = document.getElementById("btnStop");
    if (btnPause) {
      btnPause.disabled = false;
      btnPause.classList.remove("is-paused");
      btnPause.title = "Pause download";
      btnPause.innerHTML = `<i data-lucide="pause"></i> <span id="lblPause">Pause</span>`;
    }
    const btnClearVideo = document.getElementById("btnClearVideo") || document.getElementById("btnStop");
    if (btnClearVideo) {
      btnClearVideo.disabled = false;
      btnClearVideo.innerHTML = `<i data-lucide="trash-2"></i> <span>Clear Video</span>`;
    }

    const mediaTitleText = document.getElementById("mediaTitleText");
    const mediaSubText = document.getElementById("mediaSubText");
    const progressBarFill = document.getElementById("progressBarFill");
    if (mediaTitleText) mediaTitleText.innerText = smartAnalyzedInfo ? smartAnalyzedInfo.title : "Connecting to Stream Server...";
    if (mediaSubText) mediaSubText.innerText = url;
    if (progressBarFill) {
      progressBarFill.style.width = "4%";
      progressBarFill.style.background = "";
      progressBarFill.classList.remove("paused-bar");
    }

    if (smartAnalyzedInfo && smartAnalyzedInfo.thumbnail) {
      const mediaThumbImg = document.getElementById("mediaThumbImg");
      if (mediaThumbImg) mediaThumbImg.src = smartAnalyzedInfo.thumbnail;
    }

    if (window.lucide) lucide.createIcons();

    const options = {
      subtitles: document.getElementById("chkSubtitles")?.checked || false,
      bitrate: document.getElementById("selectBitrate")?.value || "320k",
      trim_start: document.getElementById("trimStart")?.value || "",
      trim_end: document.getElementById("trimEnd")?.value || ""
    };

    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.start_download(url, activeInstantPreset, options);
    }
  }

  if (btnDownloadNow) btnDownloadNow.addEventListener("click", handleInstantDownload);
  if (btnSmartDownload) btnSmartDownload.addEventListener("click", handleInstantDownload);

  const btnSmartDownloadCover = document.getElementById("btnSmartDownloadCover");
  if (btnSmartDownloadCover) {
    btnSmartDownloadCover.addEventListener("click", async () => {
      const url = urlInput ? urlInput.value.trim() : "";
      if (!url) {
        alert("Please enter a valid media link first!");
        return;
      }
      btnSmartDownloadCover.disabled = true;
      btnSmartDownloadCover.innerHTML = `<i data-lucide="loader" class="spin"></i> <span>Saving...</span>`;
      if (window.lucide) lucide.createIcons();
      if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.download_thumbnail(url);
      }
    });
  }

  window.onThumbnailDownloaded = function(res) {
    if (btnSmartDownloadCover) {
      btnSmartDownloadCover.disabled = false;
      btnSmartDownloadCover.innerHTML = `<i data-lucide="check"></i> <span>Saved!</span>`;
      setTimeout(() => {
        btnSmartDownloadCover.innerHTML = `<i data-lucide="image"></i> <span>HD Cover</span>`;
        if (window.lucide) lucide.createIcons();
      }, 2500);
    }
    showToast(`✓ Saved HD Cover: ${res.filename || 'Cover.jpg'}`);
    loadRecentDownloads();
    loadVaultData();
  };

  window.onThumbnailDownloadError = function(err) {
    if (btnSmartDownloadCover) {
      btnSmartDownloadCover.disabled = false;
      btnSmartDownloadCover.innerHTML = `<i data-lucide="image"></i> <span>HD Cover</span>`;
      if (window.lucide) lucide.createIcons();
    }
    alert(`Failed to save cover image: ${err}`);
  };

  // Add to Queue from Instant Bar
  async function handleInstantAddToQueue() {
    const url = urlInput.value.trim();
    if (!url) {
      alert("Please paste a link first to add to Queue!");
      return;
    }
    const item = {
      url: url,
      title: smartAnalyzedInfo ? smartAnalyzedInfo.title : "",
      thumbnail: smartAnalyzedInfo ? smartAnalyzedInfo.thumbnail : "",
      duration: smartAnalyzedInfo ? smartAnalyzedInfo.duration : 0,
      duration_str: smartAnalyzedInfo ? smartAnalyzedInfo.duration_str : "--:--",
      uploader: smartAnalyzedInfo ? smartAnalyzedInfo.uploader : "",
      preset: activeInstantPreset,
      subtitles: document.getElementById("chkSubtitles")?.checked || false,
      bitrate: document.getElementById("selectBitrate")?.value || "320k",
      trim_start: document.getElementById("trimStart")?.value || "",
      trim_end: document.getElementById("trimEnd")?.value || ""
    };

    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.queue_add_items([item]);
      if (res && res.success) {
        showToast("✓ Added to Download Queue!");
        urlInput.value = "";
        if (smartAnalyzerCard) smartAnalyzerCard.style.display = "none";
        updatePresetSectionVisibility();
        loadQueueItems();
      }
    }
  }

  if (btnInstantAddToQueue) btnInstantAddToQueue.addEventListener("click", handleInstantAddToQueue);
  if (btnSmartAddQueue) btnSmartAddQueue.addEventListener("click", handleInstantAddToQueue);

  // Instant Pause / Stop Handlers & State Sync
  function updatePauseUI(paused) {
    isPaused = !!paused;
    const btnPause = document.getElementById("btnPause");
    const progressBarFill = document.getElementById("progressBarFill");
    const metricSpeed = document.getElementById("metricSpeed");
    const metricEta = document.getElementById("metricEta");
    const mediaSubText = document.getElementById("mediaSubText");

    if (btnPause) {
      if (isPaused) {
        btnPause.classList.add("is-paused");
        btnPause.title = "Resume download";
        btnPause.innerHTML = `<i data-lucide="play"></i> <span id="lblPause">Resume</span>`;
        if (progressBarFill) {
          progressBarFill.classList.add("paused-bar");
        }
        if (metricSpeed) metricSpeed.innerText = "Speed: Paused (0 KB/s)";
        if (metricEta) metricEta.innerText = "ETA: Paused";
        if (mediaSubText) {
          if (!mediaSubText.getAttribute("data-original-sub")) {
            mediaSubText.setAttribute("data-original-sub", mediaSubText.innerText);
          }
          mediaSubText.innerText = "⏸️ Download paused — Click Resume to continue";
        }
      } else {
        btnPause.classList.remove("is-paused");
        btnPause.title = "Pause download";
        btnPause.innerHTML = `<i data-lucide="pause"></i> <span id="lblPause">Pause</span>`;
        if (progressBarFill) {
          progressBarFill.classList.remove("paused-bar");
        }
        if (mediaSubText && mediaSubText.getAttribute("data-original-sub")) {
          mediaSubText.innerText = mediaSubText.getAttribute("data-original-sub");
          mediaSubText.removeAttribute("data-original-sub");
        }
      }
      if (window.lucide) lucide.createIcons();
    }
  }

  window.onDownloadPauseStateChanged = function(paused) {
    updatePauseUI(paused);
  };

  const btnPause = document.getElementById("btnPause");
  const btnClearVideo = document.getElementById("btnClearVideo") || document.getElementById("btnStop");

  if (btnPause) {
    btnPause.addEventListener("click", () => {
      if (!isDownloading) return;
      isPaused = !isPaused;
      updatePauseUI(isPaused);
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.toggle_pause();
      }
    });
  }

  if (btnClearVideo) {
    btnClearVideo.addEventListener("click", () => {
      // 1. Cancel background download if active
      if (isDownloading && window.pywebview && window.pywebview.api) {
        window.pywebview.api.cancel_download();
      }

      // 2. Reset states
      isDownloading = false;
      isPaused = false;
      updatePauseUI(false);

      // 3. Cleanly dismiss/hide the transfer card
      const transferCard = document.getElementById("transferCard");
      if (transferCard) {
        transferCard.style.display = "none";
      }

      // 4. Re-enable Download Now button
      resetDownloadButtonState();

      // 5. Reset progress bar & metrics
      const progressBarFill = document.getElementById("progressBarFill");
      if (progressBarFill) {
        progressBarFill.style.width = "0%";
        progressBarFill.style.background = "";
        progressBarFill.classList.remove("paused-bar");
      }
      const metricSpeed = document.getElementById("metricSpeed");
      const metricEta = document.getElementById("metricEta");
      const metricSizePercent = document.getElementById("metricSizePercent");
      if (metricSpeed) metricSpeed.innerText = "Speed: 0 KB/s";
      if (metricEta) metricEta.innerText = "ETA: --:--";
      if (metricSizePercent) metricSizePercent.innerText = "0 MB / 0 MB (0.0%)";

      // 6. Provide brief feedback
      showToast("✓ Video cleared");
      if (window.lucide) lucide.createIcons();
    });
  }

  // Transfer Card Completed Controls
  const btnCompletedPlayInApp = document.getElementById("btnCompletedPlayInApp");
  const btnCompletedOpen = document.getElementById("btnCompletedOpen");
  const btnCompletedFolder = document.getElementById("btnCompletedFolder");
  const btnCompletedDelete = document.getElementById("btnCompletedDelete");
  const btnCompletedDismiss = document.getElementById("btnCompletedDismiss");

  if (btnCompletedPlayInApp) {
    btnCompletedPlayInApp.addEventListener("click", () => {
      if (lastDownloadedFile && lastDownloadedFile.path) {
        window.openInAppPlayer(lastDownloadedFile.path, lastDownloadedFile.filename, lastDownloadedFile.thumbnail);
      }
    });
  }

  if (btnCompletedOpen) {
    btnCompletedOpen.addEventListener("click", () => {
      if (lastDownloadedFile && lastDownloadedFile.path && window.pywebview && window.pywebview.api) {
        window.pywebview.api.open_file(lastDownloadedFile.path);
      }
    });
  }
  if (btnCompletedFolder) {
    btnCompletedFolder.addEventListener("click", () => {
      if (window.pywebview && window.pywebview.api) window.pywebview.api.open_save_folder();
    });
  }
  if (btnCompletedDelete) {
    btnCompletedDelete.addEventListener("click", () => {
      if (lastDownloadedFile && lastDownloadedFile.path) {
        window.deleteMediaItem(lastDownloadedFile.path, lastDownloadedFile.filename);
      }
    });
  }
  if (btnCompletedDismiss) {
    btnCompletedDismiss.addEventListener("click", () => {
      const transferCard = document.getElementById("transferCard");
      if (transferCard) transferCard.style.display = "none";
    });
  }

  // =========================================================================
  // =========================================================================
  // AUDIO NOTIFICATION SYSTEM (WINDOWS SYSTEM SOUND)
  // =========================================================================
  let userSoundMode = localStorage.getItem("skd_sound_mode") || "bell"; // 'bell' (Windows System Sound), 'chime', 'mute'
  let isSoundAlertEnabled = localStorage.getItem("skd_sound_enabled") !== "false";

  let sharedAudioCtx = null;
  function getOrCreateAudioContext() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return null;
      if (!sharedAudioCtx) sharedAudioCtx = new AudioCtx();
      return sharedAudioCtx;
    } catch (e) {
      console.log("AudioContext error:", e);
      return null;
    }
  }

  function playModernChime() {
    try {
      const ctx = getOrCreateAudioContext();
      if (!ctx) return;
      if (ctx.state === "suspended") ctx.resume();
      
      const now = ctx.currentTime;
      // High-resolution Studio Crystal Chime (Eb5 - G5 - Bb5 - Eb6)
      const notes = [
        { freq: 622.25, time: 0.00, dur: 0.40, gain: 0.18 },
        { freq: 783.99, time: 0.07, dur: 0.45, gain: 0.20 },
        { freq: 932.33, time: 0.14, dur: 0.55, gain: 0.22 },
        { freq: 1244.50, time: 0.22, dur: 0.85, gain: 0.25 }
      ];

      notes.forEach(n => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(n.freq, now + n.time);
        
        gain.gain.setValueAtTime(0.0001, now + n.time);
        gain.gain.linearRampToValueAtTime(n.gain, now + n.time + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + n.time + n.dur);
        
        osc.connect(gain);
        gain.connect(ctx.destination);
        
        osc.start(now + n.time);
        osc.stop(now + n.time + n.dur);
      });
    } catch (e) {
      console.log("Modern chime error:", e);
    }
  }

  function playBellChime() {
    try {
      const ctx = getOrCreateAudioContext();
      if (!ctx) return;
      if (ctx.state === "suspended") ctx.resume();
      
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(880, now);
      osc.frequency.exponentialRampToValueAtTime(440, now + 0.8);
      
      gain.gain.setValueAtTime(0.25, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.8);
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.8);
    } catch (e) {
      console.log("Bell chime error:", e);
    }
  }

  let _lastSoundPlayedTime = 0;
  function triggerDownloadCompleteSound(title = "") {
    if (!isSoundAlertEnabled || userSoundMode === "mute") return;

    const now = Date.now();
    if (now - _lastSoundPlayedTime < 1500) return; // Prevent double trigger
    _lastSoundPlayedTime = now;

    // 1. Play native Windows system sound via Python bridge (100% genuine Windows sound)
    if (window.pywebview && window.pywebview.api && window.pywebview.api.play_sound_alert) {
      window.pywebview.api.play_sound_alert(userSoundMode || "bell");
    } else {
      if (userSoundMode === "chime") {
        playModernChime();
      } else {
        playBellChime();
      }
    }
  }

  // Python Global Callbacks for Instant Downloader
  window.updateDownloadProgress = function(data) {
    if (isPaused) return; // Freeze progress text while paused

    const transferCard = document.getElementById("transferCard");
    const progressBarFill = document.getElementById("progressBarFill");
    const metricSpeed = document.getElementById("metricSpeed");
    const metricEta = document.getElementById("metricEta");
    const metricSizePercent = document.getElementById("metricSizePercent");
    const mediaTitleText = document.getElementById("mediaTitleText");
    const mediaThumbImg = document.getElementById("mediaThumbImg");
    const thumbDuration = document.getElementById("thumbDuration");

    if (transferCard && transferCard.style.display === "none") transferCard.style.display = "flex";
    if (data.percent !== undefined && progressBarFill) progressBarFill.style.width = `${data.percent}%`;
    if (data.speed_str && metricSpeed) metricSpeed.innerText = `Speed: ${data.speed_str}`;
    if (data.eta_str && metricEta) metricEta.innerText = `ETA: ${data.eta_str}`;
    if (data.total_str && data.downloaded_str && metricSizePercent) {
      metricSizePercent.innerText = `${data.downloaded_str} / ${data.total_str} (${data.percent_str || ''})`;
    }
    if (data.title && mediaTitleText) mediaTitleText.innerText = data.title;
    if (data.thumbnail && mediaThumbImg) mediaThumbImg.src = data.thumbnail;
    if (data.duration_str && thumbDuration) thumbDuration.innerText = data.duration_str;
  };

  window.onDownloadComplete = function(res) {
    isDownloading = false;
    isPaused = false;
    updatePauseUI(false);
    lastDownloadedFile = res;

    resetDownloadButtonState();

    const btnClearVideo = document.getElementById("btnClearVideo") || document.getElementById("btnStop");
    if (btnClearVideo) {
      btnClearVideo.disabled = false;
      btnClearVideo.innerHTML = `<i data-lucide="trash-2"></i> <span>Clear Video</span>`;
    }

    const transferControlsActive = document.getElementById("transferControlsActive");
    const transferControlsCompleted = document.getElementById("transferControlsCompleted");
    if (transferControlsActive) transferControlsActive.style.display = "none";
    if (transferControlsCompleted) transferControlsCompleted.style.display = "flex";

    const mediaTitleText = document.getElementById("mediaTitleText");
    const mediaSubText = document.getElementById("mediaSubText");
    const progressBarFill = document.getElementById("progressBarFill");
    if (progressBarFill) {
      progressBarFill.classList.remove("paused-bar");
      progressBarFill.style.width = "100%";
      progressBarFill.style.background = "";
    }
    if (mediaTitleText) mediaTitleText.innerText = `✓ Download Complete: ${res.filename || 'Media File'}`;
    if (mediaSubText) mediaSubText.innerText = `Saved to: ${res.path || 'Downloads folder'}`;

    if (window.lucide) lucide.createIcons();
    loadRecentDownloads();
    loadVaultData();

    // Trigger Sound & Voice Alert Announcement
    triggerDownloadCompleteSound(res.filename);
  };

  window.onDownloadError = function(err) {
    // If cancelled by user, redirect cleanly to onDownloadCancelled
    if (err && (err.toLowerCase().includes("cancelled") || err.toLowerCase().includes("stopped"))) {
      window.onDownloadCancelled();
      return;
    }

    isDownloading = false;
    isPaused = false;
    updatePauseUI(false);
    lastDownloadedFile = null;

    resetDownloadButtonState();

    const btnClearVideo = document.getElementById("btnClearVideo") || document.getElementById("btnStop");
    if (btnClearVideo) {
      btnClearVideo.disabled = false;
      btnClearVideo.innerHTML = `<i data-lucide="trash-2"></i> <span>Clear Video</span>`;
    }

    const mediaTitleText = document.getElementById("mediaTitleText");
    const mediaSubText = document.getElementById("mediaSubText");
    const progressBarFill = document.getElementById("progressBarFill");
    if (mediaTitleText) mediaTitleText.innerText = "❌ Download Failed";
    if (mediaSubText) mediaSubText.innerText = `${err || 'Error downloading media'}`;
    if (progressBarFill) {
      progressBarFill.classList.remove("paused-bar");
      progressBarFill.style.width = "100%";
      progressBarFill.style.background = "#EF4444";
    }
    if (window.lucide) lucide.createIcons();
  };

  window.onDownloadCancelled = function() {
    isDownloading = false;
    isPaused = false;
    updatePauseUI(false);

    resetDownloadButtonState();

    const btnClearVideo = document.getElementById("btnClearVideo") || document.getElementById("btnStop");
    if (btnClearVideo) {
      btnClearVideo.disabled = false;
      btnClearVideo.innerHTML = `<i data-lucide="trash-2"></i> <span>Clear Video</span>`;
    }

    const mediaTitleText = document.getElementById("mediaTitleText");
    const mediaSubText = document.getElementById("mediaSubText");
    const progressBarFill = document.getElementById("progressBarFill");
    const metricSpeed = document.getElementById("metricSpeed");
    const metricEta = document.getElementById("metricEta");

    if (mediaTitleText) mediaTitleText.innerText = "⏹️ Download Stopped";
    if (mediaSubText) mediaSubText.innerText = "Download stopped by user. Temporary files cleared.";
    if (progressBarFill) {
      progressBarFill.classList.remove("paused-bar");
      progressBarFill.style.background = "#64748B";
    }
    if (metricSpeed) metricSpeed.innerText = "Speed: 0 KB/s";
    if (metricEta) metricEta.innerText = "ETA: --:--";

    if (window.lucide) lucide.createIcons();
  };

  // =========================================================================
  // FEATURE ①: DOWNLOAD QUEUE WORKSPACE
  // =========================================================================
  const queueItemsList = document.getElementById("queueItemsList");
  const queueConcurrencyRange = document.getElementById("queueConcurrencyRange");
  const queueConcurrencyVal = document.getElementById("queueConcurrencyVal");
  const btnStartQueueGlobal = document.getElementById("btnStartQueueGlobal");
  const btnPauseQueueGlobal = document.getElementById("btnPauseQueueGlobal");
  const btnClearCompletedQueue = document.getElementById("btnClearCompletedQueue");
  const btnClearAllQueue = document.getElementById("btnClearAllQueue");
  const sidebarQueueBadge = document.getElementById("sidebarQueueBadge");

  async function loadQueueItems() {
    if (window.pywebview && window.pywebview.api) {
      const items = await window.pywebview.api.queue_get_items();
      renderQueueItems(items || []);
    }
  }

  function renderQueueItems(items) {
    if (!queueItemsList) return;

    // Update badge counter in sidebar
    if (sidebarQueueBadge) {
      const activeWaiting = items.filter(it => it.status === "waiting" || it.status === "downloading" || it.status === "analyzing").length;
      if (activeWaiting > 0) {
        sidebarQueueBadge.style.display = "inline-block";
        sidebarQueueBadge.innerText = activeWaiting;
      } else {
        sidebarQueueBadge.style.display = "none";
      }
    }

    if (!items || items.length === 0) {
      queueItemsList.innerHTML = `
        <div class="empty-state">
          <i data-lucide="list-ordered" class="empty-icon"></i>
          <p>Queue is currently empty. Add media links from Instant Downloader or Batch Workspace.</p>
        </div>
      `;
      if (window.lucide) lucide.createIcons();
      return;
    }

    queueItemsList.innerHTML = items.map((it, idx) => {
      const isDownloading = it.status === "downloading" || it.status === "analyzing";
      const cardClass = isDownloading ? "queue-item-card downloading" : "queue-item-card";
      const safeTitle = (it.title || "Media Stream").replace(/'/g, "\\'");
      const safePath = (it.file_path || "").replace(/\\/g, '\\\\').replace(/'/g, "\\'");

      return `
        <div class="${cardClass}" id="queueItem_${it.id}">
          <div class="queue-priority-box">
            <button class="btn-priority-up" onclick="window.queueMoveItem('${it.id}', 'up')" title="Move Up priority">▲</button>
            <button class="btn-priority-down" onclick="window.queueMoveItem('${it.id}', 'down')" title="Move Down priority">▼</button>
          </div>

          <div class="queue-thumb-box">
            <img src="${it.thumbnail || 'assets/default_thumb.png'}" class="queue-thumb-img" onerror="this.src='../assets/default_thumb.png'">
          </div>

          <div class="queue-info-box">
            <div class="queue-title-row">
              <div class="queue-item-title" title="${safeTitle}">${it.title || 'Media Stream'}</div>
              <span class="queue-item-preset">${it.preset.toUpperCase()}</span>
              <span class="queue-status-badge ${it.status}">${it.status}</span>
            </div>

            <div class="queue-prog-row">
              <div class="queue-prog-track">
                <div class="queue-prog-fill" style="width: ${it.percent || 0}%;"></div>
              </div>
              <span style="font-size:0.75rem; font-weight:700; color:var(--text-white); width:42px; text-align:right;">${it.percent_str || '0%'}</span>
            </div>

            <div class="queue-metrics-row">
              <span>⚡ ${it.speed_str || '0 KB/s'}</span>
              <span>⏱️ ETA: ${it.eta_str || '--:--'}</span>
              <span>📁 ${it.downloaded_str || '0 B'} / ${it.total_str || 'Calculated'}</span>
            </div>
          </div>

          <div class="queue-actions-box">
            ${it.status === 'downloading' ? `
              <button class="btn-mini-action" onclick="window.queuePauseItem('${it.id}')" title="Pause">⏸️</button>
              <button class="btn-mini-action" onclick="window.queueCancelItem('${it.id}')" title="Cancel">⏹️</button>
            ` : ''}

            ${it.status === 'paused' ? `
              <button class="btn-mini-action" onclick="window.queueResumeItem('${it.id}')" title="Resume">▶️</button>
              <button class="btn-mini-action" onclick="window.queueCancelItem('${it.id}')" title="Cancel">⏹️</button>
            ` : ''}

            ${(it.status === 'failed' || it.status === 'cancelled') ? `
              <button class="btn-mini-action" onclick="window.queueRetryItem('${it.id}')" title="Retry">🔄 Retry</button>
            ` : ''}

            ${it.status === 'completed' && it.file_path ? `
              <button class="btn-mini-action" onclick="window.pywebview.api.open_file('${safePath}')" title="Open File">▶ Open</button>
            ` : ''}

            <button class="btn-mini-delete" onclick="window.queueRemoveItem('${it.id}')" title="Remove from queue">✕</button>
          </div>
        </div>
      `;
    }).join("");

    if (window.lucide) lucide.createIcons();
  }

  // Queue Global Controls
  if (btnStartQueueGlobal) {
    btnStartQueueGlobal.addEventListener("click", async () => {
      if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.queue_start();
        loadQueueItems();
      }
    });
  }
  if (btnPauseQueueGlobal) {
    btnPauseQueueGlobal.addEventListener("click", async () => {
      if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.queue_pause();
        loadQueueItems();
      }
    });
  }
  if (btnClearCompletedQueue) {
    btnClearCompletedQueue.addEventListener("click", async () => {
      if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.queue_clear_completed();
        loadQueueItems();
      }
    });
  }
  if (btnClearAllQueue) {
    btnClearAllQueue.addEventListener("click", async () => {
      if (confirm("Are you sure you want to clear the entire download queue?")) {
        if (window.pywebview && window.pywebview.api) {
          await window.pywebview.api.queue_clear_all();
          loadQueueItems();
        }
      }
    });
  }

  // Concurrency Range Slider
  if (queueConcurrencyRange && queueConcurrencyVal) {
    queueConcurrencyRange.addEventListener("input", async (e) => {
      const val = parseInt(e.target.value);
      queueConcurrencyVal.innerText = val;
      if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.queue_set_concurrency(val);
      }
    });
  }

  // Exposed Global Queue Action Handlers
  window.queueMoveItem = async function(id, direction) {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.queue_move(id, direction);
      loadQueueItems();
    }
  };
  window.queueRemoveItem = async function(id) {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.queue_remove_item(id);
      loadQueueItems();
    }
  };
  window.queuePauseItem = async function(id) {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.queue_pause_item(id);
      loadQueueItems();
    }
  };
  window.queueResumeItem = async function(id) {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.queue_resume_item(id);
      loadQueueItems();
    }
  };
  window.queueRetryItem = async function(id) {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.queue_retry_item(id);
      loadQueueItems();
    }
  };
  window.queueCancelItem = async function(id) {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.queue_cancel_item(id);
      loadQueueItems();
    }
  };

  // Python Event Listeners for Queue Real-Time Updates
  window.onQueueUpdated = function(items) {
    renderQueueItems(items);
  };
  const completedQueueItemsSoundTracker = new Set();
  window.onQueueItemUpdated = function(item) {
    if (item && item.status === 'completed' && !completedQueueItemsSoundTracker.has(item.id)) {
      completedQueueItemsSoundTracker.add(item.id);
      triggerDownloadCompleteSound(item.title || "Media File");
    }

    // If we are currently viewing the queue tab, update the specific item card
    if (activeTab === "queue") {
      const el = document.getElementById(`queueItem_${item.id}`);
      if (el) {
        const fill = el.querySelector(".queue-prog-fill");
        if (fill) fill.style.width = `${item.percent || 0}%`;
        const pctText = el.querySelector(".queue-prog-row span");
        if (pctText) pctText.innerText = item.percent_str || "0%";
        const statusBadge = el.querySelector(".queue-status-badge");
        if (statusBadge) {
          statusBadge.className = `queue-status-badge ${item.status}`;
          statusBadge.innerText = item.status;
        }
      } else {
        loadQueueItems();
      }
    }
  };

  // =========================================================================
  // FEATURE ③: BATCH & PLAYLIST DOWNLOADER
  // =========================================================================
  const subtabBtnBatch = document.getElementById("subtabBtnBatch");
  const subtabBtnPlaylist = document.getElementById("subtabBtnPlaylist");
  const subviewBatchLinks = document.getElementById("subviewBatchLinks");
  const subviewPlaylist = document.getElementById("subviewPlaylist");

  if (subtabBtnBatch && subtabBtnPlaylist) {
    subtabBtnBatch.addEventListener("click", () => {
      subtabBtnBatch.classList.add("active");
      subtabBtnPlaylist.classList.remove("active");
      if (subviewBatchLinks) subviewBatchLinks.classList.add("active");
      if (subviewPlaylist) subviewPlaylist.classList.remove("active");
    });
    subtabBtnPlaylist.addEventListener("click", () => {
      subtabBtnPlaylist.classList.add("active");
      subtabBtnBatch.classList.remove("active");
      if (subviewPlaylist) subviewPlaylist.classList.add("active");
      if (subviewBatchLinks) subviewBatchLinks.classList.remove("active");
    });
  }

  // Multi-Link Batch Actions
  const batchUrlsInput = document.getElementById("batchUrlsInput");
  const batchPresetSelect = document.getElementById("batchPresetSelect");
  const btnImportLinksFile = document.getElementById("btnImportLinksFile");
  const btnBatchAddToQueue = document.getElementById("btnBatchAddToQueue");
  const btnStartBatchDirect = document.getElementById("btnStartBatchDirect");

  if (btnImportLinksFile) {
    btnImportLinksFile.addEventListener("click", async () => {
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.import_links_dialog();
        if (res && res.success && res.links) {
          batchUrlsInput.value = res.links.join("\n");
          showToast(`✓ Imported ${res.count} links from file!`);
        }
      }
    });
  }

  async function handleBatchAdd(autoStart = false) {
    const txt = batchUrlsInput ? batchUrlsInput.value.trim() : "";
    if (!txt) {
      alert("Please paste or import links first!");
      return;
    }
    const lines = txt.split("\n").map(l => l.trim()).filter(l => l && (l.startsWith("http://") || l.startsWith("https://")));
    if (lines.length === 0) {
      alert("No valid URLs found in input!");
      return;
    }

    const preset = batchPresetSelect ? batchPresetSelect.value : "1080p";
    const items = lines.map(u => ({ url: u, preset: preset }));

    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.queue_add_items(items);
      if (autoStart) {
        await window.pywebview.api.queue_start();
      }
      showToast(`✓ Added ${lines.length} items to Queue!`);
      batchUrlsInput.value = "";
      switchTab("queue");
    }
  }

  if (btnBatchAddToQueue) btnBatchAddToQueue.addEventListener("click", () => handleBatchAdd(false));
  if (btnStartBatchDirect) btnStartBatchDirect.addEventListener("click", () => handleBatchAdd(true));

  // Playlist Extractor
  const playlistUrlInput = document.getElementById("playlistUrlInput");
  const btnExtractPlaylist = document.getElementById("btnExtractPlaylist");
  const playlistSummaryCard = document.getElementById("playlistSummaryCard");
  const playlistTitleText = document.getElementById("playlistTitleText");
  const playlistMetaText = document.getElementById("playlistMetaText");
  const playlistItemsContainer = document.getElementById("playlistItemsContainer");
  const btnPlaylistSelectAll = document.getElementById("btnPlaylistSelectAll");
  const btnPlaylistUnselectAll = document.getElementById("btnPlaylistUnselectAll");
  const btnPlaylistAddQueue = document.getElementById("btnPlaylistAddQueue");
  const btnPlaylistDownloadSelected = document.getElementById("btnPlaylistDownloadSelected");
  const chkPlaylistNumbering = document.getElementById("chkPlaylistNumbering");

  if (btnExtractPlaylist) {
    btnExtractPlaylist.addEventListener("click", async () => {
      const url = playlistUrlInput ? playlistUrlInput.value.trim() : "";
      if (!url) {
        alert("Please paste a playlist URL first!");
        return;
      }

      btnExtractPlaylist.disabled = true;
      btnExtractPlaylist.innerHTML = `<i data-lucide="loader"></i> <span>Extracting...</span>`;
      if (window.lucide) lucide.createIcons();

      try {
        if (window.pywebview && window.pywebview.api) {
          const res = await window.pywebview.api.extract_playlist(url);
          if (res && res.success && res.items) {
            currentPlaylistItems = res.items;
            renderPlaylistItems(res.items);
            if (playlistSummaryCard) playlistSummaryCard.style.display = "block";
            if (playlistTitleText) playlistTitleText.innerText = "Extracted Playlist";
            if (playlistMetaText) playlistMetaText.innerText = `${res.count} Videos available for selective download`;
          } else {
            alert(`Failed to extract playlist: ${res ? res.error : 'Unknown error'}`);
          }
        }
      } catch (e) {
        alert(`Playlist Error: ${e}`);
      } finally {
        btnExtractPlaylist.disabled = false;
        btnExtractPlaylist.innerHTML = `<i data-lucide="search"></i> <span>Extract Playlist</span>`;
        if (window.lucide) lucide.createIcons();
      }
    });
  }

  function renderPlaylistItems(items) {
    if (!playlistItemsContainer) return;
    playlistItemsContainer.innerHTML = items.map((it, idx) => `
      <div class="playlist-item-row">
        <label class="custom-checkbox">
          <input type="checkbox" class="chk-playlist-item" data-idx="${idx}" checked>
          <span class="checkbox-box"></span>
        </label>
        <span style="font-weight:700; color:var(--primary-cyan); min-width:26px;">#${it.index || (idx+1)}</span>
        <span style="flex:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-weight:600; color:var(--text-white);">${it.title}</span>
        <span style="font-size:0.75rem; color:var(--text-dim); font-family:monospace;">${it.duration_str || '--:--'}</span>
      </div>
    `).join("");
  }

  if (btnPlaylistSelectAll) {
    btnPlaylistSelectAll.addEventListener("click", () => {
      document.querySelectorAll(".chk-playlist-item").forEach(chk => chk.checked = true);
    });
  }
  if (btnPlaylistUnselectAll) {
    btnPlaylistUnselectAll.addEventListener("click", () => {
      document.querySelectorAll(".chk-playlist-item").forEach(chk => chk.checked = false);
    });
  }

  async function handlePlaylistBatch(autoStart = false) {
    const checked = Array.from(document.querySelectorAll(".chk-playlist-item:checked"));
    if (checked.length === 0) {
      alert("Please select at least one video from the playlist!");
      return;
    }

    const numbering = chkPlaylistNumbering ? chkPlaylistNumbering.checked : true;
    const itemsToAdd = checked.map((chk, i) => {
      const idx = parseInt(chk.getAttribute("data-idx"));
      const it = currentPlaylistItems[idx];
      const prefix = numbering ? `${(i + 1).toString().padStart(2, '0')} - ` : "";
      return {
        url: it.url,
        title: prefix + (it.title || "Video"),
        duration: it.duration || 0,
        duration_str: it.duration_str || "--:--",
        thumbnail: it.thumbnail || "",
        preset: "1080p"
      };
    });

    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.queue_add_items(itemsToAdd);
      if (autoStart) {
        await window.pywebview.api.queue_start();
      }
      showToast(`✓ Added ${itemsToAdd.length} playlist videos to Queue!`);
      switchTab("queue");
    }
  }

  if (btnPlaylistAddQueue) btnPlaylistAddQueue.addEventListener("click", () => handlePlaylistBatch(false));
  if (btnPlaylistDownloadSelected) btnPlaylistDownloadSelected.addEventListener("click", () => handlePlaylistBatch(true));

  // =========================================================================
  // FEATURE ④: VIDEO CONVERTER & AUDIO EXTRACTOR
  // =========================================================================
  const btnBrowseConverterFile = document.getElementById("btnBrowseConverterFile");
  const converterDropZone = document.getElementById("converterDropZone");
  const converterFilePreview = document.getElementById("converterFilePreview");
  const converterFileName = document.getElementById("converterFileName");
  const converterFilePath = document.getElementById("converterFilePath");
  const converterTargetFormat = document.getElementById("converterTargetFormat");
  const converterResolution = document.getElementById("converterResolution");
  const converterAudioBitrate = document.getElementById("converterAudioBitrate");
  const converterSampleRate = document.getElementById("converterSampleRate");
  const converterOutDir = document.getElementById("converterOutDir");
  const btnBrowseConverterOutDir = document.getElementById("btnBrowseConverterOutDir");
  const btnStartConversion = document.getElementById("btnStartConversion");
  const btnCancelConversion = document.getElementById("btnCancelConversion");
  const converterProgressBox = document.getElementById("converterProgressBox");
  const converterProgBarFill = document.getElementById("converterProgBarFill");
  const converterProgPct = document.getElementById("converterProgPct");
  const converterProgStatus = document.getElementById("converterProgStatus");
  const converterProgSpeed = document.getElementById("converterProgSpeed");
  const converterProgTime = document.getElementById("converterProgTime");

  // Preset Pills in Converter
  let activeConverterPreset = "1080p_video";
  document.querySelectorAll(".preset-pill").forEach(pill => {
    pill.addEventListener("click", () => {
      document.querySelectorAll(".preset-pill").forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      activeConverterPreset = pill.getAttribute("data-preset");

      // Auto set formats based on preset
      if (activeConverterPreset === "mp3_320k") {
        if (converterTargetFormat) converterTargetFormat.value = "mp3";
        if (converterAudioBitrate) converterAudioBitrate.value = "320k";
      } else if (activeConverterPreset === "mp3_192k") {
        if (converterTargetFormat) converterTargetFormat.value = "mp3";
        if (converterAudioBitrate) converterAudioBitrate.value = "192k";
      } else if (activeConverterPreset === "wav_lossless") {
        if (converterTargetFormat) converterTargetFormat.value = "wav";
      } else if (activeConverterPreset === "gif_animation") {
        if (converterTargetFormat) converterTargetFormat.value = "gif";
      } else if (activeConverterPreset === "4k_video") {
        if (converterTargetFormat) converterTargetFormat.value = "mp4";
        if (converterResolution) converterResolution.value = "3840x2160";
      } else if (activeConverterPreset === "1080p_video") {
        if (converterTargetFormat) converterTargetFormat.value = "mp4";
        if (converterResolution) converterResolution.value = "1920x1080";
      } else if (activeConverterPreset === "720p_video") {
        if (converterTargetFormat) converterTargetFormat.value = "mp4";
        if (converterResolution) converterResolution.value = "1280x720";
      }
    });
  });

  async function handleSelectConverterFile() {
    if (window.pywebview && window.pywebview.api) {
      const fpath = await window.pywebview.api.select_local_file("Select Media File to Convert");
      if (fpath) {
        selectedConverterFile = fpath;
        if (converterDropZone) converterDropZone.style.display = "none";
        if (converterFilePreview) converterFilePreview.style.display = "flex";
        if (converterFileName) converterFileName.innerText = fpath.split('\\').pop() || 'Media File';
        if (converterFilePath) converterFilePath.innerText = fpath;
      }
    }
  }

  if (btnBrowseConverterFile) btnBrowseConverterFile.addEventListener("click", handleSelectConverterFile);
  if (converterDropZone) converterDropZone.addEventListener("click", handleSelectConverterFile);

  if (btnBrowseConverterOutDir) {
    btnBrowseConverterOutDir.addEventListener("click", async () => {
      if (window.pywebview && window.pywebview.api) {
        const folder = await window.pywebview.api.select_local_folder("Select Output Directory");
        if (folder && converterOutDir) {
          converterOutDir.value = folder;
        }
      }
    });
  }

  if (btnStartConversion) {
    btnStartConversion.addEventListener("click", async () => {
      if (!selectedConverterFile) {
        alert("Please select a video or audio file first!");
        return;
      }

      btnStartConversion.disabled = true;
      if (btnCancelConversion) btnCancelConversion.style.display = "inline-flex";
      if (converterProgressBox) converterProgressBox.style.display = "block";

      const outFmt = converterTargetFormat ? converterTargetFormat.value : "mp4";
      const audioBoostEl = document.getElementById("converterAudioBoost");
      const options = {
        preset: activeConverterPreset,
        resolution: converterResolution ? converterResolution.value : "original",
        audio_bitrate: converterAudioBitrate ? converterAudioBitrate.value : "320k",
        audio_sample_rate: converterSampleRate ? converterSampleRate.value : "48000",
        audio_volume: audioBoostEl ? audioBoostEl.value : "1.0",
        output_dir: converterOutDir ? converterOutDir.value : ""
      };

      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.convert_local_media(selectedConverterFile, outFmt, options);
      }
    });
  }

  if (btnCancelConversion) {
    btnCancelConversion.addEventListener("click", () => {
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.cancel_conversion();
      }
    });
  }

  // Converter Event Callbacks from Python
  window.onConverterProgress = function(data) {
    if (converterProgBarFill) converterProgBarFill.style.width = `${data.percent || 0}%`;
    if (converterProgPct) converterProgPct.innerText = data.percent_str || `${data.percent}%`;
    if (converterProgStatus) converterProgStatus.innerText = data.speed_str || "Transcoding media stream...";
    if (converterProgSpeed) converterProgSpeed.innerText = data.speed_str || "";
    if (converterProgTime) converterProgTime.innerText = data.time_str || "";
  };

  window.onConverterComplete = function(res) {
    if (btnStartConversion) btnStartConversion.disabled = false;
    if (btnCancelConversion) btnCancelConversion.style.display = "none";
    if (converterProgStatus) converterProgStatus.innerText = `✓ Conversion Finished! Saved as ${res.filename}`;
    if (converterProgBarFill) converterProgBarFill.style.width = "100%";
    if (converterProgPct) converterProgPct.innerText = "100%";
    showToast(`✓ Converted to ${res.format ? res.format.toUpperCase() : 'Media'} successfully!`);
    loadVaultData();

    // Trigger Sound Alert on conversion complete
    triggerDownloadCompleteSound(res.filename);
  };

  window.onConverterError = function(err) {
    if (btnStartConversion) btnStartConversion.disabled = false;
    if (btnCancelConversion) btnCancelConversion.style.display = "none";
    alert(`Conversion Error: ${err}`);
  };

  // =========================================================================
  // FEATURE ⑤: DOWNLOAD SCHEDULER & AUTOMATION
  // =========================================================================
  const schedJobName = document.getElementById("schedJobName");
  const schedStartTime = document.getElementById("schedStartTime");
  const schedRepeat = document.getElementById("schedRepeat");
  const schedUrls = document.getElementById("schedUrls");
  const schedPreset = document.getElementById("schedPreset");
  const schedSpeedLimit = document.getElementById("schedSpeedLimit");
  const btnAddSchedulerJob = document.getElementById("btnAddSchedulerJob");
  const scheduledJobsList = document.getElementById("scheduledJobsList");

  async function loadSchedulerData() {
    if (window.pywebview && window.pywebview.api) {
      const jobs = await window.pywebview.api.get_scheduler_jobs();
      renderSchedulerJobs(jobs || []);

      const auto = await window.pywebview.api.get_automation_settings();
      if (auto) {
        if (document.getElementById("chkAutoClipboard")) document.getElementById("chkAutoClipboard").checked = !!auto.clipboard_sniffer;
        if (document.getElementById("chkAutoDownload")) document.getElementById("chkAutoDownload").checked = !!auto.auto_download;
        if (document.getElementById("chkAutoOrganize")) document.getElementById("chkAutoOrganize").checked = !!auto.auto_organize_files;
        if (document.getElementById("chkAutoRetry")) document.getElementById("chkAutoRetry").checked = !!auto.auto_retry_failed;
        if (document.getElementById("chkAutoOpenFolder")) document.getElementById("chkAutoOpenFolder").checked = !!auto.auto_open_folder;
        if (document.getElementById("chkAutoShutdown")) document.getElementById("chkAutoShutdown").checked = !!auto.shutdown_pc_after_complete;
        if (document.getElementById("chkAutoSoundAlert")) {
          document.getElementById("chkAutoSoundAlert").checked = auto.sound_alert_on_complete !== false;
          isSoundAlertEnabled = auto.sound_alert_on_complete !== false;
        }
        if (auto.sound_mode) {
          userSoundMode = auto.sound_mode;
          if (document.getElementById("settingSoundMode")) {
            document.getElementById("settingSoundMode").value = userSoundMode;
          }
        }
      }
    }
  }

  function renderSchedulerJobs(jobs) {
    if (!scheduledJobsList) return;
    if (!jobs || jobs.length === 0) {
      scheduledJobsList.innerHTML = `<div class="empty-state">No scheduled jobs active. Use the form above to schedule automated downloads.</div>`;
      return;
    }

    scheduledJobsList.innerHTML = jobs.map(j => `
      <div class="scheduled-job-card">
        <div class="scheduled-job-info">
          <h4>${j.name} (${j.start_time})</h4>
          <p>${j.repeat.toUpperCase()} • ${j.preset} • ${j.urls ? j.urls.length : 0} URLs • Status: <strong>${j.status}</strong></p>
        </div>
        <div>
          <button class="btn-mini-delete" onclick="window.removeSchedulerJob('${j.id}')" title="Delete scheduled job">🗑️ Delete</button>
        </div>
      </div>
    `).join("");
  }

  if (btnAddSchedulerJob) {
    btnAddSchedulerJob.addEventListener("click", async () => {
      const name = schedJobName ? schedJobName.value.trim() : "";
      const timeStr = schedStartTime ? schedStartTime.value.trim() : "00:00";
      const repeat = schedRepeat ? schedRepeat.value : "once";
      const urlsRaw = schedUrls ? schedUrls.value.trim() : "";
      const preset = schedPreset ? schedPreset.value : "1080p";
      const spd = schedSpeedLimit && schedSpeedLimit.value ? parseInt(schedSpeedLimit.value) : 0;

      const urls = urlsRaw ? urlsRaw.split("\n").map(u => u.trim()).filter(u => u) : [];

      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.add_scheduler_job(
          name, timeStr, "", "", repeat, urls, preset, spd, 3
        );
        if (res && res.success) {
          showToast("✓ Scheduled Job saved successfully!");
          if (schedJobName) schedJobName.value = "";
          if (schedUrls) schedUrls.value = "";
          loadSchedulerData();
        }
      }
    });
  }

  window.removeSchedulerJob = async function(jobId) {
    if (confirm("Remove this scheduled job?")) {
      if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.remove_scheduler_job(jobId);
        loadSchedulerData();
      }
    }
  };

  // Test Sound Handlers
  const btnTestSoundAuto = document.getElementById("btnTestSoundAuto");
  const btnTestSoundSettings = document.getElementById("btnTestSoundSettings");
  const chkAutoSoundAlert = document.getElementById("chkAutoSoundAlert");
  const settingSoundMode = document.getElementById("settingSoundMode");

  if (btnTestSoundAuto) {
    btnTestSoundAuto.addEventListener("click", () => {
      triggerDownloadCompleteSound("Test Video Stream");
      showToast("🔊 Playing Test Audio Alert...");
    });
  }

  if (btnTestSoundSettings) {
    btnTestSoundSettings.addEventListener("click", () => {
      triggerDownloadCompleteSound("Test Video Stream");
      showToast("🔊 Playing Test Audio Alert...");
    });
  }

  if (chkAutoSoundAlert) {
    chkAutoSoundAlert.addEventListener("change", (e) => {
      isSoundAlertEnabled = e.target.checked;
      localStorage.setItem("skd_sound_enabled", isSoundAlertEnabled);
    });
  }

  if (settingSoundMode) {
    settingSoundMode.addEventListener("change", (e) => {
      userSoundMode = e.target.value;
      localStorage.setItem("skd_sound_mode", userSoundMode);
    });
  }

  // Save Automation Rules
  const btnSaveAutomationRules = document.getElementById("btnSaveAutomationRules");
  if (btnSaveAutomationRules) {
    btnSaveAutomationRules.addEventListener("click", async () => {
      const payload = {
        clipboard_sniffer: document.getElementById("chkAutoClipboard")?.checked ?? true,
        auto_download: document.getElementById("chkAutoDownload")?.checked ?? false,
        auto_organize_files: document.getElementById("chkAutoOrganize")?.checked ?? true,
        auto_retry_failed: document.getElementById("chkAutoRetry")?.checked ?? true,
        auto_open_folder: document.getElementById("chkAutoOpenFolder")?.checked ?? true,
        shutdown_pc_after_complete: document.getElementById("chkAutoShutdown")?.checked ?? false,
        sound_alert_on_complete: isSoundAlertEnabled,
        sound_mode: userSoundMode
      };

      if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.save_automation_settings(payload);
        showToast("✓ Smart Automation Rules saved!");
      }
    });
  }

  // Floating Clipboard Sniffer Toast (Disabled / Removed)
  window.onClipboardMediaDetected = function(url) {
    // Popup toast disabled as requested
  };

  // Shutdown Countdown Modal Handlers
  const shutdownModal = document.getElementById("shutdownModal");
  const shutdownCountdownText = document.getElementById("shutdownCountdownText");
  const btnCancelShutdown = document.getElementById("btnCancelShutdown");
  let shutdownSec = 30;
  let shutdownInterval = null;

  window.onShutdownCountdown = function(sec) {
    shutdownSec = sec || 30;
    if (shutdownModal) shutdownModal.classList.add("active");
    if (shutdownCountdownText) shutdownCountdownText.innerText = `${shutdownSec}s`;

    clearInterval(shutdownInterval);
    shutdownInterval = setInterval(() => {
      shutdownSec--;
      if (shutdownCountdownText) shutdownCountdownText.innerText = `${shutdownSec}s`;
      if (shutdownSec <= 0) {
        clearInterval(shutdownInterval);
      }
    }, 1000);
  };

  if (btnCancelShutdown) {
    btnCancelShutdown.addEventListener("click", async () => {
      clearInterval(shutdownInterval);
      if (shutdownModal) shutdownModal.classList.remove("active");
      if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.cancel_system_shutdown();
        showToast("✓ Shutdown cancelled by user.");
      }
    });
  }

  // =========================================================================
  // FEATURE ⑥: MEDIA VAULT & RECENT DOWNLOADS
  // =========================================================================
  let vaultAllItems = [];
  async function loadVaultData() {
    if (window.pywebview && window.pywebview.api) {
      vaultAllItems = await window.pywebview.api.get_history() || [];
      renderVaultList(vaultAllItems);

      if (document.getElementById("statTotalCount")) {
        document.getElementById("statTotalCount").innerText = vaultAllItems.length;
      }

      // Calculate total size across all downloads
      let totalBytes = 0;
      vaultAllItems.forEach(it => {
        if (it.size_bytes) totalBytes += it.size_bytes;
        else if (it.size && typeof it.size === 'string') {
          const match = it.size.match(/([\d\.]+)\s*(MB|GB|KB)/i);
          if (match) {
            const val = parseFloat(match[1]);
            const unit = match[2].toUpperCase();
            if (unit === 'GB') totalBytes += val * 1024 * 1024 * 1024;
            else if (unit === 'MB') totalBytes += val * 1024 * 1024;
            else if (unit === 'KB') totalBytes += val * 1024;
          }
        }
      });
      const sizeEl = document.getElementById("statTotalSize");
      if (sizeEl) {
        if (totalBytes > 1024 * 1024 * 1024) {
          sizeEl.innerText = (totalBytes / (1024 * 1024 * 1024)).toFixed(2) + " GB";
        } else if (totalBytes > 1024 * 1024) {
          sizeEl.innerText = (totalBytes / (1024 * 1024)).toFixed(1) + " MB";
        } else if (totalBytes > 0) {
          sizeEl.innerText = (totalBytes / 1024).toFixed(0) + " KB";
        } else {
          sizeEl.innerText = `${vaultAllItems.length} Files`;
        }
      }
    }
  }

  function renderVaultList(items) {
    const container = document.getElementById("vaultListContainer");
    if (!container) return;

    if (!items || items.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <i data-lucide="folder-open" style="width:36px; height:36px; color:#475569; margin-bottom:8px; display:block; margin-left:auto; margin-right:auto;"></i>
          <p>No media files found in Media Vault.</p>
        </div>
      `;
      if (window.lucide) lucide.createIcons();
      return;
    }

    container.innerHTML = items.map(it => {
      const isAudio = (it.filename && (it.filename.endsWith('.mp3') || it.filename.endsWith('.m4a') || it.filename.endsWith('.wav'))) || (it.category === 'Music');
      const iconSymbol = isAudio ? '🎵' : '🎬';
      const safePath = it.path ? it.path.replace(/\\/g, '\\\\').replace(/'/g, "\\'") : '';
      const safeName = it.filename ? it.filename.replace(/'/g, "\\'") : 'Media File';

      return `
        <div class="history-item-card">
          <div class="history-item-left">
            <div class="history-item-icon">${iconSymbol}</div>
            <div class="history-item-meta">
              <div class="history-item-title" title="${safeName}">${it.filename || 'Media File'}</div>
              <div class="history-item-sub">
                <span class="vault-meta-tag">${it.size || 'HD'}</span>
                <span>•</span>
                <span>${it.time || 'Recently'}</span>
                <span>•</span>
                <span>${it.category || 'Media'}</span>
              </div>
            </div>
          </div>
          <div class="vault-item-actions">
            <button class="btn-vault-play" onclick="window.openInAppPlayer('${safePath}', '${safeName}')" title="Play directly inside SKD Tool">
              <i data-lucide="play" style="width:12px; height:12px;"></i>
              <span>Play</span>
            </button>
            <button class="btn-vault-open" onclick="window.pywebview.api.open_file('${safePath}')" title="Open in default system player">
              <i data-lucide="external-link" style="width:12px; height:12px;"></i>
              <span>Open</span>
            </button>
            <button class="btn-vault-folder" onclick="window.pywebview.api.open_save_folder()" title="Open download folder in Explorer">
              <i data-lucide="folder" style="width:12px; height:12px;"></i>
              <span>Folder</span>
            </button>
            <button class="btn-vault-delete" onclick="window.deleteMediaItem('${safePath}', '${safeName}')" title="Delete file from computer">
              <i data-lucide="trash-2" style="width:12px; height:12px;"></i>
              <span>Delete</span>
            </button>
          </div>
        </div>
      `;
    }).join('');

    if (window.lucide) lucide.createIcons();
  }

  const vaultSearchInput = document.getElementById("vaultSearchInput");
  if (vaultSearchInput) {
    vaultSearchInput.addEventListener("input", (e) => {
      const query = e.target.value.toLowerCase().trim();
      if (!query) {
        renderVaultList(vaultAllItems);
      } else {
        const filtered = vaultAllItems.filter(it => 
          (it.filename && it.filename.toLowerCase().includes(query)) ||
          (it.category && it.category.toLowerCase().includes(query)) ||
          (it.time && it.time.toLowerCase().includes(query))
        );
        renderVaultList(filtered);
      }
    });
  }

  const btnRefreshVault = document.getElementById("btnRefreshVault");
  if (btnRefreshVault) btnRefreshVault.addEventListener("click", loadVaultData);

  const btnClearHistoryAll = document.getElementById("btnClearHistoryAll");
  if (btnClearHistoryAll) {
    btnClearHistoryAll.addEventListener("click", async () => {
      if (confirm("Clear all download history logs? (Files will remain on your computer)")) {
        if (window.pywebview && window.pywebview.api) {
          await window.pywebview.api.clear_all_history();
          loadVaultData();
          loadRecentDownloads();
        }
      }
    });
  }

  // Load Recent Downloads (Home View)
  async function loadRecentDownloads() {
    if (window.pywebview && window.pywebview.api) {
      const items = await window.pywebview.api.get_history();
      const container = document.getElementById("recentDownloadsList");
      if (!container) return;

      if (!items || items.length === 0) {
        container.innerHTML = `
          <div class="empty-recent-state">
            <i data-lucide="inbox" class="empty-icon"></i>
            <p>No recent downloads yet. Paste a link above to start downloading media!</p>
          </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
      }

      const recents = items.slice(0, 8);
      container.innerHTML = recents.map((it, idx) => {
        const isAudio = (it.filename && (it.filename.endsWith('.mp3') || it.filename.endsWith('.m4a') || it.filename.endsWith('.wav'))) || (it.category === 'Music');
        const iconSymbol = isAudio ? '🎵' : '🎬';
        const safePath = it.path ? it.path.replace(/\\/g, '\\\\').replace(/'/g, "\\'") : '';
        const safeName = it.filename ? it.filename.replace(/'/g, "\\'") : 'Media File';
        const safeSize = (it.size || 'HD').replace(/'/g, "\\'");
        const safeCategory = (it.category || 'Media').replace(/'/g, "\\'");
        const safeTime = (it.time || 'Recently').replace(/'/g, "\\'");
        const safeUrl = it.url ? it.url.replace(/'/g, "\\'") : '';
        const menuId = `recentMenu_${idx}`;

        return `
          <div class="recent-item-card">
            <div class="recent-item-left">
              <div class="recent-item-icon">${iconSymbol}</div>
              <div class="recent-item-meta">
                <div class="recent-item-title" title="${it.filename || 'Media File'}">${it.filename || 'Media File'}</div>
                <div class="recent-item-sub">${it.size || 'HD'} • ${it.category || 'Media'} • ${it.time || 'Recently'}</div>
              </div>
            </div>
            <div class="recent-item-right">
              <button class="btn-recent-action btn-recent-play inapp-play-btn" onclick="window.openInAppPlayer('${safePath}', '${safeName}')" title="Play directly inside SKD Tool">
                <i data-lucide="play" class="btn-icon-svg"></i>
                <span>Play</span>
              </button>
              <button class="btn-recent-action btn-recent-folder" onclick="window.pywebview.api.open_save_folder()" title="Open download folder">
                <i data-lucide="folder" class="btn-icon-svg"></i>
                <span>Folder</span>
              </button>
              <div class="recent-dropdown-wrap">
                <button class="btn-recent-more" onclick="window.toggleRecentDropdown(event, '${menuId}')" title="More Options">
                  <i data-lucide="more-vertical"></i>
                </button>
                <div class="recent-dropdown-menu" id="${menuId}">
                  <button class="recent-menu-item" onclick="window.openRecentExternal('${safePath}')">
                    <i data-lucide="external-link"></i>
                    <span>Open in Player</span>
                  </button>
                  <button class="recent-menu-item" onclick="window.showMediaDetails('${safePath}', '${safeName}', '${safeSize}', '${safeCategory}', '${safeTime}', '${safeUrl}')">
                    <i data-lucide="info"></i>
                    <span>File Details</span>
                  </button>
                  <div class="dropdown-divider"></div>
                  <button class="recent-menu-item item-delete" onclick="window.deleteMediaItem('${safePath}', '${safeName}')">
                    <i data-lucide="trash-2"></i>
                    <span>Delete File</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        `;
      }).join('');

      if (window.lucide) lucide.createIcons();
    }
  }

  // Dropdown toggle & outside click listener with smart collision detection
  window.toggleRecentDropdown = function(e, menuId) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    const targetMenu = document.getElementById(menuId);
    const allMenus = document.querySelectorAll(".recent-dropdown-menu");
    allMenus.forEach(m => {
      if (m !== targetMenu) m.classList.remove("active");
    });

    if (targetMenu) {
      const btn = e ? (e.currentTarget || (e.target ? e.target.closest(".btn-recent-more") : null)) : null;
      if (btn) {
        const rect = btn.getBoundingClientRect();
        const spaceBelow = window.innerHeight - rect.bottom;
        if (spaceBelow < 180) {
          targetMenu.classList.add("drop-up");
        } else {
          targetMenu.classList.remove("drop-up");
        }
      }
      targetMenu.classList.toggle("active");
    }
  };

  document.addEventListener("click", () => {
    document.querySelectorAll(".recent-dropdown-menu.active").forEach(m => m.classList.remove("active"));
  });

  window.openRecentExternal = function(filePath) {
    document.querySelectorAll(".recent-dropdown-menu.active").forEach(m => m.classList.remove("active"));
    if (filePath && window.pywebview && window.pywebview.api) {
      window.pywebview.api.open_file(filePath);
    }
  };

  // Media File Details Modal
  window.showMediaDetails = function(filePath, fileName, fileSize, fileCat, fileDate, fileUrl) {
    document.querySelectorAll(".recent-dropdown-menu.active").forEach(m => m.classList.remove("active"));
    const modal = document.getElementById("fileDetailsModal");
    if (!modal) return;

    document.getElementById("detFileName").textContent = fileName || 'Media File';
    document.getElementById("detFileSize").textContent = fileSize || 'Unknown';
    document.getElementById("detFileCategory").textContent = fileCat || 'Media';
    document.getElementById("detFileDate").textContent = fileDate || 'Recently';
    document.getElementById("detFilePath").textContent = filePath || 'N/A';

    const urlRow = document.getElementById("detUrlRow");
    if (fileUrl) {
      urlRow.style.display = "flex";
      document.getElementById("detFileUrl").textContent = fileUrl;
    } else {
      urlRow.style.display = "none";
    }

    const btnPlay = document.getElementById("btnDetPlayInApp");
    if (btnPlay) {
      btnPlay.onclick = () => {
        modal.style.display = "none";
        window.openInAppPlayer(filePath, fileName);
      };
    }

    const btnFolder = document.getElementById("btnDetOpenFolder");
    if (btnFolder) {
      btnFolder.onclick = () => {
        if (window.pywebview && window.pywebview.api) window.pywebview.api.open_save_folder();
      };
    }

    modal.style.display = "flex";
    if (window.lucide) lucide.createIcons();
  };

  // Close details modal handlers
  const btnCloseDetails = document.getElementById("btnCloseDetailsModal");
  if (btnCloseDetails) {
    btnCloseDetails.addEventListener("click", () => {
      const modal = document.getElementById("fileDetailsModal");
      if (modal) modal.style.display = "none";
    });
  }

  const btnCopyDetPath = document.getElementById("btnCopyDetPath");
  if (btnCopyDetPath) {
    btnCopyDetPath.addEventListener("click", () => {
      const txt = document.getElementById("detFilePath").textContent;
      if (navigator.clipboard) navigator.clipboard.writeText(txt);
      btnCopyDetPath.textContent = "Copied!";
      setTimeout(() => btnCopyDetPath.textContent = "Copy", 1500);
    });
  }

  const btnCopyDetUrl = document.getElementById("btnCopyDetUrl");
  if (btnCopyDetUrl) {
    btnCopyDetUrl.addEventListener("click", () => {
      const txt = document.getElementById("detFileUrl").textContent;
      if (navigator.clipboard) navigator.clipboard.writeText(txt);
      btnCopyDetUrl.textContent = "Copied!";
      setTimeout(() => btnCopyDetUrl.textContent = "Copy", 1500);
    });
  }

  // Global Delete File - Compact Modern Modal
  let pendingDeleteFilePath = null;
  let pendingDeleteFileName = null;

  const deleteConfirmModal = document.getElementById("deleteConfirmModal");
  const deleteModalFileName = document.getElementById("deleteModalFileName");
  const btnCloseDeleteModal = document.getElementById("btnCloseDeleteModal");
  const btnCancelDeleteModal = document.getElementById("btnCancelDeleteModal");
  const btnConfirmDeleteModal = document.getElementById("btnConfirmDeleteModal");

  function closeDeleteModal() {
    if (deleteConfirmModal) deleteConfirmModal.style.display = "none";
    pendingDeleteFilePath = null;
    pendingDeleteFileName = null;
  }

  if (btnCloseDeleteModal) btnCloseDeleteModal.addEventListener("click", closeDeleteModal);
  if (btnCancelDeleteModal) btnCancelDeleteModal.addEventListener("click", closeDeleteModal);
  if (deleteConfirmModal) {
    deleteConfirmModal.addEventListener("click", (e) => {
      if (e.target === deleteConfirmModal) closeDeleteModal();
    });
  }

  if (btnConfirmDeleteModal) {
    btnConfirmDeleteModal.addEventListener("click", async () => {
      const filePath = pendingDeleteFilePath;
      const displayName = pendingDeleteFileName;
      closeDeleteModal();
      if (!filePath) return;

      if (window.pywebview && window.pywebview.api) {
        try {
          const res = await window.pywebview.api.delete_history_item(filePath, true);
          if (res && res.success) {
            if (lastDownloadedFile && (lastDownloadedFile.path === filePath || lastDownloadedFile.filename === displayName)) {
              const transferCard = document.getElementById("transferCard");
              if (transferCard) transferCard.style.display = "none";
              lastDownloadedFile = null;
            }
            await loadRecentDownloads();
            await loadVaultData();
            showToast("✓ File deleted successfully");
          } else {
            showToast(`⚠️ Delete failed: ${res ? res.error : 'Unknown error'}`);
          }
        } catch (err) {
          showToast(`⚠️ Error: ${err}`);
        }
      }
    });
  }

  window.deleteMediaItem = function(filePath, fileName) {
    document.querySelectorAll(".recent-dropdown-menu.active").forEach(m => m.classList.remove("active"));
    if (!filePath) return;
    pendingDeleteFilePath = filePath;
    pendingDeleteFileName = fileName || filePath.split('\\').pop() || 'Media File';

    if (deleteModalFileName) {
      deleteModalFileName.innerText = pendingDeleteFileName;
    }
    if (deleteConfirmModal) {
      deleteConfirmModal.style.display = "flex";
      if (window.lucide) lucide.createIcons();
    }
  };

  // Quick Open Downloads Folder button
  const btnOpenFolder = document.getElementById("btnOpenFolder");
  if (btnOpenFolder) {
    btnOpenFolder.addEventListener("click", () => {
      if (window.pywebview && window.pywebview.api) window.pywebview.api.open_save_folder();
    });
  }

  const btnOpenDownloadsFolder = document.getElementById("btnOpenDownloadsFolder");
  if (btnOpenDownloadsFolder) {
    btnOpenDownloadsFolder.addEventListener("click", () => {
      if (window.pywebview && window.pywebview.api) window.pywebview.api.open_save_folder();
    });
  }

  const btnGoToVault = document.getElementById("btnGoToVault");
  if (btnGoToVault) {
    btnGoToVault.addEventListener("click", () => switchTab("vault"));
  }

  // Toast Helper
  function showToast(msg) {
    const toast = document.createElement("div");
    toast.className = "floating-clipboard-toast";
    toast.style.bottom = "30px";
    toast.style.left = "50%";
    toast.style.transform = "translateX(-50%)";
    toast.innerHTML = `<div class="toast-info"><h4 style="color:#00E5FF;">${msg}</h4></div>`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2600);
  }

  // =========================================================================
  // SETTINGS & ACTIVATION MODALS
  // =========================================================================
  const modal = document.getElementById("activationModal");
  const btnCloseModal = document.getElementById("btnCloseModal");
  const btnDoneModal = document.getElementById("btnDoneModal");
  const btnManageSubscription = document.getElementById("btnManageSubscription");
  const viewActiveLicense = document.getElementById("viewActiveLicense");
  const viewActivationForm = document.getElementById("viewActivationForm");
  const btnSwitchToChangeKey = document.getElementById("btnSwitchToChangeKey");
  const btnBackToActiveView = document.getElementById("btnBackToActiveView");
  const backToActiveBox = document.getElementById("backToActiveBox");

  function showActiveLicenseView() {
    if (viewActiveLicense) viewActiveLicense.classList.add("active");
    if (viewActivationForm) viewActivationForm.classList.remove("active");
  }

  function showActivationFormView() {
    if (viewActiveLicense) viewActiveLicense.classList.remove("active");
    if (viewActivationForm) viewActivationForm.classList.add("active");
    if (backToActiveBox) backToActiveBox.style.display = isAppLicensed ? "block" : "none";
  }

  window.showActivationModalDirectly = function() {
    showActivationFormView();
    if (modal) modal.classList.add("active");
  };

  if (btnCloseModal) btnCloseModal.addEventListener("click", () => modal.classList.remove("active"));
  if (btnDoneModal) btnDoneModal.addEventListener("click", () => modal.classList.remove("active"));

  if (btnManageSubscription) {
    btnManageSubscription.addEventListener("click", (e) => {
      e.stopPropagation();
      if (isAppLicensed) showActiveLicenseView();
      else showActivationFormView();
      modal.classList.add("active");
    });
  }
  if (btnSwitchToChangeKey) btnSwitchToChangeKey.addEventListener("click", () => showActivationFormView());
  if (btnBackToActiveView) btnBackToActiveView.addEventListener("click", () => showActiveLicenseView());

  const btnCopyActiveHwid = document.getElementById("btnCopyActiveHwid");
  if (btnCopyActiveHwid) {
    btnCopyActiveHwid.addEventListener("click", () => {
      const hw = document.getElementById("modalActiveHwid").innerText;
      navigator.clipboard.writeText(hw);
      btnCopyActiveHwid.innerText = "✓ Copied";
      setTimeout(() => btnCopyActiveHwid.innerText = "Copy", 2000);
    });
  }

  const btnActivateLicense = document.getElementById("btnActivateLicense");
  if (btnActivateLicense) {
    btnActivateLicense.addEventListener("click", async () => {
      const k = document.getElementById("modalKeyInput").value.trim();
      if (!k) {
        document.getElementById("modalStatusMsg").innerText = "Please enter a valid License Key!";
        document.getElementById("modalStatusMsg").style.color = "#EF4444";
        return;
      }
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.activate_key(k);
        if (res.valid) {
          document.getElementById("modalStatusMsg").innerText = "✓ License Activated Successfully!";
          document.getElementById("modalStatusMsg").style.color = "#10B981";
          setTimeout(() => {
            modal.classList.remove("active");
            location.reload();
          }, 600);
        } else {
          document.getElementById("modalStatusMsg").innerText = res.message || "Invalid Key";
          document.getElementById("modalStatusMsg").style.color = "#EF4444";
        }
      }
    });
  }

  const btnContactAdmin = document.getElementById("btnContactAdmin");
  if (btnContactAdmin) {
    btnContactAdmin.addEventListener("click", () => window.open("https://t.me/SKD_ADMIN", "_blank"));
  }

  // System Settings Tab
  const btnBrowseFolder = document.getElementById("btnBrowseFolder");
  const settingSaveDir = document.getElementById("settingSaveDir");
  const settingSpeedLimit = document.getElementById("settingSpeedLimit");
  const settingCookies = document.getElementById("settingCookies");
  const btnSaveSettings = document.getElementById("btnSaveSettings");
  const settingGoogleSheetUrl = document.getElementById("settingGoogleSheetUrl");
  const btnTestGoogleSheet = document.getElementById("btnTestGoogleSheet");
  const googleSheetTestStatus = document.getElementById("googleSheetTestStatus");
  const btnOpenSheetGuide = document.getElementById("btnOpenSheetGuide");
  const sheetGuideModal = document.getElementById("sheetGuideModal");
  const btnCloseSheetGuideModal = document.getElementById("btnCloseSheetGuideModal");
  const btnDoneSheetGuide = document.getElementById("btnDoneSheetGuide");
  const btnCopySheetScript = document.getElementById("btnCopySheetScript");
  const lblCopySheetScript = document.getElementById("lblCopySheetScript");
  const codeSheetScript = document.getElementById("codeSheetScript");

  const googleAppsScriptCode = `// Google Apps Script Webhook for SKD Tool Telemetry
function doPost(e) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getActiveSheet();

    // Auto-setup headers if sheet is empty
    if (sheet.getLastRow() === 0) {
      sheet.appendRow([
        "Timestamp (កាលបរិច្ឆេទ)",
        "Device / License (ម៉ាស៊ីន/កូដ)",
        "Platform (វេទិកា)",
        "Video Title (ចំណងជើង)",
        "URL (តំណភ្ជាប់)",
        "Quality (កម្រិត)",
        "File Size (ទំហំ)",
        "Status (ស្ថានភាព)"
      ]);
      sheet.getRange(1, 1, 1, 8).setFontWeight("bold").setBackground("#0f172a").setFontColor("#38bdf8");
      sheet.setFrozenRows(1);
    }

    var data = {};
    if (e.postData && e.postData.contents) {
      try {
        data = JSON.parse(e.postData.contents);
      } catch (err) {
        data = e.parameter || {};
      }
    } else {
      data = e.parameter || {};
    }

    sheet.appendRow([
      data.timestamp || Utilities.formatDate(new Date(), "GMT+7", "yyyy-MM-dd HH:mm:ss"),
      data.device || "Unknown Device",
      data.platform || "Universal",
      data.title || "Media File",
      data.url || "",
      data.quality || "Default",
      data.size || "Unknown",
      data.status || "Completed"
    ]);

    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      message: "Data logged successfully"
    })).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}`;

  if (btnBrowseFolder) {
    btnBrowseFolder.addEventListener("click", async () => {
      if (window.pywebview && window.pywebview.api) {
        const folder = await window.pywebview.api.select_local_folder("Select Default Download Folder");
        if (folder && settingSaveDir) settingSaveDir.value = folder;
      }
    });
  }

  if (btnSaveSettings) {
    btnSaveSettings.addEventListener("click", async () => {
      const settingLanguage = document.getElementById("settingLanguage");
      const settingUpdateUrl = document.getElementById("settingUpdateUrl");
      const payload = {
        save_dir: settingSaveDir ? settingSaveDir.value : "",
        speed_limit: settingSpeedLimit ? settingSpeedLimit.value : "0",
        browser_cookies: settingCookies ? settingCookies.value : "none",
        sound_mode: settingSoundMode ? settingSoundMode.value : userSoundMode,
        sound_alert: isSoundAlertEnabled,
        update_feed_url: settingUpdateUrl ? settingUpdateUrl.value.trim() : "",
        google_sheet_webhook_url: settingGoogleSheetUrl ? settingGoogleSheetUrl.value.trim() : "",
        language: settingLanguage ? settingLanguage.value : currentLanguage
      };
      if (settingSoundMode) {
        userSoundMode = settingSoundMode.value;
        localStorage.setItem("skd_sound_mode", userSoundMode);
      }
      if (settingLanguage && settingLanguage.value !== currentLanguage) {
        applyLanguage(settingLanguage.value);
      }
      if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.save_settings(payload);
        showToast("✓ Settings & Preferences Saved!");
      }
    });
  }

  // Google Sheets Webhook Test Button
  if (btnTestGoogleSheet) {
    btnTestGoogleSheet.addEventListener("click", async () => {
      const url = settingGoogleSheetUrl ? settingGoogleSheetUrl.value.trim() : "";
      if (!url) {
        showToast("⚠️ សូមបញ្ចូល Webhook URL របស់ Google Sheet ជាមុនសិន!");
        if (googleSheetTestStatus) {
          googleSheetTestStatus.style.display = "block";
          googleSheetTestStatus.style.background = "rgba(239, 68, 68, 0.15)";
          googleSheetTestStatus.style.border = "1px solid rgba(239, 68, 68, 0.35)";
          googleSheetTestStatus.style.color = "#f87171";
          googleSheetTestStatus.innerHTML = "⚠️ សូមបញ្ចូល Webhook URL របស់ Google Sheet ជាមុនសិន!";
        }
        return;
      }

      // Also persist URL immediately
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.save_settings({ google_sheet_webhook_url: url });
      }

      btnTestGoogleSheet.disabled = true;
      btnTestGoogleSheet.innerHTML = `<i data-lucide="loader-2" class="spin"></i> <span>កំពុងតេស្ត...</span>`;
      if (window.lucide) lucide.createIcons();

      if (googleSheetTestStatus) {
        googleSheetTestStatus.style.display = "block";
        googleSheetTestStatus.style.background = "rgba(6, 182, 212, 0.15)";
        googleSheetTestStatus.style.border = "1px solid rgba(6, 182, 212, 0.35)";
        googleSheetTestStatus.style.color = "#38bdf8";
        googleSheetTestStatus.innerHTML = "កំពុងបញ្ជូនទិន្នន័យតេស្តទៅកាន់ Google Sheet...";
      }

      try {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.test_google_sheet_webhook) {
          const res = await window.pywebview.api.test_google_sheet_webhook(url);
          if (res && res.success) {
            if (googleSheetTestStatus) {
              googleSheetTestStatus.style.background = "rgba(16, 185, 129, 0.15)";
              googleSheetTestStatus.style.border = "1px solid rgba(16, 185, 129, 0.4)";
              googleSheetTestStatus.style.color = "#34d399";
              googleSheetTestStatus.innerHTML = `✅ <strong>ជោគជ័យ!</strong> ${res.message || "ទិន្នន័យបានរត់ចូល Google Sheet ភ្លាមៗ (Status 200 OK)!"}`;
            }
            showToast("✓ ភ្ជាប់ Google Sheet ជោគជ័យ!");
          } else {
            if (googleSheetTestStatus) {
              googleSheetTestStatus.style.background = "rgba(239, 68, 68, 0.15)";
              googleSheetTestStatus.style.border = "1px solid rgba(239, 68, 68, 0.4)";
              googleSheetTestStatus.style.color = "#f87171";
              googleSheetTestStatus.innerHTML = `❌ <strong>បរាជ័យ:</strong> ${res.error || "មិនអាចតភ្ជាប់ទៅកាន់ Webhook បានទេ"}`;
            }
            showToast("✕ ការតភ្ជាប់បរាជ័យ!");
          }
        }
      } catch (err) {
        if (googleSheetTestStatus) {
          googleSheetTestStatus.style.background = "rgba(239, 68, 68, 0.15)";
          googleSheetTestStatus.style.border = "1px solid rgba(239, 68, 68, 0.4)";
          googleSheetTestStatus.style.color = "#f87171";
          googleSheetTestStatus.innerHTML = `❌ កំហុស: ${err.message || err}`;
        }
      } finally {
        btnTestGoogleSheet.disabled = false;
        btnTestGoogleSheet.innerHTML = `<i data-lucide="zap"></i> <span>តេស្តភ្ជាប់ (Test)</span>`;
        if (window.lucide) lucide.createIcons();
      }
    });
  }

  // Google Sheets Guide Modal & Copy Script
  if (btnOpenSheetGuide) {
    btnOpenSheetGuide.addEventListener("click", () => {
      if (codeSheetScript) codeSheetScript.textContent = googleAppsScriptCode;
      if (sheetGuideModal) sheetGuideModal.style.display = "flex";
      if (window.lucide) lucide.createIcons();
    });
  }
  if (btnCloseSheetGuideModal) {
    btnCloseSheetGuideModal.addEventListener("click", () => {
      if (sheetGuideModal) sheetGuideModal.style.display = "none";
    });
  }
  if (btnDoneSheetGuide) {
    btnDoneSheetGuide.addEventListener("click", () => {
      if (sheetGuideModal) sheetGuideModal.style.display = "none";
    });
  }
  if (btnCopySheetScript) {
    btnCopySheetScript.addEventListener("click", async () => {
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(googleAppsScriptCode);
        } else if (window.pywebview && window.pywebview.api && window.pywebview.api.set_clipboard) {
          await window.pywebview.api.set_clipboard(googleAppsScriptCode);
        }
        if (lblCopySheetScript) lblCopySheetScript.innerText = "បានចម្លងរួចរាល់! ✓";
        showToast("✓ បានចម្លងកូដ Google Apps Script រួចរាល់!");
        setTimeout(() => {
          if (lblCopySheetScript) lblCopySheetScript.innerText = "ចម្លងកូដ (Copy Code)";
        }, 2500);
      } catch (err) {
        showToast("Error copying code: " + err);
      }
    });
  }

  // =========================================================================
  // REMOTE AUTO-UPDATER ENGINE & VERSION MANAGEMENT CONTROLLER
  // =========================================================================
  const updateModal = document.getElementById("updateModal");
  const btnCloseUpdateModal = document.getElementById("btnCloseUpdateModal");
  const btnApplyUpdate = document.getElementById("btnApplyUpdate");
  const btnLaterUpdate = document.getElementById("btnLaterUpdate");
  const btnCheckUpdateManual = document.getElementById("btnCheckUpdateManual");
  const btnTopBarUpdate = document.getElementById("btnTopBarUpdate");
  const topBarUpdateLabel = document.getElementById("topBarUpdateLabel");
  const settingCurrentVerText = document.getElementById("settingCurrentVerText");
  const settingUpdateUrl = document.getElementById("settingUpdateUrl");

  const updateModalTitle = document.getElementById("updateModalTitle");
  const updateReleaseDate = document.getElementById("updateReleaseDate");
  const updatePolicyTag = document.getElementById("updatePolicyTag");
  const lblCurrentVer = document.getElementById("lblCurrentVer");
  const lblLatestVer = document.getElementById("lblLatestVer");
  const updateChangelogList = document.getElementById("updateChangelogList");
  const updateProgressBox = document.getElementById("updateProgressBox");
  const updateProgStatus = document.getElementById("updateProgStatus");
  const updateProgPct = document.getElementById("updateProgPct");
  const updateProgBarFill = document.getElementById("updateProgBarFill");
  const updateProgSpeed = document.getElementById("updateProgSpeed");
  const updateActionsRow = document.getElementById("updateActionsRow");
  const lblBtnApplyUpdate = document.getElementById("lblBtnApplyUpdate");

  let currentUpdatePackage = null;
  let isUpdateDownloading = false;
  let downloadedNewExePath = null;

  function closeUpdateModal() {
    if (isUpdateDownloading) return; // Prevent closing while actively downloading update binary
    if (updateModal) updateModal.classList.remove("active");
  }

  if (btnCloseUpdateModal) btnCloseUpdateModal.addEventListener("click", closeUpdateModal);
  if (btnLaterUpdate) btnLaterUpdate.addEventListener("click", closeUpdateModal);

  function renderUpdateModal(updateData) {
    if (!updateModal || !updateData) return;
    currentUpdatePackage = updateData;

    if (updateModalTitle) {
      updateModalTitle.innerText = updateData.title || `SKD TOOL v${updateData.latest_version}`;
    }
    if (updateReleaseDate) {
      updateReleaseDate.innerText = `Released: ${updateData.release_date || 'Recently'}`;
    }
    if (lblCurrentVer) lblCurrentVer.innerText = `v${updateData.current_version}`;
    if (lblLatestVer) lblLatestVer.innerText = `v${updateData.latest_version}`;

    if (updatePolicyTag) {
      if (updateData.mandatory) {
        updatePolicyTag.innerText = "MANDATORY (FORCE UPDATE)";
        updatePolicyTag.style.background = "rgba(239, 68, 68, 0.25)";
        updatePolicyTag.style.borderColor = "#EF4444";
        updatePolicyTag.style.color = "#EF4444";
        if (btnCloseUpdateModal) btnCloseUpdateModal.style.display = "none";
        if (btnLaterUpdate) btnLaterUpdate.style.display = "none";
      } else {
        updatePolicyTag.innerText = "OPTIONAL";
        updatePolicyTag.style.background = "rgba(124, 92, 255, 0.25)";
        updatePolicyTag.style.borderColor = "rgba(124, 92, 255, 0.5)";
        updatePolicyTag.style.color = "#E2E8F0";
        if (btnCloseUpdateModal) btnCloseUpdateModal.style.display = "block";
        if (btnLaterUpdate) btnLaterUpdate.style.display = "block";
      }
    }

    if (updateChangelogList) {
      updateChangelogList.innerHTML = "";
      const changelog = updateData.changelog || ["Bug fixes and performance improvements."];
      changelog.forEach(item => {
        const row = document.createElement("div");
        row.className = "changelog-item";
        row.innerHTML = `<span class="changelog-bullet">✦</span><span>${item}</span>`;
        updateChangelogList.appendChild(row);
      });
    }

    // Reset progress UI
    if (updateProgressBox) updateProgressBox.style.display = "none";
    if (updateActionsRow) updateActionsRow.style.display = "flex";
    if (btnApplyUpdate) {
      btnApplyUpdate.disabled = false;
      btnApplyUpdate.innerHTML = `<i data-lucide="download-cloud"></i><span id="lblBtnApplyUpdate">UPDATE NOW</span>`;
    }
    if (window.lucide) lucide.createIcons();

    updateModal.classList.add("active");
  }

  async function checkAppUpdates(isManual = false) {
    if (!window.pywebview || !window.pywebview.api) return;
    try {
      if (isManual && btnCheckUpdateManual) {
        btnCheckUpdateManual.disabled = true;
        btnCheckUpdateManual.innerHTML = `<i data-lucide="loader-2" class="spin-icon"></i><span>Checking...</span>`;
        if (window.lucide) lucide.createIcons();
      }

      const res = await window.pywebview.api.check_for_updates();
      
      if (isManual && btnCheckUpdateManual) {
        btnCheckUpdateManual.disabled = false;
        btnCheckUpdateManual.innerHTML = `<i data-lucide="rotate-cw"></i><span>Check for Updates</span>`;
        if (window.lucide) lucide.createIcons();
      }

      if (res && res.has_update) {
        currentUpdatePackage = res;
        // Show Top Bar badge with glowing pulse
        if (btnTopBarUpdate) {
          btnTopBarUpdate.style.display = "inline-flex";
          const isKm = (typeof currentLanguage !== 'undefined' && currentLanguage === "km");
          if (topBarUpdateLabel) {
            topBarUpdateLabel.innerText = isKm 
              ? `v${res.latest_version} មានកំណែថ្មី` 
              : `v${res.latest_version} Update Available`;
          }
        }
        if (isManual) {
          renderUpdateModal(res);
        }
      } else {
        currentUpdatePackage = null;
        // Hide Top Bar badge completely if up to date or already updated
        if (btnTopBarUpdate) {
          btnTopBarUpdate.style.display = "none";
        }
        if (isManual) {
          if (res && res.error) {
            alert(`Update Check: ${res.error}`);
          } else {
            showToast("✓ Your SKD Tool is fully up to date! (Latest Version)");
          }
        }
      }
    } catch (err) {
      console.log("Check update error:", err);
      if (isManual) {
        if (btnCheckUpdateManual) {
          btnCheckUpdateManual.disabled = false;
          btnCheckUpdateManual.innerHTML = `<i data-lucide="rotate-cw"></i><span>Check for Updates</span>`;
          if (window.lucide) lucide.createIcons();
        }
        alert("Failed to reach update server: " + err);
      }
    }
  }

  if (btnCheckUpdateManual) {
    btnCheckUpdateManual.addEventListener("click", () => checkAppUpdates(true));
  }

  if (btnTopBarUpdate) {
    btnTopBarUpdate.addEventListener("click", () => {
      if (currentUpdatePackage) {
        renderUpdateModal(currentUpdatePackage);
      } else {
        checkAppUpdates(true);
      }
    });
  }

  // Trigger Download & Installation
  if (btnApplyUpdate) {
    btnApplyUpdate.addEventListener("click", async () => {
      if (!currentUpdatePackage || !currentUpdatePackage.download_url) {
        alert("Download URL not found for this update release.");
        return;
      }

      // If already downloaded, install immediately
      if (downloadedNewExePath) {
        if (window.pywebview && window.pywebview.api) {
          btnApplyUpdate.disabled = true;
          btnApplyUpdate.innerText = "Restarting & Applying Update...";
          window.pywebview.api.install_update_and_restart(downloadedNewExePath);
        }
        return;
      }

      isUpdateDownloading = true;
      if (btnCloseUpdateModal) btnCloseUpdateModal.style.display = "none";
      if (btnLaterUpdate) btnLaterUpdate.style.display = "none";
      btnApplyUpdate.disabled = true;

      if (updateProgressBox) updateProgressBox.style.display = "block";
      if (updateProgStatus) updateProgStatus.innerText = "Connecting to update server...";
      if (updateProgPct) updateProgPct.innerText = "0%";
      if (updateProgBarFill) updateProgBarFill.style.width = "0%";

      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.start_download_update(
          currentUpdatePackage.download_url,
          currentUpdatePackage.sha256 || ""
        );
      }
    });
  }

  // Live PyWebView Callbacks from Python
  window.onUpdateDownloadProgress = function(data) {
    if (!data) return;
    const pct = data.percent || 0;
    if (updateProgPct) updateProgPct.innerText = `${pct.toFixed(1)}%`;
    if (updateProgBarFill) updateProgBarFill.style.width = `${pct}%`;
    if (updateProgStatus) updateProgStatus.innerText = "Downloading new release binary...";
    
    if (updateProgSpeed) {
      let infoText = "";
      if (data.speed) {
        const speedMb = (data.speed / (1024 * 1024)).toFixed(2);
        infoText += `⚡ ${speedMb} MB/s`;
      }
      if (data.downloaded && data.total) {
        const dlMb = (data.downloaded / (1024 * 1024)).toFixed(1);
        const totMb = (data.total / (1024 * 1024)).toFixed(1);
        infoText += ` • ${dlMb} / ${totMb} MB`;
      } else if (currentUpdatePackage && currentUpdatePackage.file_size) {
        infoText += ` • Size: ${currentUpdatePackage.file_size}`;
      }
      if (data.eta !== undefined && data.eta > 0) {
        const mins = Math.floor(data.eta / 60);
        const secs = data.eta % 60;
        infoText += ` • ETA: ${mins > 0 ? mins + 'm ' : ''}${secs}s`;
      }
      updateProgSpeed.innerText = infoText;
    }
  };

  window.onUpdateDownloadComplete = function(res) {
    isUpdateDownloading = false;
    if (res && res.success && res.file_path) {
      downloadedNewExePath = res.file_path;
      if (updateProgStatus) updateProgStatus.innerText = "✓ Download Verified & Complete!";
      if (updateProgPct) updateProgPct.innerText = "100%";
      if (updateProgBarFill) updateProgBarFill.style.width = "100%";
      if (updateProgSpeed) updateProgSpeed.innerText = "Verified SHA-256 Checksum! Applying update...";

      if (btnTopBarUpdate) {
        btnTopBarUpdate.style.display = "none";
      }

      if (btnApplyUpdate) {
        btnApplyUpdate.disabled = true;
        btnApplyUpdate.innerHTML = `<i data-lucide="refresh-cw"></i><span>RESTARTING APPLICATION...</span>`;
        if (window.lucide) lucide.createIcons();
      }

      // Automatically apply update and restart smoothly
      setTimeout(() => {
        if (window.pywebview && window.pywebview.api && downloadedNewExePath) {
          window.pywebview.api.install_update_and_restart(downloadedNewExePath);
        }
      }, 1200);
    }
  };

  window.onUpdateDownloadError = function(errMsg) {
    isUpdateDownloading = false;
    if (updateProgStatus) updateProgStatus.innerText = "⚠️ Download Failed";
    if (updateProgSpeed) updateProgSpeed.innerText = String(errMsg);
    if (btnApplyUpdate) {
      btnApplyUpdate.disabled = false;
      btnApplyUpdate.innerHTML = `<i data-lucide="rotate-cw"></i><span>RETRY DOWNLOAD</span>`;
      if (window.lucide) lucide.createIcons();
    }
    if (btnCloseUpdateModal && (!currentUpdatePackage || !currentUpdatePackage.mandatory)) {
      btnCloseUpdateModal.style.display = "block";
    }
    if (btnLaterUpdate && (!currentUpdatePackage || !currentUpdatePackage.mandatory)) {
      btnLaterUpdate.style.display = "block";
    }
    alert(`Update Download Failed:\n\n${errMsg}`);
  };


  // =========================================================================
  // IN-APP MEDIA PLAYER & PREVIEW ENGINE
  // =========================================================================
  const inAppPlayerModal = document.getElementById("inAppPlayerModal");
  const inAppPlayerVideo = document.getElementById("inAppPlayerVideo");
  const inAppPlayerTitle = document.getElementById("inAppPlayerTitle");
  const inAppPlayerPath = document.getElementById("inAppPlayerPath");
  const inAppPlayerAudioVisualizer = document.getElementById("inAppPlayerAudioVisualizer");
  const btnClosePlayerModal = document.getElementById("btnClosePlayerModal");
  const btnPlayerOpenFolder = document.getElementById("btnPlayerOpenFolder");
  const btnPlayerOpenExternal = document.getElementById("btnPlayerOpenExternal");
  let currentPlayerFile = "";

  window.openInAppPlayer = function(filePath, title, posterUrl) {
    if (!filePath) return;
    currentPlayerFile = filePath;
    const displayName = title || filePath.split('\\').pop() || "Media File";
    if (inAppPlayerTitle) inAppPlayerTitle.innerText = displayName;
    if (inAppPlayerPath) inAppPlayerPath.innerText = filePath;

    const ext = filePath.toLowerCase().split('.').pop() || '';
    const isAudio = ['mp3', 'm4a', 'wav', 'flac', 'aac', 'ogg'].includes(ext);

    const normalizedPath = filePath.replace(/\\/g, '/');
    const fileUrl = normalizedPath.startsWith('/') ? `file://${normalizedPath}` : `file:///${normalizedPath}`;

    if (inAppPlayerVideo) {
      inAppPlayerVideo.src = fileUrl;
      if (posterUrl) inAppPlayerVideo.poster = posterUrl;
      else inAppPlayerVideo.removeAttribute('poster');

      if (isAudio) {
        if (inAppPlayerAudioVisualizer) inAppPlayerAudioVisualizer.style.display = "flex";
        inAppPlayerVideo.style.height = "54px";
      } else {
        if (inAppPlayerAudioVisualizer) inAppPlayerAudioVisualizer.style.display = "none";
        inAppPlayerVideo.style.height = "auto";
      }

      inAppPlayerVideo.load();
      inAppPlayerVideo.play().catch(e => console.log("Player playback notice:", e));
    }

    if (inAppPlayerModal) inAppPlayerModal.style.display = "flex";
  };

  function closeInAppPlayer() {
    if (inAppPlayerVideo) {
      inAppPlayerVideo.pause();
      inAppPlayerVideo.removeAttribute('src');
      inAppPlayerVideo.load();
    }
    if (inAppPlayerModal) inAppPlayerModal.style.display = "none";
  }

  if (btnClosePlayerModal) btnClosePlayerModal.addEventListener("click", closeInAppPlayer);
  if (inAppPlayerModal) {
    inAppPlayerModal.addEventListener("click", (e) => {
      if (e.target === inAppPlayerModal) closeInAppPlayer();
    });
  }

  if (btnPlayerOpenFolder) {
    btnPlayerOpenFolder.addEventListener("click", () => {
      if (window.pywebview && window.pywebview.api) window.pywebview.api.open_save_folder();
    });
  }
  if (btnPlayerOpenExternal) {
    btnPlayerOpenExternal.addEventListener("click", () => {
      if (currentPlayerFile && window.pywebview && window.pywebview.api) {
        window.pywebview.api.open_file(currentPlayerFile);
      }
    });
  }

  // =========================================================================
  // DUAL LANGUAGE LOCALIZATION (ភាសាខ្មែរ 🇰🇭 / English 🇺🇸)
  // =========================================================================
  let allTranslations = {};

  function applyLanguage(lang) {
    currentLanguage = lang;
    const isKm = (lang === "km");

    const langToggleLabel = document.getElementById("langToggleLabel");
    if (langToggleLabel) {
      langToggleLabel.innerText = isKm ? "🇰🇭 ភាសាខ្មែរ" : "🇺🇸 English";
    }
    const settingLanguage = document.getElementById("settingLanguage");
    if (settingLanguage) settingLanguage.value = lang;

    // Sidebar items
    const sidebarItems = {
      sidebarBtnInstant: isKm ? "ទាញយកភ្លាមៗ" : "Instant Download",
      sidebarBtnQueue: isKm ? "តម្រង់ជួរទាញយក" : "Download Queue",
      sidebarBtnBatch: isKm ? "ទាញយកជាបាច់ & Playlist" : "Batch & Playlist",
      sidebarBtnConverter: isKm ? "បំលែងវីដេអូ" : "Video Converter",
      sidebarBtnScheduler: isKm ? "កំណត់ម៉ោង" : "Scheduler",
      sidebarBtnVault: isKm ? "ឃ្លាំងផ្ទុក Media" : "Media Vault",
      sidebarBtnSettings: isKm ? "ការកំណត់" : "Settings"
    };
    for (const [id, txt] of Object.entries(sidebarItems)) {
      const el = document.getElementById(id);
      if (el) {
        const span = el.querySelector("span:not(.nav-counter-badge)");
        if (span) span.innerText = txt;
      }
    }

    // Workspace titles
    workspaceTitles.instant = isKm ? "ផ្ទាំងទាញយកភ្លាមៗ (INSTANT WORKSPACE)" : "INSTANT DOWNLOADER WORKSPACE";
    workspaceTitles.queue = isKm ? "ផ្ទាំងគ្រប់គ្រងតម្រង់ជួរ (QUEUE DASHBOARD)" : "DOWNLOAD QUEUE DASHBOARD";
    workspaceTitles.batch = isKm ? "ផ្ទាំងទាញយកជាបាច់ & PLAYLIST" : "BATCH & PLAYLIST WORKSPACE";
    workspaceTitles.converter = isKm ? "ស្ទូឌីយោបំលែងវីដេអូ & សំឡេង (STUDIO)" : "MEDIA CONVERTER & AUDIO EXTRACTOR";
    workspaceTitles.scheduler = isKm ? "ផ្ទាំងកំណត់ម៉ោងទាញយក & ស្វ័យប្រវត្តិ" : "DOWNLOAD SCHEDULER & AUTOMATION";
    workspaceTitles.vault = isKm ? "ឃ្លាំងផ្ទុកឯកសារ & ស្ថិតិ (MEDIA VAULT)" : "MEDIA VAULT & ARCHIVE";
    workspaceTitles.settings = isKm ? "ការកំណត់ប្រព័ន្ធ & សុវត្ថិភាព" : "SYSTEM SETTINGS & PREFERENCES";

    const titleEl = document.getElementById("currentWorkspaceTitle");
    if (titleEl && workspaceTitles[activeTab]) {
      titleEl.innerText = workspaceTitles[activeTab];
    }

    // Hero & Input
    const btnDownloadNow = document.getElementById("btnDownloadNow");
    if (btnDownloadNow) {
      const span = btnDownloadNow.querySelector("span");
      if (span) span.innerText = isKm ? "ទាញយកឥឡូវនេះ" : "DOWNLOAD NOW";
    }
    const smartBtnDlText = document.getElementById("smartBtnDlText");
    if (smartBtnDlText) {
      smartBtnDlText.innerText = isKm ? "ទាញយកឥឡូវនេះ" : "Download Now";
    }
    const smartBtnQueueText = document.getElementById("smartBtnQueueText");
    if (smartBtnQueueText) {
      smartBtnQueueText.innerText = isKm ? "+ បន្ថែមក្នុងជួរ" : "+ Add to Queue";
    }
    const smartBtnCoverText = document.getElementById("smartBtnCoverText");
    if (smartBtnCoverText) {
      smartBtnCoverText.innerText = isKm ? "រូបភាព HD" : "HD Cover";
    }
    if (topBarUpdateLabel && currentUpdatePackage && currentUpdatePackage.latest_version) {
      topBarUpdateLabel.innerText = isKm 
        ? `v${currentUpdatePackage.latest_version} មានកំណែថ្មី` 
        : `v${currentUpdatePackage.latest_version} Update Available`;
    }
    const btnPaste = document.getElementById("btnPaste");
    if (btnPaste) {
      const span = btnPaste.querySelector("span");
      if (span) span.innerText = isKm ? "បិទភ្ជាប់" : "Paste";
    }
    const urlInput = document.getElementById("urlInput");
    if (urlInput) {
      urlInput.placeholder = isKm 
        ? "Paste Link ទីនេះ (YouTube, TikTok, Facebook, Instagram, Twitter/X, Douyin, MP4, MP3...)" 
        : "Paste link here (YouTube, TikTok, Facebook, Instagram, Twitter/X, Douyin, MP4, MP3...)";
    }
    const topBtnFolderLabel = document.getElementById("topBtnFolderLabel");
    if (topBtnFolderLabel) {
      topBtnFolderLabel.innerText = isKm ? "បើក Folder" : "Folder";
    }

    // Context Menu labels
    const ctxLblPaste = document.getElementById("ctxLblPaste");
    if (ctxLblPaste) ctxLblPaste.innerText = isKm ? "បិទភ្ជាប់" : "Paste";
    const ctxLblCopy = document.getElementById("ctxLblCopy");
    if (ctxLblCopy) ctxLblCopy.innerText = isKm ? "ចម្លង" : "Copy";
    const ctxLblCut = document.getElementById("ctxLblCut");
    if (ctxLblCut) ctxLblCut.innerText = isKm ? "កាត់" : "Cut";
    const ctxLblSelectAll = document.getElementById("ctxLblSelectAll");
    if (ctxLblSelectAll) ctxLblSelectAll.innerText = isKm ? "ជ្រើសរើសទាំងអស់" : "Select All";
    const ctxLblClear = document.getElementById("ctxLblClear");
    if (ctxLblClear) ctxLblClear.innerText = isKm ? "សម្អាត" : "Clear";

    // Converter
    const btnStartConversion = document.getElementById("btnStartConversion");
    if (btnStartConversion) {
      const span = btnStartConversion.querySelector("span");
      if (span) span.innerText = isKm ? "ចាប់ផ្តើមបំលែង" : "START CONVERSION";
    }

    const lblPastePrompt = document.getElementById("lblPastePrompt");
    if (lblPastePrompt) {
      lblPastePrompt.innerText = isKm ? "ដាក់ LINK វីដេអូ ឬចម្រៀងរបស់អ្នក" : "PASTE YOUR MEDIA LINK";
    }

    // Presets
    const pAuto = document.getElementById("presetCardAuto");
    if (pAuto && pAuto.querySelector(".quality-card-sub")) {
      pAuto.querySelector(".quality-card-sub").innerText = isKm ? "ជ្រើសរើសគុណភាពល្អបំផុតស្វ័យប្រវត្តិ" : "Auto Best Resolution";
    }
    const p4k = document.getElementById("presetCard4k");
    if (p4k && p4k.querySelector(".quality-card-sub")) {
      p4k.querySelector(".quality-card-sub").innerText = isKm ? "កម្រិតខ្ពស់បំផុត (UHD)" : "Ultra High Definition";
    }
    const p1080 = document.getElementById("presetCard1080p");
    if (p1080 && p1080.querySelector(".quality-card-sub")) {
      p1080.querySelector(".quality-card-sub").innerText = isKm ? "កម្រិតច្បាស់ពេញលេញ (ណែនាំដោយ SKD AI ✨)" : "Standard 60fps • Crystal Clear";
    }
    const p720 = document.getElementById("presetCard720p");
    if (p720 && p720.querySelector(".quality-card-sub")) {
      p720.querySelector(".quality-card-sub").innerText = isKm ? "ទាញយកលឿន សន្សំទំហំ" : "Lightweight & High-Speed";
    }
    const pMp3 = document.getElementById("presetCardMp3");
    if (pMp3 && pMp3.querySelector(".quality-card-sub")) {
      pMp3.querySelector(".quality-card-sub").innerText = isKm ? "សំឡេងច្បាស់កម្រិត Studio" : "Studio Master Audio";
    }
  }

  const btnLangToggle = document.getElementById("btnLangToggle");
  if (btnLangToggle) {
    btnLangToggle.addEventListener("click", () => {
      const nextLang = (currentLanguage === "km") ? "en" : "km";
      applyLanguage(nextLang);
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.set_language(nextLang);
      }
      showToast(nextLang === "km" ? "🇰🇭 បានប្តូរទៅភាសាខ្មែរ" : "🇺🇸 Switched to English");
    });
  }

  const topBtnFolder = document.getElementById("topBtnFolder");
  if (topBtnFolder) {
    topBtnFolder.addEventListener("click", () => {
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.open_save_folder();
      }
    });
  }

  const settingLanguage = document.getElementById("settingLanguage");
  if (settingLanguage) {
    settingLanguage.addEventListener("change", () => {
      const nextLang = settingLanguage.value;
      applyLanguage(nextLang);
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.set_language(nextLang);
      }
    });
  }

  // Initialize PyWebView Ready
  window.addEventListener('pywebviewready', async () => {
    console.log("PyWebView bridge ready with upgraded modules!");
    const info = await window.pywebview.api.get_app_info();
    if (info) {
      isAppLicensed = !!info.is_licensed;
      if (info.translations) allTranslations = info.translations;
      if (info.language) {
        currentLanguage = info.language;
        applyLanguage(currentLanguage);
      } else {
        applyLanguage("km");
      }

      if (document.getElementById("modalHwid")) document.getElementById("modalHwid").value = info.hwid || "";
      if (document.getElementById("modalActiveHwid")) document.getElementById("modalActiveHwid").innerText = info.hwid || "";
      if (document.getElementById("modalActiveKey")) document.getElementById("modalActiveKey").innerText = info.license_key || "SKD-VIP-ACTIVE";
      if (document.getElementById("modalActivePlan")) document.getElementById("modalActivePlan").innerText = info.license_plan || "Lifetime VIP";
      if (document.getElementById("modalActiveDays")) document.getElementById("modalActiveDays").innerText = info.license_remaining || "28 Days Remaining";
      if (document.getElementById("licenseStatusDays")) document.getElementById("licenseStatusDays").innerText = info.license_remaining || "28 Days Remaining";
      if (settingSaveDir) settingSaveDir.value = info.save_dir || "";
      if (settingSpeedLimit) settingSpeedLimit.value = info.speed_limit || "";
      if (settingCookies) settingCookies.value = info.browser_cookies || "none";
      if (settingSoundMode && info.sound_mode) {
        settingSoundMode.value = info.sound_mode;
        userSoundMode = info.sound_mode;
      } else if (settingSoundMode) {
        settingSoundMode.value = userSoundMode;
      }
      if (info.app_version) {
        if (settingCurrentVerText) settingCurrentVerText.innerText = `Version ${info.app_version} (Official Stable)`;
        if (lblCurrentVer) lblCurrentVer.innerText = `v${info.app_version}`;
      }
      if (settingUpdateUrl && info.update_feed_url) {
        settingUpdateUrl.value = info.update_feed_url;
      }
      if (settingGoogleSheetUrl && info.google_sheet_webhook_url) {
        settingGoogleSheetUrl.value = info.google_sheet_webhook_url;
      }

      isAppLicensed = true;
      showActiveLicenseView();
    }

    loadRecentDownloads();
    loadVaultData();
    loadQueueItems();
    loadSchedulerData();

    // Auto-check for remote software updates after launch
    setTimeout(() => {
      checkAppUpdates(false);
    }, 1200);
  });

});
