// Gemini Code Mobile Client
const outputArea = document.getElementById("outputArea");
const inputForm = document.getElementById("inputForm");
const userInput = document.getElementById("userInput");
const modelBadge = document.getElementById("modelBadge");

// Settings Elements
const settingsBtn = document.getElementById("settingsBtn");
const settingsModal = document.getElementById("settingsModal");
const apiKeyInput = document.getElementById("apiKeyInput");
const modelSelect = document.getElementById("modelSelect");
const proxyUrlInput = document.getElementById("proxyUrlInput");
const saveSettingsBtn = document.getElementById("saveSettingsBtn");
const closeSettingsBtn = document.getElementById("closeSettingsBtn");

let apiKey = localStorage.getItem("gemini_code_api_key") || "";
let selectedModel = localStorage.getItem("gemini_code_model") || "gemini-2.5-flash";
let customProxy = localStorage.getItem("gemini_code_proxy") || "";

modelBadge.textContent = selectedModel;
apiKeyInput.value = apiKey;
modelSelect.value = selectedModel;
proxyUrlInput.value = customProxy;

// Settings Toggle
settingsBtn.addEventListener("click", () => settingsModal.classList.remove("hidden"));
closeSettingsBtn.addEventListener("click", () => settingsModal.classList.add("hidden"));
saveSettingsBtn.addEventListener("click", () => {
  apiKey = apiKeyInput.value.trim();
  selectedModel = modelSelect.value;
  customProxy = proxyUrlInput.value.trim();

  localStorage.setItem("gemini_code_api_key", apiKey);
  localStorage.setItem("gemini_code_model", selectedModel);
  localStorage.setItem("gemini_code_proxy", customProxy);

  modelBadge.textContent = selectedModel;
  settingsModal.classList.add("hidden");
  appendMessage("system", "Settings saved.");
});

function appendMessage(role, text) {
  const div = document.createElement("div");
  if (role === "user") {
    div.className = "user-entry";
    div.textContent = `❯ ${text}`;
  } else if (role === "system") {
    div.className = "system-msg";
    div.textContent = `[INFO] ${text}`;
  } else {
    div.className = "model-entry";
    div.textContent = text;
  }
  outputArea.appendChild(div);
  outputArea.scrollTop = outputArea.scrollHeight;
  return div;
}

window.quickCommand = function(cmd) {
  userInput.value = cmd;
  inputForm.dispatchEvent(new Event("submit"));
};

inputForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = userInput.value.trim();
  if (!text) return;
  userInput.value = "";

  if (text === "/clear") {
    outputArea.innerHTML = "";
    return;
  }

  if (text === "/quota") {
    appendMessage("system", `Active Model: ${selectedModel}\nFree Tier: 15 RPM / 1,500 Requests/Day\nContext: 1,000,000 tokens`);
    return;
  }

  if (text === "/doctor") {
    appendMessage("system", `Browser: Safari / Mobile Web\nAPI Key Configured: ${apiKey ? "Yes" : "No"}\nActive Model: ${selectedModel}`);
    return;
  }

  appendMessage("user", text);

  if (!apiKey) {
    appendMessage("system", "Please configure your Google AI Studio API key in settings (⚙)!");
    settingsModal.classList.remove("hidden");
    return;
  }

  const modelDiv = appendMessage("model", "✦ Thinking...");
  
  try {
    const base = customProxy || "https://generativelanguage.googleapis.com";
    const cleanModel = selectedModel.startsWith("models/") ? selectedModel : `models/${selectedModel}`;
    const url = `${base.replace(/\/$/, "")}/v1beta/${cleanModel}:generateContent?key=${apiKey}`;

    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{ role: "user", parts: [{ text }] }],
        systemInstruction: {
          parts: [{ text: "You are Gemini Code Mobile. Provide concise, expert code solutions and answers." }]
        }
      })
    });

    if (!resp.ok) {
      const err = await resp.text();
      modelDiv.textContent = `Error (${resp.status}): ${err}`;
      return;
    }

    const data = await resp.json();
    const reply = data.candidates?.[0]?.content?.parts?.[0]?.text || "No response.";
    modelDiv.textContent = reply;
  } catch (err) {
    modelDiv.textContent = `Network Error: ${err.message}. If in Russia, configure a reverse proxy in settings (⚙).`;
  }
});
