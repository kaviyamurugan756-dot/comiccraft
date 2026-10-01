const form = document.querySelector("#comic-form");
const promptField = document.querySelector("#prompt");
const promptCount = document.querySelector("#prompt-count");
const createButton = document.querySelector("#create-button");
const exportButton = document.querySelector("#export-button");
const storyboard = document.querySelector("#storyboard-content");
const boardCount = document.querySelector("#board-count");
const boardStatus = document.querySelector("#board-status");
const providerLabel = document.querySelector("#provider-label");
const serviceStatus = document.querySelector("#service-status");
const toast = document.querySelector("#toast");
let panelCount = 4;
let currentComic = null;
let toastTimer;

promptField.addEventListener("input", () => {
  promptCount.textContent = `${promptField.value.length} / 1200`;
});
promptCount.textContent = `${promptField.value.length} / 1200`;

document.querySelectorAll(".segment").forEach((button) => {
  button.addEventListener("click", () => {
    panelCount = Number(button.dataset.panels);
    document.querySelectorAll(".segment").forEach((segment) => {
      const selected = segment === button;
      segment.classList.toggle("is-selected", selected);
      segment.setAttribute("aria-pressed", String(selected));
    });
  });
});

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("is-visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 3500);
}

function renderComic(comic) {
  const heading = document.createElement("div");
  heading.className = "comic-heading";
  const headingCopy = document.createElement("div");
  const title = document.createElement("h2");
  title.textContent = comic.title;
  const details = document.createElement("p");
  details.textContent = `${comic.character}  /  ${comic.setting}  /  ${comic.tone} · ${comic.art_style}`;
  headingCopy.append(title, details);
  heading.append(headingCopy);

  const grid = document.createElement("div");
  grid.className = "comic-grid";
  comic.panels.forEach((panel, index) => {
    const article = document.createElement("article");
    article.className = "comic-panel";
    const panelHead = document.createElement("div");
    panelHead.className = "panel-head";
    const panelTitle = document.createElement("strong");
    panelTitle.textContent = panel.title;
    const number = document.createElement("span");
    number.textContent = String(index + 1).padStart(2, "0");
    panelHead.append(panelTitle, number);

    const image = document.createElement("img");
    image.className = "panel-image";
    image.src = panel.image;
    image.alt = `${panel.title}: ${panel.image_prompt}`;
    image.loading = "lazy";

    const caption = document.createElement("div");
    caption.className = "panel-caption";
    const narration = document.createElement("p");
    narration.textContent = panel.narration;
    caption.append(narration);
    if (panel.dialogue) {
      const dialogue = document.createElement("blockquote");
      dialogue.textContent = `“${panel.dialogue}”`;
      caption.append(dialogue);
    }
    article.append(panelHead, image, caption);
    grid.append(article);
  });
  storyboard.replaceChildren(heading, grid);
  boardCount.textContent = `${comic.panels.length} PANELS · ${comic.tone.toUpperCase()}`; 
  providerLabel.textContent = comic.image_provider.toUpperCase();
  document.querySelector("#footer-page").textContent = `COMICCRAFT  /  ${String(comic.panels.length).padStart(3, "0")}`;
  exportButton.disabled = false;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  currentComic = null;
  exportButton.disabled = true;
  createButton.disabled = true;
  createButton.querySelector(".button-create-label").textContent = "Making your comic...";
  boardStatus.textContent = "CREATING";
  boardCount.textContent = "GIVE US A MOMENT";
  storyboard.innerHTML = '<div class="loading-state"><div class="loading-art" aria-hidden="true"><span></span><span></span><span></span><span></span></div><h2>Building your world...</h2><p>Writing a story, one panel at a time.</p></div>';
  const values = Object.fromEntries(new FormData(form).entries());
  values.panel_count = panelCount;
  try {
    const response = await fetch("/api/comics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(values),
    });
    if (!response.ok) {
      const detail = await response.json().catch(() => null);
      throw new Error(detail?.detail?.[0]?.msg || "The comic could not be created. Please try again.");
    }
    currentComic = await response.json();
    renderComic(currentComic);
    boardStatus.textContent = "READY";
    showToast(`${currentComic.panels.length} panels are ready to read.`);
  } catch (error) {
    boardStatus.textContent = "NEEDS A RETRY";
    boardCount.textContent = "SOMETHING WENT WRONG";
    const message = document.createElement("p");
    message.className = "error-message";
    message.textContent = error.message || "Couldn't reach the studio. Check your connection and try again.";
    storyboard.replaceChildren(message);
  } finally {
    createButton.disabled = false;
    createButton.querySelector(".button-create-label").textContent = "Create my comic";
  }
});

exportButton.addEventListener("click", async () => {
  if (!currentComic) return;
  exportButton.disabled = true;
  try {
    const response = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ comic: currentComic }),
    });
    if (!response.ok) throw new Error("PDF export failed. Please try again.");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `comiccraft-${currentComic.character.toLowerCase().replace(/[^a-z0-9_-]+/g, "-")}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
    showToast("Your comic PDF has been downloaded.");
  } catch (error) {
    showToast(error.message || "Couldn't export the comic.");
  } finally {
    exportButton.disabled = false;
  }
});

fetch("/api/health").then((response) => response.json()).then((health) => {
  if (health.gemini_configured || health.huggingface_configured) {
    serviceStatus.textContent = "AI MODELS CONNECTED";
  }
}).catch(() => {
  serviceStatus.textContent = "STUDIO READY";
});
