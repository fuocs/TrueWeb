const LOCALHOST_URL = 'http://127.0.0.1:38999'; // change port if needed
const LOCALHOST_TOKEN = 'dev-token';            // set a stronger shared secret
const ENABLE_FORWARD_TO_APP = true;             // set false to disable hand-off

// Utility: run a function inside the page (all frames), return first non-null
async function getLinkFromAllFrames(tabId) {
	const [{ result: tabUrl }] = await chrome.scripting.executeScript({
		target: { tabId, allFrames: false },
		func: () => location.href
	});

	// Ask every frame for its current link under cursor
	const results = await chrome.scripting.executeScript({
		target: { tabId, allFrames: true },
		func: () => {
			// Read value set by content.js
			return {
				href: globalThis.__linkUnderCursor ?? null,
				// Provide some extras for debugging/telemetry if needed
				title: globalThis.__linkUnderCursorTitle ?? null,
				frameHref: location.href
			};
		}
	});

	for (const r of results) {
		if (r?.result?.href) return r.result;
	}
	return { href: null, frameHref: tabUrl };
}

function notify(message) {
	chrome.notifications.create({
		type: 'basic',
		iconUrl: 'icons/icon128.png',
		title: 'Link Under Cursor',
		message
	});
}

async function handleCopy(tab) {
	if (!tab?.id) return;
	const info = await getLinkFromAllFrames(tab.id);
	const href = info?.href;
	if (href) {
		if (ENABLE_FORWARD_TO_APP) {
			await handOffToLocalhost(href);
		} else {
			notify('Copied to clipboard:' + href);
		}
	} else {
		notify('No link detected under the cursor. Hover a link and try again.');
	}
}

chrome.commands.onCommand.addListener(async (command, tab) => {
	if (command === 'copy-link-under-cursor') {
		const [active] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
		await handleCopy(active);
	}
});

async function handOffToLocalhost(href) {
	try {
		// Create AbortController for timeout
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
		
		const res = await fetch(`${LOCALHOST_URL}/download`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-Auth': LOCALHOST_TOKEN
			},
			body: JSON.stringify({ url: href }),
			signal: controller.signal
		});
		
		clearTimeout(timeoutId);
		
		if (!res.ok) {
			// Handle duplicate URL (409 Conflict)
			if (res.status === 409) {
				const data = await res.json().catch(() => ({}));
				notify(data.message || 'This link has already been analyzed!');
				return;
			}
			throw new Error(`HTTP ${res.status}`);
		}
		const data = await res.json().catch(() => ({}));
		notify(`Sent to app: ${data.message || href}`);
	} catch (e) {
		if (e.name === 'AbortError') {
			notify('Connection timeout - Make sure TrueWeb app is running!');
		} else {
			notify(`App not reachable: ${String(e).slice(0, 100)}\n\nMake sure TrueWeb is running.`);
		}
	}
}

chrome.runtime.onInstalled.addListener(() => {
	chrome.contextMenus.create({
		id: "scan-link-trueweb",
		title: "Scan this link with TrueWeb",
		contexts: ["link", "page", "selection"]
	});
});

// 2. Xử lý khi người dùng bấm vào menu
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
	if (info.menuItemId === "scan-link-trueweb") {
		
		// ƯU TIÊN 1: Nếu Chrome nhận diện được đó là Link chuẩn (thẻ <a>)
		if (info.linkUrl) {
			if (ENABLE_FORWARD_TO_APP) {
				await handOffToLocalhost(info.linkUrl);
			} else {
				notify('Detected Link: ' + info.linkUrl);
			}
		} 
		// ƯU TIÊN 2: Nếu là Text bôi đen (người dùng bôi đen link text)
		else if (info.selectionText && /^https?:\/\//.test(info.selectionText)) {
			 if (ENABLE_FORWARD_TO_APP) {
				await handOffToLocalhost(info.selectionText.trim());
			}
		}
		// ƯU TIÊN 3: Fallback về logic "Link Under Cursor" cũ của bạn
		// (Dùng cho trường hợp thẻ data-href hoặc cấu trúc dị mà Chrome không bắt được)
		else {
			await handleCopy(tab);
		}
	}
});
