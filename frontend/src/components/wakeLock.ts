let wakeLock: /*WakeLockSentinel*/ any | null = null;

async function requestWakeLock() {
  try {
    // TODO: Видимо, нужно обновить TS, чтобы типы, связанные с WakeLock определялись
    const wl = await (window.navigator as any).wakeLock.request("screen");
    if (wakeLock) {
      wakeLock.release();
    }
    wakeLock = wl;
    console.log("WakeLock получен");
  } catch (err) {
    console.log("Ошибка при получении WakeLock", err);
  }
}

export function enableWakeLock() {
  if (!(window.navigator as any).wakeLock) {
    return;
  }

  requestWakeLock();

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      requestWakeLock();
    }
  });
}
