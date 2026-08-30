(function () {
  "use strict";

  const state = {
    sport: "all",
    status: "all",
    query: "",
    results: [],
    hls: null,
    dash: null,
    mpegts: null,
    currentResolved: null,
    searchController: null,
    searchEpoch: 0,
  };

  const labels = {
    all: "全部体育",
    football: "足球",
    basketball: "篮球",
    f1: "F1",
    nfl: "橄榄球",
  };
  const statusLabels = { live: "直播中", upcoming: "即将开始", replay: "回放", unknown: "待确认" };

  const form = document.getElementById("searchForm");
  const input = document.getElementById("searchInput");
  const grid = document.getElementById("resultsGrid");
  const notice = document.getElementById("notice");
  const empty = document.getElementById("emptyState");
  const title = document.getElementById("resultsTitle");
  const dialog = document.getElementById("playerDialog");
  const video = document.getElementById("videoPlayer");
  const embed = document.getElementById("embedPlayer");
  const loading = document.getElementById("playerLoading");
  const playerTitle = document.getElementById("playerTitle");
  const playerProvider = document.getElementById("playerProvider");
  const playerMessage = document.getElementById("playerMessage");
  const copyButton = document.getElementById("copyUrl");
  const openSource = document.getElementById("openSource");
  const deepMode = document.getElementById("deepMode");

  async function request(url, options) {
    const response = await fetch(url, options);
    let payload;
    try { payload = await response.json(); } catch (_) { payload = {}; }
    if (!response.ok) throw new Error(payload.error || `请求失败 (${response.status})`);
    return payload;
  }

  function identifiedEmbedUrl(rawUrl) {
    const url = new URL(rawUrl);
    if (url.hostname === "www.youtube-nocookie.com" || url.hostname === "www.youtube.com") {
      url.searchParams.set("origin", window.location.origin);
    }
    return url.toString();
  }

  function proxiedMediaUrl(rawUrl, referer) {
    if (!/^https?:\/\//i.test(rawUrl)) return rawUrl;
    const localProxy = `${window.location.origin}/api/proxy`;
    if (rawUrl.startsWith(localProxy)) return rawUrl;
    const params = new URLSearchParams({ url: rawUrl });
    if (referer) params.set("referer", referer);
    return `/api/proxy?${params}`;
  }

  function showSkeletons() {
    empty.hidden = true;
    grid.replaceChildren();
    for (let i = 0; i < 6; i += 1) {
      const card = document.createElement("article");
      card.className = "stream-card skeleton";
      card.innerHTML = '<div class="card-media"></div><div class="card-body"><div class="skeleton-line short"></div><div class="skeleton-line"></div><div class="skeleton-line"></div></div>';
      grid.appendChild(card);
    }
  }

  async function search() {
    state.searchEpoch += 1;
    const epoch = state.searchEpoch;
    if (state.searchController) state.searchController.abort();
    state.searchController = new AbortController();
    state.query = input.value.trim();
    showSkeletons();
    notice.className = "notice";
    const deep = deepMode.checked;
    notice.textContent = deep ? `深度搜索${labels[state.sport]}：多引擎并行检索中…` : `正在快速搜索${labels[state.sport]}…`;
    const params = new URLSearchParams({ q: state.query, sport: state.sport, limit: deep ? "36" : "18", deep: deep ? "1" : "0" });
    try {
      const payload = await request(`/api/search?${params}`, { signal: state.searchController.signal });
      if (epoch !== state.searchEpoch) return;
      state.results = payload.results || [];
      const sourceCount = new Set(state.results.map((item) => item.provider)).size;
      const officialOnly = state.results.length > 0 && state.results.every((item) => item.source_type === "official-channel");
      const directoryOnly = state.results.length > 0 && state.results.every((item) => ["official-channel", "platform-search"].includes(item.source_type));
      notice.textContent = officialOnly
        ? `已提供 ${state.results.length} 个央视官方体育频道 · 点击后在官方播放器观看`
        : directoryOnly
          ? `已提供 ${state.results.length} 个直播平台搜索入口 · 点击后在对应平台查找当前直播间`
          : `找到 ${state.results.length} 个结果 · ${sourceCount} 个来源 · 播放前执行${deep ? "深度" : "快速"}解析`;
      renderResults();
    } catch (error) {
      if (error.name === "AbortError" || epoch !== state.searchEpoch) return;
      state.results = [];
      notice.className = "notice error";
      notice.textContent = error.message;
      renderResults();
    }
  }

  function renderResults() {
    const filtered = state.status === "all"
      ? state.results
      : state.results.filter((item) => item.live_status === state.status);
    grid.replaceChildren();
    empty.hidden = filtered.length !== 0;
    for (const item of filtered) grid.appendChild(createCard(item));
  }

  function createCard(item) {
    const isOfficial = item.source_type === "official-channel";
    const isPlatformSearch = item.source_type === "platform-search";
    const isExternalLink = isOfficial || isPlatformSearch;
    const card = document.createElement(isExternalLink ? "a" : "article");
    card.className = item.source_type === "official-channel" ? "stream-card official-channel" : "stream-card";
    card.setAttribute("aria-label", isExternalLink ? `打开 ${item.title}` : `播放 ${item.title}`);
    if (isExternalLink) {
      card.href = item.url;
      card.target = "_blank";
      card.rel = "noopener noreferrer";
    } else {
      card.tabIndex = 0;
      card.setAttribute("role", "button");
    }

    const media = document.createElement("div");
    media.className = "card-media";
    if (item.thumbnail) {
      const image = document.createElement("img");
      image.src = item.thumbnail;
      image.alt = "";
      image.loading = "lazy";
      image.referrerPolicy = "no-referrer";
      image.addEventListener("error", () => image.remove());
      media.appendChild(image);
    } else if (item.source_type === "official-channel") {
      const logo = document.createElement("strong");
      logo.className = "channel-logo";
      logo.textContent = item.title.startsWith("CCTV-5+") ? "CCTV 5+" : "CCTV 5";
      media.appendChild(logo);
    }
    const badge = document.createElement("span");
    badge.className = `status-badge ${item.live_status}`;
    badge.textContent = statusLabels[item.live_status] || statusLabels.unknown;
    const play = document.createElement("span");
    play.className = "play-button";
    play.textContent = isExternalLink ? "↗" : "▶";
    media.append(badge, play);

    const body = document.createElement("div");
    body.className = "card-body";
    const overline = document.createElement("div");
    overline.className = "card-overline";
    const sport = document.createElement("span");
    sport.className = "sport";
    sport.textContent = labels[item.sport] || labels.all;
    const provider = document.createElement("span");
    provider.textContent = item.provider;
    overline.append(sport, provider);
    const heading = document.createElement("h3");
    heading.className = "card-title";
    heading.textContent = item.title;
    const channel = document.createElement("p");
    channel.className = "card-channel";
    channel.textContent = item.channel || item.description || "待解析的直播页面";
    body.append(overline, heading, channel);
    card.append(media, body);
    if (!isExternalLink) {
      card.addEventListener("click", () => playResult(item));
      card.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          playResult(item);
        }
      });
    }
    return card;
  }

  function resetPlayer() {
    if (state.hls) {
      state.hls.destroy();
      state.hls = null;
    }
    if (state.dash) {
      state.dash.destroy();
      state.dash = null;
    }
    if (state.mpegts) {
      state.mpegts.destroy();
      state.mpegts = null;
    }
    video.pause();
    video.removeAttribute("src");
    video.load();
    embed.src = "about:blank";
    video.style.display = "none";
    embed.style.display = "none";
    loading.style.display = "grid";
    const spinner = document.createElement("span");
    const loadingText = document.createElement("p");
    loadingText.textContent = "正在解析直播源…";
    loading.replaceChildren(spinner, loadingText);
    copyButton.disabled = true;
    state.currentResolved = null;
  }

  async function playResult(item) {
    resetPlayer();
    playerTitle.textContent = item.title;
    playerProvider.textContent = item.provider.toUpperCase();
    playerMessage.textContent = "正在识别最佳播放方式";
    openSource.href = item.url;
    if (!dialog.open) dialog.showModal();
    try {
      const resolved = await request("/api/resolve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: item.url, deep: deepMode.checked }),
      });
      state.currentResolved = resolved;
      copyButton.disabled = resolved.kind === "embed";
      loading.style.display = "none";
      if (resolved.kind === "embed") {
        embed.style.display = "block";
        embed.src = identifiedEmbedUrl(resolved.playback_url);
        playerMessage.textContent = "使用平台官方嵌入播放器";
        return;
      }
      if (resolved.kind === "external") {
        const message = document.createElement("p");
        message.textContent = "该频道由央视官方播放器提供。请点击下方“打开原页面”观看；地区或赛事版权限制仍由央视决定。";
        loading.replaceChildren(message);
        loading.style.display = "grid";
        playerMessage.textContent = "央视官方播放 · 不抓取或代理受限频道信号";
        return;
      }
      video.style.display = "block";
      const path = Array.isArray(resolved.diagnostics) ? resolved.diagnostics.slice(-2).join(" → ") : "";
      playerMessage.textContent = `${resolved.engine} · ${path || "浏览器播放"}`;
      if (resolved.kind === "hls" && window.Hls && window.Hls.isSupported()) {
        state.hls = new window.Hls({ enableWorker: true, lowLatencyMode: true, backBufferLength: 30 });
        state.hls.loadSource(resolved.proxy_url);
        state.hls.attachMedia(video);
        state.hls.on(window.Hls.Events.MANIFEST_PARSED, () => video.play().catch(() => {}));
        state.hls.on(window.Hls.Events.ERROR, (_, data) => {
          if (data.fatal) playerMessage.textContent = `播放失败：${data.details || "媒体流不可用"}`;
        });
      } else if (resolved.kind === "dash" && window.dashjs) {
        const player = window.dashjs.MediaPlayer().create();
        player.extend("RequestModifier", () => ({
          modifyRequestURL: (url) => proxiedMediaUrl(url, resolved.referer || resolved.source_url),
          modifyRequestHeader: (xhr) => xhr,
        }), true);
        player.on(window.dashjs.MediaPlayer.events.ERROR, (event) => {
          const detail = event && event.error ? event.error.message || event.error.code : "媒体流不可用";
          playerMessage.textContent = `DASH 播放失败：${detail}`;
        });
        player.initialize(video, resolved.playback_url, true);
        state.dash = player;
      } else if (resolved.kind === "flv" && window.mpegts && window.mpegts.isSupported()) {
        state.mpegts = window.mpegts.createPlayer({ type: "flv", isLive: true, url: resolved.proxy_url }, { enableWorker: true, liveBufferLatencyChasing: true });
        state.mpegts.attachMediaElement(video);
        state.mpegts.load();
        state.mpegts.play().catch(() => {});
      } else {
        video.src = resolved.proxy_url;
        video.play().catch(() => {});
      }
    } catch (error) {
      const message = document.createElement("p");
      message.textContent = error.message;
      loading.replaceChildren(message);
      playerMessage.textContent = "无法播放此直播";
    }
  }

  function closePlayer() {
    resetPlayer();
    dialog.close();
  }

  form.addEventListener("submit", (event) => { event.preventDefault(); search(); });
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".nav-item").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      state.sport = button.dataset.sport;
      title.textContent = state.sport === "all" ? "正在直播" : `${labels[state.sport]}直播`;
      search();
    });
  });
  document.querySelectorAll(".filter").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".filter").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      state.status = button.dataset.status;
      renderResults();
    });
  });
  document.getElementById("closePlayer").addEventListener("click", closePlayer);
  dialog.addEventListener("click", (event) => { if (event.target === dialog) closePlayer(); });
  dialog.addEventListener("cancel", (event) => { event.preventDefault(); closePlayer(); });
  copyButton.addEventListener("click", async () => {
    if (!state.currentResolved || !state.currentResolved.playback_url) return;
    try {
      await navigator.clipboard.writeText(state.currentResolved.playback_url);
      copyButton.textContent = "已复制";
      setTimeout(() => { copyButton.textContent = "复制媒体地址"; }, 1400);
    } catch (_) {
      copyButton.textContent = "复制失败";
    }
  });

  search();
})();
