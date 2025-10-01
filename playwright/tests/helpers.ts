import type { Page } from '@playwright/test';

const CLIPBOARD_PROP = '__playwrightClipboardText';

type TokenOptions = {
  readerToken?: string | null;
  maintainerToken?: string | null;
};

export async function bootstrapSession(page: Page, options: TokenOptions = {}): Promise<void> {
  const { readerToken = null, maintainerToken = null } = options;

  await page.addInitScript(
    ({ readerToken: reader, maintainerToken: maintainer, CLIPBOARD_PROP: prop }) => {
      if (reader) {
        window.sessionStorage.setItem('dm.readerToken', reader);
      }
      if (maintainer) {
        window.sessionStorage.setItem('dm.maintainerToken', maintainer);
      }

      (window as unknown as { [key: string]: unknown })[prop] = '';

      const nav = navigator as Navigator & {
        clipboard?: {
          writeText: (text: string) => Promise<void>;
          readText?: () => Promise<string>;
        };
      };

      type ClipboardShim = {
        writeText: (text: string) => Promise<void>;
        readText: () => Promise<string>;
      };

      const shim: ClipboardShim = {
        writeText: async (text: string) => {
          (window as unknown as { [key: string]: unknown })[prop] = text;
        },
        readText: async () => {
          const value = (window as unknown as { [key: string]: unknown })[prop];
          return typeof value === 'string' ? value : '';
        },
      };

      if (nav.clipboard) {
        nav.clipboard.writeText = shim.writeText;
        if (nav.clipboard.readText) {
          nav.clipboard.readText = shim.readText;
        } else {
          Object.defineProperty(nav.clipboard, 'readText', {
            configurable: true,
            get: () => shim.readText,
          });
        }
      } else {
        Object.defineProperty(nav, 'clipboard', {
          configurable: true,
          get: () => shim,
        });
      }
    },
    { readerToken, maintainerToken, CLIPBOARD_PROP },
  );
}

export async function setSessionTokens(page: Page, options: TokenOptions): Promise<void> {
  const { readerToken = null, maintainerToken = null } = options;
  await page.evaluate(
    ({ readerToken: reader, maintainerToken: maintainer }) => {
      if (reader) {
        window.sessionStorage.setItem('dm.readerToken', reader);
      } else {
        window.sessionStorage.removeItem('dm.readerToken');
      }
      if (maintainer) {
        window.sessionStorage.setItem('dm.maintainerToken', maintainer);
      } else {
        window.sessionStorage.removeItem('dm.maintainerToken');
      }
    },
    { readerToken, maintainerToken },
  );
}

export async function readClipboard(page: Page): Promise<string> {
  return page.evaluate<string>((prop) => {
    const value = (window as unknown as { [key: string]: unknown })[prop];
    return typeof value === 'string' ? value : '';
  }, CLIPBOARD_PROP);
}
