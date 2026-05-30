(function() {
	// DOM elements
	const toggleSettingsBtn = document.getElementById('toggleSettings');
	const settingsPanel = document.getElementById('settingsPanel');
	const messagesContainer = document.getElementById('messages-container');
	const messageInput = document.getElementById('message-input');
	const sendButton = document.getElementById('send-button');
	const newChatBtn = document.getElementById('newChatBtn');
	const testBtn = document.getElementById('testConnectionBtn');
	const errorBanner = document.getElementById('errorBanner');
	const errorText = document.getElementById('errorText');
	const typingIndicator = document.getElementById('typingIndicator');

	// settings inputs
	const serverUrlInput = document.getElementById('serverUrl');
	const modelNameInput = document.getElementById('modelName');
	const apiKeyInput = document.getElementById('apiKey');

	// conversation state
	let messages = [];  // array of { role, content }
	let abortController = null;  // for stopping ongoing stream

	// load any saved settings from localStorage
	function loadSettings() {
		const savedUrl = localStorage.getItem('lm_server_url');
		if (savedUrl) serverUrlInput.value = savedUrl;
		const savedModel = localStorage.getItem('lm_model');
		if (savedModel) modelNameInput.value = savedModel;
		const savedKey = localStorage.getItem('lm_api_key');
		if (savedKey) apiKeyInput.value = savedKey;
	}
	loadSettings();

	// save settings when changed (simple)
	function saveSettings() {
		localStorage.setItem('lm_server_url', serverUrlInput.value.trim());
		localStorage.setItem('lm_model', modelNameInput.value.trim());
		localStorage.setItem('lm_api_key', apiKeyInput.value.trim());
	}

	serverUrlInput.addEventListener('change', saveSettings);
	modelNameInput.addEventListener('change', saveSettings);
	apiKeyInput.addEventListener('change', saveSettings);

	// toggle settings panel
	toggleSettingsBtn.addEventListener('click', () => {
		settingsPanel.classList.toggle('visible');
	});

	// new conversation
	newChatBtn.addEventListener('click', () => {
		if (abortController) {
			abortController.abort();
			abortController = null;
		}
		messages = [];
		messagesContainer.innerHTML = '';
		hideError();
		enableSendButton(true);
	});

	// test connection (simple non-streaming call to check reachability)
	testBtn.addEventListener('click', async () => {
		const baseUrl = serverUrlInput.value.trim();
		if (!baseUrl) {
			showError('Please enter server URL');
			return;
		}
		try {
			showError(null); // hide any old error
			const testEndpoint = baseUrl.replace(/\/+$/, '') + '/v1/models';  // OpenAI compatible models endpoint
			const response = await fetch(testEndpoint, {
				method: 'GET',
				mode: 'cors',
				headers: {
					'Accept': 'application/json',
					...(apiKeyInput.value.trim() && { 'Authorization': `Bearer ${apiKeyInput.value.trim()}` })
				}
			});
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}
			const data = await response.json();
			// show quick success
			showTemporaryMessage('✅ Connection successful! Models: ' + (data.data ? data.data.map(m => m.id).join(', ') : 'n/a'));
		} catch (err) {
			showError('Connection failed: ' + err.message + ' — check URL, CORS, and ensure LM Studio is running.');
		}
	});

	// show a temporary info message in the chat area (like a system notification)
	function showTemporaryMessage(text) {
		const msgDiv = document.createElement('div');
		msgDiv.style.backgroundColor = '#e0f2e0';
		msgDiv.style.padding = '10px 16px';
		msgDiv.style.borderRadius = '20px';
		msgDiv.style.margin = '8px 16px';
		msgDiv.style.alignSelf = 'center';
		msgDiv.style.fontSize = '0.9rem';
		msgDiv.style.color = '#1e4a1e';
		msgDiv.style.border = '1px solid #a5d6a5';
		msgDiv.innerText = text;
		messagesContainer.appendChild(msgDiv);
		setTimeout(() => msgDiv.remove(), 5000);
	}

	function appendMessageToDOM(role, content) {
		const messageDiv = document.createElement('div');
		messageDiv.classList.add('message', role);

		const senderDiv = document.createElement('div');
		senderDiv.classList.add('sender');
		senderDiv.innerText = role === 'user' ? 'You' : 'Assistant';
		messageDiv.appendChild(senderDiv);

		const bubbleDiv = document.createElement('div');
		bubbleDiv.classList.add('bubble');
		// simple line break handling
		bubbleDiv.innerText = content;
		messageDiv.appendChild(bubbleDiv);

		messagesContainer.appendChild(messageDiv);
		scrollToBottom();
	}

	function scrollToBottom() {
		messagesContainer.scrollTop = messagesContainer.scrollHeight;
	}

	function showError(msg) {
		if (msg) {
			errorText.innerText = msg;
			errorBanner.style.display = 'flex';
		} else {
			errorBanner.style.display = 'none';
		}
	}

	function hideError() { errorBanner.style.display = 'none'; }

	function enableSendButton(enable) {
		sendButton.disabled = !enable;
	}

	// handle sending message
	async function sendMessage() {
		const userText = messageInput.value.trim();
		if (!userText) return;

		// add user message to state and UI
		messages.push({ role: 'user', content: userText });
		appendMessageToDOM('user', userText);
		messageInput.value = '';
		messageInput.style.height = 'auto';
		enableSendButton(false);
		hideError();

		// show typing indicator
		typingIndicator.style.display = 'flex';
		scrollToBottom();

		// prepare for streaming
		const baseUrl = serverUrlInput.value.trim();
		const model = modelNameInput.value.trim() || 'local-model';
		const apiKey = apiKeyInput.value.trim();

		if (!baseUrl) {
			showError('Server URL is missing. Set it in settings.');
			typingIndicator.style.display = 'none';
			enableSendButton(true);
			return;
		}

		const endpoint = baseUrl.replace(/\/+$/, '') + '/v1/chat/completions';

		// Prepare request messages (including conversation history)
		const requestMessages = messages.map(m => ({ role: m.role, content: m.content }));

		const requestBody = {
			model: model,
			messages: requestMessages,
			stream: true,
			temperature: 0.7,
			max_tokens: -1,  // let LM Studio decide (or omit)
		};

		// abort previous stream if any
		if (abortController) {
			abortController.abort();
		}
		abortController = new AbortController();

		// temporary variable for accumulating assistant reply
		let assistantReply = '';
		let assistantBubble = null; // we'll update the same DOM element

		try {
			const response = await fetch(endpoint, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Accept': 'text/event-stream',
					...(apiKey && { 'Authorization': `Bearer ${apiKey}` })
				},
				body: JSON.stringify(requestBody),
				signal: abortController.signal,
				mode: 'cors', // attempt CORS
			});

			if (!response.ok) {
				let errorDetail = '';
				try {
					const errBody = await response.text();
					errorDetail = errBody.substring(0, 200);
				} catch (e) {}
				throw new Error(`HTTP ${response.status}: ${response.statusText} — ${errorDetail}`);
			}

			if (!response.body) throw new Error('ReadableStream not supported');

			const reader = response.body.getReader();
			const decoder = new TextDecoder('utf-8');
			let buffer = '';

			// read stream
			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split('\n');
				buffer = lines.pop() || ''; // keep partial line

				for (const line of lines) {
					const trimmed = line.trim();
					if (!trimmed || trimmed === 'data: [DONE]') continue;
					if (trimmed.startsWith('data: ')) {
						const jsonStr = trimmed.slice(6);
						try {
							const parsed = JSON.parse(jsonStr);
							const delta = parsed.choices?.[0]?.delta;
							if (delta && delta.content) {
								const contentPiece = delta.content;
								assistantReply += contentPiece;

								// update UI: either create new bubble or append to existing
								if (assistantBubble === null) {
									// first piece: create assistant message bubble
									const messageDiv = document.createElement('div');
									messageDiv.classList.add('message', 'assistant');
									messageDiv.setAttribute('data-msg-id', 'streaming');
									const senderDiv = document.createElement('div');
									senderDiv.classList.add('sender');
									senderDiv.innerText = 'Assistant';
									messageDiv.appendChild(senderDiv);
									const bubbleDiv = document.createElement('div');
									bubbleDiv.classList.add('bubble');
									bubbleDiv.innerText = contentPiece;
									messageDiv.appendChild(bubbleDiv);
									messagesContainer.appendChild(messageDiv);
									assistantBubble = messageDiv;
								} else {
									// update existing bubble
									const bubble = assistantBubble.querySelector('.bubble');
									bubble.innerText = assistantReply;
								}
								scrollToBottom();
							}
						} catch (e) {
							console.warn('Failed to parse JSON:', jsonStr, e);
						}
					}
				}
			}

			// after stream ends, add the full assistant message to messages array
			if (assistantReply) {
				messages.push({ role: 'assistant', content: assistantReply });
			} else {
				// if no content but stream finished without error: maybe empty response
				if (assistantBubble) {
					assistantBubble.remove(); // remove empty bubble
				}
			}

			// clean up
			typingIndicator.style.display = 'none';
			enableSendButton(true);
			abortController = null;

			// if assistantBubble exists but no content? we already handled
			// ensure scroll
			scrollToBottom();

		} catch (err) {
			if (err.name === 'AbortError') {
				console.log('Stream aborted by user');
				// if aborted, we might have partial message; decide to keep or discard
				// discard partial assistant message from UI
				if (assistantBubble) {
					assistantBubble.remove();
				}
			} else {
				console.error(err);
				showError('Request failed: ' + err.message);
			}
			typingIndicator.style.display = 'none';
			enableSendButton(true);
			abortController = null;
		}
	}

	// event listeners
	sendButton.addEventListener('click', sendMessage);

	messageInput.addEventListener('keydown', (e) => {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			if (!sendButton.disabled) sendMessage();
		}
	});

	// auto-resize textarea
	messageInput.addEventListener('input', function() {
		this.style.height = 'auto';
		this.style.height = (this.scrollHeight) + 'px';
		if (this.value.trim()) {
			// enable send button only if there's text AND not currently streaming
			if (!abortController) sendButton.disabled = false;
		} else {
			sendButton.disabled = true;
		}
	});

	// initial state: enable send button if input has text
	messageInput.dispatchEvent(new Event('input'));

	// optional: hide settings when clicking outside? not necessary.

	// clear error when user starts typing
	messageInput.addEventListener('focus', () => hideError());

	// graceful shutdown of ongoing request (if any) on page unload
	window.addEventListener('beforeunload', () => {
		if (abortController) abortController.abort();
	});

	// welcome message
	if (messages.length === 0) {
		// add a small info message from system
		const infoDiv = document.createElement('div');
		infoDiv.style.padding = '12px 18px';
		infoDiv.style.backgroundColor = '#e3f0ff';
		infoDiv.style.borderRadius = '28px';
		infoDiv.style.margin = '16px';
		infoDiv.style.textAlign = 'center';
		infoDiv.style.color = '#0a2a44';
		infoDiv.style.border = '1px solid #bbd6fb';
		infoDiv.innerText = '💬 Connect to LM Studio on your LAN. Set the correct IP in Settings, then start chatting.';
		messagesContainer.appendChild(infoDiv);
	}
})();