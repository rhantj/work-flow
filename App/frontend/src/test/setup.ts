import '@testing-library/jest-dom/vitest';

// jsdom은 scrollIntoView를 구현하지 않아 호출 시 TypeError가 발생한다.
if (typeof Element !== 'undefined' && !Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}

// jsdom은 ResizeObserver를 구현하지 않아 Radix UI 컴포넌트(예: Tooltip)가
// 렌더링될 때 ReferenceError가 발생한다.
if (typeof globalThis.ResizeObserver === 'undefined') {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}
