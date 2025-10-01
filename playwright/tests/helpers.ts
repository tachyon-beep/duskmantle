import type { Page } from '@playwright/test';

const CLIPBOARD_PROP = '__playwrightClipboardText';

type BrowserGlobals = typeof globalThis & {
  sessionStorage: Storage;
} & Record<string, unknown>;

type TokenOptions = {
  readerToken?: string | null;
  maintainerToken?: string | null;
};

export async function bootstrapSession(page: Page, options: TokenOptions = {}): Promise<void> {
  const { readerToken = null, maintainerToken = null } = options;

  await page.addInitScript(
    ({
      readerToken: reader,
      maintainerToken: maintainer,
      CLIPBOARD_PROP: prop,
    }: {
      readerToken: string | null;
      maintainerToken: string | null;
      CLIPBOARD_PROP: string;
    }) => {
      const globals = globalThis as BrowserGlobals;

      if (reader) {
        globals.sessionStorage.setItem('dm.readerToken', reader);
      }
      if (maintainer) {
        globals.sessionStorage.setItem('dm.maintainerToken', maintainer);
      }

      globals[prop] = '';

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
        writeText: (text: string) => {
          globals[prop] = text;
          return Promise.resolve();
        },
        readText: () => {
          const entry = globals[prop];
          return Promise.resolve(typeof entry === 'string' ? entry : '');
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
    ({ readerToken: reader, maintainerToken: maintainer }: { readerToken: string | null; maintainerToken: string | null }) => {
      const globals = globalThis as BrowserGlobals;

      if (reader) {
        globals.sessionStorage.setItem('dm.readerToken', reader);
      } else {
        globals.sessionStorage.removeItem('dm.readerToken');
      }
      if (maintainer) {
        globals.sessionStorage.setItem('dm.maintainerToken', maintainer);
      } else {
        globals.sessionStorage.removeItem('dm.maintainerToken');
      }
    },
    { readerToken, maintainerToken },
  );
}

export async function readClipboard(page: Page): Promise<string> {
  return page.evaluate<string, string>((prop) => {
    const globals = globalThis as BrowserGlobals;
    const entry = globals[prop];
    return typeof entry === 'string' ? entry : '';
  }, CLIPBOARD_PROP);
}
