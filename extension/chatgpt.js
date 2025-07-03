/* Content script for interacting with ChatGPT web UI */

// Utility: wait for an element that exists now or in the future
function waitFor(selector, root = document, timeout = 30000) {
  return new Promise((resolve, reject) => {
    const el = root.querySelector(selector);
    if (el) return resolve(el);

    const obs = new MutationObserver(() => {
      const node = root.querySelector(selector);
      if (node) {
        obs.disconnect();
        clearTimeout(tid);
        resolve(node);
      }
    });
    obs.observe(root, { childList: true, subtree: true });

    const tid = setTimeout(() => {
      obs.disconnect();
      reject(new Error(`Timeout waiting for ${selector}`));
    }, timeout);
  });
}

async function waitAssistantReplyInternal() {
  const thread = await waitFor('[data-message-author-role="assistant"]');
  const existingIds = new Set(
    Array.from(document.querySelectorAll('[data-message-author-role="assistant"]'))
         .map(n => n.getAttribute('data-message-id'))
  );

  return new Promise((resolve, reject) => {
    const obs = new MutationObserver(muts => {
      for (const m of muts) {
        for (const n of m.addedNodes) {
          if (
            n.nodeType === 1 &&
            n.matches?.('[data-message-author-role="assistant"]') &&
            !existingIds.has(n.getAttribute('data-message-id'))
          ) {
            obs.disconnect();
            const text = n.innerText.trim();
            resolve(text);
            return;
          }
        }
      }
    });
    obs.observe(thread, { childList: true, subtree: true });

    setTimeout(() => {
      obs.disconnect();
      reject(new Error('No assistant reply observed'));
    }, 120000);
  });
}

// Locate the editable box used for composing messages.
// ChatGPT has switched from a <textarea> to a ProseMirror editor so we
// support both patterns for forwards compatibility.
async function getComposer() {
  const selector = [
    'div[contenteditable="true"].ProseMirror',
    'textarea[data-testid="prompt-textarea"]',
    'textarea[name="prompt-textarea"]',
    'textarea[data-id="prompt-textarea"]',
    'textarea[placeholder*="Ask"]'
  ].join(', ');
  const editable = document.querySelector(selector) || await waitFor(selector);
  const isTextarea = editable.tagName.toLowerCase() === 'textarea';
  return {
    node: editable,
    isTextarea,
    sendButton() {
      return editable.closest('form')?.querySelector(
        [
          'button[data-testid="send-button"]',
          'button[aria-label^="Send"]',
          'button svg[data-testid="send"]'
        ].join(', ')
      );
    }
  };
}

// Simulate pressing Enter
function dispatchEnter(node) {
  const evtInit = { bubbles: true, cancelable: true, key: 'Enter', code: 'Enter' };
  node.dispatchEvent(new KeyboardEvent('keydown', evtInit));
  node.dispatchEvent(new KeyboardEvent('keyup', evtInit));
}

// Helper to fire the sequence of events ChatGPT expects when text is inserted
function dispatchInputLikeEvents(el) {
  el.dispatchEvent(new InputEvent('input', { bubbles: true }));
  el.dispatchEvent(new Event('change', { bubbles: true }));
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// Send a prompt and resolve with assistant reply text
async function sendPromptInternal(promptText) {
  const { node, isTextarea, sendButton } = await getComposer();

  if (isTextarea) {
    node.value = promptText;
    dispatchInputLikeEvents(node);
  } else {
    if (node.querySelector('p.is-empty')) node.innerHTML = '';
    const p = document.createElement('p');
    p.textContent = promptText;
    node.appendChild(p);
    dispatchInputLikeEvents(node);
  }

  await sleep(100);

  const btn = sendButton();
  if (btn) {
    btn.click();
  } else {
    dispatchEnter(node);
  }

  const thread = await waitFor('[data-message-author-role="assistant"]');
  const existingIds = new Set(
    Array.from(document.querySelectorAll('[data-message-author-role="assistant"]'))
         .map(n => n.getAttribute('data-message-id'))
  );

  return new Promise((resolve, reject) => {
    const obs = new MutationObserver(muts => {
      for (const m of muts) {
        for (const n of m.addedNodes) {
          if (
            n.nodeType === 1 &&
            n.matches?.('[data-message-author-role="assistant"]') &&
            !existingIds.has(n.getAttribute('data-message-id'))
          ) {
            obs.disconnect();
            const text = n.innerText.trim();
            resolve(text);
            return;
          }
        }
      }
    });
    obs.observe(thread, { childList: true, subtree: true });

    setTimeout(() => {
      obs.disconnect();
      reject(new Error('No assistant reply observed'));
    }, 120000);
  });
}

// expose globally for background script
window.sendPrompt = sendPromptInternal;
window.waitAssistantReply = waitAssistantReplyInternal;
