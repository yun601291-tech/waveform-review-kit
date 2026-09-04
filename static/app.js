"use strict";

const ui = {};
const state = {
  manifest: null,
  sectionId: "",
  visible: [],
  currentId: "",
  pageIndex: 0,
  reviews: {},
  storageKey: ""
};

const byId = id => document.getElementById(id);
const escapeCsv = value => {
  const valueText = value == null ? "" : String(value);
  return /[",\r\n]/.test(valueText) ? '"' + valueText.replaceAll('"', '""') + '"' : valueText;
};
const nowIso = () => new Date().toISOString();

function toast(message) {
  ui.toast.textContent = message;
  ui.toast.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => ui.toast.classList.remove("show"), 2200);
}

function storageLoad() {
  try {
    const parsed = JSON.parse(localStorage.getItem(state.storageKey) || "{}");
    state.reviews = parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    state.reviews = {};
  }
}

function storageSave() {
  localStorage.setItem(state.storageKey, JSON.stringify(state.reviews));
}

function sectionById(id) {
  return state.manifest.sections.find(section => section.id === id);
}

function currentItem() {
  return state.visible.find(item => item.id === state.currentId) || null;
}

function isReviewable(item) {
  const section = sectionById(item.section);
  return section ? section.reviewable !== false : true;
}

function normalizeManifest(raw) {
  const manifest = structuredClone(raw);
  manifest.project_id ||= "waveform-review";
  manifest.title ||= "Waveform Review Kit";
  manifest.description ||= "";
  manifest.sections = Array.isArray(manifest.sections) && manifest.sections.length
    ? manifest.sections
    : [{ id: "review", label: "待复核", reviewable: true }];
  manifest.labels = Array.isArray(manifest.labels) ? manifest.labels : [];
  manifest.items = Array.isArray(manifest.items) ? manifest.items : [];
  const validSections = new Set(manifest.sections.map(section => section.id));
  manifest.items = manifest.items.map((item, index) => {
    const fallbackId = "item-" + (index + 1);
    return {
      id: String(item.id ?? fallbackId),
      section: validSections.has(item.section) ? item.section : manifest.sections[0].id,
      title: item.title || String(item.id ?? fallbackId),
      subtitle: item.subtitle || "",
      tags: Array.isArray(item.tags) ? item.tags.map(String) : [],
      metadata: item.metadata && typeof item.metadata === "object" ? item.metadata : {},
      pages: Array.isArray(item.pages) ? item.pages : []
    };
  }).filter(item => item.pages.length > 0);
  return manifest;
}

function renderHeader() {
  document.title = state.manifest.title + " · Waveform Review Kit";
  ui.projectTitle.textContent = state.manifest.title;
  ui.projectDescription.textContent = state.manifest.description;
  const shortcuts = state.manifest.labels
    .filter(label => label.shortcut)
    .map(label => label.shortcut + "=" + label.name)
    .join("，");
  ui.shortcutHelp.textContent = "快捷键：←/→切换数据，[/]切换波形页"
    + (shortcuts ? "，" + shortcuts : "") + "，0=清除判定";
}

function renderTabs() {
  ui.sectionTabs.replaceChildren();
  for (const section of state.manifest.sections) {
    const count = state.manifest.items.filter(item => item.section === section.id).length;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "tab" + (section.id === state.sectionId ? " active" : "");
    button.textContent = section.label + " " + count;
    button.title = section.description || "";
    button.addEventListener("click", () => {
      state.sectionId = section.id;
      state.currentId = "";
      state.pageIndex = 0;
      populateTagFilter();
      applyFilters();
      renderTabs();
    });
    ui.sectionTabs.appendChild(button);
  }
}

function populateTagFilter() {
  const previous = ui.tagFilter.value;
  const tags = [...new Set(
    state.manifest.items
      .filter(item => item.section === state.sectionId)
      .flatMap(item => item.tags)
  )].sort((a, b) => a.localeCompare(b, "zh-CN"));
  ui.tagFilter.replaceChildren(new Option("全部标签", "all"));
  for (const tag of tags) ui.tagFilter.add(new Option(tag, tag));
  ui.tagFilter.value = tags.includes(previous) ? previous : "all";
}

function decisionName(code) {
  return state.manifest.labels.find(label => label.code === code)?.name || code || "未复核";
}

function applyFilters() {
  const search = ui.searchInput.value.trim().toLocaleLowerCase();
  const decisionFilter = ui.decisionFilter.value;
  const tag = ui.tagFilter.value;
  const sectionItems = state.manifest.items.filter(item => item.section === state.sectionId);

  state.visible = sectionItems.filter(item => {
    const review = state.reviews[item.id];
    const haystack = [
      item.id,
      item.title,
      item.subtitle,
      ...item.tags,
      ...Object.entries(item.metadata).flat()
    ].join(" ").toLocaleLowerCase();
    if (search && !haystack.includes(search)) return false;
    if (tag !== "all" && !item.tags.includes(tag)) return false;
    if (isReviewable(item)) {
      if (decisionFilter === "unreviewed" && review?.decision) return false;
      if (decisionFilter === "reviewed" && !review?.decision) return false;
      if (!["all", "unreviewed", "reviewed"].includes(decisionFilter)
          && review?.decision !== decisionFilter) return false;
    }
    return true;
  });

  if (!state.visible.some(item => item.id === state.currentId)) {
    state.currentId = state.visible[0]?.id || "";
    state.pageIndex = 0;
  }
  renderItemList();
  renderProgress();
  renderCurrent();
}

function renderItemList() {
  ui.itemSelect.replaceChildren();
  for (const item of state.visible) {
    const review = state.reviews[item.id];
    const prefix = review?.decision ? "●" : "○";
    const option = new Option(prefix + " " + item.title, item.id);
    option.title = review?.decision ? decisionName(review.decision) : "未复核";
    ui.itemSelect.add(option);
  }
  ui.itemSelect.value = state.currentId;
  ui.visibleCount.textContent = state.visible.length + " 条可见";
}

function renderProgress() {
  const reviewable = state.manifest.items.filter(isReviewable);
  const reviewed = reviewable.filter(item => state.reviews[item.id]?.decision).length;
  const percent = reviewable.length ? reviewed / reviewable.length * 100 : 0;
  ui.progressText.textContent = reviewed + " / " + reviewable.length + " 已复核";
  ui.progressBar.style.width = percent + "%";
}

function renderMetadata(item) {
  ui.metadata.replaceChildren();
  const entries = Object.entries(item.metadata);
  ui.metadata.hidden = entries.length === 0;
  for (const [label, value] of entries) {
    const box = document.createElement("div");
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = label;
    dd.textContent = value == null ? "" : String(value);
    box.append(dt, dd);
    ui.metadata.appendChild(box);
  }
}

function renderTags(item) {
  ui.itemTags.replaceChildren();
  for (const tag of item.tags) {
    const span = document.createElement("span");
    span.className = "tag";
    span.textContent = tag;
    ui.itemTags.appendChild(span);
  }
}

function renderDecision(item) {
  const reviewable = isReviewable(item);
  ui.decisionPanel.hidden = !reviewable;
  ui.referenceNotice.hidden = reviewable;
  if (!reviewable) return;

  const review = state.reviews[item.id] || {};
  ui.decisionButtons.replaceChildren();
  for (const label of state.manifest.labels) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "decision-button" + (review.decision === label.code ? " selected" : "");
    button.style.setProperty("--decision-color", label.color || "#174d78");
    button.textContent = (label.shortcut ? label.shortcut + "  " : "") + label.name;
    button.addEventListener("click", () => setDecision(item.id, label.code));
    ui.decisionButtons.appendChild(button);
  }
  ui.noteInput.value = review.note || "";
}

function renderCurrent() {
  const item = currentItem();
  const hasItem = Boolean(item);
  ui.emptyState.hidden = hasItem;
  ui.viewer.hidden = !hasItem;
  if (!item) return;

  const index = state.visible.findIndex(candidate => candidate.id === item.id);
  ui.counter.textContent = (index + 1) + " / " + state.visible.length;
  ui.itemTitle.textContent = item.title;
  ui.itemSubtitle.textContent = item.subtitle;
  renderTags(item);
  renderMetadata(item);

  state.pageIndex = Math.max(0, Math.min(state.pageIndex, item.pages.length - 1));
  ui.pageSelect.replaceChildren();
  item.pages.forEach((page, indexValue) => {
    ui.pageSelect.add(new Option(page.label || "第 " + (indexValue + 1) + " 页", String(indexValue)));
  });
  ui.pageSelect.value = String(state.pageIndex);
  ui.pageSelect.disabled = item.pages.length === 1;
  const page = item.pages[state.pageIndex];
  const src = page.image.startsWith("/") ? page.image : "/assets/" + page.image;
  ui.waveformImage.src = src;
  ui.waveformImage.alt = page.alt || item.title + " 波形图";
  ui.openImage.href = src;
  ui.imageCaption.textContent = page.caption || "";

  ui.previousButton.disabled = index <= 0;
  ui.nextButton.disabled = index < 0 || index >= state.visible.length - 1;
  renderDecision(item);
}

function selectRelative(offset) {
  const index = state.visible.findIndex(item => item.id === state.currentId);
  const next = Math.max(0, Math.min(state.visible.length - 1, index + offset));
  if (next === index || !state.visible[next]) return;
  state.currentId = state.visible[next].id;
  state.pageIndex = 0;
  ui.itemSelect.value = state.currentId;
  renderCurrent();
}

function selectPage(offset) {
  const item = currentItem();
  if (!item) return;
  const next = Math.max(0, Math.min(item.pages.length - 1, state.pageIndex + offset));
  if (next === state.pageIndex) return;
  state.pageIndex = next;
  renderCurrent();
}

function setDecision(itemId, code) {
  const previous = state.reviews[itemId] || {};
  if (!code && !previous.note) {
    delete state.reviews[itemId];
  } else {
    state.reviews[itemId] = {
      decision: code,
      note: previous.note || "",
      updated_at: nowIso()
    };
  }
  storageSave();
  renderItemList();
  renderProgress();
  renderDecision(currentItem());
}

function setNote(itemId, note) {
  const previous = state.reviews[itemId] || {};
  if (!previous.decision && !note) {
    delete state.reviews[itemId];
  } else {
    state.reviews[itemId] = {
      decision: previous.decision || "",
      note,
      updated_at: nowIso()
    };
  }
  storageSave();
}

function buildDecisionFilter() {
  for (const label of state.manifest.labels) {
    ui.decisionFilter.add(new Option(label.name, label.code));
  }
}

function exportCsv() {
  const headers = [
    "item_id", "section", "decision_code", "decision_name",
    "note", "updated_at", "title", "subtitle", "tags", "metadata_json"
  ];
  const rows = state.manifest.items.filter(isReviewable).map(item => {
    const review = state.reviews[item.id] || {};
    return [
      item.id,
      item.section,
      review.decision || "",
      decisionName(review.decision),
      review.note || "",
      review.updated_at || "",
      item.title,
      item.subtitle,
      item.tags.join("|"),
      JSON.stringify(item.metadata)
    ];
  });
  const csv = "﻿" + [headers, ...rows]
    .map(row => row.map(escapeCsv).join(","))
    .join("\r\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  const stamp = new Date().toISOString().replace(/[:T]/g, "-").slice(0, 19);
  link.download = state.manifest.project_id + "_reviews_" + stamp + ".csv";
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  toast("CSV 已导出");
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (quoted) {
      if (char === '"' && text[i + 1] === '"') {
        field += '"';
        i += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  row.push(field.replace(/\r$/, ""));
  if (row.some(value => value !== "")) rows.push(row);
  return rows;
}

async function importCsv(file) {
  const rows = parseCsv((await file.text()).replace(/^﻿/, ""));
  if (rows.length < 2) throw new Error("CSV 没有数据行");
  const headers = rows[0].map(value => value.trim());
  const index = Object.fromEntries(headers.map((name, i) => [name, i]));
  const idColumn = index.item_id ?? index.id;
  const decisionColumn = index.decision_code ?? index.decision;
  if (idColumn == null || decisionColumn == null) {
    throw new Error("CSV 需要 item_id（或 id）和 decision_code（或 decision）列");
  }
  const knownIds = new Set(state.manifest.items.map(item => item.id));
  const labelByName = new Map(state.manifest.labels.map(label => [label.name, label.code]));
  let imported = 0;
  for (const row of rows.slice(1)) {
    const id = (row[idColumn] || "").trim();
    if (!knownIds.has(id)) continue;
    const rawDecision = (row[decisionColumn] || "").trim();
    const decision = state.manifest.labels.some(label => label.code === rawDecision)
      ? rawDecision
      : (labelByName.get(rawDecision) || "");
    const note = index.note == null ? "" : (row[index.note] || "");
    if (!decision && !note) continue;
    state.reviews[id] = {
      decision,
      note,
      updated_at: index.updated_at == null ? nowIso() : (row[index.updated_at] || nowIso())
    };
    imported += 1;
  }
  storageSave();
  applyFilters();
  toast("已导入 " + imported + " 条复核记录");
}

function wireEvents() {
  ui.searchInput.addEventListener("input", applyFilters);
  ui.decisionFilter.addEventListener("change", applyFilters);
  ui.tagFilter.addEventListener("change", applyFilters);
  ui.itemSelect.addEventListener("change", () => {
    state.currentId = ui.itemSelect.value;
    state.pageIndex = 0;
    renderCurrent();
  });
  ui.previousButton.addEventListener("click", () => selectRelative(-1));
  ui.nextButton.addEventListener("click", () => selectRelative(1));
  ui.pageSelect.addEventListener("change", () => {
    state.pageIndex = Number(ui.pageSelect.value);
    renderCurrent();
  });
  ui.noteInput.addEventListener("input", () => {
    const item = currentItem();
    if (item) setNote(item.id, ui.noteInput.value);
  });
  ui.exportButton.addEventListener("click", exportCsv);
  ui.importButton.addEventListener("click", () => ui.importFile.click());
  ui.importFile.addEventListener("change", async () => {
    const file = ui.importFile.files[0];
    if (!file) return;
    try {
      await importCsv(file);
    } catch (error) {
      toast("导入失败：" + error.message);
    } finally {
      ui.importFile.value = "";
    }
  });
  ui.clearButton.addEventListener("click", () => {
    if (!confirm("清除本项目保存在当前浏览器中的全部判定和备注？请先导出需要保留的结果。")) return;
    state.reviews = {};
    storageSave();
    applyFilters();
    toast("本浏览器中的判定已清除");
  });
  document.addEventListener("keydown", event => {
    const tagName = event.target.tagName;
    if (["INPUT", "TEXTAREA", "SELECT"].includes(tagName)) return;
    if (event.key === "ArrowLeft") selectRelative(-1);
    else if (event.key === "ArrowRight") selectRelative(1);
    else if (event.key === "[") selectPage(-1);
    else if (event.key === "]") selectPage(1);
    else if (event.key === "0") {
      const item = currentItem();
      if (item && isReviewable(item)) setDecision(item.id, "");
    } else {
      const label = state.manifest.labels.find(candidate => candidate.shortcut === event.key);
      const item = currentItem();
      if (label && item && isReviewable(item)) setDecision(item.id, label.code);
    }
  });
}

async function start() {
  for (const id of [
    "projectTitle", "projectDescription", "sectionTabs", "importButton",
    "exportButton", "importFile", "progressText", "progressBar", "visibleCount",
    "searchInput", "decisionFilter", "tagFilter", "itemSelect", "previousButton",
    "nextButton", "emptyState", "viewer", "counter", "itemTitle", "itemSubtitle",
    "itemTags", "metadata", "pageSelect", "openImage", "waveformImage",
    "imageCaption", "decisionPanel", "decisionButtons", "noteInput",
    "referenceNotice", "shortcutHelp", "clearButton", "toast"
  ]) ui[id] = byId(id);

  try {
    const response = await fetch("/project.json", { cache: "no-store" });
    if (!response.ok) throw new Error("HTTP " + response.status);
    state.manifest = normalizeManifest(await response.json());
    state.sectionId = state.manifest.sections[0].id;
    state.storageKey = "waveform-review:" + state.manifest.project_id + ":"
      + (state.manifest.schema_version || 1);
    storageLoad();
    renderHeader();
    buildDecisionFilter();
    populateTagFilter();
    renderTabs();
    wireEvents();
    applyFilters();
  } catch (error) {
    document.body.replaceChildren();
    const message = document.createElement("pre");
    message.className = "fatal-error";
    message.textContent = "项目加载失败\n\n" + error.message;
    document.body.appendChild(message);
  }
}

start();
