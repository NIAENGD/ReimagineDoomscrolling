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

// Find the composer elements
async function getComposer() {
  const textarea = await waitFor('textarea[name="prompt-textarea"]');
  return {
    textarea,
    sendButton() {
      return textarea.closest('form')?.querySelector('button[aria-label^="Send"]');
    }
  };
}

// Simulate pressing Enter
function dispatchEnter(node) {
  const evtInit = { bubbles: true, cancelable: true, key: 'Enter', code: 'Enter' };
  node.dispatchEvent(new KeyboardEvent('keydown', evtInit));
  node.dispatchEvent(new KeyboardEvent('keyup', evtInit));
}

// Send a prompt and resolve with assistant reply text
async function sendPromptInternal(promptText) {
  const { textarea, sendButton } = await getComposer();

  textarea.value = promptText;
  textarea.dispatchEvent(new InputEvent('input', { bubbles: true }));

  const btn = sendButton();
  if (btn) {
    btn.click();
  } else {
    dispatchEnter(textarea);
  }

  const thread = await waitFor('#thread');
  const existingIds = new Set(
    Array.from(thread.querySelectorAll('[data-message-author-role="assistant"]'))
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
