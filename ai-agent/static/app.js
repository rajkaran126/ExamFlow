/**
 * EXAMFLOW AI Frontend Controller
 * Handles ChatGPT-style PDF drag & drop, push-to-talk voice, confirmation cards,
 * and multi-step investigation rendering.
 */

let activeSessionId = "session_" + Math.random().toString(36).substring(2, 10);
let attachedFiles = [];
let isVoiceRecording = false;
let speechRecognition = null;
let currentUtterance = null;

// Initialize Lucide Icons & Theme
document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();
    initTheme();
    initDragAndDrop();
    initVoice();
    setupFileInput();
});

// Theme Toggle
function initTheme() {
    const isDark = localStorage.getItem("theme") === "dark";
    if (isDark) {
        document.documentElement.classList.add("dark");
    }
    document.getElementById("themeToggleBtn").addEventListener("click", () => {
        document.documentElement.classList.toggle("dark");
        localStorage.setItem("theme", document.documentElement.classList.contains("dark") ? "dark" : "light");
        lucide.createIcons();
    });
}

// Drag & Drop for PDF Intelligence
function initDragAndDrop() {
    const dropZone = document.getElementById("dropZone");
    const dragOverlay = document.getElementById("dragOverlay");

    ['dragenter', 'dragover'].forEach(eventName => {
        window.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dragOverlay.classList.remove('hidden');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dragOverlay.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dragOverlay.classList.add('hidden');
        });
    });

    window.addEventListener('drop', (e) => {
        e.preventDefault();
        dragOverlay.classList.add('hidden');
        const files = e.dataTransfer.files;
        handleFiles(files);
    });
}

function setupFileInput() {
    const fileInput = document.getElementById("pdfFileInput");
    fileInput.addEventListener("change", (e) => {
        handleFiles(e.target.files);
    });
}

async function handleFiles(files) {
    for (let file of files) {
        if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
            alert(`File "${file.name}" is not a PDF.`);
            continue;
        }

        // Upload to server
        const formData = new FormData();
        formData.append("file", file);
        formData.append("session_id", activeSessionId);

        try {
            renderStagedChip(file.name, true);
            const res = await fetch("/api/documents/upload", {
                method: "POST",
                body: formData
            });

            if (res.ok) {
                const metadata = await res.json();
                attachedFiles.push(metadata);
                updateAttachedDocsUI();
                renderStagedChip(file.name, false, metadata.doc_id);
            } else {
                alert(`Failed to upload ${file.name}`);
            }
        } catch (err) {
            console.error(err);
            alert(`Network error uploading ${file.name}`);
        }
    }
}

function renderStagedChip(filename, isUploading, docId = null) {
    const chipsContainer = document.getElementById("fileUploadChips");
    chipsContainer.classList.remove("hidden");

    const chip = document.createElement("div");
    chip.id = `chip_${docId || filename}`;
    chip.className = "flex items-center space-x-1.5 bg-white dark:bg-slate-700 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-600 text-xs text-slate-700 dark:text-slate-200 shrink-0";
    chip.innerHTML = `
        <i data-lucide="file" class="w-3.5 h-3.5 text-indigo-500"></i>
        <span class="truncate max-w-[150px]">${filename}</span>
        ${isUploading ? `<span class="animate-spin text-slate-400">⏳</span>` : `
            <button onclick="removeAttachedDoc('${docId}', '${filename}')" class="text-slate-400 hover:text-rose-500">
                <i data-lucide="x" class="w-3.5 h-3.5"></i>
            </button>
        `}
    `;
    chipsContainer.appendChild(chip);
    lucide.createIcons();
}

async function removeAttachedDoc(docId, filename) {
    try {
        await fetch(`/api/documents/${docId}?session_id=${activeSessionId}`, { method: "DELETE" });
        attachedFiles = attachedFiles.filter(d => d.doc_id !== docId);
        updateAttachedDocsUI();
        const chip = document.getElementById(`chip_${docId}`);
        if (chip) chip.remove();
        if (attachedFiles.length === 0) {
            document.getElementById("fileUploadChips").classList.add("hidden");
        }
    } catch (e) {
        console.error(e);
    }
}

function updateAttachedDocsUI() {
    const list = document.getElementById("attachedDocsList");
    const badge = document.getElementById("docCountBadge");
    badge.innerText = attachedFiles.length;

    if (attachedFiles.length === 0) {
        list.innerHTML = `<p class="text-slate-400 italic">No PDF files attached yet. Drop PDF in chat to index.</p>`;
        return;
    }

    list.innerHTML = attachedFiles.map(doc => `
        <div class="p-2 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 flex items-center justify-between">
            <div class="truncate mr-2">
                <p class="font-semibold truncate text-slate-800 dark:text-slate-200">${doc.filename}</p>
                <p class="text-[10px] text-slate-400">${doc.total_pages} Pages • ${doc.chunks_count} Chunks ${doc.is_scanned ? '• (OCR)' : ''}</p>
            </div>
            <button onclick="removeAttachedDoc('${doc.doc_id}', '${doc.filename}')" class="text-slate-400 hover:text-rose-500">
                <i data-lucide="trash" class="w-3.5 h-3.5"></i>
            </button>
        </div>
    `).join("");
    lucide.createIcons();
}

// Voice Integration (Push-to-Talk & TTS)
function initVoice() {
    const pushBtn = document.getElementById("pushToTalkBtn");
    const indicator = document.getElementById("voiceWaveIndicator");

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        speechRecognition = new SpeechRec();
        speechRecognition.continuous = false;
        speechRecognition.interimResults = false;

        speechRecognition.onstart = () => {
            isVoiceRecording = true;
            pushBtn.classList.add("voice-active");
            indicator.classList.remove("hidden");
        };

        speechRecognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            document.getElementById("messageInput").value = transcript;
            submitMessage();
        };

        speechRecognition.onerror = (e) => {
            console.error("Speech error", e);
            stopVoice();
        };

        speechRecognition.onend = () => {
            stopVoice();
        };

        pushBtn.addEventListener("click", () => {
            if (!isVoiceRecording) {
                speechRecognition.start();
            } else {
                speechRecognition.stop();
            }
        });
    } else {
        pushBtn.title = "Web Speech API not supported in this browser.";
    }
}

function stopVoice() {
    isVoiceRecording = false;
    document.getElementById("pushToTalkBtn").classList.remove("voice-active");
    document.getElementById("voiceWaveIndicator").classList.add("hidden");
}

function playAudioSynthesis(text) {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();

    // Strip Markdown symbols for natural speech
    const speakable = text.replace(/[*#`_\[\]|]/g, " ").replace(/\s+/g, " ");
    const utterance = new SpeechSynthesisUtterance(speakable.substring(0, 300));
    utterance.rate = 1.05;
    utterance.onstart = () => {
        document.getElementById("audioStopBtn").classList.remove("hidden");
    };
    utterance.onend = () => {
        document.getElementById("audioStopBtn").classList.add("hidden");
    };
    window.speechSynthesis.speak(utterance);
}

function stopAudioPlayback() {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
    }
    document.getElementById("audioStopBtn").classList.add("hidden");
}

// Quick Prompt Sender
function sendQuickPrompt(promptText) {
    document.getElementById("messageInput").value = promptText;
    submitMessage();
}

function handleInputKey(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        submitMessage();
    }
}

// Main Chat Submission
async function submitMessage() {
    const input = document.getElementById("messageInput");
    const sendBtn = document.getElementById("sendBtn");
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    sendBtn.disabled = true;

    // Render User Message in UI
    appendUserMessage(text);

    // Prepare Request Payload
    const userRole = document.getElementById("userRoleSelect").value;
    const payload = {
        message: text,
        session_id: activeSessionId,
        user_role: userRole,
        active_exam_id: "EXAM-2026-GATE",
        attached_doc_ids: attachedFiles.map(d => d.doc_id)
    };

    // Render Loading Skeleton
    const loadingElemId = appendLoadingSkeleton();

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: jsonStringifySafe(payload)
        });

        const data = await response.json();
        removeLoadingSkeleton(loadingElemId);

        if (response.ok) {
            appendAssistantResponse(data);
            if (data.reply) {
                playAudioSynthesis(data.reply);
            }
        } else {
            appendErrorMessage(data.detail || "An error occurred during agent processing.");
        }
    } catch (err) {
        console.error(err);
        removeLoadingSkeleton(loadingElemId);
        appendErrorMessage("Network error: Could not reach EXAMFLOW AI service.");
    } finally {
        sendBtn.disabled = false;
    }
}

function jsonStringifySafe(obj) {
    return JSON.stringify(obj);
}

function appendUserMessage(text) {
    const container = document.getElementById("chatMessages");
    const msg = document.createElement("div");
    msg.className = "flex justify-end";
    msg.innerHTML = `
        <div class="bg-indigo-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 max-w-xl text-sm shadow-sm leading-relaxed">
            ${escapeHtml(text)}
        </div>
    `;
    container.appendChild(msg);
    scrollToBottom();
}

function appendLoadingSkeleton() {
    const container = document.getElementById("chatMessages");
    const id = "loading_" + Date.now();
    const elem = document.createElement("div");
    elem.id = id;
    elem.className = "flex items-start space-x-3 max-w-2xl";
    elem.innerHTML = `
        <div class="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white shrink-0 shadow animate-pulse">
            <i data-lucide="loader" class="w-5 h-5 animate-spin"></i>
        </div>
        <div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-2xl shadow-sm text-sm w-full space-y-2">
            <div class="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/3 animate-pulse"></div>
            <div class="h-3 bg-slate-100 dark:bg-slate-700/60 rounded w-5/6 animate-pulse"></div>
            <div class="h-3 bg-slate-100 dark:bg-slate-700/60 rounded w-2/3 animate-pulse"></div>
        </div>
    `;
    container.appendChild(elem);
    lucide.createIcons();
    scrollToBottom();
    return id;
}

function removeLoadingSkeleton(id) {
    const elem = document.getElementById(id);
    if (elem) elem.remove();
}

function appendAssistantResponse(data) {
    const container = document.getElementById("chatMessages");
    const msg = document.createElement("div");
    msg.className = "flex items-start space-x-3 max-w-4xl";

    let planHtml = "";
    if (data.plan) {
        planHtml = `
            <div class="mb-3 p-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-xs space-y-1">
                <span class="font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider flex items-center space-x-1">
                    <i data-lucide="compass" class="w-3.5 h-3.5"></i>
                    <span>Autonomous Plan: ${escapeHtml(data.plan.objective)}</span>
                </span>
                <ul class="list-disc list-inside text-slate-600 dark:text-slate-300 space-y-0.5 pt-1">
                    ${data.plan.planned_steps.map(s => `<li>${escapeHtml(s)}</li>`).join("")}
                </ul>
            </div>
        `;
    }

    let citationsHtml = "";
    if (data.citations && data.citations.length > 0) {
        citationsHtml = `
            <div class="mt-3 pt-3 border-t border-slate-100 dark:border-slate-700">
                <span class="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-1.5">Grounded PDF Citations:</span>
                <div class="flex flex-wrap gap-1.5">
                    ${data.citations.map(c => `
                        <span class="px-2 py-0.5 bg-indigo-50 dark:bg-indigo-950 border border-indigo-200 dark:border-indigo-800 text-indigo-700 dark:text-indigo-300 rounded text-xs" title="${escapeHtml(c.snippet)}">
                            📄 ${escapeHtml(c.doc_name)} (Page ${c.page_number})
                        </span>
                    `).join("")}
                </div>
            </div>
        `;
    }

    let preparedActionHtml = "";
    if (data.prepared_action) {
        const prep = data.prepared_action;
        preparedActionHtml = `
            <div class="mt-4 p-4 rounded-xl border-2 border-indigo-500/40 bg-indigo-50/50 dark:bg-indigo-950/40 space-y-3">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase tracking-wider text-indigo-700 dark:text-indigo-300 flex items-center space-x-1.5">
                        <i data-lucide="shield-alert" class="w-4 h-4 text-indigo-600"></i>
                        <span>Level 4 Action Prepared: Awaiting Authorization</span>
                    </span>
                    <span class="text-[10px] bg-indigo-200 dark:bg-indigo-800 text-indigo-900 dark:text-indigo-100 px-2 py-0.5 rounded font-mono">
                        ${prep.preparation_id}
                    </span>
                </div>
                <p class="text-xs font-semibold text-slate-800 dark:text-slate-200">${escapeHtml(prep.summary)}</p>
                <div class="text-xs text-slate-600 dark:text-slate-400 space-y-1">
                    <p class="font-medium">Consequences:</p>
                    <ul class="list-disc list-inside space-y-0.5">
                        ${prep.consequences.map(c => `<li>${escapeHtml(c)}</li>`).join("")}
                    </ul>
                </div>
                <div class="flex items-center space-x-2 pt-2 border-t border-indigo-200 dark:border-indigo-800">
                    <button onclick="confirmConsequentialAction('${prep.preparation_id}', '${prep.approver_token}', true)" class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow transition flex items-center space-x-1">
                        <i data-lucide="check-circle-2" class="w-3.5 h-3.5"></i>
                        <span>Approve & Execute (Level 5)</span>
                    </button>
                    <button onclick="confirmConsequentialAction('${prep.preparation_id}', '${prep.approver_token}', false)" class="px-3 py-1.5 bg-slate-200 dark:bg-slate-700 hover:bg-rose-100 hover:text-rose-600 text-slate-700 dark:text-slate-300 rounded-lg text-xs font-semibold transition">
                        Reject
                    </button>
                </div>
            </div>
        `;
    }

    msg.innerHTML = `
        <div class="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white shrink-0 shadow mt-1">
            <i data-lucide="bot" class="w-5 h-5"></i>
        </div>
        <div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-2xl shadow-sm text-sm space-y-3 prose dark:prose-invert max-w-none w-full">
            ${planHtml}
            <div>${formatMarkdownToHtml(data.reply)}</div>
            ${preparedActionHtml}
            ${citationsHtml}
        </div>
    `;
    container.appendChild(msg);
    lucide.createIcons();
    scrollToBottom();
}

async function confirmConsequentialAction(prepId, token, confirmed) {
    const userRole = document.getElementById("userRoleSelect").value;
    try {
        const res = await fetch("/api/action/confirm", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                preparation_id: prepId,
                approver_token: token,
                confirmed: confirmed,
                user_id: "admin_user",
                user_role: userRole
            })
        });
        const result = await res.json();
        if (res.ok) {
            appendAssistantResponse({
                reply: `**Action Outcome (Level 5 Consequential Execution):**\n\n${result.message || JSON.stringify(result, null, 2)}`
            });
        } else {
            alert(`Execution failed: ${result.detail}`);
        }
    } catch (e) {
        console.error(e);
        alert("Network error executing consequential action.");
    }
}

function appendErrorMessage(errorText) {
    const container = document.getElementById("chatMessages");
    const msg = document.createElement("div");
    msg.className = "flex items-start space-x-3 max-w-2xl";
    msg.innerHTML = `
        <div class="w-9 h-9 rounded-xl bg-rose-600 flex items-center justify-center text-white shrink-0 shadow">
            <i data-lucide="alert-octagon" class="w-5 h-5"></i>
        </div>
        <div class="bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 p-4 rounded-2xl text-sm">
            <p class="font-bold">Execution Error</p>
            <p class="text-xs mt-1">${escapeHtml(errorText)}</p>
        </div>
    `;
    container.appendChild(msg);
    lucide.createIcons();
    scrollToBottom();
}

function clearSessionChat() {
    activeSessionId = "session_" + Math.random().toString(36).substring(2, 10);
    document.getElementById("chatMessages").innerHTML = "";
    appendAssistantResponse({
        reply: "Session cleared. What would you like to investigate next?"
    });
}

function scrollToBottom() {
    const chat = document.getElementById("chatMessages");
    chat.scrollTop = chat.scrollHeight;
}

function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

function formatMarkdownToHtml(markdown) {
    if (!markdown) return "";
    let html = markdown
        .replace(/### (.*?)\n/g, '<h3 class="font-bold text-base mt-2 mb-1">$1</h3>')
        .replace(/## (.*?)\n/g, '<h2 class="font-bold text-lg mt-3 mb-1 text-indigo-600 dark:text-indigo-400">$1</h2>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`([^`]+)`/g, '<code class="bg-slate-100 dark:bg-slate-700 px-1 py-0.5 rounded text-xs font-mono">$1</code>')
        .replace(/\n\n/g, '<br><br>');

    // Basic table parser
    if (html.includes("|")) {
        const lines = html.split("<br><br>");
        html = lines.map(line => {
            if (line.includes("|") && line.includes("\n")) {
                const rows = line.trim().split("\n");
                let tableHtml = '<div class="overflow-x-auto my-2"><table class="min-w-full divide-y divide-slate-200 dark:divide-slate-700 border text-xs">';
                rows.forEach((row, idx) => {
                    if (row.includes("---")) return;
                    const cols = row.split("|").filter((c, i, a) => i !== 0 && i !== a.length - 1);
                    if (idx === 0) {
                        tableHtml += '<thead class="bg-slate-50 dark:bg-slate-900"><tr>' + cols.map(c => `<th class="px-3 py-2 text-left font-semibold text-slate-700 dark:text-slate-300">${c.trim()}</th>`).join("") + '</tr></thead><tbody>';
                    } else {
                        tableHtml += '<tr class="border-t border-slate-100 dark:border-slate-800">' + cols.map(c => `<td class="px-3 py-1.5 text-slate-800 dark:text-slate-200">${c.trim()}</td>`).join("") + '</tr>';
                    }
                });
                tableHtml += '</tbody></table></div>';
                return tableHtml;
            }
            return line;
        }).join("<br><br>");
    }

    return html;
}
