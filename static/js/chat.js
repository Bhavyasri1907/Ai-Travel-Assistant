/**
 * TravelGPT - ChatGPT Style Frontend Controller with Persistent Chat History
 */

document.addEventListener('DOMContentLoaded', () => {
    // Storage Key
    const STORAGE_KEY = 'travelgpt_sessions_v2';

    // State
    let currentSessionId = null;
    let chatSessions = loadChatSessions();
    const VOICE_STORAGE_KEY = 'travelgpt_voice_enabled';
    let speechEnabled = localStorage.getItem(VOICE_STORAGE_KEY) !== 'false'; // default enabled
    let isListening = false;
    let recognition = null;

    // DOM Elements
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const chatMessages = document.getElementById('chatMessages');
    const chatStream = document.getElementById('chatStream');
    const heroWelcome = document.getElementById('heroWelcome');
    const quickRepliesContainer = document.getElementById('quickRepliesContainer');
    const newChatBtn = document.getElementById('newChatBtn');
    const topNewChatBtn = document.getElementById('topNewChatBtn');
    const chatHistoryList = document.getElementById('chatHistoryList');
    const emptyHistoryMsg = document.getElementById('emptyHistoryMsg');
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const topVoiceToggleBtn = document.getElementById('topVoiceToggleBtn');
    const topVoiceIcon = document.getElementById('topVoiceIcon');
    const topVoiceLabel = document.getElementById('topVoiceLabel');
    const voiceToggleBtn = document.getElementById('voiceToggleBtn');
    const voiceIcon = document.getElementById('voiceIcon');
    const micBtn = document.getElementById('micBtn');
    const speechStatus = document.getElementById('speechStatus');

    // -------------------------------------------------------------
    // 1. CHAT HISTORY PERSISTENCE (LocalStorage)
    // -------------------------------------------------------------
    function loadChatSessions() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            console.error('Error loading chat sessions:', e);
            return [];
        }
    }

    function saveChatSessions() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(chatSessions));
        } catch (e) {
            console.error('Error saving chat sessions:', e);
        }
    }

    function renderSidebarHistory() {
        if (!chatHistoryList) return;
        chatHistoryList.innerHTML = '';

        if (!chatSessions || chatSessions.length === 0) {
            if (emptyHistoryMsg) emptyHistoryMsg.style.display = 'block';
            return;
        }

        if (emptyHistoryMsg) emptyHistoryMsg.style.display = 'none';

        // Render each saved session in reverse chronological order
        chatSessions.forEach(session => {
            const item = document.createElement('div');
            item.className = `history-item ${session.id === currentSessionId ? 'active' : ''}`;
            item.setAttribute('data-id', session.id);

            item.innerHTML = `
                <span class="history-text" title="${escapeHtml(session.title)}">
                    <i class="bi bi-chat-left chat-icon"></i>
                    <span class="chat-title">${escapeHtml(session.title)}</span>
                </span>
                <button class="btn-delete-session" title="Delete chat" data-id="${session.id}">
                    <i class="bi bi-trash"></i>
                </button>
            `;

            // Click to load chat session
            item.querySelector('.history-text').addEventListener('click', (e) => {
                e.stopPropagation();
                loadSession(session.id);
                if (window.innerWidth <= 768 && sidebar) {
                    sidebar.classList.remove('mobile-open');
                }
            });

            // Click to delete chat session
            item.querySelector('.btn-delete-session').addEventListener('click', (e) => {
                e.stopPropagation();
                deleteSession(session.id);
            });

            chatHistoryList.appendChild(item);
        });
    }

    function loadSession(id) {
        const session = chatSessions.find(s => s.id === id);
        if (!session) return;

        currentSessionId = session.id;

        // Reset UI & render saved messages
        chatMessages.innerHTML = '';
        quickRepliesContainer.innerHTML = '';

        (session.messages || []).forEach(msg => {
            appendMessage(msg.sender, msg.text, msg.itinerary, msg.recommended_destinations, msg.placeShowcase, false);
        });

        // Re-render sidebar to highlight active item
        renderSidebarHistory();
        chatStream.scrollTop = chatStream.scrollHeight;
    }

    function deleteSession(id) {
        chatSessions = chatSessions.filter(s => s.id !== id);
        saveChatSessions();

        if (currentSessionId === id) {
            startNewChat();
        } else {
            renderSidebarHistory();
        }
    }

    function generateSessionTitle(prompt) {
        let clean = prompt.trim().replace(/^tell me about /i, '').replace(/^what about /i, '').replace(/^plan a trip to /i, '');
        if (clean.length > 24) {
            clean = clean.substring(0, 24) + '...';
        }
        return clean.charAt(0).toUpperCase() + clean.slice(1);
    }

    function getOrCreateActiveSession(initialPrompt = '') {
        let session = chatSessions.find(s => s.id === currentSessionId);
        if (!session) {
            currentSessionId = 'chat_' + Date.now();
            session = {
                id: currentSessionId,
                title: generateSessionTitle(initialPrompt || 'New Travel Plan'),
                created_at: Date.now(),
                messages: []
            };
            chatSessions.unshift(session);
            saveChatSessions();
            renderSidebarHistory();
        }
        return session;
    }

    // -------------------------------------------------------------
    // 2. NEW CHAT & HERO SCREEN
    // -------------------------------------------------------------
    function startNewChat() {
        currentSessionId = null;
        fetch('/api/reset_context', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: 'default_user' })
        }).catch(console.error);

        // Reset chat UI with hero welcome
        chatMessages.innerHTML = '';
        if (heroWelcome) {
            chatMessages.appendChild(heroWelcome);
            heroWelcome.style.display = 'block';
        }
        quickRepliesContainer.innerHTML = '';

        if (userInput) {
            userInput.value = '';
            userInput.style.height = 'auto';
            userInput.focus();
        }

        renderSidebarHistory();
    }

    if (newChatBtn) newChatBtn.addEventListener('click', startNewChat);
    if (topNewChatBtn) topNewChatBtn.addEventListener('click', startNewChat);

    // Sidebar Toggle
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                sidebar.classList.toggle('mobile-open');
            } else {
                sidebar.classList.toggle('collapsed');
            }
        });
    }

    // Auto-resize textarea like ChatGPT
    if (userInput) {
        userInput.addEventListener('input', () => {
            userInput.style.height = 'auto';
            userInput.style.height = Math.min(userInput.scrollHeight, 150) + 'px';
        });

        // Submit on Enter (Shift+Enter for newline)
        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    }

    // Click on suggestion tiles in hero welcome
    document.querySelectorAll('.suggestion-tile').forEach(tile => {
        tile.addEventListener('click', () => {
            const prompt = tile.getAttribute('data-prompt');
            if (prompt && userInput) {
                userInput.value = prompt;
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    });

    // -------------------------------------------------------------
    // 3. SPEECH INPUT & OUTPUT
    // -------------------------------------------------------------
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-IN';

        recognition.onstart = () => {
            isListening = true;
            if (micBtn) micBtn.classList.add('text-danger');
            if (speechStatus) speechStatus.innerText = 'Listening...';
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if (userInput) userInput.value = transcript;
            if (speechStatus) speechStatus.innerText = 'Understood: "' + transcript + '"';
            setTimeout(() => {
                chatForm.dispatchEvent(new Event('submit'));
            }, 300);
        };

        recognition.onerror = () => {
            isListening = false;
            if (micBtn) micBtn.classList.remove('text-danger');
            if (speechStatus) speechStatus.innerText = '';
        };

        recognition.onend = () => {
            isListening = false;
            if (micBtn) micBtn.classList.remove('text-danger');
            setTimeout(() => { if (speechStatus) speechStatus.innerText = ''; }, 2000);
        };
    } else {
        if (micBtn) micBtn.style.display = 'none';
    }

    if (micBtn) {
        micBtn.addEventListener('click', () => {
            if (!recognition) return;
            if (isListening) recognition.stop();
            else recognition.start();
        });
    }

    // Voice UI Synchronization
    function updateVoiceToggleUI() {
        if (speechEnabled) {
            if (topVoiceToggleBtn) {
                topVoiceToggleBtn.classList.add('active');
                if (topVoiceLabel) topVoiceLabel.innerText = 'Voice: ON';
                if (topVoiceIcon) topVoiceIcon.className = 'bi bi-volume-up-fill';
            }
            if (voiceToggleBtn) {
                voiceToggleBtn.classList.add('text-primary');
                if (voiceIcon) voiceIcon.className = 'bi bi-volume-up-fill';
            }
        } else {
            if (topVoiceToggleBtn) {
                topVoiceToggleBtn.classList.remove('active');
                if (topVoiceLabel) topVoiceLabel.innerText = 'Voice: OFF';
                if (topVoiceIcon) topVoiceIcon.className = 'bi bi-volume-mute-fill';
            }
            if (voiceToggleBtn) {
                voiceToggleBtn.classList.remove('text-primary');
                if (voiceIcon) voiceIcon.className = 'bi bi-volume-mute-fill';
            }
            stopSpeaking();
        }
    }

    function toggleVoiceNarration() {
        speechEnabled = !speechEnabled;
        localStorage.setItem(VOICE_STORAGE_KEY, speechEnabled ? 'true' : 'false');
        updateVoiceToggleUI();
        if (speechEnabled) {
            speakText("AI voice narration enabled.");
        }
    }

    if (topVoiceToggleBtn) topVoiceToggleBtn.addEventListener('click', toggleVoiceNarration);
    if (voiceToggleBtn) voiceToggleBtn.addEventListener('click', toggleVoiceNarration);

    // Natural Voice Selection
    let selectedVoice = null;
    function loadVoices() {
        if (!('speechSynthesis' in window)) return;
        const voices = window.speechSynthesis.getVoices();
        if (!voices || voices.length === 0) return;
        // Priority: Natural / Fluent English voices
        selectedVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Samantha') || v.name.includes('Zira') || v.name.includes('Jenny') || v.name.includes('Guy')))
                     || voices.find(v => v.lang.startsWith('en'))
                     || voices[0];
    }

    if ('speechSynthesis' in window) {
        loadVoices();
        window.speechSynthesis.onvoiceschanged = loadVoices;
    }

    // Clean Markdown & Symbols for Natural Voice Reading
    function cleanTextForSpeech(text) {
        if (!text) return '';
        return text
            .replace(/```[\s\S]*?```/g, '')          // remove code blocks
            .replace(/`([^`]+)`/g, '$1')              // remove code tags
            .replace(/!\[.*?\]\(.*?\)/g, '')          // remove images
            .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // link text only
            .replace(/[#*_~>]/g, '')                  // remove markdown formatting
            .replace(/₹/g, ' rupees ')                // pronounce currency nicely
            .replace(/[^\w\s.,!?'"%-]/g, ' ')         // strip emojis & special icons
            .replace(/\s+/g, ' ')                     // normalize whitespace
            .trim();
    }

    let activeSpeakingButton = null;

    function stopSpeaking() {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }
        if (activeSpeakingButton) {
            activeSpeakingButton.classList.remove('speaking');
            const label = activeSpeakingButton.querySelector('.btn-speak-text');
            const icon = activeSpeakingButton.querySelector('i');
            if (label) label.innerText = 'Read Aloud';
            if (icon) icon.className = 'bi bi-volume-up';
            activeSpeakingButton = null;
        }
    }

    function speakText(text, triggerBtn = null) {
        if (!('speechSynthesis' in window)) return;

        // If user clicks the currently speaking button, stop speaking
        if (triggerBtn && triggerBtn === activeSpeakingButton && window.speechSynthesis.speaking) {
            stopSpeaking();
            return;
        }

        stopSpeaking();

        const cleaned = cleanTextForSpeech(text);
        if (!cleaned) return;

        if (triggerBtn) {
            activeSpeakingButton = triggerBtn;
            activeSpeakingButton.classList.add('speaking');
            const label = activeSpeakingButton.querySelector('.btn-speak-text');
            const icon = activeSpeakingButton.querySelector('i');
            if (label) label.innerText = 'Stop';
            if (icon) icon.className = 'bi bi-stop-circle-fill';
        }

        const utterance = new SpeechSynthesisUtterance(cleaned.substring(0, 1500));
        if (selectedVoice) {
            utterance.voice = selectedVoice;
        }
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        utterance.onend = () => {
            stopSpeaking();
        };

        utterance.onerror = (e) => {
            console.warn('SpeechSynthesis error:', e);
            stopSpeaking();
        };

        window.speechSynthesis.speak(utterance);
    }

    updateVoiceToggleUI();

    // -------------------------------------------------------------
    // 4. CHAT FORM SUBMIT & API DISPATCH
    // -------------------------------------------------------------
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = userInput.value.trim();
        if (!text) return;

        // Hide welcome hero on first message
        if (heroWelcome && heroWelcome.parentElement) {
            heroWelcome.remove();
        }

        // Get or create active session and persist user message
        const activeSession = getOrCreateActiveSession(text);
        activeSession.messages.push({ sender: 'user', text: text });
        saveChatSessions();

        // Render User Message
        appendMessage('user', text);
        userInput.value = '';
        userInput.style.height = 'auto';
        quickRepliesContainer.innerHTML = '';

        // Show typing indicator
        const typingId = showTypingIndicator();

        try {
            // Recent conversation history for multi-turn LLM reasoning
            const recentHistory = (activeSession.messages || []).slice(0, -1).slice(-6).map(m => ({
                sender: m.sender,
                text: m.text
            }));

            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    session_id: activeSession.id,
                    history: recentHistory
                })
            });

            const data = await res.json();
            removeTypingIndicator(typingId);

            if (data.status === 'success') {
                // Save bot response to session
                activeSession.messages.push({
                    sender: 'bot',
                    text: data.reply,
                    itinerary: data.itinerary,
                    recommended_destinations: data.recommended_destinations,
                    placeShowcase: data.place_showcase
                });
                saveChatSessions();

                // Render Bot Message
                const botRow = appendMessage('bot', data.reply, data.itinerary, data.recommended_destinations, data.place_showcase);

                // Render Quick Replies
                renderQuickReplies(data.quick_suggestions);

                // Auto Voice Readout (Spoken aloud by the AI)
                if (data.reply && speechEnabled) {
                    const speakBtn = botRow ? botRow.querySelector('.btn-bubble-speak') : null;
                    speakText(data.reply, speakBtn);
                }

                // Confetti on itinerary
                if (data.itinerary && window.confetti) {
                    window.confetti({ particleCount: 45, spread: 55, origin: { y: 0.85 } });
                }
            } else {
                appendMessage('bot', '⚠️ Sorry, there was an issue processing your request: ' + (data.error || 'Unknown error'));
            }
        } catch (err) {
            removeTypingIndicator(typingId);
            appendMessage('bot', '⚠️ Error contacting the travel backend. Please check server logs.');
            console.error(err);
        }
    });

    // -------------------------------------------------------------
    // 5. MESSAGE BUBBLE RENDERING
    // -------------------------------------------------------------
    function appendMessage(sender, text, itinerary = null, destinations = null, placeShowcase = null, shouldScroll = true) {
        const row = document.createElement('div');
        row.className = `message-row ${sender}-row`;

        let contentHtml = '';
        if (sender === 'user') {
            contentHtml = `
                <div class="message-bubble user-bubble">
                    <div class="message-content">${escapeHtml(text)}</div>
                </div>
            `;
        } else {
            const parsedMarkdown = marked.parse(text);
            let extraHtml = '';

            if (placeShowcase) {
                extraHtml += renderPlaceShowcaseHtml(placeShowcase);
            }

            if (itinerary) {
                extraHtml += renderItineraryCardHtml(itinerary);
            }

            if (destinations && destinations.length > 0) {
                extraHtml += renderRecommendationCardsHtml(destinations);
            }

            contentHtml = `
                <div class="bot-avatar"><i class="bi bi-compass-fill"></i></div>
                <div class="message-bubble bot-bubble">
                    <div class="message-content">${parsedMarkdown}</div>
                    ${extraHtml}
                    <div class="message-actions">
                        <button class="btn-bubble-action btn-bubble-speak" title="Read response aloud">
                            <i class="bi bi-volume-up"></i> <span class="btn-speak-text">Read Aloud</span>
                        </button>
                        <button class="btn-bubble-action btn-bubble-copy" title="Copy response to clipboard">
                            <i class="bi bi-copy"></i> <span class="btn-copy-text">Copy</span>
                        </button>
                    </div>
                </div>
            `;
        }

        row.innerHTML = contentHtml;
        chatMessages.appendChild(row);
        if (shouldScroll) {
            chatStream.scrollTop = chatStream.scrollHeight;
        }

        // Speak button on bot message
        const speakBtn = row.querySelector('.btn-bubble-speak');
        if (speakBtn) {
            speakBtn.addEventListener('click', () => {
                speakText(text, speakBtn);
            });
        }

        // Copy button on bot message
        const copyBtn = row.querySelector('.btn-bubble-copy');
        if (copyBtn) {
            copyBtn.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(text);
                    const copyText = copyBtn.querySelector('.btn-copy-text');
                    const copyIcon = copyBtn.querySelector('i');
                    if (copyText) copyText.innerText = 'Copied!';
                    if (copyIcon) copyIcon.className = 'bi bi-check2';
                    setTimeout(() => {
                        if (copyText) copyText.innerText = 'Copy';
                        if (copyIcon) copyIcon.className = 'bi bi-copy';
                    }, 2000);
                } catch (err) {
                    console.error('Clipboard copy failed:', err);
                }
            });
        }

        // Print button on itinerary card
        const printBtn = row.querySelector('.print-itinerary-btn');
        if (printBtn) {
            printBtn.addEventListener('click', () => {
                window.print();
            });
        }

        // Action buttons
        row.querySelectorAll('.rec-plan-btn, .showcase-plan-btn').forEach(b => {
            b.addEventListener('click', () => {
                const dest = b.getAttribute('data-dest');
                userInput.value = `Plan a 3-day trip to ${dest}.`;
                chatForm.dispatchEvent(new Event('submit'));
            });
        });

        return row;
    }

    function showTypingIndicator() {
        const id = 'typing_' + Date.now();
        const row = document.createElement('div');
        row.id = id;
        row.className = 'message-row bot-row';
        row.innerHTML = `
            <div class="bot-avatar"><i class="bi bi-compass-fill"></i></div>
            <div class="message-bubble bot-bubble py-2">
                <div class="d-flex align-items-center gap-2 text-muted small">
                    <div class="spinner-grow spinner-grow-sm text-success" role="status"></div>
                    <span>Thinking...</span>
                </div>
            </div>
        `;
        chatMessages.appendChild(row);
        chatStream.scrollTop = chatStream.scrollHeight;
        return id;
    }

    function removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    // -------------------------------------------------------------
    // 6. PLACE SHOWCASE & ITINERARY RENDERING
    // -------------------------------------------------------------
    function renderPlaceShowcaseHtml(p) {
        if (!p) return '';

        const heroImg = p.hero_image || 'https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1200&q=80';

        // Famous Places Around It
        let attractionsHtml = '';
        (p.attractions || []).slice(0, 4).forEach(att => {
            const img = att.image || 'https://images.unsplash.com/photo-1467269204594-9661b134dd2b?auto=format&fit=crop&w=600&q=80';
            attractionsHtml += `
                <div class="col-sm-6 mb-2">
                    <div class="attraction-photo-card">
                        <div class="attraction-img-wrap">
                            <img src="${img}" alt="${escapeHtml(att.name)}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1467269204594-9661b134dd2b?auto=format&fit=crop&w=600&q=80'">
                        </div>
                        <div class="p-2 flex-grow-1 d-flex flex-column">
                            <div class="d-flex justify-content-between align-items-start mb-1">
                                <strong class="small text-dark">${escapeHtml(att.name)}</strong>
                                <span class="badge bg-light text-primary border" style="font-size:0.65rem;">${escapeHtml(att.type || 'Sight')}</span>
                            </div>
                            <p class="text-muted mb-1" style="font-size: 0.72rem; line-height: 1.3;">${escapeHtml(att.description || '')}</p>
                            <div class="mt-auto pt-1">
                                <small class="text-warning fw-semibold" style="font-size: 0.68rem;"><i class="bi bi-clock me-1"></i>${escapeHtml(att.best_time || 'Daytime')}</small>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        // Famous Foods
        let foodsHtml = '';
        const foodList = p.famous_foods_details || [];
        if (foodList.length > 0) {
            foodList.slice(0, 3).forEach(f => {
                const fImg = f.image || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80';
                foodsHtml += `
                    <div class="col-sm-4 mb-2">
                        <div class="food-photo-card">
                            <div class="food-img-wrap">
                                <img src="${fImg}" alt="${escapeHtml(f.name)}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80'">
                            </div>
                            <div class="p-2 flex-grow-1 d-flex flex-column">
                                <strong class="text-danger small mb-1" style="font-size:0.75rem;">${escapeHtml(f.name)}</strong>
                                <p class="text-muted mb-1" style="font-size:0.7rem; line-height: 1.25;">${escapeHtml(f.description || '')}</p>
                                ${f.famous_spot ? `<small class="text-secondary fw-semibold mt-auto" style="font-size:0.65rem;"><i class="bi bi-geo-alt-fill text-danger me-1"></i>${escapeHtml(f.famous_spot)}</small>` : ''}
                            </div>
                        </div>
                    </div>
                `;
            });
        } else if (p.foods && p.foods.length > 0) {
            const chips = p.foods.map(f => `<span class="badge bg-light text-danger border me-1 mb-1 p-2">${escapeHtml(f)}</span>`).join('');
            foodsHtml = `<div class="p-2">${chips}</div>`;
        }

        // Places Around (Day Trips)
        let aroundHtml = '';
        (p.places_around || []).slice(0, 3).forEach(pa => {
            aroundHtml += `
                <div class="place-around-pill mb-1 d-flex justify-content-between align-items-center">
                    <div>
                        <strong class="small text-dark">${escapeHtml(pa.name)}</strong>
                        <div class="text-muted" style="font-size:0.72rem;">${escapeHtml(pa.desc || '')}</div>
                    </div>
                    <span class="badge bg-info-subtle text-info border">${escapeHtml(pa.distance || 'Nearby')}</span>
                </div>
            `;
        });

        return `
            <div class="place-showcase-card shadow-sm mt-3">
                <div class="place-hero-banner" style="background-image: url('${heroImg}');">
                    <div class="place-hero-overlay"></div>
                    <div class="place-hero-content">
                        <div class="d-flex justify-content-between align-items-end flex-wrap gap-2">
                            <div>
                                <span class="badge bg-primary px-2 py-1 mb-1">${escapeHtml(p.category || 'Destination')}</span>
                                <h4 class="fw-bold mb-0 text-white">${escapeHtml(p.name)}</h4>
                                <small class="text-light opacity-90"><i class="bi bi-geo-alt-fill text-danger me-1"></i>${escapeHtml(p.region || '')}</small>
                            </div>
                            <div class="text-end">
                                <span class="badge bg-warning text-dark"><i class="bi bi-sun-fill me-1"></i>${escapeHtml(p.best_season || 'October to March')}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="p-3 bg-white">
                    <div class="mb-3">
                        <h6 class="fw-bold text-dark mb-2 d-flex align-items-center gap-1">
                            <i class="bi bi-camera-fill text-primary"></i> Famous Places & Attractions in ${escapeHtml(p.name)}:
                        </h6>
                        <div class="row g-2">${attractionsHtml}</div>
                    </div>

                    <div class="mb-3 pt-2 border-top">
                        <h6 class="fw-bold text-dark mb-2 d-flex align-items-center gap-1">
                            <i class="bi bi-egg-fried text-danger"></i> Famous Food & Signature Delicacies:
                        </h6>
                        <div class="row g-2">${foodsHtml}</div>
                    </div>

                    ${(p.places_around && p.places_around.length > 0) ? `
                    <div class="mb-3 pt-2 border-top">
                        <h6 class="fw-bold text-dark mb-2 d-flex align-items-center gap-1">
                            <i class="bi bi-signpost-split-fill text-success"></i> Famous Places Around ${escapeHtml(p.name)} (Day Trips):
                        </h6>
                        <div>${aroundHtml}</div>
                    </div>` : ''}

                    <div class="d-flex justify-content-between align-items-center pt-2 border-top flex-wrap gap-2">
                        <div class="small text-muted">
                            <i class="bi bi-cash-coin text-warning me-1"></i> Avg Budget: ~₹${p.avg_budget_3day ? p.avg_budget_3day.toLocaleString() : '9,000'} / 3 Days
                        </div>
                        <button class="btn btn-sm btn-primary rounded-pill px-3 showcase-plan-btn" data-dest="${escapeHtml(p.name)}">
                            <i class="bi bi-calendar2-check me-1"></i> Plan Itinerary for ${escapeHtml(p.name)}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function renderItineraryCardHtml(itin) {
        let daysHtml = '';
        itin.days.forEach(d => {
            daysHtml += `
                <div class="day-timeline-card">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <strong class="text-primary">${d.title}</strong>
                        <span class="badge bg-light text-dark border">Est: ₹${d.estimated_cost}</span>
                    </div>
                    <div class="time-slot"><span class="slot-tag slot-morning">Morning</span> ${d.morning}</div>
                    <div class="time-slot"><span class="slot-tag slot-afternoon">Afternoon</span> ${d.afternoon}</div>
                    <div class="time-slot mb-0"><span class="slot-tag slot-evening">Evening</span> ${d.evening}</div>
                </div>
            `;
        });

        const foodsBadges = (itin.foods_to_try || []).slice(0, 4).map(f => `<span class="badge bg-light text-dark border me-1">${f}</span>`).join('');

        return `
            <div class="itinerary-card shadow-sm mt-3">
                <div class="itinerary-hero">
                    <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
                        <div>
                            <span class="badge bg-primary-subtle text-primary border mb-1">${itin.category}</span>
                            <h5 class="fw-bold mb-0 text-white">${itin.destination} • ${itin.duration_label}</h5>
                            <small class="text-light opacity-75">${itin.region}</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-warning text-dark fs-6">${itin.total_budget_formatted}</span>
                            <div class="small opacity-75 mt-1">${itin.tier}</div>
                        </div>
                    </div>
                </div>

                <div class="p-3 bg-white">
                    <div class="budget-breakdown-box mb-3">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <span class="small fw-bold text-dark"><i class="bi bi-pie-chart-fill text-primary me-1"></i> Budget Allocation Breakdown</span>
                            <span class="small text-muted">${itin.daily_budget_formatted}</span>
                        </div>
                        <div class="progress" style="height: 9px;">
                            <div class="progress-bar bg-primary" role="progressbar" style="width: 40%"></div>
                            <div class="progress-bar bg-success" role="progressbar" style="width: 25%"></div>
                            <div class="progress-bar bg-warning" role="progressbar" style="width: 20%"></div>
                            <div class="progress-bar bg-info" role="progressbar" style="width: 15%"></div>
                        </div>
                        <div class="d-flex justify-content-between text-muted small mt-1" style="font-size:0.72rem;">
                            <span>Stay: ₹${itin.budget_breakdown.stay}</span>
                            <span>Food: ₹${itin.budget_breakdown.food}</span>
                            <span>Sightseeing: ₹${itin.budget_breakdown.activities_entry}</span>
                            <span>Transit: ₹${itin.budget_breakdown.local_commute}</span>
                        </div>
                    </div>

                    <h6 class="fw-bold text-dark mb-2"><i class="bi bi-calendar-week-fill text-primary me-1"></i> Day-Wise Itinerary Plan</h6>
                    ${daysHtml}

                    <div class="mt-2 pt-2 border-top">
                        <small class="text-muted fw-bold d-block mb-1"><i class="bi bi-cup-hot-fill text-danger me-1"></i> Recommended Local Food:</small>
                        <div class="d-flex flex-wrap">${foodsBadges}</div>
                    </div>

                    <div class="d-flex justify-content-between align-items-center mt-3 pt-2 border-top">
                        <small class="text-muted"><i class="bi bi-clock-history me-1"></i> Best Season: ${itin.best_season}</small>
                        <button class="btn btn-sm btn-outline-primary print-itinerary-btn">
                            <i class="bi bi-printer-fill me-1"></i> Print / Save Plan
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function renderRecommendationCardsHtml(dests) {
        let cards = '';
        dests.forEach(d => {
            cards += `
                <div class="col-sm-6 mb-2">
                    <div class="p-2 border rounded-3 bg-light h-100 d-flex flex-column">
                        <div class="d-flex justify-content-between">
                            <strong>${d.name}</strong>
                            <span class="badge bg-warning text-dark">₹${d.min_budget_per_day}/day</span>
                        </div>
                        <small class="text-muted mb-2">${d.tagline}</small>
                        <button class="btn btn-sm btn-primary mt-auto rec-plan-btn" data-dest="${d.name}">
                            Plan Trip to ${d.name}
                        </button>
                    </div>
                </div>
            `;
        });
        return `<div class="row g-2 mt-2">${cards}</div>`;
    }

    function renderQuickReplies(suggestions) {
        quickRepliesContainer.innerHTML = '';
        if (!suggestions || suggestions.length === 0) return;

        suggestions.forEach(s => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'quick-reply-pill';
            btn.innerText = s;
            btn.addEventListener('click', () => {
                userInput.value = s;
                chatForm.dispatchEvent(new Event('submit'));
            });
            quickRepliesContainer.appendChild(btn);
        });
    }

    function escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.toString().replace(/[&<>"']/g, m => map[m]);
    }

    // Initial render of chat history from localStorage
    renderSidebarHistory();

    // If there is an existing session, load the most recent one; otherwise show hero
    if (chatSessions && chatSessions.length > 0) {
        loadSession(chatSessions[0].id);
    } else {
        startNewChat();
    }
});
