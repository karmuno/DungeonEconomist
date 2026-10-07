/* @ds-bundle: {"format":3,"namespace":"VenturekeepDesignSystem_78126b","components":[{"name":"Badge","sourcePath":"components/data/Badge.jsx"},{"name":"Card","sourcePath":"components/data/Card.jsx"},{"name":"StatCard","sourcePath":"components/data/StatCard.jsx"},{"name":"ProgressBar","sourcePath":"components/data/StatCard.jsx"},{"name":"EmptyState","sourcePath":"components/feedback/EmptyState.jsx"},{"name":"LoadingSpinner","sourcePath":"components/feedback/EmptyState.jsx"},{"name":"Modal","sourcePath":"components/feedback/Modal.jsx"},{"name":"Notification","sourcePath":"components/feedback/Notification.jsx"},{"name":"Button","sourcePath":"components/forms/Button.jsx"},{"name":"FieldLabel","sourcePath":"components/forms/Input.jsx"},{"name":"Input","sourcePath":"components/forms/Input.jsx"},{"name":"Select","sourcePath":"components/forms/Select.jsx"},{"name":"Checkbox","sourcePath":"components/forms/Select.jsx"},{"name":"Tabs","sourcePath":"components/navigation/Tabs.jsx"},{"name":"ViewToggle","sourcePath":"components/navigation/Tabs.jsx"}],"sourceHashes":{"components/data/Badge.jsx":"9a5762d10ee5","components/data/Card.jsx":"64387a0cfb79","components/data/StatCard.jsx":"a8ef90504262","components/feedback/EmptyState.jsx":"51b2bf8b91fd","components/feedback/Modal.jsx":"2023c1c0ad3a","components/feedback/Notification.jsx":"34061dd7ecb4","components/forms/Button.jsx":"a4df9632a1f9","components/forms/Input.jsx":"150f1e5e11be","components/forms/Select.jsx":"9ae0c32d7722","components/navigation/Tabs.jsx":"b76f77e01b6c","ui_kits/venturekeep/AppShell.jsx":"f677299752eb","ui_kits/venturekeep/AuthScreens.jsx":"9d0656760d2e","ui_kits/venturekeep/DashboardScreen.jsx":"898d50a7247f","ui_kits/venturekeep/KeepScreen.jsx":"13730305275e","ui_kits/venturekeep/data.js":"5cb1eeb77049","ui_kits/venturekeep/tweaks-panel.jsx":"6591467622ed"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.VenturekeepDesignSystem_78126b = window.VenturekeepDesignSystem_78126b || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/data/Badge.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const tones = {
  success: {
    bg: 'var(--vk-green-tint)',
    fg: 'var(--vk-green)',
    bd: 'rgba(74,222,128,0.3)'
  },
  warning: {
    bg: 'var(--vk-gold-tint)',
    fg: 'var(--vk-gold)',
    bd: 'rgba(251,191,36,0.3)'
  },
  danger: {
    bg: 'var(--vk-red-tint)',
    fg: 'var(--vk-red)',
    bd: 'rgba(239,68,68,0.3)'
  },
  info: {
    bg: 'var(--vk-blue-tint)',
    fg: 'var(--vk-blue)',
    bd: 'rgba(96,165,250,0.3)'
  },
  neutral: {
    bg: 'rgba(128,128,128,0.15)',
    fg: 'var(--text-muted)',
    bd: 'transparent'
  }
};

/**
 * Uppercase pill label. Use `tone` for status (Ready/Healing/On Expedition),
 * or leave neutral for class tags (Fighter, Cleric, Dwarf…).
 */
function Badge({
  tone = 'neutral',
  style,
  children,
  ...rest
}) {
  const t = tones[tone] || tones.neutral;
  return /*#__PURE__*/React.createElement("span", _extends({
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      padding: '0.15rem 0.5rem',
      fontSize: '0.65rem',
      fontWeight: 700,
      fontFamily: 'var(--font-mono)',
      textTransform: 'uppercase',
      letterSpacing: '0.06em',
      borderRadius: 'var(--radius-sm)',
      whiteSpace: 'nowrap',
      backgroundColor: t.bg,
      color: t.fg,
      border: `1px solid ${t.bd}`,
      ...style
    }
  }, rest), children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/Badge.jsx", error: String((e && e.message) || e) }); }

// components/data/Card.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const accentColors = {
  green: 'var(--vk-green)',
  purple: 'var(--vk-purple)',
  blue: 'var(--vk-blue)'
};

/**
 * Surface container. Optional `title` renders a bottom-bordered header row
 * (with optional `actions` on the right). `accent` adds a 3px left edge bar —
 * the domain-card convention (adventurer=green, party=purple, expedition=blue).
 */
function Card({
  title,
  actions,
  accent,
  hoverable = false,
  style,
  children,
  ...rest
}) {
  const [hover, setHover] = React.useState(false);
  return /*#__PURE__*/React.createElement("div", _extends({
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      backgroundColor: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderLeft: accent ? `var(--accent-bar) solid ${accentColors[accent] || accent}` : undefined,
      borderRadius: 'var(--radius)',
      boxShadow: 'var(--shadow)',
      overflow: 'hidden',
      transition: 'background-color var(--t-fast)',
      backgroundColor: hoverable && hover ? 'var(--vk-green-wash-soft)' : 'var(--bg-card)',
      cursor: hoverable ? 'pointer' : undefined,
      ...style
    }
  }, rest), title && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0.625rem 1rem',
      borderBottom: '1px solid var(--border-color)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }
  }, /*#__PURE__*/React.createElement("h3", {
    style: {
      margin: 0,
      fontSize: '1.05rem',
      color: 'var(--vk-green)',
      fontFamily: 'var(--font-mono)',
      fontWeight: 700
    }
  }, title), actions), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: title ? '1rem' : '0.75rem 1rem'
    }
  }, children));
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/Card.jsx", error: String((e && e.message) || e) }); }

// components/data/StatCard.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Centered metric tile: big green number over an uppercase muted label. */
function StatCard({
  value,
  label,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    style: {
      backgroundColor: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius)',
      padding: '0.75rem',
      textAlign: 'center',
      ...style
    }
  }, rest), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 'var(--text-stat)',
      fontWeight: 700,
      color: 'var(--vk-green)',
      lineHeight: 1.2,
      fontFamily: 'var(--font-mono)'
    }
  }, value), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: '0.65rem',
      color: 'var(--text-muted)',
      textTransform: 'uppercase',
      letterSpacing: '0.06em',
      marginTop: '0.125rem',
      fontFamily: 'var(--font-mono)'
    }
  }, label));
}

/**
 * Thin labelled progress bar. `tone` recolors the fill (green default, blue,
 * gold). Pass `label` to overlay centered text (e.g. "Day 3/5").
 */
function ProgressBar({
  value = 0,
  max = 100,
  tone = 'green',
  label,
  height = 16,
  style,
  ...rest
}) {
  const pct = max <= 0 ? 100 : Math.min(100, Math.max(0, Math.round(value / max * 100)));
  const fills = {
    green: 'var(--vk-green-dark)',
    blue: 'var(--vk-blue)',
    gold: 'var(--vk-gold)'
  };
  return /*#__PURE__*/React.createElement("div", _extends({
    style: {
      width: '100%',
      height,
      backgroundColor: 'var(--vk-surface-3)',
      border: '1px solid var(--vk-border-soft)',
      borderRadius: 'var(--radius-xs)',
      overflow: 'hidden',
      position: 'relative',
      ...style
    }
  }, rest), /*#__PURE__*/React.createElement("div", {
    style: {
      height: '100%',
      width: pct + '%',
      backgroundColor: fills[tone] || fills.green,
      borderRadius: '2px',
      transition: 'width 0.3s ease'
    }
  }), label != null && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      inset: 0,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '0.65rem',
      fontWeight: 700,
      fontFamily: 'var(--font-mono)',
      color: 'var(--text-body)',
      pointerEvents: 'none'
    }
  }, label));
}
Object.assign(__ds_scope, { StatCard, ProgressBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/StatCard.jsx", error: String((e && e.message) || e) }); }

// components/feedback/EmptyState.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Centered empty state: a large glyph over a muted message. */
function EmptyState({
  icon = '\u2014',
  message,
  style,
  children,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem 1rem',
      textAlign: 'center',
      color: 'var(--text-muted)',
      fontFamily: 'var(--font-mono)',
      ...style
    }
  }, rest), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: '2.5rem',
      marginBottom: '0.75rem',
      opacity: 0.6,
      lineHeight: 1
    }
  }, icon), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: '0.9rem'
    }
  }, message), children);
}

/** Spinning ring + optional message. Border-top is phosphor green. */
function LoadingSpinner({
  message,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem 1rem',
      gap: '0.75rem',
      fontFamily: 'var(--font-mono)',
      ...style
    }
  }, rest), /*#__PURE__*/React.createElement("style", null, `@keyframes vk-spin{to{transform:rotate(360deg)}}`), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 32,
      height: 32,
      border: '2px solid var(--vk-border-soft)',
      borderTopColor: 'var(--vk-green)',
      borderRadius: '50%',
      animation: 'vk-spin 0.7s linear infinite'
    }
  }), message && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: '0.8rem',
      color: 'var(--vk-green)',
      opacity: 0.7
    }
  }, message));
}
Object.assign(__ds_scope, { EmptyState, LoadingSpinner });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/EmptyState.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Modal.jsx
try { (() => {
/**
 * Centered modal dialog over a 75%-black scrim. Sticky bordered header with a
 * × close button; body scrolls past 85vh. Click the scrim to close.
 */
function Modal({
  isOpen,
  title,
  onClose,
  width = 640,
  style,
  children
}) {
  if (!isOpen) return null;
  return /*#__PURE__*/React.createElement("div", {
    onClick: onClose,
    style: {
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(0,0,0,0.75)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }
  }, /*#__PURE__*/React.createElement("div", {
    onClick: e => e.stopPropagation(),
    style: {
      backgroundColor: 'var(--bg-modal)',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius)',
      boxShadow: 'var(--shadow-modal)',
      width: '90%',
      maxWidth: width,
      maxHeight: '85vh',
      overflowY: 'auto',
      fontFamily: 'var(--font-mono)',
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'sticky',
      top: 0,
      backgroundColor: 'var(--bg-modal)',
      zIndex: 1,
      padding: '0.625rem 1rem',
      borderBottom: '1px solid var(--border-color)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }
  }, /*#__PURE__*/React.createElement("h3", {
    style: {
      margin: 0,
      fontSize: '1.05rem',
      color: 'var(--vk-green)',
      fontWeight: 700
    }
  }, title), /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    "aria-label": "Close",
    style: {
      background: 'none',
      border: 'none',
      color: 'var(--text-muted)',
      cursor: 'pointer',
      fontSize: '1.25rem',
      lineHeight: 1,
      padding: 0
    }
  }, "\xD7")), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '1rem'
    }
  }, children)));
}
Object.assign(__ds_scope, { Modal });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Modal.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Notification.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const toneStyles = {
  success: {
    bg: '#052e16',
    bd: 'var(--vk-green-dim)',
    fg: 'var(--vk-green)'
  },
  error: {
    bg: '#450a0a',
    bd: '#7f1d1d',
    fg: 'var(--vk-red)'
  },
  info: {
    bg: '#0c1929',
    bd: '#1e3a5f',
    fg: 'var(--vk-blue)'
  },
  warning: {
    bg: '#422006',
    bd: '#78350f',
    fg: 'var(--vk-gold)'
  }
};

/**
 * Notification feed row (sidebar). Color-coded by `type`. Optional `action`
 * link and a × dismiss. Very small type — this is a dense activity log.
 */
function Notification({
  type = 'info',
  children,
  action,
  onAction,
  onDismiss,
  style,
  ...rest
}) {
  const t = toneStyles[type] || toneStyles.info;
  return /*#__PURE__*/React.createElement("div", _extends({
    style: {
      display: 'flex',
      alignItems: 'flex-start',
      gap: '0.25rem',
      padding: '0.25rem 0.375rem',
      borderRadius: 'var(--radius)',
      fontSize: '0.625rem',
      lineHeight: 1.3,
      fontFamily: 'var(--font-mono)',
      backgroundColor: t.bg,
      border: `1px solid ${t.bd}`,
      color: t.fg,
      ...style
    }
  }, rest), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      wordBreak: 'break-word'
    }
  }, children), action && /*#__PURE__*/React.createElement("span", {
    onClick: onAction,
    style: {
      cursor: 'pointer',
      textDecoration: 'underline',
      fontWeight: 600,
      whiteSpace: 'nowrap',
      opacity: 0.9
    }
  }, action), onDismiss && /*#__PURE__*/React.createElement("button", {
    onClick: onDismiss,
    "aria-label": "Dismiss",
    style: {
      background: 'none',
      border: 'none',
      color: 'inherit',
      cursor: 'pointer',
      fontSize: '0.875rem',
      opacity: 0.6,
      padding: 0,
      lineHeight: 1
    }
  }, "\xD7"));
}
Object.assign(__ds_scope, { Notification });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Notification.jsx", error: String((e && e.message) || e) }); }

// components/forms/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Venturekeep button. Monospace, 6px radius, mechanical 0.15s transitions.
 * Variants: primary (green fill, black text), secondary (outline), danger (red).
 */
function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  type = 'button',
  onClick,
  style,
  children,
  ...rest
}) {
  const base = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    fontFamily: 'var(--font-mono)',
    fontWeight: 600,
    border: '1px solid transparent',
    borderRadius: 'var(--radius)',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.4 : 1,
    lineHeight: 1.4,
    whiteSpace: 'nowrap',
    transition: 'background-color var(--t), border-color var(--t), opacity var(--t)'
  };
  const sizes = {
    md: {
      padding: '0.5rem 1rem',
      fontSize: '0.825rem'
    },
    sm: {
      padding: '0.25rem 0.625rem',
      fontSize: '0.75rem'
    }
  };
  const variants = {
    primary: {
      backgroundColor: 'var(--vk-green-dark)',
      color: 'var(--vk-on-green)',
      borderColor: 'var(--vk-green-dark)'
    },
    secondary: {
      backgroundColor: 'transparent',
      color: 'var(--text-secondary)',
      borderColor: 'var(--border-color)'
    },
    danger: {
      backgroundColor: 'var(--vk-red)',
      color: '#fff',
      borderColor: 'var(--vk-red)'
    }
  };
  return /*#__PURE__*/React.createElement("button", _extends({
    type: type,
    disabled: disabled,
    onClick: onClick,
    style: {
      ...base,
      ...sizes[size],
      ...variants[variant],
      ...style
    }
  }, rest), children);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Button.jsx", error: String((e && e.message) || e) }); }

// components/forms/Input.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Uppercase muted field label used above inputs and selects. */
function FieldLabel({
  children,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("label", _extends({
    style: {
      display: 'block',
      marginBottom: '0.375rem',
      fontSize: '0.8rem',
      fontWeight: 600,
      color: 'var(--text-muted)',
      textTransform: 'uppercase',
      letterSpacing: '0.04em',
      fontFamily: 'var(--font-mono)',
      ...style
    }
  }, rest), children);
}
const fieldBase = {
  width: '100%',
  padding: '0.5rem 0.75rem',
  fontFamily: 'var(--font-mono)',
  fontSize: '0.825rem',
  color: 'var(--text-body)',
  backgroundColor: 'var(--bg-input)',
  border: '1px solid var(--border-color)',
  borderRadius: 'var(--radius)',
  lineHeight: 1.5,
  outline: 'none',
  transition: 'border-color var(--t)',
  boxSizing: 'border-box'
};

/** Text input. Green focus ring. Pass `label` to render an uppercase FieldLabel. */
function Input({
  label,
  id,
  style,
  ...rest
}) {
  const [focused, setFocused] = React.useState(false);
  const input = /*#__PURE__*/React.createElement("input", _extends({
    id: id,
    style: {
      ...fieldBase,
      borderColor: focused ? 'var(--vk-green)' : 'var(--border-color)',
      boxShadow: focused ? 'var(--focus-ring)' : 'none',
      ...style
    },
    onFocus: e => {
      setFocused(true);
      rest.onFocus?.(e);
    },
    onBlur: e => {
      setFocused(false);
      rest.onBlur?.(e);
    }
  }, rest));
  if (!label) return input;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: '0.5rem'
    }
  }, /*#__PURE__*/React.createElement(FieldLabel, {
    htmlFor: id
  }, label), input);
}
Object.assign(__ds_scope, { FieldLabel, Input });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Input.jsx", error: String((e && e.message) || e) }); }

// components/forms/Select.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const caret = "url(\"data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e\")";

/** Native select styled to match Venturekeep inputs, with a custom muted caret. */
function Select({
  label,
  id,
  children,
  style,
  ...rest
}) {
  const [focused, setFocused] = React.useState(false);
  const el = /*#__PURE__*/React.createElement("select", _extends({
    id: id,
    style: {
      width: '100%',
      padding: '0.5rem 2.5rem 0.5rem 0.75rem',
      fontFamily: 'var(--font-mono)',
      fontSize: '0.825rem',
      color: 'var(--text-body)',
      backgroundColor: 'var(--bg-input)',
      border: '1px solid',
      borderColor: focused ? 'var(--vk-green)' : 'var(--border-color)',
      boxShadow: focused ? 'var(--focus-ring)' : 'none',
      borderRadius: 'var(--radius)',
      lineHeight: 1.5,
      outline: 'none',
      appearance: 'none',
      backgroundImage: caret,
      backgroundPosition: 'right 0.5rem center',
      backgroundRepeat: 'no-repeat',
      backgroundSize: '1.5em 1.5em',
      transition: 'border-color var(--t)',
      boxSizing: 'border-box',
      ...style
    },
    onFocus: e => {
      setFocused(true);
      rest.onFocus?.(e);
    },
    onBlur: e => {
      setFocused(false);
      rest.onBlur?.(e);
    }
  }, rest), children);
  if (!label) return el;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: '0.5rem'
    }
  }, /*#__PURE__*/React.createElement("label", {
    htmlFor: id,
    style: {
      display: 'block',
      marginBottom: '0.375rem',
      fontSize: '0.8rem',
      fontWeight: 600,
      color: 'var(--text-muted)',
      textTransform: 'uppercase',
      letterSpacing: '0.04em',
      fontFamily: 'var(--font-mono)'
    }
  }, label), el);
}

/** Checkbox with a green accent-color tick, inline label to the right. */
function Checkbox({
  label,
  checked,
  onChange,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("label", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.4rem',
      fontSize: '0.75rem',
      color: 'var(--text-secondary)',
      fontFamily: 'var(--font-mono)',
      cursor: 'pointer',
      ...style
    }
  }, /*#__PURE__*/React.createElement("input", _extends({
    type: "checkbox",
    checked: checked,
    onChange: onChange,
    style: {
      accentColor: 'var(--vk-green)',
      cursor: 'pointer'
    }
  }, rest)), label);
}
Object.assign(__ds_scope, { Select, Checkbox });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Select.jsx", error: String((e && e.message) || e) }); }

// components/navigation/Tabs.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Underline tab bar. `tabs` is an array of strings or {label,value}. Calls
 * `onChange(value)`; the active tab gets a green label + green underline.
 */
function Tabs({
  tabs = [],
  value,
  onChange,
  style,
  ...rest
}) {
  const items = tabs.map(t => typeof t === 'string' ? {
    label: t,
    value: t
  } : t);
  return /*#__PURE__*/React.createElement("div", _extends({
    style: {
      display: 'flex',
      borderBottom: '1px solid var(--border-color)',
      fontFamily: 'var(--font-mono)',
      ...style
    }
  }, rest), items.map(t => {
    const active = t.value === value;
    return /*#__PURE__*/React.createElement("button", {
      key: t.value,
      onClick: () => onChange?.(t.value),
      style: {
        padding: '0.375rem 1rem',
        background: 'transparent',
        border: 'none',
        borderBottom: `2px solid ${active ? 'var(--vk-green)' : 'transparent'}`,
        color: active ? 'var(--vk-green)' : 'var(--text-muted)',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.825rem',
        fontWeight: 600,
        cursor: 'pointer',
        transition: 'color var(--t), border-color var(--t)'
      }
    }, t.label);
  }));
}

/**
 * Segmented control — a bordered group of buttons; the active one fills green.
 * Use for compact view switches (table / cards).
 */
function ViewToggle({
  options = [],
  value,
  onChange,
  style,
  ...rest
}) {
  const items = options.map(o => typeof o === 'string' ? {
    label: o,
    value: o
  } : o);
  return /*#__PURE__*/React.createElement("div", _extends({
    style: {
      display: 'inline-flex',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius)',
      overflow: 'hidden',
      ...style
    }
  }, rest), items.map((o, i) => {
    const active = o.value === value;
    return /*#__PURE__*/React.createElement("button", {
      key: o.value,
      onClick: () => onChange?.(o.value),
      style: {
        padding: '0.25rem 0.625rem',
        background: active ? 'var(--vk-green-dark)' : 'transparent',
        color: active ? 'var(--vk-on-green)' : 'var(--text-muted)',
        border: 'none',
        borderRight: i < items.length - 1 ? '1px solid var(--border-color)' : 'none',
        cursor: 'pointer',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.8rem',
        transition: 'background-color var(--t), color var(--t)'
      }
    }, o.label);
  }));
}
Object.assign(__ds_scope, { Tabs, ViewToggle });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/Tabs.jsx", error: String((e && e.message) || e) }); }

// ui_kits/venturekeep/AppShell.jsx
try { (() => {
// Venturekeep app shell: fixed header + left sidebar (game day, treasury, time controls, feed)
const {
  Button,
  Notification,
  StatCard
} = window.VenturekeepDesignSystem_78126b;
function VKHeader({
  keepName,
  route,
  onNav,
  onSwitch
}) {
  const nav = [{
    key: 'dashboard',
    label: keepName || 'Keep'
  }, {
    key: 'village',
    label: 'Village'
  }, {
    key: 'tavern',
    label: 'Tavern'
  }, {
    key: 'parties',
    label: 'Parties'
  }, {
    key: 'expeditions',
    label: 'Expeditions'
  }];
  return /*#__PURE__*/React.createElement("header", {
    style: {
      height: 56,
      background: 'var(--vk-black)',
      borderBottom: '1px solid var(--border-color)',
      display: 'flex',
      alignItems: 'center',
      padding: '0 24px',
      boxSizing: 'border-box',
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 20,
      fontWeight: 700,
      color: 'var(--vk-green)',
      letterSpacing: '0.5px',
      marginRight: 'auto',
      cursor: 'pointer'
    },
    onClick: () => onNav('dashboard')
  }, "VentureKeep"), /*#__PURE__*/React.createElement("nav", {
    style: {
      display: 'flex',
      gap: 24
    }
  }, nav.map(n => /*#__PURE__*/React.createElement("a", {
    key: n.key,
    onClick: () => onNav(n.key),
    style: {
      color: route === n.key ? 'var(--vk-green)' : 'var(--text-secondary)',
      fontSize: 14,
      padding: '4px 0',
      cursor: 'pointer',
      textDecoration: 'none'
    }
  }, n.label))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      marginLeft: 24
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: onSwitch,
    style: vkHeaderBtn
  }, "Switch Keep"), /*#__PURE__*/React.createElement("button", {
    onClick: onSwitch,
    style: vkHeaderBtn
  }, "Sign Out")));
}
const vkHeaderBtn = {
  padding: '4px 12px',
  background: 'transparent',
  color: 'var(--text-muted)',
  border: '1px solid var(--border-color)',
  borderRadius: 'var(--radius)',
  fontFamily: 'var(--font-mono)',
  fontSize: 12,
  cursor: 'pointer'
};
function VKSidebar({
  day,
  gold,
  feed,
  onAdvance
}) {
  return /*#__PURE__*/React.createElement("aside", {
    style: {
      width: 260,
      background: 'var(--vk-black)',
      borderRight: '1px solid var(--border-color)',
      padding: '14px 16px',
      boxSizing: 'border-box',
      overflowY: 'auto',
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: vkSectionLabel
  }, "Game Day"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: '2rem',
      fontWeight: 700,
      color: 'var(--vk-text-1)',
      lineHeight: 1
    }
  }, day), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: '0.7rem',
      color: 'var(--vk-text-muted)'
    }
  }, window.vkGameDay(day)))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: vkSectionLabel
  }, "Treasury"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: '1.1rem',
      fontWeight: 700,
      color: 'var(--vk-green)'
    }
  }, gold, "gp")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6,
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement(Button, {
    onClick: onAdvance,
    style: {
      flex: 1
    }
  }, "Advance Day"), /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm",
    style: {
      flex: 1
    }
  }, "Skip to Event")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 3
    }
  }, feed.map((f, i) => /*#__PURE__*/React.createElement(Notification, {
    key: i,
    type: f.type,
    action: f.action,
    onAction: () => {},
    onDismiss: () => {}
  }, f.text))));
}
const vkSectionLabel = {
  fontSize: 10,
  textTransform: 'uppercase',
  letterSpacing: '1.5px',
  color: 'var(--vk-text-muted)',
  margin: '0 0 2px'
};
Object.assign(window, {
  VKHeader,
  VKSidebar
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/venturekeep/AppShell.jsx", error: String((e && e.message) || e) }); }

// ui_kits/venturekeep/AuthScreens.jsx
try { (() => {
// Venturekeep auth + keep-select screens
const {
  Button,
  Input,
  Card,
  Badge
} = window.VenturekeepDesignSystem_78126b;
function VKLogin({
  onLogin
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: 'var(--vk-black)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 400,
      width: '100%',
      textAlign: 'center'
    }
  }, /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("h1", {
    style: {
      margin: '0 0 0.375rem',
      color: 'var(--vk-green)',
      fontSize: '1.5rem'
    }
  }, "VentureKeep"), /*#__PURE__*/React.createElement("p", {
    style: {
      color: 'var(--vk-text-muted)',
      margin: '0 0 0.625rem',
      fontSize: 13
    }
  }, "Sign in to your account"), /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'left'
    }
  }, /*#__PURE__*/React.createElement(Input, {
    label: "Username",
    defaultValue: "cody"
  }), /*#__PURE__*/React.createElement(Input, {
    label: "Password",
    type: "password",
    defaultValue: "hunter2"
  })), /*#__PURE__*/React.createElement(Button, {
    onClick: onLogin,
    style: {
      width: '100%',
      marginTop: 8
    }
  }, "Sign In"), /*#__PURE__*/React.createElement("p", {
    style: {
      marginTop: 12,
      color: 'var(--vk-text-muted)',
      fontSize: 13
    }
  }, "No account? ", /*#__PURE__*/React.createElement("a", {
    onClick: onLogin,
    style: {
      color: 'var(--vk-green)',
      cursor: 'pointer'
    }
  }, "Register")))));
}
function VKKeepSelect({
  keeps,
  onSelect,
  onSignOut
}) {
  const [name, setName] = React.useState('');
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      background: 'var(--vk-black)',
      padding: 24,
      boxSizing: 'border-box'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 500,
      width: '100%'
    }
  }, /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement("h1", {
    style: {
      margin: '0 0 0.375rem',
      color: 'var(--vk-green)',
      fontSize: '1.5rem',
      textAlign: 'center'
    }
  }, "Your Keeps"), /*#__PURE__*/React.createElement("p", {
    style: {
      color: 'var(--vk-text-muted)',
      margin: '0 0 0.875rem',
      fontSize: 13,
      textAlign: 'center'
    }
  }, "Signed in as ", /*#__PURE__*/React.createElement("strong", {
    style: {
      color: 'var(--vk-text-1)'
    }
  }, "cody"), /*#__PURE__*/React.createElement("span", {
    onClick: onSignOut,
    style: {
      cursor: 'pointer',
      marginLeft: 6
    }
  }, "(sign out)")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 8,
      marginBottom: 14
    }
  }, keeps.map(k => /*#__PURE__*/React.createElement("div", {
    key: k.id,
    onClick: () => onSelect(k),
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '12px 16px',
      background: 'var(--vk-black)',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius)',
      cursor: 'pointer'
    },
    onMouseEnter: e => e.currentTarget.style.borderColor = 'var(--vk-green)',
    onMouseLeave: e => e.currentTarget.style.borderColor = 'var(--border-color)'
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 6,
      flexWrap: 'wrap'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 700,
      color: 'var(--vk-text-1)'
    }
  }, k.name), k.dungeon && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      fontStyle: 'italic',
      color: 'var(--vk-text-muted)'
    }
  }, "vs."), k.dungeon && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      fontWeight: 700,
      color: 'var(--vk-green)'
    }
  }, k.dungeon)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--vk-text-muted)',
      marginTop: 2
    }
  }, "Day ", k.day, " \xB7 ", k.gold, "gp", k.buildings.length ? ' · ' + k.buildings.join(', ') : '')), /*#__PURE__*/React.createElement("button", {
    style: {
      ...vkDeleteBtn
    }
  }, "Delete")))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Input, {
    placeholder: "New keep name (e.g. The Dragon's Rest)",
    value: name,
    onChange: e => setName(e.target.value),
    style: {
      flex: 1
    }
  }), /*#__PURE__*/React.createElement(Button, {
    onClick: () => onSelect(keeps[0]),
    disabled: !name.trim()
  }, "Create Keep")))));
}
const vkDeleteBtn = {
  background: 'none',
  border: '1px solid var(--border-color)',
  borderRadius: 'var(--radius)',
  color: 'var(--vk-text-muted)',
  fontSize: 11,
  cursor: 'pointer',
  padding: '3px 8px',
  fontFamily: 'var(--font-mono)'
};
Object.assign(window, {
  VKLogin,
  VKKeepSelect
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/venturekeep/AuthScreens.jsx", error: String((e && e.message) || e) }); }

// ui_kits/venturekeep/DashboardScreen.jsx
try { (() => {
// Venturekeep dashboard — dungeon header, active expeditions, parties + unassigned, village
const {
  Card,
  Badge,
  Button,
  ProgressBar,
  Modal
} = window.VenturekeepDesignSystem_78126b;
const statusTone = {
  Ready: 'success',
  Healing: 'warning',
  'On Expedition': 'info',
  Empty: 'neutral'
};
function AdvRow({
  a,
  onOpen
}) {
  return /*#__PURE__*/React.createElement("div", {
    onClick: () => onOpen(a),
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      padding: '3px 0',
      borderBottom: '1px solid var(--border-color)',
      fontSize: 12,
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--vk-text-muted)',
      fontSize: 12
    }
  }, "\u2630"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600,
      flex: 1,
      color: 'var(--vk-text-1)'
    }
  }, a.name), /*#__PURE__*/React.createElement(Badge, null, a.cls), /*#__PURE__*/React.createElement("span", {
    style: vkStat
  }, "Lv ", a.lv), /*#__PURE__*/React.createElement("span", {
    style: {
      ...vkStat,
      color: a.hp >= a.hpMax ? 'var(--vk-green)' : 'var(--vk-gold)'
    }
  }, a.hp, "/", a.hpMax), /*#__PURE__*/React.createElement("span", {
    style: {
      ...vkStat,
      color: 'var(--vk-blue)'
    }
  }, a.xp, "/", a.xpNext, " XP"), /*#__PURE__*/React.createElement("span", {
    style: {
      ...vkStat,
      color: 'var(--vk-gold)'
    }
  }, a.gold, "gp"));
}
const vkStat = {
  fontSize: 11,
  fontFamily: 'var(--font-mono)',
  color: 'var(--vk-text-muted)'
};
function VKDashboard({
  data,
  onLaunch
}) {
  const [openParty, setOpenParty] = React.useState(1);
  const [openBuilding, setOpenBuilding] = React.useState(null);
  const [sheet, setSheet] = React.useState(null);
  const d = data;
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'baseline',
      gap: 12,
      marginBottom: 10
    }
  }, /*#__PURE__*/React.createElement("h1", {
    style: {
      margin: 0,
      fontSize: '1.3rem',
      color: 'var(--vk-green)'
    }
  }, d.dungeon.name), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: 'var(--vk-text-muted)'
    }
  }, "Depth ", d.dungeon.depth, " reached")), /*#__PURE__*/React.createElement(Card, {
    title: "Active Expeditions",
    style: {
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 6
    }
  }, d.expeditions.map(e => /*#__PURE__*/React.createElement("div", {
    key: e.id,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      padding: '6px 0',
      borderBottom: '1px solid var(--border-color)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      minWidth: 220
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600,
      fontSize: 13,
      color: 'var(--vk-text-1)'
    }
  }, e.party), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--vk-text-muted)'
    }
  }, "Depth ", e.depth), e.decision && /*#__PURE__*/React.createElement(Badge, {
    tone: "warning"
  }, "Decision")), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement(ProgressBar, {
    value: e.elapsed,
    max: e.duration,
    tone: "blue",
    height: 6
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--vk-text-muted)',
      whiteSpace: 'nowrap'
    }
  }, "Day ", e.elapsed, "/", e.duration))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 12,
      alignItems: 'start',
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement(Card, {
    title: "Unassigned Adventurers"
  }, d.unassigned.map(a => /*#__PURE__*/React.createElement(AdvRow, {
    key: a.id,
    a: a,
    onOpen: setSheet
  }))), /*#__PURE__*/React.createElement(Card, {
    title: "Parties",
    actions: /*#__PURE__*/React.createElement(Button, {
      size: "sm"
    }, "+ New Party")
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column'
    }
  }, d.parties.map(p => {
    const open = openParty === p.id;
    const avg = p.members.length ? (p.members.reduce((s, m) => s + m.lv, 0) / 6).toFixed(1) : '—';
    return /*#__PURE__*/React.createElement("div", {
      key: p.id,
      style: {
        borderBottom: '1px solid var(--border-color)'
      }
    }, /*#__PURE__*/React.createElement("div", {
      onClick: () => setOpenParty(open ? null : p.id),
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '6px 0',
        cursor: 'pointer'
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 10,
        color: 'var(--vk-text-muted)',
        width: 14
      }
    }, open ? '\u25BC' : '\u25B6'), /*#__PURE__*/React.createElement("span", {
      style: {
        fontWeight: 600,
        fontSize: 13,
        flex: 1,
        color: 'var(--vk-text-1)'
      }
    }, p.name), /*#__PURE__*/React.createElement("span", {
      style: vkStat
    }, p.members.length, "/6"), /*#__PURE__*/React.createElement("span", {
      style: vkStat
    }, "avg Lv ", avg), /*#__PURE__*/React.createElement(Badge, {
      tone: statusTone[p.status]
    }, p.status)), open && /*#__PURE__*/React.createElement("div", {
      style: {
        padding: '4px 0 8px 22px'
      }
    }, p.members.map(m => /*#__PURE__*/React.createElement(AdvRow, {
      key: m.id,
      a: m,
      onOpen: setSheet
    })), p.members.length === 0 && /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 12,
        color: 'var(--vk-text-muted)',
        padding: '4px 0'
      }
    }, "Drop adventurers here"), /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        gap: 6,
        marginTop: 6
      }
    }, p.status !== 'On Expedition' && p.members.length > 0 && /*#__PURE__*/React.createElement(Button, {
      size: "sm",
      onClick: () => onLaunch(p)
    }, "Launch Expedition"), /*#__PURE__*/React.createElement(Button, {
      variant: "secondary",
      size: "sm"
    }, "Manage"))));
  })))), /*#__PURE__*/React.createElement(Card, {
    title: "Village",
    actions: /*#__PURE__*/React.createElement(Button, {
      variant: "secondary",
      size: "sm"
    }, "Manage")
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column'
    }
  }, d.buildings.map(b => {
    const open = openBuilding === b.type;
    return /*#__PURE__*/React.createElement("div", {
      key: b.type,
      style: {
        borderBottom: '1px solid var(--border-color)'
      }
    }, /*#__PURE__*/React.createElement("div", {
      onClick: () => setOpenBuilding(open ? null : b.type),
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        padding: '6px 0',
        cursor: 'pointer'
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 10,
        color: 'var(--vk-text-muted)',
        width: 14
      }
    }, open ? '\u25BC' : '\u25B6'), /*#__PURE__*/React.createElement("span", {
      style: {
        fontWeight: 600,
        fontSize: 13,
        flex: 1,
        color: 'var(--vk-text-1)'
      }
    }, b.name), /*#__PURE__*/React.createElement("span", {
      style: vkStat
    }, b.assigned, " assigned"), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 10,
        color: 'var(--vk-green)'
      }
    }, b.effect)), open && /*#__PURE__*/React.createElement("div", {
      style: {
        padding: '4px 0 8px 22px',
        fontSize: 12,
        color: 'var(--vk-text-muted)'
      }
    }, "Drop ", b.cls, "s here to activate bonuses"));
  }))), /*#__PURE__*/React.createElement(Modal, {
    isOpen: !!sheet,
    title: sheet?.name,
    onClose: () => setSheet(null)
  }, sheet && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: 'var(--vk-text-2)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      marginBottom: 10
    }
  }, /*#__PURE__*/React.createElement(Badge, null, sheet.cls), /*#__PURE__*/React.createElement(Badge, {
    tone: "info"
  }, "Level ", sheet.lv)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("div", null, "HP ", /*#__PURE__*/React.createElement("strong", {
    style: {
      color: 'var(--vk-green)'
    }
  }, sheet.hp, "/", sheet.hpMax)), /*#__PURE__*/React.createElement("div", null, "Gold ", /*#__PURE__*/React.createElement("strong", {
    style: {
      color: 'var(--vk-gold)'
    }
  }, sheet.gold, "gp"))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 10
    }
  }, "XP to next level"), /*#__PURE__*/React.createElement(ProgressBar, {
    value: sheet.xp,
    max: sheet.xpNext,
    label: `${sheet.xp}/${sheet.xpNext}`,
    tone: "blue",
    style: {
      marginTop: 4
    }
  }))));
}
Object.assign(window, {
  VKDashboard
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/venturekeep/DashboardScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/venturekeep/KeepScreen.jsx
try { (() => {
// Venturekeep — STREAMLINED single-canvas game view.
// One screen: a persistent world strip (clock · treasury · Advance Day) sits atop
// a roster canvas. Expeditions live INSIDE the party cards (no separate list).
// Launching is inline. Detail comes to you as a right drawer; the village is a
// pocket slide-over. No tabs, no page changes during normal play.
const {
  Button,
  Badge,
  ProgressBar,
  Card
} = window.VenturekeepDesignSystem_78126b;

// ---- density tokens (UX-first: "comfortable" loosens the terminal density for a11y) ----
const DENSITY = {
  comfortable: {
    rowPad: '11px 14px',
    rowMin: 46,
    listGap: 8,
    cardPad: 18,
    fz: 14,
    meta: 12.5,
    hgap: 16
  },
  compact: {
    rowPad: '5px 10px',
    rowMin: 30,
    listGap: 4,
    cardPad: 12,
    fz: 13,
    meta: 11,
    hgap: 10
  }
};
const CLASS_ACCENT = {
  Fighter: 'var(--vk-red)',
  Cleric: 'var(--vk-gold)',
  'Magic-User': 'var(--vk-purple)',
  Elf: 'var(--vk-green)',
  Dwarf: 'var(--vk-blue)',
  Halfling: 'var(--vk-green)'
};
const sectionLabel = {
  fontSize: 10.5,
  textTransform: 'uppercase',
  letterSpacing: '1.5px',
  color: 'var(--vk-text-muted)',
  fontWeight: 700
};

// ============================================================ world strip
function WorldStrip({
  day,
  gold,
  dens,
  keepName,
  dungeon,
  keeps,
  onSwitch,
  onAdvance,
  onVillage,
  advancing
}) {
  const [menu, setMenu] = React.useState(false);
  return /*#__PURE__*/React.createElement("header", {
    style: {
      position: 'sticky',
      top: 0,
      zIndex: 20,
      background: 'var(--vk-black)',
      borderBottom: '1px solid var(--vk-border)',
      display: 'flex',
      alignItems: 'center',
      gap: dens.hgap,
      flexWrap: 'wrap',
      padding: '12px 20px',
      boxSizing: 'border-box'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative'
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => setMenu(m => !m),
    title: "Switch keep",
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      background: 'none',
      border: 'none',
      cursor: 'pointer',
      padding: 0,
      fontFamily: 'var(--font-mono)',
      textAlign: 'left'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 19,
      fontWeight: 700,
      color: 'var(--vk-green)',
      letterSpacing: '0.5px'
    }
  }, "VentureKeep"), /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      lineHeight: 1.2
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      fontWeight: 700,
      color: 'var(--vk-text-1)'
    }
  }, keepName, " ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--vk-text-muted)',
      fontSize: 10
    }
  }, "\u25BC")), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--vk-text-muted)'
    }
  }, "vs. ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--vk-green)'
    }
  }, dungeon)))), menu && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: '110%',
      left: 0,
      minWidth: 240,
      background: 'var(--vk-surface-modal)',
      border: '1px solid var(--vk-border)',
      borderRadius: 'var(--radius)',
      boxShadow: '0 0 40px rgba(0,0,0,.8)',
      padding: 6,
      zIndex: 30
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      ...sectionLabel,
      padding: '6px 8px'
    }
  }, "Switch Keep"), keeps.map(k => /*#__PURE__*/React.createElement("button", {
    key: k.id,
    onClick: () => {
      onSwitch(k);
      setMenu(false);
    },
    style: {
      display: 'block',
      width: '100%',
      textAlign: 'left',
      background: 'none',
      border: '1px solid transparent',
      borderRadius: 4,
      cursor: 'pointer',
      padding: '8px 8px',
      fontFamily: 'var(--font-mono)',
      color: 'var(--vk-text-1)'
    },
    onMouseEnter: e => {
      e.currentTarget.style.background = 'var(--vk-green-wash)';
      e.currentTarget.style.borderColor = 'var(--vk-green-dim)';
    },
    onMouseLeave: e => {
      e.currentTarget.style.background = 'none';
      e.currentTarget.style.borderColor = 'transparent';
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 700
    }
  }, k.name), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--vk-text-muted)'
    }
  }, "Day ", k.day, " \xB7 ", k.gold, "gp"))))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'right',
      lineHeight: 1.1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: sectionLabel
  }, "Day ", day), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--vk-text-muted)'
    }
  }, window.vkGameDay(day))), /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'right',
      lineHeight: 1.1,
      minWidth: 64
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: sectionLabel
  }, "Treasury"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 18,
      fontWeight: 700,
      color: 'var(--vk-gold)'
    }
  }, gold, "gp")), /*#__PURE__*/React.createElement("button", {
    onClick: onVillage,
    title: "Village",
    style: {
      padding: '9px 14px',
      minHeight: 42,
      background: 'transparent',
      color: 'var(--vk-text-2)',
      border: '1px solid var(--vk-border)',
      borderRadius: 'var(--radius)',
      fontFamily: 'var(--font-mono)',
      fontSize: 13,
      cursor: 'pointer'
    },
    onMouseEnter: e => {
      e.currentTarget.style.borderColor = 'var(--vk-green)';
      e.currentTarget.style.color = 'var(--vk-green)';
    },
    onMouseLeave: e => {
      e.currentTarget.style.borderColor = 'var(--vk-border)';
      e.currentTarget.style.color = 'var(--vk-text-2)';
    }
  }, "\u2302 Village"), /*#__PURE__*/React.createElement(Button, {
    onClick: onAdvance,
    disabled: advancing,
    style: {
      minHeight: 42,
      fontSize: 14,
      padding: '0 18px'
    }
  }, advancing ? 'Advancing…' : 'Advance Day \u25B6'));
}

// ============================================================ event readout (the reward)
function EventReadout({
  event,
  onDismiss
}) {
  if (!event) return null;
  const tone = {
    success: 'var(--vk-green)',
    info: 'var(--vk-blue)',
    warning: 'var(--vk-gold)',
    danger: 'var(--vk-red)'
  }[event.type] || 'var(--vk-green)';
  return /*#__PURE__*/React.createElement("div", {
    role: "status",
    style: {
      border: `1px solid ${tone}`,
      borderLeft: `3px solid ${tone}`,
      background: 'var(--vk-surface-3)',
      borderRadius: 'var(--radius)',
      padding: '14px 16px',
      marginBottom: 16,
      boxShadow: '0 2px 8px rgba(0,0,0,.5)',
      display: 'flex',
      alignItems: 'flex-start',
      gap: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      ...sectionLabel,
      color: tone,
      marginBottom: 6
    }
  }, "Day ", event.day, " \xB7 ", event.heading), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 4
    }
  }, event.lines.map((l, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      fontSize: 14,
      color: 'var(--vk-text-1)'
    }
  }, l)))), /*#__PURE__*/React.createElement("button", {
    onClick: onDismiss,
    "aria-label": "Dismiss",
    style: {
      background: 'none',
      border: 'none',
      color: 'var(--vk-text-muted)',
      cursor: 'pointer',
      fontSize: 18,
      lineHeight: 1,
      padding: 4
    }
  }, "\xD7"));
}

// ============================================================ member row
function MemberRow({
  a,
  dens,
  onOpen
}) {
  const [hov, setHov] = React.useState(false);
  const lowHp = a.hp < a.hpMax;
  return /*#__PURE__*/React.createElement("div", {
    role: "button",
    tabIndex: 0,
    onClick: () => onOpen(a),
    onKeyDown: e => {
      if (e.key === 'Enter') onOpen(a);
    },
    onMouseEnter: () => setHov(true),
    onMouseLeave: () => setHov(false),
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: dens.rowPad,
      minHeight: dens.rowMin,
      borderTop: '1px solid var(--vk-border-soft)',
      cursor: 'pointer',
      boxSizing: 'border-box',
      background: hov ? 'var(--vk-green-wash-soft)' : 'transparent'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 3,
      alignSelf: 'stretch',
      borderRadius: 2,
      background: CLASS_ACCENT[a.cls] || 'var(--vk-text-muted)',
      flexShrink: 0
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600,
      flex: 1,
      color: 'var(--vk-text-1)',
      fontSize: dens.fz,
      minWidth: 120
    }
  }, a.name), /*#__PURE__*/React.createElement(Badge, null, a.cls), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: dens.meta,
      color: 'var(--vk-text-muted)',
      width: 42
    }
  }, "Lv ", a.lv), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: dens.meta,
      color: lowHp ? 'var(--vk-gold)' : 'var(--vk-green)',
      width: 56,
      textAlign: 'right'
    }
  }, a.hp, "/", a.hpMax, " HP"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: dens.meta,
      color: 'var(--vk-text-muted)'
    }
  }, "\u203A"));
}

// ============================================================ party card (timer OR inline delve, in place)
const DEPTHS = [1, 2, 3, 4];
function PartyCard({
  party,
  exp,
  dens,
  dungeon,
  onOpen,
  onLaunch
}) {
  const [open, setOpen] = React.useState(party.members.length > 0);
  const [launching, setLaunching] = React.useState(false);
  const [depth, setDepth] = React.useState(dungeon.depth);
  const delving = !!exp;
  const avg = party.members.length ? (party.members.reduce((s, m) => s + m.lv, 0) / party.members.length).toFixed(1) : '—';
  const accent = delving ? 'blue' : 'purple';
  const statusTone = delving ? 'info' : party.status === 'Healing' ? 'warning' : party.members.length ? 'success' : 'neutral';
  const statusText = delving ? 'Delving' : party.members.length === 0 ? 'Empty' : party.status;
  return /*#__PURE__*/React.createElement(Card, {
    accent: accent,
    style: {
      padding: 0,
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("div", {
    onClick: () => setOpen(o => !o),
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: dens.rowPad,
      minHeight: dens.rowMin,
      cursor: 'pointer',
      boxSizing: 'border-box'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      color: 'var(--vk-text-muted)',
      width: 12
    }
  }, open ? '\u25BC' : '\u25B6'), /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 700,
      flex: 1,
      color: 'var(--vk-text-1)',
      fontSize: dens.fz + 1
    }
  }, party.name), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: dens.meta,
      color: 'var(--vk-text-muted)'
    }
  }, party.members.length, "/6"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: dens.meta,
      color: 'var(--vk-text-muted)'
    }
  }, "avg Lv ", avg), /*#__PURE__*/React.createElement(Badge, {
    tone: statusTone
  }, statusText)), delving && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: `0 14px 12px`,
      display: 'flex',
      alignItems: 'center',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: dens.meta,
      color: 'var(--vk-blue)',
      whiteSpace: 'nowrap'
    }
  }, "Depth ", exp.depth), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement(ProgressBar, {
    value: exp.elapsed,
    max: exp.duration,
    tone: "blue",
    height: 6
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: dens.meta,
      color: 'var(--vk-text-muted)',
      whiteSpace: 'nowrap'
    }
  }, "Day ", exp.elapsed, "/", exp.duration), exp.decision && /*#__PURE__*/React.createElement(Badge, {
    tone: "warning"
  }, "Decision")), open && /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 0 4px'
    }
  }, party.members.map(m => /*#__PURE__*/React.createElement(MemberRow, {
    key: m.id,
    a: m,
    dens: dens,
    onOpen: onOpen
  })), party.members.length === 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: dens.meta,
      color: 'var(--vk-text-muted)',
      padding: dens.rowPad,
      borderTop: '1px solid var(--vk-border-soft)'
    }
  }, "Drag adventurers here to fill this party."), !delving && party.members.length > 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      borderTop: '1px solid var(--vk-border-soft)',
      padding: '10px 14px'
    }
  }, !launching ? /*#__PURE__*/React.createElement(Button, {
    size: "sm",
    onClick: () => setLaunching(true)
  }, "Send Delving") : /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      flexWrap: 'wrap'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: dens.meta,
      color: 'var(--vk-text-muted)'
    }
  }, "Target depth"), /*#__PURE__*/React.createElement("div", {
    role: "radiogroup",
    style: {
      display: 'flex',
      border: '1px solid var(--vk-border)',
      borderRadius: 'var(--radius)',
      overflow: 'hidden'
    }
  }, DEPTHS.map(dp => /*#__PURE__*/React.createElement("button", {
    key: dp,
    role: "radio",
    "aria-checked": depth === dp,
    onClick: () => setDepth(dp),
    style: {
      minWidth: 38,
      minHeight: 34,
      border: 'none',
      cursor: 'pointer',
      fontFamily: 'var(--font-mono)',
      fontSize: 13,
      background: depth === dp ? 'var(--vk-green-dark)' : 'transparent',
      color: depth === dp ? 'var(--vk-on-green)' : 'var(--vk-text-2)',
      borderRight: dp !== DEPTHS[DEPTHS.length - 1] ? '1px solid var(--vk-border)' : 'none'
    }
  }, dp))), /*#__PURE__*/React.createElement(Button, {
    size: "sm",
    onClick: () => {
      onLaunch(party, depth);
      setLaunching(false);
    }
  }, "Delve!"), /*#__PURE__*/React.createElement(Button, {
    size: "sm",
    variant: "secondary",
    onClick: () => setLaunching(false)
  }, "Cancel")))));
}

// ============================================================ character drawer (right slide-in)
function CharacterDrawer({
  a,
  dens,
  onClose
}) {
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    onClick: onClose,
    style: {
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,.6)',
      zIndex: 40,
      opacity: a ? 1 : 0,
      pointerEvents: a ? 'auto' : 'none',
      transition: 'opacity .15s'
    }
  }), /*#__PURE__*/React.createElement("aside", {
    "aria-hidden": !a,
    style: {
      position: 'fixed',
      top: 0,
      right: 0,
      height: '100%',
      width: 'min(380px, 92vw)',
      zIndex: 41,
      background: 'var(--vk-surface-modal)',
      borderLeft: '1px solid var(--vk-border)',
      boxShadow: '0 0 40px rgba(0,0,0,.8)',
      boxSizing: 'border-box',
      padding: 20,
      transform: a ? 'translateX(0)' : 'translateX(100%)',
      transition: 'transform .18s ease',
      overflowY: 'auto'
    }
  }, a && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'flex-start',
      gap: 10,
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 20,
      fontWeight: 700,
      color: 'var(--vk-text-1)'
    }
  }, a.name), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6,
      marginTop: 8
    }
  }, /*#__PURE__*/React.createElement(Badge, null, a.cls), /*#__PURE__*/React.createElement(Badge, {
    tone: "info"
  }, "Level ", a.lv))), /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    "aria-label": "Close",
    style: {
      background: 'none',
      border: 'none',
      color: 'var(--vk-text-muted)',
      fontSize: 22,
      cursor: 'pointer',
      lineHeight: 1
    }
  }, "\xD7")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 12,
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: sectionLabel
  }, "HP"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 20,
      fontWeight: 700,
      color: a.hp < a.hpMax ? 'var(--vk-gold)' : 'var(--vk-green)'
    }
  }, a.hp, "/", a.hpMax)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: sectionLabel
  }, "Purse"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 20,
      fontWeight: 700,
      color: 'var(--vk-gold)'
    }
  }, a.gold, "gp"))), /*#__PURE__*/React.createElement("div", {
    style: {
      ...sectionLabel,
      marginBottom: 6
    }
  }, "Experience"), /*#__PURE__*/React.createElement(ProgressBar, {
    value: a.xp,
    max: a.xpNext,
    label: `${a.xp}/${a.xpNext} XP`,
    tone: "blue"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 20,
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    style: {
      width: '100%'
    }
  }, "Reassign Party"), /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    style: {
      width: '100%'
    }
  }, "Send to Temple")))));
}

// ============================================================ village slide-over (rare pocket)
function VillageSheet({
  open,
  dens,
  onClose
}) {
  const d = window.VK_DATA;
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    onClick: onClose,
    style: {
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,.6)',
      zIndex: 40,
      opacity: open ? 1 : 0,
      pointerEvents: open ? 'auto' : 'none',
      transition: 'opacity .15s'
    }
  }), /*#__PURE__*/React.createElement("aside", {
    "aria-hidden": !open,
    style: {
      position: 'fixed',
      top: 0,
      right: 0,
      height: '100%',
      width: 'min(440px, 94vw)',
      zIndex: 41,
      background: 'var(--vk-surface-modal)',
      borderLeft: '1px solid var(--vk-border)',
      boxShadow: '0 0 40px rgba(0,0,0,.8)',
      boxSizing: 'border-box',
      padding: 20,
      transform: open ? 'translateX(0)' : 'translateX(100%)',
      transition: 'transform .18s ease',
      overflowY: 'auto'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: 0,
      fontSize: 18,
      color: 'var(--vk-green)',
      flex: 1
    }
  }, "Village"), /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    "aria-label": "Close",
    style: {
      background: 'none',
      border: 'none',
      color: 'var(--vk-text-muted)',
      fontSize: 22,
      cursor: 'pointer'
    }
  }, "\xD7")), /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 12.5,
      color: 'var(--vk-text-muted)',
      margin: '0 0 14px'
    }
  }, "Spend gold on buildings. Assign a matching class to unlock each bonus."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 10
    }
  }, d.buildings.map(b => /*#__PURE__*/React.createElement("div", {
    key: b.type,
    style: {
      border: '1px solid var(--vk-border)',
      borderRadius: 'var(--radius)',
      padding: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginBottom: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 700,
      flex: 1,
      color: 'var(--vk-text-1)',
      fontSize: 14
    }
  }, b.name), /*#__PURE__*/React.createElement(Badge, null, b.cls)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12.5,
      color: 'var(--vk-text-muted)',
      marginBottom: 10
    }
  }, "Unlocks ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--vk-green)'
    }
  }, b.effect), "."), b.assigned > 0 ? /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm"
  }, "+ Assign ", b.cls, " (", b.assigned, "/2)") : /*#__PURE__*/React.createElement(Button, {
    size: "sm"
  }, "Build \xB7 50gp"))))));
}

// ============================================================ orchestrator
function KeepScreen({
  keep,
  keeps,
  density,
  onSwitch
}) {
  const d = window.VK_DATA;
  const dens = DENSITY[density] || DENSITY.comfortable;
  const [day, setDay] = React.useState(keep.day);
  const [gold, setGold] = React.useState(keep.gold);
  const [sheet, setSheet] = React.useState(null);
  const [village, setVillage] = React.useState(false);
  const [event, setEvent] = React.useState(null);
  const [advancing, setAdvancing] = React.useState(false);
  // expeditions keyed by party id — source of truth for "who's out"
  const [exps, setExps] = React.useState({
    1: {
      depth: 3,
      elapsed: 3,
      duration: 5,
      decision: false
    }
  });
  function launch(party, depth) {
    const duration = 3 + depth;
    setExps(e => ({
      ...e,
      [party.id]: {
        depth,
        elapsed: 0,
        duration,
        decision: false
      }
    }));
    setEvent({
      day,
      type: 'info',
      heading: 'Expedition Begins',
      lines: [`${party.name} descended into the ${d.dungeon.name}, bound for Depth ${depth}.`]
    });
  }
  function advance() {
    setAdvancing(true);
    setTimeout(() => {
      const lines = [];
      const next = {};
      Object.entries(exps).forEach(([pid, e]) => {
        const elapsed = e.elapsed + 1;
        const party = d.parties.find(p => p.id === Number(pid));
        if (elapsed >= e.duration) {
          const haul = 40 + e.depth * 18;
          setGold(g => g + haul);
          lines.push(`${party ? party.name : 'A party'} returned from Depth ${e.depth} with ${haul}gp.`);
        } else {
          next[pid] = {
            ...e,
            elapsed
          };
        }
      });
      lines.push('Upkeep paid — 6gp deducted from the treasury.');
      setGold(g => Math.max(0, g - 6));
      setExps(next);
      setDay(dd => dd + 1);
      setEvent({
        day: day + 1,
        type: lines.length > 1 ? 'success' : 'info',
        heading: 'A Day Passes',
        lines
      });
      setAdvancing(false);
    }, 380);
  }
  return /*#__PURE__*/React.createElement("div", {
    style: {
      minHeight: '100vh',
      background: 'var(--vk-black)'
    }
  }, /*#__PURE__*/React.createElement(WorldStrip, {
    day: day,
    gold: gold,
    dens: dens,
    keepName: keep.name,
    dungeon: keep.dungeon,
    keeps: keeps,
    onSwitch: onSwitch,
    onAdvance: advance,
    onVillage: () => setVillage(true),
    advancing: advancing
  }), /*#__PURE__*/React.createElement("main", {
    style: {
      maxWidth: 860,
      margin: '0 auto',
      padding: '20px 20px 64px'
    }
  }, /*#__PURE__*/React.createElement(EventReadout, {
    event: event,
    onDismiss: () => setEvent(null)
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      ...sectionLabel,
      marginBottom: 10
    }
  }, "Parties"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    }
  }, d.parties.map(p => /*#__PURE__*/React.createElement(PartyCard, {
    key: p.id,
    party: p,
    exp: exps[p.id],
    dens: dens,
    dungeon: d.dungeon,
    onOpen: setSheet,
    onLaunch: launch
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      ...sectionLabel,
      margin: '24px 0 10px'
    }
  }, "Unassigned \xB7 ", d.unassigned.length), /*#__PURE__*/React.createElement(Card, {
    style: {
      padding: 0
    }
  }, d.unassigned.map(a => /*#__PURE__*/React.createElement(MemberRow, {
    key: a.id,
    a: a,
    dens: dens,
    onOpen: setSheet
  })))), /*#__PURE__*/React.createElement(CharacterDrawer, {
    a: sheet,
    dens: dens,
    onClose: () => setSheet(null)
  }), /*#__PURE__*/React.createElement(VillageSheet, {
    open: village,
    dens: dens,
    onClose: () => setVillage(false)
  }));
}
Object.assign(window, {
  KeepScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/venturekeep/KeepScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/venturekeep/data.js
try { (() => {
// Fake game data for the Venturekeep UI kit (cosmetic only).
const VK_DATA = {
  account: 'cody',
  keeps: [{
    id: 1,
    name: "The Dragon's Rest",
    dungeon: 'Crypt of the Mad Baron',
    day: 12,
    gold: 142,
    buildings: ['Temple', 'Smithy']
  }, {
    id: 2,
    name: 'Greywatch',
    dungeon: 'The Sunless Warrens',
    day: 3,
    gold: 8,
    buildings: []
  }],
  dungeon: {
    name: 'Crypt of the Mad Baron',
    depth: 3
  },
  expeditions: [{
    id: 11,
    party: 'The Iron Wolves',
    depth: 3,
    elapsed: 3,
    duration: 5,
    decision: false
  }, {
    id: 12,
    party: 'Ash & Ember',
    depth: 2,
    elapsed: 4,
    duration: 4,
    decision: true
  }],
  parties: [{
    id: 1,
    name: 'The Iron Wolves',
    status: 'On Expedition',
    members: [{
      id: 1,
      name: 'Borin Stonefist',
      cls: 'Dwarf',
      lv: 4,
      hp: 22,
      hpMax: 22,
      xp: 8200,
      xpNext: 12000,
      gold: 31
    }, {
      id: 2,
      name: 'Sera Lightbringer',
      cls: 'Cleric',
      lv: 3,
      hp: 14,
      hpMax: 18,
      xp: 4100,
      xpNext: 6000,
      gold: 12
    }, {
      id: 3,
      name: 'Pip Underbough',
      cls: 'Halfling',
      lv: 3,
      hp: 12,
      hpMax: 12,
      xp: 3900,
      xpNext: 6000,
      gold: 9
    }, {
      id: 4,
      name: 'Garruk the Bold',
      cls: 'Fighter',
      lv: 4,
      hp: 19,
      hpMax: 26,
      xp: 8800,
      xpNext: 12000,
      gold: 22
    }]
  }, {
    id: 2,
    name: 'Ash & Ember',
    status: 'Healing',
    members: [{
      id: 5,
      name: 'Vael Nightwhisper',
      cls: 'Elf',
      lv: 2,
      hp: 6,
      hpMax: 14,
      xp: 1400,
      xpNext: 3000,
      gold: 4
    }, {
      id: 6,
      name: 'Mordecai',
      cls: 'Magic-User',
      lv: 2,
      hp: 5,
      hpMax: 9,
      xp: 1600,
      xpNext: 3000,
      gold: 7
    }]
  }, {
    id: 3,
    name: 'The Reserves',
    status: 'Empty',
    members: []
  }],
  unassigned: [{
    id: 7,
    name: 'Tomas Quill',
    cls: 'Fighter',
    lv: 1,
    hp: 8,
    hpMax: 8,
    xp: 200,
    xpNext: 2000,
    gold: 0
  }, {
    id: 8,
    name: 'Old Henrik',
    cls: 'Cleric',
    lv: 1,
    hp: 6,
    hpMax: 6,
    xp: 120,
    xpNext: 2000,
    gold: 0
  }],
  buildings: [{
    type: 'temple',
    name: 'Temple',
    cls: 'Cleric',
    assigned: 1,
    effect: '+1 HP healed / day'
  }, {
    type: 'smithy',
    name: 'Smithy',
    cls: 'Dwarf',
    assigned: 0,
    effect: 'Craft armor'
  }, {
    type: 'library',
    name: 'Library',
    cls: 'Magic-User',
    assigned: 0,
    effect: '+10% XP gain'
  }, {
    type: 'training',
    name: 'Training Grounds',
    cls: 'Fighter',
    assigned: 0,
    effect: '+1 recruit / week'
  }],
  feed: [{
    type: 'success',
    text: 'The Iron Wolves recovered 84gp from Depth 3.',
    action: 'View Summary'
  }, {
    type: 'info',
    text: 'A Halfling arrived at the tavern.'
  }, {
    type: 'warning',
    text: 'Upkeep due — 24cp deducted from treasury.'
  }, {
    type: 'error',
    text: 'Vael Nightwhisper was wounded and is healing.'
  }]
};
const VK_CALENDAR = ['Frostmoot', 'Thawtide', 'Greentide', 'Highsun', 'Harvestmoon', 'Darkfall'];
function vkGameDay(day) {
  const m = VK_CALENDAR[Math.floor((day - 1) / 30) % VK_CALENDAR.length];
  const d = (day - 1) % 30 + 1;
  return `${m} ${d}, Yr 1`;
}
window.VK_DATA = VK_DATA;
window.vkGameDay = vkGameDay;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/venturekeep/data.js", error: String((e && e.message) || e) }); }

// ui_kits/venturekeep/tweaks-panel.jsx
try { (() => {
// @ds-adherence-ignore -- omelette starter scaffold (raw elements/hex/px by design)

/* BEGIN USAGE */
// tweaks-panel.jsx
// Reusable Tweaks shell + form-control helpers.
// Exports (to window): useTweaks, TweaksPanel, TweakSection, TweakRow, TweakSlider,
//   TweakToggle, TweakRadio, TweakSelect, TweakText, TweakNumber, TweakColor, TweakButton.
//
// Owns the host protocol (listens for __activate_edit_mode / __deactivate_edit_mode,
// posts __edit_mode_available / __edit_mode_set_keys / __edit_mode_dismissed) so
// individual prototypes don't re-roll it. Ships a consistent set of controls so you
// don't hand-draw <input type="range">, segmented radios, steppers, etc.
//
// Usage (in an HTML file that loads React + Babel):
//
//   const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
//     "primaryColor": "#D97757",
//     "palette": ["#D97757", "#29261b", "#f6f4ef"],
//     "fontSize": 16,
//     "density": "regular",
//     "dark": false
//   }/*EDITMODE-END*/;
//
//   function App() {
//     const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
//     return (
//       <div style={{ fontSize: t.fontSize, color: t.primaryColor }}>
//         Hello
//         <TweaksPanel>
//           <TweakSection label="Typography" />
//           <TweakSlider label="Font size" value={t.fontSize} min={10} max={32} unit="px"
//                        onChange={(v) => setTweak('fontSize', v)} />
//           <TweakRadio  label="Density" value={t.density}
//                        options={['compact', 'regular', 'comfy']}
//                        onChange={(v) => setTweak('density', v)} />
//           <TweakSection label="Theme" />
//           <TweakColor  label="Primary" value={t.primaryColor}
//                        options={['#D97757', '#2A6FDB', '#1F8A5B', '#7A5AE0']}
//                        onChange={(v) => setTweak('primaryColor', v)} />
//           <TweakColor  label="Palette" value={t.palette}
//                        options={[['#D97757', '#29261b', '#f6f4ef'],
//                                  ['#475569', '#0f172a', '#f1f5f9']]}
//                        onChange={(v) => setTweak('palette', v)} />
//           <TweakToggle label="Dark mode" value={t.dark}
//                        onChange={(v) => setTweak('dark', v)} />
//         </TweaksPanel>
//       </div>
//     );
//   }
//
// TweakRadio is the segmented control for 2–3 short options (auto-falls-back to
// TweakSelect past ~16/~10 chars per label); reach for TweakSelect directly when
// options are many or long. For color tweaks always curate 3-4 options rather than
// a free picker; an option can also be a whole 2–5 color palette (the stored value
// is the array). The Tweak* controls are a floor, not a ceiling — build custom
// controls inside the panel if a tweak calls for UI they don't cover.
/* END USAGE */
// ─────────────────────────────────────────────────────────────────────────────

const __TWEAKS_STYLE = `
  .twk-panel{position:fixed;right:16px;bottom:16px;z-index:2147483646;width:280px;
    max-height:calc(100vh - 32px);display:flex;flex-direction:column;
    transform:scale(var(--dc-inv-zoom,1));transform-origin:bottom right;
    background:rgba(250,249,247,.78);color:#29261b;
    -webkit-backdrop-filter:blur(24px) saturate(160%);backdrop-filter:blur(24px) saturate(160%);
    border:.5px solid rgba(255,255,255,.6);border-radius:14px;
    box-shadow:0 1px 0 rgba(255,255,255,.5) inset,0 12px 40px rgba(0,0,0,.18);
    font:11.5px/1.4 ui-sans-serif,system-ui,-apple-system,sans-serif;overflow:hidden}
  .twk-hd{display:flex;align-items:center;justify-content:space-between;
    padding:10px 8px 10px 14px;cursor:move;user-select:none}
  .twk-hd b{font-size:12px;font-weight:600;letter-spacing:.01em}
  .twk-x{appearance:none;border:0;background:transparent;color:rgba(41,38,27,.55);
    width:22px;height:22px;border-radius:6px;cursor:default;font-size:13px;line-height:1}
  .twk-x:hover{background:rgba(0,0,0,.06);color:#29261b}
  .twk-body{padding:2px 14px 14px;display:flex;flex-direction:column;gap:10px;
    overflow-y:auto;overflow-x:hidden;min-height:0;
    scrollbar-width:thin;scrollbar-color:rgba(0,0,0,.15) transparent}
  .twk-body::-webkit-scrollbar{width:8px}
  .twk-body::-webkit-scrollbar-track{background:transparent;margin:2px}
  .twk-body::-webkit-scrollbar-thumb{background:rgba(0,0,0,.15);border-radius:4px;
    border:2px solid transparent;background-clip:content-box}
  .twk-body::-webkit-scrollbar-thumb:hover{background:rgba(0,0,0,.25);
    border:2px solid transparent;background-clip:content-box}
  .twk-row{display:flex;flex-direction:column;gap:5px}
  .twk-row-h{flex-direction:row;align-items:center;justify-content:space-between;gap:10px}
  .twk-lbl{display:flex;justify-content:space-between;align-items:baseline;
    color:rgba(41,38,27,.72)}
  .twk-lbl>span:first-child{font-weight:500}
  .twk-val{color:rgba(41,38,27,.5);font-variant-numeric:tabular-nums}

  .twk-sect{font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
    color:rgba(41,38,27,.45);padding:10px 0 0}
  .twk-sect:first-child{padding-top:0}

  .twk-field{appearance:none;box-sizing:border-box;width:100%;min-width:0;height:26px;padding:0 8px;
    border:.5px solid rgba(0,0,0,.1);border-radius:7px;
    background:rgba(255,255,255,.6);color:inherit;font:inherit;outline:none}
  .twk-field:focus{border-color:rgba(0,0,0,.25);background:rgba(255,255,255,.85)}
  select.twk-field{padding-right:22px;
    background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path fill='rgba(0,0,0,.5)' d='M0 0h10L5 6z'/></svg>");
    background-repeat:no-repeat;background-position:right 8px center}

  .twk-slider{appearance:none;-webkit-appearance:none;width:100%;height:4px;margin:6px 0;
    border-radius:999px;background:rgba(0,0,0,.12);outline:none}
  .twk-slider::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;
    width:14px;height:14px;border-radius:50%;background:#fff;
    border:.5px solid rgba(0,0,0,.12);box-shadow:0 1px 3px rgba(0,0,0,.2);cursor:default}
  .twk-slider::-moz-range-thumb{width:14px;height:14px;border-radius:50%;
    background:#fff;border:.5px solid rgba(0,0,0,.12);box-shadow:0 1px 3px rgba(0,0,0,.2);cursor:default}

  .twk-seg{position:relative;display:flex;padding:2px;border-radius:8px;
    background:rgba(0,0,0,.06);user-select:none}
  .twk-seg-thumb{position:absolute;top:2px;bottom:2px;border-radius:6px;
    background:rgba(255,255,255,.9);box-shadow:0 1px 2px rgba(0,0,0,.12);
    transition:left .15s cubic-bezier(.3,.7,.4,1),width .15s}
  .twk-seg.dragging .twk-seg-thumb{transition:none}
  .twk-seg button{appearance:none;position:relative;z-index:1;flex:1;border:0;
    background:transparent;color:inherit;font:inherit;font-weight:500;min-height:22px;
    border-radius:6px;cursor:default;padding:4px 6px;line-height:1.2;
    overflow-wrap:anywhere}

  .twk-toggle{position:relative;width:32px;height:18px;border:0;border-radius:999px;
    background:rgba(0,0,0,.15);transition:background .15s;cursor:default;padding:0}
  .twk-toggle[data-on="1"]{background:#34c759}
  .twk-toggle i{position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:50%;
    background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.25);transition:transform .15s}
  .twk-toggle[data-on="1"] i{transform:translateX(14px)}

  .twk-num{display:flex;align-items:center;box-sizing:border-box;min-width:0;height:26px;padding:0 0 0 8px;
    border:.5px solid rgba(0,0,0,.1);border-radius:7px;background:rgba(255,255,255,.6)}
  .twk-num-lbl{font-weight:500;color:rgba(41,38,27,.6);cursor:ew-resize;
    user-select:none;padding-right:8px}
  .twk-num input{flex:1;min-width:0;height:100%;border:0;background:transparent;
    font:inherit;font-variant-numeric:tabular-nums;text-align:right;padding:0 8px 0 0;
    outline:none;color:inherit;-moz-appearance:textfield}
  .twk-num input::-webkit-inner-spin-button,.twk-num input::-webkit-outer-spin-button{
    -webkit-appearance:none;margin:0}
  .twk-num-unit{padding-right:8px;color:rgba(41,38,27,.45)}

  .twk-btn{appearance:none;height:26px;padding:0 12px;border:0;border-radius:7px;
    background:rgba(0,0,0,.78);color:#fff;font:inherit;font-weight:500;cursor:default}
  .twk-btn:hover{background:rgba(0,0,0,.88)}
  .twk-btn.secondary{background:rgba(0,0,0,.06);color:inherit}
  .twk-btn.secondary:hover{background:rgba(0,0,0,.1)}

  .twk-swatch{appearance:none;-webkit-appearance:none;width:56px;height:22px;
    border:.5px solid rgba(0,0,0,.1);border-radius:6px;padding:0;cursor:default;
    background:transparent;flex-shrink:0}
  .twk-swatch::-webkit-color-swatch-wrapper{padding:0}
  .twk-swatch::-webkit-color-swatch{border:0;border-radius:5.5px}
  .twk-swatch::-moz-color-swatch{border:0;border-radius:5.5px}

  .twk-chips{display:flex;gap:6px}
  .twk-chip{position:relative;appearance:none;flex:1;min-width:0;height:46px;
    padding:0;border:0;border-radius:6px;overflow:hidden;cursor:default;
    box-shadow:0 0 0 .5px rgba(0,0,0,.12),0 1px 2px rgba(0,0,0,.06);
    transition:transform .12s cubic-bezier(.3,.7,.4,1),box-shadow .12s}
  .twk-chip:hover{transform:translateY(-1px);
    box-shadow:0 0 0 .5px rgba(0,0,0,.18),0 4px 10px rgba(0,0,0,.12)}
  .twk-chip[data-on="1"]{box-shadow:0 0 0 1.5px rgba(0,0,0,.85),
    0 2px 6px rgba(0,0,0,.15)}
  .twk-chip>span{position:absolute;top:0;bottom:0;right:0;width:34%;
    display:flex;flex-direction:column;box-shadow:-1px 0 0 rgba(0,0,0,.1)}
  .twk-chip>span>i{flex:1;box-shadow:0 -1px 0 rgba(0,0,0,.1)}
  .twk-chip>span>i:first-child{box-shadow:none}
  .twk-chip svg{position:absolute;top:6px;left:6px;width:13px;height:13px;
    filter:drop-shadow(0 1px 1px rgba(0,0,0,.3))}
`;

// ── useTweaks ───────────────────────────────────────────────────────────────
// Single source of truth for tweak values. setTweak persists via the host
// (__edit_mode_set_keys → host rewrites the EDITMODE block on disk).
function useTweaks(defaults) {
  const [values, setValues] = React.useState(defaults);
  // Accepts either setTweak('key', value) or setTweak({ key: value, ... }) so a
  // useState-style call doesn't write a "[object Object]" key into the persisted
  // JSON block.
  const setTweak = React.useCallback((keyOrEdits, val) => {
    const edits = typeof keyOrEdits === 'object' && keyOrEdits !== null ? keyOrEdits : {
      [keyOrEdits]: val
    };
    setValues(prev => ({
      ...prev,
      ...edits
    }));
    window.parent.postMessage({
      type: '__edit_mode_set_keys',
      edits
    }, '*');
    // Same-window signal so in-page listeners (deck-stage rail thumbnails)
    // can react — the parent message only reaches the host, not peers.
    window.dispatchEvent(new CustomEvent('tweakchange', {
      detail: edits
    }));
  }, []);
  return [values, setTweak];
}

// ── TweaksPanel ─────────────────────────────────────────────────────────────
// Floating shell. Registers the protocol listener BEFORE announcing
// availability — if the announce ran first, the host's activate could land
// before our handler exists and the toolbar toggle would silently no-op.
// The close button posts __edit_mode_dismissed so the host's toolbar toggle
// flips off in lockstep; the host echoes __deactivate_edit_mode back which
// is what actually hides the panel.
function TweaksPanel({
  title = 'Tweaks',
  children
}) {
  const [open, setOpen] = React.useState(false);
  const dragRef = React.useRef(null);
  const offsetRef = React.useRef({
    x: 16,
    y: 16
  });
  const PAD = 16;
  const clampToViewport = React.useCallback(() => {
    const panel = dragRef.current;
    if (!panel) return;
    const w = panel.offsetWidth,
      h = panel.offsetHeight;
    const maxRight = Math.max(PAD, window.innerWidth - w - PAD);
    const maxBottom = Math.max(PAD, window.innerHeight - h - PAD);
    offsetRef.current = {
      x: Math.min(maxRight, Math.max(PAD, offsetRef.current.x)),
      y: Math.min(maxBottom, Math.max(PAD, offsetRef.current.y))
    };
    panel.style.right = offsetRef.current.x + 'px';
    panel.style.bottom = offsetRef.current.y + 'px';
  }, []);
  React.useEffect(() => {
    if (!open) return;
    clampToViewport();
    if (typeof ResizeObserver === 'undefined') {
      window.addEventListener('resize', clampToViewport);
      return () => window.removeEventListener('resize', clampToViewport);
    }
    const ro = new ResizeObserver(clampToViewport);
    ro.observe(document.documentElement);
    return () => ro.disconnect();
  }, [open, clampToViewport]);
  React.useEffect(() => {
    const onMsg = e => {
      const t = e?.data?.type;
      if (t === '__activate_edit_mode') setOpen(true);else if (t === '__deactivate_edit_mode') setOpen(false);
    };
    window.addEventListener('message', onMsg);
    window.parent.postMessage({
      type: '__edit_mode_available'
    }, '*');
    return () => window.removeEventListener('message', onMsg);
  }, []);
  const dismiss = () => {
    setOpen(false);
    window.parent.postMessage({
      type: '__edit_mode_dismissed'
    }, '*');
  };
  const onDragStart = e => {
    const panel = dragRef.current;
    if (!panel) return;
    const r = panel.getBoundingClientRect();
    const sx = e.clientX,
      sy = e.clientY;
    const startRight = window.innerWidth - r.right;
    const startBottom = window.innerHeight - r.bottom;
    const move = ev => {
      offsetRef.current = {
        x: startRight - (ev.clientX - sx),
        y: startBottom - (ev.clientY - sy)
      };
      clampToViewport();
    };
    const up = () => {
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseup', up);
    };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', up);
  };
  if (!open) return null;
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("style", null, __TWEAKS_STYLE), /*#__PURE__*/React.createElement("div", {
    ref: dragRef,
    className: "twk-panel",
    "data-omelette-chrome": "",
    style: {
      right: offsetRef.current.x,
      bottom: offsetRef.current.y
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-hd",
    onMouseDown: onDragStart
  }, /*#__PURE__*/React.createElement("b", null, title), /*#__PURE__*/React.createElement("button", {
    className: "twk-x",
    "aria-label": "Close tweaks",
    onMouseDown: e => e.stopPropagation(),
    onClick: dismiss
  }, "\u2715")), /*#__PURE__*/React.createElement("div", {
    className: "twk-body"
  }, children)));
}

// ── Layout helpers ──────────────────────────────────────────────────────────

function TweakSection({
  label,
  children
}) {
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "twk-sect"
  }, label), children);
}
function TweakRow({
  label,
  value,
  children,
  inline = false
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: inline ? 'twk-row twk-row-h' : 'twk-row'
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-lbl"
  }, /*#__PURE__*/React.createElement("span", null, label), value != null && /*#__PURE__*/React.createElement("span", {
    className: "twk-val"
  }, value)), children);
}

// ── Controls ────────────────────────────────────────────────────────────────

function TweakSlider({
  label,
  value,
  min = 0,
  max = 100,
  step = 1,
  unit = '',
  onChange
}) {
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label,
    value: `${value}${unit}`
  }, /*#__PURE__*/React.createElement("input", {
    type: "range",
    className: "twk-slider",
    min: min,
    max: max,
    step: step,
    value: value,
    onChange: e => onChange(Number(e.target.value))
  }));
}
function TweakToggle({
  label,
  value,
  onChange
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "twk-row twk-row-h"
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-lbl"
  }, /*#__PURE__*/React.createElement("span", null, label)), /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: "twk-toggle",
    "data-on": value ? '1' : '0',
    role: "switch",
    "aria-checked": !!value,
    onClick: () => onChange(!value)
  }, /*#__PURE__*/React.createElement("i", null)));
}
function TweakRadio({
  label,
  value,
  options,
  onChange
}) {
  const trackRef = React.useRef(null);
  const [dragging, setDragging] = React.useState(false);
  // The active value is read by pointer-move handlers attached for the lifetime
  // of a drag — ref it so a stale closure doesn't fire onChange for every move.
  const valueRef = React.useRef(value);
  valueRef.current = value;

  // Segments wrap mid-word once per-segment width runs out. The track is
  // ~248px (280 panel − 28 body pad − 4 seg pad), each button loses 12px
  // to its own padding, and 11.5px system-ui averages ~6.3px/char — so 2
  // options fit ~16 chars each, 3 fit ~10. Past that (or >3 options), fall
  // back to a dropdown rather than wrap.
  const labelLen = o => String(typeof o === 'object' ? o.label : o).length;
  const maxLen = options.reduce((m, o) => Math.max(m, labelLen(o)), 0);
  const fitsAsSegments = maxLen <= ({
    2: 16,
    3: 10
  }[options.length] ?? 0);
  if (!fitsAsSegments) {
    // <select> emits strings — map back to the original option value so the
    // fallback stays type-preserving (numbers, booleans) like the segment path.
    const resolve = s => {
      const m = options.find(o => String(typeof o === 'object' ? o.value : o) === s);
      return m === undefined ? s : typeof m === 'object' ? m.value : m;
    };
    return /*#__PURE__*/React.createElement(TweakSelect, {
      label: label,
      value: value,
      options: options,
      onChange: s => onChange(resolve(s))
    });
  }
  const opts = options.map(o => typeof o === 'object' ? o : {
    value: o,
    label: o
  });
  const idx = Math.max(0, opts.findIndex(o => o.value === value));
  const n = opts.length;
  const segAt = clientX => {
    const r = trackRef.current.getBoundingClientRect();
    const inner = r.width - 4;
    const i = Math.floor((clientX - r.left - 2) / inner * n);
    return opts[Math.max(0, Math.min(n - 1, i))].value;
  };
  const onPointerDown = e => {
    setDragging(true);
    const v0 = segAt(e.clientX);
    if (v0 !== valueRef.current) onChange(v0);
    const move = ev => {
      if (!trackRef.current) return;
      const v = segAt(ev.clientX);
      if (v !== valueRef.current) onChange(v);
    };
    const up = () => {
      setDragging(false);
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("div", {
    ref: trackRef,
    role: "radiogroup",
    onPointerDown: onPointerDown,
    className: dragging ? 'twk-seg dragging' : 'twk-seg'
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-seg-thumb",
    style: {
      left: `calc(2px + ${idx} * (100% - 4px) / ${n})`,
      width: `calc((100% - 4px) / ${n})`
    }
  }), opts.map(o => /*#__PURE__*/React.createElement("button", {
    key: o.value,
    type: "button",
    role: "radio",
    "aria-checked": o.value === value
  }, o.label))));
}
function TweakSelect({
  label,
  value,
  options,
  onChange
}) {
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("select", {
    className: "twk-field",
    value: value,
    onChange: e => onChange(e.target.value)
  }, options.map(o => {
    const v = typeof o === 'object' ? o.value : o;
    const l = typeof o === 'object' ? o.label : o;
    return /*#__PURE__*/React.createElement("option", {
      key: v,
      value: v
    }, l);
  })));
}
function TweakText({
  label,
  value,
  placeholder,
  onChange
}) {
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("input", {
    className: "twk-field",
    type: "text",
    value: value,
    placeholder: placeholder,
    onChange: e => onChange(e.target.value)
  }));
}
function TweakNumber({
  label,
  value,
  min,
  max,
  step = 1,
  unit = '',
  onChange
}) {
  const clamp = n => {
    if (min != null && n < min) return min;
    if (max != null && n > max) return max;
    return n;
  };
  const startRef = React.useRef({
    x: 0,
    val: 0
  });
  const onScrubStart = e => {
    e.preventDefault();
    startRef.current = {
      x: e.clientX,
      val: value
    };
    const decimals = (String(step).split('.')[1] || '').length;
    const move = ev => {
      const dx = ev.clientX - startRef.current.x;
      const raw = startRef.current.val + dx * step;
      const snapped = Math.round(raw / step) * step;
      onChange(clamp(Number(snapped.toFixed(decimals))));
    };
    const up = () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "twk-num"
  }, /*#__PURE__*/React.createElement("span", {
    className: "twk-num-lbl",
    onPointerDown: onScrubStart
  }, label), /*#__PURE__*/React.createElement("input", {
    type: "number",
    value: value,
    min: min,
    max: max,
    step: step,
    onChange: e => onChange(clamp(Number(e.target.value)))
  }), unit && /*#__PURE__*/React.createElement("span", {
    className: "twk-num-unit"
  }, unit));
}

// Relative-luminance contrast pick — checkmarks drawn over a swatch need to
// read on both #111 and #fafafa without per-option configuration. Hex input
// only (#rgb / #rrggbb); named or rgb()/hsl() colors fall through to "light".
function __twkIsLight(hex) {
  const h = String(hex).replace('#', '');
  const x = h.length === 3 ? h.replace(/./g, c => c + c) : h.padEnd(6, '0');
  const n = parseInt(x.slice(0, 6), 16);
  if (Number.isNaN(n)) return true;
  const r = n >> 16 & 255,
    g = n >> 8 & 255,
    b = n & 255;
  return r * 299 + g * 587 + b * 114 > 148000;
}
const __TwkCheck = ({
  light
}) => /*#__PURE__*/React.createElement("svg", {
  viewBox: "0 0 14 14",
  "aria-hidden": "true"
}, /*#__PURE__*/React.createElement("path", {
  d: "M3 7.2 5.8 10 11 4.2",
  fill: "none",
  strokeWidth: "2.2",
  strokeLinecap: "round",
  strokeLinejoin: "round",
  stroke: light ? 'rgba(0,0,0,.78)' : '#fff'
}));

// TweakColor — curated color/palette picker. Each option is either a single
// hex string or an array of 1-5 hex strings; the card adapts — a lone color
// renders solid, a palette renders colors[0] as the hero (left ~2/3) with the
// rest stacked in a sharp column on the right. onChange emits the
// option in the shape it was passed (string stays string, array stays array).
// Without options it falls back to the native color input for back-compat.
function TweakColor({
  label,
  value,
  options,
  onChange
}) {
  if (!options || !options.length) {
    return /*#__PURE__*/React.createElement("div", {
      className: "twk-row twk-row-h"
    }, /*#__PURE__*/React.createElement("div", {
      className: "twk-lbl"
    }, /*#__PURE__*/React.createElement("span", null, label)), /*#__PURE__*/React.createElement("input", {
      type: "color",
      className: "twk-swatch",
      value: value,
      onChange: e => onChange(e.target.value)
    }));
  }
  // Native <input type=color> emits lowercase hex per the HTML spec, so
  // compare case-insensitively. String() guards JSON.stringify(undefined),
  // which returns the primitive undefined (no .toLowerCase).
  const key = o => String(JSON.stringify(o)).toLowerCase();
  const cur = key(value);
  return /*#__PURE__*/React.createElement(TweakRow, {
    label: label
  }, /*#__PURE__*/React.createElement("div", {
    className: "twk-chips",
    role: "radiogroup"
  }, options.map((o, i) => {
    const colors = Array.isArray(o) ? o : [o];
    const [hero, ...rest] = colors;
    const sup = rest.slice(0, 4);
    const on = key(o) === cur;
    return /*#__PURE__*/React.createElement("button", {
      key: i,
      type: "button",
      className: "twk-chip",
      role: "radio",
      "aria-checked": on,
      "data-on": on ? '1' : '0',
      "aria-label": colors.join(', '),
      title: colors.join(' · '),
      style: {
        background: hero
      },
      onClick: () => onChange(o)
    }, sup.length > 0 && /*#__PURE__*/React.createElement("span", null, sup.map((c, j) => /*#__PURE__*/React.createElement("i", {
      key: j,
      style: {
        background: c
      }
    }))), on && /*#__PURE__*/React.createElement(__TwkCheck, {
      light: __twkIsLight(hero)
    }));
  })));
}
function TweakButton({
  label,
  onClick,
  secondary = false
}) {
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    className: secondary ? 'twk-btn secondary' : 'twk-btn',
    onClick: onClick
  }, label);
}
Object.assign(window, {
  useTweaks,
  TweaksPanel,
  TweakSection,
  TweakRow,
  TweakSlider,
  TweakToggle,
  TweakRadio,
  TweakSelect,
  TweakText,
  TweakNumber,
  TweakColor,
  TweakButton
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/venturekeep/tweaks-panel.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.StatCard = __ds_scope.StatCard;

__ds_ns.ProgressBar = __ds_scope.ProgressBar;

__ds_ns.EmptyState = __ds_scope.EmptyState;

__ds_ns.LoadingSpinner = __ds_scope.LoadingSpinner;

__ds_ns.Modal = __ds_scope.Modal;

__ds_ns.Notification = __ds_scope.Notification;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.FieldLabel = __ds_scope.FieldLabel;

__ds_ns.Input = __ds_scope.Input;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.Checkbox = __ds_scope.Checkbox;

__ds_ns.Tabs = __ds_scope.Tabs;

__ds_ns.ViewToggle = __ds_scope.ViewToggle;

})();
